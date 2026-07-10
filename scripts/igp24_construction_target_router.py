#!/usr/bin/env python3
"""Route valuable IGP24 target pairs to structurally plausible families.

This is the Phase 5 bridge between the score-aware target planner and the
construction-family registry. It is read-only: it does not generate
polynomials, call SAIR, call Magma/PARI/GAP, or submit anything.

Routes are structurally eligible only when target group invariants are
available from a group-cycle index and the registry family is not ruled out by
those invariants. That is still not generation-ready: a generation-ready route
must also have an executable target-bound generator, demonstrated structure
preservation, instantiated parameters, and local/adaptive checks on generated
outputs.
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
from src.igp24.constructions.generators import generation_status_for_route  # noqa: E402
from src.igp24.constructions.registry import SOUNDNESS_NOTE, default_registry  # noqa: E402
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord, progress_states_for_pairs  # noqa: E402
from src.igp24.scoring import official_score_economics  # noqa: E402


DEFAULT_SCORE_PLAN = REPO_ROOT / "data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json"

ROOT_BUCKET_WEIGHTS = {
    24: 72.0,
    20: 62.0,
    16: 68.0,
    12: 70.0,
    8: 76.0,
    6: 24.0,
    4: 22.0,
    2: 18.0,
    0: 28.0,
}

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


def load_progress_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if not isinstance(row, dict):
                raise ValueError(f"unexpected non-object progress row in {path}:{line_number}")
            rows.append(row)
    return rows


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


def _target_rows_for_category(score_plan: dict[str, Any], category: str | None) -> list[dict[str, Any]]:
    source_keys = ["ranked_targets"]
    if category:
        source_keys.extend(
            [
                "top_uncovered_targets",
                "top_score_followup_targets",
                "top_api_scoreable_targets",
                "top_api_pending_targets",
                "top_lightly_solved_targets",
            ]
        )
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for source_key in source_keys:
        for row in score_plan.get(source_key) or []:
            if not isinstance(row, dict) or not row.get("pair_key"):
                continue
            dedupe_key = (str(row["pair_key"]), row.get("category"))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            rows.append(row)
    return rows


def _all_target_rows(score_plan: dict[str, Any]) -> list[dict[str, Any]]:
    source_keys = [
        "ranked_targets",
        "top_uncovered_targets",
        "top_score_followup_targets",
        "top_api_scoreable_targets",
        "top_api_pending_targets",
        "top_lightly_solved_targets",
    ]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_key in source_keys:
        for row in score_plan.get(source_key) or []:
            if not isinstance(row, dict) or not row.get("pair_key"):
                continue
            pair = str(row["pair_key"])
            if pair in seen:
                continue
            seen.add(pair)
            rows.append(row)
    return rows


def select_targets(score_plan: dict[str, Any], *, top_targets: int, category: str | None) -> list[dict[str, Any]]:
    rows = _target_rows_for_category(score_plan, category)
    if category:
        rows = [row for row in rows if row.get("category") == category]
    return rows[: int(top_targets)]


def parse_pair_key(pair_key: str) -> tuple[str, int]:
    if "|r=" not in pair_key:
        raise ValueError(f"invalid pair key {pair_key!r}; expected 24Tt|r=n")
    label, r_text = pair_key.split("|r=", 1)
    if not label.startswith("24T") or not label.removeprefix("24T").isdigit():
        raise ValueError(f"invalid degree-24 label in pair key {pair_key!r}")
    try:
        r_value = int(r_text)
    except ValueError as exc:
        raise ValueError(f"invalid real-root count in pair key {pair_key!r}") from exc
    return label, r_value


def _explicit_row_from_progress(pair_key: str, progress_state: dict[str, Any]) -> dict[str, Any]:
    label, r_value = parse_pair_key(pair_key)
    state = str(progress_state.get("progress_state") or "progress_data_missing_unknown")
    score_value_status = str(progress_state.get("score_value_status") or "unknown_no_score_value")
    team_count = int(progress_state.get("team_count") or 0)
    uncovered = state == "allowed_remaining"
    baseline_pair = bool(progress_state.get("in_baseline", False))
    if state in {"allowed_remaining", "allowed_discovered"}:
        official = official_score_economics(
            current_team_count=team_count,
            uncovered=uncovered,
            baseline_pair=baseline_pair,
            current_best_disc_abs=progress_state.get("minimum_disc_abs"),
        )
        maximum_points = official["maximum_possible_points"]
        estimated_points = official["estimated_expected_points"]
        ceiling_class = official["score_ceiling_class"]
    else:
        official = {
            "official_current_team_count": team_count,
            "official_prospective_team_count": None,
            "score_multiplier": None,
            "maximum_possible_points": 0.0,
            "estimated_expected_points": None,
            "estimated_points_basis": "no_score_value",
            "score_ceiling_class": score_value_status,
        }
        maximum_points = 0.0
        estimated_points = None
        ceiling_class = score_value_status

    if state == "allowed_remaining":
        category = "explicit_uncovered_signature"
    elif state == "allowed_discovered":
        category = "explicit_low_team_signature" if team_count <= 20 else "explicit_discovered_signature"
    elif state == "signature_not_allowed":
        category = "explicit_signature_not_allowed"
    else:
        category = "explicit_progress_unknown"

    target_score = ROOT_BUCKET_WEIGHTS.get(r_value, 10.0)
    target_score += min(float(maximum_points or 0.0) * 260.0, 320.0)
    if state == "allowed_remaining":
        target_score += 520.0
    elif state == "allowed_discovered" and team_count <= 5:
        target_score += 160.0
    elif state == "allowed_discovered" and team_count <= 12:
        target_score += 105.0
    elif state == "allowed_discovered" and team_count <= 20:
        target_score += 45.0
    elif state not in {"allowed_remaining", "allowed_discovered"}:
        target_score -= 200.0

    return {
        "pair_key": pair_key,
        "label": label,
        "t": int(label.removeprefix("24T")),
        "r": r_value,
        "category": category,
        "progress_state": state,
        "score_value_status": score_value_status,
        "target_score": round(target_score, 3),
        "maximum_possible_points": maximum_points,
        "estimated_expected_points": estimated_points,
        "estimated_points_basis": official.get("estimated_points_basis"),
        "score_ceiling_class": ceiling_class,
        "signature_team_count": team_count,
        "minimum_disc_abs": progress_state.get("minimum_disc_abs"),
        "baseline_pair": baseline_pair,
        "explicit_target_requested": True,
        "explicit_target_source": "progress_jsonl",
    }


def explicit_targets_from_pairs(
    score_plan: dict[str, Any],
    *,
    target_pairs: list[str],
    progress_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_by_pair = {str(row["pair_key"]): row for row in _all_target_rows(score_plan)}
    progress_by_pair = progress_states_for_pairs(target_pairs, progress_rows)
    targets: list[dict[str, Any]] = []
    for pair_key in target_pairs:
        pair = str(pair_key)
        parse_pair_key(pair)
        if pair in plan_by_pair:
            row = dict(plan_by_pair[pair])
            row["explicit_target_requested"] = True
            row["explicit_target_source"] = "score_plan"
            targets.append(row)
            continue
        targets.append(_explicit_row_from_progress(pair, progress_by_pair[pair]))
    return targets


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def structural_status_and_blocks(
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
    target_pairs: list[str] | None = None,
    progress_rows: list[dict[str, Any]] | None = None,
    require_group_invariants: bool = True,
) -> list[dict[str, Any]]:
    registry = default_registry()
    explicit_pairs = [str(pair) for pair in target_pairs or []]
    targets = (
        explicit_targets_from_pairs(
            score_plan,
            target_pairs=explicit_pairs,
            progress_rows=list(progress_rows or []),
        )
        if explicit_pairs
        else select_targets(score_plan, top_targets=top_targets, category=category)
    )
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
            structurally_eligible, blocks = structural_status_and_blocks(
                target_group=group,
                family_rank=family,
                require_group_invariants=require_group_invariants,
            )
            generator_status = generation_status_for_route(
                family_name=str(family["family"]),
                r_value=r_value,
                group_record=group,
                structurally_eligible=structurally_eligible,
            )
            generation_blocks = list(blocks)
            if structurally_eligible:
                generation_blocks.extend(generator_status["generation_ready_blocking_reasons"])
            route_stage = "blocked"
            if structurally_eligible:
                route_stage = (
                    "executable_generator_available"
                    if generator_status["executable_generator_available"]
                    else "structurally_eligible"
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
                    "score_value_status": target.get("score_value_status"),
                    "explicit_target_requested": bool(target.get("explicit_target_requested")),
                    "explicit_target_source": target.get("explicit_target_source"),
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
                    "structurally_eligible": structurally_eligible,
                    "route_stage": route_stage,
                    "executable_generator_available": generator_status["executable_generator_available"],
                    "executable_generator_name": generator_status["executable_generator_name"],
                    "executable_generator_soundness": generator_status["executable_generator_soundness"],
                    "target_parameters_instantiated": generator_status["target_parameters_instantiated"],
                    "target_generator_parameters": generator_status["target_generator_parameters"],
                    "structure_preservation_declared": generator_status["structure_preservation_declared"],
                    "structure_preservation": generator_status["structure_preservation"],
                    "intended_group_constraint": generator_status.get("intended_group_constraint"),
                    "executable_generation_ready": generator_status["executable_generation_ready"],
                    "generation_ready": generator_status["executable_generation_ready"],
                    "generation_ready_deprecated": True,
                    "generation_ready_deprecation": (
                        "Use structurally_eligible for invariant-based routing. "
                        "generation_ready is reserved for executable target-bound "
                        "generators that pass local/adaptive checks."
                    ),
                    "blocking_reasons": blocks,
                    "generation_ready_blocking_reasons": generation_blocks,
                    "live_submission_recommended_now": False,
                    "soundness": SOUNDNESS_NOTE,
                }
            )
    routes.sort(
        key=lambda row: (
            bool(row["structurally_eligible"]),
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
    target_pairs_requested: list[str] | None = None,
    progress_jsonl_path: Path | None = None,
    progress_row_count: int = 0,
    require_group_invariants: bool = True,
) -> dict[str, Any]:
    target_pairs = {str(row["pair_key"]) for row in routes}
    targets_with_group = {str(row["pair_key"]) for row in routes if row.get("target_group_record_available")}
    blocks = Counter(reason for row in routes for reason in row.get("blocking_reasons") or [])
    generation_blocks = Counter(reason for row in routes for reason in row.get("generation_ready_blocking_reasons") or [])
    families = Counter(str(row["family"]) for row in routes)
    structurally_eligible_routes = [row for row in routes if row.get("structurally_eligible")]
    executable_generator_routes = [row for row in routes if row.get("executable_generator_available")]
    generation_ready_routes = [row for row in routes if row.get("executable_generation_ready")]
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
        "explicit_target_pairs_requested": list(target_pairs_requested or []),
        "explicit_target_pair_count": len(target_pairs_requested or []),
        "input_progress_jsonl": str(progress_jsonl_path) if progress_jsonl_path else None,
        "progress_jsonl_row_count": int(progress_row_count),
        "top_targets_requested": int(top_targets),
        "families_per_target": int(families_per_target),
        "avoid_labels": list(avoid_labels),
        "target_pair_count": len(target_pairs),
        "route_count": len(routes),
        "target_group_record_hit_count": len(targets_with_group),
        "target_group_record_missing_count": len(target_pairs) - len(targets_with_group),
        "structurally_eligible_route_count": len(structurally_eligible_routes),
        "structurally_eligible_target_count": len({str(row["pair_key"]) for row in structurally_eligible_routes}),
        "executable_generator_available_route_count": len(executable_generator_routes),
        "executable_generator_available_target_count": len(
            {str(row["pair_key"]) for row in executable_generator_routes}
        ),
        "generation_ready_route_count": len(generation_ready_routes),
        "generation_ready_target_count": len({str(row["pair_key"]) for row in generation_ready_routes}),
        "generation_ready_count_deprecated": True,
        "executable_generation_ready_route_count": len(generation_ready_routes),
        "executable_generation_ready_target_count": len({str(row["pair_key"]) for row in generation_ready_routes}),
        "blocking_reason_counts": dict(sorted(blocks.items())),
        "generation_ready_blocking_reason_counts": dict(sorted(generation_blocks.items())),
        "family_route_counts": dict(sorted(families.items())),
        "top_structurally_eligible_routes": [
            {
                "pair_key": row["pair_key"],
                "family": row["family"],
                "combined_priority_score": row["combined_priority_score"],
            }
            for row in structurally_eligible_routes[:10]
        ],
        "top_generation_ready_routes": [
            {
                "pair_key": row["pair_key"],
                "family": row["family"],
                "combined_priority_score": row["combined_priority_score"],
            }
            for row in generation_ready_routes[:10]
        ],
        "top_executable_generator_routes": [
            {
                "pair_key": row["pair_key"],
                "family": row["family"],
                "generator": row.get("executable_generator_name"),
                "combined_priority_score": row["combined_priority_score"],
            }
            for row in executable_generator_routes[:10]
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
        f"- Structurally eligible routes: `{summary['structurally_eligible_route_count']}`",
        f"- Executable-generator routes: `{summary['executable_generator_available_route_count']}`",
        f"- Generation-ready routes: `{summary['generation_ready_route_count']}`",
        f"- Blocking reasons: `{summary['blocking_reason_counts']}`",
        f"- Generation-ready blockers: `{summary['generation_ready_blocking_reason_counts']}`",
        f"- Soundness: `{summary['soundness']}`",
        f"- Safety: {summary['safety_note']}",
        "- Live submission recommended now: `False`",
        "",
        "## Top Routes",
        "",
        "| rank | pair | family | combined score | structural | executable | generation-ready | blocks | gen blockers | warnings |",
        "| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(routes[:25], start=1):
        blocks = ", ".join(row.get("blocking_reasons") or []) or "-"
        generation_blocks = ", ".join(row.get("generation_ready_blocking_reasons") or []) or "-"
        warnings = ", ".join(row.get("family_warnings") or []) or "-"
        lines.append(
            f"| {index} | `{row['pair_key']}` | `{row['family']}` | "
            f"{row['combined_priority_score']} | `{row['structurally_eligible']}` | "
            f"`{row['executable_generator_available']}` | `{row['executable_generation_ready']}` | "
            f"{blocks} | {generation_blocks} | {warnings} |"
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
                "",
                "Routes marked `structurally_eligible` still require an executable target-bound generator, "
                "structure-preservation checks, instantiated parameters, and adaptive Frobenius review before "
                "they can become generation-ready.",
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
    parser.add_argument(
        "--target_pair",
        action="append",
        default=[],
        help="Explicit 24Tt|r=n pair to route. May be passed multiple times; bypasses top-target selection.",
    )
    parser.add_argument(
        "--progress_jsonl",
        help="Optional SAIR label-progress JSONL used to score explicit target pairs safely.",
    )
    parser.add_argument("--avoid_label", action="append", default=[])
    parser.add_argument(
        "--allow_proxy_without_group_index",
        action="store_true",
        help="Mark routes ready without target group invariants. Intended only for diagnostics.",
    )
    args = parser.parse_args(argv)

    score_plan_path = Path(args.score_plan)
    group_index_path = Path(args.group_index) if args.group_index else None
    progress_jsonl_path = Path(args.progress_jsonl) if args.progress_jsonl else None
    score_plan = load_score_plan(score_plan_path)
    group_index = open_group_index(group_index_path)
    progress_rows = load_progress_jsonl(progress_jsonl_path)
    require_group_invariants = not bool(args.allow_proxy_without_group_index)
    routes = build_routes(
        score_plan=score_plan,
        group_index=group_index,
        avoid_labels=list(args.avoid_label or []),
        top_targets=int(args.top_targets),
        families_per_target=int(args.families_per_target),
        category=args.target_category or None,
        target_pairs=list(args.target_pair or []),
        progress_rows=progress_rows,
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
        target_pairs_requested=list(args.target_pair or []),
        progress_jsonl_path=progress_jsonl_path,
        progress_row_count=len(progress_rows),
        require_group_invariants=require_group_invariants,
    )
    write_outputs(Path(args.output_dir), summary=summary, routes=routes)

    print(f"target_pair_count {summary['target_pair_count']}")
    print(f"route_count {summary['route_count']}")
    print(f"structurally_eligible_route_count {summary['structurally_eligible_route_count']}")
    print(f"generation_ready_route_count {summary['generation_ready_route_count']}")
    print(f"blocking_reason_counts {json.dumps(summary['blocking_reason_counts'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
