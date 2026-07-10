"""Exact structural helpers for quartic-in-``x^6`` descent searches.

For ``f(x) = h(x^6)`` with monic quartic ``h``, the splitting field of
``f`` maps onto the splitting field of ``h``.  This makes the exact Galois
group of the outer quartic a useful construction invariant: it is stronger
than coefficient-shape similarity while remaining much cheaper than a
degree-24 exact Galois-group computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

import sympy as sp

from src.igp24.constructions.generators import lift_base_to_degree24_by_power


TARGET_9993_LABEL = "24T9993"
TARGET_9993_PAIR = "24T9993|r=8"
TARGET_9993_OUTER_ACTION = {
    "block_size": 6,
    "block_count": 4,
    "induced_action_transitive_id": "4T5",
    "induced_action_order": 24,
    "induced_action_name": "S4",
    "soundness": "exact_gap_target_invariant_and_exact_outer_quartic_quotient",
}


@dataclass(frozen=True, order=True)
class QuarticX6Parameters:
    """Monic quartic ``y^4 + a*y^3 + b*y^2 + c*y + d`` parameters."""

    a: int
    b: int
    c: int
    d: int = 1

    @property
    def ascending_coefficients(self) -> tuple[int, int, int, int, int]:
        return (self.d, self.c, self.b, self.a, 1)

    @property
    def reciprocal(self) -> "QuarticX6Parameters":
        if self.d != 1:
            raise ValueError("reciprocal monic normalization currently requires d=1")
        return QuarticX6Parameters(a=self.c, b=self.b, c=self.a, d=1)

    @property
    def reciprocal_key(self) -> tuple[int, int, int, int]:
        if self.d != 1:
            return (self.a, self.b, self.c, self.d)
        return min(
            (self.a, self.b, self.c, self.d),
            (self.c, self.b, self.a, self.d),
        )


def quartic_discriminant(parameters: QuarticX6Parameters) -> int:
    """Return the exact discriminant of the monic outer quartic."""

    a, b, c, d = parameters.a, parameters.b, parameters.c, parameters.d
    return int(
        256 * d**3
        - 192 * a * c * d**2
        - 128 * b**2 * d**2
        + 144 * b * c**2 * d**2
        - 27 * c**4
        + 144 * a**2 * b * d**2
        - 6 * a**2 * c**2 * d
        - 80 * a * b**2 * c * d
        + 18 * a * b * c**3
        + 16 * b**4 * d
        - 4 * b**3 * c**2
        - 27 * a**4 * d**2
        + 18 * a**3 * b * c * d
        - 4 * a**3 * c**3
        - 4 * a**2 * b**3 * d
        + a**2 * b**2 * c**2
    )


def quartic_x6_polynomial_discriminant_abs(parameters: QuarticX6Parameters) -> int:
    """Return ``abs(Disc(h(x^6)))`` from the exact composition formula."""

    outer_disc = abs(quartic_discriminant(parameters))
    return int(6**24 * abs(parameters.d) ** 5 * outer_disc**6)


def quartic_poly(parameters: QuarticX6Parameters) -> sp.Poly:
    y = sp.Symbol("y")
    return sp.Poly(
        y**4 + parameters.a * y**3 + parameters.b * y**2 + parameters.c * y + parameters.d,
        y,
        domain=sp.ZZ,
    )


def positive_real_root_count(parameters: QuarticX6Parameters) -> int:
    """Count positive outer roots exactly with a Sturm-sequence computation."""

    return int(quartic_poly(parameters).count_roots(0, sp.oo))


def outer_galois_profile(parameters: QuarticX6Parameters) -> dict[str, object]:
    """Return exact degree-4 Galois evidence used by the structured route."""

    polynomial = quartic_poly(parameters)
    irreducible = bool(polynomial.is_irreducible)
    if not irreducible:
        return {
            "outer_irreducible": False,
            "outer_galois_group_order": None,
            "outer_galois_group_name": None,
            "outer_action_matches_24T9993": False,
            "evidence_status": "outer_quartic_reducible",
        }
    group, alternating = polynomial.galois_group()
    order = int(group.order())
    name = "S4" if order == 24 else "D4" if order == 8 else "C4_or_V4" if order == 4 else f"order_{order}"
    return {
        "outer_irreducible": True,
        "outer_galois_group_order": order,
        "outer_galois_group_name": name,
        "outer_galois_group_in_alternating": bool(alternating),
        "outer_action_matches_24T9993": order == 24,
        "target_outer_action": dict(TARGET_9993_OUTER_ACTION),
        "evidence_status": "exact_outer_quartic_galois_group",
    }


def lift_quartic_x6(parameters: QuarticX6Parameters) -> list[int]:
    """Return ascending ``a_0..a_23`` coefficients for monic ``h(x^6)``."""

    return lift_base_to_degree24_by_power(parameters.ascending_coefficients, 6)


def iter_alternating_sign_grid(
    *,
    a_abs_min: int,
    a_abs_max: int,
    b_min: int,
    b_max: int,
    c_abs_min: int,
    c_abs_max: int,
    d: int = 1,
    maximum_quartic_discriminant: int | None = None,
    deduplicate_reciprocals: bool = True,
) -> Iterator[QuarticX6Parameters]:
    """Yield a deterministic exact coefficient grid for four-positive-root quartics.

    Alternating coefficient signs are necessary, but not sufficient, for four
    positive roots.  Callers must still run :func:`positive_real_root_count`.
    """

    if min(a_abs_min, b_min, c_abs_min, d) <= 0:
        raise ValueError("alternating-sign grid bounds and d must be positive")
    rows: list[tuple[int, QuarticX6Parameters]] = []
    seen_reciprocals: set[tuple[int, int, int, int]] = set()
    for a_abs in range(int(a_abs_min), int(a_abs_max) + 1):
        for b in range(int(b_min), int(b_max) + 1):
            for c_abs in range(int(c_abs_min), int(c_abs_max) + 1):
                parameters = QuarticX6Parameters(a=-a_abs, b=b, c=-c_abs, d=d)
                outer_disc = quartic_discriminant(parameters)
                if outer_disc <= 0:
                    continue
                if maximum_quartic_discriminant is not None and outer_disc > int(maximum_quartic_discriminant):
                    continue
                if deduplicate_reciprocals:
                    key = parameters.reciprocal_key
                    if key in seen_reciprocals:
                        continue
                    seen_reciprocals.add(key)
                rows.append((outer_disc, parameters))
    for _outer_disc, parameters in sorted(rows):
        yield parameters


def coefficient_support(coefficients: Sequence[int]) -> tuple[int, ...]:
    return tuple(index for index, value in enumerate(coefficients) if int(value) != 0)


def is_exact_quartic_x6_support(coefficients: Iterable[int]) -> bool:
    values = tuple(int(value) for value in coefficients)
    if len(values) == 25:
        values = values[:-1]
    if len(values) != 24:
        return False
    return all(value == 0 or exponent in {0, 6, 12, 18} for exponent, value in enumerate(values))
