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
    candidate_features,
    candidate_payload,
    frobenius_evidence_budget,
    greedy_select,
    group_compatibility,
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
        "duplicated_pair_row_count": sum(max(0, count - 1) for count in pair_counts.values()),
        "duplicated_pair_rate": round(
            sum(max(0, count - 1) for count in pair_counts.values()) / submitted,
            6,
        ),
        "crowded_collapse_rows": len(crowded_rows),
        "crowded_collapse_rate": round(len(crowded_rows) / submitted, 6),
        "all_rows_hit_crowded_labels": bool(rows) and len(crowded_rows) == len(rows),
        "low_team_pair_yield": len(low_team_pairs),
        "low_team_pairs": low_team_pairs,
        "estimated_points_unique_pairs": round(estimated_points, 12),
        "estimated_points_per_100_submitted": round(100.0 * estimated_points / submitted, 12),
        "pair_values": pair_values,
    }


def _bool_field(row: dict[str, Any], key: str) -> bool | None:
    value = row.get(key)
    if value is None:
        value = candidate_payload(row).get(key)
    if value is None:
        return None
    return bool(value)


def _candidate_hash(row: dict[str, Any]) -> str:
    features = candidate_features(row)
    return str(row.get("canonical_hash") or features.get("canonical_hash") or "")


