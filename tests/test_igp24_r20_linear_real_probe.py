from scripts.igp24_r20_linear_real_probe import (
    DECOMPOSITION_PATTERN,
    candidate_family_key,
    coefficients_from_trial,
    linear_real_product_coefficients,
    support_profile,
)
from src.igp24.polynomial import DEGREE, coefficient_height, score_candidate


def _trial():
    roots = tuple(list(range(-10, 0)) + list(range(1, 10)) + [11])
    no_real = (1, 2)
    return {
        "mode": "single_low_coefficient_break",
        "real_roots": roots,
        "no_real_quadratics": no_real,
        "base_coefficients": linear_real_product_coefficients(roots, no_real),
        "coefficient_perturbations": ((1, 1),),
    }


def test_r20_linear_real_product_builds_degree24_non_even_support():
    coeffs, metadata = coefficients_from_trial(_trial())
    profile = support_profile(coeffs)

    assert len(coeffs) == DEGREE
    assert coeffs[0] != 0
    assert metadata["construction_family"].startswith("twenty_linear_real_roots")
    assert metadata["decomposition_degree_pattern"] == DECOMPOSITION_PATTERN
    assert metadata["target_r_heuristic"] == 20
    assert metadata["r20_linear_base_real_root_count"] == 20
    assert metadata["r20_linear_family_key"] == candidate_family_key({"generation_metadata": metadata})
    assert profile["support_gcd"] == 1
    assert profile["even_support"] is False


def test_r20_linear_real_known_small_perturbation_is_exact_local_r20():
    coeffs, metadata = coefficients_from_trial(_trial())

    score, analysis = score_candidate(
        coeffs,
        coeff_bound=10**16,
        target_r=20,
        prime_limit=7,
        exact_score_timeout=5,
        seen_hashes=set(),
    )

    assert coefficient_height(coeffs) <= 10**16
    assert analysis.valid is True
    assert analysis.real_root_count == 20
    assert analysis.irreducible is True
    assert analysis.squarefree is True
    assert analysis.rejection_reason is None
    assert analysis.canonical_hash
    assert metadata["r20_linear_mode"] == "single_low_coefficient_break"
    assert score >= 0
