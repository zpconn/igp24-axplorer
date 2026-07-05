#!/usr/bin/env python3
"""Audit local algebraic structure for an IGP24 exact-verification queue.

This helper is local-exact-algebra only. It recomputes discriminants and
coefficient support structure from queued candidates, but it does not call
PARI, MAGMA, SAIR, network APIs, training, GPU sampling, local search, or
submission paths. It does not claim exact Galois labels.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl
from src.igp24.polynomial import DEGREE, IGP24Error, exact_discriminant, validate_coefficients


AUDIT_JSONL = "structure_audit.jsonl"
PRIORITY_JSONL = "manual_priority.jsonl"
PRIORITY_TXT = "manual_priority_hashes.txt"
SUMMARY_JSON = "structure_summary.json"
REPORT_MD = "structure_report.md"
DEFAULT_BLOCK_DIVISORS = (2, 3, 4, 6, 8, 12)
SAFETY_NOTE = (
    "Local exact-algebra structure audit only. No exact Galois label is "
    "claimed, and no PARI, MAGMA, SAIR, network API, training loop, GPU "
    "sampler, CPU hot loop, local search, or submission path is used."
)


class StructureAuditError(ValueError):
    """Raised when a queue row cannot be structurally audited."""


def _coerce_int_list(value: Any) -> list[int] | None:
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        return None
    return list(value)


def exported_coefficients(record: dict[str, Any]) -> list[int]:
    """Return validated `[a0, ..., a23, 1]` coefficients from common row shapes."""

    raw = _coerce_int_list(record.get("exported_coefficients"))
    if raw is not None and len(raw) == DEGREE + 1 and raw[-1] == 1:
        return raw
    raw = _coerce_int_list(record.get("coefficients"))
    if raw is not None:
        if len(raw) == DEGREE:
            return raw + [1]
        if len(raw) == DEGREE + 1 and raw[-1] == 1:
            return raw
    raw = _coerce_int_list(record.get("decoded_coefficients"))
    if raw is not None and len(raw) == DEGREE:
        return raw + [1]
    raise StructureAuditError("missing_valid_exported_coefficients")


def free_coefficients(record: dict[str, Any]) -> list[int]:
    return exported_coefficients(record)[:-1]


def _strategy(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    return str(record.get("source_strategy") or metadata.get("strategy") or "missing")


def _flags(record: dict[str, Any]) -> list[str]:
    flags = record.get("non_generic_flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _claimed_square_discriminant(record: dict[str, Any]) -> bool:
    evidence = record.get("non_generic_evidence") or {}
    return "square_discriminant_excludes_s24" in _flags(record) or bool(evidence.get("square_discriminant"))


def _claimed_exact_composed(record: dict[str, Any]) -> bool:
    evidence = record.get("non_generic_evidence") or {}
    block = evidence.get("block_structure") or {}
    return "exact_composed_support" in _flags(record) or bool(block.get("exact_block_divisors"))


def _is_square_integer(value: int) -> bool:
    if value < 0:
        return False
    root = math.isqrt(value)
    return root * root == value


def _nonzero_exponents(coefficients: list[int]) -> list[int]:
    return [exponent for exponent, coeff in enumerate(coefficients) if coeff != 0]


def _polynomial_text(coefficients: list[int], variable: str = "y") -> str:
    terms: list[str] = []
    for power, coeff in enumerate(coefficients):
        if coeff == 0:
            continue
        if power == 0:
            base = "1"
        elif power == 1:
            base = variable
        else:
            base = f"{variable}^{power}"
        terms.append(f"({coeff})*{base}")
    return " + ".join(terms) if terms else "0"


def exact_block_bases(
    coefficients: list[int],
    *,
    block_divisors: Iterable[int] = DEFAULT_BLOCK_DIVISORS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return exact `f(x)=g(x^d)` bases and per-divisor support summaries."""

    if len(coefficients) != DEGREE + 1:
        raise StructureAuditError(f"expected_{DEGREE + 1}_exported_coefficients")
    nonzero = _nonzero_exponents(coefficients)
    bases: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for raw_divisor in block_divisors:
        divisor = int(raw_divisor)
        if divisor <= 1 or DEGREE % divisor:
            continue
        off_block = [exponent for exponent in nonzero if exponent % divisor != 0]
        exact = len(off_block) == 0
        summary = {
            "divisor": divisor,
            "off_block_terms": len(off_block),
            "off_block_exponents": off_block,
            "exact_composed_support": exact,
        }
        summaries.append(summary)
        if exact:
            base_degree = DEGREE // divisor
            base_coefficients = [coefficients[index * divisor] for index in range(base_degree + 1)]
            bases.append(
                {
                    "divisor": divisor,
                    "base_degree": base_degree,
                    "base_coefficients": base_coefficients,
                    "base_nonzero_term_count": len(_nonzero_exponents(base_coefficients)),
                    "base_polynomial": _polynomial_text(base_coefficients, variable="y"),
                }
            )
    return bases, summaries


