import hashlib
import json
import math
import queue
import threading
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
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

            X_init = generation_prefix_tensor(sample_batch_size, args, stoi, env)
            X_init = X_init.to(args.device)
            top_k = args.top_k if args.top_k != -1 else None
            batch_numpy = model.generate(
                X_init,
                generation_max_new_tokens(args, X_init.shape[1]),
                temperature=curr_temp,
                top_k=top_k,
                do_sample=True,
            ).cpu().numpy()

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


def generation_prefix_token_ids(args: Any, stoi: dict[Any, int], env: Any) -> list[int]:
    tokens = [int(stoi["BOS"])]
    mode = str(getattr(args, "igp24_target_r_conditioning_mode", "none") or "none")
    if mode != "control_token":
        return tokens
    token_ids = []
    helper = getattr(env.tokenizer, "target_r_control_token_ids", None)
    if helper is not None:
        token_ids = helper(getattr(args, "target_r", None))
    tokens.extend(int(token_id) for token_id in token_ids)
    return tokens


def generation_prefix_tensor(batch_size: int, args: Any, stoi: dict[Any, int], env: Any) -> torch.Tensor:
    prefix = generation_prefix_token_ids(args, stoi, env)
    X_init = torch.empty((int(batch_size), len(prefix)), dtype=torch.long)
    for index, token_id in enumerate(prefix):
        X_init[:, index] = int(token_id)
    return X_init


def generation_max_new_tokens(args: Any, prefix_length: int) -> int:
    block_size = int(getattr(args, "block_size", int(getattr(args, "max_len", 0)) + 2))
    return max(1, block_size - int(prefix_length))


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


def _json_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_csv_set(value: Any) -> set[str]:
    return {item.strip() for item in str(value or "").split(",") if item.strip()}


def _record_hash_values(record: dict[str, Any]) -> set[str]:
    hashes: set[str] = set()
    for container in (
        record,
        record.get("generation_metadata") if isinstance(record.get("generation_metadata"), dict) else {},
        record.get("sample_provenance") if isinstance(record.get("sample_provenance"), dict) else {},
        record.get("source_sample_export") if isinstance(record.get("source_sample_export"), dict) else {},
    ):
        if not isinstance(container, dict):
            continue
        for key in ("canonical_hash", "coefficient_hash", "decoded_hash", "exported_coefficient_hash"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                hashes.add(value.strip())
    return hashes


def _decoded_hash_values(decoded_coefficients: list[int] | None, provenance: dict[str, Any] | None = None) -> set[str]:
    hashes: set[str] = set()
    if decoded_coefficients is None:
        return hashes
    if isinstance(provenance, dict):
        hashes.update(_record_hash_values(provenance))
    hashes.add(_json_hash({"degree": 24, "coefficients": decoded_coefficients}))
    try:
        from src.igp24.polynomial import stable_canonical_hash

        hashes.add(stable_canonical_hash(decoded_coefficients))
    except Exception:
        pass
    return {value for value in hashes if value}


def _load_excluded_hashes(path_text: str | None) -> tuple[set[str], dict[str, Any]]:
    path_text = str(path_text or "").strip()
    stats: dict[str, Any] = {
        "excluded_hashes_enabled": bool(path_text),
        "excluded_hashes_path": path_text or None,
        "excluded_hashes_source_rows_read": 0,
        "excluded_hashes_loaded": 0,
        "excluded_hashes_invalid_rows_skipped": 0,
    }
    if not path_text:
        return set(), stats

    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"sample export excluded hashes file does not exist: {path}")

    hashes: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        stats["excluded_hashes_source_rows_read"] += 1
        if line.startswith("{"):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                stats["excluded_hashes_invalid_rows_skipped"] += 1
                continue
            if isinstance(record, dict):
                hashes.update(_record_hash_values(record))
                decoded = _decoded_coefficients_from_record(record)
                if decoded is not None:
                    hashes.update(_decoded_hash_values(decoded))
        else:
            hashes.add(line)
    stats["excluded_hashes_loaded"] = len(hashes)
    return hashes, stats


