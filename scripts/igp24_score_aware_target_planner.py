#!/usr/bin/env python3
"""Score-aware IGP24 target and lane planner.

This helper joins live SAIR label progress, local accepted-pair state,
user-reported score snapshots, and label-basin constraints. It does not
generate candidates or submit anything; it ranks target pockets and recommends
the next bounded search lane.
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

from scripts.igp24_sair_progress_targets import (  # noqa: E402
    coverage_by_r,
    fetch_progress_snapshot,
    load_progress_snapshot,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402


DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"
DEFAULT_SCORE_SNAPSHOT = REPO_ROOT / "data/igp24/sair_score_snapshot_20260707_user_reported.json"
DEFAULT_LABEL_BASIN_SUMMARY = REPO_ROOT / "data/igp24/label_basin_analysis_20260707/label_basin_summary.json"

PLAN_JSON = "score_aware_target_plan.json"
SUMMARY_JSON = "score_aware_target_summary.json"
REPORT_MD = "score_aware_target_report.md"
RANKED_TARGETS_JSONL = "score_aware_ranked_targets.jsonl"
LANES_JSON = "score_aware_lane_recommendations.json"

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
COLLAPSED_LABELS = {"24T24932", "24T24984", "24T25000", "24T24979", "24T24970", "24T24651", "24T23883"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pair_status(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("record_type") != "igp24_pair_status_ledger":
        raise ValueError(f"unexpected pair status record_type in {path}")
    return payload


def load_score_snapshot(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("record_type") != "igp24_user_reported_sair_score_snapshot":
        raise ValueError(f"unexpected score snapshot record_type in {path}")
    return payload


def load_basin_summary(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("record_type") != "igp24_label_basin_analysis":
        raise ValueError(f"unexpected basin summary record_type in {path}")
    return payload


def pair_key(label: str, r_value: int) -> str:
    return f"{label}|r={int(r_value)}"


def index_pairs(pair_status: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["pair_key"]): row
        for row in pair_status.get("pairs") or []
        if isinstance(row, dict) and row.get("pair_key")
    }


def score_snapshot_by_pair(score_snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["pair_key"]): row
        for row in score_snapshot.get("rows") or []
        if isinstance(row, dict) and row.get("pair_key")
    }


def constraints_by_name(basin_summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["name"]): row
        for row in basin_summary.get("anti_basin_constraints") or []
        if isinstance(row, dict) and row.get("name")
    }


def avoided_labels(basin_summary: dict[str, Any]) -> set[str]:
    labels: set[str] = set(COLLAPSED_LABELS)
    for constraint in basin_summary.get("anti_basin_constraints") or []:
        for label in constraint.get("labels") or []:
            labels.add(str(label))
    return labels


def signature_by_r(label_row: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for signature in label_row.get("signatures") or []:
        if isinstance(signature, dict) and signature.get("r") is not None:
            out[int(signature["r"])] = signature
    return out


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _score_points(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    value = row.get("points_numeric")
    if value is None:
        return None
    return float(value)


def iter_progress_pairs(
    labels: Iterable[dict[str, Any]],
    *,
    pair_status_by_key: dict[str, dict[str, Any]],
    score_by_pair: dict[str, dict[str, Any]],
    avoid_labels: set[str],
    remaining_by_r: dict[int, int],
) -> Iterable[dict[str, Any]]:
    for label_row in labels:
        if not isinstance(label_row, dict) or not label_row.get("label"):
            continue
        label = str(label_row["label"])
        t_value = int(label_row.get("t") or label.removeprefix("24T"))
        allowed = [int(value) for value in label_row.get("allowedR") or []]
        discovered = {int(value) for value in label_row.get("discoveredSignatures") or []}
        remaining = {int(value) for value in label_row.get("remainingSignatures") or []}
        signatures = signature_by_r(label_row)
        label_team_count = int(label_row.get("teamCount") or 0)
        for r_value in allowed:
            signature = signatures.get(r_value) or {}
            key = pair_key(label, r_value)
            score_row = score_by_pair.get(key)
            status_row = pair_status_by_key.get(key)
            signature_team_count = int(
                signature.get("teamCount")
                if signature.get("teamCount") is not None
                else (score_row or {}).get("solved_teams") or 0
            )
            progress_state = (
                "remaining"
                if r_value in remaining
                else "discovered"
                if r_value in discovered
                else "undiscovered_state_unknown"
            )
            category = "covered_or_crowded"
            if progress_state == "remaining":
                category = "uncovered_signature"
            elif _score_points(score_row):
                category = "scored_pair_followup"
            elif signature_team_count <= 12:
                category = "lightly_solved_signature"
            elif signature_team_count <= 20:
                category = "moderately_solved_signature"

            points = _score_points(score_row)
            score = ROOT_BUCKET_WEIGHTS.get(r_value, 10.0)
            score += min(remaining_by_r.get(r_value, 0) / 85.0, 135.0)
            score += min(len(remaining), 12) * 3.0
            if progress_state == "remaining":
                score += 520.0
            elif progress_state != "discovered":
                score += 420.0
            if points is not None:
                score += min(points * 100000.0, 260.0)
                if (score_row or {}).get("solved_teams", 99) <= 12:
                    score += 90.0
            if signature_team_count <= 5:
                score += 160.0
            elif signature_team_count <= 12:
                score += 105.0
            elif signature_team_count <= 20:
                score += 45.0
            score -= min(label_team_count, 80) * 1.15
            if status_row and points is None:
                score -= 155.0
            elif status_row and points is not None:
                score -= 35.0
            if label in avoid_labels:
                score -= 210.0 if points is None else 85.0
            if not remaining and points is None and category == "covered_or_crowded":
                score -= 80.0

            yield {
                "pair_key": key,
                "label": label,
                "t": t_value,
                "r": r_value,
                "category": category,
                "target_score": round(score, 3),
                "progress_state": progress_state,
                "label_team_count": label_team_count,
                "signature_team_count": signature_team_count,
                "label_remaining_signature_count": len(remaining),
                "label_discovered_signature_count": len(discovered),
                "label_allowed_signature_count": len(allowed),
                "local_pair_status": status_row.get("status") if status_row else None,
                "local_pair_already_accepted": bool(status_row and status_row.get("status") == "accepted"),
                "score_snapshot_points": (score_row or {}).get("points"),
                "score_snapshot_points_numeric": points,
                "score_snapshot_solved_teams": (score_row or {}).get("solved_teams"),
                "scoring_discriminant_abs": (score_row or {}).get("scoring_discriminant_abs"),
                "label_in_avoid_basin": label in avoid_labels,
                "minimum_disc_abs": signature.get("minimumDiscAbs") or label_row.get("minimumDiscAbs"),
            }


def rank_r_buckets(target_rows: list[dict[str, Any]], coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_r: dict[int, dict[str, Any]] = {int(row["r"]): dict(row) for row in coverage_rows}
    counts: dict[int, Counter[str]] = defaultdict(Counter)
    point_sum: Counter[int] = Counter()
    top_target: dict[int, dict[str, Any]] = {}
    for row in target_rows:
        r_value = int(row["r"])
        counts[r_value][str(row["category"])] += 1
        point_sum[r_value] += float(row.get("score_snapshot_points_numeric") or 0.0)
        if r_value not in top_target or row["target_score"] > top_target[r_value]["target_score"]:
            top_target[r_value] = row
    ranked: list[dict[str, Any]] = []
    for r_value, coverage in by_r.items():
        rem = int(coverage.get("remaining") or 0)
        score = ROOT_BUCKET_WEIGHTS.get(r_value, 10.0) + min(rem / 55.0, 240.0)
        score += counts[r_value]["uncovered_signature"] * 0.075
        score += counts[r_value]["lightly_solved_signature"] * 0.008
        score += counts[r_value]["moderately_solved_signature"] * 0.004
        score += point_sum[r_value] * 100000.0
        ranked.append(
            {
                "r": r_value,
                "priority_score": round(score, 3),
                "allowed": coverage.get("allowed"),
                "discovered": coverage.get("discovered"),
                "remaining": rem,
                "discovered_pct": coverage.get("discovered_pct"),
                "category_counts": dict(counts[r_value]),
                "score_snapshot_points_total": round(float(point_sum[r_value]), 6),
                "top_pair": top_target.get(r_value, {}).get("pair_key"),
                "top_pair_score": top_target.get(r_value, {}).get("target_score"),
            }
        )
    return sorted(ranked, key=lambda row: row["priority_score"], reverse=True)


def lane_from_family(family: str, pair: str, r_value: int) -> str:
    if family == "r8_quartic_lift":
        return "r8_quartic_lift_score_followup"
    if family == "degree12_base_six_positive_roots_lifted_by_x2":
        return "r12_gx2_structured_score_followup"
    if "4x6" in family:
        return "new_4x6_inner_family_not_current_roots"
    return f"{family or 'unknown'}_score_followup_r{r_value}_{pair.split('|', 1)[0]}"


def build_lane_recommendations(
    *,
    score_snapshot: dict[str, Any],
    basin_summary: dict[str, Any],
    ranked_targets: list[dict[str, Any]],
    bucket_priorities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pair_summary = basin_summary.get("pair_summary") or {}
    lanes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for score_row in sorted(
        score_snapshot.get("rows") or [],
        key=lambda row: (float(row.get("points_numeric") or 0.0), -int(row.get("solved_teams") or 999)),
        reverse=True,
    ):
        points = _score_points(score_row)
        if points is None:
            continue
        key = str(score_row["pair_key"])
        summary = pair_summary.get(key) or {}
        family_counts = summary.get("construction_family_counts") or {}
        primary_family = next(iter(sorted(family_counts, key=family_counts.get, reverse=True)), "")
        lane_name = lane_from_family(primary_family, key, int(score_row["r"]))
        if lane_name in seen:
            continue
        seen.add(lane_name)
        lanes.append(
            {
                "lane": lane_name,
                "rank_reason": f"visible score outlier {key} at {score_row['points']} with {score_row['solved_teams']} solved teams",
                "source_pair": key,
                "source_points": score_row["points"],
                "source_solved_teams": score_row["solved_teams"],
                "source_family": primary_family,
                "construction_family_counts": family_counts,
                "recommended_for_generation_now": True,
                "recommended_for_submission_now": False,
                "submission_gate": "fresh queue must pass local exact checks, score-aware planner, anti-basin planner, and SAIR dry-run first",
            }
        )
    top_remaining = [row for row in ranked_targets if row["category"] == "uncovered_signature"][:5]
    if top_remaining:
        top_rs = ",".join(str(row["r"]) for row in bucket_priorities[:4])
        lanes.append(
            {
                "lane": "zero_team_high_real_target_conditioning",
                "rank_reason": "live progress still has many zero-team/uncovered signatures; current generators cannot directly condition exact labels",
                "source_pair": top_remaining[0]["pair_key"],
                "top_uncovered_pairs": [row["pair_key"] for row in top_remaining],
                "target_r_buckets": top_rs,
                "recommended_for_generation_now": False,
                "recommended_for_submission_now": False,
                "submission_gate": "requires a stronger exact-label steering mechanism before spending a packet",
            }
        )
    lanes.append(
        {
            "lane": "no_more_collapsed_composition_lanes",
            "rank_reason": "basin constraints show 6x4, ordinary 8x3, and current 4x6 inner-root family are exhausted",
            "avoid_families": [
                "nearby r24 6x4 towers",
                "ordinary 8x3 outer coefficient perturbations",
                "current 4x6 inner roots -3,-2,-1,1,2,4",
                "product/quadratic low-odd perturbation lanes into 24T25000",
            ],
            "recommended_for_generation_now": False,
            "recommended_for_submission_now": False,
            "submission_gate": "avoidance rule only",
        }
    )
    return lanes


def build_plan(
    *,
    snapshot: dict[str, Any],
    pair_status: dict[str, Any],
    score_snapshot: dict[str, Any],
    basin_summary: dict[str, Any],
    top_limit: int = 250,
) -> dict[str, Any]:
    labels = list(snapshot.get("labels") or [])
    coverage_rows = coverage_by_r(labels)
    remaining_by_r = {int(row["r"]): int(row.get("remaining") or 0) for row in coverage_rows}
    pair_status_by_key = index_pairs(pair_status)
    score_by_pair = score_snapshot_by_pair(score_snapshot)
    avoid = avoided_labels(basin_summary)
    target_rows = list(
        iter_progress_pairs(
            labels,
            pair_status_by_key=pair_status_by_key,
            score_by_pair=score_by_pair,
            avoid_labels=avoid,
            remaining_by_r=remaining_by_r,
        )
    )
    ranked_targets = sorted(target_rows, key=lambda row: (row["target_score"], -int(row["t"])), reverse=True)
    bucket_priorities = rank_r_buckets(target_rows, coverage_rows)
    lanes = build_lane_recommendations(
        score_snapshot=score_snapshot,
        basin_summary=basin_summary,
        ranked_targets=ranked_targets,
        bucket_priorities=bucket_priorities,
    )
    constraints = constraints_by_name(basin_summary)
    best_lane = next((lane for lane in lanes if lane.get("recommended_for_generation_now")), lanes[0] if lanes else None)
    return {
        "schema_version": 1,
        "record_type": "igp24_score_aware_target_plan",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_score_aware_target_planner.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "input_snapshot": {
            "record_type": snapshot.get("record_type"),
            "created_at": snapshot.get("created_at"),
            "query": snapshot.get("query"),
            "page_count": snapshot.get("page_count"),
            "label_count": snapshot.get("label_count") or len(labels),
            "first_generated_at": (snapshot.get("pages") or [{}])[0].get("generatedAt"),
            "last_generated_at": (snapshot.get("pages") or [{}])[-1].get("generatedAt"),
            "published": ((snapshot.get("pages") or [{}])[0].get("meta") or {}).get("published"),
        },
        "inputs": {
            "pair_status_record_type": pair_status.get("record_type"),
            "score_snapshot_record_type": score_snapshot.get("record_type"),
            "score_snapshot_rows": len(score_snapshot.get("rows") or []),
            "basin_summary_record_type": basin_summary.get("record_type"),
            "basin_observations": basin_summary.get("observation_count"),
            "anti_basin_constraint_count": len(basin_summary.get("anti_basin_constraints") or []),
        },
        "safety": {
            "gpu_training": False,
            "model_training": False,
            "sair_submission": False,
            "sair_dry_run": False,
            "api_key_recorded": False,
        },
        "coverage_by_r": coverage_rows,
        "r_bucket_priorities": bucket_priorities,
        "ranked_targets": ranked_targets[:top_limit],
        "top_uncovered_targets": [row for row in ranked_targets if row["category"] == "uncovered_signature"][:50],
        "top_score_followup_targets": [row for row in ranked_targets if row["category"] == "scored_pair_followup"][:25],
        "top_lightly_solved_targets": [row for row in ranked_targets if row["category"] == "lightly_solved_signature"][:25],
        "lane_recommendations": lanes,
        "avoidance_constraints": {
            "avoid_labels": sorted(avoid),
            "high_severity_names": [
                name for name, row in constraints.items() if row.get("severity") == "high"
            ],
        },
        "decision": {
            "recommended_next_lane": best_lane,
            "clear_bounded_generation_lane": bool(best_lane and best_lane.get("recommended_for_generation_now")),
            "submission_recommended_now": False,
            "submission_reason": "no candidate packet was generated by this planning helper; any future packet must pass score-aware and anti-basin gates plus SAIR dry-run",
            "gpu_training_recommended_now": False,
            "big_model_training_recommended_now": False,
        },
    }


def build_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Score-Aware Target Plan",
        "",
        "## Snapshot",
        "",
        f"- Labels: {plan['input_snapshot'].get('label_count')}",
        f"- Pages: {plan['input_snapshot'].get('page_count')}",
        f"- Published: {plan['input_snapshot'].get('published')}",
        f"- Generated: `{plan['input_snapshot'].get('first_generated_at')}` to `{plan['input_snapshot'].get('last_generated_at')}`",
        f"- Score snapshot rows: {plan['inputs'].get('score_snapshot_rows')}",
        f"- Basin constraints: {plan['inputs'].get('anti_basin_constraint_count')}",
        "",
        "## Priority r Buckets",
        "",
        "| rank | r | priority | remaining | category counts | top pair |",
        "| ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for rank, row in enumerate(plan["r_bucket_priorities"][:10], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    str(row["r"]),
                    f"{float(row['priority_score']):.2f}",
                    str(row["remaining"]),
                    json.dumps(row["category_counts"], sort_keys=True),
                    str(row.get("top_pair")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Top Uncovered Targets",
            "",
            "| rank | pair | score | label teams | signature teams | remaining on label |",
            "| ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for rank, row in enumerate(plan["top_uncovered_targets"][:15], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    row["pair_key"],
                    f"{float(row['target_score']):.2f}",
                    str(row["label_team_count"]),
                    str(row["signature_team_count"]),
                    str(row["label_remaining_signature_count"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Score Follow-Up Targets",
            "",
            "| rank | pair | points | solved teams | source score | category |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for rank, row in enumerate(plan["top_score_followup_targets"][:10], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    row["pair_key"],
                    str(row.get("score_snapshot_points")),
                    str(row.get("score_snapshot_solved_teams")),
                    f"{float(row['target_score']):.2f}",
                    row["category"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Lane Recommendations",
            "",
            "| rank | lane | generation now | submission now | reason |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for rank, row in enumerate(plan["lane_recommendations"], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    row["lane"],
                    str(row.get("recommended_for_generation_now")),
                    str(row.get("recommended_for_submission_now")),
                    str(row.get("rank_reason", "")).replace("|", "/"),
                ]
            )
            + " |"
        )
    decision = plan["decision"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Recommended next lane: `{(decision.get('recommended_next_lane') or {}).get('lane')}`",
            f"- Clear bounded generation lane: `{decision['clear_bounded_generation_lane']}`",
            f"- Submission recommended now: `{decision['submission_recommended_now']}`",
            f"- GPU/model training now: `{decision['gpu_training_recommended_now']}` / `{decision['big_model_training_recommended_now']}`",
            f"- Submission reason: {decision['submission_reason']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(plan: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "plan_json": output_dir / PLAN_JSON,
        "summary_json": output_dir / SUMMARY_JSON,
        "report_md": output_dir / REPORT_MD,
        "ranked_targets_jsonl": output_dir / RANKED_TARGETS_JSONL,
        "lanes_json": output_dir / LANES_JSON,
    }
    output_files = {name: str(path) for name, path in paths.items()}
    plan_with_files = {**plan, "output_files": output_files}
    paths["plan_json"].write_text(json.dumps(plan_with_files, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    summary = {
        "schema_version": plan["schema_version"],
        "record_type": plan["record_type"],
        "created_at": plan["created_at"],
        "input_snapshot": plan["input_snapshot"],
        "top_r_buckets": plan["r_bucket_priorities"][:8],
        "top_uncovered_targets": plan["top_uncovered_targets"][:12],
        "top_score_followup_targets": plan["top_score_followup_targets"][:8],
        "lane_recommendations": plan["lane_recommendations"],
        "decision": plan["decision"],
        "safety": plan["safety"],
        "output_files": output_files,
    }
    paths["summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    paths["report_md"].write_text(build_markdown(plan_with_files), encoding="utf-8")
    paths["lanes_json"].write_text(json.dumps(plan["lane_recommendations"], indent=2, sort_keys=False) + "\n", encoding="utf-8")
    with paths["ranked_targets_jsonl"].open("w", encoding="utf-8") as handle:
        for row in plan["ranked_targets"]:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--progress_snapshot_json", type=Path)
    source.add_argument("--fetch_live_progress", action="store_true")
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--score_snapshot_json", type=Path, default=DEFAULT_SCORE_SNAPSHOT)
    parser.add_argument("--label_basin_summary_json", type=Path, default=DEFAULT_LABEL_BASIN_SUMMARY)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--top_limit", type=int, default=250)
    parser.add_argument("--fetch_limit", type=int, default=5000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    snapshot = (
        fetch_progress_snapshot(limit=args.fetch_limit)
        if args.fetch_live_progress
        else load_progress_snapshot(args.progress_snapshot_json)
    )
    plan = build_plan(
        snapshot=snapshot,
        pair_status=load_pair_status(args.pair_status_json),
        score_snapshot=load_score_snapshot(args.score_snapshot_json),
        basin_summary=load_basin_summary(args.label_basin_summary_json),
        top_limit=args.top_limit,
    )
    paths = write_outputs(plan, args.output_dir)
    decision = plan["decision"]
    print(f"top_r_buckets\t{json.dumps(plan['r_bucket_priorities'][:5])}")
    print(f"recommended_next_lane\t{json.dumps(decision['recommended_next_lane'])}")
    print(f"clear_bounded_generation_lane\t{decision['clear_bounded_generation_lane']}")
    print(f"submission_recommended_now\t{decision['submission_recommended_now']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