def _sparse_bucket(nonzero_term_count: int) -> str:
    if nonzero_term_count <= 6:
        return "very_sparse"
    if nonzero_term_count <= 10:
        return "sparse"
    return "dense"


def _claim_status(claimed: bool, confirmed: bool) -> str:
    if claimed and confirmed:
        return "confirmed"
    if claimed and not confirmed:
        return "refuted"
    if not claimed and confirmed:
        return "unclaimed_confirmed"
    return "not_claimed"


def audit_record(
    record: dict[str, Any],
    *,
    queue_index: int,
    block_divisors: Iterable[int] = DEFAULT_BLOCK_DIVISORS,
) -> dict[str, Any]:
    exported = exported_coefficients(record)
    free = exported[:-1]
    try:
        validate_coefficients(free)
    except IGP24Error as exc:
        raise StructureAuditError(str(exc)) from exc

    discriminant = exact_discriminant(free)
    is_square = _is_square_integer(discriminant)
    square_root = math.isqrt(discriminant) if is_square else None
    bases, block_summaries = exact_block_bases(exported, block_divisors=block_divisors)
    exact_divisors = [int(item["divisor"]) for item in bases]
    primary_base = max(bases, key=lambda item: int(item["divisor"])) if bases else None
    nonzero_exponents = _nonzero_exponents(exported)
    sparse_bucket = _sparse_bucket(len(nonzero_exponents))
    claimed_square = _claimed_square_discriminant(record)
    claimed_exact = _claimed_exact_composed(record)
    recorded_discriminant = record.get("discriminant")
    recorded_matches = recorded_discriminant == discriminant if isinstance(recorded_discriminant, int) else None

    return {
        "schema_version": 1,
        "record_type": "igp24_structure_audit_record",
        "queue_index": int(record.get("input_index") or queue_index),
        "canonical_hash": record.get("canonical_hash"),
        "short_hash": str(record.get("canonical_hash") or "")[:12],
        "source_strategy": _strategy(record),
        "source_ledger_path": record.get("source_ledger_path"),
        "score": record.get("score"),
        "non_generic_score": record.get("non_generic_score"),
        "real_root_count": record.get("real_root_count"),
        "coefficient_height": record.get("coefficient_height"),
        "non_generic_flags": _flags(record),
        "local_discriminant": discriminant,
        "local_log_abs_discriminant": math.log(abs(discriminant)) if discriminant else None,
        "local_discriminant_is_square": is_square,
        "local_discriminant_square_root": square_root,
        "recorded_discriminant_matches_local": recorded_matches,
        "claimed_square_discriminant": claimed_square,
        "square_discriminant_claim_status": _claim_status(claimed_square, is_square),
        "nonzero_exponents": nonzero_exponents,
        "nonzero_term_count": len(nonzero_exponents),
        "sparse_bucket": sparse_bucket,
        "exact_block_divisors": exact_divisors,
        "block_summaries": block_summaries,
        "base_polynomials": bases,
        "primary_exact_block_divisor": primary_base.get("divisor") if primary_base else None,
        "primary_base_degree": primary_base.get("base_degree") if primary_base else None,
        "primary_base_polynomial": primary_base.get("base_polynomial") if primary_base else None,
        "claimed_exact_composed_support": claimed_exact,
        "exact_composed_claim_status": _claim_status(claimed_exact, bool(exact_divisors)),
        "structural_family": {
            "square_discriminant": is_square,
            "primary_exact_block_divisor": primary_base.get("divisor") if primary_base else None,
            "primary_base_degree": primary_base.get("base_degree") if primary_base else None,
            "sparse_bucket": sparse_bucket,
            "source_strategy": _strategy(record),
        },
        "exact_galois_label_claimed": False,
        "verified_group_label": None,
        "local_algebra_caveat": SAFETY_NOTE,
    }


