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
    export_index: int | None = None,
    batch_index: int,
    batch_row: int,
    token_ids: list[int],
    decoded_coefficients: list[int] | None,
    args: Any,
    temperature: float,
    top_k: int | None,
    dedup_enabled: bool = False,
    unique_decoded_index: int | None = None,
) -> dict[str, Any]:
    exported_coefficients = decoded_coefficients + [1] if decoded_coefficients is not None else None
    return {
        "schema_version": 1,
        "record_type": "igp24_model_sample_export",
        "sample_index": int(sample_index),
        "export_index": int(sample_index if export_index is None else export_index),
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
        "deduplication": {
            "enabled": bool(dedup_enabled),
            "key_type": "decoded_coefficients",
            "unique_decoded_index": unique_decoded_index,
            "duplicate_decoded_coefficients": False,
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


def sample_export_summary_path(export_path: Path) -> Path:
    return export_path.with_suffix(export_path.suffix + ".summary.json")


def sample_and_export(model, args, stoi, itos, env, temp, temp_span=0, export_path=None):
    if export_path is None:
        raise ValueError("sample export path is required")

    export_path = Path(export_path)
    export_path.parent.mkdir(parents=True, exist_ok=True)

    sample_batch_size = args.gen_batch_size
    requested_total = int(args.num_samples_from_model)
    max_attempts_arg = int(getattr(args, "sample_export_max_attempts", 0) or 0)
    attempt_budget = max_attempts_arg if max_attempts_arg > 0 else requested_total
    unique_target = int(getattr(args, "sample_export_unique_target", 0) or 0)
    dedup_enabled = bool(getattr(args, "sample_export_dedup", False) or unique_target > 0)
    progress_interval = int(getattr(args, "sample_export_progress_interval", 0) or 0)
    controlled_export = dedup_enabled or unique_target > 0 or max_attempts_arg > 0

    top_k = args.top_k if args.top_k != -1 else None
    attempted_samples = 0
    records_written = 0
    decoded_records = 0
    invalid_decode_records = 0
    decoded_attempts = 0
    invalid_decode_attempts = 0
    duplicate_decoded_records_skipped = 0
    seen_decoded_coefficients: dict[tuple[int, ...], int] = {}
    stop_reason = "no_attempts_requested" if attempt_budget <= 0 else None

    logger.info(f"Export-only model sampling to {export_path}")
    if controlled_export:
        logger.info(
            "Export-only dedup controls: enabled=%s unique_target=%s attempt_budget=%s progress_interval=%s",
            dedup_enabled,
            unique_target,
            attempt_budget,
            progress_interval,
        )
    with export_path.open("w", encoding="utf-8") as handle:
        batch_index = 0
        while attempted_samples < attempt_budget:
            if unique_target > 0 and len(seen_decoded_coefficients) >= unique_target:
                stop_reason = "unique_target_reached"
                break

            batch_size = min(sample_batch_size, attempt_budget - attempted_samples)
            if batch_size <= 0:
                break
            if temp_span > 0:
                curr_temp = temp + 0.1 * np.random.randint(temp_span + 1)
            else:
                curr_temp = temp
            logger.info(f"{attempted_samples} / {attempt_budget} samples attempted for export")

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
                if unique_target > 0 and len(seen_decoded_coefficients) >= unique_target:
                    stop_reason = "unique_target_reached"
                    break

                sample_index = attempted_samples
                attempted_samples += 1
                token_ids = [int(token) for token in batch_numpy[batch_row].tolist()]
                decoded = env.tokenizer.decode(batch_numpy[batch_row])
                decoded_coefficients = None
                unique_decoded_index = None
                if decoded is not None:
                    decoded_coefficients = [int(coefficient) for coefficient in decoded.coefficients]
                    decoded_attempts += 1
                    decoded_key = tuple(decoded_coefficients)
                    if decoded_key in seen_decoded_coefficients:
                        if dedup_enabled:
                            duplicate_decoded_records_skipped += 1
                            if progress_interval > 0 and attempted_samples % progress_interval == 0:
                                logger.info(
                                    "Export-only dedup progress: attempts=%s/%s records_written=%s unique_decoded=%s duplicate_skipped=%s invalid_decode=%s",
                                    attempted_samples,
                                    attempt_budget,
                                    records_written,
                                    len(seen_decoded_coefficients),
                                    duplicate_decoded_records_skipped,
                                    invalid_decode_attempts,
                                )
                            continue
                    else:
                        unique_decoded_index = len(seen_decoded_coefficients)
                        seen_decoded_coefficients[decoded_key] = sample_index
                    decoded_records += 1
                else:
                    invalid_decode_attempts += 1
                    invalid_decode_records += 1

                record = build_sample_export_record(
                    sample_index=sample_index,
                    export_index=records_written,
                    batch_index=batch_index,
                    batch_row=batch_row,
                    token_ids=token_ids,
                    decoded_coefficients=decoded_coefficients,
                    args=args,
                    temperature=curr_temp,
                    top_k=top_k,
                    dedup_enabled=dedup_enabled,
                    unique_decoded_index=unique_decoded_index,
                )
                handle.write(json.dumps(record, sort_keys=True) + "\n")
                records_written += 1

                if progress_interval > 0 and attempted_samples % progress_interval == 0:
                    logger.info(
                        "Export-only dedup progress: attempts=%s/%s records_written=%s unique_decoded=%s duplicate_skipped=%s invalid_decode=%s",
                        attempted_samples,
                        attempt_budget,
                        records_written,
                        len(seen_decoded_coefficients),
                        duplicate_decoded_records_skipped,
                        invalid_decode_attempts,
                    )

            batch_index += 1

    if stop_reason is None:
        if unique_target > 0 and len(seen_decoded_coefficients) >= unique_target:
            stop_reason = "unique_target_reached"
        elif dedup_enabled or max_attempts_arg > 0:
            stop_reason = "attempt_budget_exhausted"
        else:
            stop_reason = "completed_requested_samples"

    summary_path = sample_export_summary_path(export_path) if controlled_export else None
    summary = {
        "export_path": str(export_path),
        "summary_path": str(summary_path) if summary_path is not None else None,
        "records_written": records_written,
        "requested_samples": requested_total,
        "attempt_budget": attempt_budget,
        "attempted_samples": attempted_samples,
        "decoded_attempts": decoded_attempts,
        "invalid_decode_attempts": invalid_decode_attempts,
        "decoded_records": decoded_records,
        "invalid_decode_records": invalid_decode_records,
        "deduplication_enabled": dedup_enabled,
        "deduplication_key_type": "decoded_coefficients",
        "unique_target": unique_target,
        "unique_decoded_coefficients": len(seen_decoded_coefficients),
        "duplicate_decoded_records_skipped": duplicate_decoded_records_skipped,
        "stop_reason": stop_reason,
        "progress_interval": progress_interval,
        "scoring_avoided": True,
        "local_search_avoided": True,
        "dataset_update_avoided": True,
    }
    if summary_path is not None:
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    logger.info(
        "Export-only model sampling wrote %s records to %s; attempts=%s decoded=%s invalid_decode=%s unique_decoded=%s duplicate_skipped=%s stop_reason=%s",
        records_written,
        export_path,
        attempted_samples,
        decoded_records,
        invalid_decode_records,
        len(seen_decoded_coefficients),
        duplicate_decoded_records_skipped,
        stop_reason,
    )
    return summary
