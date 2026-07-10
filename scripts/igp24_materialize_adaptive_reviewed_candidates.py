#!/usr/bin/env python3
"""Materialize candidates with stronger adaptive Frobenius review.

This read-only helper merges an adaptive Frobenius benchmark artifact back
into candidate rows, recomputes group compatibility from the reviewed modular
patterns, and emits a candidate JSONL suitable for the packet optimizer.
It does not call SAIR, use network access, verify exact labels, or submit.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.adaptive_frobenius import compatibility_for_patterns  # noqa: E402
from src.igp24.group_compatibility import GroupCycleIndex, read_jsonl, write_json, write_jsonl  # noqa: E402

SUMMARY_JSON = "adaptive_reviewed_candidates_summary.json"
CANDIDATES_JSONL = "adaptive_reviewed_candidates.jsonl"
REJECTED_JSONL = "adaptive_reviewed_candidates_rejected.jsonl"
REPORT_MD = "adaptive_reviewed_candidates_report.md"


def _patterns(adaptive_row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"prime": int(item["prime"]), "degrees": [int(value) for value in item["degrees"]]}
        for item in adaptive_row.get("mod_p_factorization_degree_patterns") or []
    ]


def review_candidate(
    candidate: dict[str, Any],
    adaptive_row: dict[str, Any],
    compatibility: dict[str, Any],
    *,
    minimum_usable_primes: int,
) -> dict[str, Any]:
    reviewed = dict(candidate)
    target_label = str(
        candidate.get("route", {}).get("label")
        or candidate.get("target_metadata", {}).get("target_t")
        or candidate.get("label")
        or candidate.get("verified_group_label")
        or ""
    )
    target_pair = str(
        candidate.get("route", {}).get("pair_key")
        or candidate.get("pair_key")
        or (
            f"{target_label}|r={candidate.get('real_root_count')}"
            if target_label and candidate.get("real_root_count") not in (None, "")
            else ""
        )
    )
    survivor_labels = set(str(label) for label in compatibility.get("indexed_target_labels_not_ruled_out") or [])
    valuable_pairs = set(str(pair) for pair in compatibility.get("valuable_targets_not_ruled_out") or [])
    usable_prime_count = int(adaptive_row.get("usable_prime_count") or len(_patterns(adaptive_row)))
    reviewed["group_compatibility"] = compatibility
    reviewed["adaptive_frobenius"] = {
        **(candidate.get("adaptive_frobenius") if isinstance(candidate.get("adaptive_frobenius"), dict) else {}),
        "review_source": "adaptive_frobenius_benchmark_materialized",
        "usable_prime_count": usable_prime_count,
        "primes_examined": adaptive_row.get("primes_examined"),
        "skipped_ramified_primes": adaptive_row.get("skipped_ramified_primes") or [],
        "observations": adaptive_row.get("observations") or [],
        "mod_p_factorization_degree_patterns": _patterns(adaptive_row),
        "final_compatibility": compatibility,
        "runtime_seconds": adaptive_row.get("runtime_seconds"),
    }
    reviewed["mod_p_factorization_degree_patterns"] = _patterns(adaptive_row)
    reviewed["frobenius_usable_prime_count"] = usable_prime_count
    reviewed["sufficient_adaptive_frobenius_evidence"] = usable_prime_count >= int(minimum_usable_primes)
    reviewed["target_label_not_ruled_out"] = bool(target_label and target_label in survivor_labels)
    reviewed["target_pair_valuable_not_ruled_out"] = bool(target_pair and target_pair in valuable_pairs)
    reviewed["any_valuable_target_not_ruled_out"] = bool(valuable_pairs)
    reviewed["adaptive_review"] = {
        "source_row_index": adaptive_row.get("row_index"),
        "source_short_hash": adaptive_row.get("short_hash"),
        "usable_prime_count": usable_prime_count,
        "final_indexed_target_survivor_count": compatibility.get("indexed_target_survivor_count"),
        "final_valuable_target_count": len(valuable_pairs),
        "minimum_usable_primes": int(minimum_usable_primes),
        "soundness": "necessary_target_exclusion_only_not_exact_label_verification",
    }
    reviewed["eligible_for_packet"] = bool(reviewed["sufficient_adaptive_frobenius_evidence"] and valuable_pairs)
    reviewed["live_submission_recommended_now"] = False
    if not reviewed["sufficient_adaptive_frobenius_evidence"]:
        reviewed["submission_recommendation"] = "false_insufficient_adaptive_evidence"
    elif not valuable_pairs:
        reviewed["submission_recommendation"] = "false_no_valuable_targets_not_ruled_out"
    elif target_pair and target_pair in valuable_pairs and reviewed["target_label_not_ruled_out"]:
        reviewed["submission_recommendation"] = "offline_review_only_target_compatible"
    else:
        reviewed["submission_recommendation"] = "offline_review_only_non_target_valuable_compatibility"
    return reviewed


def materialize(
    candidates: list[dict[str, Any]],
    adaptive_rows: list[dict[str, Any]],
    *,
    index: GroupCycleIndex,
    progress_rows: list[dict[str, Any]],
    minimum_usable_primes: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    adaptive_by_hash = {str(row.get("canonical_hash")): row for row in adaptive_rows if row.get("canonical_hash")}
    reviewed: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for candidate in candidates:
        canonical_hash = str(candidate.get("canonical_hash") or "")
        adaptive_row = adaptive_by_hash.get(canonical_hash)
        if adaptive_row is None:
            rejected.append({**candidate, "adaptive_review_rejection_reason": "missing_adaptive_review_row"})
            continue
        patterns = _patterns(adaptive_row)
        if len(patterns) < int(minimum_usable_primes):
            rejected.append({**candidate, "adaptive_review_rejection_reason": "insufficient_reviewed_patterns"})
            continue
        compatibility = compatibility_for_patterns(candidate, patterns, index, progress_rows)
        reviewed.append(
            review_candidate(
                candidate,
                adaptive_row,
                compatibility,
                minimum_usable_primes=int(minimum_usable_primes),
            )
        )
    return reviewed, rejected


def summarize(
    *,
    candidates: list[dict[str, Any]],
    reviewed: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    output_dir: Path,
    minimum_usable_primes: int,
    candidate_jsonl: Path,
    adaptive_rows_jsonl: Path,
    index_path: Path,
    progress_jsonl: Path | None,
) -> dict[str, Any]:
    valuable_counts = Counter()
    for row in reviewed:
        for pair in (row.get("group_compatibility") or {}).get("valuable_targets_not_ruled_out") or []:
            valuable_counts[str(pair)] += 1
    return {
        "record_type": "igp24_adaptive_reviewed_candidates",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_materialize_adaptive_reviewed_candidates.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety": {
            "calls_sair": False,
            "uses_network": False,
            "submits": False,
            "exact_label_verification": False,
        },
        "inputs": {
            "candidate_jsonl": str(candidate_jsonl),
            "adaptive_rows_jsonl": str(adaptive_rows_jsonl),
            "index": str(index_path),
            "progress_jsonl": str(progress_jsonl) if progress_jsonl else None,
            "minimum_usable_primes": int(minimum_usable_primes),
        },
        "input_candidate_count": len(candidates),
        "reviewed_candidate_count": len(reviewed),
        "rejected_candidate_count": len(rejected),
        "eligible_for_packet_count": sum(1 for row in reviewed if row.get("eligible_for_packet")),
        "target_compatible_count": sum(
            1
            for row in reviewed
            if row.get("target_label_not_ruled_out") and row.get("target_pair_valuable_not_ruled_out")
        ),
        "any_valuable_target_count": sum(1 for row in reviewed if row.get("any_valuable_target_not_ruled_out")),
        "median_indexed_target_survivor_count": (
            sorted(
                int((row.get("group_compatibility") or {}).get("indexed_target_survivor_count") or 0)
                for row in reviewed
            )[len(reviewed) // 2]
            if reviewed
            else None
        ),
        "valuable_target_frequency_top20": valuable_counts.most_common(20),
        "rejection_reason_counts": dict(Counter(str(row.get("adaptive_review_rejection_reason")) for row in rejected)),
        "live_submission_recommended_now": False,
        "submission_recommendation": "false_offline_compatibility_only",
        "output_files": {
            "summary_json": str(output_dir / SUMMARY_JSON),
            "candidates_jsonl": str(output_dir / CANDIDATES_JSONL),
            "rejected_jsonl": str(output_dir / REJECTED_JSONL),
            "report_md": str(output_dir / REPORT_MD),
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Adaptive-Reviewed Candidates",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Input candidates: `{summary['input_candidate_count']}`",
        f"- Reviewed candidates: `{summary['reviewed_candidate_count']}`",
        f"- Rejected candidates: `{summary['rejected_candidate_count']}`",
        f"- Eligible for packet: `{summary['eligible_for_packet_count']}`",
        f"- Target compatible: `{summary['target_compatible_count']}`",
        f"- Any valuable target: `{summary['any_valuable_target_count']}`",
        f"- Median indexed survivors: `{summary['median_indexed_target_survivor_count']}`",
        f"- Live submission recommended now: `{summary['live_submission_recommended_now']}`",
        "",
        "Compatibility remains necessary target-exclusion evidence only; it is not exact label verification.",
        "",
        "## Top Valuable Target Frequencies",
        "",
    ]
    for pair, count in summary["valuable_target_frequency_top20"]:
        lines.append(f"- `{pair}`: {count}")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], reviewed: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / CANDIDATES_JSONL, reviewed)
    write_jsonl(output_dir / REJECTED_JSONL, rejected)
    (output_dir / REPORT_MD).write_text(render_report(summary), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_jsonl", type=Path, required=True)
    parser.add_argument("--adaptive_rows_jsonl", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--progress_jsonl", type=Path)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--minimum_usable_primes", type=int, default=40)
    args = parser.parse_args(argv)

    candidates = read_jsonl(args.candidate_jsonl)
    adaptive_rows = read_jsonl(args.adaptive_rows_jsonl)
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl and args.progress_jsonl.exists() else []
    index = GroupCycleIndex(args.index)
    reviewed, rejected = materialize(
        candidates,
        adaptive_rows,
        index=index,
        progress_rows=progress_rows,
        minimum_usable_primes=int(args.minimum_usable_primes),
    )
    summary = summarize(
        candidates=candidates,
        reviewed=reviewed,
        rejected=rejected,
        output_dir=args.output_dir,
        minimum_usable_primes=int(args.minimum_usable_primes),
        candidate_jsonl=args.candidate_jsonl,
        adaptive_rows_jsonl=args.adaptive_rows_jsonl,
        index_path=args.index,
        progress_jsonl=args.progress_jsonl,
    )
    write_outputs(args.output_dir, summary=summary, reviewed=reviewed, rejected=rejected)
    print(f"input_candidate_count\t{summary['input_candidate_count']}")
    print(f"reviewed_candidate_count\t{summary['reviewed_candidate_count']}")
    print(f"eligible_for_packet_count\t{summary['eligible_for_packet_count']}")
    print(f"target_compatible_count\t{summary['target_compatible_count']}")
    print(f"any_valuable_target_count\t{summary['any_valuable_target_count']}")
    print(f"live_submission_recommended_now\t{summary['live_submission_recommended_now']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
