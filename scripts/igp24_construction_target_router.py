#!/usr/bin/env python3
"""Route valuable IGP24 target pairs to structurally plausible families.

This is the Phase 5 bridge between the score-aware target planner and the
construction-family registry. It is read-only: it does not generate
polynomials, call SAIR, call Magma/PARI/GAP, or submit anything.

Routes are generation-ready only when target group invariants are available
from a group-cycle index. Without that index, family rankings are proxy audit
metadata and must not be treated as target-group compatibility.
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
from src.igp24.constructions.registry import SOUNDNESS_NOTE, default_registry  # noqa: E402
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord  # noqa: E402


DEFAULT_SCORE_PLAN = REPO_ROOT / "data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json"

SUMMARY_JSON = "construction_target_router_summary.json"
ROUTES_JSONL = "construction_target_routes.jsonl"
REPORT_MD = "construction_target_router_report.md"

SAFETY_NOTE = (
    "Read-only target-to-construction router. It does not generate candidates, "
    "call external algebra systems or SAIR, or recommend live submission."
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def load_score_plan(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("record_type") != "igp24_score_aware_target_plan":
        raise ValueError(f"unexpected score-plan record_type in {path}")
    return payload


def open_group_index(path: Path | None) -> GroupCycleIndex | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(path)
    return GroupCycleIndex(path)


def group_for_label(index: GroupCycleIndex | None, label: str) -> GroupRecord | None:
    if index is None:
        return None
    return index.records_for_labels([label]).get(label)


def select_targets(score_plan: dict[str, Any], *, top_targets: int, category: str | None) -> list[dict[str, Any]]:
    rows = [row for row in score_plan.get("ranked_targets") or [] if isinstance(row, dict) and row.get("pair_key")]
    if category:
        rows = [row for row in rows if row.get("category") == category]
    return rows[: int(top_targets)]


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def route_status_and_blocks(
    *,
    target_group: GroupRecord | None,
    family_rank: dict[str, Any],
    require_group_invariants: bool,
) -> tuple[bool, list[str]]:
    blocks: list[str] = []
    if require_group_invariants and target_group is None:
        blocks.append("missing_group_invariants")
    if not family_rank.get("supports_target_r"):
        blocks.append("unsupported_target_r")
    if "forced_imprimitive_family_for_primitive_target" in (family_rank.get("warnings") or []):
        blocks.append("forced_imprimitive_family_for_primitive_target")
    if "likely_solvable_family_for_nonsolvable_target" in (family_rank.get("warnings") or []):
        blocks.append("likely_solvable_family_for_nonsolvable_target")
    return not blocks, blocks


def build_routes(
    *,
    score_plan: dict[str, Any],
    group_index: GroupCycleIndex | None,
    avoid_labels: list[str],
    top_targets: int,
    families_per_target: int,
    category: str | None = "uncovered_signature",
    require_group_invariants: bool = True,
) -> list[dict[str, Any]]:
    registry = default_registry()
    targets = select_targets(score_plan, top_targets=top_targets, category=category)
    routes: list[dict[str, Any]] = []
    for target_rank, target in enumerate(targets, start=1):
        label = str(target["label"])
        r_value = int(target["r"])
        group = group_for_label(group_index, label)
        family_ranks = registry.rank_for_target(
            r_value=r_value,
            group_record=group,
            avoid_labels=avoid_labels,
            top_limit=families_per_target,
        )
        for family_rank, family in enumerate(family_ranks, start=1):
            ready, blocks = route_status_and_blocks(
                target_group=group,
                family_rank=family,
                require_group_invariants=require_group_invariants,
            )
            target_score = _safe_float(target.get("target_score"))
            maximum_points = _safe_float(target.get("maximum_possible_points"))
            combined_score = target_score + 0.25 * _safe_float(family.get("routing_score")) + 250.0 * maximum_points
            routes.append(
                {
                    "target_rank": target_rank,
                    "family_rank": family_rank,
                    "pair_key": target["pair_key"],
                    "label": label,
                    "t": int(target.get("t") or label.removeprefix("24T")),
                    "r": r_value,
                    "target_category": target.get("category"),
                    "progress_state": target.get("progress_state"),
                    "target_score": target.get("target_score"),
                    "maximum_possible_points": target.get("maximum_possible_points"),
                    "estimated_expected_points": target.get("estimated_expected_points"),
                    "score_ceiling_class": target.get("score_ceiling_class"),
                    "signature_team_count": target.get("signature_team_count"),
                    "family": family["family"],
                    "family_display_name": family["display_name"],
                    "family_routing_score": family["routing_score"],
                    "combined_priority_score": round(combined_score, 6),
                    "supports_target_r": family["supports_target_r"],
                    "expected_block_sizes": family["expected_block_sizes"],
                    "imprimitive_expectation": family["imprimitive_expectation"],
                    "primitive_target_fit": family["primitive_target_fit"],
                    "solvability_bias": family["solvability_bias"],
                    "known_collapse_labels": family["known_collapse_labels"],
                    "known_score_positive_pairs": family["known_score_positive_pairs"],
                    "family_reasons": family["reasons"],
                    "family_warnings": family["warnings"],
                    "target_group_record_available": group is not None,
                    "target_group_primitive": group.primitive if group else None,
                    "target_group_solvable": group.solvable if group else None,
                    "target_group_block_sizes": list(group.block_sizes) if group else [],
                    "generation_ready": ready,
                    "blocking_reasons": blocks,
                    "live_submission_recommended_now": False,
                    "soundness": SOUNDNESS_NOTE,
                }
            )
    routes.sort(
        key=lambda row: (
            bool(row["generation_ready"]),
            _safe_float(row["combined_priority_score"]),
            -int(row["target_rank"]),
            -int(row["family_rank"]),
        ),
        reverse=True,
    )
    return routes


def summarize_routes(
    *,
    score_plan_path: Path,
    group_index_path: Path | None,
    score_plan: dict[str, Any],
    routes: list[dict[str, Any]],
    avoid_labels: list[str],
    top_targets: int,
    families_per_target: int,
    category: str | None,
    require_group_invariants: bool,
) -> dict[str, Any]:
    target_pairs = {str(row["pair_key"]) for row in routes}
    targets_with_group = {str(row["pair_key"]) for row in routes if row.get("target_group_record_available")}
    blocks = Counter(reason for row in routes for reason in row.get("blocking_reasons") or [])
    families = Counter(str(row["family"]) for row in routes)
    ready_routes = [row for row in routes if row.get("generation_ready")]
    return {
        "record_type": "igp24_construction_target_router",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_construction_target_router.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "soundness": SOUNDNESS_NOTE,
        "input_score_plan": str(score_plan_path),
        "input_score_plan_created_at": score_plan.get("created_at"),
        "input_group_index": str(group_index_path) if group_index_path else None,
        "group_index_provided": group_index_path is not None,
        "require_group_invariants": require_group_invariants,
        "target_category_filter": category,
        "top_targets_requested": int(top_targets),
        "families_per_target": int(families_per_target),
        "avoid_labels": list(avoid_labels),
        "target_pair_count": len(target_pairs),
        "route_count": len(routes),
        "target_group_record_hit_count": len(targets_with_group),
        "target_group_record_missing_count": len(target_pairs) - len(targets_with_group),
        "generation_ready_route_count": len(ready_routes),
        "generation_ready_target_count": len({str(row["pair_key"]) for row in ready_routes}),
        "blocking_reason_counts": dict(sorted(blocks.items())),
        "family_route_counts": dict(sorted(families.items())),
        "top_generation_ready_routes": [
            {
                "pair_key": row["pair_key"],
                "family": row["family"],
                "combined_priority_score": row["combined_priority_score"],
            }
            for row in ready_routes[:10]
        ],
        "top_proxy_routes": [
            {
                "pair_key": row["pair_key"],
                "family": row["family"],
                "combined_priority_score": row["combined_priority_score"],
                "blocking_reasons": row["blocking_reasons"],
            }
            for row in routes[:10]
        ],
        "live_submission_recommended_now": False,
    }


def render_report(summary: dict[str, Any], routes: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Construction Target Router",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Score plan: `{summary['input_score_plan']}`",
        f"- Group index provided: `{summary['group_index_provided']}`",
        f"- Require group invariants: `{summary['require_group_invariants']}`",
        f"- Target pairs: `{summary['target_pair_count']}`",
        f"- Routes: `{summary['route_count']}`",
        f"- Target group records found: `{summary['target_group_record_hit_count']}`",
        f"- Generation-ready routes: `{summary['generation_ready_route_count']}`",
        f"- Blocking reasons: `{summary['blocking_reason_counts']}`",
        f"- Soundness: `{summary['soundness']}`",
        f"- Safety: {summary['safety_note']}",
        "- Live submission recommended now: `False`",
        "",
        "## Top Routes",
        "",
        "| rank | pair | family | combined score | ready | blocks | warnings |",
        "| ---: | --- | --- | ---: | --- | --- | --- |",
    ]
    for index, row in enumerate(routes[:25], start=1):
        blocks = ", ".join(row.get("blocking_reasons") or []) or "-"
        warnings = ", ".join(row.get("family_warnings") or []) or "-"
        lines.append(
            f"| {index} | `{row['pair_key']}` | `{row['family']}` | "
            f"{row['combined_priority_score']} | `{row['generation_ready']}` | {blocks} | {warnings} |"
        )
    if summary["target_group_record_missing_count"]:
        lines.extend(
            [
                "",
                "## Interpretation",
                "",
                "Routes blocked by `missing_group_invariants` are proxy routing rows only. They show which "
                "construction families would be plausible by real-root count and history, but they are not "
                "evidence that the family can hit the target 24T label.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], routes: list[dict[str, Any]]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / SUMMARY_JSON
    routes_path = output_dir / ROUTES_JSONL
    report_path = output_dir / REPORT_MD
    write_json(summary_path, summary)
    write_jsonl(routes_path, routes)
    report_path.write_text(render_report(summary, routes), encoding="utf-8")
    return {"summary_json": summary_path, "routes_jsonl": routes_path, "report_md": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score_plan", default=str(DEFAULT_SCORE_PLAN))
    parser.add_argument("--group_index")
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--top_targets", type=int, default=25)
    parser.add_argument("--families_per_target", type=int, default=5)
    parser.add_argument("--target_category", default="uncovered_signature")
    parser.add_argument("--avoid_label", action="append", default=[])
    parser.add_argument(
        "--allow_proxy_without_group_index",
        action="store_true",
        help="Mark routes ready without target group invariants. Intended only for diagnostics.",
    )
    args = parser.parse_args(argv)

    score_plan_path = Path(args.score_plan)
    group_index_path = Path(args.group_index) if args.group_index else None
    score_plan = load_score_plan(score_plan_path)
    group_index = open_group_index(group_index_path)
    require_group_invariants = not bool(args.allow_proxy_without_group_index)
    routes = build_routes(
        score_plan=score_plan,
        group_index=group_index,
        avoid_labels=list(args.avoid_label or []),
        top_targets=int(args.top_targets),
        families_per_target=int(args.families_per_target),
        category=args.target_category or None,
        require_group_invariants=require_group_invariants,
    )
    summary = summarize_routes(
        score_plan_path=score_plan_path,
        group_index_path=group_index_path,
        score_plan=score_plan,
        routes=routes,
        avoid_labels=list(args.avoid_label or []),
        top_targets=int(args.top_targets),
        families_per_target=int(args.families_per_target),
        category=args.target_category or None,
        require_group_invariants=require_group_invariants,
    )
    write_outputs(Path(args.output_dir), summary=summary, routes=routes)

    print(f"target_pair_count {summary['target_pair_count']}")
    print(f"route_count {summary['route_count']}")
    print(f"generation_ready_route_count {summary['generation_ready_route_count']}")
    print(f"blocking_reason_counts {json.dumps(summary['blocking_reason_counts'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
