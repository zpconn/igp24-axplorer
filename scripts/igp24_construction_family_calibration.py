#!/usr/bin/env python3
"""Calibrate IGP24 construction families from offline remediation artifacts.

This helper joins router rows, exact-label route outcomes, adaptive-reviewed
candidate pools, packet-optimizer rows, and chronological replay summaries into
one family-level advisory report. It is intentionally local/file-only: it does
not call SAIR, GAP, Magma, PARI, train a model, generate candidates, or submit
anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_packet_optimizer import candidate_features, group_compatibility, read_jsonl, route_metadata  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.constructions.registry import default_registry  # noqa: E402

SUMMARY_JSON = "construction_family_calibration_summary.json"
ROWS_JSONL = "construction_family_calibration_rows.jsonl"
REPORT_MD = "construction_family_calibration_report.md"

SAFETY_NOTE = (
    "Local-only construction-family calibration. It reads existing artifacts "
    "and writes advisory summaries; it does not submit to SAIR or claim exact "
    "Galois labels for compatibility-only rows."
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _short_list(values: Iterable[str], limit: int = 10) -> list[str]:
    return sorted({str(value) for value in values if str(value)})[:limit]


@dataclass
class FamilyStats:
    family: str
    raw_family_names: Counter[str] = field(default_factory=Counter)
    router_route_count: int = 0
    structurally_eligible_route_count: int = 0
    executable_generator_route_count: int = 0
    generation_ready_route_count: int = 0
    router_outcome_blocked_route_count: int = 0
    routed_pairs: Counter[str] = field(default_factory=Counter)
    router_blocking_reasons: Counter[str] = field(default_factory=Counter)
    generation_ready_blocking_reasons: Counter[str] = field(default_factory=Counter)
    route_outcome_count: int = 0
    exact_label_row_count: int = 0
    target_hit_count: int = 0
    false_target_count: int = 0
    submission_grade_count: int = 0
    blocked_route_count: int = 0
    observed_pair_counts: Counter[str] = field(default_factory=Counter)
    route_actions: Counter[str] = field(default_factory=Counter)
    adaptive_candidate_count: int = 0
    adaptive_packet_eligible_count: int = 0
    adaptive_target_compatible_count: int = 0
    adaptive_valuable_survival_count: int = 0
    adaptive_known_submission_count: int = 0
    adaptive_survivor_counts: list[int] = field(default_factory=list)
    adaptive_usable_prime_counts: list[int] = field(default_factory=list)
    replay_source_candidate_count: int = 0
    replay_valuable_survival_count: int = 0
    replay_containment_evaluated_count: int = 0
    replay_containment_success_count: int = 0
    replay_family_outcomes: Counter[str] = field(default_factory=Counter)
    packet_selected_count: int = 0
    packet_rejected_count: int = 0
    packet_reject_reasons: Counter[str] = field(default_factory=Counter)
    packet_candidate_count_from_summaries: int = 0
    packet_selected_count_from_summaries: int = 0

    def add_raw_family(self, raw: str | None) -> None:
        if raw:
            self.raw_family_names[str(raw)] += 1


class FamilyNormalizer:
    def __init__(self) -> None:
        self.registry = default_registry()

    def canonical(self, value: str | None) -> str:
        if not value:
            return "unknown"
        family = self.registry.resolve(str(value))
        if family is not None:
            return family.name
        return str(value)


def stats_for(families: dict[str, FamilyStats], family: str) -> FamilyStats:
    if family not in families:
        families[family] = FamilyStats(family=family)
    return families[family]


def ingest_router_routes(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        rows = read_jsonl(path) if path.exists() else []
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": len(rows)})
        for row in rows:
            raw_family = str(row.get("family") or "")
            family = normalizer.canonical(raw_family)
            stats = stats_for(families, family)
            stats.add_raw_family(raw_family)
            stats.router_route_count += 1
            stats.structurally_eligible_route_count += int(bool(row.get("structurally_eligible")))
            stats.executable_generator_route_count += int(bool(row.get("executable_generator_available")))
            stats.generation_ready_route_count += int(bool(row.get("executable_generation_ready") or row.get("generation_ready")))
            stats.router_outcome_blocked_route_count += int(bool(row.get("construction_outcome_blocking_reasons")))
            if row.get("pair_key"):
                stats.routed_pairs[str(row["pair_key"])] += 1
            stats.router_blocking_reasons.update(str(item) for item in row.get("blocking_reasons") or [])
            stats.generation_ready_blocking_reasons.update(
                str(item) for item in row.get("generation_ready_blocking_reasons") or []
            )
    return inputs


def ingest_route_outcomes(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        rows = read_jsonl(path) if path.exists() else []
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": len(rows)})
        for row in rows:
            raw_family = str(row.get("family") or "")
            family = normalizer.canonical(raw_family)
            stats = stats_for(families, family)
            stats.add_raw_family(raw_family)
            stats.route_outcome_count += 1
            stats.exact_label_row_count += _safe_int(row.get("exact_label_row_count"))
            stats.target_hit_count += _safe_int(row.get("target_hit_count"))
            stats.false_target_count += _safe_int(row.get("false_target_count"))
            stats.submission_grade_count += _safe_int(row.get("submission_grade_count"))
            stats.blocked_route_count += int(bool(row.get("block_repeat_exact_basin")))
            stats.route_actions[str(row.get("recommended_route_action") or "unknown")] += 1
            for pair, count in (row.get("observed_pair_counts") or {}).items():
                stats.observed_pair_counts[str(pair)] += _safe_int(count)
    return inputs


def _compat_from_candidate(row: dict[str, Any]) -> dict[str, Any]:
    compat = group_compatibility(row)
    adaptive = row.get("adaptive_frobenius")
    if not compat and isinstance(adaptive, dict):
        nested = adaptive.get("final_compatibility")
        if isinstance(nested, dict):
            compat = nested
    return compat if isinstance(compat, dict) else {}


def _survivor_count(row: dict[str, Any], compat: dict[str, Any]) -> int | None:
    adaptive_review = row.get("adaptive_review") if isinstance(row.get("adaptive_review"), dict) else {}
    sources = [
        adaptive_review.get("final_indexed_target_survivor_count"),
        compat.get("indexed_target_survivor_count"),
        compat.get("compatible_label_count"),
    ]
    for value in sources:
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _usable_prime_count(row: dict[str, Any]) -> int | None:
    adaptive_review = row.get("adaptive_review") if isinstance(row.get("adaptive_review"), dict) else {}
    adaptive = row.get("adaptive_frobenius") if isinstance(row.get("adaptive_frobenius"), dict) else {}
    for value in (
        row.get("frobenius_usable_prime_count"),
        row.get("usable_prime_count"),
        adaptive_review.get("usable_prime_count"),
        adaptive.get("usable_prime_count"),
    ):
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    patterns = row.get("mod_p_factorization_degree_patterns")
    if isinstance(patterns, list):
        return len(patterns)
    return None


def _family_from_candidate(row: dict[str, Any], normalizer: FamilyNormalizer) -> tuple[str, str | None]:
    route = route_metadata(row)
    features = candidate_features(row)
    metadata = row.get("generation_metadata") if isinstance(row.get("generation_metadata"), dict) else {}
    raw = (
        route.get("family")
        or features.get("construction_family")
        or metadata.get("construction_family")
        or row.get("source_strategy")
        or row.get("construction_family")
    )
    return normalizer.canonical(str(raw) if raw else None), str(raw) if raw else None


def ingest_adaptive_candidates(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        rows = read_jsonl(path) if path.exists() else []
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": len(rows)})
        for row in rows:
            family, raw_family = _family_from_candidate(row, normalizer)
            stats = stats_for(families, family)
            stats.add_raw_family(raw_family)
            stats.adaptive_candidate_count += 1
            stats.adaptive_packet_eligible_count += int(bool(row.get("eligible_for_packet")))
            stats.adaptive_target_compatible_count += int(bool(row.get("target_label_not_ruled_out")))
            stats.adaptive_valuable_survival_count += int(
                bool(row.get("any_valuable_target_not_ruled_out") or row.get("target_pair_valuable_not_ruled_out"))
            )
            stats.adaptive_known_submission_count += int(bool(row.get("known_submission_hash") or row.get("known_submission_hash_match")))
            compat = _compat_from_candidate(row)
            survivor_count = _survivor_count(row, compat)
            if survivor_count is not None:
                stats.adaptive_survivor_counts.append(survivor_count)
            usable_primes = _usable_prime_count(row)
            if usable_primes is not None:
                stats.adaptive_usable_prime_counts.append(usable_primes)
    return inputs


def ingest_packet_rejections(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        rows = read_jsonl(path) if path.exists() else []
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": len(rows)})
        for row in rows:
            family, raw_family = _family_from_candidate(row, normalizer)
            stats = stats_for(families, family)
            stats.add_raw_family(raw_family)
            stats.packet_rejected_count += 1
            stats.packet_reject_reasons.update(str(reason) for reason in row.get("reject_reasons") or [])
    return inputs


def ingest_packet_selected(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        rows = read_jsonl(path) if path.exists() else []
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": len(rows)})
        for row in rows:
            family, raw_family = _family_from_candidate(row, normalizer)
            stats = stats_for(families, family)
            stats.add_raw_family(raw_family)
            stats.packet_selected_count += 1
    return inputs


def ingest_packet_summaries(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        payload = load_json(path) if path.exists() else {}
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": int(bool(payload))})
        selected_diversity = payload.get("selected_diversity") if isinstance(payload.get("selected_diversity"), dict) else {}
        family_counts = selected_diversity.get("construction_family") if isinstance(selected_diversity.get("construction_family"), dict) else {}
        for raw_family, count in family_counts.items():
            family = normalizer.canonical(str(raw_family))
            stats = stats_for(families, family)
            stats.add_raw_family(str(raw_family))
            stats.packet_selected_count_from_summaries += _safe_int(count)
    return inputs


def ingest_replay_summaries(paths: Iterable[Path], families: dict[str, FamilyStats], normalizer: FamilyNormalizer) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for path in paths:
        payload = load_json(path) if path.exists() else {}
        cases = payload.get("cases") if isinstance(payload.get("cases"), list) else []
        inputs.append({"path": str(path), "exists": path.exists(), "rows_loaded": len(cases)})
        for case in cases:
            metrics = ((case.get("remediated_replay") or {}).get("source_candidate_metrics") or {})
            family_counts = metrics.get("construction_family_counts") or {}
            valuable = _safe_int(metrics.get("valuable_survival_row_count"))
            source_count = _safe_int(metrics.get("source_candidate_count"))
            containment_eval = _safe_int(metrics.get("true_label_containment_evaluated_count"))
            containment_success = _safe_int(metrics.get("true_label_containment_success_count"))
            for raw_family, count in family_counts.items():
                family = normalizer.canonical(str(raw_family))
                stats = stats_for(families, family)
                stats.add_raw_family(str(raw_family))
                count_int = _safe_int(count)
                fraction = count_int / max(1, source_count)
                stats.replay_source_candidate_count += count_int
                stats.replay_valuable_survival_count += round(valuable * fraction)
                stats.replay_containment_evaluated_count += round(containment_eval * fraction)
                stats.replay_containment_success_count += round(containment_success * fraction)
            for raw_family, outcomes in (metrics.get("family_outcomes") or {}).items():
                family = normalizer.canonical(str(raw_family))
                stats = stats_for(families, family)
                stats.add_raw_family(str(raw_family))
                if isinstance(outcomes, dict):
                    for label, count in outcomes.items():
                        stats.replay_family_outcomes[str(label)] += _safe_int(count)
    return inputs


def recommend_action(stats: FamilyStats) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if stats.blocked_route_count:
        reasons.append("exact_label_route_outcome_blocked_repeat_basin")
        return "block_repeat_exact_basin", reasons
    if stats.exact_label_row_count >= 3 and stats.false_target_count == stats.exact_label_row_count and stats.target_hit_count == 0:
        reasons.append("all_exact_rows_false_targets")
        return "block_repeat_exact_basin", reasons
    if stats.adaptive_candidate_count and stats.adaptive_valuable_survival_count == 0:
        reasons.append("adaptive_review_found_no_valuable_survivors")
        return "do_not_widen_without_material_structural_change", reasons
    if stats.routed_pairs and stats.adaptive_candidate_count >= 3 and stats.adaptive_target_compatible_count == 0:
        reasons.append("adaptive_review_found_no_target_compatible_survivors")
        if stats.adaptive_valuable_survival_count:
            reasons.append("valuable_survivors_are_non_target_review_only")
            return "review_only_until_reparameterized", reasons
        return "do_not_widen_without_material_structural_change", reasons
    if stats.replay_source_candidate_count >= 3 and not stats.replay_valuable_survival_count:
        reasons.append("historical_replay_collapse_has_no_valuable_survivors")
        if stats.family == "generic_sparse_random":
            return "baseline_only_until_new_conditioning", reasons
        return "review_only_until_reparameterized", reasons
    if stats.executable_generator_route_count and not stats.router_outcome_blocked_route_count:
        reasons.append("executable_route_available_without_exact_negative_outcome")
        if stats.adaptive_candidate_count == 0:
            reasons.append("needs_bounded_adaptive_experiment")
        return "run_bounded_adaptive_experiment", reasons
    if stats.structurally_eligible_route_count and not stats.executable_generator_route_count:
        reasons.append("structural_route_exists_but_no_executable_generator")
        return "candidate_for_generator_implementation", reasons
    reasons.append("insufficient_family_evidence")
    return "review_only_insufficient_evidence", reasons


def family_row(stats: FamilyStats) -> dict[str, Any]:
    action, reasons = recommend_action(stats)
    adaptive_median_survivors = median(stats.adaptive_survivor_counts) if stats.adaptive_survivor_counts else None
    adaptive_median_primes = median(stats.adaptive_usable_prime_counts) if stats.adaptive_usable_prime_counts else None
    containment_rate = (
        stats.replay_containment_success_count / stats.replay_containment_evaluated_count
        if stats.replay_containment_evaluated_count
        else None
    )
    return {
        "record_type": "igp24_construction_family_calibration_row",
        "schema_version": 1,
        "family": stats.family,
        "raw_family_names": dict(sorted(stats.raw_family_names.items())),
        "router_route_count": stats.router_route_count,
        "structurally_eligible_route_count": stats.structurally_eligible_route_count,
        "executable_generator_route_count": stats.executable_generator_route_count,
        "generation_ready_route_count": stats.generation_ready_route_count,
        "router_outcome_blocked_route_count": stats.router_outcome_blocked_route_count,
        "top_routed_pairs": _short_list(stats.routed_pairs),
        "router_blocking_reasons": dict(sorted(stats.router_blocking_reasons.items())),
        "generation_ready_blocking_reasons": dict(sorted(stats.generation_ready_blocking_reasons.items())),
        "route_outcome_count": stats.route_outcome_count,
        "exact_label_row_count": stats.exact_label_row_count,
        "target_hit_count": stats.target_hit_count,
        "false_target_count": stats.false_target_count,
        "submission_grade_count": stats.submission_grade_count,
        "blocked_route_count": stats.blocked_route_count,
        "observed_pair_counts": dict(sorted(stats.observed_pair_counts.items())),
        "route_actions": dict(sorted(stats.route_actions.items())),
        "adaptive_candidate_count": stats.adaptive_candidate_count,
        "adaptive_packet_eligible_count": stats.adaptive_packet_eligible_count,
        "adaptive_target_compatible_count": stats.adaptive_target_compatible_count,
        "adaptive_valuable_survival_count": stats.adaptive_valuable_survival_count,
        "adaptive_known_submission_count": stats.adaptive_known_submission_count,
        "adaptive_median_indexed_survivor_count": adaptive_median_survivors,
        "adaptive_median_usable_prime_count": adaptive_median_primes,
        "replay_source_candidate_count": stats.replay_source_candidate_count,
        "replay_valuable_survival_count": stats.replay_valuable_survival_count,
        "replay_containment_evaluated_count": stats.replay_containment_evaluated_count,
        "replay_containment_success_count": stats.replay_containment_success_count,
        "replay_true_label_containment_rate": round(containment_rate, 6) if containment_rate is not None else None,
        "replay_family_outcomes": dict(sorted(stats.replay_family_outcomes.items())),
        "packet_selected_count": stats.packet_selected_count,
        "packet_rejected_count": stats.packet_rejected_count,
        "packet_reject_reasons": dict(sorted(stats.packet_reject_reasons.items())),
        "packet_candidate_count_from_summaries": stats.packet_candidate_count_from_summaries,
        "packet_selected_count_from_summaries": stats.packet_selected_count_from_summaries,
        "recommended_action": action,
        "recommendation_reasons": reasons,
        "score_estimate_status": "unavailable_uncalibrated",
        "soundness": "family_advisory_not_exact_label_evidence",
    }


def build_summary(rows: list[dict[str, Any]], inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    action_counts = Counter(str(row["recommended_action"]) for row in rows)
    runnable = [
        row
        for row in rows
        if row["recommended_action"] in {"run_bounded_adaptive_experiment", "candidate_for_generator_implementation"}
    ]
    blocked = [row for row in rows if row["recommended_action"] == "block_repeat_exact_basin"]
    return {
        "record_type": "igp24_construction_family_calibration_summary",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_construction_family_calibration.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "inputs": inputs,
        "family_count": len(rows),
        "recommended_action_counts": dict(sorted(action_counts.items())),
        "blocked_family_count": len(blocked),
        "bounded_experiment_candidate_count": len(runnable),
        "top_bounded_experiment_candidates": [
            {
                "family": row["family"],
                "recommended_action": row["recommended_action"],
                "structurally_eligible_route_count": row["structurally_eligible_route_count"],
                "executable_generator_route_count": row["executable_generator_route_count"],
                "adaptive_candidate_count": row["adaptive_candidate_count"],
                "reasons": row["recommendation_reasons"],
            }
            for row in runnable[:10]
        ],
        "blocked_families": [
            {
                "family": row["family"],
                "blocked_route_count": row["blocked_route_count"],
                "exact_label_row_count": row["exact_label_row_count"],
                "false_target_count": row["false_target_count"],
                "observed_pair_counts": row["observed_pair_counts"],
            }
            for row in blocked
        ],
        "expected_points_status": "unavailable_uncalibrated",
        "live_submission_recommended_now": False,
    }


def render_report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Construction Family Calibration",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Families: `{summary['family_count']}`",
        f"- Recommended actions: `{json.dumps(summary['recommended_action_counts'], sort_keys=True)}`",
        f"- Expected points: `{summary['expected_points_status']}`",
        f"- Safety: {summary['safety_note']}",
        "- Live submission recommended now: `False`",
        "",
        "## Family Actions",
        "",
        "| family | action | structural | executable | adaptive rows | valuable adaptive | exact rows | target hits | false targets | packet selected | reasons |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['family']}`",
                    f"`{row['recommended_action']}`",
                    str(row["structurally_eligible_route_count"]),
                    str(row["executable_generator_route_count"]),
                    str(row["adaptive_candidate_count"]),
                    str(row["adaptive_valuable_survival_count"]),
                    str(row["exact_label_row_count"]),
                    str(row["target_hit_count"]),
                    str(row["false_target_count"]),
                    str(row["packet_selected_count"] or row["packet_selected_count_from_summaries"]),
                    ", ".join(row["recommendation_reasons"]) or "-",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report is an advisory calibration layer, not a verifier. It does not turn compatibility survivors into exact labels or expected official points.",
            "Families marked for bounded experiments still need fresh candidate generation, known-hash exclusion, adaptive Frobenius review, exact-label verification, and the usual no-live-submission gate.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_calibration(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    normalizer = FamilyNormalizer()
    families: dict[str, FamilyStats] = {}
    inputs = {
        "router_routes_jsonl": ingest_router_routes(args.router_routes_jsonl or [], families, normalizer),
        "route_outcomes_jsonl": ingest_route_outcomes(args.route_outcomes_jsonl or [], families, normalizer),
        "adaptive_candidates_jsonl": ingest_adaptive_candidates(args.adaptive_candidates_jsonl or [], families, normalizer),
        "packet_rejected_jsonl": ingest_packet_rejections(args.packet_rejected_jsonl or [], families, normalizer),
        "packet_selected_jsonl": ingest_packet_selected(args.packet_selected_jsonl or [], families, normalizer),
        "packet_summary_json": ingest_packet_summaries(args.packet_summary_json or [], families, normalizer),
        "replay_summary_json": ingest_replay_summaries(args.replay_summary_json or [], families, normalizer),
    }
    rows = [family_row(stats) for stats in families.values()]
    rows.sort(
        key=lambda row: (
            row["recommended_action"] != "block_repeat_exact_basin",
            row["recommended_action"] != "run_bounded_adaptive_experiment",
            row["recommended_action"] != "candidate_for_generator_implementation",
            -row["structurally_eligible_route_count"],
            -row["adaptive_valuable_survival_count"],
            row["family"],
        )
    )
    return rows, build_summary(rows, inputs)


def write_outputs(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary_json": output_dir / SUMMARY_JSON,
        "rows_jsonl": output_dir / ROWS_JSONL,
        "report_md": output_dir / REPORT_MD,
    }
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    write_json(paths["summary_json"], summary)
    write_jsonl(paths["rows_jsonl"], rows)
    paths["report_md"].write_text(render_report(summary, rows), encoding="utf-8")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--router_routes_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--route_outcomes_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--adaptive_candidates_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--packet_rejected_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--packet_selected_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--packet_summary_json", type=Path, action="append", default=[])
    parser.add_argument("--replay_summary_json", type=Path, action="append", default=[])
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, summary = build_calibration(args)
    paths = write_outputs(args.output_dir, rows, summary)
    print(f"family_count\t{summary['family_count']}")
    print(f"recommended_action_counts\t{json.dumps(summary['recommended_action_counts'], sort_keys=True)}")
    print(f"bounded_experiment_candidate_count\t{summary['bounded_experiment_candidate_count']}")
    print(f"blocked_family_count\t{summary['blocked_family_count']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
