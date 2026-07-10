"""Scalable exact composition families for degree-24 AXG pretraining.

The core family is

``f(x) = h(x**m)``, where ``deg(h) * m = 24`` and
``h(y) = product(y - p*c_i) + p``.

For distinct nonzero integer centers ``c_i`` and prime ``p``, every
non-leading coefficient of both ``h`` and ``f`` is divisible by ``p`` while
the constant coefficient is not divisible by ``p**2``.  Eisenstein therefore
proves irreducibility over Q.  When the centers are paired by sign and each
negative-sign interval has an exact midpoint witness, ``h`` has one pair of
real roots in every such interval.  This proves the intended real-root count
for ``f`` without a numerical root finder.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from src.igp24.adaptive_frobenius import small_primes
from src.igp24.constructions.quartic_x6_descent import QuarticX6Parameters, quartic_discriminant
from src.igp24.polynomial import DEGREE, export_coefficients, stable_canonical_hash


def multiply_ascending(left: Sequence[int], right: Sequence[int]) -> tuple[int, ...]:
    output = [0] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            output[left_index + right_index] += int(left_value) * int(right_value)
    return tuple(output)


def polynomial_from_integer_roots(roots: Iterable[int]) -> tuple[int, ...]:
    coefficients: tuple[int, ...] = (1,)
    for root in roots:
        coefficients = multiply_ascending(coefficients, (-int(root), 1))
    return coefficients


def evaluate_ascending(coefficients: Sequence[int], numerator: int, denominator: int = 1) -> int:
    """Return ``denominator**degree * f(numerator / denominator)`` exactly."""

    degree = len(coefficients) - 1
    return sum(
        int(coefficient) * numerator**power * denominator ** (degree - power)
        for power, coefficient in enumerate(coefficients)
    )


@dataclass(frozen=True)
class EisensteinCompositionCertificate:
    prime: int
    outer_degree: int
    inner_power: int
    positive_outer_root_count: int
    real_root_count: int
    interval_witness_numerators: tuple[int, ...]
    outer_coefficients: tuple[int, ...]
    coefficients: tuple[int, ...]

    @property
    def exported_coefficients(self) -> tuple[int, ...]:
        return tuple(export_coefficients(self.coefficients))

    @property
    def canonical_hash(self) -> str:
        return stable_canonical_hash(self.coefficients)

    @property
    def certificate_id(self) -> str:
        payload = {
            "prime": self.prime,
            "outer_degree": self.outer_degree,
            "inner_power": self.inner_power,
            "centers_proof": "paired_integer_centers_midpoint_ivt",
            "irreducibility_proof": "eisenstein",
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _validate_eisenstein(coefficients: Sequence[int], prime: int) -> None:
    if int(coefficients[-1]) != 1:
        raise ValueError("composition_not_monic")
    if any(int(value) % prime for value in coefficients[:-1]):
        raise ValueError("nonleading_coefficient_not_divisible_by_eisenstein_prime")
    if int(coefficients[0]) % (prime * prime) == 0:
        raise ValueError("constant_divisible_by_eisenstein_prime_square")


def build_eisenstein_power_composition(
    centers: Sequence[int],
    *,
    prime: int,
    inner_power: int,
) -> EisensteinCompositionCertificate:
    """Build and exactly certify ``(prod(y-p*c_i)+p)(x**m)``.

    The current scalable corpus uses even outer degree and even inner power.
    Centers must sort into same-sign pairs so the perturbation cannot move a
    certified root pair across zero.
    """

    normalized_centers = tuple(sorted(int(center) for center in centers))
    outer_degree = len(normalized_centers)
    if outer_degree <= 0 or outer_degree % 2:
        raise ValueError("outer_degree_must_be_positive_and_even")
    if inner_power <= 0 or outer_degree * int(inner_power) != DEGREE:
        raise ValueError("outer_degree_times_inner_power_must_equal_24")
    if int(inner_power) % 2:
        raise ValueError("scalable_root_certificate_currently_requires_even_inner_power")
    if len(set(normalized_centers)) != outer_degree or 0 in normalized_centers:
        raise ValueError("centers_must_be_distinct_and_nonzero")
    if int(prime) < 2 or any(int(prime) % divisor == 0 for divisor in range(2, math.isqrt(int(prime)) + 1)):
        raise ValueError("eisenstein_prime_must_be_prime")

    scaled_roots = tuple(int(prime) * center for center in normalized_centers)
    base_outer = polynomial_from_integer_roots(scaled_roots)
    outer = (base_outer[0] + int(prime),) + base_outer[1:]
    _validate_eisenstein(outer, int(prime))

    positive_outer_roots = 0
    witnesses: list[int] = []
    denominator = 2
    perturbation_scaled = int(prime) * denominator**outer_degree
    for index in range(0, outer_degree, 2):
        left = scaled_roots[index]
        right = scaled_roots[index + 1]
        if left < 0 < right:
            raise ValueError("paired_root_interval_crosses_zero")
        midpoint_numerator = left + right
        base_value_scaled = evaluate_ascending(base_outer, midpoint_numerator, denominator)
        if base_value_scaled + perturbation_scaled >= 0:
            raise ValueError("midpoint_does_not_certify_two_real_roots")
        witnesses.append(midpoint_numerator)
        if left > 0:
            positive_outer_roots += 2

    free_coefficients = [0] * DEGREE
    for outer_power, coefficient in enumerate(outer[:-1]):
        free_coefficients[outer_power * int(inner_power)] = int(coefficient)
    full = tuple(free_coefficients) + (1,)
    _validate_eisenstein(full, int(prime))
    real_root_count = 2 * positive_outer_roots
    return EisensteinCompositionCertificate(
        prime=int(prime),
        outer_degree=outer_degree,
        inner_power=int(inner_power),
        positive_outer_root_count=positive_outer_roots,
        real_root_count=real_root_count,
        interval_witness_numerators=tuple(witnesses),
        outer_coefficients=outer,
        coefficients=tuple(free_coefficients),
    )


def quartic_outer_s4_certificate(
    outer_coefficients: Sequence[int],
    *,
    maximum_prime: int = 43,
) -> dict[str, object]:
    """Prove an irreducible quartic outer action is S4 when possible.

    Eisenstein supplies transitivity. A squarefree modular factorization with
    exactly one linear factor supplies a 3-cycle, narrowing the transitive
    group to A4 or S4. A nonsquare discriminant then rules out A4.
    """

    if len(outer_coefficients) != 5 or int(outer_coefficients[-1]) != 1:
        raise ValueError("outer_quartic_coefficients_required")
    d, c, b, a, _leading = (int(value) for value in outer_coefficients)
    discriminant = quartic_discriminant(QuarticX6Parameters(a=a, b=b, c=c, d=d))
    discriminant_abs = abs(int(discriminant))
    nonsquare = math.isqrt(discriminant_abs) ** 2 != discriminant_abs
    witness = None
    if nonsquare and discriminant:
        for prime in small_primes():
            if prime > int(maximum_prime):
                break
            if discriminant % prime == 0:
                continue
            roots = [
                value
                for value in range(prime)
                if sum(int(coefficient) * pow(value, power, prime) for power, coefficient in enumerate(outer_coefficients))
                % prime
                == 0
            ]
            if len(roots) == 1:
                witness = {"prime": int(prime), "linear_root": int(roots[0]), "factorization_pattern": [1, 3]}
                break
    return {
        "outer_degree": 4,
        "outer_discriminant": int(discriminant),
        "outer_discriminant_nonsquare": bool(nonsquare),
        "three_cycle_witness": witness,
        "outer_galois_group": "S4" if nonsquare and witness else None,
        "proved": bool(nonsquare and witness),
        "proof": "eisenstein_transitive_plus_unramified_3cycle_plus_nonsquare_discriminant",
    }