def classify_sparse_support_submode(odd_support_exponents: list[int]) -> str:
    odd_support = sorted({int(exponent) for exponent in odd_support_exponents})
    if not odd_support:
        return "sparse_no_odd_support_gcd1"
    if len(odd_support) == 1:
        return f"sparse_odd_single_e{odd_support[0]}_support_gcd1"
    if len(odd_support) == 2:
        gap = odd_support[1] - odd_support[0]
        return f"sparse_odd_pair_gap{gap}_support_gcd1"
    span = odd_support[-1] - odd_support[0]
    return f"sparse_odd_multi_n{len(odd_support)}_span{span}_support_gcd1"


def sample_support_profile(decoded_coefficients: list[int] | None) -> dict[str, Any]:
    if decoded_coefficients is None:
        return {
            "support": [],
            "support_count": 0,
            "support_gcd": None,
            "even_support_like": None,
            "odd_support_exponents": [],
            "support_pattern": "invalid_decode",
            "sparse_support_submode": None,
        }
    coeffs = [int(value) for value in decoded_coefficients]
    support = [index for index, value in enumerate(coeffs) if value != 0]
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, int(exponent))
    support_gcd_value = support_gcd or None
    even_support_like = bool(support) and all(index % 2 == 0 for index in support)
    odd_support = [index for index in support if index % 2 == 1]
    if not support:
        support_pattern = "zero_decoded"
    elif len(support) == 1 and support[0] == 0:
        support_pattern = "constant_only"
    elif even_support_like:
        support_pattern = "even_support_like"
    elif support_gcd_value and support_gcd_value > 1:
        support_pattern = f"support_gcd_{support_gcd_value}"
    elif len(support) <= 6:
        support_pattern = "sparse_mixed_support_gcd1"
    elif len(support) <= 14:
        support_pattern = "medium_mixed_support_gcd1"
    else:
        support_pattern = "dense_mixed_support_gcd1"
    sparse_support_submode = (
        classify_sparse_support_submode(odd_support) if support_pattern == "sparse_mixed_support_gcd1" else None
    )
    return {
        "support": support,
        "support_count": len(support),
        "support_gcd": support_gcd_value,
        "even_support_like": even_support_like,
        "odd_support_exponents": odd_support,
        "support_pattern": support_pattern,
        "sparse_support_submode": sparse_support_submode,
    }


