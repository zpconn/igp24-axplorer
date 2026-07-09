#!/usr/bin/env python3
"""Write a read-only construction-family routing report for IGP24.

This helper does not generate candidates, call SAIR, call Magma/PARI/GAP, or
submit anything. It materializes the Phase 5 construction registry and, when a
local group-cycle index is supplied, ranks families against a target label's
declared group invariants.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.constructions.registry import (  # noqa: E402
    ConstructionRegistry,
    default_registry,
    registry_summary,
)
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord  # noqa: E402


FAMILIES_JSON = "construction_registry_families.json"
SUMMARY_JSON = "construction_registry_summary.json"
RANKINGS_JSONL = "construction_family_rankings.jsonl"
REPORT_MD = "construction_registry_report.md"

SAFETY_NOTE = (
    "Read-only construction registry report. It does not generate candidates, "
    "call external algebra systems or SAIR, or recommend live submission."
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def load_target_group(index_path: Path | None, target_label: str | None) -> GroupRecord | None:
    if not index_path or not target_label:
        return None
    index = GroupCycleIndex(index_path)
    records = index.records_for_labels([target_label])
    return records.get(str(target_label))


def build_payloads(
    *,
    registry: ConstructionRegistry,
    target_r: int | None,
    target_label: str | None,
    target_group: GroupRecord | None,
    avoid_labels: list[str],
    top_limit: int,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], str]:
    families_payload = registry.as_json()
    rankings = registry.rank_for_target(
        r_value=target_r,
        group_record=target_group,
        avoid_labels=avoid_labels,
        top_limit=top_limit,
    )
    summary = registry_summary(registry)
    summary.update(
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tool": "scripts/igp24_construction_registry_report.py",
            "source_commit": get_source_commit(REPO_ROOT),
            "safety_note": SAFETY_NOTE,
            "target": {
                "r": target_r,
                "label": target_label,
                "group_record_available": target_group is not None,
                "primitive": target_group.primitive if target_group else None,
                "solvable": target_group.solvable if target_group else None,
                "block_sizes": list(target_group.block_sizes) if target_group else [],
            },
            "avoid_labels": list(avoid_labels),
            "top_ranked_families": [row["family"] for row in rankings[: min(5, len(rankings))]],
            "live_submission_recommended_now": False,
        }
    )
    report = render_report(summary, families_payload, rankings)
    return families_payload, summary, rankings, report


def render_report(
    summary: dict[str, Any],
    families_payload: dict[str, Any],
    rankings: list[dict[str, Any]],
) -> str:
    target = summary["target"]
    lines = [
        "# IGP24 Construction Registry",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Families: `{summary['family_count']}`",
        f"- Exact-label claims: `{summary['exact_label_claimed_count']}`",
        f"- Soundness: `{summary['soundness']}`",
        f"- Safety: {summary['safety_note']}",
        f"- Target label: `{target.get('label')}`",
        f"- Target r: `{target.get('r')}`",
        f"- Target group record available: `{target.get('group_record_available')}`",
        "- Live submission recommended now: `False`",
        "",
        "## Ranked Families",
        "",
        "| rank | family | score | supports r | blocks | warnings |",
        "| ---: | --- | ---: | --- | --- | --- |",
    ]
    for index, row in enumerate(rankings, start=1):
        warnings = ", ".join(row.get("warnings") or []) or "-"
        blocks = ",".join(str(value) for value in row.get("expected_block_sizes") or []) or "-"
        lines.append(
            f"| {index} | `{row['family']}` | {row['routing_score']} | "
            f"`{row['supports_target_r']}` | `{blocks}` | {warnings} |"
        )
    lines.extend(["", "## Registry Families", ""])
    for family in families_payload["families"]:
        lines.extend(
            [
                f"### {family['name']}",
                "",
                f"- Display name: {family['display_name']}",
                f"- Degree pattern: `{family['degree_pattern']}`",
                f"- Expected block sizes: `{family['expected_block_sizes']}`",
                f"- Imprimitive expectation: `{family['imprimitive_expectation']}`",
                f"- Supported r values: `{family['supported_r_values']}`",
                f"- Known collapse labels: `{family['known_collapse_labels']}`",
                f"- Known score-positive pairs: `{family['known_score_positive_pairs']}`",
                f"- Exact-label claimed: `{family['exact_label_claimed']}`",
                f"- Notes: {family['notes']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--target_r", type=int)
    parser.add_argument("--target_label")
    parser.add_argument("--group_index")
    parser.add_argument("--avoid_label", action="append", default=[])
    parser.add_argument("--top_limit", type=int, default=25)
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    registry = default_registry()
    target_group = load_target_group(Path(args.group_index) if args.group_index else None, args.target_label)
    families_payload, summary, rankings, report = build_payloads(
        registry=registry,
        target_r=args.target_r,
        target_label=args.target_label,
        target_group=target_group,
        avoid_labels=list(args.avoid_label or []),
        top_limit=int(args.top_limit),
    )

    write_json(output_dir / FAMILIES_JSON, families_payload)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / RANKINGS_JSONL, rankings)
    (output_dir / REPORT_MD).write_text(report, encoding="utf-8")

    print(f"family_count {summary['family_count']}")
    print(f"exact_label_claimed_count {summary['exact_label_claimed_count']}")
    print(f"top_ranked_families {','.join(summary['top_ranked_families'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