def _candidate_r(row: dict[str, Any]) -> int | None:
    features = candidate_features(row)
    for value in (
        row.get("real_root_count"),
        row.get("r"),
        features.get("r"),
        candidate_payload(row).get("real_root_count"),
        candidate_payload(row).get("r"),
    ):
        try:
            if value is not None and value != "":
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _intended_r(row: dict[str, Any]) -> int | None:
    features = candidate_features(row)
    payload = candidate_payload(row)
    sources = [
        row.get("target_r"),
        row.get("target_r_intent"),
        features.get("target_r"),
        features.get("target_r_intent"),
    ]
    for key in ("target_metadata", "generation_metadata", "source_sample_export", "sample_provenance"):
        source = row.get(key)
        if isinstance(source, dict):
            sources.extend([source.get("target_r"), source.get("target_r_intent")])
            nested = source.get("generation_metadata")
            if isinstance(nested, dict):
                sources.extend([nested.get("target_r"), nested.get("target_r_intent")])
    metadata = payload.get("generation_metadata")
    if isinstance(metadata, dict):
        sources.extend([metadata.get("target_r"), metadata.get("target_r_intent")])
    for value in sources:
        try:
            if value is not None and value != "":
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _median(values: list[int]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _feedback_by_hash(feedback: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_hash: dict[str, dict[str, Any]] = {}
    for row in feedback.get("accepted_rows") or []:
        if not isinstance(row, dict):
            continue
        canonical_hash = str(row.get("canonical_hash") or "")
        if canonical_hash:
            by_hash[canonical_hash] = row
    return by_hash


def selected_candidate_metrics(rows: list[dict[str, Any]], feedback: dict[str, Any]) -> dict[str, Any]:
    hashes = [_candidate_hash(row) for row in rows if _candidate_hash(row)]
    valid_flags = [_bool_field(row, "valid") for row in rows]
    irreducible_flags = [_bool_field(row, "irreducible") for row in rows]
    squarefree_flags = [_bool_field(row, "squarefree") for row in rows]
    target_r_known = 0
    target_r_matches = 0
    family_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    compat_rows = 0
    valuable_survival_rows = 0
    indexed_survivor_counts: list[int] = []
    usable_prime_counts: list[int] = []
    containment_evaluated = 0
    containment_success = 0
    containment_failures: list[dict[str, Any]] = []
    containment_missing = 0
    by_hash = _feedback_by_hash(feedback)
    family_outcomes: dict[str, Counter[str]] = {}

    for row in rows:
        features = candidate_features(row)
        family = str(features.get("construction_family") or "missing")
        mode = str(features.get("perturbation_mode") or "missing")
        family_counts[family] += 1
        mode_counts[mode] += 1
        candidate_r = _candidate_r(row)
        intended_r = _intended_r(row)
        if candidate_r is not None and intended_r is not None:
            target_r_known += 1
            target_r_matches += int(candidate_r == intended_r)

        compat = group_compatibility(row)
        if compat:
            compat_rows += 1
            survivor_count = (
                compat.get("indexed_target_survivor_count")
                or compat.get("compatible_label_count")
                or len(compat.get("indexed_target_labels_not_ruled_out") or compat.get("compatible_labels") or [])
            )
            try:
                indexed_survivor_counts.append(int(survivor_count))
            except (TypeError, ValueError):
                pass
            if compat.get("valuable_targets_not_ruled_out") or compat.get("compatible_uncovered_pairs") or compat.get("compatible_low_team_pairs"):
                valuable_survival_rows += 1
            budget = frobenius_evidence_budget(row, compat)
            usable_prime_counts.append(int(budget.get("usable_prime_count") or 0))

        canonical_hash = _candidate_hash(row)
        feedback_row = by_hash.get(canonical_hash)
        true_label = str(feedback_row.get("label") or "") if feedback_row else ""
        if feedback_row:
            family_outcomes.setdefault(family, Counter())[true_label or "missing_label"] += 1
        labels = compat.get("indexed_target_labels_not_ruled_out") or compat.get("compatible_labels") or []
        if true_label and labels:
            containment_evaluated += 1
            if true_label in set(str(label) for label in labels):
                containment_success += 1
            else:
                containment_failures.append(
                    {
                        "canonical_hash": canonical_hash,
                        "true_label": true_label,
                        "compatible_labels": list(labels)[:25],
                    }
                )
        elif feedback_row:
            containment_missing += 1

    row_count = len(rows)
    unique_hash_count = len(set(hashes))
    return {
        "source_candidate_count": row_count,
        "unique_canonical_hash_count": unique_hash_count,
        "duplicate_hash_count": max(0, len(hashes) - unique_hash_count),
        "unique_decode_rate": round(unique_hash_count / max(1, row_count), 6),
        "valid_row_count": sum(1 for value in valid_flags if value is True),
        "valid_rate_among_known": round(
            sum(1 for value in valid_flags if value is True) / max(1, sum(value is not None for value in valid_flags)),
            6,
        )
        if any(value is not None for value in valid_flags)
        else None,
        "irreducible_row_count": sum(1 for value in irreducible_flags if value is True),
        "squarefree_row_count": sum(1 for value in squarefree_flags if value is True),
        "target_r_known_count": target_r_known,
        "target_r_match_count": target_r_matches,
        "target_r_match_rate": round(target_r_matches / max(1, target_r_known), 6) if target_r_known else None,
        "construction_family_counts": dict(family_counts),
        "perturbation_mode_counts": dict(mode_counts),
        "compatibility_evidence_row_count": compat_rows,
        "compatibility_evidence_rate": round(compat_rows / max(1, row_count), 6),
        "valuable_survival_row_count": valuable_survival_rows,
        "valuable_survival_rate": round(valuable_survival_rows / max(1, row_count), 6),
        "median_indexed_survivor_count": _median(indexed_survivor_counts),
        "max_indexed_survivor_count": max(indexed_survivor_counts) if indexed_survivor_counts else None,
        "median_frobenius_usable_prime_count": _median(usable_prime_counts),
        "true_label_containment_evaluated_count": containment_evaluated,
        "true_label_containment_success_count": containment_success,
        "true_label_containment_rate": round(containment_success / containment_evaluated, 6)
        if containment_evaluated
        else None,
        "true_label_containment_missing_evidence_count": containment_missing,
        "true_label_containment_failures": containment_failures[:50],
        "family_outcomes": {family: dict(counter) for family, counter in sorted(family_outcomes.items())},
    }


def optimizer_replay(
    *,
    selected_path: Path | None,
    feedback: dict[str, Any],
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
    source_metrics = selected_candidate_metrics(rows, feedback)
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
        "source_candidate_metrics": source_metrics,
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
        feedback=feedback,
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
    source_metrics = [
        case["remediated_replay"].get("source_candidate_metrics") or {}
        for case in cases
        if case["remediated_replay"].get("source_candidate_metrics")
    ]
    containment_evaluated = sum(int(metrics.get("true_label_containment_evaluated_count") or 0) for metrics in source_metrics)
    containment_success = sum(int(metrics.get("true_label_containment_success_count") or 0) for metrics in source_metrics)
    containment_missing = sum(
        int(metrics.get("true_label_containment_missing_evidence_count") or 0) for metrics in source_metrics
    )
    source_candidates = sum(int(metrics.get("source_candidate_count") or 0) for metrics in source_metrics)
    unique_hashes = sum(int(metrics.get("unique_canonical_hash_count") or 0) for metrics in source_metrics)
    duplicate_hashes = sum(int(metrics.get("duplicate_hash_count") or 0) for metrics in source_metrics)
    target_r_known = sum(int(metrics.get("target_r_known_count") or 0) for metrics in source_metrics)
    target_r_match = sum(int(metrics.get("target_r_match_count") or 0) for metrics in source_metrics)
    compat_rows = sum(int(metrics.get("compatibility_evidence_row_count") or 0) for metrics in source_metrics)
    valuable_rows = sum(int(metrics.get("valuable_survival_row_count") or 0) for metrics in source_metrics)
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
            "source_candidate_count": source_candidates,
            "unique_canonical_hash_count": unique_hashes,
            "duplicate_hash_count": duplicate_hashes,
            "unique_decode_rate": round(unique_hashes / max(1, source_candidates), 6),
            "target_r_match_rate": round(target_r_match / max(1, target_r_known), 6) if target_r_known else None,
            "compatibility_evidence_rate": round(compat_rows / max(1, source_candidates), 6),
            "valuable_survival_rate": round(valuable_rows / max(1, source_candidates), 6),
            "true_label_containment_evaluated_count": containment_evaluated,
            "true_label_containment_success_count": containment_success,
            "true_label_containment_rate": round(containment_success / containment_evaluated, 6)
            if containment_evaluated
            else None,
            "true_label_containment_missing_evidence_count": containment_missing,
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
        f"- Remediated source unique-decode rate: {new.get('unique_decode_rate')}",
        f"- Remediated source target-r match rate: {new.get('target_r_match_rate')}",
        f"- Remediated source compatibility-evidence rate: {new.get('compatibility_evidence_rate')}",
        f"- Remediated source valuable-survival rate: {new.get('valuable_survival_rate')}",
        f"- True-label containment evaluated rows: {new.get('true_label_containment_evaluated_count')}",
        f"- True-label containment rate: {new.get('true_label_containment_rate')}",
        f"- True-label containment missing-evidence rows: {new.get('true_label_containment_missing_evidence_count')}",
        f"- Phase 7 minimum gate passed: `{summary['phase7_minimum_gate_passed']}`",
        "",
        "## Cases",
        "",
        "| case | submitted | accepted | labels | pairs | collapse rate | duplicate pair rate | old points/100 | source unique | compat rows | containment | remediated selected | stop/downrank |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for case in summary["cases"]:
        old_case = case["old_pipeline"]
        replay = case["remediated_replay"]
        source_metrics = replay.get("source_candidate_metrics") or {}
        containment = (
            f"{source_metrics.get('true_label_containment_success_count')}/"
            f"{source_metrics.get('true_label_containment_evaluated_count')}"
            if source_metrics.get("true_label_containment_evaluated_count")
            else "n/a"
        )
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
                    str(old_case.get("duplicated_pair_rate")),
                    str(old_case["estimated_points_per_100_submitted"]),
                    str(source_metrics.get("unique_decode_rate")),
                    str(source_metrics.get("compatibility_evidence_row_count")),
                    containment,
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
