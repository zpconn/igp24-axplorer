#!/usr/bin/env python3
"""Prepare a provenance-rich r=8 score-followup lane for anti-basin gating."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from scripts.igp24_anti_basin_planner import mod_pattern_signature, support_summary, write_jsonl


REQUIRED_PROVENANCE_FIELDS = [
    "sample_export_source",
    "construction_family",
    "generation_strategy",
    "template_family_id",
    "basin_fingerprint",
    "perturbation_mode",
    "support_pattern",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def coefficient_list(row: dict[str, Any]) -> list[int] | None:
    coeffs = row.get("exported_coefficients") or row.get("coefficients")
    if not isinstance(coeffs, list):
        return None
    try:
        return [int(value) for value in coeffs]
    except (TypeError, ValueError):
        return None


def coefficient_gcd(coeffs: Iterable[int]) -> int:
    result = 0
    for value in coeffs:
        result = math.gcd(result, abs(int(value)))
    return result


def short_digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def coefficient_line(coeffs: list[int] | None) -> str:
    return ",".join(str(int(value)) for value in coeffs or [])


def r8_metadata_value(metadata: dict[str, Any], key: str, default: Any = None) -> Any:
    return metadata.get(f"r8_quartic_lift_{key}", default)


def derive_provenance(row: dict[str, Any], *, source_path: Path, source_signal_pair: str) -> dict[str, Any]:
    metadata = row.get("generation_metadata") if isinstance(row.get("generation_metadata"), dict) else {}
    coeffs = coefficient_list(row)
    support = support_summary(coeffs)
    template_name = str(r8_metadata_value(metadata, "template_name", "unknown_template"))
    mode = str(
        metadata.get("perturbation_mode")
        or r8_metadata_value(metadata, "perturbation_mode")
        or "unknown_perturbation"
    )
    family_key = str(
        r8_metadata_value(metadata, "family_key")
        or metadata.get("family_key")
        or f"{template_name}:{mode}:{coefficient_line(coeffs)}"
    )
    construction_family = str(
        metadata.get("construction_family")
        or metadata.get("source_family")
        or metadata.get("resolved_generation_strategy")
        or metadata.get("strategy")
        or row.get("construction_family")
        or "r8_quartic_lift_perturbed"
    )
    generation_strategy = "r8_score_followup_24T9993"
    support_gcd = metadata.get("support_gcd") or r8_metadata_value(metadata, "support_gcd") or support.get("support_gcd")
    even_support = metadata.get("even_support_like")
    if even_support is None:
        even_support = r8_metadata_value(metadata, "even_support")
    if even_support is None:
        even_support = support.get("even_support")
    support_pattern = f"quartic_in_x6_{mode}_support_gcd{support_gcd or 'unknown'}"
    template_family_id = f"r8_score_followup:{template_name}:{mode}"
    mod_sig = mod_pattern_signature(row) or "modp:none"
    basin_basis = "|".join(
        [
            source_signal_pair,
            construction_family,
            template_name,
            mode,
            family_key,
            str(support_gcd),
            ",".join(str(value) for value in support.get("odd_support_exponents") or []),
            mod_sig,
        ]
    )
    basin_fingerprint = short_digest(basin_basis)
    source_seed_hash = short_digest(f"{source_path}:{row.get('canonical_hash') or coefficient_line(coeffs)}")
    return {
        "sample_export_source": "lane_generate:r8_score_followup",
        "construction_family": construction_family,
        "generation_strategy": generation_strategy,
        "template_family_id": template_family_id,
        "basin_fingerprint": basin_fingerprint,
        "perturbation_mode": mode,
        "support_pattern": support_pattern,
        "support_gcd": int(support_gcd) if support_gcd is not None else None,
        "even_support_like": bool(even_support) if even_support is not None else None,
        "odd_support_exponents": support.get("odd_support_exponents") or [],
        "family_key": family_key,
        "decomposition_pattern": "quartic_in_x6",
        "mod_p_pattern_signature": mod_sig,
        "source_signal_pair": source_signal_pair,
        "source_path": str(source_path),
        "source_seed_hash": source_seed_hash,
    }


def enrich_candidate(row: dict[str, Any], *, source_path: Path, source_signal_pair: str) -> dict[str, Any]:
    provenance = derive_provenance(row, source_path=source_path, source_signal_pair=source_signal_pair)
    metadata = dict(row.get("generation_metadata") or {})
    metadata.update(provenance)
    enriched = dict(row)
    enriched.update(provenance)
    enriched["generation_metadata"] = metadata
    enriched["record_type"] = "igp24_r8_score_followup_candidate"
    return enriched


def rejection_reasons(row: dict[str, Any], *, target_r: int, seen_hashes: set[str], seen_lines: set[str]) -> list[str]:
    reasons: list[str] = []
    coeffs = coefficient_list(row)
    line = coefficient_line(coeffs)
    if coeffs is None or len(coeffs) != 25:
        reasons.append("missing_25_integer_coefficients")
    else:
        if coeffs[0] == 0:
            reasons.append("zero_constant_coefficient")
        if coeffs[-1] != 1:
            reasons.append("not_monic_degree_24")
        if coefficient_gcd(coeffs) != 1:
            reasons.append("coefficient_gcd_not_one")
    try:
        r_value = int(row.get("real_root_count", row.get("r")))
    except (TypeError, ValueError):
        r_value = None
    if r_value != target_r:
        reasons.append("real_root_count_not_target")
    if row.get("irreducible") is False:
        reasons.append("not_irreducible")
    if row.get("squarefree") is False:
        reasons.append("not_squarefree")
    if row.get("valid") is False:
        reasons.append("local_valid_false")
    if row.get("canonical_hash") and row.get("canonical_hash") in seen_hashes:
        reasons.append("duplicate_canonical_hash")
    if line and line in seen_lines:
        reasons.append("duplicate_coefficient_line")
    missing = [field for field in REQUIRED_PROVENANCE_FIELDS if not row.get(field)]
    if missing:
        reasons.append("missing_required_provenance:" + ",".join(missing))
    return reasons


def prepare_lane(
    rows_by_path: list[tuple[Path, dict[str, Any]]],
    *,
    target_r: int,
    source_signal_pair: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    seen_lines: set[str] = set()
    for source_path, row in rows_by_path:
        enriched = enrich_candidate(row, source_path=source_path, source_signal_pair=source_signal_pair)
        reasons = rejection_reasons(enriched, target_r=target_r, seen_hashes=seen_hashes, seen_lines=seen_lines)
        if reasons:
            rejected_row = dict(enriched)
            rejected_row["lane_rejection_reasons"] = reasons
            rejected.append(rejected_row)
            continue
        accepted.append(enriched)
        if enriched.get("canonical_hash"):
            seen_hashes.add(str(enriched["canonical_hash"]))
        line = coefficient_line(coefficient_list(enriched))
        if line:
            seen_lines.add(line)
    summary = {
        "record_type": "igp24_r8_score_followup_lane_summary",
        "source_signal_pair": source_signal_pair,
        "target_r": target_r,
        "input_rows": len(rows_by_path),
        "accepted_rows": len(accepted),
        "rejected_rows": len(rejected),
        "unique_canonical_hashes": len({row.get("canonical_hash") for row in accepted if row.get("canonical_hash")}),
        "template_family_counts": dict(Counter(str(row.get("template_family_id")) for row in accepted)),
        "basin_fingerprint_count": len({row.get("basin_fingerprint") for row in accepted if row.get("basin_fingerprint")}),
        "perturbation_mode_counts": dict(Counter(str(row.get("perturbation_mode")) for row in accepted)),
        "mod_p_signature_counts": dict(Counter(str(row.get("mod_p_pattern_signature")) for row in accepted)),
        "rejection_reason_counts": dict(Counter(reason for row in rejected for reason in row.get("lane_rejection_reasons", []))),
        "required_provenance_fields": REQUIRED_PROVENANCE_FIELDS,
    }
    return accepted, rejected, summary


def build_report(summary: dict[str, Any], output_files: dict[str, str]) -> str:
    lines = [
        "# r8 Score-Followup Lane",
        "",
        f"- Source signal pair: `{summary['source_signal_pair']}`",
        f"- Target r: `{summary['target_r']}`",
        f"- Input rows: `{summary['input_rows']}`",
        f"- Accepted lane rows: `{summary['accepted_rows']}`",
        f"- Rejected rows: `{summary['rejected_rows']}`",
        f"- Template families: `{json.dumps(summary['template_family_counts'], sort_keys=True)}`",
        f"- Basin fingerprints: `{summary['basin_fingerprint_count']}`",
        f"- Perturbation modes: `{json.dumps(summary['perturbation_mode_counts'], sort_keys=True)}`",
        f"- Mod-p signatures: `{json.dumps(summary['mod_p_signature_counts'], sort_keys=True)}`",
        f"- Rejection reasons: `{json.dumps(summary['rejection_reason_counts'], sort_keys=True)}`",
        "",
        "## Outputs",
    ]
    for name, path in output_files.items():
        lines.append(f"- {name}: `{path}`")
    lines.append("")
    lines.append("This lane-prep step does not call SAIR and does not claim exact labels.")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a provenance-rich r8 score-followup lane")
    parser.add_argument("--candidate_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_r", type=int, default=8)
    parser.add_argument("--source_signal_pair", default="24T9993|r=8")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows_by_path: list[tuple[Path, dict[str, Any]]] = []
    for path in args.candidate_jsonl:
        rows_by_path.extend((path, row) for row in read_jsonl(path))
    accepted, rejected, summary = prepare_lane(
        rows_by_path,
        target_r=int(args.target_r),
        source_signal_pair=str(args.source_signal_pair),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "candidate_jsonl": str(args.output_dir / "r8_score_followup_candidates.jsonl"),
        "rejected_jsonl": str(args.output_dir / "r8_score_followup_rejected.jsonl"),
        "summary_json": str(args.output_dir / "r8_score_followup_lane_summary.json"),
        "report_md": str(args.output_dir / "r8_score_followup_lane_report.md"),
    }
    write_jsonl(Path(output_files["candidate_jsonl"]), accepted)
    write_jsonl(Path(output_files["rejected_jsonl"]), rejected)
    summary = {
        **summary,
        "candidate_paths": [str(path) for path in args.candidate_jsonl],
        "output_files": output_files,
        "command": [sys.executable, "scripts/igp24_r8_score_followup_lane.py", *(argv or sys.argv[1:])],
    }
    Path(output_files["summary_json"]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(output_files["report_md"]).write_text(build_report(summary, output_files), encoding="utf-8")
    print(f"input_rows\t{summary['input_rows']}")
    print(f"accepted_rows\t{summary['accepted_rows']}")
    print(f"rejected_rows\t{summary['rejected_rows']}")
    print(f"candidate_jsonl\t{output_files['candidate_jsonl']}")
    print(f"summary_json\t{output_files['summary_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
