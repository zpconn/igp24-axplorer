#!/usr/bin/env python3
"""Score IGP24 candidate queues against known SAIR label basins.

This helper is a steering layer, not a verifier. It joins local candidate
metadata with accepted-feedback basin fingerprints and live SAIR label progress
so a small packet can be reviewed for novelty before any live submission.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_r16_diversity_probe import coefficient_line  # noqa: E402
from scripts.igp24_sair_progress_targets import (  # noqa: E402
    coverage_by_r,
    fetch_progress_snapshot,
    load_progress_snapshot,
)
from scripts.igp24_sair_sync import (  # noqa: E402
    load_sync_progress_snapshot,
    load_sync_status,
    load_sync_submission_rows,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.verifiers.sair_api import format_polynomial_line  # noqa: E402


DEFAULT_LABEL_BASIN_SUMMARY = REPO_ROOT / "data/igp24/axg19_sparse_escape_20260709/label_basin_analysis/label_basin_summary.json"
DEFAULT_LABEL_BASIN_OBSERVATIONS = REPO_ROOT / "data/igp24/axg19_sparse_escape_20260709/label_basin_analysis/label_basin_observations.jsonl"
DEFAULT_ACCEPTED_FEEDBACK_JSONS = [
    REPO_ROOT / "data/igp24/alt_composition_8x3_sair_probe_20260707/alt_composition_8x3_sair_accepted_feedback_20260707.json",
    REPO_ROOT / "data/igp24/anti_basin_steering_20260707/anti_basin_sair_accepted_feedback_20260707.json",
    REPO_ROOT / "data/igp24/anti_basin_4x6_steering_20260707/anti_basin_4x6_sair_accepted_feedback_20260707.json",
    REPO_ROOT / "data/igp24/r20_linear_real_sair_accepted_feedback_20260707.json",
    REPO_ROOT / "data/igp24/r24_tower_odd_escape_sair_accepted_feedback_20260707.json",
    REPO_ROOT / "data/igp24/r8_quartic_lift_perturbed_sair_accepted_feedback_20260707.json",
    REPO_ROOT
    / "data/igp24/r8_score_followup_20260708/anti_collapse_gate/r8_score_followup_sair_accepted_feedback_20260708.json",
    REPO_ROOT
    / "data/igp24/r24_r16_high_real_refinement_20260708/r16_gate/r16_high_real_refinement_sair_accepted_feedback_20260709.json",
    REPO_ROOT
    / "data/igp24/r24_deterministic_high_real_expansion_20260709/submission/r24_deterministic_sair_accepted_feedback_20260709.json",
    REPO_ROOT
    / "data/igp24/axg16_conditioned_20260709/proposal_loop/axg16_anti_collapse_multir_gate_20260709/axg16_sair_accepted_feedback_20260709.json",
    REPO_ROOT
    / "data/igp24/axg17_score_aware_20260709/proposal_loop/axg17_score_aware_gate_20260709/axg17_sair_accepted_feedback_20260709.json",
    REPO_ROOT
    / "data/igp24/axg18_escape_20260709/proposal_loop/axg18_high_real_escape_combined_gate_20260709/axg18_sair_accepted_feedback_20260709.json",
]
DEFAULT_AVOID_LABELS = {"24T24932", "24T25000", "24T24979", "24T24970", "24T24651", "24T23883"}
DEFAULT_TARGET_RS = [24, 20, 16, 12, 8]
HIGH_VALUE_R_WEIGHTS = {24: 40.0, 16: 32.0, 20: 30.0, 12: 24.0, 8: 22.0}
R8_QUARTIC_IN_X6_COLLAPSE_FAMILIES = {
    "r8_quartic_lift_perturbed",
    "r8_quartic_lift_score_followup",
}
FATAL_RISK_REASON_PREFIXES = (
    "real_root_count_not_target",
    "missing_local_irreducible_squarefree",
    "support_gcd_not_one",
    "even_support",
    "accepted_hash_duplicate",
    "known_repeated_pair_collision",
    "outer_constant_shift",
    "construction_family_known_high_label_collapse",
    "r8_quartic_in_x6_known_label_collapse",
    "template_family_known_high_label_collapse",
    "basin_fingerprint_known_high_label_collapse",
    "model_template_family_known_high_label_collapse",
    "model_basin_fingerprint_known_high_label_collapse",
    "model_mixed_high_real_24T25000_collapse_pattern",
    "model_fixed_sparse_high_real_24T25000_collapse_pattern",
    "exact_crowded_basin_fingerprint",
)


def is_fatal_risk_reason(reason: str) -> bool:
    return reason.startswith(FATAL_RISK_REASON_PREFIXES)
CONSTRUCTION_FAMILY_HARD_STOP_COLLAPSES = {
    "odd_perturbed_r24_6x4_tower_escape",
    "positive_quadratic_product_plus_low_odd_perturbation",
    "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation",
}
AXG16_MODEL_MIXED_24T25000_COLLAPSE_RS = {12, 20, 24}
AXG16_MODEL_MIXED_24T25000_COLLAPSE_MODES = {
    "dense_mixed_support_gcd1",
    "medium_mixed_support_gcd1",
}
AXG18_MODEL_FIXED_SPARSE_24T25000_COLLAPSE_RS = {16, 20, 24}
AXG18_MODEL_FIXED_SPARSE_24T25000_COLLAPSE_MODES = {
    "dense_mixed_support_gcd1",
    "medium_mixed_support_gcd1",
}

PROGRESS_CACHE_JSON = "anti_basin_live_progress_cache.json"
SCORES_JSONL = "anti_basin_candidate_scores.jsonl"
SELECTED_JSONL = "anti_basin_selected_queue.jsonl"
COEFFICIENTS_TXT = "anti_basin_candidate_coefficients.txt"
HASHES_TXT = "anti_basin_candidate_hashes.txt"
SUMMARY_JSON = "anti_basin_planner_summary.json"
REPORT_MD = "anti_basin_planner_report.md"


def parse_csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {raw.strip() for raw in str(value).split(",") if raw.strip()}


def parse_target_rs(value: str | None) -> list[int]:
    if not value:
        return list(DEFAULT_TARGET_RS)
    rows = [int(raw.strip()) for raw in str(value).split(",") if raw.strip()]
    return rows or list(DEFAULT_TARGET_RS)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_accepted_feedback_observations(paths: Iterable[Path]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("accepted_rows") or []:
            if isinstance(row, dict):
                observations.append(row)
    return observations


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def mod_pattern_signature(row: dict[str, Any] | None) -> str | None:
    patterns = (row or {}).get("mod_p_factorization_degree_patterns")
    if not isinstance(patterns, list) or not patterns:
        return None
    parts: list[str] = []
    for pattern in patterns:
        if not isinstance(pattern, dict):
            continue
        degrees = "-".join(str(int(value)) for value in pattern.get("degrees") or [])
        if degrees:
            parts.append(f"p{pattern.get('prime')}:{degrees}")
    return ";".join(sorted(parts)) or None


def support_summary(coefficients: Iterable[int] | None) -> dict[str, Any]:
    if not coefficients:
        return {"support_gcd": None, "even_support": None, "odd_support_exponents": []}
    coeffs = [int(value) for value in coefficients]
    support = [index for index, value in enumerate(coeffs) if value != 0]
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, exponent)
    return {
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
        "odd_support_exponents": [exponent for exponent in support if exponent % 2 == 1],
    }


def family_key(metadata: dict[str, Any], row: dict[str, Any]) -> str:
    for key in (
        "family_key",
        "template_family_id",
        "basin_fingerprint",
        "alt_composition_family_key",
        "r24_tower_family_key",
        "r24_tower_odd_escape_family_key",
        "r12_tower_family_key",
        "r24_high_real_family_key",
        "r20_high_real_family_key",
        "r20_linear_family_key",
        "r16_diversity_family_key",
        "r12_structured_family_key",
        "r8_quartic_lift_family_key",
    ):
        if metadata.get(key):
            return str(metadata[key])
    return str(row.get("source_family_key") or row.get("template_family_id") or row.get("basin_fingerprint") or "")


def candidate_features(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("generation_metadata") if isinstance(row.get("generation_metadata"), dict) else {}
    exported = row.get("exported_coefficients")
    support = support_summary(exported if isinstance(exported, list) else None)
    support_gcd = (
        metadata.get("support_gcd")
        or row.get("support_gcd")
        or
        metadata.get("alt_support_gcd")
        or metadata.get("r24_tower_odd_escape_support_gcd")
        or metadata.get("r20_linear_support_gcd")
        or (1 if metadata.get("r16_diversity_divisor2_off_block_terms") else None)
        or metadata.get("r8_quartic_lift_support_gcd")
        or support.get("support_gcd")
    )
    even_support = metadata.get("even_support_like")
    if even_support is None:
        even_support = row.get("even_support_like")
    if even_support is None:
        even_support = metadata.get("alt_even_support")
    if even_support is None:
        even_support = metadata.get("r24_tower_odd_escape_even_support_after_perturbation")
    if even_support is None:
        even_support = metadata.get("r20_linear_even_support")
    if even_support is None and metadata.get("r16_diversity_divisor2_off_block_terms"):
        even_support = False
    if even_support is None:
        even_support = metadata.get("r8_quartic_lift_even_support")
    if even_support is None:
        even_support = support.get("even_support")
    perturbations = (
        metadata.get("alt_outer_perturbations")
        or metadata.get("r24_tower_odd_escape_odd_perturbations")
        or metadata.get("r20_linear_coefficient_perturbations")
        or metadata.get("r16_diversity_odd_perturbations")
        or metadata.get("r16_diversity_y_perturbations")
        or metadata.get("r16_diversity_off_block_perturbation_exponents")
        or metadata.get("r8_quartic_lift_perturbation_exponents")
        or metadata.get("r24_high_real_odd_perturbations")
        or metadata.get("r24_high_real_odd_support_after_perturbation")
        or metadata.get("odd_support_exponents")
        or []
    )
    mode = str(
        metadata.get("perturbation_mode")
        or row.get("perturbation_mode")
        or metadata.get("alt_perturbation_mode")
        or metadata.get("r8_quartic_lift_perturbation_mode")
        or metadata.get("r24_high_real_perturbation_mode")
        or metadata.get("r24_high_real_mode")
        or metadata.get("r24_tower_mode")
        or metadata.get("r24_tower_odd_escape_mode")
        or metadata.get("r20_linear_mode")
        or metadata.get("r16_diversity_mode")
        or row.get("source_mode")
        or ""
    )
    pattern = str(
        metadata.get("decomposition_degree_pattern")
        or metadata.get("decomposition_pattern")
        or row.get("decomposition_pattern")
        or metadata.get("support_pattern")
        or row.get("support_pattern")
        or (
            f"near_composed_quadratic_product_d{metadata.get('r24_high_real_exact_composed_seed_divisor')}"
            if metadata.get("r24_high_real_exact_composed_seed_divisor")
            else ""
        )
        or ("quartic_in_x6" if metadata.get("source_family") in R8_QUARTIC_IN_X6_COLLAPSE_FAMILIES else "")
    )
    construction = str(
        metadata.get("construction_family")
        or metadata.get("source_family")
        or row.get("construction_family")
        or metadata.get("generation_strategy")
        or metadata.get("resolved_generation_strategy")
        or metadata.get("strategy")
        or ""
    )
    high_real_mode = metadata.get("r24_high_real_perturbation_mode") or metadata.get("r24_high_real_mode")
    template_family_id = str(
        metadata.get("template_family_id")
        or row.get("template_family_id")
        or (f"r24_high_real:{high_real_mode}" if high_real_mode else "")
        or (f"{construction}:{pattern}:{mode}" if construction and (pattern or mode) else "")
    )
    inferred_family_key = family_key(metadata, row)
    basin_fingerprint = str(
        metadata.get("basin_fingerprint")
        or row.get("basin_fingerprint")
        or metadata.get("r24_high_real_family_key")
        or metadata.get("r24_tower_odd_escape_family_key")
        or metadata.get("r20_linear_family_key")
        or metadata.get("r16_diversity_family_key")
        or metadata.get("alt_composition_family_key")
        or inferred_family_key
        or ""
    )
    coefficient_hash = str(metadata.get("coefficient_hash") or row.get("coefficient_hash") or "")
    decoded_hash = str(metadata.get("decoded_hash") or row.get("decoded_hash") or "")
    source_seed_hash = str(metadata.get("source_seed_hash") or row.get("source_seed_hash") or "")
    label = str(row.get("label") or row.get("verified_group_label") or "")
    r_for_pair = row.get("real_root_count", row.get("r"))
    pair_key = str(row.get("pair_key") or row.get("verified_pair_key") or "")
    if not pair_key and label and r_for_pair is not None:
        try:
            pair_key = f"{label}|r={int(r_for_pair)}"
        except (TypeError, ValueError):
            pair_key = ""
    return {
        "canonical_hash": str(row.get("canonical_hash") or ""),
        "short_hash": str(row.get("canonical_hash") or "")[:12],
        "label": label,
        "pair_key": pair_key,
        "r": int(row.get("real_root_count") or row.get("r") or -1),
        "coefficient_height": int(row.get("coefficient_height") or metadata.get("alt_coefficient_height") or 0),
        "construction_family": construction,
        "decomposition_pattern": pattern,
        "perturbation_mode": mode,
        "perturbation_terms": len(perturbations) if isinstance(perturbations, list) else 0,
        "family_key": inferred_family_key,
        "template_family_id": template_family_id,
        "basin_fingerprint": basin_fingerprint,
        "coefficient_hash": coefficient_hash,
        "decoded_hash": decoded_hash,
        "source_seed_hash": source_seed_hash,
        "support_gcd": int(support_gcd) if support_gcd is not None else None,
        "even_support": bool(even_support) if even_support is not None else None,
        "odd_support_exponents": (
            metadata.get("alt_odd_support_exponents")
            or metadata.get("r24_tower_odd_escape_odd_support_exponents")
            or metadata.get("r20_linear_odd_support_exponents")
            or metadata.get("r16_diversity_off_block_perturbation_exponents")
            or metadata.get("odd_support_exponents")
            or metadata.get("r24_high_real_odd_support_after_perturbation")
            or support.get("odd_support_exponents")
            or []
        ),
        "mod_p_pattern_signature": mod_pattern_signature(row),
        "irreducible": bool(row.get("irreducible")),
        "squarefree": bool(row.get("squarefree")),
        "exported_coefficients": exported if isinstance(exported, list) else None,
    }


def is_axg16_model_mixed_24t25000_collapse_pattern(features: dict[str, Any]) -> bool:
    """Detect the proven AXG-1.6 model-export pattern that collapsed to 24T25000.

    Generic loose basin matches stay advisory elsewhere. This helper only flags
    high-real model samples with the same dense/medium mixed support family that
    the AXG-1.6 SAIR feedback showed repeatedly landing in 24T25000.
    """
    if features.get("construction_family") != "model_sample_export":
        return False
    try:
        r_value = int(features.get("r"))
    except (TypeError, ValueError):
        return False
    if r_value not in AXG16_MODEL_MIXED_24T25000_COLLAPSE_RS:
        return False
    mode = str(features.get("perturbation_mode") or features.get("decomposition_pattern") or "")
    template = str(features.get("template_family_id") or "")
    if mode not in AXG16_MODEL_MIXED_24T25000_COLLAPSE_MODES:
        return False
    return template.startswith(f"model:mixed:r{r_value}:")


def is_axg18_model_fixed_sparse_24t25000_collapse_pattern(features: dict[str, Any]) -> bool:
    """Detect the AXG-1.8 fixed-sparse high-real pattern that collapsed to 24T25000."""
    if features.get("construction_family") != "model_sample_export":
        return False
    try:
        r_value = int(features.get("r"))
    except (TypeError, ValueError):
        return False
    if r_value not in AXG18_MODEL_FIXED_SPARSE_24T25000_COLLAPSE_RS:
        return False
    mode = str(features.get("perturbation_mode") or features.get("decomposition_pattern") or "")
    template = str(features.get("template_family_id") or "")
    if mode not in AXG18_MODEL_FIXED_SPARSE_24T25000_COLLAPSE_MODES:
        return False
    return template.startswith(f"model:fixed_sparse_template:r{r_value}:")


def sample_export_source(row: dict[str, Any] | None) -> str:
    """Return the sampler source in a form shared by proposal summaries."""
    if not isinstance(row, dict):
        return "unknown"
    source = row.get("sample_export_source")
    if source:
        return str(source)
    source = row.get("source_strategy")
    if source:
        return str(source)
    source_sample_export = row.get("source_sample_export")
    if isinstance(source_sample_export, dict):
        source = source_sample_export.get("sample_export_source")
        if source:
            return str(source)
    generation_metadata = row.get("generation_metadata")
    if isinstance(generation_metadata, dict):
        source = (
            generation_metadata.get("sample_export_source")
            or generation_metadata.get("source")
            or generation_metadata.get("strategy")
            or generation_metadata.get("construction_family")
        )
        if source:
            return str(source)
    return "unknown"


def scored_sample_export_source(row: dict[str, Any]) -> str:
    candidate = row.get("candidate")
    return sample_export_source(candidate if isinstance(candidate, dict) else row)


def is_model_generated_source(source: str) -> bool:
    return (
        source == "model_generate"
        or "model_generate" in source
        or "model_sample" in source
        or "lane_generate" in source
    )


def candidate_pair_key(row: dict[str, Any]) -> str | None:
    features = row.get("features") if isinstance(row.get("features"), dict) else {}
    candidate = row.get("candidate") if isinstance(row.get("candidate"), dict) else {}
    pair = (
        row.get("pair_key")
        or features.get("pair_key")
        or candidate.get("pair_key")
        or candidate.get("verified_pair_key")
    )
    if pair:
        return str(pair)
    label = (
        row.get("label")
        or features.get("label")
        or candidate.get("label")
        or candidate.get("verified_group_label")
    )
    r_value = row.get("r", features.get("r", candidate.get("r", candidate.get("real_root_count"))))
    if not label or r_value is None:
        return None
    try:
        return f"{label}|r={int(r_value)}"
    except (TypeError, ValueError):
        return None


def candidate_r_values(rows: list[dict[str, Any]]) -> set[int]:
    values: set[int] = set()
    for row in rows:
        features = row.get("features") if isinstance(row.get("features"), dict) else {}
        candidate = row.get("candidate") if isinstance(row.get("candidate"), dict) else {}
        r_value = row.get("r", features.get("r", candidate.get("r", candidate.get("real_root_count"))))
        try:
            parsed = int(r_value)
        except (TypeError, ValueError):
            continue
        if parsed >= 0:
            values.add(parsed)
    return values


def pending_submission_pair_counts(rows: Iterable[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        status_class = str(row.get("status_class") or "")
        scoring_status = str(row.get("scoring_status") or row.get("scoringStatus") or "")
        if status_class != "pending" and scoring_status != "pending" and not row.get("queued"):
            continue
        pair = row.get("pair_key")
        if not pair and row.get("label") and row.get("r") is not None:
            try:
                pair = f"{row['label']}|r={int(row['r'])}"
            except (TypeError, ValueError):
                pair = None
        if pair:
            counts[str(pair)] += 1
    return counts


def sync_full_submission_state_complete(sync_status: dict[str, Any] | None) -> bool:
    if sync_status is None:
        return True
    if "full_submission_state_complete" in sync_status:
        return bool(sync_status.get("full_submission_state_complete"))
    if "submission_state_complete" in sync_status:
        return bool(sync_status.get("submission_state_complete"))
    return not bool(sync_status.get("partial_sync"))


def build_sync_submission_gate(
    selected: list[dict[str, Any]],
    *,
    sync_status: dict[str, Any] | None = None,
    sync_submission_rows: list[dict[str, Any]] | None = None,
    pending_collision_labels: set[str] | None = None,
) -> dict[str, Any]:
    sync_rows = sync_submission_rows or []
    selected_pairs = sorted({pair for row in selected if (pair := candidate_pair_key(row))})
    selected_rs = sorted(candidate_r_values(selected))
    pending_counts = pending_submission_pair_counts(sync_rows)
    exact_pending = {pair: int(pending_counts[pair]) for pair in selected_pairs if pending_counts.get(pair)}
    labels = set(pending_collision_labels or set())
    pending_high_label_basin: dict[str, int] = {}
    for pair, count in pending_counts.items():
        label, _, r_text = pair.partition("|r=")
        try:
            r_value = int(r_text)
        except ValueError:
            continue
        if label in labels and r_value in selected_rs:
            pending_high_label_basin[pair] = int(count)

    hold_reasons: list[str] = []
    full_state = sync_full_submission_state_complete(sync_status)
    if sync_status is not None and not full_state:
        submission_index_known = sync_status.get("submission_index_complete")
        if submission_index_known is None and sync_rows:
            submission_index_known = True
        if submission_index_known:
            hold_reasons.append("locally_ready_but_blocked_by_incomplete_sair_state")
        else:
            hold_reasons.append("locally_ready_but_blocked_by_missing_sair_submission_index")
    if exact_pending:
        pending_text = ",".join(f"{pair}={count}" for pair, count in sorted(exact_pending.items()))
        hold_reasons.append(f"locally_ready_but_pending_collision_risk:{pending_text}")
    if pending_high_label_basin:
        pending_text = ",".join(f"{pair}={count}" for pair, count in sorted(pending_high_label_basin.items()))
        hold_reasons.append(f"safe_to_review_only_after_pending_rows_resolve:{pending_text}")

    return {
        "full_submission_state_complete": bool(full_state),
        "partial_sync": bool((sync_status or {}).get("partial_sync")) if sync_status is not None else False,
        "submission_detail_complete": (sync_status or {}).get("submission_detail_complete"),
        "download_complete": (sync_status or {}).get("download_complete"),
        "degraded_mode_summary": (sync_status or {}).get("degraded_mode_summary"),
        "selected_pair_keys": selected_pairs,
        "selected_r_values": selected_rs,
        "pending_pair_counts": dict(sorted(pending_counts.items())),
        "selected_exact_pair_pending_collisions": exact_pending,
        "pending_high_label_basin_collisions": dict(sorted(pending_high_label_basin.items())),
        "hold_reasons": hold_reasons,
    }


def observation_features(row: dict[str, Any]) -> dict[str, Any]:
    construction = str(row.get("construction_family") or "")
    pattern = str(row.get("decomposition_pattern") or "")
    mode = str(row.get("perturbation_mode") or "")
    family = str(row.get("family_key") or "")
    return {
        "label": str(row.get("label") or ""),
        "pair_key": str(row.get("pair_key") or ""),
        "r": int(row.get("r") or -1),
        "construction_family": construction,
        "decomposition_pattern": pattern,
        "perturbation_mode": mode,
        "support_gcd": int(row["support_gcd"]) if row.get("support_gcd") is not None else None,
        "even_support": row.get("even_support"),
        "family_key": family,
        "template_family_id": str(row.get("template_family_id") or (f"{construction}:{pattern}:{mode}" if construction and (pattern or mode) else "")),
        "basin_fingerprint": str(row.get("basin_fingerprint") or family),
        "mod_p_pattern_signature": row.get("mod_p_pattern_signature"),
        "canonical_hash": str(row.get("canonical_hash") or ""),
    }


def load_progress(*, fetch_live: bool, progress_snapshot_json: Path | None) -> dict[str, Any]:
    if fetch_live:
        return fetch_progress_snapshot(limit=5000)
    if progress_snapshot_json:
        return load_progress_snapshot(progress_snapshot_json)
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "query": {"source": "not_loaded"},
        "page_count": 0,
        "label_count": 0,
        "pages": [],
        "labels": [],
    }


def normalize_progress_cache(
    snapshot: dict[str, Any],
    *,
    target_rs: list[int],
    max_pair_progress: int = 5000,
) -> dict[str, Any]:
    labels = list(snapshot.get("labels") or [])
    by_r = coverage_by_r(labels) if labels else []
    label_progress: dict[str, Any] = {}
    pair_rows: list[tuple[str, dict[str, Any]]] = []
    target_r_set = set(int(value) for value in target_rs)
    for row in labels:
        if not isinstance(row, dict) or not row.get("label"):
            continue
        label = str(row["label"])
        remaining = [int(value) for value in row.get("remainingSignatures") or []]
        discovered = [int(value) for value in row.get("discoveredSignatures") or []]
        allowed = [int(value) for value in row.get("allowedR") or []]
        label_progress[label] = {
            "t": int(row.get("t") or label.removeprefix("24T")),
            "team_count": int(row.get("teamCount") or 0),
            "allowed_r": allowed,
            "discovered_r": discovered,
            "remaining_r": remaining,
            "fully_covered": bool(row) and not remaining,
            "minimum_disc_abs": row.get("minimumDiscAbs"),
        }
        signatures = {int(sig.get("r")): sig for sig in row.get("signatures") or [] if sig.get("r") is not None}
        for r_value in allowed:
            if target_r_set and r_value not in target_r_set:
                continue
            signature = signatures.get(r_value) or {}
            pair_rows.append(
                (
                    f"{label}|r={r_value}",
                    {
                        "label": label,
                        "r": r_value,
                        "discovered": r_value in discovered,
                        "remaining": r_value in remaining,
                        "label_team_count": int(row.get("teamCount") or 0),
                        "signature_team_count": int(signature.get("teamCount") or 0),
                        "label_remaining_signature_count": len(remaining),
                        "minimum_disc_abs": signature.get("minimumDiscAbs") or row.get("minimumDiscAbs"),
                    },
                )
            )
    pair_rows.sort(
        key=lambda item: (
            not bool(item[1]["remaining"]),
            int(item[1]["signature_team_count"]),
            int(item[1]["label_team_count"]),
            -int(item[1]["label_remaining_signature_count"]),
            item[0],
        )
    )
    pair_progress = {
        key: value
        for key, value in pair_rows[: int(max_pair_progress)]
    }
    pair_progress_overflow_count = max(0, len(pair_rows) - len(pair_progress))
    return {
        "record_type": "igp24_anti_basin_live_progress_cache",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot": {
            "record_type": snapshot.get("record_type"),
            "created_at": snapshot.get("created_at"),
            "query": snapshot.get("query"),
            "page_count": snapshot.get("page_count"),
            "label_count": snapshot.get("label_count"),
            "first_generated_at": (snapshot.get("pages") or [{}])[0].get("generatedAt"),
            "last_generated_at": (snapshot.get("pages") or [{}])[-1].get("generatedAt"),
            "published": ((snapshot.get("pages") or [{}])[0].get("meta") or {}).get("published"),
        },
        "target_rs": target_rs,
        "coverage_by_r": by_r,
        "label_progress": label_progress,
        "pair_progress": pair_progress,
        "pair_progress_limit": int(max_pair_progress),
        "pair_progress_total_target_r_pairs": len(pair_rows),
        "pair_progress_overflow_count": pair_progress_overflow_count,
    }


def build_basin_profile(
    observations: list[dict[str, Any]],
    label_summary: dict[str, Any],
    *,
    avoid_labels: set[str],
    crowded_team_threshold: int,
) -> dict[str, Any]:
    crowded_labels = set(avoid_labels)
    for label, row in label_summary.items():
        progress = row.get("global_progress") or {}
        if progress.get("fully_covered") or int(progress.get("team_count") or 0) >= crowded_team_threshold:
            crowded_labels.add(str(label))

    crowded_observations = [observation_features(row) for row in observations if str(row.get("label")) in crowded_labels]
    exact_fingerprints = Counter()
    loose_fingerprints = Counter()
    mod_signatures = Counter()
    mode_by_family_pattern = Counter()
    collapsed_construction_r_labels: dict[tuple[str, int], set[str]] = defaultdict(set)
    collapsed_family_pattern_labels: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    collapsed_pair_counts: Counter[str] = Counter()
    collapsed_template_r_labels: dict[tuple[str, int], set[str]] = defaultdict(set)
    collapsed_basin_r_labels: dict[tuple[str, int], set[str]] = defaultdict(set)
    collapsed_model_template_r_labels: dict[tuple[str, int], set[str]] = defaultdict(set)
    collapsed_model_basin_r_labels: dict[tuple[str, int], set[str]] = defaultdict(set)
    accepted_hashes = set()
    for row in crowded_observations:
        exact_key = (
            row["construction_family"],
            row["decomposition_pattern"],
            row["perturbation_mode"],
            row["support_gcd"],
            row["mod_p_pattern_signature"],
        )
        loose_key = (
            row["construction_family"],
            row["decomposition_pattern"],
            row["perturbation_mode"],
            row["support_gcd"],
        )
        exact_fingerprints[exact_key] += 1
        loose_fingerprints[loose_key] += 1
        if row.get("mod_p_pattern_signature"):
            mod_signatures[str(row["mod_p_pattern_signature"])] += 1
        mode_by_family_pattern[(row["construction_family"], row["decomposition_pattern"], row["perturbation_mode"])] += 1
        if row.get("construction_family"):
            collapsed_construction_r_labels[(row["construction_family"], row["r"])].add(row["label"])
        collapsed_family_pattern_labels[(row["construction_family"], row["decomposition_pattern"], row["r"])].add(row["label"])
        if row.get("pair_key"):
            collapsed_pair_counts[str(row["pair_key"])] += 1
        if row.get("template_family_id"):
            collapsed_template_r_labels[(str(row["template_family_id"]), row["r"])].add(row["label"])
        if row.get("basin_fingerprint"):
            collapsed_basin_r_labels[(str(row["basin_fingerprint"]), row["r"])].add(row["label"])
        if row["construction_family"] == "model_sample_export":
            if row.get("template_family_id"):
                collapsed_model_template_r_labels[(str(row["template_family_id"]), row["r"])].add(row["label"])
            if row.get("basin_fingerprint"):
                collapsed_model_basin_r_labels[(str(row["basin_fingerprint"]), row["r"])].add(row["label"])
        if row.get("canonical_hash"):
            accepted_hashes.add(str(row["canonical_hash"]))

    return {
        "avoid_labels": sorted(avoid_labels),
        "crowded_labels": sorted(crowded_labels),
        "crowded_observation_count": len(crowded_observations),
        "exact_fingerprints": exact_fingerprints,
        "loose_fingerprints": loose_fingerprints,
        "mod_signatures": mod_signatures,
        "mode_by_family_pattern": mode_by_family_pattern,
        "collapsed_construction_r_labels": {
            key: sorted(labels) for key, labels in collapsed_construction_r_labels.items()
        },
        "collapsed_family_pattern_labels": {
            key: sorted(labels) for key, labels in collapsed_family_pattern_labels.items()
        },
        "collapsed_pair_counts": collapsed_pair_counts,
        "collapsed_template_r_labels": {
            key: sorted(labels) for key, labels in collapsed_template_r_labels.items()
        },
        "collapsed_basin_r_labels": {
            key: sorted(labels) for key, labels in collapsed_basin_r_labels.items()
        },
        "collapsed_model_template_r_labels": {
            key: sorted(labels) for key, labels in collapsed_model_template_r_labels.items()
        },
        "collapsed_model_basin_r_labels": {
            key: sorted(labels) for key, labels in collapsed_model_basin_r_labels.items()
        },
        "accepted_hashes": accepted_hashes,
    }


def r_opportunity(r_value: int, progress_cache: dict[str, Any]) -> dict[str, Any]:
    by_r = {int(row["r"]): row for row in progress_cache.get("coverage_by_r") or []}
    row = by_r.get(r_value) or {}
    remaining = int(row.get("remaining") or 0)
    allowed = int(row.get("allowed") or 0)
    remaining_pct = float(row.get("remaining_pct") or 0.0)
    return {
        "remaining": remaining,
        "allowed": allowed,
        "remaining_pct": remaining_pct,
        "score": HIGH_VALUE_R_WEIGHTS.get(r_value, 0.0) + min(60.0, remaining / 200.0) + remaining_pct / 2.0,
    }


def score_candidate_row(
    row: dict[str, Any],
    *,
    target_rs: set[int],
    progress_cache: dict[str, Any],
    basin_profile: dict[str, Any],
) -> dict[str, Any]:
    features = candidate_features(row)
    explanation: list[str] = []
    risk_reasons: list[str] = []
    score = 0.0
    r_value = int(features["r"])

    opportunity = r_opportunity(r_value, progress_cache)
    score += float(opportunity["score"])
    explanation.append(f"r{r_value}_opportunity={opportunity['score']:.2f}")

    if r_value not in target_rs:
        risk_reasons.append("real_root_count_not_target")
        score -= 200.0
    if not features.get("irreducible") or not features.get("squarefree"):
        risk_reasons.append("missing_local_irreducible_squarefree")
        score -= 120.0
    if features.get("support_gcd") != 1:
        risk_reasons.append("support_gcd_not_one")
        score -= 120.0
    if features.get("even_support") is True:
        risk_reasons.append("even_support_g_x_squared_like")
        score -= 120.0
    if features.get("canonical_hash") in basin_profile["accepted_hashes"]:
        risk_reasons.append("accepted_hash_duplicate")
        score -= 200.0

    if features.get("perturbation_mode") == "outer_constant_shift":
        score -= 90.0
        risk_reasons.append("outer_constant_shift_after_24T24932_collapse")
    else:
        score += 35.0
        explanation.append("nonconstant_outer_perturbation_bonus=35")

    exact_key = (
        features["construction_family"],
        features["decomposition_pattern"],
        features["perturbation_mode"],
        features["support_gcd"],
        features["mod_p_pattern_signature"],
    )
    loose_key = (
        features["construction_family"],
        features["decomposition_pattern"],
        features["perturbation_mode"],
        features["support_gcd"],
    )
    mode_key = (features["construction_family"], features["decomposition_pattern"], features["perturbation_mode"])

    exact_hits = int(basin_profile["exact_fingerprints"].get(exact_key, 0))
    loose_hits = int(basin_profile["loose_fingerprints"].get(loose_key, 0))
    mode_hits = int(basin_profile["mode_by_family_pattern"].get(mode_key, 0))
    construction_key = (features["construction_family"], r_value)
    construction_labels = basin_profile.get("collapsed_construction_r_labels", {}).get(construction_key, [])
    family_pattern_key = (features["construction_family"], features["decomposition_pattern"], r_value)
    collapsed_labels = basin_profile.get("collapsed_family_pattern_labels", {}).get(family_pattern_key, [])
    if features.get("pair_key") and basin_profile.get("collapsed_pair_counts", {}).get(features["pair_key"]):
        hits = basin_profile["collapsed_pair_counts"][features["pair_key"]]
        risk_reasons.append(f"known_repeated_pair_collision:{features['pair_key']}={hits}")
        score -= 180.0
    if construction_labels and features["construction_family"] in CONSTRUCTION_FAMILY_HARD_STOP_COLLAPSES:
        labels = ",".join(str(label) for label in construction_labels)
        risk_reasons.append(f"construction_family_known_high_label_collapse={labels}")
        score -= 150.0
    if (
        features["construction_family"] in R8_QUARTIC_IN_X6_COLLAPSE_FAMILIES
        and features["decomposition_pattern"] == "quartic_in_x6"
        and r_value == 8
        and collapsed_labels
    ):
        labels = ",".join(str(label) for label in collapsed_labels)
        risk_reasons.append(f"r8_quartic_in_x6_known_label_collapse={labels}")
        score -= 140.0
    template_key = (features.get("template_family_id") or "", r_value)
    template_labels = basin_profile.get("collapsed_template_r_labels", {}).get(template_key, [])
    if template_labels:
        labels = ",".join(str(label) for label in template_labels)
        risk_reasons.append(f"template_family_known_high_label_collapse={labels}")
        score -= 120.0
    basin_key = (features.get("basin_fingerprint") or "", r_value)
    basin_labels = basin_profile.get("collapsed_basin_r_labels", {}).get(basin_key, [])
    if basin_labels:
        labels = ",".join(str(label) for label in basin_labels)
        risk_reasons.append(f"basin_fingerprint_known_high_label_collapse={labels}")
        score -= 140.0
    if features["construction_family"] == "model_sample_export":
        if is_axg16_model_mixed_24t25000_collapse_pattern(features):
            risk_reasons.append(
                f"model_mixed_high_real_24T25000_collapse_pattern:r{r_value}:{features.get('perturbation_mode')}"
            )
            score -= 220.0
        if is_axg18_model_fixed_sparse_24t25000_collapse_pattern(features):
            risk_reasons.append(
                f"model_fixed_sparse_high_real_24T25000_collapse_pattern:r{r_value}:{features.get('perturbation_mode')}"
            )
            score -= 220.0
        template_labels = basin_profile.get("collapsed_model_template_r_labels", {}).get(template_key, [])
        if template_labels:
            labels = ",".join(str(label) for label in template_labels)
            risk_reasons.append(f"model_template_family_known_high_label_collapse={labels}")
            score -= 160.0
        basin_labels = basin_profile.get("collapsed_model_basin_r_labels", {}).get(basin_key, [])
        if basin_labels:
            labels = ",".join(str(label) for label in basin_labels)
            risk_reasons.append(f"model_basin_fingerprint_known_high_label_collapse={labels}")
            score -= 180.0
    if exact_hits:
        risk_reasons.append(f"exact_crowded_basin_fingerprint_hits={exact_hits}")
        score -= 85.0
    elif loose_hits:
        risk_reasons.append(f"loose_crowded_basin_fingerprint_hits={loose_hits}")
        score -= 35.0
    else:
        score += 25.0
        explanation.append("no_crowded_feature_fingerprint_bonus=25")

    mod_sig = features.get("mod_p_pattern_signature")
    if mod_sig and basin_profile["mod_signatures"].get(mod_sig):
        risk_reasons.append(f"crowded_mod_p_signature_hits={basin_profile['mod_signatures'][mod_sig]}")
        score -= 25.0
    elif mod_sig:
        score += 15.0
        explanation.append("novel_mod_p_signature_bonus=15")

    if mode_hits == 0 and features.get("perturbation_mode"):
        score += 20.0
        explanation.append("unseen_mode_for_family_pattern_bonus=20")

    height = int(features.get("coefficient_height") or 0)
    if height:
        height_penalty = min(25.0, math.log10(max(height, 10)) * 1.5)
        score -= height_penalty
        explanation.append(f"height_penalty={height_penalty:.2f}")

    fatal_risk_reasons = [reason for reason in risk_reasons if is_fatal_risk_reason(str(reason))]
    advisory_risk_reasons = [reason for reason in risk_reasons if not is_fatal_risk_reason(str(reason))]
    high_risk = bool(fatal_risk_reasons)
    eligible = not high_risk and features.get("exported_coefficients") is not None
    classification = "packet_candidate" if eligible else "reject_or_hold_known_basin_risk"
    if eligible and loose_hits:
        classification = "review_packet_candidate_loose_basin_match"
    elif eligible and not loose_hits:
        classification = "strong_packet_candidate"

    return {
        "canonical_hash": features["canonical_hash"],
        "short_hash": features["short_hash"],
        "score": round(score, 3),
        "eligible_for_packet": bool(eligible),
        "anti_basin_classification": classification,
        "risk_reasons": risk_reasons,
        "fatal_risk_reasons": fatal_risk_reasons,
        "advisory_risk_reasons": advisory_risk_reasons,
        "score_explanation": explanation,
        "features": {key: value for key, value in features.items() if key != "exported_coefficients"},
        "candidate": row,
    }


def select_diverse_scores(
    scored_rows: list[dict[str, Any]],
    *,
    packet_limit: int,
    per_mode_cap: int,
    per_pattern_cap: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    hashes: set[str] = set()
    family_keys: set[str] = set()
    mode_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    rows = sorted(scored_rows, key=lambda row: (float(row["score"]), row["short_hash"]), reverse=True)
    for row in rows:
        if not row.get("eligible_for_packet"):
            continue
        features = row.get("features") or {}
        hash_value = str(row.get("canonical_hash") or "")
        family = str(features.get("family_key") or features.get("template_family_id") or features.get("basin_fingerprint") or hash_value)
        mode = str(features.get("perturbation_mode") or "unknown")
        pattern = str(features.get("decomposition_pattern") or "unknown")
        if hash_value in hashes or family in family_keys:
            continue
        if mode_counts[mode] >= per_mode_cap or pattern_counts[pattern] >= per_pattern_cap:
            continue
        selected.append(row)
        hashes.add(hash_value)
        family_keys.add(family)
        mode_counts[mode] += 1
        pattern_counts[pattern] += 1
        if len(selected) >= packet_limit:
            break
    return selected


def validated_coefficients(row: dict[str, Any]) -> str:
    exported = (row.get("candidate") or {}).get("exported_coefficients")
    if not isinstance(exported, list):
        raise ValueError("selected row missing exported_coefficients")
    return format_polynomial_line(exported)


def build_submission_recommendation(
    selected: list[dict[str, Any]],
    *,
    min_packet_rows: int,
    min_model_generated_rows: int = 0,
    min_perturbation_mode_count: int = 2,
    min_template_family_count: int = 0,
    min_basin_fingerprint_count: int = 0,
    reject_unknown_provenance: bool = False,
    sync_status: dict[str, Any] | None = None,
    sync_submission_rows: list[dict[str, Any]] | None = None,
    pending_collision_labels: set[str] | None = None,
) -> dict[str, Any]:
    mode_counts = Counter(str((row.get("features") or {}).get("perturbation_mode") or "unknown") for row in selected)
    mod_counts = Counter(str((row.get("features") or {}).get("mod_p_pattern_signature") or "none") for row in selected)
    family_counts = Counter(
        str(
            (row.get("features") or {}).get("template_family_id")
            or (row.get("features") or {}).get("family_key")
            or "unknown"
        )
        for row in selected
    )
    basin_counts = Counter(str((row.get("features") or {}).get("basin_fingerprint") or "unknown") for row in selected)
    source_counts = Counter(scored_sample_export_source(row) for row in selected)
    model_generated_rows = sum(count for source, count in source_counts.items() if is_model_generated_source(source))
    fatal_risk_count = sum(
        1
        for row in selected
        if row.get("fatal_risk_reasons")
        or any(is_fatal_risk_reason(str(reason)) for reason in row.get("risk_reasons") or [])
    )
    advisory_risk_count = sum(
        1
        for row in selected
        if row.get("advisory_risk_reasons")
        or any(not is_fatal_risk_reason(str(reason)) for reason in row.get("risk_reasons") or [])
    )
    unknown_modes = sum(count for mode, count in mode_counts.items() if mode in {"", "unknown", "manual_or_unknown"})
    unknown_families = sum(count for family, count in family_counts.items() if family in {"", "unknown"})
    unknown_basins = sum(count for basin, count in basin_counts.items() if basin in {"", "unknown"})
    local_recommended = (
        len(selected) >= min_packet_rows
        and model_generated_rows >= int(min_model_generated_rows)
        and fatal_risk_count == 0
        and "outer_constant_shift" not in mode_counts
        and len(mode_counts) >= int(min_perturbation_mode_count)
        and len(mod_counts) >= max(2, min_packet_rows // 2)
        and len(family_counts) >= int(min_template_family_count)
        and len(basin_counts) >= int(min_basin_fingerprint_count)
        and not (reject_unknown_provenance and (unknown_modes or unknown_families or unknown_basins))
    )
    reasons: list[str] = []
    if len(selected) < min_packet_rows:
        reasons.append(f"only_{len(selected)}_eligible_rows_below_min_{min_packet_rows}")
    if model_generated_rows < int(min_model_generated_rows):
        reasons.append(f"only_{model_generated_rows}_model_generated_rows_below_min_{int(min_model_generated_rows)}")
    if fatal_risk_count:
        reasons.append(f"{fatal_risk_count}_selected_rows_have_fatal_risk_reasons")
    if "outer_constant_shift" in mode_counts:
        reasons.append("selected_rows_include_outer_constant_shift")
    if len(mode_counts) < int(min_perturbation_mode_count):
        reasons.append(f"selected_rows_do_not_have_min_perturbation_mode_count_{int(min_perturbation_mode_count)}")
    if len(mod_counts) < max(2, min_packet_rows // 2):
        reasons.append("selected_rows_do_not_have_enough_mod_p_diversity")
    if len(family_counts) < int(min_template_family_count):
        reasons.append("selected_rows_do_not_have_enough_template_family_diversity")
    if len(basin_counts) < int(min_basin_fingerprint_count):
        reasons.append("selected_rows_do_not_have_enough_basin_fingerprint_diversity")
    if reject_unknown_provenance and unknown_modes:
        reasons.append(f"{unknown_modes}_selected_rows_have_unknown_perturbation_mode")
    if reject_unknown_provenance and unknown_families:
        reasons.append(f"{unknown_families}_selected_rows_have_unknown_template_family")
    if reject_unknown_provenance and unknown_basins:
        reasons.append(f"{unknown_basins}_selected_rows_have_unknown_basin_fingerprint")
    sync_gate = build_sync_submission_gate(
        selected,
        sync_status=sync_status,
        sync_submission_rows=sync_submission_rows,
        pending_collision_labels=pending_collision_labels,
    )
    if sync_gate["hold_reasons"]:
        reasons.extend(sync_gate["hold_reasons"])
    recommended = local_recommended and not sync_gate["hold_reasons"]
    reason = "anti-basin gates passed" if recommended else "; ".join(reasons)
    if local_recommended and sync_gate["hold_reasons"]:
        reason = "; ".join(sync_gate["hold_reasons"])
    return {
        "recommended_for_sair_packet": recommended,
        "local_recommended_for_sair_packet": local_recommended,
        "status": "reviewed_packet_ready_for_dry_run" if recommended else "hold_no_submission",
        "reason": reason,
        "selected_rows": len(selected),
        "selected_mode_counts": dict(mode_counts),
        "min_perturbation_mode_count": int(min_perturbation_mode_count),
        "selected_mod_p_signature_counts": dict(mod_counts),
        "selected_template_family_counts": dict(family_counts),
        "selected_basin_fingerprint_counts": dict(basin_counts),
        "selected_source_counts": dict(source_counts),
        "model_generated_selected_rows": model_generated_rows,
        "min_model_generated_rows": int(min_model_generated_rows),
        "min_template_family_count": int(min_template_family_count),
        "min_basin_fingerprint_count": int(min_basin_fingerprint_count),
        "reject_unknown_provenance": bool(reject_unknown_provenance),
        "risk_count": fatal_risk_count,
        "fatal_risk_count": fatal_risk_count,
        "advisory_risk_count": advisory_risk_count,
        "sync_submission_gate": sync_gate,
    }


def build_summary(
    *,
    candidate_paths: list[Path],
    label_basin_summary: dict[str, Any],
    progress_cache: dict[str, Any],
    scored_rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    basin_profile: dict[str, Any],
    recommendation: dict[str, Any],
    target_rs: list[int],
    output_files: dict[str, str],
    command: list[str],
    repo_root: Path,
) -> dict[str, Any]:
    score_classes = Counter(str(row.get("anti_basin_classification")) for row in scored_rows)
    eligible = [row for row in scored_rows if row.get("eligible_for_packet")]
    progress_source = progress_cache.get("source_snapshot") or {}
    return {
        "schema_version": 1,
        "record_type": "igp24_anti_basin_planner",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_anti_basin_planner.py",
        "source_commit": get_source_commit(repo_root.resolve()),
        "command": command,
        "safety": {
            "gpu_training": False,
            "model_training": False,
            "sair_submission": False,
            "sair_dry_run": False,
            "magma": False,
            "pari": False,
            "api_key_recorded": False,
        },
        "inputs": {
            "candidate_paths": [str(path) for path in candidate_paths],
            "label_basin_summary_record_type": label_basin_summary.get("record_type"),
            "progress_source": progress_source,
            "target_rs": target_rs,
        },
        "basin_profile": {
            "avoid_labels": basin_profile["avoid_labels"],
            "crowded_labels": basin_profile["crowded_labels"],
            "crowded_observation_count": basin_profile["crowded_observation_count"],
            "accepted_hash_count": len(basin_profile["accepted_hashes"]),
            "exact_fingerprint_count": len(basin_profile["exact_fingerprints"]),
            "loose_fingerprint_count": len(basin_profile["loose_fingerprints"]),
            "mod_p_signature_count": len(basin_profile["mod_signatures"]),
            "collapsed_family_pattern_count": len(basin_profile.get("collapsed_family_pattern_labels") or {}),
            "collapsed_construction_r_count": len(basin_profile.get("collapsed_construction_r_labels") or {}),
            "collapsed_pair_count": len(basin_profile.get("collapsed_pair_counts") or {}),
            "collapsed_template_r_count": len(basin_profile.get("collapsed_template_r_labels") or {}),
            "collapsed_basin_r_count": len(basin_profile.get("collapsed_basin_r_labels") or {}),
            "collapsed_model_template_r_count": len(basin_profile.get("collapsed_model_template_r_labels") or {}),
            "collapsed_model_basin_r_count": len(basin_profile.get("collapsed_model_basin_r_labels") or {}),
        },
        "candidate_count": len(scored_rows),
        "eligible_candidate_count": len(eligible),
        "selected_rows": len(selected),
        "score_classification_counts": dict(score_classes),
        "top_scored_rows": [
            {
                "rank": index + 1,
                "short_hash": row["short_hash"],
                "score": row["score"],
                "eligible_for_packet": row["eligible_for_packet"],
                "classification": row["anti_basin_classification"],
                "risk_reasons": row["risk_reasons"],
                "features": row["features"],
            }
            for index, row in enumerate(sorted(scored_rows, key=lambda item: item["score"], reverse=True)[:20])
        ],
        "selected_rows_summary": [
            {
                "rank": index + 1,
                "short_hash": row["short_hash"],
                "score": row["score"],
                "features": row["features"],
            }
            for index, row in enumerate(selected)
        ],
        "submission_recommendation": recommendation,
        "next_decision": (
            "Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet."
            if recommendation["recommended_for_sair_packet"]
            else "Do not submit this packet; local packet is ready, but wait for complete SAIR state and pending rows to resolve."
            if recommendation.get("local_recommended_for_sair_packet")
            else "Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity."
        ),
        "output_files": output_files,
    }


def build_report(summary: dict[str, Any]) -> str:
    recommendation = summary["submission_recommendation"]
    lines = [
        "# IGP24 Anti-Basin Planner",
        "",
        "This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.",
        "",
        "## Inputs",
        "",
        f"- Candidates scored: {summary['candidate_count']}",
        f"- Eligible candidates: {summary['eligible_candidate_count']}",
        f"- Selected rows: {summary['selected_rows']}",
        f"- Progress labels: {summary['inputs']['progress_source'].get('label_count')}",
        f"- Avoid labels: `{json.dumps(summary['basin_profile']['avoid_labels'])}`",
        f"- Crowded labels: `{json.dumps(summary['basin_profile']['crowded_labels'])}`",
        "",
        "## Recommendation",
        "",
        f"- Status: `{recommendation['status']}`",
        f"- Recommended for packet: `{recommendation['recommended_for_sair_packet']}`",
        f"- Local packet ready: `{recommendation.get('local_recommended_for_sair_packet')}`",
        f"- Reason: {recommendation['reason']}",
        f"- Sync gate: `{json.dumps(recommendation.get('sync_submission_gate') or {}, sort_keys=True)}`",
        f"- Mode counts: `{json.dumps(recommendation['selected_mode_counts'], sort_keys=True)}`",
        f"- Mod-p signature counts: `{json.dumps(recommendation['selected_mod_p_signature_counts'], sort_keys=True)}`",
        f"- Template family counts: `{json.dumps(recommendation.get('selected_template_family_counts') or {}, sort_keys=True)}`",
        f"- Basin fingerprint counts: `{json.dumps(recommendation.get('selected_basin_fingerprint_counts') or {}, sort_keys=True)}`",
        "",
        "## Selected Rows",
        "",
        "| rank | hash | score | r | mode | pattern | height | mod-p |",
        "| ---: | --- | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in summary["selected_rows_summary"]:
        features = row["features"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["rank"]),
                    f"`{row['short_hash']}`",
                    f"{float(row['score']):.2f}",
                    str(features.get("r")),
                    f"`{features.get('perturbation_mode')}`",
                    f"`{features.get('decomposition_pattern')}`",
                    str(features.get("coefficient_height")),
                    f"`{features.get('mod_p_pattern_signature')}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Top Scored Rows",
            "",
            "| rank | hash | score | eligible | classification | risks |",
            "| ---: | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in summary["top_scored_rows"][:15]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["rank"]),
                    f"`{row['short_hash']}`",
                    f"{float(row['score']):.2f}",
                    str(row["eligible_for_packet"]),
                    f"`{row['classification']}`",
                    f"`{';'.join(row['risk_reasons'])}`",
                ]
            )
            + " |"
        )
    lines.extend(["", f"Next decision: {summary['next_decision']}", ""])
    return "\n".join(lines)


def write_outputs(
    *,
    output_dir: Path,
    progress_cache: dict[str, Any],
    scored_rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    summary_without_outputs: dict[str, Any],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / PROGRESS_CACHE_JSON
    scores_path = output_dir / SCORES_JSONL
    selected_path = output_dir / SELECTED_JSONL
    coefficients_path = output_dir / COEFFICIENTS_TXT
    hashes_path = output_dir / HASHES_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD

    progress_path.write_text(json.dumps(progress_cache, separators=(",", ":"), sort_keys=False) + "\n", encoding="utf-8")
    write_jsonl(scores_path, [{key: value for key, value in row.items() if key != "candidate"} for row in scored_rows])
    write_jsonl(
        selected_path,
        [
            row["candidate"]
            | {
                "anti_basin_score": row["score"],
                "anti_basin_features": row["features"],
                "anti_basin_classification": row["anti_basin_classification"],
                "anti_basin_risk_reasons": row["risk_reasons"],
                "anti_basin_score_explanation": row["score_explanation"],
            }
            for row in selected
        ],
    )
    with coefficients_path.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(validated_coefficients(row) + "\n")
    hashes_path.write_text(
        "".join(f"{index}\t{row['canonical_hash']}\t{row['score']}\n" for index, row in enumerate(selected, start=1)),
        encoding="utf-8",
    )
    output_files = {
        "progress_cache_json": str(progress_path),
        "scores_jsonl": str(scores_path),
        "selected_jsonl": str(selected_path),
        "coefficients_txt": str(coefficients_path),
        "hashes_txt": str(hashes_path),
        "summary_json": str(summary_path),
        "report_md": str(report_path),
    }
    summary = {**summary_without_outputs, "output_files": output_files}
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")
    return {name: Path(path) for name, path in output_files.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score IGP24 candidate queues against accepted label basins")
    parser.add_argument("--candidate_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--label_basin_summary_json", type=Path, default=DEFAULT_LABEL_BASIN_SUMMARY)
    parser.add_argument("--label_basin_observations_jsonl", type=Path, default=DEFAULT_LABEL_BASIN_OBSERVATIONS)
    parser.add_argument(
        "--accepted_feedback_json",
        type=Path,
        action="append",
        help="Additional accepted-feedback artifact whose accepted_rows should be treated as basin observations",
    )
    progress = parser.add_mutually_exclusive_group()
    progress.add_argument("--progress_snapshot_json", type=Path)
    progress.add_argument("--fetch_live_progress", action="store_true")
    progress.add_argument("--sair_sync_dir", type=Path)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_rs", default="24,20,16,12,8")
    parser.add_argument("--avoid_labels", default=",".join(sorted(DEFAULT_AVOID_LABELS)))
    parser.add_argument("--crowded_team_threshold", type=int, default=20)
    parser.add_argument("--packet_limit", type=int, default=12)
    parser.add_argument("--min_packet_rows", type=int, default=8)
    parser.add_argument(
        "--min_model_generated_rows",
        type=int,
        default=0,
        help="minimum selected rows that must come from model-generated sample export sources before recommending a packet",
    )
    parser.add_argument("--min_perturbation_mode_count", type=int, default=2)
    parser.add_argument("--per_mode_cap", type=int, default=4)
    parser.add_argument("--per_pattern_cap", type=int, default=12)
    parser.add_argument("--min_template_family_count", type=int, default=0)
    parser.add_argument("--min_basin_fingerprint_count", type=int, default=0)
    parser.add_argument("--reject_unknown_provenance", action="store_true", default=False)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target_rs = parse_target_rs(args.target_rs)
    avoid_labels = parse_csv_set(args.avoid_labels)
    candidate_rows: list[dict[str, Any]] = []
    for path in args.candidate_jsonl:
        candidate_rows.extend(read_jsonl(path))
    label_basin_summary = json.loads(args.label_basin_summary_json.read_text(encoding="utf-8"))
    feedback_paths = list(DEFAULT_ACCEPTED_FEEDBACK_JSONS)
    if args.accepted_feedback_json is not None:
        feedback_paths.extend(args.accepted_feedback_json)
    observations = read_jsonl(args.label_basin_observations_jsonl)
    observations.extend(load_accepted_feedback_observations(feedback_paths))
    sync_status = None
    sync_submission_rows: list[dict[str, Any]] = []
    if args.sair_sync_dir:
        snapshot = load_sync_progress_snapshot(args.sair_sync_dir)
        sync_status = load_sync_status(args.sair_sync_dir)
        sync_submission_rows = load_sync_submission_rows(args.sair_sync_dir)
    else:
        snapshot = load_progress(fetch_live=bool(args.fetch_live_progress), progress_snapshot_json=args.progress_snapshot_json)
    progress_cache = normalize_progress_cache(snapshot, target_rs=target_rs)
    basin_profile = build_basin_profile(
        observations,
        label_basin_summary.get("label_summary") or {},
        avoid_labels=avoid_labels,
        crowded_team_threshold=int(args.crowded_team_threshold),
    )
    scored_rows = [
        score_candidate_row(
            row,
            target_rs=set(target_rs),
            progress_cache=progress_cache,
            basin_profile=basin_profile,
        )
        for row in candidate_rows
    ]
    selected = select_diverse_scores(
        scored_rows,
        packet_limit=int(args.packet_limit),
        per_mode_cap=int(args.per_mode_cap),
        per_pattern_cap=int(args.per_pattern_cap),
    )
    recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=int(args.min_packet_rows),
        min_model_generated_rows=int(args.min_model_generated_rows),
        min_perturbation_mode_count=int(args.min_perturbation_mode_count),
        min_template_family_count=int(args.min_template_family_count),
        min_basin_fingerprint_count=int(args.min_basin_fingerprint_count),
        reject_unknown_provenance=bool(args.reject_unknown_provenance),
        sync_status=sync_status,
        sync_submission_rows=sync_submission_rows,
        pending_collision_labels=avoid_labels,
    )
    placeholder_outputs = {
        "progress_cache_json": str(args.output_dir / PROGRESS_CACHE_JSON),
        "scores_jsonl": str(args.output_dir / SCORES_JSONL),
        "selected_jsonl": str(args.output_dir / SELECTED_JSONL),
        "coefficients_txt": str(args.output_dir / COEFFICIENTS_TXT),
        "hashes_txt": str(args.output_dir / HASHES_TXT),
        "summary_json": str(args.output_dir / SUMMARY_JSON),
        "report_md": str(args.output_dir / REPORT_MD),
    }
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_anti_basin_planner.py", *argv]
    summary = build_summary(
        candidate_paths=list(args.candidate_jsonl),
        label_basin_summary=label_basin_summary,
        progress_cache=progress_cache,
        scored_rows=scored_rows,
        selected=selected,
        basin_profile=basin_profile,
        recommendation=recommendation,
        target_rs=target_rs,
        output_files=placeholder_outputs,
        command=command,
        repo_root=args.repo_root,
    )
    paths = write_outputs(
        output_dir=args.output_dir,
        progress_cache=progress_cache,
        scored_rows=scored_rows,
        selected=selected,
        summary_without_outputs=summary,
    )
    print(f"candidate_count\t{len(scored_rows)}")
    print(f"eligible_candidate_count\t{summary['eligible_candidate_count']}")
    print(f"selected_rows\t{len(selected)}")
    print(f"recommended_for_sair_packet\t{recommendation['recommended_for_sair_packet']}")
    print(f"recommendation_status\t{recommendation['status']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
