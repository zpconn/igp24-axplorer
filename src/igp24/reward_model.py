"""Advisory reward and collapse-risk model for IGP24 active learning.

This module intentionally keeps the first Phase 2 model small, deterministic,
and dependency-free. It is not an exact-label verifier and it is not a fatal
submission gate. It learns from historical outcome labels to rank candidates by
score-positive evidence and collapse risk while reporting uncertainty.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

SCHEMA_VERSION = 1
MODEL_TYPE = "igp24_advisory_reward_risk_nb"

OUTCOME_SCORE_POSITIVE = "score_positive"
OUTCOME_LOW_TEAM_SCOREABLE = "low_team_scoreable"
OUTCOME_CROWDED_COLLAPSE = "crowded_accepted_collapse"
OUTCOME_NO_VALUABLE_TARGET_SURVIVAL = "no_valuable_target_survival"
OUTCOME_ACCEPTED_DUPLICATE = "accepted_duplicate"
OUTCOME_WRONG_R = "wrong_r"
OUTCOME_INVALID = "invalid"
OUTCOME_UNKNOWN = "unknown"

SUPERVISED_OUTCOMES = (
    OUTCOME_SCORE_POSITIVE,
    OUTCOME_LOW_TEAM_SCOREABLE,
    OUTCOME_CROWDED_COLLAPSE,
    OUTCOME_NO_VALUABLE_TARGET_SURVIVAL,
    OUTCOME_ACCEPTED_DUPLICATE,
    OUTCOME_WRONG_R,
    OUTCOME_INVALID,
)
POSITIVE_OUTCOMES = {OUTCOME_SCORE_POSITIVE, OUTCOME_LOW_TEAM_SCOREABLE}
COLLAPSE_RISK_OUTCOMES = {
    OUTCOME_CROWDED_COLLAPSE,
    OUTCOME_NO_VALUABLE_TARGET_SURVIVAL,
    OUTCOME_ACCEPTED_DUPLICATE,
    OUTCOME_WRONG_R,
    OUTCOME_INVALID,
}
# Verified label and team-count fields are downstream score context, not
# reliable generator features. Including them made "missing label" a spurious
# positive signal for unverified candidates.
DEFAULT_FEATURE_KEYS = (
    "r_bucket",
    "height_bucket",
    "support_size_bucket",
    "support_gcd",
    "even_support",
    "odd_support_count_bucket",
    "construction_family",
    "template_family_id",
    "decomposition_pattern",
    "perturbation_mode",
    "sparse_support_submode",
    "basin_fingerprint",
    "mod_p_pattern_signature",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def _as_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _bucket_number(value: Any, bounds: Sequence[int], *, missing: str = "missing") -> str:
    parsed = _as_int(value)
    if parsed is None:
        return missing
    magnitude = abs(parsed)
    for bound in bounds:
        if magnitude <= bound:
            return f"<= {bound}"
    return f"> {bounds[-1]}"


def _truthy_bucket(value: Any) -> str:
    if value is None:
        return "missing"
    return "true" if bool(value) else "false"


def _support_size(coefficients: Sequence[Any] | None) -> int | None:
    if not coefficients:
        return None
    return sum(1 for value in coefficients if int(value) != 0)


def _feature_source(record: dict[str, Any]) -> dict[str, Any]:
    features = record.get("features")
    return features if isinstance(features, dict) else {}


def _score_aware_source(record: dict[str, Any]) -> dict[str, Any]:
    score_aware = record.get("score_aware_supervision")
    return score_aware if isinstance(score_aware, dict) else {}


def _generator_training_source(record: dict[str, Any]) -> dict[str, Any]:
    contract = record.get("generator_training")
    return contract if isinstance(contract, dict) else {}


def _sair_feedback_source(record: dict[str, Any]) -> dict[str, Any]:
    feedback = record.get("sair_feedback")
    return feedback if isinstance(feedback, dict) else {}


def _progress_source(record: dict[str, Any]) -> dict[str, Any]:
    progress = record.get("progress_context")
    return progress if isinstance(progress, dict) else {}


def outcome_from_record(record: dict[str, Any]) -> str:
    """Map heterogeneous active-learning records to Phase 2 outcome classes."""

    score_aware = _score_aware_source(record)
    generator_training = _generator_training_source(record)
    derived = str(record.get("derived_class_label") or "")
    score_label = str(score_aware.get("label") or "")
    role = str(generator_training.get("role") or "")
    feedback = _sair_feedback_source(record)
    status = str(feedback.get("status") or record.get("status") or "")
    scoreable = feedback.get("scoreable")

    if score_label == "score_positive" or role == OUTCOME_SCORE_POSITIVE:
        return OUTCOME_SCORE_POSITIVE
    if score_label == "low_team_scoreable" or role == OUTCOME_LOW_TEAM_SCOREABLE:
        return OUTCOME_LOW_TEAM_SCOREABLE
    if score_label == OUTCOME_NO_VALUABLE_TARGET_SURVIVAL or role == OUTCOME_NO_VALUABLE_TARGET_SURVIVAL:
        return OUTCOME_NO_VALUABLE_TARGET_SURVIVAL
    if score_label == "accepted_but_crowded_collapse" or role == "crowded_collapse":
        return OUTCOME_CROWDED_COLLAPSE
    if score_label == "accepted_duplicate" or role == OUTCOME_ACCEPTED_DUPLICATE:
        return OUTCOME_ACCEPTED_DUPLICATE
    if score_label == "wrong_r" or role == OUTCOME_WRONG_R or derived == "wrong_real_root_count":
        return OUTCOME_WRONG_R
    if score_label == "invalid" or role == OUTCOME_INVALID or derived == "locally_invalid":
        return OUTCOME_INVALID
    if derived == "accepted_globally_covered_high_team_basin":
        return OUTCOME_CROWDED_COLLAPSE
    if derived == "accepted_useful_or_unknown" and status == "accepted" and scoreable is True:
        return OUTCOME_UNKNOWN
    return OUTCOME_UNKNOWN


def group_key_from_record(record: dict[str, Any]) -> str:
    """Return the leakage-prevention group key used for Phase 2 validation."""

    features = _feature_source(record)
    generator_training = _generator_training_source(record)
    for source, key in (
        (features, "construction_family"),
        (features, "template_family_id"),
        (features, "family_key"),
        (features, "basin_fingerprint"),
        (generator_training, "split_group_key"),
        (features, "canonical_hash"),
    ):
        value = source.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    canonical_hash = record.get("canonical_hash") or record.get("dataset_row_id") or stable_hash(record)
    return f"canonical_hash:{canonical_hash}"


def group_family_from_record(record: dict[str, Any]) -> str:
    features = _feature_source(record)
    for key in ("construction_family", "template_family_id", "family_key", "basin_fingerprint"):
        value = features.get(key)
        if value not in (None, ""):
            return str(value)
    return group_key_from_record(record)


def feature_projection(record: dict[str, Any]) -> dict[str, str]:
    """Extract categorical features for the advisory model."""

    features = _feature_source(record)
    feedback = _sair_feedback_source(record)
    progress = _progress_source(record)
    coefficients = record.get("coefficients")
    if not isinstance(coefficients, list):
        coefficients = features.get("exported_coefficients")
    odd_support = features.get("odd_support_exponents")
    if not isinstance(odd_support, list):
        odd_support = []

    label = features.get("label") or feedback.get("label") or ""
    signature_team_count = progress.get("signature_team_count") or _score_aware_source(record).get("signature_team_count")
    label_team_count = progress.get("label_team_count") or _score_aware_source(record).get("label_team_count")

    projection = {
        "r_bucket": _bucket_number(record.get("r", features.get("r")), [0, 4, 8, 12, 16, 20, 24]),
        "height_bucket": _bucket_number(features.get("coefficient_height"), [1, 8, 32, 128, 1024, 1_000_000]),
        "support_size_bucket": _bucket_number(_support_size(coefficients), [2, 4, 6, 8, 12, 18, 25]),
        "support_gcd": str(features.get("support_gcd") if features.get("support_gcd") is not None else "missing"),
        "even_support": _truthy_bucket(features.get("even_support")),
        "odd_support_count_bucket": _bucket_number(len(odd_support), [0, 1, 2, 4, 8, 16]),
        "construction_family": str(features.get("construction_family") or "missing"),
        "template_family_id": str(features.get("template_family_id") or "missing"),
        "decomposition_pattern": str(features.get("decomposition_pattern") or "missing"),
        "perturbation_mode": str(features.get("perturbation_mode") or "missing"),
        "sparse_support_submode": str(features.get("sparse_support_submode") or "missing"),
        "basin_fingerprint": str(features.get("basin_fingerprint") or "missing"),
        "mod_p_pattern_signature": str(features.get("mod_p_pattern_signature") or "missing"),
        "label": str(label or "missing"),
        "signature_team_bucket": _bucket_number(signature_team_count, [0, 1, 3, 10, 25, 50]),
        "label_team_bucket": _bucket_number(label_team_count, [0, 1, 3, 10, 25, 50]),
    }
    return projection


@dataclass(frozen=True)
class RewardPrediction:
    probabilities: dict[str, float]
    reward_probability: float
    collapse_risk_probability: float
    uncertainty_entropy: float
    confidence: float
    decision: str
    top_outcome: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "probabilities": dict(sorted(self.probabilities.items())),
            "reward_probability": self.reward_probability,
            "collapse_risk_probability": self.collapse_risk_probability,
            "uncertainty_entropy": self.uncertainty_entropy,
            "confidence": self.confidence,
            "decision": self.decision,
            "top_outcome": self.top_outcome,
        }


class AdvisoryRewardModel:
    """Class-balanced categorical Naive Bayes reward/risk model."""

    def __init__(
        self,
        *,
        class_feature_counts: dict[str, dict[str, dict[str, float]]],
        class_feature_totals: dict[str, dict[str, float]],
        class_counts: dict[str, int],
        feature_value_counts: dict[str, int],
        alpha: float = 0.5,
        min_supervised_rows: int = 12,
        abstain_entropy_threshold: float = 0.72,
        abstain_confidence_threshold: float = 0.45,
    ) -> None:
        self.class_feature_counts = class_feature_counts
        self.class_feature_totals = class_feature_totals
        self.class_counts = class_counts
        self.feature_value_counts = feature_value_counts
        self.alpha = float(alpha)
        self.min_supervised_rows = int(min_supervised_rows)
        self.abstain_entropy_threshold = float(abstain_entropy_threshold)
        self.abstain_confidence_threshold = float(abstain_confidence_threshold)
        self.outcomes = tuple(label for label in SUPERVISED_OUTCOMES if self.class_counts.get(label, 0) > 0)

    @property
    def supervised_row_count(self) -> int:
        return int(sum(self.class_counts.values()))

    def predict(self, record: dict[str, Any] | dict[str, str]) -> RewardPrediction:
        if not self.outcomes:
            probabilities = {label: 0.0 for label in SUPERVISED_OUTCOMES}
            probabilities[OUTCOME_UNKNOWN] = 1.0
            return RewardPrediction(
                probabilities=probabilities,
                reward_probability=0.0,
                collapse_risk_probability=0.0,
                uncertainty_entropy=1.0,
                confidence=0.0,
                decision="abstain_insufficient_supervision",
                top_outcome=OUTCOME_UNKNOWN,
            )

        projection = record if all(isinstance(value, str) for value in record.values()) else feature_projection(record)  # type: ignore[arg-type]
        log_probs: dict[str, float] = {}
        uniform_log_prior = -math.log(len(self.outcomes))
        for outcome in self.outcomes:
            log_prob = uniform_log_prior
            for feature in DEFAULT_FEATURE_KEYS:
                value = str(projection.get(feature, "missing"))
                value_count = max(1, int(self.feature_value_counts.get(feature, 1)))
                numerator = (
                    self.class_feature_counts.get(outcome, {})
                    .get(feature, {})
                    .get(value, 0.0)
                    + self.alpha
                )
                denominator = self.class_feature_totals.get(outcome, {}).get(feature, 0.0) + self.alpha * value_count
                log_prob += math.log(numerator / denominator)
            log_probs[outcome] = log_prob

        max_log = max(log_probs.values())
        raw = {outcome: math.exp(value - max_log) for outcome, value in log_probs.items()}
        normalizer = sum(raw.values()) or 1.0
        probabilities = {label: 0.0 for label in SUPERVISED_OUTCOMES}
        probabilities.update({outcome: raw[outcome] / normalizer for outcome in raw})
        reward_probability = sum(probabilities.get(label, 0.0) for label in POSITIVE_OUTCOMES)
        collapse_risk = sum(probabilities.get(label, 0.0) for label in COLLAPSE_RISK_OUTCOMES)
        top_outcome = max(probabilities, key=lambda label: probabilities[label])
        confidence = probabilities[top_outcome]
        entropy = -sum(value * math.log(value) for value in probabilities.values() if value > 0)
        normalized_entropy = entropy / math.log(max(2, len([value for value in probabilities.values() if value > 0])))
        positive_supervised_count = sum(self.class_counts.get(label, 0) for label in POSITIVE_OUTCOMES)

        if self.supervised_row_count < self.min_supervised_rows:
            decision = "abstain_insufficient_supervision"
        elif normalized_entropy >= self.abstain_entropy_threshold or confidence < self.abstain_confidence_threshold:
            decision = "abstain_uncertain"
        elif collapse_risk >= 0.70 and collapse_risk > reward_probability:
            decision = "avoid_high_collapse_risk"
        elif positive_supervised_count < 20 and collapse_risk >= 0.25:
            decision = "advisory_conflicted_sparse_positive"
        elif positive_supervised_count < 20 and reward_probability >= 0.55 and reward_probability > collapse_risk:
            decision = "advisory_sparse_positive_candidate"
        elif reward_probability >= 0.55 and reward_probability > collapse_risk:
            decision = "prefer_reward_candidate"
        else:
            decision = "advisory_review"

        return RewardPrediction(
            probabilities=probabilities,
            reward_probability=reward_probability,
            collapse_risk_probability=collapse_risk,
            uncertainty_entropy=normalized_entropy,
            confidence=confidence,
            decision=decision,
            top_outcome=top_outcome,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "record_type": "igp24_reward_model",
            "model_type": MODEL_TYPE,
            "created_at": utc_now(),
            "alpha": self.alpha,
            "min_supervised_rows": self.min_supervised_rows,
            "abstain_entropy_threshold": self.abstain_entropy_threshold,
            "abstain_confidence_threshold": self.abstain_confidence_threshold,
            "feature_keys": list(DEFAULT_FEATURE_KEYS),
            "supervised_outcomes": list(SUPERVISED_OUTCOMES),
            "class_counts": dict(sorted(self.class_counts.items())),
            "class_feature_counts": self.class_feature_counts,
            "class_feature_totals": self.class_feature_totals,
            "feature_value_counts": dict(sorted(self.feature_value_counts.items())),
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "AdvisoryRewardModel":
        if payload.get("model_type") != MODEL_TYPE:
            raise ValueError(f"unsupported reward model type: {payload.get('model_type')}")
        return cls(
            class_feature_counts=payload.get("class_feature_counts") or {},
            class_feature_totals=payload.get("class_feature_totals") or {},
            class_counts={str(key): int(value) for key, value in (payload.get("class_counts") or {}).items()},
            feature_value_counts={
                str(key): int(value) for key, value in (payload.get("feature_value_counts") or {}).items()
            },
            alpha=float(payload.get("alpha", 1.0)),
            min_supervised_rows=int(payload.get("min_supervised_rows", 12)),
            abstain_entropy_threshold=float(payload.get("abstain_entropy_threshold", 0.72)),
            abstain_confidence_threshold=float(payload.get("abstain_confidence_threshold", 0.45)),
        )


def train_reward_model(
    records: Sequence[dict[str, Any]],
    *,
    alpha: float = 0.5,
    min_supervised_rows: int = 12,
    abstain_entropy_threshold: float = 0.72,
    abstain_confidence_threshold: float = 0.45,
) -> AdvisoryRewardModel:
    """Train an advisory model, excluding unknown labels.

    The class prior used at prediction time is uniform, which handles class
    imbalance without letting crowded rows dominate by raw count. Within each
    class, feature likelihoods use raw counts so repeated historical collapse
    labels/families remain strong risk evidence.
    """

    supervised = [(record, outcome_from_record(record)) for record in records]
    supervised = [(record, outcome) for record, outcome in supervised if outcome != OUTCOME_UNKNOWN]
    class_counts = Counter(outcome for _, outcome in supervised)
    feature_values: dict[str, set[str]] = {key: set() for key in DEFAULT_FEATURE_KEYS}
    class_feature_counts: dict[str, dict[str, dict[str, float]]] = {
        outcome: {feature: defaultdict(float) for feature in DEFAULT_FEATURE_KEYS} for outcome in SUPERVISED_OUTCOMES
    }
    class_feature_totals: dict[str, dict[str, float]] = {
        outcome: {feature: 0.0 for feature in DEFAULT_FEATURE_KEYS} for outcome in SUPERVISED_OUTCOMES
    }

    for record, outcome in supervised:
        projection = feature_projection(record)
        class_weight = 1.0
        for feature in DEFAULT_FEATURE_KEYS:
            value = str(projection.get(feature, "missing"))
            feature_values[feature].add(value)
            class_feature_counts[outcome][feature][value] += class_weight
            class_feature_totals[outcome][feature] += class_weight

    return AdvisoryRewardModel(
        class_feature_counts={
            outcome: {feature: dict(values) for feature, values in by_feature.items()}
            for outcome, by_feature in class_feature_counts.items()
        },
        class_feature_totals=class_feature_totals,
        class_counts=dict(class_counts),
        feature_value_counts={feature: max(1, len(values)) for feature, values in feature_values.items()},
        alpha=alpha,
        min_supervised_rows=min_supervised_rows,
        abstain_entropy_threshold=abstain_entropy_threshold,
        abstain_confidence_threshold=abstain_confidence_threshold,
    )


def grouped_split(records: Sequence[dict[str, Any]], *, holdout_fraction: float = 0.2) -> dict[str, Any]:
    """Deterministic group split with no family leakage."""

    groups: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        groups[group_key_from_record(record)].append(index)
    ordered_groups = sorted(groups.items(), key=lambda item: (stable_hash(item[0]), item[0]))
    supervised_by_group = {
        group: sum(1 for index in indices if outcome_from_record(records[index]) != OUTCOME_UNKNOWN)
        for group, indices in ordered_groups
    }
    supervised_total = sum(supervised_by_group.values())
    target = max(1, int(round(supervised_total * holdout_fraction))) if supervised_total else 0
    eval_groups: set[str] = set()
    eval_supervised = 0
    for group, _indices in ordered_groups:
        if supervised_by_group[group] <= 0:
            continue
        if eval_supervised < target:
            eval_groups.add(group)
            eval_supervised += supervised_by_group[group]
    train_indices: list[int] = []
    eval_indices: list[int] = []
    for group, indices in groups.items():
        if group in eval_groups:
            eval_indices.extend(indices)
        else:
            train_indices.extend(indices)
    overlap = sorted(set(group_key_from_record(records[index]) for index in train_indices) & set(eval_groups))
    return {
        "train_indices": sorted(train_indices),
        "eval_indices": sorted(eval_indices),
        "train_groups": sorted(set(group_key_from_record(records[index]) for index in train_indices)),
        "eval_groups": sorted(eval_groups),
        "group_overlap": overlap,
        "supervised_total": supervised_total,
        "eval_supervised": eval_supervised,
    }


def confusion_matrix(
    truth_and_predictions: Iterable[tuple[str, str]],
    *,
    labels: Sequence[str] = SUPERVISED_OUTCOMES,
) -> dict[str, dict[str, int]]:
    matrix = {truth: {prediction: 0 for prediction in labels} for truth in labels}
    for truth, prediction in truth_and_predictions:
        if truth in matrix and prediction in matrix[truth]:
            matrix[truth][prediction] += 1
    return matrix


def per_class_metrics(matrix: dict[str, dict[str, int]]) -> dict[str, dict[str, float | int]]:
    labels = list(matrix)
    metrics: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = matrix[label].get(label, 0)
        fp = sum(matrix[other].get(label, 0) for other in labels if other != label)
        fn = sum(count for pred, count in matrix[label].items() if pred != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": tp + fn,
        }
    return metrics


def calibration_summary(rows: Iterable[tuple[str, RewardPrediction]]) -> dict[str, Any]:
    buckets = {
        "0.00-0.50": {"count": 0, "correct": 0},
        "0.50-0.70": {"count": 0, "correct": 0},
        "0.70-0.85": {"count": 0, "correct": 0},
        "0.85-1.00": {"count": 0, "correct": 0},
    }
    entropy_values: list[float] = []
    abstentions = 0
    for truth, prediction in rows:
        confidence = prediction.confidence
        if confidence < 0.50:
            bucket = "0.00-0.50"
        elif confidence < 0.70:
            bucket = "0.50-0.70"
        elif confidence < 0.85:
            bucket = "0.70-0.85"
        else:
            bucket = "0.85-1.00"
        buckets[bucket]["count"] += 1
        buckets[bucket]["correct"] += int(prediction.top_outcome == truth)
        entropy_values.append(prediction.uncertainty_entropy)
        if prediction.decision.startswith("abstain"):
            abstentions += 1
    for bucket in buckets.values():
        bucket["accuracy"] = bucket["correct"] / bucket["count"] if bucket["count"] else None
    total = sum(bucket["count"] for bucket in buckets.values())
    return {
        "buckets": buckets,
        "mean_entropy": sum(entropy_values) / len(entropy_values) if entropy_values else None,
        "abstention_count": abstentions,
        "abstention_rate": abstentions / total if total else None,
        "evaluated_count": total,
    }


def evaluate_records(
    model: AdvisoryRewardModel,
    records: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    evaluated: list[tuple[str, RewardPrediction]] = []
    truth_predictions: list[tuple[str, str]] = []
    unknown_count = 0
    for record in records:
        truth = outcome_from_record(record)
        if truth == OUTCOME_UNKNOWN:
            unknown_count += 1
            continue
        prediction = model.predict(record)
        evaluated.append((truth, prediction))
        truth_predictions.append((truth, prediction.top_outcome))
    matrix = confusion_matrix(truth_predictions)
    return {
        "supervised_evaluated_count": len(evaluated),
        "unknown_excluded_count": unknown_count,
        "confusion_matrix": matrix,
        "per_class_metrics": per_class_metrics(matrix),
        "calibration": calibration_summary(evaluated),
    }


def leave_one_family_out(records: Sequence[dict[str, Any]], *, max_families: int | None = None) -> dict[str, Any]:
    families: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        if outcome_from_record(record) == OUTCOME_UNKNOWN:
            continue
        families[group_family_from_record(record)].append(index)
    ordered = sorted(families.items(), key=lambda item: (-len(item[1]), item[0]))
    if max_families is not None:
        ordered = ordered[: max(0, max_families)]
    rows: list[dict[str, Any]] = []
    aggregate_truth_predictions: list[tuple[str, str]] = []
    for family, indices in ordered:
        train = [record for index, record in enumerate(records) if index not in set(indices)]
        test = [records[index] for index in indices]
        supervised_train_count = sum(1 for record in train if outcome_from_record(record) != OUTCOME_UNKNOWN)
        if supervised_train_count == 0:
            continue
        model = train_reward_model(train)
        metrics = evaluate_records(model, test)
        for record in test:
            truth = outcome_from_record(record)
            if truth == OUTCOME_UNKNOWN:
                continue
            aggregate_truth_predictions.append((truth, model.predict(record).top_outcome))
        rows.append(
            {
                "family": family,
                "heldout_rows": len(test),
                "heldout_supervised_rows": sum(1 for record in test if outcome_from_record(record) != OUTCOME_UNKNOWN),
                "train_supervised_rows": supervised_train_count,
                "metrics": metrics,
            }
        )
    matrix = confusion_matrix(aggregate_truth_predictions)
    return {
        "families_evaluated": len(rows),
        "rows": rows,
        "aggregate_confusion_matrix": matrix,
        "aggregate_per_class_metrics": per_class_metrics(matrix),
    }


def ranked_family_risk(model: AdvisoryRewardModel, records: Sequence[dict[str, Any]], *, limit: int = 20) -> list[dict[str, Any]]:
    by_family: dict[str, list[RewardPrediction]] = defaultdict(list)
    observed_outcomes: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        family = group_family_from_record(record)
        prediction = model.predict(record)
        by_family[family].append(prediction)
        observed_outcomes[family][outcome_from_record(record)] += 1
    rows: list[dict[str, Any]] = []
    for family, predictions in by_family.items():
        collapse = sum(prediction.collapse_risk_probability for prediction in predictions) / len(predictions)
        reward = sum(prediction.reward_probability for prediction in predictions) / len(predictions)
        rows.append(
            {
                "family": family,
                "row_count": len(predictions),
                "mean_collapse_risk_probability": collapse,
                "mean_reward_probability": reward,
                "observed_outcomes": dict(sorted(observed_outcomes[family].items())),
            }
        )
    return sorted(rows, key=lambda row: (-row["mean_collapse_risk_probability"], -row["row_count"], row["family"]))[:limit]


def positive_vs_crowded_diagnostic(model: AdvisoryRewardModel, records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    for record in records:
        outcome = outcome_from_record(record)
        if outcome not in POSITIVE_OUTCOMES | COLLAPSE_RISK_OUTCOMES:
            continue
        prediction = model.predict(record)
        scored.append(
            {
                "outcome": outcome,
                "r": _feature_source(record).get("r", record.get("r")),
                "construction_family": _feature_source(record).get("construction_family"),
                "template_family_id": _feature_source(record).get("template_family_id"),
                "reward_probability": prediction.reward_probability,
                "collapse_risk_probability": prediction.collapse_risk_probability,
                "decision": prediction.decision,
            }
        )
    positive = [row for row in scored if row["outcome"] in POSITIVE_OUTCOMES]
    crowded = [row for row in scored if row["outcome"] == OUTCOME_CROWDED_COLLAPSE]
    collapse_risk = [row for row in scored if row["outcome"] in COLLAPSE_RISK_OUTCOMES]
    positive_mean = (
        sum(float(row["reward_probability"]) for row in positive) / len(positive)
        if positive
        else None
    )
    crowded_mean = (
        sum(float(row["reward_probability"]) for row in crowded) / len(crowded)
        if crowded
        else None
    )
    collapse_risk_mean = (
        sum(float(row["reward_probability"]) for row in collapse_risk) / len(collapse_risk)
        if collapse_risk
        else None
    )
    return {
        "score_positive_count": len(positive),
        "crowded_collapse_count": len(crowded),
        "collapse_risk_count": len(collapse_risk),
        "mean_positive_reward_probability": positive_mean,
        "mean_crowded_reward_probability": crowded_mean,
        "mean_collapse_risk_reward_probability": collapse_risk_mean,
        "positive_ranks_above_crowded_mean": (
            positive_mean is not None and crowded_mean is not None and positive_mean > crowded_mean
        ),
        "positive_ranks_above_collapse_risk_mean": (
            positive_mean is not None and collapse_risk_mean is not None and positive_mean > collapse_risk_mean
        ),
        "top_positive_rows": sorted(positive, key=lambda row: -float(row["reward_probability"]))[:10],
        "top_crowded_rows": sorted(crowded, key=lambda row: -float(row["collapse_risk_probability"]))[:10],
        "top_collapse_risk_rows": sorted(
            collapse_risk,
            key=lambda row: -float(row["collapse_risk_probability"]),
        )[:10],
    }


def build_training_artifacts(records: Sequence[dict[str, Any]], *, source_path: str | None = None) -> dict[str, Any]:
    split = grouped_split(records)
    if split["group_overlap"]:
        raise ValueError(f"group leakage detected: {split['group_overlap']}")
    train_records = [records[index] for index in split["train_indices"]]
    eval_records = [records[index] for index in split["eval_indices"]]
    model = train_reward_model(train_records)
    train_metrics = evaluate_records(model, train_records)
    eval_metrics = evaluate_records(model, eval_records)
    all_metrics = evaluate_records(model, records)
    family_replay = leave_one_family_out(records)
    family_risk = ranked_family_risk(model, records)
    positive_diagnostic = positive_vs_crowded_diagnostic(model, records)
    outcome_counts = Counter(outcome_from_record(record) for record in records)
    group_counts = Counter(group_family_from_record(record) for record in records)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "igp24_reward_model_training_manifest",
        "created_at": utc_now(),
        "model_type": MODEL_TYPE,
        "source_path": source_path,
        "source_sha256": stable_hash([record.get("canonical_hash") or record.get("dataset_row_id") for record in records]),
        "row_count": len(records),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "group_count": len(group_counts),
        "feature_keys": list(DEFAULT_FEATURE_KEYS),
        "split": {
            key: value
            for key, value in split.items()
            if key not in {"train_indices", "eval_indices"}
        }
        | {
            "train_rows": len(split["train_indices"]),
            "eval_rows": len(split["eval_indices"]),
        },
        "advisory_status": (
            "advisory_insufficient_positive_data"
            if outcome_counts.get(OUTCOME_SCORE_POSITIVE, 0) + outcome_counts.get(OUTCOME_LOW_TEAM_SCOREABLE, 0) < 20
            else "advisory"
        ),
        "limitations": [
            "This is an advisory risk/reward model, not an exact Galois-group verifier.",
            "Unknown rows are excluded from supervised training and are not treated as negative.",
            "Rows with adaptive no-valuable-target survival are supervised collapse-risk evidence, not exact labels.",
            "Positive supervision remains sparse; use uncertainty and abstention in downstream gates.",
            "Family-grouped and leave-one-family-out metrics are more meaningful than random row splits.",
        ],
    }
    return {
        "model": model,
        "manifest": manifest,
        "metrics": {
            "schema_version": SCHEMA_VERSION,
            "record_type": "igp24_reward_model_metrics",
            "created_at": utc_now(),
            "train": train_metrics,
            "eval": eval_metrics,
            "all_records": all_metrics,
            "leave_one_family_out": family_replay,
            "family_risk_ranking": family_risk,
            "positive_vs_crowded": positive_diagnostic,
        },
    }
