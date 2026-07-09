#!/usr/bin/env python3
"""Chronological replay benchmark for IGP24 remediation.

The benchmark joins historical selected packets with later SAIR accepted-label
feedback. It then replays the original pre-feedback candidate rows through the
current packet optimizer and reports whether the remediated stack would still
spend a packet on the same rows.

This script is read-only. It does not submit to SAIR and does not use the API.
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

from scripts.igp24_packet_optimizer import (  # noqa: E402
    greedy_select,
    load_score_plan,
    normalize_candidate,
    read_jsonl,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402


DEFAULT_SCORE_PLAN = REPO_ROOT / "data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json"
DEFAULT_CROWDED_LABELS = {
    "24T23883",
    "24T24651",
    "24T24932",
    "24T24970",
    "24T24979",
    "24T25000",
}
DEFAULT_REPLAY_FEEDBACKS = [
    REPO_ROOT / "data/igp24/r8_score_followup_20260708/anti_collapse_gate/r8_score_followup_sair_accepted_feedback_20260708.json",
    REPO_ROOT / "data/igp24/r24_deterministic_high_real_expansion_20260709/submission/r24_deterministic_sair_accepted_feedback_20260709.json",
    REPO_ROOT / "data/igp24/axg16_conditioned_20260709/proposal_loop/axg16_anti_collapse_multir_gate_20260709/axg16_sair_accepted_feedback_20260709.json",
    REPO_ROOT / "data/igp24/axg17_score_aware_20260709/proposal_loop/axg17_score_aware_gate_20260709/axg17_sair_accepted_feedback_20260709.json",
    REPO_ROOT / "data/igp24/axg18_escape_20260709/proposal_loop/axg18_high_real_escape_combined_gate_20260709/axg18_sair_accepted_feedback_20260709.json",
    REPO_ROOT / "data/igp24/axg110_hash_exclusion_20260709/proposal_loop/axg110_hash_exclusion_spillover_gate_sparse_submode_freshsync_20260709/axg110_sair_accepted_feedback_20260709.json",
    REPO_ROOT / "data/igp24/axg112_pivot_20260709/proposal_loop/axg112_r12_pivot_combined_gate_composed_advisory_20260709/axg112_sair_accepted_feedback_20260709.json",
]

SUMMARY_JSON = "replay_benchmark_summary.json"
REPORT_MD = "replay_benchmark_report.md"
CASES_JSONL = "replay_benchmark_cases.jsonl"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def resolve_repo_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def infer_source_selected_path(feedback_path: Path, feedback: dict[str, Any]) -> Path | None:
    direct = resolve_repo_path(feedback.get("source_selected_jsonl"))
    if direct and direct.exists():
        return direct
    parent = feedback_path.parent
    for name in ("selected_review_packet.jsonl", "anti_basin_selected_queue.jsonl"):
        path = parent / name
        if path.exists():
            return path
    for manifest_name in ("proposal_loop_summary.json", "run_manifest.json", "anti_basin_planner_summary.json"):
        manifest_path = parent / manifest_name
        if not manifest_path.exists():
            continue
        try:
            manifest = load_json(manifest_path)
        except json.JSONDecodeError:
            continue
        candidates: list[Any] = []
        for key in ("output_files", "outputs", "files"):
            value = manifest.get(key)
            if isinstance(value, dict):
                candidates.extend(value.values())
        for key in ("selected_review_packet", "selected_jsonl", "selected_packet_jsonl"):
            if manifest.get(key):
                candidates.append(manifest[key])
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            path = resolve_repo_path(candidate)
            if path and path.exists() and path.suffix == ".jsonl":
                return path
    return direct


def pair_value(pair_key: str, score_plan: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = score_plan.get(pair_key) or {}
    return {
        "pair_key": pair_key,
        "maximum_possible_points": float(row.get("maximum_possible_points") or 0.0),
        "estimated_expected_points": float(row.get("estimated_expected_points") or 0.0),
        "score_ceiling_class": row.get("score_ceiling_class"),
        "category": row.get("category"),
    }


def feedback_metrics(
    feedback: dict[str, Any],
    *,
    score_plan: dict[str, dict[str, Any]],
    crowded_labels: set[str],
    low_team_threshold: float,
) -> dict[str, Any]:
    rows = [row for row in feedback.get("accepted_rows") or [] if isinstance(row, dict)]
    label_counts = Counter(str(row.get("label") or "") for row in rows)
    pair_counts = Counter(str(row.get("pair_key") or "") for row in rows if row.get("pair_key"))
    crowded_rows = [row for row in rows if str(row.get("label") or "") in crowded_labels]
    scoreable_rows = [row for row in rows if row.get("scoreable") is True or row.get("scoring_status") == "scoreable"]
    unique_pairs = sorted(pair_counts)
    pair_values = {pair: pair_value(pair, score_plan) for pair in unique_pairs}
    low_team_pairs = [
        pair
        for pair, value in pair_values.items()
        if float(value.get("maximum_possible_points") or 0.0) >= low_team_threshold
        and pair.split("|", 1)[0] not in crowded_labels
    ]
    estimated_points = sum(float(value.get("estimated_expected_points") or 0.0) for value in pair_values.values())
    submitted = max(1, len(rows))
    return {
        "accepted_rows": len(rows),
        "scoreable_rows": len(scoreable_rows),
        "label_counts": dict(label_counts),
        "pair_counts": dict(pair_counts),
        "distinct_verified_pair_count": len(unique_pairs),
        "distinct_verified_pairs": unique_pairs,
        "crowded_collapse_rows": len(crowded_rows),
        "crowded_collapse_rate": round(len(crowded_rows) / submitted, 6),
        "all_rows_hit_crowded_labels": bool(rows) and len(crowded_rows) == len(rows),
        "low_team_pair_yield": len(low_team_pairs),
        "low_team_pairs": low_team_pairs,
        "estimated_points_unique_pairs": round(estimated_points, 12),
        "estimated_points_per_100_submitted": round(100.0 * estimated_points / submitted, 12),
        "pair_values": pair_values,
    }


def optimizer_replay(
    *,
    selected_path: Path | None,
    score_plan: dict[str, dict[str, Any]],
    packet_limit: int,
    caps: dict[str, int],
) -> dict[str, Any]:
    if selected_path is None or not selected_path.exists():
        return {
            "source_selected_jsonl": str(selected_path) if selected_path else None,
            "source_available": False,
            "source_candidate_count": 0,
            "optimizer_eligible_count": 0,
            "optimizer_selected_rows": 0,
            "optimizer_selected_possible_uncovered_pair_count": 0,
            "optimizer_selected_possible_low_team_pair_count": 0,
            "optimizer_reject_reason_counts": {},
            "optimizer_rejected_all": False,
            "optimizer_downrank_fraction": None,
            "optimizer_heavily_downranked": None,
        }
    rows = read_jsonl(selected_path)
    candidates = [
        normalize_candidate(row, score_plan=score_plan, require_eligible=True)
        for row in rows
    ]
    selected, rejected = greedy_select(candidates, packet_limit=packet_limit, caps=caps)
    reject_counts = Counter(reason for row in rejected for reason in row.get("reject_reasons", []))
    source_count = len(candidates)
    selected_count = len(selected)
    denominator = max(1, source_count)
    downrank_fraction = selected_count / denominator
    uncovered = sorted({pair for row in selected for pair in row.get("possible_uncovered_pairs", [])})
    low_team = sorted({pair for row in selected for pair in row.get("possible_low_team_pairs", [])})
    return {
        "source_selected_jsonl": str(selected_path.relative_to(REPO_ROOT) if selected_path.is_relative_to(REPO_ROOT) else selected_path),
        "source_available": True,
        "source_candidate_count": source_count,
        "optimizer_eligible_count": sum(1 for row in candidates if row.get("eligible_for_optimization")),
        "optimizer_selected_rows": selected_count,
        "optimizer_selected_possible_uncovered_pair_count": len(uncovered),
        "optimizer_selected_possible_low_team_pair_count": len(low_team),
        "optimizer_selected_possible_uncovered_pairs": uncovered[:100],
        "optimizer_selected_possible_low_team_pairs": low_team[:100],
        "optimizer_reject_reason_counts": dict(reject_counts),
        "optimizer_rejected_all": selected_count == 0,
        "optimizer_downrank_fraction": round(downrank_fraction, 6),
        "optimizer_heavily_downranked": downrank_fraction <= 0.25,
    }


def evaluate_case(
    feedback_path: Path,
    *,
    score_plan: dict[str, dict[str, Any]],
    crowded_labels: set[str],
    low_team_threshold: float,
    packet_limit: int,
    caps: dict[str, int],
) -> dict[str, Any]:
    feedback = load_json(feedback_path)
    selected_path = infer_source_selected_path(feedback_path, feedback)
    observed = feedback_metrics(
        feedback,
        score_plan=score_plan,
        crowded_labels=crowded_labels,
        low_team_threshold=low_team_threshold,
    )
    replay = optimizer_replay(
        selected_path=selected_path,
        score_plan=score_plan,
        packet_limit=packet_limit,
        caps=caps,
    )
    major_collapse = (
        observed["accepted_rows"] >= 3
        and observed["crowded_collapse_rate"] >= 0.75
        and observed["low_team_pair_yield"] == 0
    )
    remediated_stops = bool(
        replay.get("optimizer_rejected_all")
        or replay.get("optimizer_heavily_downranked")
    )
    return {
        "feedback_path": str(feedback_path.relative_to(REPO_ROOT) if feedback_path.is_relative_to(REPO_ROOT) else feedback_path),
        "submission_id": feedback.get("submission_id"),
        "submitted_at": feedback.get("submitted_at"),
        "source_commit": feedback.get("source_commit"),
        "major_crowded_collapse_batch": major_collapse,
        "remediated_stops_or_downranks": remediated_stops,
        "old_pipeline": observed,
        "remediated_replay": replay,
    }


def aggregate_cases(cases: list[dict[str, Any]], *, caps: dict[str, int], feedback_paths: list[Path]) -> dict[str, Any]:
    major = [case for case in cases if case.get("major_crowded_collapse_batch")]
    stopped = [case for case in major if case.get("remediated_stops_or_downranks")]
    rows = sum(int(case["old_pipeline"]["accepted_rows"]) for case in cases)
    crowded_rows = sum(int(case["old_pipeline"]["crowded_collapse_rows"]) for case in cases)
    old_pairs = sorted({pair for case in cases for pair in case["old_pipeline"]["distinct_verified_pairs"]})
    new_selected = sum(int(case["remediated_replay"].get("optimizer_selected_rows") or 0) for case in cases)
    return {
        "schema_version": 1,
        "record_type": "igp24_chronological_replay_benchmark",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_replay_benchmark.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety": {
            "sair_submission": False,
            "sair_dry_run": False,
            "network_calls": False,
            "api_key_recorded": False,
        },
        "inputs": {
            "feedback_paths": [str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path) for path in feedback_paths],
            "case_count": len(cases),
            "caps": caps,
        },
        "old_pipeline_totals": {
            "accepted_rows": rows,
            "crowded_collapse_rows": crowded_rows,
            "crowded_collapse_rate": round(crowded_rows / max(1, rows), 6),
            "distinct_verified_pair_count": len(old_pairs),
            "distinct_verified_pairs": old_pairs,
            "estimated_points_per_100_submitted": round(
                sum(float(case["old_pipeline"]["estimated_points_unique_pairs"]) for case in cases) * 100.0 / max(1, rows),
                12,
            ),
        },
        "remediated_totals": {
            "optimizer_selected_rows": new_selected,
            "major_collapse_case_count": len(major),
            "major_collapse_cases_stopped_or_downranked": len(stopped),
            "all_major_collapse_cases_stopped_or_downranked": bool(major) and len(major) == len(stopped),
        },
        "phase7_minimum_gate_passed": bool(major) and len(major) == len(stopped),
        "cases": cases,
    }


def build_report(summary: dict[str, Any]) -> str:
    old = summary["old_pipeline_totals"]
    new = summary["remediated_totals"]
    lines = [
        "# IGP24 Chronological Replay Benchmark",
        "",
        "This benchmark replays historical selected packets against later SAIR feedback and the current remediated packet optimizer. It does not use live APIs or authorize submission.",
        "",
        "## Aggregate",
        "",
        f"- Cases: {summary['inputs']['case_count']}",
        f"- Old accepted rows: {old['accepted_rows']}",
        f"- Old crowded-collapse rate: {old['crowded_collapse_rate']}",
        f"- Old distinct verified pairs: {old['distinct_verified_pair_count']}",
        f"- Estimated old points per 100 submitted rows: {old['estimated_points_per_100_submitted']}",
        f"- Major collapse cases: {new['major_collapse_case_count']}",
        f"- Major collapse cases stopped/downranked by remediated replay: {new['major_collapse_cases_stopped_or_downranked']}",
        f"- Phase 7 minimum gate passed: `{summary['phase7_minimum_gate_passed']}`",
        "",
        "## Cases",
        "",
        "| case | submitted | accepted | labels | pairs | collapse rate | old points/100 | remediated selected | stop/downrank |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for case in summary["cases"]:
        old_case = case["old_pipeline"]
        replay = case["remediated_replay"]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{case.get('submission_id')}`",
                    str(case.get("submitted_at")),
                    str(old_case["accepted_rows"]),
                    json.dumps(old_case["label_counts"], sort_keys=True),
                    json.dumps(old_case["pair_counts"], sort_keys=True),
                    str(old_case["crowded_collapse_rate"]),
                    str(old_case["estimated_points_per_100_submitted"]),
                    str(replay.get("optimizer_selected_rows")),
                    str(case.get("remediated_stops_or_downranks")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A pass here is not leaderboard progress. It is evidence that the remediated stack no longer approves the historical collapse packets that produced crowded-label outcomes such as `24T25000` and `24T24979`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary_json": output_dir / SUMMARY_JSON,
        "report_md": output_dir / REPORT_MD,
        "cases_jsonl": output_dir / CASES_JSONL,
    }
    output_files = {name: str(path) for name, path in paths.items()}
    final_summary = {**summary, "output_files": output_files}
    paths["summary_json"].write_text(json.dumps(final_summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    paths["report_md"].write_text(build_report(final_summary), encoding="utf-8")
    write_jsonl(paths["cases_jsonl"], summary["cases"])
    return paths


def parse_csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted_feedback_json", type=Path, action="append")
    parser.add_argument("--score_plan_json", type=Path, default=DEFAULT_SCORE_PLAN)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--crowded_labels", default=",".join(sorted(DEFAULT_CROWDED_LABELS)))
    parser.add_argument("--low_team_threshold", type=float, default=0.001)
    parser.add_argument("--packet_limit", type=int, default=100)
    parser.add_argument("--per_construction_family_cap", type=int, default=40)
    parser.add_argument("--per_template_family_cap", type=int, default=12)
    parser.add_argument("--per_perturbation_mode_cap", type=int, default=20)
    parser.add_argument("--per_basin_fingerprint_cap", type=int, default=3)
    parser.add_argument("--per_mod_signature_cap", type=int, default=4)
    parser.add_argument("--per_compatible_cluster_cap", type=int, default=8)
    parser.add_argument("--per_r_cap", type=int, default=40)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    feedback_paths = args.accepted_feedback_json or list(DEFAULT_REPLAY_FEEDBACKS)
    score_plan = load_score_plan(args.score_plan_json)
    crowded_labels = parse_csv_set(args.crowded_labels)
    caps = {
        "construction_family": int(args.per_construction_family_cap),
        "template_family_id": int(args.per_template_family_cap),
        "perturbation_mode": int(args.per_perturbation_mode_cap),
        "basin_fingerprint": int(args.per_basin_fingerprint_cap),
        "mod_p_pattern_signature": int(args.per_mod_signature_cap),
        "compatible_label_cluster": int(args.per_compatible_cluster_cap),
        "r": int(args.per_r_cap),
    }
    cases = [
        evaluate_case(
            path,
            score_plan=score_plan,
            crowded_labels=crowded_labels,
            low_team_threshold=float(args.low_team_threshold),
            packet_limit=int(args.packet_limit),
            caps=caps,
        )
        for path in feedback_paths
        if path.exists()
    ]
    summary = aggregate_cases(cases, caps=caps, feedback_paths=feedback_paths)
    paths = write_outputs(args.output_dir, summary)
    print(f"case_count\t{summary['inputs']['case_count']}")
    print(f"old_crowded_collapse_rate\t{summary['old_pipeline_totals']['crowded_collapse_rate']}")
    print(f"major_collapse_cases\t{summary['remediated_totals']['major_collapse_case_count']}")
    print(
        "major_collapse_cases_stopped_or_downranked\t"
        f"{summary['remediated_totals']['major_collapse_cases_stopped_or_downranked']}"
    )
    print(f"phase7_minimum_gate_passed\t{summary['phase7_minimum_gate_passed']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
