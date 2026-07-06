#!/usr/bin/env python3
"""Join verified IGP24 exact labels back to local structure evidence.

This helper is local/file-only. It reads already-saved structure-audit rows and
already-parsed exact-verifier result rows, joins them by canonical hash, and
writes feedback reports for search planning. It does not call PARI, MAGMA,
SAIR, the online calculator, training, GPU sampling, CPU proxy-search loops,
local search, network APIs, or submission paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl


JOINED_JSONL = "verified_label_feedback.jsonl"
REPRESENTATIVES_JSONL = "verified_label_representatives.jsonl"
SUMMARY_JSON = "verified_label_feedback_summary.json"
REPORT_MD = "verified_label_feedback_report.md"
GENERIC_S24_LABEL = "24T25000"
SAFETY_NOTE = (
    "Verified-label feedback is local/file-only. It joins saved structure "
    "audit rows to saved parsed Magma results, but does not call PARI, MAGMA, "
    "SAIR, the online calculator, training, GPU sampling, CPU proxy-search "
    "loops, local search, network APIs, or submission paths."
)


class FeedbackError(ValueError):
    """Raised when exact-label feedback inputs are inconsistent."""


def _short_hash(value: Any) -> str:
    return str(value or "")[:12]


def _index_by_hash(records: Iterable[dict[str, Any]], *, field: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        key = record.get(field)
        if not isinstance(key, str) or not key:
            continue
        if key in indexed:
            raise FeedbackError(f"duplicate {field}: {key}")
        indexed[key] = record
    return indexed


def _diagnostic_by_hash(records: Iterable[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    return _index_by_hash(records or [], field="canonical_hash")


def _flag_list(record: dict[str, Any]) -> list[str]:
    flags = record.get("non_generic_flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _exported_coefficients(record: dict[str, Any] | None) -> list[int] | None:
    if not record:
        return None
    raw = record.get("exported_coefficients")
    if isinstance(raw, list) and len(raw) == 25 and all(isinstance(item, int) for item in raw):
        return list(raw)
    raw = record.get("coefficients")
    if isinstance(raw, list) and all(isinstance(item, int) for item in raw):
        if len(raw) == 25:
            return list(raw)
        if len(raw) == 24:
            return list(raw) + [1]
    return None


def _coefficient_summary(
    *,
    audit: dict[str, Any],
    diagnostic: dict[str, Any] | None,
) -> dict[str, Any]:
    exported = _exported_coefficients(diagnostic)
    summary = {
        "coefficient_height": audit.get("coefficient_height"),
        "nonzero_exponents": audit.get("nonzero_exponents") or [],
        "nonzero_term_count": audit.get("nonzero_term_count"),
        "primary_base_polynomial": audit.get("primary_base_polynomial"),
    }
    if exported is not None:
        summary["exported_coefficients"] = exported
        summary["free_coefficients"] = exported[:-1]
    return summary


def _family_key(record: dict[str, Any]) -> str:
    square = bool(record.get("local_discriminant_is_square"))
    divisor = record.get("primary_exact_block_divisor")
    base_degree = record.get("primary_base_degree")
    sparse = record.get("sparse_bucket")
    strategy = record.get("source_strategy")
    return f"square={square}|divisor={divisor}|base_degree={base_degree}|sparse={sparse}|strategy={strategy}"


def join_feedback_rows(
    *,
    structure_records: list[dict[str, Any]],
    verification_records: list[dict[str, Any]],
    diagnostic_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audits = _index_by_hash(structure_records, field="canonical_hash")
    diagnostics = _diagnostic_by_hash(diagnostic_records)
    joined: list[dict[str, Any]] = []
    missing_structure: list[str] = []
    non_verified: list[str] = []
    not_degree_24_irreducible: list[str] = []

    for result in verification_records:
        candidate_hash = result.get("candidate_hash")
        if not isinstance(candidate_hash, str) or not candidate_hash:
            continue
        audit = audits.get(candidate_hash)
        if audit is None:
            missing_structure.append(candidate_hash)
            continue
        if result.get("status") != "verified" or not result.get("verified_group_label"):
            non_verified.append(candidate_hash)
            continue
        if result.get("degree") != 24 or result.get("is_irreducible") is not True:
            not_degree_24_irreducible.append(candidate_hash)
        diagnostic = diagnostics.get(candidate_hash)
        label = str(result.get("verified_group_label"))
        row = {
            "schema_version": 1,
            "record_type": "igp24_verified_label_feedback_record",
            "canonical_hash": candidate_hash,
            "short_hash": _short_hash(candidate_hash),
            "queue_index": audit.get("queue_index"),
            "verified_group_label": label,
            "transitive_group_id": result.get("transitive_group_id"),
            "degree": result.get("degree"),
            "is_irreducible": result.get("is_irreducible"),
            "magma_runtime_seconds": result.get("magma_runtime_seconds"),
            "magma_version": result.get("magma_version"),
            "raw_output_source_path": result.get("raw_output_source_path"),
            "local_discriminant_is_square": bool(audit.get("local_discriminant_is_square")),
            "primary_exact_block_divisor": audit.get("primary_exact_block_divisor"),
            "primary_base_degree": audit.get("primary_base_degree"),
            "sparse_bucket": audit.get("sparse_bucket"),
            "source_strategy": audit.get("source_strategy"),
            "non_generic_flags": _flag_list(audit),
            "score": audit.get("score"),
            "non_generic_score": audit.get("non_generic_score"),
            "coefficient_summary": _coefficient_summary(audit=audit, diagnostic=diagnostic),
            "structural_family_key": _family_key(audit),
            "feedback_caveat": SAFETY_NOTE,
        }
        joined.append(row)

    joined.sort(key=lambda row: (int(row.get("queue_index") or 0), str(row.get("canonical_hash") or "")))
    diagnostics_info = {
        "structure_records": len(structure_records),
        "verification_records": len(verification_records),
        "diagnostic_records": len(diagnostic_records or []),
        "joined_records": len(joined),
        "missing_structure_hashes": missing_structure,
        "non_verified_hashes": non_verified,
        "not_degree_24_irreducible_hashes": not_degree_24_irreducible,
    }
    return joined, diagnostics_info


def _nested_label_counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        nested[str(row.get(field))][str(row.get("verified_group_label"))] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(nested.items())}


def _flag_label_counts(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        label = str(row.get("verified_group_label"))
        for flag in row.get("non_generic_flags") or []:
            nested[str(flag)][label] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(nested.items())}


def _block_label_counts(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        key = f"d={row.get('primary_exact_block_divisor')}|base={row.get('primary_base_degree')}"
        nested[key][str(row.get("verified_group_label"))] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(nested.items())}


def _family_label_counts(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        nested[str(row.get("structural_family_key"))][str(row.get("verified_group_label"))] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(nested.items())}


def representative_rows(rows: list[dict[str, Any]], *, per_label: int = 3) -> list[dict[str, Any]]:
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_label[str(row.get("verified_group_label"))].append(row)
    representatives: list[dict[str, Any]] = []
    for label in sorted(by_label):
        ordered = sorted(
            by_label[label],
            key=lambda row: (
                float(row.get("non_generic_score") or 0.0),
                float(row.get("score") or 0.0),
                -int(row.get("queue_index") or 0),
            ),
            reverse=True,
        )
        for rank, row in enumerate(ordered[: max(0, int(per_label))], start=1):
            representatives.append(
                {
                    "verified_group_label": label,
                    "representative_rank": rank,
                    "canonical_hash": row.get("canonical_hash"),
                    "short_hash": row.get("short_hash"),
                    "queue_index": row.get("queue_index"),
                    "score": row.get("score"),
                    "non_generic_score": row.get("non_generic_score"),
                    "local_discriminant_is_square": row.get("local_discriminant_is_square"),
                    "primary_exact_block_divisor": row.get("primary_exact_block_divisor"),
                    "primary_base_degree": row.get("primary_base_degree"),
                    "sparse_bucket": row.get("sparse_bucket"),
                    "source_strategy": row.get("source_strategy"),
                    "coefficient_summary": row.get("coefficient_summary"),
                }
            )
    return representatives


def build_recommendations(summary: dict[str, Any]) -> list[str]:
    label_counts = summary.get("exact_label_counts") or {}
    generic_count = int(label_counts.get(GENERIC_S24_LABEL, 0))
    recommendations: list[str] = []
    if generic_count == 0 and summary.get("verified_records") == summary.get("joined_records"):
        recommendations.append(
            "Treat composed-support structure as a confirmed high-signal family for non-generic exact labels."
        )
    if label_counts.get("24T24970"):
        recommendations.append(
            "Prioritize divisor-2 composed-support/quartic_lift expansions for the square-discriminant 24T24970 family."
        )
    if label_counts.get("24T24979"):
        recommendations.append(
            "Keep a nonsquare divisor-2 composed-support tail to target or monitor 24T24979 separately from 24T24970."
        )
    if label_counts.get("24T24759"):
        recommendations.append(
            "Preserve a small divisor-3/base-degree-8 coverage track for 24T24759."
        )
    recommendations.append(
        "Wire exact-label feedback into shortlist/reporting or generation knobs before starting a larger GPU run."
    )
    recommendations.append(
        "Keep exact labels out of training, GPU sampling, CPU proxy scoring, local search, SAIR, and automatic network paths."
    )
    return recommendations


def build_summary(
    *,
    joined: list[dict[str, Any]],
    representatives: list[dict[str, Any]],
    diagnostics_info: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    structure_path: Path,
    verification_path: Path,
    diagnostic_path: Path | None,
) -> dict[str, Any]:
    label_counts = dict(sorted(Counter(row.get("verified_group_label") for row in joined).items()))
    summary: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_verified_label_feedback.py",
        "source_commit": source_commit,
        "command": command,
        "structure_audit_jsonl": str(structure_path),
        "magma_results_jsonl": str(verification_path),
        "diagnostic_jsonl": str(diagnostic_path) if diagnostic_path else None,
        "joined_records": len(joined),
        "verified_records": sum(1 for row in joined if row.get("verified_group_label")),
        "degree_24_irreducible_records": sum(
            1 for row in joined if row.get("degree") == 24 and row.get("is_irreducible") is True
        ),
        "generic_24T25000_records": label_counts.get(GENERIC_S24_LABEL, 0),
        "exact_label_counts": label_counts,
        "label_by_structural_family": _family_label_counts(joined),
        "label_by_square_discriminant": _nested_label_counts(joined, "local_discriminant_is_square"),
        "label_by_primary_block": _block_label_counts(joined),
        "label_by_source_strategy": _nested_label_counts(joined, "source_strategy"),
        "label_by_sparse_bucket": _nested_label_counts(joined, "sparse_bucket"),
        "label_by_diagnostic_flag": _flag_label_counts(joined),
        "representative_records": representatives,
        "input_diagnostics": diagnostics_info,
        "output_files": {
            "joined_jsonl": str(output_dir / JOINED_JSONL),
            "representatives_jsonl": str(output_dir / REPRESENTATIVES_JSONL),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "safety": {
            "local_file_only": True,
            "pari_executed": False,
            "magma_executed": False,
            "online_calculator_executed": False,
            "network_calls": False,
            "sair_submission": False,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
    }
    summary["recommendations"] = build_recommendations(summary)
    return summary


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _format_counts(counts: Any) -> str:
    return json.dumps(counts or {}, sort_keys=True)


def build_report(summary: dict[str, Any], joined: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Verified Label Feedback",
        "",
        SAFETY_NOTE,
        "",
        f"- Structure audit: `{summary.get('structure_audit_jsonl')}`",
        f"- Magma results: `{summary.get('magma_results_jsonl')}`",
        f"- Diagnostic rows: `{summary.get('diagnostic_jsonl')}`",
        f"- Joined records: {summary.get('joined_records')}",
        f"- Degree-24 irreducible records: {summary.get('degree_24_irreducible_records')}",
        f"- Exact label counts: `{_format_counts(summary.get('exact_label_counts'))}`",
        f"- Generic `{GENERIC_S24_LABEL}` records: {summary.get('generic_24T25000_records')}",
        "",
        "## Exact Labels By Structure",
        "",
        "### Square Discriminant",
        "",
        f"`{_format_counts(summary.get('label_by_square_discriminant'))}`",
        "",
        "### Primary Block",
        "",
        f"`{_format_counts(summary.get('label_by_primary_block'))}`",
        "",
        "### Source Strategy",
        "",
        f"`{_format_counts(summary.get('label_by_source_strategy'))}`",
        "",
        "### Diagnostic Flags",
        "",
        f"`{_format_counts(summary.get('label_by_diagnostic_flag'))}`",
        "",
        "## Representatives",
        "",
        "| label | rank | queue | hash | square | divisor | base degree | sparse | strategy | non-generic | base polynomial |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for record in summary.get("representative_records") or []:
        coeff_summary = record.get("coefficient_summary") or {}
        base_poly = str(coeff_summary.get("primary_base_polynomial") or "").replace("|", "\\|")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(record.get("verified_group_label")),
                    str(record.get("representative_rank")),
                    str(record.get("queue_index")),
                    f"`{record.get('short_hash')}`",
                    str(record.get("local_discriminant_is_square")),
                    str(record.get("primary_exact_block_divisor") or ""),
                    str(record.get("primary_base_degree") or ""),
                    str(record.get("sparse_bucket") or ""),
                    f"`{record.get('source_strategy')}`",
                    f"{float(record.get('non_generic_score') or 0.0):.3f}",
                    base_poly,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Joined Queue",
            "",
            "| queue | hash | label | square | divisor | base degree | sparse | strategy | flags |",
            "| ---: | --- | --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in joined:
        flags = ",".join(row.get("non_generic_flags") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("queue_index")),
                    f"`{row.get('short_hash')}`",
                    str(row.get("verified_group_label")),
                    str(row.get("local_discriminant_is_square")),
                    str(row.get("primary_exact_block_divisor") or ""),
                    str(row.get("primary_base_degree") or ""),
                    str(row.get("sparse_bucket") or ""),
                    f"`{row.get('source_strategy')}`",
                    flags,
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    for recommendation in summary.get("recommendations") or []:
        lines.append(f"- {recommendation}")
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Joined JSONL: `{summary.get('output_files', {}).get('joined_jsonl')}`",
            f"- Representatives JSONL: `{summary.get('output_files', {}).get('representatives_jsonl')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    *,
    joined: list[dict[str, Any]],
    representatives: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    joined_path = output_dir / JOINED_JSONL
    representatives_path = output_dir / REPRESENTATIVES_JSONL
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    _write_jsonl(joined_path, joined)
    _write_jsonl(representatives_path, representatives)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, joined), encoding="utf-8")
    return {
        "joined_jsonl": joined_path,
        "representatives_jsonl": representatives_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Join verified IGP24 exact labels to structure-audit evidence")
    parser.add_argument("--structure_audit_jsonl", type=Path, required=True)
    parser.add_argument("--magma_results_jsonl", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--diagnostic_jsonl", type=Path)
    parser.add_argument("--representatives_per_label", type=int, default=3)
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    structure_path = args.structure_audit_jsonl.resolve()
    verification_path = args.magma_results_jsonl.resolve()
    diagnostic_path = args.diagnostic_jsonl.resolve() if args.diagnostic_jsonl else None
    output_dir = args.output_dir.resolve()
    try:
        structure_records = read_jsonl(structure_path)
        verification_records = read_jsonl(verification_path)
        diagnostic_records = read_jsonl(diagnostic_path) if diagnostic_path else None
        joined, diagnostics_info = join_feedback_rows(
            structure_records=structure_records,
            verification_records=verification_records,
            diagnostic_records=diagnostic_records,
        )
    except (FileNotFoundError, FeedbackError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    representatives = representative_rows(joined, per_label=args.representatives_per_label)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_verified_label_feedback.py", *argv]
    summary = build_summary(
        joined=joined,
        representatives=representatives,
        diagnostics_info=diagnostics_info,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        structure_path=structure_path,
        verification_path=verification_path,
        diagnostic_path=diagnostic_path,
    )
    paths = write_outputs(joined=joined, representatives=representatives, summary=summary, output_dir=output_dir)
    print(f"joined_records\t{summary['joined_records']}")
    print(f"verified_records\t{summary['verified_records']}")
    print(f"degree_24_irreducible_records\t{summary['degree_24_irreducible_records']}")
    print(f"exact_label_counts\t{json.dumps(summary['exact_label_counts'], sort_keys=True)}")
    print(f"generic_24T25000_records\t{summary['generic_24T25000_records']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
