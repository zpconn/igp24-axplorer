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


def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _record_r_value(record):
    for key in ("real_root_count", "r", "target_r"):
        value = _int_or_none(record.get(key))
        if value is not None:
            return value
    feedback = record.get("sair_feedback")
    if isinstance(feedback, dict):
        value = _int_or_none(feedback.get("r"))
        if value is not None:
            return value
        pair_key = feedback.get("pair_key")
        if isinstance(pair_key, str) and "|r=" in pair_key:
            return _int_or_none(pair_key.rsplit("|r=", 1)[-1])
    source = record.get("source_sample_export")
    if isinstance(source, dict):
        metadata = source.get("generation_metadata")
        if isinstance(metadata, dict):
            value = _int_or_none(metadata.get("target_r") or metadata.get("target_r_intent"))
            if value is not None:
                return value
    return None


def _decoded_coefficients_from_record(record):
    decoded = record.get("decoded_coefficients")
    if isinstance(decoded, list) and len(decoded) == 24:
        try:
            return [int(value) for value in decoded]
        except (TypeError, ValueError):
            return None

    exported = record.get("exported_coefficients")
    if isinstance(exported, list) and len(exported) == 25 and _int_or_none(exported[-1]) == 1:
        try:
            return [int(value) for value in exported[:-1]]
        except (TypeError, ValueError):
            return None

    coefficients = record.get("coefficients")
    if isinstance(coefficients, list):
        try:
            values = [int(value) for value in coefficients]
        except (TypeError, ValueError):
            return None
        if len(values) == 24:
            return values
        if len(values) == 25 and values[-1] == 1:
            return values[:-1]

    polynomial = record.get("polynomial")
    if isinstance(polynomial, str):
        parts = [part.strip() for part in polynomial.split(",") if part.strip()]
        if len(parts) == 25:
            try:
                values = [int(part) for part in parts]
            except ValueError:
                return None
            if values[-1] == 1:
                return values[:-1]
    return None


def _seed_label(record):
    feedback = record.get("sair_feedback")
    if isinstance(feedback, dict) and feedback.get("label"):
        return feedback.get("label")
    return record.get("label") or record.get("verified_group_label")


