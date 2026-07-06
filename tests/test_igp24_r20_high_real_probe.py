import random

import pytest

pytest.importorskip("sympy")

from scripts.igp24_r20_high_real_probe import (
    candidate_family_key,
    coefficient_line,
    coefficients_from_trial,
    mixed_quadratic_product_coefficients,
    negative_quadratic_layouts,
    positive_quadratic_root_layouts,
    trial_variants,
)
from src.igp24.polynomial import (
    DEGREE,
    coefficient_height,
    export_coefficients,
    is_irreducible_over_q,
    is_squarefree,
    real_root_count,
    score_candidate,
)


def test_r20_mixed_quadratic_seed_has_twenty_real_roots_and_export_format():
    positives = tuple(range(1, 11))
    negatives = (1, 2)
    coeffs = mixed_quadratic_product_coefficients(positives, negatives)

    assert len(coeffs) == DEGREE
    assert export_coefficients(coeffs)[-1] == 1
    assert len(coefficient_line(export_coefficients(coeffs)).split(",")) == DEGREE + 1
    assert coefficient_height(coeffs) == 10813088
    assert real_root_count(coeffs) == 20
    assert not is_irreducible_over_q(coeffs)
    assert is_squarefree(coeffs)


def test_r20_low_odd_perturbation_is_known_valid_local_template():
    positives = tuple(range(1, 11))
    negatives = (1, 2)
    base = mixed_quadratic_product_coefficients(positives, negatives)
    coeffs, metadata = coefficients_from_trial(
        {
            "mode": "single_low_odd_break",
            "positive_quadratic_roots": positives,
            "negative_quadratic_roots": negatives,
            "base_coefficients": base,
            "odd_perturbations": [(1, 1)],
        }
    )

    score, analysis = score_candidate(
        coeffs,
        coeff_bound=100_000_000,
        target_r=20,
        prime_limit=7,
        exact_score_timeout=5.0,
    )

    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 20
    assert analysis.irreducible
    assert analysis.squarefree
    assert metadata["strategy"] == "r20_high_real_mixed_quadratic_product_probe"
    assert metadata["construction_family"] == "ten_positive_two_negative_quadratic_product_plus_low_odd_perturbation"
    assert metadata["target_r_heuristic"] == 20
    assert metadata["r20_high_real_odd_perturbations"] == [{"x_exponent": 1, "delta": 1}]
    assert candidate_family_key({"generation_metadata": metadata}).endswith("|odd=1")


def test_r20_trial_variants_are_deterministic_and_record_structure():
    first = list(trial_variants(rng=random.Random(2020), max_trials=5))
    second = list(trial_variants(rng=random.Random(2020), max_trials=5))

    assert first == second
    assert len(first) == 5
    assert positive_quadratic_root_layouts()[0] == tuple(range(1, 11))
    assert negative_quadratic_layouts()[0] == (1, 2)
    for trial in first:
        coeffs, metadata = coefficients_from_trial(trial)
        assert len(coeffs) == DEGREE
        assert coeffs[0] != 0
        assert metadata["r20_high_real_mode"] in {
            "single_low_odd_break",
            "two_low_odd_break",
            "three_low_odd_break",
        }
        assert metadata["r20_high_real_base_real_root_count"] == 20
        assert metadata["r20_high_real_base_is_reducible"] is True
        assert len(metadata["r20_high_real_positive_quadratic_roots"]) == 10
        assert len(metadata["r20_high_real_negative_quadratic_roots"]) == 2
        assert metadata["r20_high_real_perturbation_terms"] >= 1
        assert metadata["r20_high_real_family_key"] == candidate_family_key({"generation_metadata": metadata})