def audit_records(
    records: Iterable[dict[str, Any]],
    *,
    block_divisors: Iterable[int] = DEFAULT_BLOCK_DIVISORS,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    audited: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for index, record in enumerate(records, start=1):
        try:
            audited.append(audit_record(record, queue_index=index, block_divisors=block_divisors))
        except StructureAuditError as exc:
            skipped[str(exc)] += 1
    return audited, dict(sorted(skipped.items()))


def _family_groups(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for record in records:
        key = (
            bool(record.get("local_discriminant_is_square")),
            record.get("primary_exact_block_divisor"),
            record.get("primary_base_degree"),
            record.get("sparse_bucket"),
            record.get("source_strategy"),
        )
        group = groups.setdefault(
            key,
            {
                "square_discriminant": key[0],
                "primary_exact_block_divisor": key[1],
                "primary_base_degree": key[2],
                "sparse_bucket": key[3],
                "source_strategy": key[4],
                "count": 0,
                "hashes": [],
            },
        )
        group["count"] += 1
        group["hashes"].append(record.get("canonical_hash"))
    return sorted(groups.values(), key=lambda item: (-int(item["count"]), str(item["source_strategy"]), str(item["primary_exact_block_divisor"])))


def _coverage_buckets(record: dict[str, Any]) -> set[str]:
    buckets = {
        f"square:{bool(record.get('local_discriminant_is_square'))}",
        f"divisor:{record.get('primary_exact_block_divisor')}",
        f"base_degree:{record.get('primary_base_degree')}",
        f"sparse:{record.get('sparse_bucket')}",
        f"strategy:{record.get('source_strategy')}",
    }
    flags = set(record.get("non_generic_flags") or [])
    if "all_sampled_frobenius_even" in flags:
        buckets.add("modular:all_sampled_frobenius_even")
    if "no_long_cycle_witness_in_sample" in flags:
        buckets.add("modular:no_long_cycle_witness_in_sample")
    if "square_discriminant_excludes_s24" in flags:
        buckets.add("claim:square_discriminant")
    if "exact_composed_support" in flags:
        buckets.add("claim:exact_composed_support")
    return buckets


def _priority_value(record: dict[str, Any]) -> tuple[float, float, float, int]:
    return (
        1.0 if record.get("local_discriminant_is_square") else 0.0,
        1.0 if record.get("exact_block_divisors") else 0.0,
        float(record.get("non_generic_score") or record.get("score") or 0.0),
        -int(record.get("queue_index") or 0),
    )


def prioritize_records(records: list[dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    remaining = sorted(records, key=_priority_value, reverse=True)
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    limit = max(0, int(limit))
    while remaining and len(selected) < limit:
        best_index = 0
        best_key: tuple[int, tuple[float, float, float, int]] | None = None
        for index, record in enumerate(remaining):
            new_buckets = _coverage_buckets(record) - covered
            key = (len(new_buckets), _priority_value(record))
            if best_key is None or key > best_key:
                best_key = key
                best_index = index
        record = dict(remaining.pop(best_index))
        new_buckets = sorted(_coverage_buckets(record) - covered)
        covered.update(_coverage_buckets(record))
        record["manual_priority_rank"] = len(selected) + 1
        record["manual_priority_new_coverage"] = new_buckets
        record["manual_priority_reason"] = "covers new structural buckets" if new_buckets else "highest remaining local-structure evidence"
        selected.append(record)
    return selected


def _status_counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter(str(record.get(field)) for record in records)
    return dict(sorted(counts.items()))


def build_summary(
    *,
    input_path: Path,
    records_loaded: int,
    audited: list[dict[str, Any]],
    skipped_counts: dict[str, int],
    priority: list[dict[str, Any]],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    block_divisors: list[int],
) -> dict[str, Any]:
    square_refuted = [record["canonical_hash"] for record in audited if record.get("square_discriminant_claim_status") == "refuted"]
    exact_refuted = [record["canonical_hash"] for record in audited if record.get("exact_composed_claim_status") == "refuted"]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_queue_structure_audit.py",
        "source_commit": source_commit,
        "command": command,
        "input_path": str(input_path),
        "records_loaded": records_loaded,
        "records_audited": len(audited),
        "skipped_counts": skipped_counts,
        "block_divisors": block_divisors,
        "square_discriminant_claim_status_counts": _status_counts(audited, "square_discriminant_claim_status"),
        "exact_composed_claim_status_counts": _status_counts(audited, "exact_composed_claim_status"),
        "square_claim_refuted_hashes": square_refuted,
        "exact_composed_claim_refuted_hashes": exact_refuted,
        "records_with_local_square_discriminant": sum(1 for record in audited if record.get("local_discriminant_is_square")),
        "records_with_exact_composed_support": sum(1 for record in audited if record.get("exact_block_divisors")),
        "strategy_counts": dict(sorted(Counter(record.get("source_strategy") for record in audited).items())),
        "primary_block_divisor_counts": dict(sorted(Counter(str(record.get("primary_exact_block_divisor")) for record in audited).items())),
        "sparse_bucket_counts": dict(sorted(Counter(record.get("sparse_bucket") for record in audited).items())),
        "family_groups": _family_groups(audited),
        "manual_priority_records": len(priority),
        "manual_priority_hashes": [record.get("canonical_hash") for record in priority],
        "output_files": {
            "audit_jsonl": str(output_dir / AUDIT_JSONL),
            "priority_jsonl": str(output_dir / PRIORITY_JSONL),
            "priority_txt": str(output_dir / PRIORITY_TXT),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "safety": {
            "local_exact_algebra_only": True,
            "exact_galois_labels_claimed": False,
            "pari_executed": False,
            "magma_executed": False,
            "sair_submission": False,
            "network_calls": False,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], audited: list[dict[str, Any]], priority: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Queue Structure Audit",
        "",
        SAFETY_NOTE,
        "",
        f"- Input: `{summary.get('input_path')}`",
        f"- Records audited: {summary.get('records_audited')} of {summary.get('records_loaded')}",
        f"- Square-discriminant claim status: `{json.dumps(summary.get('square_discriminant_claim_status_counts', {}), sort_keys=True)}`",
        f"- Exact-composed claim status: `{json.dumps(summary.get('exact_composed_claim_status_counts', {}), sort_keys=True)}`",
        f"- Local square discriminants: {summary.get('records_with_local_square_discriminant')}",
        f"- Local exact composed support: {summary.get('records_with_exact_composed_support')}",
        f"- Strategy counts: `{json.dumps(summary.get('strategy_counts', {}), sort_keys=True)}`",
        f"- Primary block divisor counts: `{json.dumps(summary.get('primary_block_divisor_counts', {}), sort_keys=True)}`",
        f"- Sparse bucket counts: `{json.dumps(summary.get('sparse_bucket_counts', {}), sort_keys=True)}`",
        "",
        "Interpretation:",
        "- These are local algebra checks, not exact Galois labels.",
        "- Square discriminant and exact composed support are confirmed or refuted independently from the proxy diagnostic flags.",
        "- Exact `24Tt` labels still require manual/local exact verification outside this helper.",
        "",
        "## Manual Verification Priority",
        "",
        "| priority | queue | hash | square | divisor | base degree | sparse | strategy | non-generic | reason |",
        "| ---: | ---: | --- | --- | ---: | ---: | --- | --- | ---: | --- |",
    ]
    if not priority:
        lines.append("|  |  |  |  |  |  |  |  |  |  |")
    for record in priority:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(record.get("manual_priority_rank")),
                    str(record.get("queue_index")),
                    f"`{record.get('short_hash')}`",
                    str(record.get("local_discriminant_is_square")),
                    str(record.get("primary_exact_block_divisor") or ""),
                    str(record.get("primary_base_degree") or ""),
                    str(record.get("sparse_bucket") or ""),
                    f"`{record.get('source_strategy')}`",
                    f"{float(record.get('non_generic_score') or 0.0):.3f}",
                    ", ".join(record.get("manual_priority_new_coverage") or []),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Audited Queue",
            "",
            "| queue | hash | square claim | exact claim | divisor | base degree | sparse | flags |",
            "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for record in audited:
        flags = ",".join(record.get("non_generic_flags") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(record.get("queue_index")),
                    f"`{record.get('short_hash')}`",
                    str(record.get("square_discriminant_claim_status")),
                    str(record.get("exact_composed_claim_status")),
                    str(record.get("primary_exact_block_divisor") or ""),
                    str(record.get("primary_base_degree") or ""),
                    str(record.get("sparse_bucket") or ""),
                    flags,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Audit JSONL: `{summary.get('output_files', {}).get('audit_jsonl')}`",
            f"- Priority JSONL: `{summary.get('output_files', {}).get('priority_jsonl')}`",
            f"- Priority hashes: `{summary.get('output_files', {}).get('priority_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def write_outputs(
    *,
    audited: list[dict[str, Any]],
    priority: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / AUDIT_JSONL
    priority_path = output_dir / PRIORITY_JSONL
    priority_txt_path = output_dir / PRIORITY_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    _write_jsonl(audit_path, audited)
    _write_jsonl(priority_path, priority)
    priority_txt_path.write_text(
        "".join(f"{record.get('manual_priority_rank')}\t{record.get('queue_index')}\t{record.get('canonical_hash')}\n" for record in priority),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, audited, priority), encoding="utf-8")
    return {
        "audit_jsonl": audit_path,
        "priority_jsonl": priority_path,
        "priority_txt": priority_txt_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit local algebraic structure for an IGP24 manual verification queue")
    parser.add_argument("queue_input", type=Path, help="Queue verification_batch.jsonl or diagnostic shortlist JSONL")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--priority_limit", type=int, default=10)
    parser.add_argument("--block_divisors", default="2,3,4,6,8,12")
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def _parse_divisors(value: str) -> list[int]:
    out: list[int] = []
    for raw in str(value).split(","):
        raw = raw.strip()
        if not raw:
            continue
        out.append(int(raw))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    input_path = args.queue_input.resolve()
    output_dir = args.output_dir.resolve()
    try:
        block_divisors = _parse_divisors(args.block_divisors)
        records = read_jsonl(input_path)
        audited, skipped = audit_records(records, block_divisors=block_divisors)
    except (FileNotFoundError, ValueError, IGP24Error, StructureAuditError) as exc:
        parser.error(str(exc))

    priority = prioritize_records(audited, limit=args.priority_limit)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_queue_structure_audit.py", *argv]
    summary = build_summary(
        input_path=input_path,
        records_loaded=len(records),
        audited=audited,
        skipped_counts=skipped,
        priority=priority,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        block_divisors=block_divisors,
    )
    paths = write_outputs(audited=audited, priority=priority, summary=summary, output_dir=output_dir)
    print(f"records_loaded\t{len(records)}")
    print(f"records_audited\t{len(audited)}")
    print(f"square_claim_status_counts\t{json.dumps(summary['square_discriminant_claim_status_counts'], sort_keys=True)}")
    print(f"exact_composed_claim_status_counts\t{json.dumps(summary['exact_composed_claim_status_counts'], sort_keys=True)}")
    print(f"priority_records\t{len(priority)}")
    print(f"square_claim_refuted\t{len(summary['square_claim_refuted_hashes'])}")
    print(f"exact_composed_claim_refuted\t{len(summary['exact_composed_claim_refuted_hashes'])}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
