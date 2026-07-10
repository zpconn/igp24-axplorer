import sympy as sp

from src.igp24.constructions.eisenstein_composition import (
    build_eisenstein_power_composition,
    quartic_outer_s4_certificate,
)
from src.igp24.polynomial import construct_polynomial, real_root_count, translate_coefficients


def test_quartic_x6_composition_is_exact_r8_eisenstein_and_irreducible():
    certificate = build_eisenstein_power_composition([1, 2, 3, 4], prime=2, inner_power=6)
    polynomial = construct_polynomial(certificate.coefficients)

    assert certificate.outer_coefficients == (386, -400, 140, -20, 1)
    assert certificate.real_root_count == 8
    assert certificate.positive_outer_root_count == 4
    assert polynomial.is_irreducible is True
    assert polynomial.gcd(polynomial.diff()).degree() == 0
    assert real_root_count(certificate.coefficients) == 8
    assert all(value % 2 == 0 for value in certificate.exported_coefficients[:-1])
    assert certificate.exported_coefficients[0] % 4 == 2


def test_degree12_x2_composition_controls_high_real_root_count():
    centers = [-4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8]
    certificate = build_eisenstein_power_composition(centers, prime=2, inner_power=2)

    assert certificate.positive_outer_root_count == 8
    assert certificate.real_root_count == 16
    assert construct_polynomial(certificate.coefficients).is_irreducible is True
    assert real_root_count(certificate.coefficients) == 16


def test_quartic_outer_s4_certificate_matches_sympy_exact_group():
    certificate = build_eisenstein_power_composition([1, 2, 4, 7], prime=2, inner_power=6)
    proof = quartic_outer_s4_certificate(certificate.outer_coefficients)
    y = sp.Symbol("y")
    outer = sp.Poly(
        sum(coefficient * y**power for power, coefficient in enumerate(certificate.outer_coefficients)),
        y,
        domain=sp.ZZ,
    )
    group, _alternating = outer.galois_group()

    assert proof["proved"] is True
    assert proof["outer_galois_group"] == "S4"
    assert group.order() == 24


def test_integer_translation_matches_direct_sympy_expansion():
    certificate = build_eisenstein_power_composition([1, 2, 3, 5], prime=3, inner_power=6)
    x = sp.Symbol("x")
    polynomial = construct_polynomial(certificate.coefficients)

    for shift in range(-2, 3):
        expected = sp.Poly(sp.expand(polynomial.as_expr().subs(x, x + shift)), x, domain=sp.ZZ)
        assert translate_coefficients(certificate.coefficients, shift) == tuple(
            int(expected.nth(power)) for power in range(24)
        )
