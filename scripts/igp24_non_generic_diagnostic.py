#!/usr/bin/env python3
"""Rank IGP24 candidates by proxy evidence for non-generic Galois behavior.

This helper is file-only and proxy-only. It reads existing ledger/review rows,
uses already recorded discriminants, modular factorization patterns, and
coefficient structure, then writes an auditable shortlist for later exact
verification. It never calls PARI, MAGMA, SAIR, network APIs, or submission
paths.
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

from scripts.igp24_shortlist import get_source_commit, load_records, parse_csv, resolve_ledger_paths


DIAGNOSTIC_JSONL = "non_generic_diagnostic.jsonl"
SHORTLIST_JSONL = "non_generic_shortlist.jsonl"
COEFFICIENTS_TXT = "non_generic_coefficients.txt"
SUMMARY_JSON = "non_generic_summary.json"
REPORT_MD = "non_generic_report.md"

DEGREE = 24
DEFAULT_BLOCK_DIVISORS = (2, 3, 4, 6, 8, 12)
SAFETY_NOTE = (
    "Proxy-only non-generic diagnostic. No exact Galois label is claimed, and "
    "no PARI, MAGMA, SAIR, network API, training loop, GPU sampler, CPU hot "
    "loop, local search, or submission path is used."
)


class DiagnosticError(ValueError):
    """Raised when a candidate record cannot be diagnosed."""


def _coerce_int_list(value: Any) -> list[int] | None:
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        return None
    return list(value)


def record_coefficients(record: dict[str, Any]) -> list[int] | None:
    """Return [a0, ..., a23] coefficients from common candidate record shapes."""

    raw = _coerce_int_list(record.get("coefficients"))
    if raw is not None and len(raw) == DEGREE:
        return raw
    raw = _coerce_int_list(record.get("decoded_coefficients"))
    if raw is not None and len(raw) == DEGREE:
        return raw
    raw = _coerce_int_list(record.get("exported_coefficients"))
    if raw is not None and len(raw) == DEGREE + 1 and raw[-1] == 1:
        return raw[:-1]
    return None


def _strategy(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    return str(metadata.get("strategy") or record.get("source_strategy") or "missing")


def _is_valid_proxy_record(record: dict[str, Any]) -> bool:
    if record.get("valid") is False:
        return False
    status = str(record.get("verification_status") or "")
    if status == "rejected":
        return False
    if record.get("rejection_reason"):
        return False
    return record_coefficients(record) is not None and bool(record.get("canonical_hash"))


def _is_square_discriminant(discriminant: Any) -> bool:
    if not isinstance(discriminant, int) or discriminant < 0:
        return False
    root = math.isqrt(discriminant)
    return root * root == discriminant


def _near_square_scaled_gap(discriminant: Any) -> float | None:
    if not isinstance(discriminant, int) or discriminant <= 0:
        return None
    root = math.isqrt(discriminant)
    lower_gap = abs(discriminant - root * root)
    upper_gap = abs((root + 1) * (root + 1) - discriminant)
    gap = min(lower_gap, upper_gap)
    return float(gap / max(1, 2 * root + 1))


def _nonzero_exponents(coefficients: list[int]) -> list[int]:
    exponents = [index for index, coeff in enumerate(coefficients) if coeff != 0]
    exponents.append(DEGREE)
    return sorted(set(exponents))


def block_structure_evidence(
    coefficients: list[int],
    *,
    block_divisors: Iterable[int] = DEFAULT_BLOCK_DIVISORS,
) -> dict[str, Any]:
    """Describe exact/near support in x^d for divisors d of 24."""

    exponents = _nonzero_exponents(coefficients)
    summaries: list[dict[str, Any]] = []
    for divisor in block_divisors:
        divisor = int(divisor)
        if divisor <= 1 or DEGREE % divisor:
            continue
        off_block = [exponent for exponent in exponents if exponent % divisor != 0]
        summaries.append(
            {
                "divisor": divisor,
                "off_block_terms": len(off_block),
                "off_block_exponents": off_block,
                "exact_composed_support": len(off_block) == 0,
            }
        )
    best = min(summaries, key=lambda item: (int(item["off_block_terms"]), -int(item["divisor"]))) if summaries else None
    exact = [item["divisor"] for item in summaries if item["exact_composed_support"]]
    return {
        "nonzero_exponents": exponents,
        "nonzero_term_count": len(exponents),
        "exact_block_divisors": exact,
        "best_near_block_divisor": best["divisor"] if best else None,
        "best_near_block_off_terms": best["off_block_terms"] if best else None,
        "best_near_block_off_exponents": best["off_block_exponents"] if best else [],
        "block_summaries": summaries,
    }


def _pattern_degrees(pattern: Any) -> list[int]:
    if not isinstance(pattern, dict):
        return []
    degrees = pattern.get("degrees")
    if not isinstance(degrees, list):
        return []
    out: list[int] = []
    for value in degrees:
        try:
            out.append(int(value))
        except (TypeError, ValueError):
            return []
    return out


def modular_evidence(record: dict[str, Any]) -> dict[str, Any]:
    patterns = record.get("mod_p_factorization_degree_patterns") or []
    parity_counts: Counter[str] = Counter()
    degree_patterns: list[list[int]] = []
    has_long_cycle_witness = False
    for pattern in patterns:
        degrees = _pattern_degrees(pattern)
        if not degrees:
            continue
        degree_patterns.append(degrees)
        parity = "odd" if (DEGREE - len(degrees)) % 2 else "even"
        parity_counts[parity] += 1
        if degrees == [DEGREE] or (len(degrees) == 2 and sorted(degrees) == [1, DEGREE - 1]):
            has_long_cycle_witness = True
    sampled = sum(parity_counts.values())
    return {
        "sampled_unramified_primes": sampled,
        "frobenius_parity_counts": dict(sorted(parity_counts.items())),
        "all_sampled_frobenius_even": sampled > 0 and parity_counts.get("odd", 0) == 0,
        "has_odd_frobenius_witness": parity_counts.get("odd", 0) > 0,
        "has_long_cycle_witness": has_long_cycle_witness,
        "degree_patterns": degree_patterns,
    }


def diagnose_record(
    record: dict[str, Any],
    *,
    block_divisors: Iterable[int] = DEFAULT_BLOCK_DIVISORS,
) -> dict[str, Any]:
    coefficients = record_coefficients(record)
    if coefficients is None:
        raise DiagnosticError("missing coefficient vector")
    discriminant = record.get("discriminant")
    square_discriminant = _is_square_discriminant(discriminant)
    near_square_gap = _near_square_scaled_gap(discriminant)
    block = block_structure_evidence(coefficients, block_divisors=block_divisors)
    modular = modular_evidence(record)

    flags: list[str] = []
    score = 0.0
    if square_discriminant:
        flags.append("square_discriminant_excludes_s24")
        score += 1000.0
    if near_square_gap is not None and near_square_gap < 1e-6:
        flags.append("very_near_square_discriminant")
        score += 120.0
    elif near_square_gap is not None and near_square_gap < 1e-3:
        flags.append("near_square_discriminant")
        score += 40.0
    if block["exact_block_divisors"]:
        flags.append("exact_composed_support")
        score += 500.0 + 25.0 * len(block["exact_block_divisors"])
    off_terms = block.get("best_near_block_off_terms")
    if isinstance(off_terms, int):
        if off_terms <= 2:
            flags.append("near_composed_support")
            score += 180.0 / (1.0 + off_terms)
        elif off_terms <= 4:
            flags.append("weak_near_composed_support")
            score += 60.0 / off_terms
    term_count = int(block["nonzero_term_count"])
    if term_count <= 6:
        flags.append("very_sparse_support")
        score += 80.0
    elif term_count <= 10:
        flags.append("sparse_support")
        score += 30.0
    if modular["all_sampled_frobenius_even"]:
        flags.append("all_sampled_frobenius_even")
        score += 60.0
    if not modular["has_long_cycle_witness"]:
        flags.append("no_long_cycle_witness_in_sample")
        score += 20.0
    log_disc = record.get("log_abs_discriminant")
    if isinstance(log_disc, (int, float)):
        score += max(0.0, 100.0 - float(log_disc)) * 0.25

    return {
        "canonical_hash": record.get("canonical_hash"),
        "score": record.get("score"),
        "non_generic_score": round(score, 6),
        "non_generic_flags": flags,
        "real_root_count": record.get("real_root_count"),
        "source_strategy": _strategy(record),
        "source_ledger_path": record.get("source_ledger_path"),
        "exported_coefficients": record.get("exported_coefficients") or coefficients + [1],
        "coefficient_height": record.get("coefficient_height"),
        "log_abs_discriminant": record.get("log_abs_discriminant"),
        "verification_status": record.get("verification_status", "proxy_scored"),
        "verified_group_label": None,
        "non_generic_evidence": {
            "square_discriminant": square_discriminant,
            "near_square_scaled_gap": near_square_gap,
            "block_structure": block,
            "modular_factorization": modular,
        },
        "proxy_only_caveat": SAFETY_NOTE,
    }


def diagnose_records(
    records: Iterable[dict[str, Any]],
    *,
    target_r: int | None = None,
    strategies: set[str] | None = None,
    block_divisors: Iterable[int] = DEFAULT_BLOCK_DIVISORS,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    diagnostics: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    seen: set[str] = set()
    for record in records:
        if not _is_valid_proxy_record(record):
            skipped["invalid_or_missing_coefficients"] += 1
            continue
        if target_r is not None and record.get("real_root_count") != target_r:
            skipped["target_r_mismatch"] += 1
            continue
        if strategies and _strategy(record) not in strategies:
            skipped["strategy_mismatch"] += 1
            continue
        canonical_hash = str(record.get("canonical_hash"))
        if canonical_hash in seen:
            skipped["duplicate_canonical_hash"] += 1
            continue
        seen.add(canonical_hash)
        try:
            diagnostics.append(diagnose_record(record, block_divisors=block_divisors))
        except DiagnosticError as exc:
            skipped[str(exc)] += 1
    diagnostics.sort(key=lambda item: (float(item["non_generic_score"]), float(item.get("score") or 0.0)), reverse=True)
    return diagnostics, dict(sorted(skipped.items()))


def _flag_counts(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        counts.update(record.get("non_generic_flags") or [])
    return dict(sorted(counts.items()))


def build_summary(
    *,
    input_paths: list[Path],
    ledger_paths: list[Path],
    diagnostics: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    skipped_counts: dict[str, int],
    output_dir: Path,
    filters: dict[str, Any],
    command: list[str],
    source_commit: str | None,
) -> dict[str, Any]:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_non_generic_diagnostic.py",
        "source_commit": source_commit,
        "command": command,
        "input_paths": [str(path) for path in input_paths],
        "resolved_ledger_paths": [str(path) for path in ledger_paths],
        "records_diagnosed": len(diagnostics),
        "selected_records": len(selected),
        "skipped_counts": skipped_counts,
        "filters": filters,
        "top_non_generic_score": selected[0]["non_generic_score"] if selected else None,
        "strategy_counts": dict(sorted(Counter(record.get("source_strategy") for record in selected).items())),
        "flag_counts": _flag_counts(selected),
        "output_files": {
            "diagnostic_jsonl": str(output_dir / DIAGNOSTIC_JSONL),
            "shortlist_jsonl": str(output_dir / SHORTLIST_JSONL),
            "coefficients_txt": str(output_dir / COEFFICIENTS_TXT),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "safety": {
            "proxy_only": True,
            "exact_group_claims": False,
            "verifier_executed": False,
            "network_calls": False,
            "sair_submission": False,
            "submission_executed": False,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Non-Generic Galois Proxy Diagnostic",
        "",
        SAFETY_NOTE,
        "",
        f"- Records diagnosed: {summary.get('records_diagnosed')}",
        f"- Selected records: {summary.get('selected_records')}",
        f"- Top non-generic proxy score: {summary.get('top_non_generic_score')}",
        f"- Strategy counts: `{json.dumps(summary.get('strategy_counts', {}), sort_keys=True)}`",
        f"- Flag counts: `{json.dumps(summary.get('flag_counts', {}), sort_keys=True)}`",
        "",
        "| rank | non-generic | proxy score | hash | r | strategy | flags | block | log disc |",
        "| ---: | ---: | ---: | --- | ---: | --- | --- | --- | ---: |",
    ]
    for rank, record in enumerate(selected, start=1):
        evidence = record.get("non_generic_evidence") or {}
        block = evidence.get("block_structure") or {}
        flags = ",".join(record.get("non_generic_flags") or [])
        score = record.get("score")
        score_text = f"{float(score):.6f}" if score is not None else ""
        log_disc = record.get("log_abs_discriminant")
        log_disc_text = f"{float(log_disc):.3f}" if log_disc is not None else ""
        block_text = f"d={block.get('best_near_block_divisor')}, off={block.get('best_near_block_off_terms')}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    f"{float(record.get('non_generic_score') or 0.0):.3f}",
                    score_text,
                    f"`{str(record.get('canonical_hash') or '')[:12]}`",
                    str(record.get("real_root_count") if record.get("real_root_count") is not None else ""),
                    f"`{record.get('source_strategy')}`",
                    flags,
                    block_text,
                    log_disc_text,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "- These rows are not exact Galois labels. They are candidates whose recorded proxy data make generic `S_24` less attractive than ordinary high-score ranking.",
            "- `exact_composed_support` and `square_discriminant_excludes_s24` are stronger structural signals; `near_composed_support`, sparse support, and missing modular generic witnesses are triage signals.",
            "",
            "Artifacts:",
            f"- Diagnostic JSONL: `{summary.get('output_files', {}).get('diagnostic_jsonl')}`",
            f"- Shortlist JSONL: `{summary.get('output_files', {}).get('shortlist_jsonl')}`",
            f"- Coefficients TXT: `{summary.get('output_files', {}).get('coefficients_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(selected: list[dict[str, Any]], diagnostics: list[dict[str, Any]], output_dir: Path, summary: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_path = output_dir / DIAGNOSTIC_JSONL
    shortlist_path = output_dir / SHORTLIST_JSONL
    coefficients_path = output_dir / COEFFICIENTS_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD

    with diagnostic_path.open("w", encoding="utf-8") as handle:
        for record in diagnostics:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with shortlist_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with coefficients_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(record.get("exported_coefficients"), separators=(",", ":")) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, selected), encoding="utf-8")
    return {
        "diagnostic_jsonl": diagnostic_path,
        "shortlist_jsonl": shortlist_path,
        "coefficients_txt": coefficients_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a proxy-only IGP24 non-generic Galois diagnostic shortlist")
    parser.add_argument("inputs", nargs="+", type=Path, help="Ledger JSONL files, benchmark summary.json files, or benchmark directories")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_r", type=int, default=None, help="Keep only records with this real-root count")
    parser.add_argument("--strategies", default=None, help="Comma-separated generation strategy filter")
    parser.add_argument("--limit", type=int, default=25, help="Maximum diagnostic shortlist rows")
    parser.add_argument("--block_divisors", default="2,3,4,6,8,12", help="Comma-separated divisors of 24 used for composed-support checks")
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    input_paths = [path.resolve() for path in args.inputs]
    output_dir = args.output_dir.resolve()
    strategies = set(parse_csv(args.strategies))
    try:
        block_divisors = [int(value) for value in parse_csv(args.block_divisors)]
        ledger_paths = resolve_ledger_paths(input_paths)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    records = load_records(ledger_paths)
    diagnostics, skipped = diagnose_records(
        records,
        target_r=args.target_r,
        strategies=strategies or None,
        block_divisors=block_divisors,
    )
    selected = diagnostics[: max(0, int(args.limit))]
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_non_generic_diagnostic.py", *argv]
    summary = build_summary(
        input_paths=input_paths,
        ledger_paths=ledger_paths,
        diagnostics=diagnostics,
        selected=selected,
        skipped_counts=skipped,
        output_dir=output_dir,
        filters={
            "target_r": args.target_r,
            "strategies": sorted(strategies),
            "limit": args.limit,
            "block_divisors": block_divisors,
            "deduplicate_by": "canonical_hash",
        },
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
    )
    paths = write_outputs(selected, diagnostics, output_dir, summary)
    print(f"loaded_records\t{len(records)}")
    print(f"diagnosed_records\t{len(diagnostics)}")
    print(f"selected_records\t{len(selected)}")
    print(f"top_non_generic_score\t{summary['top_non_generic_score'] if summary['top_non_generic_score'] is not None else 'NA'}")
    print(f"flag_counts\t{json.dumps(summary['flag_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
