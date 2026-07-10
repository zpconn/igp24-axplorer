from __future__ import annotations

from src.igp24.constructions.eisenstein_composition import (
    build_eisenstein_power_composition,
    polynomial_from_integer_roots,
)
from src.igp24.adaptive_frobenius import unramified_factorization_degrees_mod_prime
from src.igp24.model_projection import (
    ProjectionFamily,
    deterministic_baseline_centers,
    deterministic_projection_jitter,
    outer_coefficients_from_power_composition,
    project_outer_roots_to_family,
    project_strictly_increasing_integers,
)


def test_extract_outer_coefficients_from_exact_power_composition() -> None:
    certificate = build_eisenstein_power_composition(range(1, 13), prime=2, inner_power=2)
    assert outer_coefficients_from_power_composition(certificate.coefficients, inner_power=2) == certificate.outer_coefficients
    assert (
        outer_coefficients_from_power_composition(certificate.exported_coefficients, inner_power=2)
        == certificate.outer_coefficients
    )


def test_integer_projection_is_bounded_strict_and_least_squares() -> None:
    projected = project_strictly_increasing_integers([1.1, 1.2, 4.8], minimum=1, maximum=5)
    assert projected == (1, 2, 5)


def test_outer_root_projection_recovers_exact_integer_root_shape() -> None:
    family = ProjectionFamily("test", prime=2, center_start=1, center_count=32)
    exact_centers = tuple(range(3, 15))
    exact_outer = polynomial_from_integer_roots(2 * center for center in exact_centers)
    projection = project_outer_roots_to_family(exact_outer, family)
    assert projection.centers == exact_centers
    assert projection.normalized_projection_error < 1e-4


def test_projected_centers_build_an_exact_r24_certificate() -> None:
    family = ProjectionFamily("test", prime=3, center_start=1, center_count=72)
    source = build_eisenstein_power_composition(range(2, 14), prime=3, inner_power=2)
    projection = project_outer_roots_to_family(source.outer_coefficients, family)
    rebuilt = build_eisenstein_power_composition(projection.centers, prime=family.prime, inner_power=2)
    assert rebuilt.real_root_count == 24
    assert len(set(projection.centers)) == 12
    assert min(projection.centers) >= family.center_start
    assert max(projection.centers) <= family.center_stop


def test_deterministic_proposal_controls_are_reproducible() -> None:
    family = ProjectionFamily("test", prime=2, center_start=1, center_count=72)
    assert deterministic_projection_jitter("abc", family.family_id, 2, 12) == deterministic_projection_jitter(
        "abc", family.family_id, 2, 12
    )
    centers = deterministic_baseline_centers("abc", family, variant=2)
    assert centers == deterministic_baseline_centers("abc", family, variant=2)
    assert len(centers) == len(set(centers)) == 12


def test_modular_factorization_explicitly_rejects_ramified_prime() -> None:
    certificate = build_eisenstein_power_composition(range(1, 13), prime=2, inner_power=2)
    assert unramified_factorization_degrees_mod_prime(certificate.coefficients, 2) is None
    assert sum(unramified_factorization_degrees_mod_prime(certificate.coefficients, 3) or ()) == 24
