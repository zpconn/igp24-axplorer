"""Executable construction generators for IGP24 route experiments.

The helpers in this module are intentionally modest. They expose target-bound
generators whose algebraic shape is clear enough for routing experiments, but
they do not claim exact 24T labels. Any generated polynomial still needs local
validity checks, known-submission exclusion, and adaptive Frobenius review.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Sequence

from src.igp24.group_compatibility import GroupRecord
from src.igp24.polynomial import DEGREE

GENERATOR_SOUNDNESS = "executable_structure_preserving_generator_not_exact_label_evidence"
GX2_GENERATOR_NAME = "gx2_exact_composed_lift_v1"
QUARTIC_X6_GENERATOR_NAME = "quartic_x6_exact_lift_v1"
COMPOSITION_8X3_GENERATOR_NAME = "composition_8x3_exact_cubic_lift_v1"
TOWER_6X4_GENERATOR_NAME = "tower_6x4_exact_quartic_inner_v1"


def multiply_polynomials(left: Iterable[int], right: Iterable[int]) -> list[int]:
    """Multiply ascending-order integer coefficient lists."""

    a = [int(value) for value in left]
    b = [int(value) for value in right]
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


@dataclass(frozen=True)
class ExecutableGeneratorSpec:
    family: str
    generator_name: str
    supported_r_values: tuple[int, ...]
    required_block_sizes: tuple[int, ...]
    structure_preservation: str
    intended_group_constraint: str
    parameterization: tuple[str, ...]
    soundness: str = GENERATOR_SOUNDNESS

    def supports_r(self, r_value: int | None) -> bool:
        return r_value is not None and int(r_value) in self.supported_r_values


GX2_SPEC = ExecutableGeneratorSpec(
    family="gx2_degree12_lift",
    generator_name=GX2_GENERATOR_NAME,
    supported_r_values=tuple(range(0, 25, 2)),
    required_block_sizes=(2, 12),
    structure_preservation="exact g(x^2) support; no odd x-power perturbations",
    intended_group_constraint=(
        "The polynomial is composed through x^2, so the construction preserves "
        "a divisor-2 block symmetry before exact Galois verification."
    ),
    parameterization=(
        "positive_y_root_count = target_r / 2",
        "negative_y_root_count = 12 - positive_y_root_count",
        "small base-coefficient perturbations inside g(y)",
    ),
)


QUARTIC_X6_SPEC = ExecutableGeneratorSpec(
    family="quartic_in_x6",
    generator_name=QUARTIC_X6_GENERATOR_NAME,
    supported_r_values=(0, 2, 4, 6, 8),
    required_block_sizes=(6, 12),
    structure_preservation="exact h(x^6) support; no off-core perturbations",
    intended_group_constraint=(
        "The polynomial is composed through x^6, so the construction preserves "
        "a divisor-6 block symmetry before exact Galois verification."
    ),
    parameterization=(
        "positive_y_root_count = target_r / 2",
        "negative_y_root_count = 4 - positive_y_root_count",
        "small base-coefficient perturbations inside h(y)",
    ),
)


COMPOSITION_8X3_SPEC = ExecutableGeneratorSpec(
    family="composition_8x3",
    generator_name=COMPOSITION_8X3_GENERATOR_NAME,
    supported_r_values=(8, 12, 16, 20, 24),
    required_block_sizes=(3, 8),
    structure_preservation="exact h(c(x)) support with deg(h)=8 and monic cubic c(x)",
    intended_group_constraint=(
        "The polynomial is an exact composition h(c(x)) with a degree-3 inner map, "
        "so it preserves a degree-3 fiber/block structure before exact Galois verification."
    ),
    parameterization=(
        "inner cubic c(x)=x^3-s*x with s chosen so selected outer levels have one or three real preimages",
        "inside_y_root_count = (target_r - 8) / 2",
        "outside_y_root_count = 8 - inside_y_root_count",
        "small outer degree-8 coefficient perturbations while preserving exact composition",
    ),
)


TOWER_6X4_SPEC = ExecutableGeneratorSpec(
    family="tower_6x4",
    generator_name=TOWER_6X4_GENERATOR_NAME,
    supported_r_values=(0, 4, 8, 12, 16, 20, 24),
    required_block_sizes=(4, 6, 12),
    structure_preservation="exact h(q(x)) support with deg(h)=6 and quartic q(x)=x^4-s*x^2",
    intended_group_constraint=(
        "The polynomial is an exact degree-6-by-degree-4 tower h(q(x)); the quartic "
        "inner map preserves an imprimitive tower/fiber structure before exact Galois verification."
    ),
    parameterization=(
        "inner quartic q(x)=x^4-s*x^2 with s chosen so selected outer levels have four or zero real preimages",
        "four_real_preimage_level_count = target_r / 4",
        "no_real_preimage_level_count = 6 - four_real_preimage_level_count",
        "small outer degree-6 coefficient perturbations while preserving exact composition",
    ),
)


EXECUTABLE_GENERATOR_SPECS = {
    GX2_SPEC.family: GX2_SPEC,
    QUARTIC_X6_SPEC.family: QUARTIC_X6_SPEC,
    COMPOSITION_8X3_SPEC.family: COMPOSITION_8X3_SPEC,
    TOWER_6X4_SPEC.family: TOWER_6X4_SPEC,
}


def executable_generator_for_family(family_name: str) -> ExecutableGeneratorSpec | None:
    return EXECUTABLE_GENERATOR_SPECS.get(str(family_name))


def gx2_target_parameters(r_value: int) -> dict[str, int]:
    r_int = int(r_value)
    if r_int < 0 or r_int > 24 or r_int % 2:
        raise ValueError(f"g(x^2) target_r must be even in [0,24], got {r_value}")
    positive_count = r_int // 2
    return {
        "target_r": r_int,
        "base_degree": 12,
        "positive_y_root_count": positive_count,
        "negative_y_root_count": 12 - positive_count,
    }


def quartic_x6_target_parameters(r_value: int) -> dict[str, int]:
    r_int = int(r_value)
    if r_int < 0 or r_int > 8 or r_int % 2:
        raise ValueError(f"h(x^6) target_r must be even in [0,8], got {r_value}")
    positive_count = r_int // 2
    return {
        "target_r": r_int,
        "base_degree": 4,
        "positive_y_root_count": positive_count,
        "negative_y_root_count": 4 - positive_count,
    }


def composition_8x3_target_parameters(r_value: int) -> dict[str, int]:
    r_int = int(r_value)
    if r_int not in COMPOSITION_8X3_SPEC.supported_r_values:
        raise ValueError(f"8x3 exact composition target_r must be one of {COMPOSITION_8X3_SPEC.supported_r_values}, got {r_value}")
    inside_count = (r_int - 8) // 2
    inner_s = 3 if inside_count <= 3 else 12
    y_bound = 2 if inner_s == 3 else 16
    return {
        "target_r": r_int,
        "outer_degree": 8,
        "inner_degree": 3,
        "inside_y_root_count": inside_count,
        "outside_y_root_count": 8 - inside_count,
        "inner_cubic_s": inner_s,
        "three_real_preimage_y_abs_bound_exclusive": y_bound,
    }


def tower_6x4_target_parameters(r_value: int) -> dict[str, int]:
    r_int = int(r_value)
    if r_int not in TOWER_6X4_SPEC.supported_r_values:
        raise ValueError(f"6x4 exact tower target_r must be one of {TOWER_6X4_SPEC.supported_r_values}, got {r_value}")
    four_real_count = r_int // 4
    return {
        "target_r": r_int,
        "outer_degree": 6,
        "inner_degree": 4,
        "four_real_preimage_level_count": four_real_count,
        "no_real_preimage_level_count": 6 - four_real_count,
        "inner_quartic_s": 6,
        "quartic_minimum_floor_abs": 9,
    }


def target_parameters_for_family(family_name: str, r_value: int) -> dict[str, int]:
    if str(family_name) == GX2_SPEC.family:
        return gx2_target_parameters(r_value)
    if str(family_name) == QUARTIC_X6_SPEC.family:
        return quartic_x6_target_parameters(r_value)
    if str(family_name) == COMPOSITION_8X3_SPEC.family:
        return composition_8x3_target_parameters(r_value)
    if str(family_name) == TOWER_6X4_SPEC.family:
        return tower_6x4_target_parameters(r_value)
    raise ValueError(f"no executable target parameterization for family {family_name!r}")


def generation_status_for_route(
    *,
    family_name: str,
    r_value: int | None,
    group_record: GroupRecord | None,
    structurally_eligible: bool,
) -> dict[str, Any]:
    """Return route-level executable-generator status.

    This deliberately does not mark a route as generation-ready. The route has
    not produced any candidate rows yet, so local validity and adaptive
    target-exclusion checks are still pending.
    """

    spec = executable_generator_for_family(family_name)
    if spec is None:
        return {
            "executable_generator_available": False,
            "executable_generator_name": None,
            "executable_generator_soundness": GENERATOR_SOUNDNESS,
            "target_parameters_instantiated": False,
            "target_generator_parameters": {},
            "structure_preservation_declared": False,
            "structure_preservation": None,
            "executable_generation_ready": False,
            "generation_ready_blocking_reasons": [
                "executable_generator_not_bound_to_target",
                "structure_preservation_not_verified",
                "target_parameters_not_instantiated",
                "generated_outputs_not_validated",
                "adaptive_target_exclusion_not_run",
            ],
        }

    parameter_blockers: list[str] = []
    parameters: dict[str, Any] = {}
    if not spec.supports_r(r_value):
        parameter_blockers.append("generator_unsupported_target_r")
    else:
        parameters = target_parameters_for_family(spec.family, int(r_value))

    block_sizes = set(int(value) for value in (group_record.block_sizes if group_record else ()))
    if group_record is None:
        parameter_blockers.append("missing_group_invariants")
    elif group_record.primitive is True:
        parameter_blockers.append("generator_requires_imprimitive_target")
    elif not block_sizes.intersection(spec.required_block_sizes):
        parameter_blockers.append("generator_block_structure_not_matched_to_target")

    available = bool(structurally_eligible) and not parameter_blockers
    blockers: list[str] = []
    if not available:
        blockers.extend(parameter_blockers or ["route_not_structurally_eligible"])
    else:
        blockers.extend(["generated_outputs_not_validated", "adaptive_target_exclusion_not_run"])

    return {
        "executable_generator_available": available,
        "executable_generator_name": spec.generator_name if available else None,
        "executable_generator_soundness": spec.soundness,
        "target_parameters_instantiated": available,
        "target_generator_parameters": parameters if available else {},
        "structure_preservation_declared": available,
        "structure_preservation": spec.structure_preservation if available else None,
        "intended_group_constraint": spec.intended_group_constraint if available else None,
        "executable_generation_ready": False,
        "generation_ready_blocking_reasons": blockers,
    }


def _root_layouts(count: int) -> list[tuple[int, ...]]:
    if count < 0 or count > 12:
        raise ValueError(f"invalid degree-12 root count: {count}")
    if count == 0:
        return [()]
    layouts: set[tuple[int, ...]] = set()
    layouts.add(tuple(range(1, count + 1)))
    layouts.add(tuple(range(2, count + 2)))
    layouts.add(tuple(sorted([1, *range(3, count + 2)])))
    layouts.add(tuple(sorted([1, 2, *range(4, count + 2)])))
    spread = tuple(sorted(1 + 2 * index for index in range(count)))
    layouts.add(spread)
    capped = tuple(sorted(min(18, value) for value in spread))
    if len(set(capped)) == count:
        layouts.add(capped)
    return sorted(layouts)


def root_product_coefficients_y(
    positive_roots: Sequence[int],
    negative_roots: Sequence[int],
) -> list[int]:
    """Return ascending coefficients for prod(y-a) * prod(y+b)."""

    coeffs = [1]
    for root in positive_roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    for root in negative_roots:
        coeffs = multiply_polynomials(coeffs, [int(root), 1])
    return [int(value) for value in coeffs]


def base_polynomial_coefficients_y(
    positive_roots: Sequence[int],
    negative_roots: Sequence[int],
) -> list[int]:
    """Return ascending coefficients for prod(y-a) * prod(y+b)."""

    coeffs = root_product_coefficients_y(positive_roots, negative_roots)
    if len(coeffs) != 13 or coeffs[-1] != 1:
        raise ValueError("expected monic degree-12 base polynomial")
    return coeffs


def quartic_base_polynomial_coefficients_y(
    positive_roots: Sequence[int],
    negative_roots: Sequence[int],
) -> list[int]:
    """Return ascending coefficients for a monic quartic h(y)."""

    coeffs = root_product_coefficients_y(positive_roots, negative_roots)
    if len(coeffs) != 5 or coeffs[-1] != 1:
        raise ValueError("expected monic degree-4 base polynomial")
    return coeffs


def lift_base_to_degree24_by_power(base_coefficients_y: Iterable[int], power: int) -> list[int]:
    """Return [a0, ..., a23] for g(x^power), omitting the monic x^24 term."""

    base = [int(value) for value in base_coefficients_y]
    power_int = int(power)
    if power_int <= 0 or DEGREE % power_int:
        raise ValueError(f"power must be a positive divisor of {DEGREE}, got {power}")
    expected_len = DEGREE // power_int + 1
    if len(base) != expected_len or base[-1] != 1:
        raise ValueError(f"expected monic degree-{DEGREE // power_int} base coefficients")
    coeffs = [0] * DEGREE
    for y_exponent, coefficient in enumerate(base[:-1]):
        coeffs[power_int * y_exponent] = int(coefficient)
    return coeffs


def lift_base_to_degree24(base_coefficients_y: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for g(x^2), omitting the monic x^24 term."""

    return lift_base_to_degree24_by_power(base_coefficients_y, 2)


