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


def executable_generator_for_family(family_name: str) -> ExecutableGeneratorSpec | None:
    if str(family_name) == GX2_SPEC.family:
        return GX2_SPEC
    return None


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
        parameters = gx2_target_parameters(int(r_value))

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


def base_polynomial_coefficients_y(
    positive_roots: Sequence[int],
    negative_roots: Sequence[int],
) -> list[int]:
    """Return ascending coefficients for prod(y-a) * prod(y+b)."""

    coeffs = [1]
    for root in positive_roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    for root in negative_roots:
        coeffs = multiply_polynomials(coeffs, [int(root), 1])
    if len(coeffs) != 13 or coeffs[-1] != 1:
        raise ValueError("expected monic degree-12 base polynomial")
    return [int(value) for value in coeffs]


def lift_base_to_degree24(base_coefficients_y: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for g(x^2), omitting the monic x^24 term."""

    base = [int(value) for value in base_coefficients_y]
    if len(base) != 13 or base[-1] != 1:
        raise ValueError("expected monic degree-12 base coefficients")
    coeffs = [0] * DEGREE
    for y_exponent, coefficient in enumerate(base[:-1]):
        coeffs[2 * y_exponent] = int(coefficient)
    return coeffs


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
