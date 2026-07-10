"""Hard corpus-readiness checks for named IGP24 AXG model iterations.

The checks operate on the rows that survived the real JSONL loader.  Counts
therefore reflect eligibility filtering, coefficient/r filters, caps,
canonical-hash deduplication, and grouped train/evaluation assignment rather
than raw JSONL line counts or repeated sampler draws.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


NAMED_ITERATION = "named_iteration"
SMOKE_TEST = "smoke_test"


@dataclass(frozen=True)
class TrainingReadinessThresholds:
    """Minimum evidence required before a run may be called an AXG iteration."""

    min_unique_train_examples: int = 1_000_000
    min_unique_eval_examples: int = 100_000
    min_train_effective_sample_size: int = 500_000
    min_train_split_groups: int = 32
    min_eval_split_groups: int = 8
    min_train_construction_families: int = 4
    min_eval_construction_families: int = 1


def _metadata(row: Any) -> dict[str, Any]:
    value = getattr(row, "source_metadata", None)
    return value if isinstance(value, dict) else {}


def _contract(row: Any) -> dict[str, Any]:
    value = _metadata(row).get("generator_training")
    return value if isinstance(value, dict) else {}


def _identity(row: Any) -> str | None:
    metadata = _metadata(row)
    canonical_hash = metadata.get("canonical_hash")
    if canonical_hash not in (None, ""):
        return str(canonical_hash)
    features = getattr(row, "features", None)
    if features not in (None, ""):
        return str(features)
    return None


def _split_group(row: Any) -> str | None:
    value = getattr(row, "generator_training_split_group", None)
    return None if value in (None, "") else str(value)


def _construction_family(row: Any) -> str | None:
    contract = _contract(row)
    value = contract.get("construction_family")
    if value not in (None, ""):
        return str(value)
    metadata = _metadata(row)
    value = metadata.get("construction_family")
    if value not in (None, ""):
        return str(value)
    return None


def _conditioning_r(row: Any) -> int | None:
    value = getattr(row, "conditioning_target_r", None)
    if value is None:
        value = _metadata(row).get("conditioning_target_r")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _conditioning_inner_power(row: Any) -> int | None:
    value = getattr(row, "conditioning_inner_power", None)
    if value is None:
        value = _metadata(row).get("conditioning_inner_power")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def effective_sample_size(weights: Iterable[float]) -> float:
    positive = [float(weight) for weight in weights if float(weight) > 0.0]
    if not positive:
        return 0.0
    total = sum(positive)
    squared = sum(weight * weight for weight in positive)
    return (total * total) / squared if squared else 0.0


def _distribution(rows: Sequence[Any]) -> dict[str, Any]:
    identities = [_identity(row) for row in rows]
    explicit_identities = [identity for identity in identities if identity]
    groups = {_split_group(row) for row in rows} - {None}
    families = {_construction_family(row) for row in rows} - {None}
    roles = Counter(str(getattr(row, "generator_training_role", "unknown")) for row in rows)
    r_counts = Counter(_conditioning_r(row) for row in rows)
    inner_power_counts = Counter(_conditioning_inner_power(row) for row in rows)
    weights = [float(getattr(row, "generator_training_weight", 1.0)) for row in rows]
    return {
        "physical_row_count": len(rows),
        "unique_canonical_example_count": len(set(explicit_identities)),
        "rows_missing_canonical_identity": len(rows) - len(explicit_identities),
        "duplicate_canonical_identity_count": len(explicit_identities) - len(set(explicit_identities)),
        "effective_sample_size": effective_sample_size(weights),
        "positive_sampling_mass": sum(weight for weight in weights if weight > 0.0),
        "split_group_count": len(groups),
        "construction_family_count": len(families),
        "split_group_examples": sorted(groups)[:100],
        "construction_families": sorted(families),
        "role_counts": dict(sorted(roles.items())),
        "conditioning_r_counts": {
            str(key) if key is not None else "unknown": value
            for key, value in sorted(r_counts.items(), key=lambda item: (-1 if item[0] is None else item[0]))
        },
        "conditioning_inner_power_counts": {
            str(key) if key is not None else "unknown": value
            for key, value in sorted(inner_power_counts.items(), key=lambda item: (-1 if item[0] is None else item[0]))
        },
        "_canonical_identities": set(explicit_identities),
        "_split_groups": groups,
        "_construction_families": families,
    }


def _check(actual: int | float, minimum: int | float) -> dict[str, Any]:
    return {
        "passed": actual >= minimum,
        "actual": actual,
        "minimum": minimum,
    }


def assess_training_readiness(
    train_rows: Sequence[Any],
    eval_rows: Sequence[Any],
    *,
    target_rs: Iterable[int] = (),
    thresholds: TrainingReadinessThresholds | None = None,
) -> dict[str, Any]:
    """Assess the actual post-loader corpus for a named AXG iteration."""

    thresholds = thresholds or TrainingReadinessThresholds()
    requested_rs = tuple(sorted({int(value) for value in target_rs}))
    train = _distribution(train_rows)
    evaluation = _distribution(eval_rows)

    train_identities = train.pop("_canonical_identities")
    eval_identities = evaluation.pop("_canonical_identities")
    train_groups = train.pop("_split_groups")
    eval_groups = evaluation.pop("_split_groups")
    train_families = train.pop("_construction_families")
    eval_families = evaluation.pop("_construction_families")

    checks: dict[str, dict[str, Any]] = {
        "unique_train_examples": _check(
            train["unique_canonical_example_count"], thresholds.min_unique_train_examples
        ),
        "unique_eval_examples": _check(
            evaluation["unique_canonical_example_count"], thresholds.min_unique_eval_examples
        ),
        "train_effective_sample_size": _check(
            train["effective_sample_size"], thresholds.min_train_effective_sample_size
        ),
        "train_split_groups": _check(train["split_group_count"], thresholds.min_train_split_groups),
        "eval_split_groups": _check(evaluation["split_group_count"], thresholds.min_eval_split_groups),
        "train_construction_families": _check(
            train["construction_family_count"], thresholds.min_train_construction_families
        ),
        "eval_construction_families": _check(
            evaluation["construction_family_count"], thresholds.min_eval_construction_families
        ),
        "train_rows_have_canonical_identity": {
            "passed": train["rows_missing_canonical_identity"] == 0,
            "actual_missing": train["rows_missing_canonical_identity"],
            "maximum_missing": 0,
        },
        "eval_rows_have_canonical_identity": {
            "passed": evaluation["rows_missing_canonical_identity"] == 0,
            "actual_missing": evaluation["rows_missing_canonical_identity"],
            "maximum_missing": 0,
        },
        "train_canonical_deduplicated": {
            "passed": train["duplicate_canonical_identity_count"] == 0,
            "actual_duplicates": train["duplicate_canonical_identity_count"],
            "maximum_duplicates": 0,
        },
        "eval_canonical_deduplicated": {
            "passed": evaluation["duplicate_canonical_identity_count"] == 0,
            "actual_duplicates": evaluation["duplicate_canonical_identity_count"],
            "maximum_duplicates": 0,
        },
        "train_eval_hash_disjoint": {
            "passed": not (train_identities & eval_identities),
            "overlap_count": len(train_identities & eval_identities),
            "overlap_examples": sorted(train_identities & eval_identities)[:20],
        },
        "train_eval_split_group_disjoint": {
            "passed": not (train_groups & eval_groups),
            "overlap_count": len(train_groups & eval_groups),
            "overlap_examples": sorted(train_groups & eval_groups)[:20],
        },
        "train_eval_construction_family_disjoint": {
            "passed": not (train_families & eval_families),
            "overlap_count": len(train_families & eval_families),
            "overlap_examples": sorted(train_families & eval_families)[:20],
        },
    }

    per_r_requirements: dict[str, Any] = {}
    if requested_rs:
        min_train_per_r = math.ceil(thresholds.min_unique_train_examples / len(requested_rs))
        min_eval_per_r = math.ceil(thresholds.min_unique_eval_examples / len(requested_rs))
        train_r_counts = train["conditioning_r_counts"]
        eval_r_counts = evaluation["conditioning_r_counts"]
        for target_r in requested_rs:
            train_check = _check(int(train_r_counts.get(str(target_r), 0)), min_train_per_r)
            eval_check = _check(int(eval_r_counts.get(str(target_r), 0)), min_eval_per_r)
            checks[f"train_examples_r{target_r}"] = train_check
            checks[f"eval_examples_r{target_r}"] = eval_check
            per_r_requirements[str(target_r)] = {
                "train": train_check,
                "eval": eval_check,
            }

    failed_checks = sorted(name for name, result in checks.items() if not result["passed"])
    ready = not failed_checks
    return {
        "schema_version": "igp24_training_readiness_v1",
        "status": "ready_for_named_iteration" if ready else "smoke_only_not_model_iteration",
        "ready_for_named_iteration": ready,
        "counting_semantics": {
            "training_examples": "unique canonical generator-eligible rows after loader filters and holdout",
            "repeated_sampler_draws_count": False,
            "epochs_count_as_new_examples": False,
            "augmented_duplicates_count": False,
            "evaluation_is_separate": True,
        },
        "thresholds": asdict(thresholds),
        "requested_conditioning_rs": list(requested_rs),
        "per_r_requirements": per_r_requirements,
        "train": train,
        "eval": evaluation,
        "checks": checks,
        "failed_checks": failed_checks,
    }


def enforce_training_readiness(report: dict[str, Any], run_kind: str) -> None:
    if run_kind not in {NAMED_ITERATION, SMOKE_TEST}:
        raise ValueError(f"unsupported IGP24 training run kind: {run_kind}")
    if run_kind == NAMED_ITERATION and not report.get("ready_for_named_iteration"):
        failed = ", ".join(report.get("failed_checks") or ["unknown_readiness_failure"])
        raise ValueError(
            "IGP24 named AXG iteration blocked by corpus-readiness gate: "
            f"{failed}. Use smoke_test only for explicitly labeled plumbing probes."
        )


def add_training_schedule_readiness(
    report: dict[str, Any],
    *,
    sampling_mode: str,
    batch_size: int,
    max_steps: int,
) -> dict[str, Any]:
    """Require one complete unique-corpus traversal for a named iteration."""

    unique_train = int((report.get("train") or {}).get("unique_canonical_example_count") or 0)
    presentations = int(batch_size) * int(max_steps)
    check = {
        "passed": sampling_mode == "epoch_shuffle" and presentations >= unique_train,
        "sampling_mode": str(sampling_mode),
        "batch_size": int(batch_size),
        "max_steps": int(max_steps),
        "scheduled_presentations": presentations,
        "minimum_unique_train_examples_to_traverse": unique_train,
        "requires_without_replacement_epoch_shuffle": True,
    }
    report["training_schedule"] = check
    report.setdefault("checks", {})["complete_unique_corpus_traversal"] = check
    failed = sorted(name for name, result in report["checks"].items() if not result["passed"])
    report["failed_checks"] = failed
    ready = not failed
    report["ready_for_named_iteration"] = ready
    report["status"] = "ready_for_named_iteration" if ready else "smoke_only_not_model_iteration"
    return report


def write_training_readiness_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