def _write_seed_bank_export_records(
    *,
    handle,
    args,
    export_path: Path,
    temperature: float,
    top_k: int | None,
    seen_decoded_coefficients: dict[tuple[int, ...], int],
    records_written: int,
    dedup_enabled: bool,
) -> tuple[int, dict[str, Any]]:
    seed_bank_path_text = str(getattr(args, "sample_export_seed_bank_jsonl", "") or "").strip()
    seed_limit = int(getattr(args, "sample_export_seed_bank_limit", 0) or 0)
    target_r = getattr(args, "sample_export_seed_bank_target_r", None)
    if target_r is None:
        target_r = getattr(args, "target_r", None)
    target_r = _int_or_none(target_r)
    stats: dict[str, Any] = {
        "seed_bank_enabled": bool(seed_bank_path_text and seed_limit > 0),
        "seed_bank_path": seed_bank_path_text or None,
        "seed_bank_target_r": target_r,
        "seed_bank_limit": seed_limit,
        "seed_bank_source_rows_read": 0,
        "seed_bank_rows_matching_target_r": 0,
        "seed_bank_records_written": 0,
        "seed_bank_duplicate_decoded_records_skipped": 0,
        "seed_bank_invalid_rows_skipped": 0,
        "seed_bank_max_coefficient_height": None,
    }
    if not stats["seed_bank_enabled"]:
        return records_written, stats

    seed_bank_path = Path(seed_bank_path_text)
    if not seed_bank_path.exists():
        raise FileNotFoundError(f"sample export seed bank does not exist: {seed_bank_path}")

    conditioning_mode = str(getattr(args, "sample_export_target_r_conditioning_mode", "seed_bank_prefix") or "seed_bank_prefix")
    max_height = 0
    with seed_bank_path.open("r", encoding="utf-8") as source:
        for source_index, line in enumerate(source):
            if stats["seed_bank_records_written"] >= seed_limit:
                break
            if not line.strip():
                continue
            stats["seed_bank_source_rows_read"] += 1
            try:
                source_record = json.loads(line)
            except json.JSONDecodeError:
                stats["seed_bank_invalid_rows_skipped"] += 1
                continue

            r_value = _record_r_value(source_record)
            if target_r is not None and r_value != target_r:
                continue
            stats["seed_bank_rows_matching_target_r"] += 1

            decoded_coefficients = _decoded_coefficients_from_record(source_record)
            if decoded_coefficients is None:
                stats["seed_bank_invalid_rows_skipped"] += 1
                continue
            decoded_key = tuple(decoded_coefficients)
            if decoded_key in seen_decoded_coefficients:
                if dedup_enabled:
                    stats["seed_bank_duplicate_decoded_records_skipped"] += 1
                    continue
            else:
                seen_decoded_coefficients[decoded_key] = records_written

            max_height = max(max_height, max(abs(value) for value in decoded_coefficients))
            record = build_sample_export_record(
                sample_index=records_written,
                export_index=records_written,
                batch_index=-1,
                batch_row=source_index,
                token_ids=[],
                decoded_coefficients=decoded_coefficients,
                args=args,
                temperature=temperature,
                top_k=top_k,
                dedup_enabled=dedup_enabled,
                unique_decoded_index=seen_decoded_coefficients.get(decoded_key),
            )
            record["sample_export_source"] = "target_r_seed_bank"
            record["seed_bank"] = {
                "path": str(seed_bank_path),
                "source_index": int(source_index),
                "source_record_type": source_record.get("record_type"),
                "source_role": source_record.get("source_role"),
                "target_r": target_r,
                "source_r": r_value,
                "label": _seed_label(source_record),
                "canonical_hash": source_record.get("canonical_hash"),
            }
            record["generation_metadata"].update(
                {
                    "strategy": "target_r_seed_bank_export",
                    "source": "target_r_seed_bank_prefix",
                    "target_r": target_r,
                    "target_r_intent": target_r,
                    "target_r_conditioning_mode": conditioning_mode,
                    "seed_bank_path": str(seed_bank_path),
                    "seed_bank_source_index": int(source_index),
                    "seed_bank_label": _seed_label(source_record),
                    "sample_export_only": True,
                }
            )
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            records_written += 1
            stats["seed_bank_records_written"] += 1

    stats["seed_bank_max_coefficient_height"] = max_height if stats["seed_bank_records_written"] else None
    logger.info(
        "Export-only target-r seed bank wrote %s records from %s for r=%s",
        stats["seed_bank_records_written"],
        seed_bank_path,
        target_r,
    )
    return records_written, stats


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
    target_r = _int_or_none(getattr(args, "target_r", None))
    conditioning_mode = str(getattr(args, "sample_export_target_r_conditioning_mode", "none") or "none")
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
        "sample_export_source": "model_generate",
        "generation_metadata": {
            "strategy": "model_sample_export",
            "source": "gpu_or_device_model_generate",
            "resolved_generation_strategy": getattr(args, "igp24_generation_strategy", None),
            "generation_preset": getattr(args, "igp24_generation_preset", None),
            "target_r": target_r,
            "target_r_intent": target_r,
            "target_r_conditioning_mode": conditioning_mode,
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
    seed_bank_requested = bool(getattr(args, "sample_export_seed_bank_jsonl", "") and int(getattr(args, "sample_export_seed_bank_limit", 0) or 0) > 0)
    controlled_export = dedup_enabled or unique_target > 0 or max_attempts_arg > 0 or seed_bank_requested

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
    seed_bank_stats: dict[str, Any] = {}

    logger.info(f"Export-only model sampling to {export_path}")
    if controlled_export:
        logger.info(
            "Export-only controls: dedup_enabled=%s unique_target=%s attempt_budget=%s progress_interval=%s seed_bank_requested=%s",
            dedup_enabled,
            unique_target,
            attempt_budget,
            progress_interval,
            seed_bank_requested,
        )
    with export_path.open("w", encoding="utf-8") as handle:
        records_written, seed_bank_stats = _write_seed_bank_export_records(
            handle=handle,
            args=args,
            export_path=export_path,
            temperature=temp,
            top_k=top_k,
            seen_decoded_coefficients=seen_decoded_coefficients,
            records_written=records_written,
            dedup_enabled=dedup_enabled,
        )
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
        **seed_bank_stats,
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
