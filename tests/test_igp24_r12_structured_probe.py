import math
import random

import pytest

pytest.importorskip("sympy")

from scripts.igp24_r12_structured_probe import (
    base_polynomial_coefficients_y,
    candidate_family_key,
    coefficient_line,
    coefficients_from_trial,
    lift_base_to_degree24,
    negative_base_root_layouts,
    positive_base_root_layouts,
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


def test_r12_exact_composed_seed_has_twelve_real_roots_and_export_format():
    positives = tuple(range(1, 7))
    negatives = tuple(range(1, 7))
    base = base_polynomial_coefficients_y(positives, negatives)
    coeffs = lift_base_to_degree24(base)
    exported = export_coefficients(coeffs)

    assert len(base) == 13
    assert len(coeffs) == DEGREE
    assert exported[-1] == 1
    assert len(coefficient_line(exported).split(",")) == DEGREE + 1
    assert math.gcd(*[abs(value) for value in exported]) == 1
    assert coefficient_height(coeffs) == 773136
    assert real_root_count(coeffs) == 12
    assert not is_irreducible_over_q(coeffs)
    assert is_squarefree(coeffs)
    assert all(index % 2 == 0 for index, coeff in enumerate(coeffs) if coeff != 0)


def test_r12_base_perturbation_is_known_valid_local_template():
    positives = tuple(range(1, 7))
    negatives = tuple(range(1, 7))
    base = base_polynomial_coefficients_y(positives, negatives)
    coeffs, metadata = coefficients_from_trial(
        {
            "mode": "single_base_coefficient_perturbation",
            "positive_base_roots": positives,
            "negative_base_roots": negatives,
            "base_coefficients_y": base,
            "base_perturbations": [(0, 1)],
        }
    )

    score, analysis = score_candidate(
        coeffs,
        coeff_bound=5_000_000,
        target_r=12,
        prime_limit=7,
        exact_score_timeout=5.0,
    )

    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 12
    assert analysis.irreducible
    assert analysis.squarefree
    assert all(index % 2 == 0 for index, coeff in enumerate(coeffs) if coeff != 0)
    assert metadata["strategy"] == "r12_exact_composed_base_perturbation_probe"
    assert metadata["construction_family"] == "degree12_base_six_positive_roots_lifted_by_x2"
    assert metadata["target_r_heuristic"] == 12
    assert metadata["composed_support"] is True
    assert metadata["exact_composed_support_divisor"] == 2
    assert metadata["r12_structured_base_perturbations"] == [{"y_exponent": 0, "delta": 1}]
    assert candidate_family_key({"generation_metadata": metadata}).endswith("|y=0")


def test_r12_trial_variants_are_deterministic_and_record_structure():
    first = list(trial_variants(rng=random.Random(1212), max_trials=5))
    second = list(trial_variants(rng=random.Random(1212), max_trials=5))

    assert first == second
    assert len(first) == 5
    assert positive_base_root_layouts()[0] == tuple(range(1, 7))
    assert negative_base_root_layouts()[0] == tuple(range(1, 7))
    for trial in first:
        coeffs, metadata = coefficients_from_trial(trial)
        assert len(coeffs) == DEGREE
        assert coeffs[0] != 0
        assert metadata["r12_structured_mode"] in {
            "single_base_coefficient_perturbation",
            "structured_base_coefficient_perturbation",
        }
        assert metadata["r12_structured_base_positive_real_roots"] == 6
        assert metadata["r12_structured_base_negative_real_roots"] == 6
        assert metadata["r12_structured_lift"] == "x_squared"
        assert metadata["r12_structured_exact_composed_support_divisor"] == 2
        assert metadata["r12_structured_perturbation_terms"] >= 1
        assert metadata["r12_structured_family_key"] == candidate_family_key({"generation_metadata": metadata})
