from types import SimpleNamespace

import pytest

from src.igp24.training_readiness import (
    NAMED_ITERATION,
    SMOKE_TEST,
    TrainingReadinessThresholds,
    assess_training_readiness,
    effective_sample_size,
    enforce_training_readiness,
)


def row(index, *, split, family, target_r=8, weight=1.0, group=None):
    canonical_hash = f"{split}-{index}"
    return SimpleNamespace(
        features=canonical_hash,
        conditioning_target_r=target_r,
        generator_training_weight=weight,
        generator_training_role="exact_local_exploration",
        generator_training_split_group=group or f"{family}:group-{index}",
        source_metadata={
            "canonical_hash": canonical_hash,
            "conditioning_target_r": target_r,
            "construction_family": family,
            "generator_training": {
                "eligible": True,
                "weight": weight,
                "role": "exact_local_exploration",
                "construction_family": family,
            },
        },
    )


def test_default_gate_reclassifies_16_4_corpus_as_smoke_only():
    train = [row(index, split="train", family=f"train-family-{index % 4}") for index in range(16)]
    evaluation = [row(index, split="eval", family="eval-family") for index in range(4)]

    report = assess_training_readiness(train, evaluation, target_rs=[8])

    assert report["status"] == "smoke_only_not_model_iteration"
    assert report["train"]["unique_canonical_example_count"] == 16
    assert report["eval"]["unique_canonical_example_count"] == 4
    assert report["checks"]["unique_train_examples"] == {
        "passed": False,
        "actual": 16,
        "minimum": 1_000_000,
    }
    assert report["counting_semantics"]["repeated_sampler_draws_count"] is False
    with pytest.raises(ValueError, match="named AXG iteration blocked"):
        enforce_training_readiness(report, NAMED_ITERATION)
    enforce_training_readiness(report, SMOKE_TEST)


def test_ready_corpus_requires_unique_balanced_rows_and_disjoint_families():
    train = [
        row(index, split="train", family=f"train-family-{index % 2}", target_r=8 if index < 4 else 16)
        for index in range(8)
    ]
    evaluation = [
        row(index, split="eval", family="eval-family", target_r=8 if index < 2 else 16)
        for index in range(4)
    ]
    thresholds = TrainingReadinessThresholds(
        min_unique_train_examples=8,
        min_unique_eval_examples=4,
        min_train_effective_sample_size=8,
        min_train_split_groups=8,
        min_eval_split_groups=4,
        min_train_construction_families=2,
        min_eval_construction_families=1,
    )

    report = assess_training_readiness(train, evaluation, target_rs=[8, 16], thresholds=thresholds)

    assert report["ready_for_named_iteration"] is True
    assert report["per_r_requirements"]["8"]["train"]["actual"] == 4
    assert report["per_r_requirements"]["16"]["eval"]["actual"] == 2
    enforce_training_readiness(report, NAMED_ITERATION)


def test_gate_detects_hash_group_and_family_leakage():
    train = [row(0, split="shared", family="shared-family", group="shared-group")]
    evaluation = [row(0, split="shared", family="shared-family", group="shared-group")]
    thresholds = TrainingReadinessThresholds(
        min_unique_train_examples=1,
        min_unique_eval_examples=1,
        min_train_effective_sample_size=1,
        min_train_split_groups=1,
        min_eval_split_groups=1,
        min_train_construction_families=1,
        min_eval_construction_families=1,
    )

    report = assess_training_readiness(train, evaluation, target_rs=[8], thresholds=thresholds)

    assert report["checks"]["train_eval_hash_disjoint"]["passed"] is False
    assert report["checks"]["train_eval_split_group_disjoint"]["passed"] is False
    assert report["checks"]["train_eval_construction_family_disjoint"]["passed"] is False
    assert report["ready_for_named_iteration"] is False


def test_effective_sample_size_penalizes_repeated_weight_concentration():
    assert effective_sample_size([1.0] * 10) == pytest.approx(10.0)
    assert effective_sample_size([100.0] + [1.0] * 9) < 2.0
