import json
import queue
import threading
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from typing import Any

import numpy as np
import torch

from src.datasets import detokenize
from src.envs.environment import do_score, do_stats
from src.utils import MAX_WORKERS

logger = getLogger()


class _CpuSink:
    def __init__(self, fn, decouple=False):
        self._fn = fn
        self._decouple = decouple
        self._queue = None
        self._thread = None
        self._error = None

    def start(self):
        if not self._decouple:
            return
        self._queue = queue.Queue()

        def consumer():
            try:
                while True:
                    item = self._queue.get()
                    if item is None:
                        break
                    self._fn(*item)
            except Exception as e:
                self._error = e

        self._thread = threading.Thread(target=consumer, daemon=True)
        self._thread.start()

    def submit(self, *args):
        if self._decouple:
            if self._error is not None:
                raise self._error
            self._queue.put(args)
        else:
            self._fn(*args)

    def join(self):
        if self._decouple:
            self._queue.put(None)
            self._thread.join()
            if self._error is not None:
                raise self._error


@contextmanager
def cpu_sink(fn, decouple=False):
    sink = _CpuSink(fn, decouple)
    sink.start()
    try:
        yield sink
    finally:
        sink.join()


def sample_and_score(model, args, stoi, itos, env, temp, temp_span=0):
    sample_batch_size = args.gen_batch_size
    todo = args.num_samples_from_model // sample_batch_size
    DETOK_CHUNK_SIZE = 1

    results = []
    total_invalid = 0
    all_processed_data = []
    results_lock = threading.Lock()

    executor = ProcessPoolExecutor(max_workers=min(MAX_WORKERS, args.num_workers))

    def process_batches(batches):
        nonlocal total_invalid
        all_data = [batch_numpy[j] for batch_numpy in batches for j in range(batch_numpy.shape[0])]
        detok_results = detokenize(all_data, args, env, executor=executor)
        valid_data, n_invalid, processed_data = do_score(detok_results, args=args, executor=executor)
        with results_lock:
            results.extend(valid_data)
            total_invalid += n_invalid
            all_processed_data.extend(processed_data)

    with cpu_sink(process_batches, decouple=True) as sink:
        pending_batches = []

        for i in range(todo):
            if temp_span > 0:
                curr_temp = temp + 0.1 * np.random.randint(temp_span + 1)
            else:
                curr_temp = temp
            if i % 100 == 0:
                with results_lock:
                    scored_so_far = len(results)
                logger.info(f"{i*sample_batch_size} / {todo * sample_batch_size} samples generated, {scored_so_far} scored")

            X_init = torch.empty((sample_batch_size, 1), dtype=torch.long)
            X_init[:, 0] = stoi["BOS"]
            X_init = X_init.to(args.device)
            top_k = args.top_k if args.top_k != -1 else None
            batch_numpy = model.generate(X_init, args.max_len + 1, temperature=curr_temp, top_k=top_k, do_sample=True).cpu().numpy()

            pending_batches.append(batch_numpy)

            if len(pending_batches) >= DETOK_CHUNK_SIZE:
                sink.submit(pending_batches)
                pending_batches = []

        if pending_batches:
            sink.submit(pending_batches)

    executor.shutdown(wait=True)

    do_stats(total_invalid, all_processed_data)

    return results


def build_sample_export_record(
    *,
    sample_index: int,
    batch_index: int,
    batch_row: int,
    token_ids: list[int],
    decoded_coefficients: list[int] | None,
    args: Any,
    temperature: float,
    top_k: int | None,
) -> dict[str, Any]:
    exported_coefficients = decoded_coefficients + [1] if decoded_coefficients is not None else None
    return {
        "schema_version": 1,
        "record_type": "igp24_model_sample_export",
        "sample_index": int(sample_index),
        "batch_index": int(batch_index),
        "batch_row": int(batch_row),
        "env_name": getattr(args, "env_name", None),
        "exp_name": getattr(args, "exp_name", None),
        "exp_id": getattr(args, "exp_id", None),
        "device": getattr(args, "device", None),
        "temperature": float(temperature),
        "top_k": top_k,
        "max_len": int(getattr(args, "max_len", 0)),
        "coeff_bound": int(getattr(args, "coeff_bound", 0)),
        "token_ids": token_ids,
        "decoded": decoded_coefficients is not None,
        "decoded_coefficients": decoded_coefficients,
        "exported_coefficients": exported_coefficients,
        "score": None,
        "scoring_status": "unscored",
        "local_search_status": "not_run",
        "verification_status": "not_run",
        "verified_group_label": None,
        "generation_metadata": {
            "strategy": "model_sample_export",
            "source": "gpu_or_device_model_generate",
            "resolved_generation_strategy": getattr(args, "igp24_generation_strategy", None),
            "generation_preset": getattr(args, "igp24_generation_preset", None),
            "sample_export_only": True,
        },
        "safety": {
            "proxy_only": True,
            "scored": False,
            "local_search_run": False,
            "runs_exact_verifiers": False,
            "calls_sair": False,
            "uses_network": False,
            "auto_submits": False,
        },
    }


def sample_and_export(model, args, stoi, itos, env, temp, temp_span=0, export_path=None):
    if export_path is None:
        raise ValueError("sample export path is required")

    export_path = Path(export_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)

    sample_batch_size = args.gen_batch_size
    total = int(args.num_samples_from_model)
    batch_counts = [sample_batch_size] * (total // sample_batch_size)
    remainder = total % sample_batch_size
    if remainder:
        batch_counts.append(remainder)

    top_k = args.top_k if args.top_k != -1 else None
    records_written = 0
    decoded_records = 0
    invalid_decode_records = 0

    logger.info(f"Export-only model sampling to {export_path}")
    with export_path.open("w", encoding="utf-8") as handle:
        for batch_index, batch_size in enumerate(batch_counts):
            if temp_span > 0:
                curr_temp = temp + 0.1 * np.random.randint(temp_span + 1)
            else:
                curr_temp = temp
            logger.info(f"{records_written} / {total} samples generated for export")

            X_init = torch.empty((batch_size, 1), dtype=torch.long)
            X_init[:, 0] = stoi["BOS"]
            X_init = X_init.to(args.device)
            batch_numpy = model.generate(
                X_init,
                args.max_len + 1,
                temperature=curr_temp,
                top_k=top_k,
                do_sample=True,
            ).cpu().numpy()

            for batch_row in range(batch_numpy.shape[0]):
                token_ids = [int(token) for token in batch_numpy[batch_row].tolist()]
                decoded = env.tokenizer.decode(batch_numpy[batch_row])
                decoded_coefficients = None
                if decoded is not None:
                    decoded_coefficients = [int(coefficient) for coefficient in decoded.coefficients]
                    decoded_records += 1
                else:
                    invalid_decode_records += 1

                record = build_sample_export_record(
                    sample_index=records_written,
                    batch_index=batch_index,
                    batch_row=batch_row,
                    token_ids=token_ids,
                    decoded_coefficients=decoded_coefficients,
                    args=args,
                    temperature=curr_temp,
                    top_k=top_k,
                )
                handle.write(json.dumps(record, sort_keys=True) + "\n")
                records_written += 1

    logger.info(
        "Export-only model sampling wrote %s records to %s; decoded=%s invalid_decode=%s",
        records_written,
        export_path,
        decoded_records,
        invalid_decode_records,
    )
    return {
        "export_path": str(export_path),
        "records_written": records_written,
        "decoded_records": decoded_records,
        "invalid_decode_records": invalid_decode_records,
        "scoring_avoided": True,
        "local_search_avoided": True,
        "dataset_update_avoided": True,
    }
