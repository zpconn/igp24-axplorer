"""Project free-form AXG outputs onto exact structural constructions.

The language model proposes the shape of an outer polynomial.  This module
extracts approximate outer roots, projects them onto distinct integer centers,
and lets the exact Eisenstein construction rebuild the polynomial.  Projection
does not identify a Galois group; it only turns a model proposal into a valid,
structure-preserving parameter proposal.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from src.igp24.polynomial import DEGREE, validate_coefficients


@dataclass(frozen=True)
class ProjectionFamily:
    family_id: str
    prime: int
    center_start: int
    center_count: int
    inner_power: int = 2
    outer_degree: int = 12

    @property
    def center_stop(self) -> int:
        return self.center_start + self.center_count - 1


R24_M2_PROJECTION_FAMILIES = (
    ProjectionFamily("train_d12_x2_p2_low", 2, 1, 72),
    ProjectionFamily("train_d12_x2_p3_low", 3, 1, 72),
    ProjectionFamily("train_d12_x2_p5_mid", 5, 17, 72),
    ProjectionFamily("train_d12_x2_p7_mid", 7, 33, 72),
)


@dataclass(frozen=True)
class StructuralProjection:
    family: ProjectionFamily
    centers: tuple[int, ...]
    center_estimates: tuple[float, ...]
    assignment_rmse: float
    imaginary_rmse: float
    normalized_projection_error: float


def outer_coefficients_from_power_composition(
    coefficients: Sequence[int],
    *,
    inner_power: int,
) -> tuple[int, ...]:
    """Extract ascending monic outer coefficients from ``h(x**m)``."""

    values = tuple(int(value) for value in coefficients)
    if len(values) == DEGREE + 1:
        if values[-1] != 1:
            raise ValueError("non_monic_exported_coefficients")
        values = values[:-1]
    values = validate_coefficients(values)
    power = int(inner_power)
    if power <= 0 or DEGREE % power:
        raise ValueError("inner_power_must_divide_degree_24")
    if any(value for exponent, value in enumerate(values) if exponent % power):
        raise ValueError("coefficients_do_not_have_required_power_support")
    return tuple(values[exponent] for exponent in range(0, DEGREE, power)) + (1,)


def approximate_outer_roots(outer_coefficients: Sequence[int]) -> tuple[complex, ...]:
    """Compute scale-normalized numerical roots of a monic outer polynomial."""

    outer = tuple(int(value) for value in outer_coefficients)
    degree = len(outer) - 1
    if degree <= 0 or outer[-1] != 1:
        raise ValueError("monic_outer_polynomial_required")
    mean_root_scale = abs(float(outer[-2])) / degree if outer[-2] else 1.0
    scale = max(1.0, mean_root_scale)
    descending = [float(outer[power]) / scale ** (degree - power) for power in range(degree, -1, -1)]
    roots = np.roots(np.asarray(descending, dtype=np.float64)) * scale
    if len(roots) != degree or not np.all(np.isfinite(roots)):
        raise ValueError("outer_root_approximation_failed")
    return tuple(complex(root) for root in roots)


def project_strictly_increasing_integers(
    values: Sequence[float],
    *,
    minimum: int,
    maximum: int,
) -> tuple[int, ...]:
    """Least-squares projection onto a bounded, strictly increasing tuple."""

    ordered = tuple(sorted(float(value) for value in values))
    count = len(ordered)
    domain = tuple(range(int(minimum), int(maximum) + 1))
    if count <= 0 or len(domain) < count:
        raise ValueError("integer_projection_domain_too_small")

    infinity = float("inf")
    previous = [infinity] * len(domain)
    parents: list[list[int]] = [[-1] * len(domain) for _ in range(count)]
    last_first_index = len(domain) - count
    for index in range(last_first_index + 1):
        previous[index] = (ordered[0] - domain[index]) ** 2

    for value_index in range(1, count):
        prefix_cost = [infinity] * len(domain)
        prefix_index = [-1] * len(domain)
        best_cost = infinity
        best_index = -1
        for domain_index, cost in enumerate(previous):
            if cost < best_cost:
                best_cost = cost
                best_index = domain_index
            prefix_cost[domain_index] = best_cost
            prefix_index[domain_index] = best_index

        current = [infinity] * len(domain)
        first_index = value_index
        last_index = len(domain) - (count - value_index)
        for domain_index in range(first_index, last_index + 1):
            predecessor = prefix_index[domain_index - 1]
            if predecessor < 0:
                continue
            current[domain_index] = (
                prefix_cost[domain_index - 1] + (ordered[value_index] - domain[domain_index]) ** 2
            )
            parents[value_index][domain_index] = predecessor
        previous = current

    final_index = min(range(len(domain)), key=previous.__getitem__)
    if not math.isfinite(previous[final_index]):
        raise ValueError("integer_projection_has_no_solution")
    selected = [final_index]
    for value_index in range(count - 1, 0, -1):
        final_index = parents[value_index][final_index]
        selected.append(final_index)
    selected.reverse()
    return tuple(domain[index] for index in selected)


def project_outer_roots_to_family(
    outer_coefficients: Sequence[int],
    family: ProjectionFamily,
    *,
    jitter: Sequence[float] | None = None,
) -> StructuralProjection:
    """Project an AXG outer polynomial onto one exact corpus-family domain."""

    roots = approximate_outer_roots(outer_coefficients)
    if len(roots) != family.outer_degree:
        raise ValueError("outer_degree_does_not_match_projection_family")
    ordered_roots = sorted(roots, key=lambda root: (root.real, root.imag))
    estimates = [root.real / family.prime for root in ordered_roots]
    if jitter is not None:
        if len(jitter) != len(estimates):
            raise ValueError("projection_jitter_length_mismatch")
        estimates = [estimate + float(delta) for estimate, delta in zip(estimates, jitter)]
    centers = project_strictly_increasing_integers(
        estimates,
        minimum=family.center_start,
        maximum=family.center_stop,
    )
    assignment_rmse = math.sqrt(
        sum((estimate - center) ** 2 for estimate, center in zip(sorted(estimates), centers)) / len(centers)
    )
    imaginary_rmse = math.sqrt(
        sum((root.imag / family.prime) ** 2 for root in ordered_roots) / len(ordered_roots)
    )
    span = max(1, family.center_count - 1)
    normalized = math.sqrt(assignment_rmse**2 + imaginary_rmse**2) / span
    return StructuralProjection(
        family=family,
        centers=centers,
        center_estimates=tuple(sorted(estimates)),
        assignment_rmse=assignment_rmse,
        imaginary_rmse=imaginary_rmse,
        normalized_projection_error=normalized,
    )


def deterministic_projection_jitter(
    source_hash: str,
    family_id: str,
    variant: int,
    count: int,
) -> tuple[float, ...]:
    if int(variant) == 0:
        return (0.0,) * int(count)
    payload = f"projection|{source_hash}|{family_id}|{int(variant)}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    generator = random.Random(seed)
    radius = min(4.0, 0.75 * int(variant))
    return tuple(generator.uniform(-radius, radius) for _ in range(int(count)))


def deterministic_baseline_centers(
    source_hash: str,
    family: ProjectionFamily,
    *,
    variant: int,
) -> tuple[int, ...]:
    payload = f"baseline|{source_hash}|{family.family_id}|{int(variant)}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    generator = random.Random(seed)
    domain = range(family.center_start, family.center_stop + 1)
    return tuple(sorted(generator.sample(tuple(domain), family.outer_degree)))
