"""Adaptive Frobenius-cycle evidence for IGP24 candidates.

For unramified primes, factorization degrees modulo p give necessary
cycle-type evidence for the Galois group. This module computes those
observations incrementally and evaluates them against a group-cycle index.

The evidence is necessary target-exclusion evidence only. It is not exact
label verification.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from src.igp24.group_compatibility import GroupCycleIndex, candidate_compatibility, cycle_type_key
from src.igp24.polynomial import DEGREE, construct_polynomial, exact_discriminant, validate_coefficients


def small_primes() -> Iterable[int]:
    primes: list[int] = []
    n = 2
    while True:
        is_prime = True
        for p in primes:
            if p * p > n:
                break
            if n % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(n)
            yield n
        n += 1 if n == 2 else 2


def coefficients_from_record(record: dict[str, Any]) -> tuple[int, ...]:
    for key in ("coefficients", "exported_coefficients", "decoded_coefficients"):
        value = record.get(key)
        if isinstance(value, list):
            coeffs = [int(item) for item in value]
            if len(coeffs) == DEGREE + 1:
                if coeffs[-1] != 1:
                    raise ValueError("non_monic_exported_coefficients")
                return validate_coefficients(coeffs[:-1])
            if len(coeffs) == DEGREE:
                return validate_coefficients(coeffs)
    polynomial = record.get("polynomial")
    if isinstance(polynomial, str):
        coeffs = [int(part.strip()) for part in polynomial.split(",") if part.strip()]
        if len(coeffs) == DEGREE + 1:
            if coeffs[-1] != 1:
                raise ValueError("non_monic_polynomial_line")
            return validate_coefficients(coeffs[:-1])
    raise ValueError("missing_degree24_coefficients")


def discriminant_from_record(record: dict[str, Any], coefficients: Sequence[int]) -> tuple[int, str]:
    for key in (
        "polynomial_discriminant_abs",
        "polynomial_disc_abs",
        "polynomial_discriminant",
        "discriminant_abs",
        "discriminant",
    ):
        value = record.get(key)
        if value not in (None, ""):
            disc = int(value)
            return abs(disc), key
    return abs(exact_discriminant(coefficients)), "computed_sympy_polynomial_discriminant"


def factorization_degrees_mod_prime(coefficients: Sequence[int], prime: int) -> tuple[int, ...]:
    poly = construct_polynomial(coefficients)
    x = poly.gens[0]
    mod_poly = poly.__class__(poly.as_expr(), x, modulus=int(prime))
    _unit, factors = mod_poly.factor_list()
    degrees: list[int] = []
    for factor, exponent in factors:
        degrees.extend([int(factor.degree())] * int(exponent))
    if sum(degrees) != DEGREE:
        raise ValueError(f"bad_modular_degree_sum:{prime}:{degrees}")
    return tuple(sorted(degrees))


def unramified_factorization_degrees_mod_prime(
    coefficients: Sequence[int],
    prime: int,
) -> tuple[int, ...] | None:
    """Return factor degrees exactly when ``prime`` is unramified.

    For a monic integral polynomial, reduction modulo ``p`` is squarefree if
    and only if ``p`` does not divide the polynomial discriminant.  Checking
    factor multiplicities therefore verifies unramifiedness without first
    constructing the often enormous integer discriminant.
    """

    poly = construct_polynomial(coefficients)
    x = poly.gens[0]
    mod_poly = poly.__class__(poly.as_expr(), x, modulus=int(prime))
    _unit, factors = mod_poly.factor_list()
    if any(int(exponent) != 1 for _factor, exponent in factors):
        return None
    degrees = tuple(sorted(int(factor.degree()) for factor, _exponent in factors))
    if sum(degrees) != DEGREE:
        raise ValueError(f"bad_modular_degree_sum:{prime}:{degrees}")
    return degrees


@dataclass(frozen=True)
class FrobeniusObservation:
    prime: int
    degrees: tuple[int, ...]
    cycle_type: str
    indexed_target_survivor_count: int
    valuable_target_count: int

    def as_json(self) -> dict[str, Any]:
        return {
            "prime": self.prime,
            "degrees": list(self.degrees),
            "cycle_type": self.cycle_type,
            "indexed_target_survivor_count": self.indexed_target_survivor_count,
            "valuable_target_count": self.valuable_target_count,
        }


def compatibility_for_patterns(
    record: dict[str, Any],
    patterns: list[dict[str, Any]],
    index: GroupCycleIndex,
    progress_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    row = {**record, "mod_p_factorization_degree_patterns": patterns}
    return candidate_compatibility(row, index, progress_rows=progress_rows)


def collect_frobenius_observations(
    record: dict[str, Any],
    index: GroupCycleIndex,
    *,
    progress_rows: Iterable[dict[str, Any]] = (),
    max_usable_primes: int = 80,
    max_prime: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    coefficients = coefficients_from_record(record)
    discriminant, discriminant_source = discriminant_from_record(record, coefficients)
    patterns: list[dict[str, Any]] = []
    observations: list[FrobeniusObservation] = []
    skipped_ramified: list[int] = []
    primes_examined = 0
    for prime in small_primes():
        if max_prime is not None and prime > int(max_prime):
            break
        if len(observations) >= int(max_usable_primes):
            break
        primes_examined += 1
        if discriminant % prime == 0:
            skipped_ramified.append(prime)
            continue
        degrees = factorization_degrees_mod_prime(coefficients, prime)
        pattern = {"prime": prime, "degrees": list(degrees)}
        patterns.append(pattern)
        compat = compatibility_for_patterns(record, patterns, index, progress_rows)
        observations.append(
            FrobeniusObservation(
                prime=prime,
                degrees=degrees,
                cycle_type=cycle_type_key(degrees),
                indexed_target_survivor_count=int(compat.get("indexed_target_survivor_count") or 0),
                valuable_target_count=len(compat.get("valuable_targets_not_ruled_out") or []),
            )
        )
    final_compatibility = compatibility_for_patterns(record, patterns, index, progress_rows) if patterns else candidate_compatibility(record, index, progress_rows=progress_rows)
    return {
        "canonical_hash": record.get("canonical_hash"),
        "label": record.get("label") or record.get("verified_group_label"),
        "r": record.get("r") or record.get("real_root_count"),
        "pair_key": record.get("pair_key"),
        "discriminant_abs": str(discriminant),
        "discriminant_source": discriminant_source,
        "primes_examined": primes_examined,
        "skipped_ramified_primes": skipped_ramified,
        "usable_prime_count": len(observations),
        "observations": [item.as_json() for item in observations],
        "mod_p_factorization_degree_patterns": patterns,
        "final_compatibility": final_compatibility,
        "runtime_seconds": time.perf_counter() - started,
    }


def adaptive_frobenius_evidence(
    record: dict[str, Any],
    index: GroupCycleIndex,
    *,
    progress_rows: Iterable[dict[str, Any]] = (),
    max_usable_primes: int = 80,
    stable_after: int = 5,
    min_usable_primes: int = 1,
    stop_when_no_valuable_targets: bool = True,
) -> dict[str, Any]:
    collected = collect_frobenius_observations(
        record,
        index,
        progress_rows=progress_rows,
        max_usable_primes=max_usable_primes,
    )
    patterns: list[dict[str, Any]] = []
    previous_survivors: tuple[str, ...] | None = None
    stable_count = 0
    stop_reason = "evidence_budget_exhausted"
    used_observations: list[dict[str, Any]] = []
    for observation in collected["observations"]:
        patterns.append({"prime": observation["prime"], "degrees": observation["degrees"]})
        compat = compatibility_for_patterns(record, patterns, index, progress_rows)
        survivors = tuple(compat.get("indexed_target_labels_not_ruled_out") or [])
        if previous_survivors is not None and survivors == previous_survivors:
            stable_count += 1
        else:
            stable_count = 0
        previous_survivors = survivors
        used_observations.append(observation)
        if (
            stop_when_no_valuable_targets
            and len(patterns) >= int(min_usable_primes)
            and len(compat.get("valuable_targets_not_ruled_out") or []) == 0
        ):
            stop_reason = "valuable_targets_ruled_out"
            break
        if int(stable_after) > 0 and stable_count >= int(stable_after):
            stop_reason = "survivor_set_stable"
            break
    final_patterns = [{"prime": item["prime"], "degrees": item["degrees"]} for item in used_observations]
    final_compatibility = compatibility_for_patterns(record, final_patterns, index, progress_rows) if final_patterns else collected["final_compatibility"]
    return {
        **collected,
        "observations": used_observations,
        "mod_p_factorization_degree_patterns": final_patterns,
        "usable_prime_count": len(used_observations),
        "final_compatibility": final_compatibility,
        "stop_reason": stop_reason,
        "stable_after": int(stable_after),
        "min_usable_primes": int(min_usable_primes),
        "soundness": "adaptive_unramified_frobenius_cycle_target_exclusion_only",
    }
