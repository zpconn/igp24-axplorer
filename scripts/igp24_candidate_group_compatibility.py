#!/usr/bin/env python3
"""Annotate IGP24 candidates with group-cycle compatibility evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.igp24.group_compatibility import (  # noqa: E402
    GroupCycleIndex,
    candidate_compatibility,
    read_jsonl,
    summarize_compatibility,
    utc_now,
    validate_historical_containment,
    write_json,
    write_jsonl,
)

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/remediation_20260709/group_compatibility_phase3"
DEFAULT_INDEX = DEFAULT_OUTPUT_DIR / "degree24_group_cycle_index.sqlite"


def write_report(path: Path, summary: dict[str, Any], containment: dict[str, Any] | None) -> None:
    lines = [
        "# IGP24 Group Compatibility Report",
        "",
        f"- Created UTC: `{summary['created_at']}`",
        f"- Rows: `{summary['row_count']}`",
        f"- Status counts: `{json.dumps(summary['compatibility_summary']['status_counts'], sort_keys=True)}`",
        f"- Median indexed-target survivor count: `{summary['compatibility_summary']['median_indexed_target_survivor_count']}`",
        f"- Fraction below 100 labels: `{summary['compatibility_summary']['fraction_below_100']}`",
        f"- Crowded-only count: `{summary['compatibility_summary']['crowded_only_count']}`",
        "",
        "Compatibility is necessary target-exclusion evidence only. With an incomplete index, unindexed true labels remain possible.",
        "",
    ]
    if containment is not None:
        lines.extend(
            [
                "## Historical Containment",
                "",
                f"- Checked rows: `{containment['checked_count']}`",
                f"- Failure count: `{containment['failure_count']}`",
                f"- True-label containment: `{containment['true_label_containment']}`",
                f"- True labels outside index: `{containment.get('true_label_outside_index_count')}`",
                f"- Median indexed-target survivor count: `{containment['median_indexed_target_survivor_count']}`",
                "",
            ]
        )
        if containment["failures"]:
            lines.extend(
                [
                    "Containment failures block submission use of this compatibility index.",
                    "",
                    "| label | r | hash | status | compatible count |",
                    "| --- | ---: | --- | --- | ---: |",
                ]
            )
            for row in containment["failures"][:20]:
                lines.append(
                    f"| `{row['label']}` | {row.get('r')} | `{row.get('canonical_hash')}` | "
                    f"`{row.get('status')}` | {row.get('compatible_label_count')} |"
                )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--input_jsonl", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--progress_jsonl", type=Path)
    parser.add_argument("--historical_validation", action="store_true")
    parser.add_argument("--low_team_threshold", type=int, default=20)
    parser.add_argument("--crowded_team_threshold", type=int, default=21)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.index.exists():
        raise FileNotFoundError(f"group cycle index not found: {args.index}")
    rows = read_jsonl(args.input_jsonl)
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl else []
    index = GroupCycleIndex(args.index)
    annotated: list[dict[str, Any]] = []
    for row in rows:
        compatibility = candidate_compatibility(
            row,
            index,
            progress_rows=progress_rows,
            low_team_threshold=args.low_team_threshold,
            crowded_team_threshold=args.crowded_team_threshold,
        )
        annotated.append({**row, "group_compatibility": compatibility})

    compatibility_summary = summarize_compatibility(annotated)
    containment = (
        validate_historical_containment(rows, index, progress_rows=progress_rows)
        if args.historical_validation
        else None
    )
    summary = {
        "schema_version": 1,
        "record_type": "igp24_candidate_group_compatibility_summary",
        "created_at": utc_now(),
        "index": str(args.index),
        "input_jsonl": str(args.input_jsonl),
        "row_count": len(rows),
        "compatibility_summary": compatibility_summary,
        "historical_containment": containment,
        "soundness": "necessary_condition_only",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "candidate_group_compatibility_rows.jsonl", annotated)
    write_json(args.output_dir / "candidate_group_compatibility_summary.json", summary)
    write_report(args.output_dir / "candidate_group_compatibility_report.md", summary, containment)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if containment and containment["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
