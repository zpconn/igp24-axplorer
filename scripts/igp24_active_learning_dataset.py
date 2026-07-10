#!/usr/bin/env python3
"""Build AXG active-learning training rows from local and SAIR feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_anti_basin_planner import candidate_features, mod_pattern_signature
from scripts.igp24_shortlist import get_source_commit
from src.igp24.scoring import official_score_economics

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/active_learning"
DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"
DEFAULT_SAIR_SYNC_DIR = REPO_ROOT / "data/igp24/sair_sync_basin_gate_20260707"
DEFAULT_COLLAPSED_LABELS = {
    "24T23883",
    "24T24651",
    "24T24932",
    "24T24970",
    "24T24979",
    "24T24984",
    "24T25000",
}
DEFAULT_SCORE_POSITIVE_PAIRS = {"24T9993|r=8", "24T22770|r=12"}
SCORE_AWARE_LABELS = {
    "score_positive",
    "low_team_scoreable",
    "accepted_but_crowded_collapse",
    "accepted_duplicate",
    "wrong_r",
    "invalid",
    "pending_or_unknown",
}
SCORE_AWARE_REWARDS = {
    "score_positive": 3.0,
    "low_team_scoreable": 2.0,
    "pending_or_unknown": 0.0,
    "accepted_duplicate": -1.5,
    "wrong_r": -2.0,
    "invalid": -2.5,
    "accepted_but_crowded_collapse": -4.0,
}
SCORE_AWARE_WEIGHTS = {
    "score_positive": 4.0,
    "low_team_scoreable": 3.0,
    "pending_or_unknown": 0.5,
    "accepted_duplicate": 2.0,
    "wrong_r": 1.5,
    "invalid": 1.5,
    "accepted_but_crowded_collapse": 5.0,
}
GENERATOR_TRAINING_POLICY = {
    "score_positive": {"eligible": True, "weight": 12.0, "role": "score_positive"},
    "low_team_scoreable": {"eligible": True, "weight": 8.0, "role": "low_team_scoreable"},
    "accepted_useful_unknown": {"eligible": True, "weight": 3.0, "role": "accepted_useful_unknown"},
    "exact_local_exploration": {"eligible": True, "weight": 1.0, "role": "exact_local_exploration"},
    "crowded_collapse": {"eligible": False, "weight": 0.0, "role": "crowded_collapse"},
    "accepted_duplicate": {"eligible": False, "weight": 0.0, "role": "accepted_duplicate"},
    "wrong_r": {"eligible": False, "weight": 0.0, "role": "wrong_r"},
    "invalid": {"eligible": False, "weight": 0.0, "role": "invalid"},
    "no_valuable_target_survival": {"eligible": False, "weight": 0.0, "role": "no_valuable_target_survival"},
    "construction_route_outcome_blocked": {
        "eligible": False,
        "weight": 0.0,
        "role": "construction_route_outcome_blocked",
    },
    "non_improving_exact_pair": {"eligible": False, "weight": 0.0, "role": "non_improving_exact_pair"},
    "known_submission_hash": {"eligible": False, "weight": 0.0, "role": "known_submission_hash"},
    "packet_ineligible": {"eligible": False, "weight": 0.0, "role": "packet_ineligible"},
}
SAIR_KEY_RE = re.compile(r"sair_[0-9a-f]{12}_[A-Za-z0-9]{20,}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def parse_csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def parse_int_set(value: str | None) -> set[int]:
    if not value:
        return set()
    return {int(part.strip()) for part in value.split(",") if part.strip()}


def coefficient_list(row: dict[str, Any]) -> list[int] | None:
    exported = row.get("exported_coefficients")
    if isinstance(exported, list) and len(exported) == 25:
        return [int(value) for value in exported]
    coefficients = row.get("coefficients")
    if isinstance(coefficients, list):
        values = [int(value) for value in coefficients]
        if len(values) == 25:
            return values
        if len(values) == 24:
            return values + [1]
    decoded = row.get("decoded_coefficients")
    if isinstance(decoded, list) and len(decoded) == 24:
        return [int(value) for value in decoded] + [1]
    polynomial = row.get("polynomial")
    if isinstance(polynomial, str):
        parts = [part.strip() for part in polynomial.split(",") if part.strip()]
        if len(parts) == 25:
            try:
                return [int(part) for part in parts]
            except ValueError:
                return None
    return None


def support_features(coefficients: list[int] | None) -> dict[str, Any]:
    if not coefficients:
        return {"support_gcd": None, "even_support": None, "odd_support_exponents": []}
    support = [index for index, value in enumerate(coefficients) if int(value) != 0]
    positive = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive:
        support_gcd = math.gcd(support_gcd, exponent)
    return {
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
        "odd_support_exponents": [exponent for exponent in support if exponent % 2 == 1],
    }


def canonical_hash_for_coefficients(coefficients: list[int] | None) -> str | None:
    if not coefficients:
        return None
    text = ",".join(str(int(value)) for value in coefficients)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def feedback_rows(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("accepted_rows")
    if rows is None:
        rows = payload.get("rows")
    if rows is None:
        return []
    return [row for row in rows if isinstance(row, dict)]


def default_feedback_paths(data_root: Path) -> list[Path]:
    return sorted(data_root.glob("**/*accepted_feedback*.json"))


def load_pair_status(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"by_pair": {}, "by_hash": {}}
    payload = read_json(path)
    by_pair: dict[str, Any] = {}
    by_hash: dict[str, Any] = {}
    for row in payload.get("pairs") or []:
        if not isinstance(row, dict):
            continue
        if row.get("pair_key"):
            by_pair[str(row["pair_key"])] = row
        if row.get("canonical_hash"):
            by_hash[str(row["canonical_hash"])] = row
        for alt in row.get("accepted_alternates") or []:
            if isinstance(alt, dict) and alt.get("canonical_hash"):
                by_hash[str(alt["canonical_hash"])] = {**row, **alt}
    return {"by_pair": by_pair, "by_hash": by_hash}


def load_sair_sync(sync_dir: Path | None) -> dict[str, Any]:
    if sync_dir is None or not sync_dir.exists():
        return {"submission_rows": [], "by_hash": {}, "progress_by_label": {}, "progress_by_pair": {}}
    submission_rows = read_jsonl(sync_dir / "sair_submission_rows.jsonl")
    by_hash: dict[str, dict[str, Any]] = {}
    for row in submission_rows:
        if row.get("canonical_hash"):
            by_hash[str(row["canonical_hash"])] = row

    progress_by_label: dict[str, dict[str, Any]] = {}
    progress_by_pair: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(sync_dir / "sair_label_progress.jsonl"):
        label = str(row.get("label") or "")
        if not label:
            continue
        remaining = [int(value) for value in row.get("remainingSignatures") or []]
        discovered = [int(value) for value in row.get("discoveredSignatures") or []]
        progress_by_label[label] = {
            "label": label,
            "t": row.get("t"),
            "team_count": int(row.get("teamCount") or 0),
            "allowed_r": [int(value) for value in row.get("allowedR") or []],
            "discovered_r": discovered,
            "remaining_r": remaining,
            "fully_covered": not remaining,
            "minimum_disc_abs": row.get("minimumDiscAbs"),
        }
        for sig in row.get("signatures") or []:
            if sig.get("r") is None:
                continue
            r_value = int(sig["r"])
            progress_by_pair[f"{label}|r={r_value}"] = {
                "label": label,
                "r": r_value,
                "discovered": bool(sig.get("discovered", r_value in discovered)),
                "remaining": bool(r_value in remaining),
                "signature_team_count": int(sig.get("teamCount") or 0),
                "minimum_disc_abs": sig.get("minimumDiscAbs") or row.get("minimumDiscAbs"),
            }
    return {
        "submission_rows": submission_rows,
        "by_hash": by_hash,
        "progress_by_label": progress_by_label,
        "progress_by_pair": progress_by_pair,
    }


def pair_key(label: str | None, r_value: int | None) -> str | None:
    if not label or r_value is None:
        return None
    return f"{label}|r={int(r_value)}"


def safe_points_numeric(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    scoring = row.get("leaderboard_scoring") or {}
    value = scoring.get("points_numeric")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def exact_submission_grade_economics(row: dict[str, Any]) -> dict[str, Any] | None:
    """Official-score economics for exact-labeled local submission-grade rows.

    These rows are not treated as live SAIR-accepted rows. They are exact local
    evidence that a candidate would be scoreable if explicitly submitted and
    accepted, so they may receive positive generator-training mass without
    conflating compatibility-only candidates with exact labels.
    """
    if not boolish(row.get("submission_grade_candidate")):
        return None
    if row.get("known_submission_hash_match") or row.get("known_submission_hash"):
        return None
    classification = str(row.get("score_aware_classification") or "")
    if classification not in {
        "new_uncovered_pair",
        "accepted_pair_material_discriminant_improvement",
        "sair_discovered_pair_material_discriminant_improvement",
    }:
        return None
    exact_label = row.get("verified_group_label") or row.get("label")
    exact_r = row.get("computed_r") if row.get("computed_r") is not None else row.get("r")
    exact_nfdisc = row.get("exact_nfdisc_abs") or row.get("nfdisc_abs") or row.get("field_disc_abs")
    if not exact_label or exact_r is None or exact_nfdisc in {None, ""}:
        return None

    progress_state = str(row.get("sair_progress_state") or "")
    uncovered = progress_state == "allowed_remaining" or classification == "new_uncovered_pair"
    team_count = int(row.get("sair_progress_team_count") or row.get("team_count") or 0)
    economics = official_score_economics(
        current_team_count=team_count,
        uncovered=uncovered,
        baseline_pair=boolish(row.get("sair_progress_in_baseline")),
        current_best_disc_abs=row.get("sair_progress_minimum_disc_abs"),
        candidate_disc_abs=exact_nfdisc,
    )
    estimated = economics.get("estimated_expected_points")
    if estimated is None or float(estimated) <= 0:
        return None
    if not uncovered and economics.get("candidate_improves_current_best") is False:
        return None
    return {
        **economics,
        "basis": "exact_submission_grade_official_score_economics",
        "pair_key": pair_key(str(exact_label), int(exact_r)),
        "score_aware_classification": classification,
    }


def source_role_from_path(path: Path) -> str:
    text = str(path)
    if "accepted_feedback" in text:
        return "accepted_feedback"
    if "candidate_queue" in text or "candidates.jsonl" in text or "selected_queue" in text:
        return "candidate_queue"
    if "sair_submission_rows" in text:
        return "sair_submission_row"
    return "artifact_row"


def feature_projection(row: dict[str, Any]) -> dict[str, Any]:
    try:
        features = candidate_features(row)
    except Exception:
        coeffs = coefficient_list(row)
        support = support_features(coeffs)
        features = {
            "r": int(row.get("real_root_count") or row.get("r") or -1),
            "coefficient_height": int(row.get("coefficient_height") or 0),
            "construction_family": str(row.get("construction_family") or ""),
            "decomposition_pattern": str(row.get("decomposition_pattern") or ""),
            "perturbation_mode": str(row.get("perturbation_mode") or ""),
            "family_key": str(row.get("family_key") or ""),
            "support_gcd": support["support_gcd"],
            "even_support": support["even_support"],
            "odd_support_exponents": support["odd_support_exponents"],
            "mod_p_pattern_signature": mod_pattern_signature(row),
            "irreducible": bool(row.get("irreducible")),
            "squarefree": bool(row.get("squarefree")),
        }
    coeffs = coefficient_list(row)
    if not features.get("mod_p_pattern_signature"):
        features["mod_p_pattern_signature"] = row.get("mod_p_pattern_signature")
    if coeffs and not features.get("support_gcd"):
        features.update(support_features(coeffs))
    return {key: value for key, value in features.items() if key != "exported_coefficients"}


def generator_training_policy(
    *,
    class_label: str,
    score_label: str,
    label: str | None,
    pair: str | None,
    features: dict[str, Any],
) -> dict[str, Any]:
    if score_label in {"score_positive", "low_team_scoreable"}:
        policy = GENERATOR_TRAINING_POLICY[score_label]
        reason = f"{score_label} row is a positive generator demonstration"
    elif class_label == "accepted_useful_or_unknown":
        policy = GENERATOR_TRAINING_POLICY["accepted_useful_unknown"]
        reason = "accepted row is not currently known as crowded or duplicate"
    elif class_label == "exact_local_valid":
        policy = GENERATOR_TRAINING_POLICY["exact_local_exploration"]
        reason = "locally exact-valid row with unknown label remains exploratory"
    elif score_label == "accepted_duplicate":
        policy = GENERATOR_TRAINING_POLICY["accepted_duplicate"]
        reason = "accepted duplicate is evidence for risk/reward models, not LM imitation"
    elif score_label == "accepted_but_crowded_collapse" or class_label == "accepted_globally_covered_high_team_basin":
        policy = GENERATOR_TRAINING_POLICY["crowded_collapse"]
        reason = "crowded accepted row is negative evidence, not a generator demonstration"
    elif score_label == "wrong_r" or class_label == "wrong_real_root_count":
        policy = GENERATOR_TRAINING_POLICY["wrong_r"]
        reason = "wrong real-root count for current training target"
    elif score_label == "invalid" or class_label == "locally_invalid":
        policy = GENERATOR_TRAINING_POLICY["invalid"]
        reason = "locally invalid row"
    else:
        policy = GENERATOR_TRAINING_POLICY["exact_local_exploration"]
        reason = "unknown rows are not treated as negative"

    family = (
        features.get("construction_family")
        or features.get("template_family")
        or features.get("family_key")
        or features.get("basin_fingerprint")
        or "unknown"
    )
    return {
        "eligible": bool(policy["eligible"]),
        "weight": float(policy["weight"]),
        "role": str(policy["role"]),
        "reason": reason,
        "pair_key": pair,
        "label": label,
        "construction_family": family,
        "basin_fingerprint": features.get("basin_fingerprint"),
    }


def generator_training_block_from_row(row: dict[str, Any]) -> tuple[str, str] | None:
    if row.get("construction_route_outcome_blocked"):
        return (
            "construction_route_outcome_blocked",
            "exact route outcome ledger blocks repeating this construction basin",
        )
    if row.get("known_submission_hash_match") or row.get("known_submission_hash"):
        return ("known_submission_hash", "known canonical submission hashes are not generator demonstrations")
    if row.get("score_aware_classification") in {
        "sair_discovered_pair_not_improved",
        "accepted_pair_duplicate",
    }:
        return ("non_improving_exact_pair", "exact SAIR-discovered pair did not improve current progress")
    if row.get("eligible_for_packet") is False:
        if row.get("any_valuable_target_not_ruled_out") is False or row.get("submission_recommendation") in {
            "false_no_valuable_targets_not_ruled_out",
            "false_offline_compatibility_only",
        }:
            return (
                "no_valuable_target_survival",
                "adaptive review ruled out every currently valuable target",
            )
        return ("packet_ineligible", "row is explicitly not packet-eligible")
    return None


def split_group_key(*, features: dict[str, Any], canonical_hash: str | None) -> str:
    for key in ("construction_family", "template_family", "family_key", "basin_fingerprint"):
        value = features.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return f"canonical_hash:{canonical_hash or 'missing'}"


def enrich_row(
    *,
    row: dict[str, Any],
    source_path: Path,
    source_index: int,
    pair_status: dict[str, Any],
    sync: dict[str, Any],
    target_rs: set[int],
    collapsed_labels: set[str],
    score_positive_pairs: set[str],
    high_team_threshold: int,
) -> dict[str, Any]:
    coeffs = coefficient_list(row)
    canonical_hash = str(row.get("canonical_hash") or row.get("hash") or canonical_hash_for_coefficients(coeffs) or "")
    sync_row = sync["by_hash"].get(canonical_hash, {})
    pair_row_by_hash = pair_status["by_hash"].get(canonical_hash, {})

    r_value = row.get("real_root_count")
    if r_value is None:
        r_value = row.get("r", sync_row.get("r", pair_row_by_hash.get("r")))
    r_int = int(r_value) if r_value is not None else None

    label = row.get("label") or row.get("verified_group_label") or sync_row.get("label") or pair_row_by_hash.get("label")
    pair = row.get("pair_key") or sync_row.get("pair_key") or pair_row_by_hash.get("pair_key") or pair_key(label, r_int)
    pair_status_row = pair_status["by_pair"].get(str(pair), {}) if pair else {}
    progress_label = sync["progress_by_label"].get(str(label), {}) if label else {}
    progress_pair = sync["progress_by_pair"].get(str(pair), {}) if pair else {}
    features = feature_projection(row)
    if r_int is not None:
        features["r"] = r_int
    if canonical_hash:
        features["canonical_hash"] = canonical_hash

    local_valid = bool(row.get("valid", True))
    local_exact_valid = bool(
        local_valid
        and (row.get("irreducible", True) is not False)
        and (row.get("squarefree", True) is not False)
        and coeffs
        and len(coeffs) == 25
        and coeffs[-1] == 1
        and coeffs[0] != 0
    )
    points = safe_points_numeric(pair_status_row) or safe_points_numeric(pair_row_by_hash)
    signature_team_count = int(progress_pair.get("signature_team_count") or 0)
    label_team_count = int(progress_label.get("team_count") or 0)
    known_status = sync_row.get("status") or row.get("status") or pair_status_row.get("status")
    scoreable = sync_row.get("scoreable", row.get("scoreable"))
    exact_official_score = exact_submission_grade_economics(row)

    class_label = derive_class_label(
        label=str(label) if label else None,
        pair=str(pair) if pair else None,
        r_value=r_int,
        local_exact_valid=local_exact_valid,
        target_rs=target_rs,
        known_status=str(known_status) if known_status else None,
        scoreable=scoreable,
        points_numeric=points,
        progress_label=progress_label,
        signature_team_count=signature_team_count,
        label_team_count=label_team_count,
        collapsed_labels=collapsed_labels,
        score_positive_pairs=score_positive_pairs,
        high_team_threshold=high_team_threshold,
    )
    score_label = derive_score_aware_label(
        label=str(label) if label else None,
        pair=str(pair) if pair else None,
        r_value=r_int,
        local_exact_valid=local_exact_valid,
        target_rs=target_rs,
        known_status=str(known_status) if known_status else None,
        scoreable=scoreable,
        points_numeric=points,
        progress_label=progress_label,
        progress_pair=progress_pair,
        signature_team_count=signature_team_count,
        label_team_count=label_team_count,
        collapsed_labels=collapsed_labels,
        score_positive_pairs=score_positive_pairs,
        high_team_threshold=high_team_threshold,
    )
    if exact_official_score is not None and score_label in {
        "accepted_but_crowded_collapse",
        "accepted_duplicate",
        "pending_or_unknown",
    }:
        score_label = "low_team_scoreable"
    avoid_for_generation = score_label in {
        "accepted_but_crowded_collapse",
        "accepted_duplicate",
        "wrong_r",
        "invalid",
    }
    generator_block = generator_training_block_from_row(row)
    if generator_block is not None:
        avoid_for_generation = True

    generator_training = generator_training_policy(
        class_label=class_label,
        score_label=score_label,
        label=str(label) if label else None,
        pair=str(pair) if pair else None,
        features=features,
    )
    if generator_block is not None:
        block_policy_key, block_reason = generator_block
        block_policy = GENERATOR_TRAINING_POLICY[block_policy_key]
        generator_training = {
            **generator_training,
            "eligible": bool(block_policy["eligible"]),
            "weight": float(block_policy["weight"]),
            "role": str(block_policy["role"]),
            "reason": block_reason,
        }
    split_key = split_group_key(features=features, canonical_hash=canonical_hash)
    split_value = int(hashlib.sha256(split_key.encode("utf-8")).hexdigest()[:8], 16) % 10
    train_eval_split = "eval" if split_value in {0, 1} else "train"
    row_id = hashlib.sha256(f"{source_path}:{source_index}:{canonical_hash}".encode("utf-8")).hexdigest()[:16]

    return {
        "schema_version": 1,
        "record_type": "igp24_axg_active_learning_row",
        "dataset_row_id": row_id,
        "source_path": str(source_path),
        "source_index": source_index,
        "source_role": source_role_from_path(source_path),
        "canonical_hash": canonical_hash or None,
        "coefficients": coeffs,
        "coefficient_reference": {
            "source_path": str(source_path),
            "field": "exported_coefficients/polynomial/coefficients",
        },
        "r": r_int,
        "local_validity": {
            "valid": bool(local_valid),
            "exact_local_valid": bool(local_exact_valid),
            "irreducible": row.get("irreducible"),
            "squarefree": row.get("squarefree"),
            "verification_status": row.get("verification_status"),
        },
        "features": features,
        "sair_feedback": {
            "label": label,
            "pair_key": pair,
            "status": known_status,
            "scoreable": scoreable,
            "scoring_status": sync_row.get("scoring_status") or row.get("scoring_status") or row.get("score_status"),
            "field_disc_abs": sync_row.get("field_disc_abs") or row.get("field_disc_abs") or row.get("fieldDiscAbs"),
            "points_numeric": points,
            "exact_submission_grade_estimated_points": (
                exact_official_score.get("estimated_expected_points") if exact_official_score else None
            ),
            "in_baseline": sync_row.get("in_baseline") if sync_row else row.get("in_baseline"),
        },
        "progress_context": {
            "label_team_count": label_team_count,
            "signature_team_count": signature_team_count,
            "label_fully_covered": progress_label.get("fully_covered"),
            "pair_remaining": progress_pair.get("remaining"),
        },
        "derived_class_label": class_label,
        "score_aware_supervision": {
            "label": score_label,
            "reward": SCORE_AWARE_REWARDS[score_label],
            "weight": SCORE_AWARE_WEIGHTS[score_label],
            "avoid_for_generation": avoid_for_generation,
            "is_score_positive": score_label == "score_positive",
            "is_low_team_scoreable": score_label == "low_team_scoreable",
            "is_crowded_collapse": score_label == "accepted_but_crowded_collapse",
            "is_duplicate": score_label == "accepted_duplicate",
            "signature_team_count": signature_team_count,
            "label_team_count": label_team_count,
            "pair_remaining": progress_pair.get("remaining"),
            "pair_discovered": progress_pair.get("discovered"),
            "exact_submission_grade_official_score": exact_official_score,
        },
        "generator_training": {
            **generator_training,
            "split_group_key": split_key,
        },
        "train_eval_split": train_eval_split,
        "leakage_provenance": {
            "source_role": source_role_from_path(source_path),
            "uses_sair_label_feedback": bool(label),
            "uses_sair_score_feedback": points is not None,
            "safe_for_generator_training": True,
            "training_use_note": "Labels are used as active-learning supervision, not as raw submission targets.",
        },
    }


def derive_class_label(
    *,
    label: str | None,
    pair: str | None,
    r_value: int | None,
    local_exact_valid: bool,
    target_rs: set[int],
    known_status: str | None,
    scoreable: Any,
    points_numeric: float | None,
    progress_label: dict[str, Any],
    signature_team_count: int,
    label_team_count: int,
    collapsed_labels: set[str],
    score_positive_pairs: set[str],
    high_team_threshold: int,
) -> str:
    if not local_exact_valid and known_status != "accepted":
        return "locally_invalid"
    if target_rs and r_value is not None and r_value not in target_rs:
        return "wrong_real_root_count"
    if known_status == "accepted" or label or pair:
        if pair in score_positive_pairs or (points_numeric is not None and points_numeric > 0):
            return "accepted_useful_score_positive"
        if label in collapsed_labels:
            return "accepted_duplicate_collapsed_basin"
        if bool(progress_label.get("fully_covered")) or signature_team_count >= high_team_threshold or label_team_count >= high_team_threshold:
            return "accepted_globally_covered_high_team_basin"
        if scoreable is False or str(scoreable).lower() == "false":
            return "pending_score"
        return "accepted_useful_or_unknown"
    return "exact_local_valid" if local_exact_valid else "locally_invalid"


def derive_score_aware_label(
    *,
    label: str | None,
    pair: str | None,
    r_value: int | None,
    local_exact_valid: bool,
    target_rs: set[int],
    known_status: str | None,
    scoreable: Any,
    points_numeric: float | None,
    progress_label: dict[str, Any],
    progress_pair: dict[str, Any],
    signature_team_count: int,
    label_team_count: int,
    collapsed_labels: set[str],
    score_positive_pairs: set[str],
    high_team_threshold: int,
) -> str:
    """Return AXG-1.7 score-aware supervision for training and gating.

    This is intentionally separate from ``derive_class_label`` so older AXG
    consumers keep their previous class vocabulary while AXG-1.7 can learn from
    score potential and known collapse failures.
    """
    if not local_exact_valid and known_status != "accepted":
        return "invalid"
    if target_rs and r_value is not None and r_value not in target_rs:
        return "wrong_r"

    is_accepted = known_status == "accepted" or bool(label) or bool(pair)
    positive = pair in score_positive_pairs or (points_numeric is not None and points_numeric > 0)
    if positive:
        return "score_positive"

    crowded = (
        label in collapsed_labels
        or bool(progress_label.get("fully_covered"))
        or signature_team_count >= high_team_threshold
        or label_team_count >= high_team_threshold
    )
    if is_accepted and crowded:
        return "accepted_but_crowded_collapse"

    scoreable_bool = None
    if scoreable is not None:
        scoreable_bool = bool(scoreable) if isinstance(scoreable, bool) else str(scoreable).lower() == "true"
    low_team = (
        is_accepted
        and scoreable_bool is True
        and not progress_pair.get("remaining", False)
        and 0 < signature_team_count <= 3
    )
    if low_team:
        return "low_team_scoreable"

    if is_accepted and progress_pair.get("discovered") and signature_team_count > 3:
        return "accepted_duplicate"
    if is_accepted and scoreable_bool is True and not progress_pair.get("remaining", False):
        return "accepted_duplicate"

    return "pending_or_unknown"


def build_dataset(
    *,
    candidate_paths: list[Path],
    feedback_paths: list[Path],
    pair_status_path: Path | None,
    sair_sync_dir: Path | None,
    target_rs: set[int],
    collapsed_labels: set[str],
    score_positive_pairs: set[str],
    high_team_threshold: int,
    max_rows: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pair_status = load_pair_status(pair_status_path)
    sync = load_sair_sync(sair_sync_dir)
    rows: list[dict[str, Any]] = []

    sources: list[tuple[Path, list[dict[str, Any]]]] = []
    for path in candidate_paths:
        sources.append((path, read_jsonl(path)))
    for path in feedback_paths:
        sources.append((path, feedback_rows(path)))
    if sair_sync_dir and (sair_sync_dir / "sair_submission_rows.jsonl").exists():
        sources.append((sair_sync_dir / "sair_submission_rows.jsonl", sync["submission_rows"]))

    for path, source_rows in sources:
        for index, source_row in enumerate(source_rows):
            rows.append(
                enrich_row(
                    row=source_row,
                    source_path=path,
                    source_index=index,
                    pair_status=pair_status,
                    sync=sync,
                    target_rs=target_rs,
                    collapsed_labels=collapsed_labels,
                    score_positive_pairs=score_positive_pairs,
                    high_team_threshold=high_team_threshold,
                )
            )
            if max_rows is not None and len(rows) >= max_rows:
                break
        if max_rows is not None and len(rows) >= max_rows:
            break

    class_counts = Counter(row["derived_class_label"] for row in rows)
    score_aware_counts = Counter(row["score_aware_supervision"]["label"] for row in rows)
    score_aware_weight_by_class = {
        label: round(sum(float(row["score_aware_supervision"]["weight"]) for row in rows if row["score_aware_supervision"]["label"] == label), 3)
        for label in sorted(score_aware_counts)
    }
    source_counts = Counter(row["source_role"] for row in rows)
    label_counts = Counter((row["sair_feedback"] or {}).get("label") or "unknown" for row in rows)
    split_counts = Counter(row["train_eval_split"] for row in rows)
    generator_counts = Counter(row["generator_training"]["role"] for row in rows)
    generator_eligible_rows = [row for row in rows if row["generator_training"]["eligible"] and row["generator_training"]["weight"] > 0]
    generator_mass_by_role: Counter[str] = Counter()
    generator_mass_by_label: Counter[str] = Counter()
    generator_mass_by_family: Counter[str] = Counter()
    for row in generator_eligible_rows:
        generator = row["generator_training"]
        weight = float(generator["weight"])
        generator_mass_by_role[str(generator["role"])] += weight
        generator_mass_by_label[str(generator.get("label") or "unknown")] += weight
        generator_mass_by_family[str(generator.get("construction_family") or "unknown")] += weight
    summary = {
        "schema_version": 1,
        "record_type": "igp24_axg_active_learning_dataset_summary",
        "created_at": utc_now(),
        "source_commit": get_source_commit(REPO_ROOT),
        "row_count": len(rows),
        "candidate_source_count": len(candidate_paths),
        "feedback_source_count": len(feedback_paths),
        "sair_sync_dir": str(sair_sync_dir) if sair_sync_dir else None,
        "pair_status_path": str(pair_status_path) if pair_status_path else None,
        "target_rs": sorted(target_rs),
        "collapsed_labels": sorted(collapsed_labels),
        "score_positive_pairs": sorted(score_positive_pairs),
        "high_team_threshold": high_team_threshold,
        "class_counts": dict(class_counts),
        "score_aware_class_counts": dict(score_aware_counts),
        "score_aware_weight_by_class": score_aware_weight_by_class,
        "generator_training": {
            "physical_row_count": len(rows),
            "eligible_row_count": len(generator_eligible_rows),
            "role_counts": dict(generator_counts),
            "eligible_role_counts": dict(Counter(row["generator_training"]["role"] for row in generator_eligible_rows)),
            "sampling_mass_by_role": dict(sorted(generator_mass_by_role.items())),
            "sampling_mass_by_label_top": generator_mass_by_label.most_common(20),
            "sampling_mass_by_construction_family_top": generator_mass_by_family.most_common(20),
            "policy": GENERATOR_TRAINING_POLICY,
        },
        "source_role_counts": dict(source_counts),
        "label_counts_top": label_counts.most_common(20),
        "train_eval_split_counts": dict(split_counts),
        "safety": {
            "calls_sair": False,
            "uses_network": False,
            "auto_submits": False,
            "api_key_recorded": False,
        },
    }
    return rows, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--accepted_feedback_json", type=Path, action="append", default=[])
    parser.add_argument("--auto_feedback_root", type=Path, default=None)
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--sair_sync_dir", type=Path, default=DEFAULT_SAIR_SYNC_DIR)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dataset_date", default=datetime.now(timezone.utc).strftime("%Y%m%d"))
    parser.add_argument("--target_rs", default="")
    parser.add_argument("--collapsed_labels", default=",".join(sorted(DEFAULT_COLLAPSED_LABELS)))
    parser.add_argument("--score_positive_pairs", default=",".join(sorted(DEFAULT_SCORE_POSITIVE_PAIRS)))
    parser.add_argument("--high_team_threshold", type=int, default=20)
    parser.add_argument("--max_rows", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    feedback_paths = list(args.accepted_feedback_json)
    if args.auto_feedback_root:
        feedback_paths.extend(default_feedback_paths(args.auto_feedback_root))
    rows, summary = build_dataset(
        candidate_paths=list(args.candidate_jsonl),
        feedback_paths=sorted(set(feedback_paths)),
        pair_status_path=args.pair_status_json,
        sair_sync_dir=args.sair_sync_dir,
        target_rs=parse_int_set(args.target_rs),
        collapsed_labels=parse_csv_set(args.collapsed_labels),
        score_positive_pairs=parse_csv_set(args.score_positive_pairs),
        high_team_threshold=args.high_team_threshold,
        max_rows=args.max_rows,
    )
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / f"axg_training_dataset_{args.dataset_date}.jsonl"
    summary_path = output_dir / f"axg_training_dataset_summary_{args.dataset_date}.json"
    write_jsonl(dataset_path, rows)
    write_json(summary_path, {**summary, "dataset_path": str(dataset_path), "summary_path": str(summary_path)})

    text = json.dumps(summary)
    if SAIR_KEY_RE.search(text) or any(SAIR_KEY_RE.search(json.dumps(row)) for row in rows):
        raise RuntimeError("SAIR key-shaped string found in dataset output")

    print(f"dataset_path\t{dataset_path}")
    print(f"summary_path\t{summary_path}")
    print(f"row_count\t{summary['row_count']}")
    print(f"class_counts\t{json.dumps(summary['class_counts'], sort_keys=True)}")
    print(f"source_role_counts\t{json.dumps(summary['source_role_counts'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
