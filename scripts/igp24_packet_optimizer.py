#!/usr/bin/env python3
"""Optimize IGP24 candidate packets for valuable pair coverage.

This is a packet selector, not a verifier. It expects a locally filtered
candidate pool and greedily selects rows that maximize the union of plausible
valuable ``(24Tt, r)`` pairs while enforcing provenance/diversity caps.
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

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.verifiers.sair_api import format_polynomial_line  # noqa: E402


DEFAULT_SCORE_PLAN = REPO_ROOT / "data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json"

SUMMARY_JSON = "packet_optimizer_summary.json"
REPORT_MD = "packet_optimizer_report.md"
SELECTED_JSONL = "packet_optimizer_selected.jsonl"
REJECTED_JSONL = "packet_optimizer_rejected.jsonl"
COEFFICIENTS_TXT = "packet_optimizer_coefficients.txt"
HASHES_TXT = "packet_optimizer_hashes.txt"
DEFAULT_MINIMUM_FROBENIUS_PRIMES = 10


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def load_score_plan(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_pair: dict[str, dict[str, Any]] = {}
    for key in (
        "ranked_targets",
        "top_uncovered_targets",
        "top_score_followup_targets",
        "top_api_scoreable_targets",
        "top_lightly_solved_targets",
    ):
        for row in payload.get(key) or []:
            if isinstance(row, dict) and row.get("pair_key"):
                by_pair[str(row["pair_key"])] = row
    return by_pair


def load_known_submission_hashes(paths: Iterable[Path] | None) -> dict[str, list[dict[str, Any]]]:
    hashes: dict[str, list[dict[str, Any]]] = {}
    for path in paths or []:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            candidate_hash = str(row.get("canonical_hash") or "")
            if candidate_hash:
                hashes.setdefault(candidate_hash, []).append(
                    {
                        "submission_id": row.get("submission_id"),
                        "submitted_line_number": row.get("submitted_line_number"),
                        "status": row.get("status"),
                        "status_class": row.get("status_class"),
                        "label": row.get("label"),
                        "t": row.get("t"),
                        "r": row.get("r"),
                        "pair_key": row.get("pair_key"),
                        "scoreable": row.get("scoreable"),
                        "scoring_status": row.get("scoring_status"),
                        "disc_source": row.get("disc_source"),
                        "field_disc_abs": row.get("field_disc_abs"),
                    }
                )
    return hashes


def known_submission_matches(
    canonical_hash: str,
    known_submission_hashes: dict[str, list[dict[str, Any]]] | set[str] | None,
) -> list[dict[str, Any]]:
    if not canonical_hash or not known_submission_hashes:
        return []
    if isinstance(known_submission_hashes, set):
        return [{"canonical_hash": canonical_hash}] if canonical_hash in known_submission_hashes else []
    return list(known_submission_hashes.get(canonical_hash, []))


def nested_dict(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key)
    return value if isinstance(value, dict) else {}


def candidate_payload(row: dict[str, Any]) -> dict[str, Any]:
    candidate = nested_dict(row, "candidate")
    return candidate if candidate else row


def candidate_features(row: dict[str, Any]) -> dict[str, Any]:
    features = nested_dict(row, "features") or nested_dict(row, "anti_basin_features")
    if features:
        return features
    candidate = candidate_payload(row)
    metadata = nested_dict(candidate, "generation_metadata")
    return {
        "canonical_hash": candidate.get("canonical_hash"),
        "short_hash": str(candidate.get("canonical_hash") or "")[:12],
        "label": candidate.get("label") or candidate.get("verified_group_label"),
        "pair_key": candidate.get("pair_key") or candidate.get("verified_pair_key"),
        "r": candidate.get("real_root_count") or candidate.get("r"),
        "construction_family": metadata.get("construction_family") or metadata.get("source_family") or candidate.get("construction_family"),
        "template_family_id": metadata.get("template_family_id") or candidate.get("template_family_id"),
        "perturbation_mode": metadata.get("perturbation_mode") or candidate.get("perturbation_mode"),
        "basin_fingerprint": metadata.get("basin_fingerprint") or candidate.get("basin_fingerprint"),
        "mod_p_pattern_signature": candidate.get("mod_p_pattern_signature"),
        "family_key": metadata.get("family_key") or candidate.get("family_key"),
    }


def group_compatibility(row: dict[str, Any]) -> dict[str, Any]:
    candidate = candidate_payload(row)
    for source in (row, candidate, nested_dict(row, "candidate")):
        for key in ("group_compatibility", "candidate_group_compatibility"):
            value = source.get(key) if isinstance(source, dict) else None
            if isinstance(value, dict):
                return value
    return {}


def _int_or_none(value: Any) -> int | None:
    try:
        if value is not None and value != "":
            return int(value)
    except (TypeError, ValueError):
        return None
    return None


def frobenius_evidence_budget(row: dict[str, Any], compat: dict[str, Any]) -> dict[str, Any]:
    """Return the largest explicit usable-prime count attached to a row.

    Compatibility over a partial index is only useful as target-exclusion
    evidence when it is backed by enough Frobenius observations. Older rows
    may store this evidence in several places, so this helper accepts the
    current adaptive fields as well as legacy pattern lists.
    """

    candidate = candidate_payload(row)
    sources: list[tuple[str, dict[str, Any]]] = []
    for name, source in (("row", row), ("candidate", candidate), ("group_compatibility", compat)):
        if isinstance(source, dict):
            sources.append((name, source))
    best_count = 0
    best_source = "missing"
    for source_name, source in sources:
        for key in (
            "frobenius_usable_prime_count",
            "usable_prime_count",
            "adaptive_usable_prime_count",
            "prime_count",
        ):
            count = _int_or_none(source.get(key))
            if count is not None and count > best_count:
                best_count = count
                best_source = f"{source_name}.{key}"
        for key in ("adaptive_frobenius_evidence", "adaptive_frobenius", "frobenius_evidence"):
            nested = source.get(key)
            if not isinstance(nested, dict):
                continue
            count = _int_or_none(nested.get("usable_prime_count") or nested.get("frobenius_usable_prime_count"))
            if count is None:
                observations = nested.get("observations")
                patterns = nested.get("mod_p_factorization_degree_patterns")
                if isinstance(observations, list):
                    count = len(observations)
                elif isinstance(patterns, list):
                    count = len(patterns)
            if count is not None and count > best_count:
                best_count = count
                best_source = f"{source_name}.{key}"
        evidence = source.get("evidence")
        if isinstance(evidence, dict):
            primes = evidence.get("primes")
            if isinstance(primes, list) and len(primes) > best_count:
                best_count = len(primes)
                best_source = f"{source_name}.evidence.primes"
        patterns = source.get("mod_p_factorization_degree_patterns")
        if isinstance(patterns, list) and len(patterns) > best_count:
            best_count = len(patterns)
            best_source = f"{source_name}.mod_p_factorization_degree_patterns"
    return {"usable_prime_count": best_count, "source": best_source}


def exported_coefficients(row: dict[str, Any]) -> list[int] | None:
    candidate = candidate_payload(row)
    for source in (row, candidate):
        coeffs = source.get("exported_coefficients") if isinstance(source, dict) else None
        if isinstance(coeffs, list) and len(coeffs) == 25:
            return [int(value) for value in coeffs]
    return None


def pair_key_from_features(features: dict[str, Any]) -> str | None:
    pair_key = features.get("pair_key")
    if pair_key:
        return str(pair_key)
    label = features.get("label")
    r_value = features.get("r")
    if not label or r_value is None:
        return None
    try:
        return f"{label}|r={int(r_value)}"
    except (TypeError, ValueError):
        return None


def pair_economics(pair_key: str, score_plan: dict[str, dict[str, Any]], fallback_kind: str) -> dict[str, Any]:
    row = score_plan.get(pair_key) or {}
    max_points = row.get("maximum_possible_points")
    est_points = row.get("estimated_expected_points")
    if max_points is None:
        max_points = 1.0 if fallback_kind == "uncovered" else 0.015625 if fallback_kind == "low_team" else 0.0
    if est_points is None:
        est_points = max_points
    return {
        "pair_key": pair_key,
        "maximum_possible_points": float(max_points or 0.0),
        "estimated_expected_points": float(est_points or 0.0),
        "score_ceiling_class": row.get("score_ceiling_class")
        or ("uncovered_first_team_one_point" if fallback_kind == "uncovered" else fallback_kind),
        "category": row.get("category"),
        "r": row.get("r"),
        "label": row.get("label") or pair_key.split("|", 1)[0],
    }


def add_pairs(
    out: dict[str, dict[str, Any]],
    pairs: Iterable[str],
    *,
    score_plan: dict[str, dict[str, Any]],
    fallback_kind: str,
) -> None:
    for pair in pairs:
        if pair and pair not in out:
            out[str(pair)] = pair_economics(str(pair), score_plan, fallback_kind)


def normalize_candidate(
    row: dict[str, Any],
    *,
    score_plan: dict[str, dict[str, Any]],
    require_eligible: bool,
    known_submission_hashes: dict[str, list[dict[str, Any]]] | set[str] | None = None,
    minimum_frobenius_primes: int = DEFAULT_MINIMUM_FROBENIUS_PRIMES,
) -> dict[str, Any]:
    candidate = candidate_payload(row)
    features = candidate_features(row)
    compat = group_compatibility(row)
    coeffs = exported_coefficients(row)
    canonical_hash = str(row.get("canonical_hash") or features.get("canonical_hash") or "")
    short_hash = str(row.get("short_hash") or features.get("short_hash") or canonical_hash[:12])
    pair_values: dict[str, dict[str, Any]] = {}
    add_pairs(pair_values, compat.get("compatible_uncovered_pairs") or [], score_plan=score_plan, fallback_kind="uncovered")
    add_pairs(pair_values, compat.get("compatible_low_team_pairs") or [], score_plan=score_plan, fallback_kind="low_team")
    add_pairs(pair_values, compat.get("compatible_crowded_pairs") or [], score_plan=score_plan, fallback_kind="crowded")
    exact_pair = pair_key_from_features(features)
    exact_pair_verified = bool(
        exact_pair
        and (
            row.get("exact_label_verified")
            or row.get("verified_label")
            or row.get("verified_group_label")
            or candidate.get("exact_label_verified")
            or candidate.get("verified_label")
            or candidate.get("verified_group_label")
            or features.get("exact_label_verified")
            or features.get("exact_verified_pair")
        )
    )
    if exact_pair_verified:
        fallback = "uncovered" if str(exact_pair) in score_plan and score_plan[str(exact_pair)].get("progress_state") == "remaining" else "exact_pair"
        add_pairs(pair_values, [exact_pair], score_plan=score_plan, fallback_kind=fallback)
    frobenius_budget = frobenius_evidence_budget(row, compat)
    usable_prime_count = int(frobenius_budget["usable_prime_count"])
    minimum_frobenius_primes = int(minimum_frobenius_primes)
    sufficient_frobenius_evidence = bool(exact_pair_verified or usable_prime_count >= minimum_frobenius_primes)
    if exact_pair_verified:
        adaptive_evidence_status = "exact_verified_pair_no_adaptive_required"
    elif sufficient_frobenius_evidence:
        adaptive_evidence_status = "sufficient_adaptive_frobenius_evidence"
    else:
        adaptive_evidence_status = "insufficient_adaptive_frobenius_evidence"

    indexed_survivor_count = int(
        compat.get("indexed_target_survivor_count")
        or compat.get("compatible_label_count")
        or len(compat.get("indexed_target_labels_not_ruled_out") or compat.get("compatible_labels") or [])
        or 0
    )
    best_case_points = min(1.0, max((float(row["maximum_possible_points"]) for row in pair_values.values()), default=0.0))
    exact_estimated_points = None
    if exact_pair_verified and exact_pair in pair_values:
        exact_estimated_points = min(1.0, float(pair_values[exact_pair].get("estimated_expected_points") or 0.0))
    expected_points_status = "available_exact_verified_pair" if exact_estimated_points is not None else "unavailable_uncalibrated"
    uncovered_pairs = [key for key, value in pair_values.items() if value.get("score_ceiling_class") == "uncovered_first_team_one_point" or value.get("category") == "uncovered_signature"]
    low_team_pairs = [
        key
        for key, value in pair_values.items()
        if key not in uncovered_pairs and float(value.get("maximum_possible_points") or 0.0) >= 0.001
    ]
    crowded_pairs = [key for key in pair_values if key not in uncovered_pairs and key not in low_team_pairs]
    crowded_only = bool(compat.get("crowded_only")) or (bool(pair_values) and not uncovered_pairs and not low_team_pairs)

    eligible = bool(row.get("eligible_for_packet", row.get("eligible", True)))
    fatal = list(row.get("fatal_risk_reasons") or [])
    reject_reasons: list[str] = []
    if require_eligible and not eligible:
        reject_reasons.append("not_eligible_for_packet")
    if fatal:
        reject_reasons.append("fatal_risk_reasons")
    if not pair_values:
        reject_reasons.append("missing_pair_or_compatibility_evidence")
    if pair_values and not sufficient_frobenius_evidence:
        reject_reasons.append("insufficient_adaptive_frobenius_evidence")
    if crowded_only:
        reject_reasons.append("crowded_only")
    known_matches = known_submission_matches(canonical_hash, known_submission_hashes)
    known_submission_hash = bool(known_matches)
    if known_submission_hash:
        reject_reasons.append("known_submission_hash")

    cluster_parts = sorted(pair_values)[:24]
    cluster = "|".join(cluster_parts) if cluster_parts else f"unknown_r{features.get('r')}"
    anti_basin_score = float(row.get("anti_basin_score", row.get("score", 0.0)) or 0.0)
    return {
        "canonical_hash": canonical_hash,
        "short_hash": short_hash,
        "features": features,
        "pair_values": pair_values,
        "valuable_targets_not_ruled_out": sorted(set(uncovered_pairs + low_team_pairs)),
        "possible_uncovered_pairs": uncovered_pairs,
        "possible_low_team_pairs": low_team_pairs,
        "possible_crowded_pairs": crowded_pairs,
        "indexed_target_survivor_count": indexed_survivor_count,
        "indexed_target_labels_not_ruled_out": compat.get("indexed_target_labels_not_ruled_out") or compat.get("compatible_labels") or [],
        "index_scope": compat.get("index_scope"),
        "indexed_group_count": compat.get("indexed_group_count"),
        "expected_global_group_count": compat.get("expected_global_group_count"),
        "global_index_complete": compat.get("global_index_complete"),
        "unindexed_label_mass_unknown": compat.get("unindexed_label_mass_unknown"),
        "soundness": compat.get("soundness") or "necessary_target_exclusion_only",
        "evidence_strength": (
            "insufficient_modular_cycle_evidence"
            if compat.get("status") == "insufficient_cycle_evidence"
            else compat.get("evidence_strength") or "unknown"
        ),
        "frobenius_usable_prime_count": usable_prime_count,
        "frobenius_evidence_source": frobenius_budget["source"],
        "minimum_frobenius_primes_required": minimum_frobenius_primes,
        "sufficient_frobenius_evidence": sufficient_frobenius_evidence,
        "adaptive_evidence_status": adaptive_evidence_status,
        "compatible_label_count": indexed_survivor_count,
        "compatible_label_count_deprecated": True,
        "compatibility_ambiguity_factor": None,
        "compatible_label_cluster": cluster,
        "best_case_points": round(best_case_points, 12),
        "maximum_possible_points": round(best_case_points, 12),
        "estimated_expected_points": round(exact_estimated_points, 12) if exact_estimated_points is not None else None,
        "expected_points_status": expected_points_status,
        "expected_points_basis": "exact_verified_pair_official_economics" if exact_estimated_points is not None else "unavailable_no_calibrated_probability_model",
        "anti_basin_score": anti_basin_score,
        "eligible_for_optimization": not reject_reasons,
        "reject_reasons": reject_reasons,
        "known_submission_hash": known_submission_hash,
        "known_submission_matches": known_matches,
        "has_coefficients": coeffs is not None,
        "exported_coefficients": coeffs,
        "source_row": row,
    }


def cap_key(candidate: dict[str, Any], field: str) -> str:
    features = candidate["features"]
    if field == "compatible_label_cluster":
        return str(candidate.get("compatible_label_cluster") or "")
    if field == "r":
        return str(features.get("r") or "")
    return str(features.get(field) or "")


def within_caps(candidate: dict[str, Any], counts: dict[str, Counter[str]], caps: dict[str, int]) -> tuple[bool, str | None]:
    for field, cap in caps.items():
        if cap <= 0:
            continue
        key = cap_key(candidate, field)
        if key and counts[field][key] >= cap:
            return False, f"cap_{field}:{key}"
    return True, None


def greedy_select(candidates: list[dict[str, Any]], *, packet_limit: int, caps: dict[str, int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    covered_pairs: set[str] = set()
    selected_hashes: set[str] = set()
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    remaining = list(candidates)
    while len(selected) < packet_limit:
        best: dict[str, Any] | None = None
        best_key: tuple[float, float, float, float, str] | None = None
        best_marginal_pairs: dict[str, dict[str, Any]] = {}
        best_cap_reason: str | None = None
        for candidate in remaining:
            if not candidate["eligible_for_optimization"]:
                continue
            if candidate["canonical_hash"] and candidate["canonical_hash"] in selected_hashes:
                continue
            ok, cap_reason = within_caps(candidate, counts, caps)
            if not ok:
                if best is None:
                    best_cap_reason = cap_reason
                continue
            marginal_pairs = {
                pair: value for pair, value in candidate["pair_values"].items() if pair not in covered_pairs
            }
            marginal = min(1.0, max((float(value.get("maximum_possible_points") or 0.0) for value in marginal_pairs.values()), default=0.0))
            if marginal <= 0:
                continue
            key = (
                marginal,
                float(candidate.get("best_case_points") or candidate.get("maximum_possible_points") or 0.0),
                float(len(marginal_pairs)),
                float(candidate.get("anti_basin_score") or 0.0),
                str(candidate.get("short_hash") or ""),
            )
            if best_key is None or key > best_key:
                best = candidate
                best_key = key
                best_marginal_pairs = marginal_pairs
                best_cap_reason = None
        if best is None:
            if best_cap_reason:
                for candidate in remaining:
                    if candidate["eligible_for_optimization"]:
                        candidate.setdefault("optimizer_stop_reasons", []).append(best_cap_reason)
            break
        best = dict(best)
        best["optimizer_rank"] = len(selected) + 1
        best["marginal_pair_values"] = best_marginal_pairs
        best["marginal_best_case_points"] = round(best_key[0] if best_key else 0.0, 12)
        best["marginal_estimated_points"] = None
        selected.append(best)
        for pair in best_marginal_pairs:
            covered_pairs.add(pair)
        if best["canonical_hash"]:
            selected_hashes.add(best["canonical_hash"])
        for field in caps:
            key = cap_key(best, field)
            if key:
                counts[field][key] += 1
        remaining = [candidate for candidate in remaining if candidate["canonical_hash"] != best["canonical_hash"]]
    selected_ids = {row["canonical_hash"] for row in selected if row.get("canonical_hash")}
    for candidate in candidates:
        if candidate.get("canonical_hash") in selected_ids:
            continue
        rejected.append(candidate)
    return selected, rejected


def summarize(
    *,
    candidate_paths: list[Path],
    candidates: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    caps: dict[str, int],
    output_files: dict[str, str],
    minimum_frobenius_primes: int = DEFAULT_MINIMUM_FROBENIUS_PRIMES,
) -> dict[str, Any]:
    covered_uncovered = sorted({pair for row in selected for pair in row["possible_uncovered_pairs"]})
    covered_low = sorted({pair for row in selected for pair in row["possible_low_team_pairs"]})
    selected_clusters = sorted({str(row["compatible_label_cluster"]) for row in selected})
    selected_features = [row["features"] for row in selected]
    all_expected_available = bool(selected) and all(
        row.get("expected_points_status") == "available_exact_verified_pair" for row in selected
    )
    packet_best_case = round(sum(float(row.get("best_case_points") or row.get("maximum_possible_points") or 0.0) for row in selected), 12)
    exact_expected = (
        round(sum(float(row.get("estimated_expected_points") or 0.0) for row in selected), 12)
        if all_expected_available
        else None
    )
    return {
        "schema_version": 1,
        "record_type": "igp24_packet_optimizer",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_packet_optimizer.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety": {
            "sair_submission": False,
            "sair_dry_run": False,
            "network_calls": False,
            "api_key_recorded": False,
        },
        "inputs": {
            "candidate_paths": [str(path) for path in candidate_paths],
            "candidate_count": len(candidates),
            "caps": caps,
            "minimum_frobenius_primes": int(minimum_frobenius_primes),
        },
        "candidate_count": len(candidates),
        "eligible_candidate_count": sum(1 for row in candidates if row["eligible_for_optimization"]),
        "selected_rows": len(selected),
        "rejected_rows": len(rejected),
        "reject_reason_counts": dict(Counter(reason for row in rejected for reason in row.get("reject_reasons", []))),
        "crowded_only_candidates_rejected": sum(1 for row in rejected if "crowded_only" in row.get("reject_reasons", [])),
        "known_submission_hash_candidates_rejected": sum(
            1 for row in rejected if "known_submission_hash" in row.get("reject_reasons", [])
        ),
        "pair_evidence_missing_candidates": sum(
            1 for row in candidates if "missing_pair_or_compatibility_evidence" in row.get("reject_reasons", [])
        ),
        "insufficient_adaptive_frobenius_candidates": sum(
            1 for row in candidates if "insufficient_adaptive_frobenius_evidence" in row.get("reject_reasons", [])
        ),
        "selected_possible_uncovered_pair_count": len(covered_uncovered),
        "selected_possible_low_team_pair_count": len(covered_low),
        "selected_possible_uncovered_pairs": covered_uncovered[:100],
        "selected_possible_low_team_pairs": covered_low[:100],
        "distinct_compatible_label_clusters": len(selected_clusters),
        "selected_compatible_label_clusters": selected_clusters[:100],
        "best_case_packet_points": packet_best_case,
        "expected_score_ceiling": packet_best_case,
        "expected_score_ceiling_deprecated": True,
        "expected_score_estimate": exact_expected,
        "expected_points_status": "available_exact_verified_pairs" if all_expected_available else "unavailable_uncalibrated",
        "expected_points_basis": (
            "exact_verified_pair_official_economics"
            if all_expected_available
            else "unavailable_no_calibrated_probability_model_over_indexed_and_unindexed_labels"
        ),
        "selected_diversity": {
            "construction_family": dict(Counter(str(row.get("construction_family") or "") for row in selected_features)),
            "template_family_id": dict(Counter(str(row.get("template_family_id") or "") for row in selected_features)),
            "perturbation_mode": dict(Counter(str(row.get("perturbation_mode") or "") for row in selected_features)),
            "basin_fingerprint": dict(Counter(str(row.get("basin_fingerprint") or "") for row in selected_features)),
            "mod_p_pattern_signature": dict(Counter(str(row.get("mod_p_pattern_signature") or "") for row in selected_features)),
            "r": dict(Counter(str(row.get("r") or "") for row in selected_features)),
        },
        "local_packet_ready_for_review": bool(selected and covered_uncovered or covered_low),
        "live_submission_recommended_now": False,
        "live_submission_reason": "optimizer never authorizes live SAIR submission; exact packet still needs local validation, dry-run, and explicit user approval",
        "selected_rows_summary": [
            {
                "rank": row["optimizer_rank"],
                "short_hash": row["short_hash"],
                "marginal_best_case_points": row.get("marginal_best_case_points"),
                "marginal_estimated_points": row.get("marginal_estimated_points"),
                "best_case_points": row.get("best_case_points"),
                "maximum_possible_points": row["maximum_possible_points"],
                "expected_points_status": row.get("expected_points_status"),
                "possible_uncovered_pairs": row["possible_uncovered_pairs"][:10],
                "possible_uncovered_pair_count": len(row["possible_uncovered_pairs"]),
                "possible_low_team_pairs": row["possible_low_team_pairs"][:10],
                "possible_low_team_pair_count": len(row["possible_low_team_pairs"]),
                "valuable_targets_not_ruled_out": row.get("valuable_targets_not_ruled_out", [])[:10],
                "valuable_targets_not_ruled_out_count": len(row.get("valuable_targets_not_ruled_out", [])),
                "indexed_target_survivor_count": row.get("indexed_target_survivor_count"),
                "compatible_label_count": row["compatible_label_count"],
                "frobenius_usable_prime_count": row.get("frobenius_usable_prime_count"),
                "minimum_frobenius_primes_required": row.get("minimum_frobenius_primes_required"),
                "adaptive_evidence_status": row.get("adaptive_evidence_status"),
                "features": row["features"],
            }
            for row in selected
        ],
        "output_files": output_files,
    }


def report_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Packet Optimizer",
        "",
        "This report selects a diversified packet by plausible valuable-pair coverage. It does not verify exact labels and does not authorize live submission.",
        "",
        "## Summary",
        "",
        f"- Candidates considered: {summary['candidate_count']}",
        f"- Eligible for optimization: {summary['eligible_candidate_count']}",
        f"- Selected rows: {summary['selected_rows']}",
        f"- Possible uncovered pairs covered: {summary['selected_possible_uncovered_pair_count']}",
        f"- Possible low-team pairs covered: {summary['selected_possible_low_team_pair_count']}",
        f"- Crowded-only rejected: {summary['crowded_only_candidates_rejected']}",
        f"- Known submitted hashes rejected: {summary.get('known_submission_hash_candidates_rejected', 0)}",
        f"- Missing pair evidence: {summary['pair_evidence_missing_candidates']}",
        f"- Insufficient adaptive Frobenius evidence: {summary.get('insufficient_adaptive_frobenius_candidates', 0)}",
        f"- Best-case packet points: {summary['best_case_packet_points']}",
        f"- Expected points status: `{summary['expected_points_status']}`",
        f"- Expected points basis: {summary['expected_points_basis']}",
        f"- Live submission recommended now: `{summary['live_submission_recommended_now']}`",
        "",
        "## Selected Rows",
        "",
        "| rank | hash | marginal best case | row best case | expected status | uncovered pairs | low-team pairs | r | family | mode |",
        "| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in summary["selected_rows_summary"]:
        features = row["features"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["rank"]),
                    f"`{row['short_hash']}`",
                    str(row["marginal_best_case_points"]),
                    str(row["best_case_points"]),
                    f"`{row['expected_points_status']}`",
                    str(row.get("possible_uncovered_pair_count", len(row["possible_uncovered_pairs"]))),
                    str(row.get("possible_low_team_pair_count", len(row["possible_low_team_pairs"]))),
                    str(features.get("r")),
                    f"`{features.get('construction_family')}`",
                    f"`{features.get('perturbation_mode')}`",
                ]
            )
            + " |"
        )
    lines.extend(["", f"Reason: {summary['live_submission_reason']}", ""])
    return "\n".join(lines)


def strip_source(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"source_row", "exported_coefficients"}}


def write_outputs(output_dir: Path, *, selected: list[dict[str, Any]], rejected: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary_json": output_dir / SUMMARY_JSON,
        "report_md": output_dir / REPORT_MD,
        "selected_jsonl": output_dir / SELECTED_JSONL,
        "rejected_jsonl": output_dir / REJECTED_JSONL,
        "coefficients_txt": output_dir / COEFFICIENTS_TXT,
        "hashes_txt": output_dir / HASHES_TXT,
    }
    output_files = {name: str(path) for name, path in paths.items()}
    final_summary = {**summary, "output_files": output_files}
    paths["summary_json"].write_text(json.dumps(final_summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    paths["report_md"].write_text(report_markdown(final_summary), encoding="utf-8")
    write_jsonl(paths["selected_jsonl"], [strip_source(row) for row in selected])
    write_jsonl(paths["rejected_jsonl"], [strip_source(row) for row in rejected])
    with paths["coefficients_txt"].open("w", encoding="utf-8") as handle:
        for row in selected:
            coeffs = row.get("exported_coefficients")
            if coeffs:
                handle.write(format_polynomial_line(coeffs) + "\n")
    paths["hashes_txt"].write_text(
        "".join(f"{row.get('optimizer_rank', '-')}\t{row['short_hash']}\t{row.get('marginal_best_case_points', 0)}\n" for row in selected),
        encoding="utf-8",
    )
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--score_plan_json", type=Path, default=DEFAULT_SCORE_PLAN)
    parser.add_argument("--known_submission_rows_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--packet_limit", type=int, default=100)
    parser.add_argument("--allow_ineligible", action="store_true")
    parser.add_argument("--per_construction_family_cap", type=int, default=40)
    parser.add_argument("--per_template_family_cap", type=int, default=12)
    parser.add_argument("--per_perturbation_mode_cap", type=int, default=20)
    parser.add_argument("--per_basin_fingerprint_cap", type=int, default=3)
    parser.add_argument("--per_mod_signature_cap", type=int, default=4)
    parser.add_argument("--per_compatible_cluster_cap", type=int, default=8)
    parser.add_argument("--per_r_cap", type=int, default=40)
    parser.add_argument("--minimum_frobenius_primes", type=int, default=DEFAULT_MINIMUM_FROBENIUS_PRIMES)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows: list[dict[str, Any]] = []
    for path in args.candidate_jsonl:
        rows.extend(read_jsonl(path))
    score_plan = load_score_plan(args.score_plan_json)
    known_submission_hashes = load_known_submission_hashes(args.known_submission_rows_jsonl)
    candidates = [
        normalize_candidate(
            row,
            score_plan=score_plan,
            require_eligible=not args.allow_ineligible,
            known_submission_hashes=known_submission_hashes,
            minimum_frobenius_primes=int(args.minimum_frobenius_primes),
        )
        for row in rows
    ]
    caps = {
        "construction_family": int(args.per_construction_family_cap),
        "template_family_id": int(args.per_template_family_cap),
        "perturbation_mode": int(args.per_perturbation_mode_cap),
        "basin_fingerprint": int(args.per_basin_fingerprint_cap),
        "mod_p_pattern_signature": int(args.per_mod_signature_cap),
        "compatible_label_cluster": int(args.per_compatible_cluster_cap),
        "r": int(args.per_r_cap),
    }
    selected, rejected = greedy_select(candidates, packet_limit=int(args.packet_limit), caps=caps)
    placeholder_outputs = {
        "summary_json": str(args.output_dir / SUMMARY_JSON),
        "report_md": str(args.output_dir / REPORT_MD),
        "selected_jsonl": str(args.output_dir / SELECTED_JSONL),
        "rejected_jsonl": str(args.output_dir / REJECTED_JSONL),
        "coefficients_txt": str(args.output_dir / COEFFICIENTS_TXT),
        "hashes_txt": str(args.output_dir / HASHES_TXT),
    }
    summary = summarize(
        candidate_paths=list(args.candidate_jsonl),
        candidates=candidates,
        selected=selected,
        rejected=rejected,
        caps=caps,
        output_files=placeholder_outputs,
        minimum_frobenius_primes=int(args.minimum_frobenius_primes),
    )
    paths = write_outputs(args.output_dir, selected=selected, rejected=rejected, summary=summary)
    print(f"candidate_count\t{summary['candidate_count']}")
    print(f"eligible_candidate_count\t{summary['eligible_candidate_count']}")
    print(f"selected_rows\t{summary['selected_rows']}")
    print(f"possible_uncovered_pairs\t{summary['selected_possible_uncovered_pair_count']}")
    print(f"possible_low_team_pairs\t{summary['selected_possible_low_team_pair_count']}")
    print(f"best_case_packet_points\t{summary['best_case_packet_points']}")
    print(f"expected_points_status\t{summary['expected_points_status']}")
    print(f"live_submission_recommended_now\t{summary['live_submission_recommended_now']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
