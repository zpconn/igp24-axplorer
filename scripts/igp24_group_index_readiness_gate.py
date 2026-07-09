#!/usr/bin/env python3
"""Evaluate whether an IGP24 group-cycle index is ready for target routing.

This is a read-only gate. It does not build groups, generate candidates, call
SAIR/Magma/PARI/GAP, or submit anything. It checks whether a local group-cycle
index covers the target labels needed by the score-aware plan, whether
historical true-label containment passes when rows are provided, and whether
construction target routing is unblocked by group invariants.
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

from scripts.igp24_construction_target_router import (  # noqa: E402
    build_routes,
    load_score_plan,
    select_targets,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.group_compatibility import (  # noqa: E402
    GroupCycleIndex,
    read_jsonl,
    validate_historical_containment,
)


DEFAULT_SCORE_PLAN = REPO_ROOT / "data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json"

SUMMARY_JSON = "group_index_readiness_summary.json"
REPORT_MD = "group_index_readiness_report.md"
ROUTES_JSONL = "group_index_readiness_routes.jsonl"

SAFETY_NOTE = (
    "Read-only group-index readiness gate. It does not build groups, generate "
    "candidates, call external algebra systems or SAIR, or recommend live submission."
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def load_historical_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(read_jsonl(path))
    return rows


def index_coverage(index: GroupCycleIndex | None, labels: list[str]) -> dict[str, Any]:
    if index is None:
        return {
            "target_label_count": len(labels),
            "covered_target_label_count": 0,
            "missing_target_labels": labels,
            "group_count": 0,
            "complete": False,
        }
    records = index.records_for_labels(labels)
    missing = [label for label in labels if label not in records]
    return {
        "target_label_count": len(labels),
        "covered_target_label_count": len(records),
        "missing_target_labels": missing,
        "group_count": index.group_count(),
        "complete": not missing,
    }


def build_readiness(
    *,
    index_path: Path | None,
    score_plan_path: Path,
    historical_paths: list[Path],
    progress_path: Path | None,
    output_dir: Path,
    top_targets: int,
    families_per_target: int,
    target_category: str | None,
    avoid_labels: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    score_plan = load_score_plan(score_plan_path)
    targets = select_targets(score_plan, top_targets=top_targets, category=target_category)
    target_labels = []
    for row in targets:
        label = str(row["label"])
        if label not in target_labels:
            target_labels.append(label)

    index_exists = bool(index_path and index_path.exists())
    index = GroupCycleIndex(index_path) if index_exists and index_path is not None else None
    coverage = index_coverage(index, target_labels)
    progress_rows = read_jsonl(progress_path) if progress_path else []
    historical_rows = load_historical_rows(historical_paths)
    containment = None
    if index is not None and historical_rows:
        containment = validate_historical_containment(historical_rows, index, progress_rows=progress_rows)

    routes = build_routes(
        score_plan=score_plan,
        group_index=index,
        avoid_labels=avoid_labels,
        top_targets=top_targets,
        families_per_target=families_per_target,
        category=target_category,
        require_group_invariants=True,
    )
    route_blocks = Counter(reason for row in routes for reason in row.get("blocking_reasons") or [])
    ready_routes = [row for row in routes if row.get("generation_ready")]

    blocking_reasons: list[str] = []
    if not index_exists:
        blocking_reasons.append("missing_group_index")
    if not coverage["complete"]:
        blocking_reasons.append("target_label_coverage_incomplete")
    if not historical_paths:
        blocking_reasons.append("missing_historical_validation_input")
    elif containment is None:
        blocking_reasons.append("historical_validation_not_run")
    elif int(containment.get("failure_count") or 0) != 0:
        blocking_reasons.append("historical_true_label_containment_failed")
    elif containment.get("true_label_containment") != 1.0:
        blocking_reasons.append("historical_true_label_containment_not_100pct")
    if not ready_routes:
        blocking_reasons.append("no_generation_ready_routes")

    summary = {
        "schema_version": 1,
        "record_type": "igp24_group_index_readiness_gate",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_group_index_readiness_gate.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "input_score_plan": str(score_plan_path),
        "input_score_plan_created_at": score_plan.get("created_at"),
        "input_group_index": str(index_path) if index_path else None,
        "group_index_exists": index_exists,
        "historical_inputs": [str(path) for path in historical_paths],
        "progress_input": str(progress_path) if progress_path else None,
        "top_targets_requested": int(top_targets),
        "target_category_filter": target_category,
        "target_pair_count": len(targets),
        "target_labels": target_labels,
        "index_coverage": coverage,
        "historical_row_count": len(historical_rows),
        "historical_containment": containment,
        "route_count": len(routes),
        "generation_ready_route_count": len(ready_routes),
        "generation_ready_target_count": len({str(row["pair_key"]) for row in ready_routes}),
        "route_blocking_reason_counts": dict(sorted(route_blocks.items())),
        "blocking_reasons": blocking_reasons,
        "ready_for_group_directed_generation": not blocking_reasons,
        "live_submission_recommended_now": False,
        "output_files": {
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
            "routes_jsonl": str(output_dir / ROUTES_JSONL),
        },
    }
    return summary, routes


def render_report(summary: dict[str, Any], routes: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Group Index Readiness Gate",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Group index: `{summary['input_group_index']}`",
        f"- Group index exists: `{summary['group_index_exists']}`",
        f"- Target pairs: `{summary['target_pair_count']}`",
        f"- Covered target labels: `{summary['index_coverage']['covered_target_label_count']}` / `{summary['index_coverage']['target_label_count']}`",
        f"- Historical rows: `{summary['historical_row_count']}`",
        f"- Generation-ready routes: `{summary['generation_ready_route_count']}`",
        f"- Blocking reasons: `{summary['blocking_reasons']}`",
        f"- Ready for group-directed generation: `{summary['ready_for_group_directed_generation']}`",
        "- Live submission recommended now: `False`",
        f"- Safety: {summary['safety_note']}",
        "",
    ]
    missing = summary["index_coverage"].get("missing_target_labels") or []
    if missing:
        lines.extend(
            [
                "## Missing Target Labels",
                "",
                ", ".join(f"`{label}`" for label in missing[:100]),
                "",
            ]
        )
    containment = summary.get("historical_containment")
    if containment is not None:
        lines.extend(
            [
                "## Historical Containment",
                "",
                f"- Checked rows: `{containment['checked_count']}`",
                f"- Failure count: `{containment['failure_count']}`",
                f"- True-label containment: `{containment['true_label_containment']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Top Routes",
            "",
            "| rank | pair | family | ready | blocks |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for index, row in enumerate(routes[:25], start=1):
        blocks = ", ".join(row.get("blocking_reasons") or []) or "-"
        lines.append(
            f"| {index} | `{row['pair_key']}` | `{row['family']}` | `{row['generation_ready']}` | {blocks} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], routes: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / ROUTES_JSONL, routes)
    (output_dir / REPORT_MD).write_text(render_report(summary, routes), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--score_plan", type=Path, default=DEFAULT_SCORE_PLAN)
    parser.add_argument("--historical_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--progress_jsonl", type=Path)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--top_targets", type=int, default=25)
    parser.add_argument("--families_per_target", type=int, default=5)
    parser.add_argument("--target_category", default="uncovered_signature")
    parser.add_argument("--avoid_label", action="append", default=[])
    parser.add_argument("--fail_on_block", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary, routes = build_readiness(
        index_path=args.index,
        score_plan_path=args.score_plan,
        historical_paths=list(args.historical_jsonl or []),
        progress_path=args.progress_jsonl,
        output_dir=args.output_dir,
        top_targets=int(args.top_targets),
        families_per_target=int(args.families_per_target),
        target_category=args.target_category or None,
        avoid_labels=list(args.avoid_label or []),
    )
    write_outputs(args.output_dir, summary=summary, routes=routes)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.fail_on_block and summary["blocking_reasons"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