def compose_polynomial(outer_coefficients_y: Iterable[int], inner_coefficients_x: Iterable[int]) -> list[int]:
    """Return ascending coefficients for outer(inner(x))."""

    outer = [int(value) for value in outer_coefficients_y]
    inner = [int(value) for value in inner_coefficients_x]
    out = [0]
    power = [1]
    for coefficient in outer:
        if coefficient:
            if len(out) < len(power):
                out.extend([0] * (len(power) - len(out)))
            for index, value in enumerate(power):
                out[index] += int(coefficient) * int(value)
        power = multiply_polynomials(power, inner)
    return [int(value) for value in out]


def compose_outer_degree8_with_cubic(outer_coefficients_y: Iterable[int], inner_coefficients_x: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for a monic degree-8 polynomial composed with a cubic."""

    outer = [int(value) for value in outer_coefficients_y]
    inner = [int(value) for value in inner_coefficients_x]
    if len(outer) != 9 or outer[-1] != 1:
        raise ValueError("expected monic degree-8 outer coefficients")
    if len(inner) != 4 or inner[-1] != 1:
        raise ValueError("expected monic cubic inner coefficients")
    coeffs = compose_polynomial(outer, inner)
    if len(coeffs) != DEGREE + 1 or coeffs[-1] != 1:
        raise ValueError("expected monic degree-24 composed polynomial")
    return coeffs[:DEGREE]


def compose_outer_degree6_with_quartic(
    outer_coefficients_y: Iterable[int],
    inner_coefficients_x: Iterable[int],
) -> list[int]:
    """Return [a0, ..., a23] for a monic degree-6 polynomial composed with a quartic."""

    outer = [int(value) for value in outer_coefficients_y]
    inner = [int(value) for value in inner_coefficients_x]
    if len(outer) != 7 or outer[-1] != 1:
        raise ValueError("expected monic degree-6 outer coefficients")
    if len(inner) != 5 or inner[-1] != 1:
        raise ValueError("expected monic quartic inner coefficients")
    coeffs = compose_polynomial(outer, inner)
    if len(coeffs) != DEGREE + 1 or coeffs[-1] != 1:
        raise ValueError("expected monic degree-24 composed polynomial")
    return coeffs[:DEGREE]


def _base_perturbation_groups(rng: random.Random) -> list[tuple[tuple[int, int], ...]]:
    singles = [((index, delta),) for index in range(0, 12) for delta in (-5, -3, -2, -1, 1, 2, 3, 5)]
    groups = [
        ((0, 1), (6, -1)),
        ((0, -1), (6, 1)),
        ((1, 2), (5, -1)),
        ((1, -2), (5, 1)),
        ((2, 1), (7, -1)),
        ((2, -1), (7, 1)),
        ((3, 1), (8, -1)),
        ((3, -1), (8, 1)),
        ((1, 1), (4, -1), (7, 1)),
        ((2, 1), (5, -1), (8, 1)),
    ]
    out = singles + groups
    rng.shuffle(out)
    return out


def _quartic_perturbation_groups(rng: random.Random) -> list[tuple[tuple[int, int], ...]]:
    singles = [((index, delta),) for index in range(0, 4) for delta in (-3, -2, -1, 1, 2, 3)]
    groups = [
        ((0, 1), (1, -1)),
        ((0, -1), (1, 1)),
        ((1, 1), (2, -1)),
        ((1, -1), (2, 1)),
        ((2, 1), (3, -1)),
        ((2, -1), (3, 1)),
        ((0, 1), (2, -1), (3, 1)),
        ((0, -1), (2, 1), (3, -1)),
    ]
    out = singles + groups
    rng.shuffle(out)
    return out


def _degree8_perturbation_groups(rng: random.Random) -> list[tuple[tuple[int, int], ...]]:
    singles = [((index, delta),) for index in range(0, 8) for delta in (-3, -2, -1, 1, 2, 3)]
    groups = [
        ((0, 1), (2, -1)),
        ((0, -1), (2, 1)),
        ((1, 1), (3, -1)),
        ((1, -1), (3, 1)),
        ((2, 1), (4, -1), (6, 1)),
        ((2, -1), (4, 1), (6, -1)),
        ((0, 2), (5, -1)),
        ((0, -2), (5, 1)),
    ]
    out = singles + groups
    rng.shuffle(out)
    return out


def _degree6_perturbation_groups(rng: random.Random) -> list[tuple[tuple[int, int], ...]]:
    singles = [((index, delta),) for index in range(0, 6) for delta in (-3, -2, -1, 1, 2, 3)]
    groups = [
        ((0, 1), (2, -1)),
        ((0, -1), (2, 1)),
        ((1, 1), (3, -1)),
        ((1, -1), (3, 1)),
        ((0, 2), (4, -1)),
        ((0, -2), (4, 1)),
        ((2, 2), (5, -1)),
        ((2, -2), (5, 1)),
        ((0, 1), (2, -2), (4, 1)),
        ((0, -1), (2, 2), (4, -1)),
        ((1, 2), (3, -1), (5, 1)),
        ((1, -2), (3, 1), (5, -1)),
    ]
    out = singles + groups
    rng.shuffle(out)
    return out


def _inside_cubic_level_layouts(count: int, *, bound_exclusive: int) -> list[tuple[int, ...]]:
    if count < 0 or count > 8:
        raise ValueError(f"invalid inside level count: {count}")
    if count == 0:
        return [()]
    layouts: set[tuple[int, ...]] = set()
    odd_pool = tuple(value for value in (-13, -11, -9, -7, -5, -3, -1, 1, 3, 5, 7, 9, 11, 13) if abs(value) < bound_exclusive)
    even_pool = tuple(value for value in (-14, -12, -10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12, 14) if abs(value) < bound_exclusive)
    mixed_pool = tuple(value for value in (-13, -9, -5, -1, 1, 5, 9, 13) if abs(value) < bound_exclusive)
    pools = [pool for pool in (odd_pool, even_pool, mixed_pool) if len(pool) >= count]
    for pool in pools:
        layouts.add(tuple(sorted(pool[:count])))
        layouts.add(tuple(sorted(pool[-count:])))
    if not layouts:
        raise ValueError(f"not enough inside cubic levels for count={count}, bound={bound_exclusive}")
    return sorted(layouts)


def _outside_cubic_level_layouts(count: int, *, bound_exclusive: int) -> list[tuple[int, ...]]:
    if count < 0 or count > 8:
        raise ValueError(f"invalid outside level count: {count}")
    if count == 0:
        return [()]
    layouts: set[tuple[int, ...]] = set()
    start = int(bound_exclusive) + 1
    positive = tuple(range(start, start + count))
    negative = tuple(range(-start - count + 1, -start + 1))
    mixed_pool = tuple([-(start + 7), -(start + 5), -(start + 3), -(start + 1), start + 1, start + 3, start + 5, start + 7])
    layouts.add(tuple(sorted(positive)))
    layouts.add(tuple(sorted(negative)))
    layouts.add(tuple(sorted(mixed_pool[:count])))
    layouts.add(tuple(sorted(mixed_pool[-count:])))
    return sorted(layouts)


def _tower_four_real_level_layouts(count: int, *, inner_s: int) -> list[tuple[int, ...]]:
    if count < 0 or count > 6:
        raise ValueError(f"invalid four-real tower level count: {count}")
    if count == 0:
        return [()]
    minimum_abs = (int(inner_s) * int(inner_s)) // 4
    pool = tuple(range(-1, -minimum_abs, -1))
    if len(pool) < count:
        raise ValueError(f"not enough four-real tower levels for count={count}, s={inner_s}")
    layouts: set[tuple[int, ...]] = set()
    layouts.add(tuple(sorted(pool[:count])))
    layouts.add(tuple(sorted(pool[-count:])))
    spread = tuple(sorted(pool[index] for index in range(0, min(len(pool), 2 * count), 2)))
    if len(spread) == count:
        layouts.add(spread)
    centered_pool = tuple(range(-(count + 1), -1))
    if len(centered_pool) == count and all(-minimum_abs < value < 0 for value in centered_pool):
        layouts.add(tuple(sorted(centered_pool)))
    return sorted(layouts)


def _tower_no_real_level_layouts(count: int, *, inner_s: int) -> list[tuple[int, ...]]:
    if count < 0 or count > 6:
        raise ValueError(f"invalid no-real tower level count: {count}")
    if count == 0:
        return [()]
    minimum_abs = (int(inner_s) * int(inner_s)) // 4
    start = minimum_abs + 1
    layouts: set[tuple[int, ...]] = set()
    near = tuple(range(-start, -start - count, -1))
    shifted = tuple(range(-(start + 2), -(start + 2 + count), -1))
    spaced = tuple(-(start + 2 * index) for index in range(count))
    layouts.add(tuple(sorted(near)))
    layouts.add(tuple(sorted(shifted)))
    layouts.add(tuple(sorted(spaced)))
    return sorted(layouts)


def iter_gx2_trials(*, target_r: int, seed: int, max_trials: int) -> Iterator[dict[str, Any]]:
    """Yield deterministic bounded exact-composed g(x^2) trial plans."""

    params = gx2_target_parameters(target_r)
    rng = random.Random(int(seed))
    positives = _root_layouts(params["positive_y_root_count"])
    negatives = _root_layouts(params["negative_y_root_count"])
    rng.shuffle(positives)
    rng.shuffle(negatives)
    perturbations = _base_perturbation_groups(rng)

    emitted = 0
    for positive_roots in positives:
        for negative_roots in negatives:
            base = base_polynomial_coefficients_y(positive_roots, negative_roots)
            for group in perturbations:
                yield {
                    "generator_name": GX2_GENERATOR_NAME,
                    "family": GX2_SPEC.family,
                    "mode": "base_coefficient_perturbation",
                    "target_r": int(target_r),
                    "positive_y_roots": list(positive_roots),
                    "negative_y_roots": list(negative_roots),
                    "base_coefficients_y_before_perturbation": list(base),
                    "base_perturbations": [
                        {"y_exponent": int(index), "delta": int(delta)} for index, delta in group
                    ],
                }
                emitted += 1
                if emitted >= int(max_trials):
                    return


def iter_quartic_x6_trials(*, target_r: int, seed: int, max_trials: int) -> Iterator[dict[str, Any]]:
    """Yield deterministic bounded exact-composed h(x^6) trial plans."""

    params = quartic_x6_target_parameters(target_r)
    rng = random.Random(int(seed))
    positives = _root_layouts(params["positive_y_root_count"])
    negatives = _root_layouts(params["negative_y_root_count"])
    rng.shuffle(positives)
    rng.shuffle(negatives)
    perturbations = _quartic_perturbation_groups(rng)

    emitted = 0
    for positive_roots in positives:
        for negative_roots in negatives:
            base = quartic_base_polynomial_coefficients_y(positive_roots, negative_roots)
            for group in perturbations:
                yield {
                    "generator_name": QUARTIC_X6_GENERATOR_NAME,
                    "family": QUARTIC_X6_SPEC.family,
                    "mode": "quartic_base_coefficient_perturbation",
                    "target_r": int(target_r),
                    "positive_y_roots": list(positive_roots),
                    "negative_y_roots": list(negative_roots),
                    "base_coefficients_y_before_perturbation": list(base),
                    "base_perturbations": [
                        {"y_exponent": int(index), "delta": int(delta)} for index, delta in group
                    ],
                }
                emitted += 1
                if emitted >= int(max_trials):
                    return


def iter_composition_8x3_trials(*, target_r: int, seed: int, max_trials: int) -> Iterator[dict[str, Any]]:
    """Yield deterministic bounded exact h(c(x)) trial plans for deg(h)=8 and deg(c)=3."""

    params = composition_8x3_target_parameters(target_r)
    rng = random.Random(int(seed))
    inside_layouts = _inside_cubic_level_layouts(
        params["inside_y_root_count"],
        bound_exclusive=params["three_real_preimage_y_abs_bound_exclusive"],
    )
    outside_layouts = _outside_cubic_level_layouts(
        params["outside_y_root_count"],
        bound_exclusive=params["three_real_preimage_y_abs_bound_exclusive"],
    )
    rng.shuffle(inside_layouts)
    rng.shuffle(outside_layouts)
    perturbations = _degree8_perturbation_groups(rng)

    emitted = 0
    inner_coefficients = [0, -int(params["inner_cubic_s"]), 0, 1]
    for inside_levels in inside_layouts:
        for outside_levels in outside_layouts:
            outer_roots = tuple(sorted((*inside_levels, *outside_levels)))
            if len(set(outer_roots)) != 8:
                continue
            base = root_product_coefficients_y(outer_roots, ())
            if len(base) != 9 or base[-1] != 1:
                raise ValueError("expected monic degree-8 outer polynomial")
            for group in perturbations:
                yield {
                    "generator_name": COMPOSITION_8X3_GENERATOR_NAME,
                    "family": COMPOSITION_8X3_SPEC.family,
                    "mode": "outer_degree8_coefficient_perturbation",
                    "target_r": int(target_r),
                    "inside_y_levels": list(inside_levels),
                    "outside_y_levels": list(outside_levels),
                    "outer_roots_before_perturbation": list(outer_roots),
                    "outer_coefficients_y_before_perturbation": list(base),
                    "inner_cubic_coefficients_x": list(inner_coefficients),
                    "inner_cubic_s": int(params["inner_cubic_s"]),
                    "three_real_preimage_y_abs_bound_exclusive": int(
                        params["three_real_preimage_y_abs_bound_exclusive"]
                    ),
                    "outer_perturbations": [
                        {"y_exponent": int(index), "delta": int(delta)} for index, delta in group
                    ],
                }
                emitted += 1
                if emitted >= int(max_trials):
                    return


def iter_tower_6x4_trials(*, target_r: int, seed: int, max_trials: int) -> Iterator[dict[str, Any]]:
    """Yield deterministic bounded exact h(q(x)) tower plans for deg(h)=6 and deg(q)=4."""

    params = tower_6x4_target_parameters(target_r)
    rng = random.Random(int(seed))
    inner_s_values = [int(params["inner_quartic_s"])]
    if params["four_real_preimage_level_count"] <= 4:
        inner_s_values.extend([5, 4])
    if params["four_real_preimage_level_count"] >= 5:
        inner_s_values.extend([7, 8])
    inner_s_values = list(dict.fromkeys(inner_s_values))
    rng.shuffle(inner_s_values)
    perturbations = _degree6_perturbation_groups(rng)

    emitted = 0
    for inner_s in inner_s_values:
        four_real_layouts = _tower_four_real_level_layouts(
            params["four_real_preimage_level_count"],
            inner_s=inner_s,
        )
        no_real_layouts = _tower_no_real_level_layouts(
            params["no_real_preimage_level_count"],
            inner_s=inner_s,
        )
        rng.shuffle(four_real_layouts)
        rng.shuffle(no_real_layouts)
        inner_coefficients = [0, 0, -int(inner_s), 0, 1]
        for four_real_levels in four_real_layouts:
            for no_real_levels in no_real_layouts:
                outer_roots = tuple(sorted((*four_real_levels, *no_real_levels)))
                if len(set(outer_roots)) != 6:
                    continue
                base = root_product_coefficients_y(outer_roots, ())
                if len(base) != 7 or base[-1] != 1:
                    raise ValueError("expected monic degree-6 outer polynomial")
                for group in perturbations:
                    yield {
                        "generator_name": TOWER_6X4_GENERATOR_NAME,
                        "family": TOWER_6X4_SPEC.family,
                        "mode": "outer_degree6_coefficient_perturbation",
                        "target_r": int(target_r),
                        "inner_quartic_coefficients_x": list(inner_coefficients),
                        "inner_quartic_s": int(inner_s),
                        "quartic_minimum_floor_abs": (int(inner_s) * int(inner_s)) // 4,
                        "four_real_preimage_levels": list(four_real_levels),
                        "no_real_preimage_levels": list(no_real_levels),
                        "outer_roots_before_perturbation": list(outer_roots),
                        "outer_coefficients_y_before_perturbation": list(base),
                        "outer_perturbations": [
                            {"y_exponent": int(index), "delta": int(delta)} for index, delta in group
                        ],
                    }
                    emitted += 1
                    if emitted >= int(max_trials):
                        return


def iter_trials_for_family(*, family_name: str, target_r: int, seed: int, max_trials: int) -> Iterator[dict[str, Any]]:
    if str(family_name) == GX2_SPEC.family:
        yield from iter_gx2_trials(target_r=target_r, seed=seed, max_trials=max_trials)
        return
    if str(family_name) == QUARTIC_X6_SPEC.family:
        yield from iter_quartic_x6_trials(target_r=target_r, seed=seed, max_trials=max_trials)
        return
    if str(family_name) == COMPOSITION_8X3_SPEC.family:
        yield from iter_composition_8x3_trials(target_r=target_r, seed=seed, max_trials=max_trials)
        return
    if str(family_name) == TOWER_6X4_SPEC.family:
        yield from iter_tower_6x4_trials(target_r=target_r, seed=seed, max_trials=max_trials)
        return
    raise ValueError(f"no executable trial generator for family {family_name!r}")


def coefficients_from_gx2_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    positive_roots = tuple(int(value) for value in trial["positive_y_roots"])
    negative_roots = tuple(int(value) for value in trial["negative_y_roots"])
    base_before = [
        int(value)
        for value in trial.get("base_coefficients_y_before_perturbation")
        or base_polynomial_coefficients_y(positive_roots, negative_roots)
    ]
    base_after = list(base_before)
    perturbations = []
    for item in trial.get("base_perturbations") or []:
        y_exponent = int(item["y_exponent"])
        delta = int(item["delta"])
        base_after[y_exponent] += delta
        perturbations.append({"y_exponent": y_exponent, "delta": delta})
    coeffs = lift_base_to_degree24(base_after)
    support = [index for index, value in enumerate(coeffs) if int(value) != 0]
    metadata = {
        "construction_family": GX2_SPEC.family,
        "executable_generator_name": GX2_SPEC.generator_name,
        "generator_soundness": GX2_SPEC.soundness,
        "structure_preservation": GX2_SPEC.structure_preservation,
        "intended_group_constraint": GX2_SPEC.intended_group_constraint,
        "target_r": int(trial["target_r"]),
        "positive_y_root_count": len(positive_roots),
        "negative_y_root_count": len(negative_roots),
        "positive_y_roots": list(positive_roots),
        "negative_y_roots": list(negative_roots),
        "base_coefficients_y_before_perturbation": list(base_before),
        "base_coefficients_y": list(base_after),
        "base_perturbations": perturbations,
        "support_after_lift": support,
        "exact_composed_support_divisor": 2,
        "composed_support": True,
        "odd_x_power_terms_present": any(index % 2 for index in support),
        "parameterization_status": "target_r_instantiated",
    }
    return coeffs, metadata


def coefficients_from_quartic_x6_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    positive_roots = tuple(int(value) for value in trial["positive_y_roots"])
    negative_roots = tuple(int(value) for value in trial["negative_y_roots"])
    base_before = [
        int(value)
        for value in trial.get("base_coefficients_y_before_perturbation")
        or quartic_base_polynomial_coefficients_y(positive_roots, negative_roots)
    ]
    base_after = list(base_before)
    perturbations = []
    for item in trial.get("base_perturbations") or []:
        y_exponent = int(item["y_exponent"])
        delta = int(item["delta"])
        base_after[y_exponent] += delta
        perturbations.append({"y_exponent": y_exponent, "delta": delta})
    coeffs = lift_base_to_degree24_by_power(base_after, 6)
    support = [index for index, value in enumerate(coeffs) if int(value) != 0]
    metadata = {
        "construction_family": QUARTIC_X6_SPEC.family,
        "executable_generator_name": QUARTIC_X6_SPEC.generator_name,
        "generator_soundness": QUARTIC_X6_SPEC.soundness,
        "structure_preservation": QUARTIC_X6_SPEC.structure_preservation,
        "intended_group_constraint": QUARTIC_X6_SPEC.intended_group_constraint,
        "target_r": int(trial["target_r"]),
        "positive_y_root_count": len(positive_roots),
        "negative_y_root_count": len(negative_roots),
        "positive_y_roots": list(positive_roots),
        "negative_y_roots": list(negative_roots),
        "base_coefficients_y_before_perturbation": list(base_before),
        "base_coefficients_y": list(base_after),
        "base_perturbations": perturbations,
        "support_after_lift": support,
        "exact_composed_support_divisor": 6,
        "composed_support": True,
        "non_x6_power_terms_present": any(index % 6 for index in support),
        "parameterization_status": "target_r_instantiated",
    }
    return coeffs, metadata


def coefficients_from_composition_8x3_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    base_before = [int(value) for value in trial["outer_coefficients_y_before_perturbation"]]
    base_after = list(base_before)
    perturbations = []
    for item in trial.get("outer_perturbations") or []:
        y_exponent = int(item["y_exponent"])
        delta = int(item["delta"])
        base_after[y_exponent] += delta
        perturbations.append({"y_exponent": y_exponent, "delta": delta})
    inner = [int(value) for value in trial["inner_cubic_coefficients_x"]]
    coeffs = compose_outer_degree8_with_cubic(base_after, inner)
    support = [index for index, value in enumerate(coeffs) if int(value) != 0]
    metadata = {
        "construction_family": COMPOSITION_8X3_SPEC.family,
        "executable_generator_name": COMPOSITION_8X3_SPEC.generator_name,
        "generator_soundness": COMPOSITION_8X3_SPEC.soundness,
        "structure_preservation": COMPOSITION_8X3_SPEC.structure_preservation,
        "intended_group_constraint": COMPOSITION_8X3_SPEC.intended_group_constraint,
        "target_r": int(trial["target_r"]),
        "inside_y_root_count": len(trial.get("inside_y_levels") or []),
        "outside_y_root_count": len(trial.get("outside_y_levels") or []),
        "inside_y_levels": list(trial.get("inside_y_levels") or []),
        "outside_y_levels": list(trial.get("outside_y_levels") or []),
        "outer_roots_before_perturbation": list(trial.get("outer_roots_before_perturbation") or []),
        "outer_coefficients_y_before_perturbation": list(base_before),
        "outer_coefficients_y": list(base_after),
        "inner_cubic_coefficients_x": list(inner),
        "inner_cubic_s": int(trial.get("inner_cubic_s") or 0),
        "three_real_preimage_y_abs_bound_exclusive": int(
            trial.get("three_real_preimage_y_abs_bound_exclusive") or 0
        ),
        "outer_perturbations": perturbations,
        "support_after_lift": support,
        "exact_composition_degree_pattern": "8x3",
        "composed_support": True,
        "exact_composed_support_divisor": None,
        "parameterization_status": "target_r_instantiated",
    }
    return coeffs, metadata


def coefficients_from_tower_6x4_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    base_before = [int(value) for value in trial["outer_coefficients_y_before_perturbation"]]
    base_after = list(base_before)
    perturbations = []
    for item in trial.get("outer_perturbations") or []:
        y_exponent = int(item["y_exponent"])
        delta = int(item["delta"])
        if not 0 <= y_exponent <= 5:
            raise ValueError("tower perturbations may not change the leading outer y^6 coefficient")
        base_after[y_exponent] += delta
        perturbations.append({"y_exponent": y_exponent, "delta": delta})
    inner = [int(value) for value in trial["inner_quartic_coefficients_x"]]
    coeffs = compose_outer_degree6_with_quartic(base_after, inner)
    support = [index for index, value in enumerate(coeffs) if int(value) != 0]
    metadata = {
        "construction_family": TOWER_6X4_SPEC.family,
        "executable_generator_name": TOWER_6X4_SPEC.generator_name,
        "generator_soundness": TOWER_6X4_SPEC.soundness,
        "structure_preservation": TOWER_6X4_SPEC.structure_preservation,
        "intended_group_constraint": TOWER_6X4_SPEC.intended_group_constraint,
        "target_r": int(trial["target_r"]),
        "four_real_preimage_level_count": len(trial.get("four_real_preimage_levels") or []),
        "no_real_preimage_level_count": len(trial.get("no_real_preimage_levels") or []),
        "four_real_preimage_levels": list(trial.get("four_real_preimage_levels") or []),
        "no_real_preimage_levels": list(trial.get("no_real_preimage_levels") or []),
        "outer_roots_before_perturbation": list(trial.get("outer_roots_before_perturbation") or []),
        "outer_coefficients_y_before_perturbation": list(base_before),
        "outer_coefficients_y": list(base_after),
        "inner_quartic_coefficients_x": list(inner),
        "inner_quartic_s": int(trial.get("inner_quartic_s") or 0),
        "quartic_minimum_floor_abs": int(trial.get("quartic_minimum_floor_abs") or 0),
        "outer_perturbations": perturbations,
        "support_after_lift": support,
        "exact_composition_degree_pattern": "6x4",
        "tower_expression": "h(q(x)), q(x)=x^4-s*x^2",
        "composed_support": True,
        "exact_composed_support_divisor": None,
        "even_inner_quartic": True,
        "odd_x_power_terms_present": any(index % 2 for index in support),
        "parameterization_status": "target_r_instantiated",
    }
    return coeffs, metadata


def coefficients_from_trial_for_family(
    *, family_name: str, trial: dict[str, Any]
) -> tuple[list[int], dict[str, Any]]:
    if str(family_name) == GX2_SPEC.family:
        return coefficients_from_gx2_trial(trial)
    if str(family_name) == QUARTIC_X6_SPEC.family:
        return coefficients_from_quartic_x6_trial(trial)
    if str(family_name) == COMPOSITION_8X3_SPEC.family:
        return coefficients_from_composition_8x3_trial(trial)
    if str(family_name) == TOWER_6X4_SPEC.family:
        return coefficients_from_tower_6x4_trial(trial)
    raise ValueError(f"no executable coefficient builder for family {family_name!r}")
