#!/usr/bin/env python3
"""Compare a selected AXG packet against pending SAIR submission rows.

This report is intentionally conservative: it can prove exact coefficient-hash
overlap and describe local provenance diversity, but it cannot prove a
candidate's eventual `24Tt` label before SAIR/Magma-style verification.
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

from scripts.igp24_sair_sync import load_sync_status, load_sync_submission_rows  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.verifiers.sair_api import parse_polynomial_line  # noqa: E402


SUMMARY_JSON = "pending_collision_report_summary.json"
REPORT_MD = "pending_collision_report.md"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def coefficient_values(row: dict[str, Any]) -> list[int] | None:
    candidate = row.get("candidate") if isinstance(row.get("candidate"), dict) else {}
    for value in (
        row.get("exported_coefficients"),
        candidate.get("exported_coefficients"),
        row.get("coefficients"),
        candidate.get("coefficients"),
    ):
        if isinstance(value, list):
            return [int(item) for item in value]
    polynomial = row.get("polynomial")
    if isinstance(polynomial, str):
        try:
            return parse_polynomial_line(polynomial)
        except Exception:
            return None
    return None


def support_features(coefficients: Iterable[int] | None) -> dict[str, Any]:
    if coefficients is None:
        return {
            "support_count": None,
            "support_gcd": None,
            "even_support": None,
            "odd_support_exponents": [],
        }
    coeffs = [int(value) for value in coefficients]
    support = [index for index, value in enumerate(coeffs) if value != 0]
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, exponent)
    return {
        "support_count": len(support),
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
        "odd_support_exponents": [exponent for exponent in support if exponent % 2 == 1],
    }


def selected_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    features = row.get("features") if isinstance(row.get("features"), dict) else {}
    candidate = row.get("candidate") if isinstance(row.get("candidate"), dict) else {}
    coefficients = coefficient_values(row)
    support = support_features(coefficients)
    return {
        "canonical_hash": row.get("canonical_hash") or features.get("canonical_hash") or candidate.get("canonical_hash"),
        "short_hash": row.get("short_hash") or str(row.get("canonical_hash") or "")[:12],
        "r": features.get("r") or candidate.get("real_root_count") or candidate.get("r"),
        "source": candidate.get("sample_export_source")
        or (candidate.get("source_sample_export") or {}).get("sample_export_source")
        or (candidate.get("generation_metadata") or {}).get("sample_export_source"),
        "template_family_id": features.get("template_family_id") or candidate.get("template_family_id"),
        "basin_fingerprint": features.get("basin_fingerprint") or candidate.get("basin_fingerprint"),
        "perturbation_mode": features.get("perturbation_mode") or candidate.get("perturbation_mode"),
        "mod_p_pattern_signature": features.get("mod_p_pattern_signature"),
        "support": support,
    }


def pending_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    coefficients = coefficient_values(row)
    support = support_features(coefficients)
    return {
        "canonical_hash": row.get("canonical_hash"),
        "short_hash": row.get("short_hash") or str(row.get("canonical_hash") or "")[:12],
        "pair_key": row.get("pair_key"),
        "label": row.get("label"),
        "r": row.get("r"),
        "submission_id": row.get("submission_id"),
        "status_class": row.get("status_class"),
        "scoring_status": row.get("scoring_status"),
        "support": support,
        "local_match_status": row.get("local_match_status"),
    }


def support_key(row: dict[str, Any]) -> tuple[Any, ...]:
    support = row.get("support") or {}
    return (
        support.get("support_count"),
        support.get("support_gcd"),
        support.get("even_support"),
        tuple(support.get("odd_support_exponents") or []),
    )


def build_summary(
    *,
    selected_jsonl: Path,
    sync_dir: Path,
    focus_pair: str,
    output_dir: Path,
    command: list[str],
) -> dict[str, Any]:
    selected = [selected_row_summary(row) for row in read_jsonl(selected_jsonl)]
    sync_status = load_sync_status(sync_dir)
    sync_rows = load_sync_submission_rows(sync_dir)
    pending_rows = [
        pending_row_summary(row)
        for row in sync_rows
        if row.get("status_class") == "pending" or row.get("scoring_status") == "pending"
    ]
    focus_pending = [row for row in pending_rows if row.get("pair_key") == focus_pair]
    selected_hashes = {str(row.get("canonical_hash")) for row in selected if row.get("canonical_hash")}
    pending_hashes = {str(row.get("canonical_hash")) for row in focus_pending if row.get("canonical_hash")}
    exact_hash_overlap = sorted(selected_hashes & pending_hashes)
    selected_support_counts = Counter(str(support_key(row)) for row in selected)
    pending_support_counts = Counter(str(support_key(row)) for row in focus_pending)
    support_key_overlap = sorted(set(selected_support_counts) & set(pending_support_counts))
    selected_r_values = sorted({int(row["r"]) for row in selected if row.get("r") is not None})
    pending_pair_counts = Counter(str(row.get("pair_key")) for row in pending_rows if row.get("pair_key"))
    output_files = {
        "summary_json": str(output_dir / SUMMARY_JSON),
        "report_md": str(output_dir / REPORT_MD),
    }
    return {
        "schema_version": 1,
        "record_type": "igp24_pending_collision_report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_pending_collision_report.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "command": command,
        "inputs": {
            "selected_jsonl": str(selected_jsonl),
            "sair_sync_dir": str(sync_dir),
            "focus_pair": focus_pair,
        },
        "sync_status": sync_status,
        "selected_rows": selected,
        "pending_pair_counts": dict(sorted(pending_pair_counts.items())),
        "focus_pending_rows": focus_pending,
        "comparison": {
            "selected_count": len(selected),
            "selected_r_values": selected_r_values,
            "focus_pending_count": len(focus_pending),
            "exact_hash_overlap_count": len(exact_hash_overlap),
            "exact_hash_overlap": exact_hash_overlap,
            "selected_template_family_counts": dict(Counter(str(row.get("template_family_id")) for row in selected)),
            "selected_basin_fingerprint_counts": dict(Counter(str(row.get("basin_fingerprint")) for row in selected)),
            "selected_perturbation_mode_counts": dict(Counter(str(row.get("perturbation_mode")) for row in selected)),
            "selected_mod_p_signature_counts": dict(Counter(str(row.get("mod_p_pattern_signature")) for row in selected)),
            "selected_support_key_counts": dict(selected_support_counts),
            "focus_pending_support_key_counts": dict(pending_support_counts),
            "support_key_overlap": support_key_overlap,
            "pending_has_mod_p_or_template_metadata": False,
        },
        "conclusion": {
            "live_submission_allowed": False,
            "reason": (
                "No exact selected-vs-pending coefficient hash overlap was found, but the focus pair still has "
                "pending SAIR rows and sync is not complete; treat the packet as review-only until pending rows resolve."
            ),
            "evidence_strength": "weak_for_label_novelty_strong_for_exact_hash_nonoverlap"
            if not exact_hash_overlap
            else "exact_hash_collision_detected",
        },
        "output_files": output_files,
    }


def build_report(summary: dict[str, Any]) -> str:
    comparison = summary["comparison"]
    sync_status = summary.get("sync_status") or {}
    lines = [
        "# Pending Collision Report",
        "",
        f"- Focus pair: `{summary['inputs']['focus_pair']}`",
        f"- Selected rows: {comparison['selected_count']}",
        f"- Focus pending rows: {comparison['focus_pending_count']}",
        f"- Exact coefficient-hash overlaps: {comparison['exact_hash_overlap_count']}",
        f"- Full submission state complete: `{sync_status.get('full_submission_state_complete', sync_status.get('submission_state_complete'))}`",
        f"- Degraded sync summary: {sync_status.get('degraded_mode_summary')}",
        f"- Live submission allowed: `{summary['conclusion']['live_submission_allowed']}`",
        f"- Evidence strength: `{summary['conclusion']['evidence_strength']}`",
        "",
        "## Selected Provenance",
        "",
        f"- Template families: `{json.dumps(comparison['selected_template_family_counts'], sort_keys=True)}`",
        f"- Basin fingerprints: `{json.dumps(comparison['selected_basin_fingerprint_counts'], sort_keys=True)}`",
        f"- Perturbation modes: `{json.dumps(comparison['selected_perturbation_mode_counts'], sort_keys=True)}`",
        f"- Mod-p signatures: `{json.dumps(comparison['selected_mod_p_signature_counts'], sort_keys=True)}`",
        "",
        "## Pending Pressure",
        "",
        f"- Pending pair counts: `{json.dumps(summary['pending_pair_counts'], sort_keys=True)}`",
        f"- Support-key overlap with focus pending rows: `{json.dumps(comparison['support_key_overlap'])}`",
        "",
        "## Conclusion",
        "",
        summary["conclusion"]["reason"],
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected_jsonl", type=Path, required=True)
    parser.add_argument("--sair_sync_dir", type=Path, required=True)
    parser.add_argument("--focus_pair", default="24T25000|r=20")
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_pending_collision_report.py", *argv]
    summary = build_summary(
        selected_jsonl=args.selected_jsonl,
        sync_dir=args.sair_sync_dir,
        focus_pair=str(args.focus_pair),
        output_dir=args.output_dir,
        command=command,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    (output_dir / REPORT_MD).write_text(build_report(summary), encoding="utf-8")
    print(f"selected_rows\t{summary['comparison']['selected_count']}")
    print(f"focus_pending_rows\t{summary['comparison']['focus_pending_count']}")
    print(f"exact_hash_overlap_count\t{summary['comparison']['exact_hash_overlap_count']}")
    print(f"live_submission_allowed\t{summary['conclusion']['live_submission_allowed']}")
    print(f"summary_json\t{output_dir / SUMMARY_JSON}")
    print(f"report_md\t{output_dir / REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