def build_sample_provenance(
    *,
    decoded_coefficients: list[int] | None,
    args: Any,
    sample_index: int,
    batch_index: int,
    batch_row: int,
    temperature: float,
    top_k: int | None,
) -> dict[str, Any]:
    target_r = _int_or_none(getattr(args, "target_r", None))
    strategy = str(getattr(args, "igp24_generation_strategy", "") or "unknown")
    preset = str(getattr(args, "igp24_generation_preset", "") or "none")
    support = sample_support_profile(decoded_coefficients)
    support_gcd = support["support_gcd"]
    even_support_like = support["even_support_like"]
    support_pattern = str(support["support_pattern"])
    sparse_support_submode = support.get("sparse_support_submode")
    if decoded_coefficients is None:
        perturbation_mode = "invalid_decode"
    elif even_support_like:
        perturbation_mode = "even_support_g_x2_like"
    elif support_gcd and int(support_gcd) > 1:
        perturbation_mode = f"support_gcd_{int(support_gcd)}_composed_like"
    elif support["support_count"] <= 6:
        perturbation_mode = str(sparse_support_submode or "sparse_mixed_support_gcd1")
    elif support["support_count"] <= 14:
        perturbation_mode = "medium_mixed_support_gcd1"
    else:
        perturbation_mode = "dense_mixed_support_gcd1"

    template_family_id = f"model:{strategy}:r{target_r if target_r is not None else 'any'}:{support_pattern}"
    basin_key = {
        "strategy": strategy,
        "target_r": target_r,
        "support_pattern": support_pattern,
        "support": support["support"],
        "support_count": support["support_count"],
        "odd_support_exponents": support["odd_support_exponents"],
        "sparse_support_submode": sparse_support_submode,
        "support_gcd": support_gcd,
        "even_support_like": even_support_like,
        "perturbation_mode": perturbation_mode,
    }
    basin_fingerprint = _json_hash(basin_key)[:24]
    lineage = {
        "seed": getattr(args, "seed", None),
        "exp_name": getattr(args, "exp_name", None),
        "exp_id": getattr(args, "exp_id", None),
        "sample_index": int(sample_index),
        "batch_index": int(batch_index),
        "batch_row": int(batch_row),
    }
    coefficient_hash = _json_hash({"degree": 24, "coefficients": decoded_coefficients}) if decoded_coefficients is not None else None
    exported_hash = (
        _json_hash({"degree": 24, "exported_coefficients": list(decoded_coefficients) + [1]})
        if decoded_coefficients is not None
        else None
    )
    return {
        "schema_version": 1,
        "generation_strategy": strategy,
        "generation_preset": preset,
        "target_r": target_r,
        "template_family_id": template_family_id,
        "family_key": f"{template_family_id}:{basin_fingerprint}",
        "perturbation_mode": perturbation_mode,
        "support_pattern": support_pattern,
        "support": support["support"],
        "support_count": support["support_count"],
        "support_gcd": support_gcd,
        "even_support_like": even_support_like,
        "odd_support_exponents": support["odd_support_exponents"],
        "sparse_support_submode": sparse_support_submode,
        "coefficient_hash": coefficient_hash,
        "decoded_hash": coefficient_hash,
        "exported_coefficient_hash": exported_hash,
        "basin_fingerprint": basin_fingerprint,
        "basin_fingerprint_key": basin_key,
        "modular_signature": None,
        "source_seed_hash": _json_hash(lineage)[:24],
        "source_lineage": lineage,
        "sampler_knobs": {
            "temperature": float(temperature),
            "top_k": top_k,
            "unique_target": int(getattr(args, "sample_export_unique_target", 0) or 0),
            "dedup": bool(getattr(args, "sample_export_dedup", False)),
            "max_attempts": int(getattr(args, "sample_export_max_attempts", 0) or 0),
            "model_target_r_conditioning_mode": str(getattr(args, "igp24_target_r_conditioning_mode", "none") or "none"),
            "sample_export_target_r_conditioning_mode": str(
                getattr(args, "sample_export_target_r_conditioning_mode", "none") or "none"
            ),
        },
    }


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
    excluded_hashes: set[str] | None = None,
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
        "seed_bank_excluded_hash_records_skipped": 0,
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
            row_hashes = _record_hash_values(source_record) | _decoded_hash_values(decoded_coefficients)
            if excluded_hashes and row_hashes.intersection(excluded_hashes):
                stats["seed_bank_excluded_hash_records_skipped"] += 1
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
    sample_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exported_coefficients = decoded_coefficients + [1] if decoded_coefficients is not None else None
    target_r = _int_or_none(getattr(args, "target_r", None))
    sample_conditioning_mode = str(getattr(args, "sample_export_target_r_conditioning_mode", "none") or "none")
    model_conditioning_mode = str(getattr(args, "igp24_target_r_conditioning_mode", "none") or "none")
    conditioning_mode = model_conditioning_mode if sample_conditioning_mode == "none" else sample_conditioning_mode
    provenance = sample_provenance or build_sample_provenance(
        decoded_coefficients=decoded_coefficients,
        args=args,
        sample_index=sample_index,
        batch_index=batch_index,
        batch_row=batch_row,
        temperature=temperature,
        top_k=top_k,
    )
    record = {
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
        "sample_provenance": provenance,
        "template_family_id": provenance.get("template_family_id"),
        "perturbation_mode": provenance.get("perturbation_mode"),
        "support_pattern": provenance.get("support_pattern"),
        "sparse_support_submode": provenance.get("sparse_support_submode"),
        "support_gcd": provenance.get("support_gcd"),
        "even_support_like": provenance.get("even_support_like"),
        "coefficient_hash": provenance.get("coefficient_hash"),
        "decoded_hash": provenance.get("decoded_hash"),
        "basin_fingerprint": provenance.get("basin_fingerprint"),
        "modular_signature": provenance.get("modular_signature"),
        "source_seed_hash": provenance.get("source_seed_hash"),
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
            "generation_strategy": provenance.get("generation_strategy"),
            "generation_preset": getattr(args, "igp24_generation_preset", None),
            "construction_family": "model_sample_export",
            "source_family": "model_sample_export",
            "template_family_id": provenance.get("template_family_id"),
            "family_key": provenance.get("family_key"),
            "perturbation_mode": provenance.get("perturbation_mode"),
            "support_pattern": provenance.get("support_pattern"),
            "sparse_support_submode": provenance.get("sparse_support_submode"),
            "support_gcd": provenance.get("support_gcd"),
            "even_support_like": provenance.get("even_support_like"),
            "odd_support_exponents": provenance.get("odd_support_exponents"),
            "coefficient_hash": provenance.get("coefficient_hash"),
            "decoded_hash": provenance.get("decoded_hash"),
            "exported_coefficient_hash": provenance.get("exported_coefficient_hash"),
            "basin_fingerprint": provenance.get("basin_fingerprint"),
            "modular_signature": provenance.get("modular_signature"),
            "source_seed_hash": provenance.get("source_seed_hash"),
            "sampler_knobs": provenance.get("sampler_knobs"),
            "encoding_tokens": getattr(args, "encoding_tokens", None),
            "target_r": target_r,
            "target_r_intent": target_r,
            "target_r_conditioning_mode": conditioning_mode,
            "model_target_r_conditioning_mode": model_conditioning_mode,
            "sample_export_target_r_conditioning_mode": sample_conditioning_mode,
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
    return record


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
    avoid_even_support_like = bool(getattr(args, "sample_export_avoid_even_support_like", False))
    require_support_gcd_one = bool(getattr(args, "sample_export_require_support_gcd_one", False))
    require_nonzero_constant = bool(getattr(args, "sample_export_require_nonzero_constant", False))
    required_support_patterns = _parse_csv_set(getattr(args, "sample_export_required_support_patterns", ""))
    excluded_support_patterns = _parse_csv_set(getattr(args, "sample_export_excluded_support_patterns", ""))
    excluded_hashes, excluded_hash_stats = _load_excluded_hashes(getattr(args, "sample_export_excluded_hashes_jsonl", ""))
    family_cap = int(getattr(args, "sample_export_family_cap", 0) or 0)
    basin_fingerprint_cap = int(getattr(args, "sample_export_basin_fingerprint_cap", 0) or 0)
    provenance_controls_enabled = (
        avoid_even_support_like
        or require_support_gcd_one
        or require_nonzero_constant
        or bool(required_support_patterns)
        or bool(excluded_support_patterns)
        or bool(excluded_hashes)
        or family_cap > 0
        or basin_fingerprint_cap > 0
    )
    controlled_export = (
        dedup_enabled
        or unique_target > 0
        or max_attempts_arg > 0
        or seed_bank_requested
        or provenance_controls_enabled
    )

    top_k = args.top_k if args.top_k != -1 else None
    attempted_samples = 0
    records_written = 0
    decoded_records = 0
    invalid_decode_records = 0
    decoded_attempts = 0
    invalid_decode_attempts = 0
    duplicate_decoded_records_skipped = 0
    excluded_hash_records_skipped = 0
    seen_decoded_coefficients: dict[tuple[int, ...], int] = {}
    exported_family_counts: Counter[str] = Counter()
    exported_basin_fingerprint_counts: Counter[str] = Counter()
    provenance_skip_counts: Counter[str] = Counter()
    stop_reason = "no_attempts_requested" if attempt_budget <= 0 else None
    seed_bank_stats: dict[str, Any] = {}

    logger.info(f"Export-only model sampling to {export_path}")
    if controlled_export:
        logger.info(
            "Export-only controls: dedup_enabled=%s unique_target=%s attempt_budget=%s progress_interval=%s seed_bank_requested=%s provenance_controls=%s",
            dedup_enabled,
            unique_target,
            attempt_budget,
            progress_interval,
            seed_bank_requested,
            provenance_controls_enabled,
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
            excluded_hashes=excluded_hashes,
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

            X_init = generation_prefix_tensor(batch_size, args, stoi, env)
            X_init = X_init.to(args.device)
            batch_numpy = model.generate(
                X_init,
                generation_max_new_tokens(args, X_init.shape[1]),
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
                sample_provenance = None
                if decoded is not None:
                    decoded_coefficients = [int(coefficient) for coefficient in decoded.coefficients]
                    decoded_attempts += 1
                    decoded_key = tuple(decoded_coefficients)
                    decoded_already_seen = decoded_key in seen_decoded_coefficients
                    if decoded_already_seen:
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
                    sample_provenance = build_sample_provenance(
                        decoded_coefficients=decoded_coefficients,
                        args=args,
                        sample_index=sample_index,
                        batch_index=batch_index,
                        batch_row=batch_row,
                        temperature=curr_temp,
                        top_k=top_k,
                    )
                    skip_reasons: list[str] = []
                    if avoid_even_support_like and sample_provenance.get("even_support_like") is True:
                        skip_reasons.append("even_support_like")
                    support_gcd = sample_provenance.get("support_gcd")
                    if require_support_gcd_one and support_gcd != 1:
                        skip_reasons.append("support_gcd_not_one")
                    if require_nonzero_constant and int(decoded_coefficients[0]) == 0:
                        skip_reasons.append("zero_constant_term")
                    support_pattern = str(sample_provenance.get("support_pattern") or "unknown")
                    if required_support_patterns and support_pattern not in required_support_patterns:
                        skip_reasons.append("required_support_pattern_mismatch")
                    if excluded_support_patterns and support_pattern in excluded_support_patterns:
                        skip_reasons.append("excluded_support_pattern")
                    if excluded_hashes and _decoded_hash_values(decoded_coefficients, sample_provenance).intersection(excluded_hashes):
                        skip_reasons.append("excluded_hash")
                    family_id = str(sample_provenance.get("template_family_id") or "unknown")
                    basin_fingerprint = str(sample_provenance.get("basin_fingerprint") or "unknown")
                    if family_cap > 0 and exported_family_counts[family_id] >= family_cap:
                        skip_reasons.append("template_family_cap")
                    if basin_fingerprint_cap > 0 and exported_basin_fingerprint_counts[basin_fingerprint] >= basin_fingerprint_cap:
                        skip_reasons.append("basin_fingerprint_cap")
                    if skip_reasons:
                        for reason in skip_reasons:
                            provenance_skip_counts[reason] += 1
                        if "excluded_hash" in skip_reasons:
                            excluded_hash_records_skipped += 1
                        if progress_interval > 0 and attempted_samples % progress_interval == 0:
                            logger.info(
                                "Export-only provenance skip: attempts=%s/%s reasons=%s written=%s unique_decoded=%s",
                                attempted_samples,
                                attempt_budget,
                                ",".join(skip_reasons),
                                records_written,
                                len(seen_decoded_coefficients),
                            )
                        continue
                    else:
                        if decoded_already_seen:
                            unique_decoded_index = seen_decoded_coefficients[decoded_key]
                        else:
                            unique_decoded_index = len(seen_decoded_coefficients)
                            seen_decoded_coefficients[decoded_key] = sample_index
                    exported_family_counts[family_id] += 1
                    exported_basin_fingerprint_counts[basin_fingerprint] += 1
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
                    sample_provenance=sample_provenance,
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
        "target_r": _int_or_none(getattr(args, "target_r", None)),
        "encoding_tokens": getattr(args, "encoding_tokens", None),
        "model_target_r_conditioning_mode": getattr(args, "igp24_target_r_conditioning_mode", "none"),
        "sample_export_target_r_conditioning_mode": getattr(args, "sample_export_target_r_conditioning_mode", "none"),
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
        "excluded_hash_records_skipped": excluded_hash_records_skipped,
        "provenance_controls_enabled": provenance_controls_enabled,
        "avoid_even_support_like": avoid_even_support_like,
        "require_support_gcd_one": require_support_gcd_one,
        "require_nonzero_constant": require_nonzero_constant,
        "required_support_patterns": sorted(required_support_patterns),
        "excluded_support_patterns": sorted(excluded_support_patterns),
        "excluded_hashes_path": excluded_hash_stats.get("excluded_hashes_path"),
        "excluded_hashes_loaded": excluded_hash_stats.get("excluded_hashes_loaded", 0),
        "family_cap": family_cap,
        "basin_fingerprint_cap": basin_fingerprint_cap,
        "provenance_skip_counts": dict(provenance_skip_counts),
        "exported_template_family_counts": dict(exported_family_counts),
        "exported_basin_fingerprint_counts": dict(exported_basin_fingerprint_counts),
        "stop_reason": stop_reason,
        "progress_interval": progress_interval,
        "scoring_avoided": True,
        "local_search_avoided": True,
        "dataset_update_avoided": True,
        **seed_bank_stats,
        **excluded_hash_stats,
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
