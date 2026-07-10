"""Exact and proxy polynomial utilities for the IGP24 stage-0 scaffold.

Candidates are represented by the 24 free coefficients [a0, ..., a23] of the
monic degree-24 polynomial x**24 + a23*x**23 + ... + a0.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import signal
import threading
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from numbers import Integral
from typing import Any, Iterable, Iterator, Mapping, Sequence

try:  # Keep upstream environments importable before the SymPy env is active.
    import sympy as sp
except ModuleNotFoundError:  # pragma: no cover - exercised only without deps
    sp = None


DEGREE = 24
DEFAULT_TRANSLATION_RADIUS = 2


class IGP24Error(ValueError):
    """Base error for IGP24 candidate handling."""


class ExactScoreTimeout(TimeoutError):
    """Raised when exact candidate analysis exceeds the configured timeout."""


@dataclass(frozen=True)
class ModFactorizationPattern:
    prime: int
    degrees: tuple[int, ...]


@dataclass(frozen=True)
class CandidateAnalysis:
    coefficients: tuple[int, ...]
    exported_coefficients: tuple[int, ...]
    polynomial_string: str
    real_root_count: int | None
    discriminant: int | None
    log_abs_discriminant: float | None
    coefficient_height: int | None
    irreducible: bool | None
    squarefree: bool | None
    sampled_primes: tuple[int, ...]
    mod_p_factorization_degree_patterns: tuple[ModFactorizationPattern, ...]
    canonical_coefficients: tuple[int, ...]
    canonical_hash: str
    canonical_translation: int
    valid: bool
    rejection_reason: str | None
    score_components: dict[str, float | int | bool] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


def _require_sympy() -> Any:
    if sp is None:
        raise IGP24Error("missing_sympy_dependency")
    return sp


def _symbol() -> Any:
    sympy = _require_sympy()
    return sympy.Symbol("x")


def _coerce_integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise IGP24Error("coefficients_must_be_integers")
    return int(value)


def validate_coefficients(coefficients: Sequence[Any], degree: int = DEGREE) -> tuple[int, ...]:
    """Validate and normalize the [a0, ..., a23] coefficient vector."""

    try:
        values = tuple(_coerce_integer(c) for c in coefficients)
    except TypeError as exc:
        raise IGP24Error("coefficients_must_be_a_sequence") from exc
    if len(values) != degree:
        raise IGP24Error(f"wrong_length:{len(values)}")
    return values


def export_coefficients(coefficients: Sequence[Any]) -> list[int]:
    """Return the SAIR-style [a0, ..., a23, 1] export vector."""

    return list(validate_coefficients(coefficients)) + [1]


def coefficient_height(coefficients: Sequence[Any]) -> int:
    values = validate_coefficients(coefficients)
    return max(abs(c) for c in values)


def construct_polynomial(coefficients: Sequence[Any]) -> Any:
    """Construct a SymPy Poly over ZZ from [a0, ..., a23]."""

    sympy = _require_sympy()
    values = validate_coefficients(coefficients)
    x = _symbol()
    expr = x**DEGREE
    for i, coeff in enumerate(values):
        if coeff:
            expr += coeff * x**i
    return sympy.Poly(expr, x, domain=sympy.ZZ)


def polynomial_string(coefficients: Sequence[Any]) -> str:
    sympy = _require_sympy()
    return sympy.sstr(construct_polynomial(coefficients).as_expr())


def is_squarefree(coefficients: Sequence[Any]) -> bool:
    poly = construct_polynomial(coefficients)
    return poly.gcd(poly.diff()).degree() == 0


def is_irreducible_over_q(coefficients: Sequence[Any]) -> bool:
    poly = construct_polynomial(coefficients)
    return bool(poly.is_irreducible)


def exact_discriminant(coefficients: Sequence[Any]) -> int:
    return int(construct_polynomial(coefficients).discriminant())


def real_root_count(coefficients: Sequence[Any]) -> int:
    sympy = _require_sympy()
    poly = construct_polynomial(coefficients)
    return int(poly.count_roots(inf=-sympy.oo, sup=sympy.oo))


def translate_coefficients(coefficients: Sequence[Any], k: int) -> tuple[int, ...]:
    """Return coefficients for f(x + k), preserving the fixed leading 1."""

    if not isinstance(k, Integral):
        raise IGP24Error("translation_must_be_integer")
    values = validate_coefficients(coefficients)
    shift = int(k)
    full = values + (1,)
    translated = []
    for output_degree in range(DEGREE):
        translated.append(
            sum(
                full[input_degree]
                * math.comb(input_degree, output_degree)
                * shift ** (input_degree - output_degree)
                for input_degree in range(output_degree, DEGREE + 1)
            )
        )
    return tuple(translated)


def canonicalize_under_translations(
    coefficients: Sequence[Any],
    radius: int = DEFAULT_TRANSLATION_RADIUS,
    coeff_bound: int | None = None,
) -> tuple[tuple[int, ...], int]:
    """Choose a stable representative among small translations f(x + k).

    The representative minimizes coefficient height first, then lexicographic
    order. If coeff_bound is supplied, representatives exceeding the bound are
    ignored unless every candidate exceeds it.
    """

    values = validate_coefficients(coefficients)
    radius = max(0, int(radius))
    candidates: list[tuple[tuple[int, ...], int]] = []
    overflow_candidates: list[tuple[tuple[int, ...], int]] = []
    for k in range(-radius, radius + 1):
        try:
            translated = translate_coefficients(values, k)
        except IGP24Error:
            continue
        target = overflow_candidates if coeff_bound is not None and coefficient_height(translated) > coeff_bound else candidates
        target.append((translated, k))
    if not candidates:
        candidates = overflow_candidates or [(values, 0)]
    best_coeffs, best_k = min(candidates, key=lambda item: (coefficient_height(item[0]), item[0]))
    return best_coeffs, best_k


def stable_canonical_hash(
    coefficients: Sequence[Any],
    radius: int = DEFAULT_TRANSLATION_RADIUS,
    coeff_bound: int | None = None,
) -> str:
    canonical, _ = canonicalize_under_translations(coefficients, radius=radius, coeff_bound=coeff_bound)
    payload = json.dumps({"degree": DEGREE, "coefficients": list(canonical)}, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _small_primes(limit: int) -> list[int]:
    if limit < 2:
        return []
    primes: list[int] = []
    for n in range(2, limit + 1):
        for p in primes:
            if p * p > n:
                break
            if n % p == 0:
                break
        else:
            primes.append(n)
            continue
        if primes and n % primes[-1] == 0:
            continue
    # The loop above is intentionally simple; re-check to avoid edge bugs.
    out: list[int] = []
    for n in range(2, limit + 1):
        if all(n % p for p in range(2, int(math.sqrt(n)) + 1)):
            out.append(n)
    return out


def mod_p_factorization_patterns(coefficients: Sequence[Any], discriminant: int, prime_limit: int) -> tuple[ModFactorizationPattern, ...]:
    """Factor modulo small unramified primes and return degree patterns.

    These are Frobenius cycle-type proxies only. They are not exact Galois
    labels and must not be reported as such.
    """

    sympy = _require_sympy()
    x = _symbol()
    poly = construct_polynomial(coefficients)
    patterns: list[ModFactorizationPattern] = []
    for prime in _small_primes(int(prime_limit)):
        if discriminant % prime == 0:
            continue
        mod_poly = sympy.Poly(poly.as_expr(), x, modulus=prime)
        _, factors = mod_poly.factor_list()
        degrees: list[int] = []
        for factor, exponent in factors:
            degrees.extend([int(factor.degree())] * int(exponent))
        patterns.append(ModFactorizationPattern(prime=prime, degrees=tuple(sorted(degrees))))
    return tuple(patterns)


@contextlib.contextmanager
def _timeout(seconds: float | None) -> Iterator[None]:
    if not seconds or seconds <= 0 or not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        yield
        return

    def handler(_signum: int, _frame: Any) -> None:
        raise ExactScoreTimeout("exact_score_timeout")

    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def _invalid_analysis(raw_coefficients: Sequence[Any], reason: str, warnings: Iterable[str] = ()) -> CandidateAnalysis:
    try:
        coefficients = tuple(int(c) for c in raw_coefficients)
    except Exception:
        coefficients = ()
    canonical = coefficients if len(coefficients) == DEGREE else ()
    canonical_hash = ""
    if len(canonical) == DEGREE:
        try:
            canonical_hash = stable_canonical_hash(canonical)
        except Exception:
            canonical_hash = hashlib.sha256(repr(canonical).encode("utf-8")).hexdigest()
    return CandidateAnalysis(
        coefficients=coefficients,
        exported_coefficients=tuple(export_coefficients(coefficients)) if len(coefficients) == DEGREE else (),
        polynomial_string="",
        real_root_count=None,
        discriminant=None,
        log_abs_discriminant=None,
        coefficient_height=coefficient_height(coefficients) if len(coefficients) == DEGREE else None,
        irreducible=None,
        squarefree=None,
        sampled_primes=(),
        mod_p_factorization_degree_patterns=(),
        canonical_coefficients=canonical,
        canonical_hash=canonical_hash,
        canonical_translation=0,
        valid=False,
        rejection_reason=reason,
        score_components={},
        warnings=tuple(warnings),
    )


def analyze_candidate(
    coefficients: Sequence[Any],
    coeff_bound: int,
    prime_limit: int,
    exact_score_timeout: float | None = None,
    translation_radius: int = DEFAULT_TRANSLATION_RADIUS,
) -> CandidateAnalysis:
    """Run exact stage-0 validation plus modular proxy feature extraction."""

    try:
        with _timeout(exact_score_timeout):
            values = validate_coefficients(coefficients)
            height = coefficient_height(values)
            if values[0] == 0:
                return _invalid_analysis(values, "zero_constant_term")
            if height > int(coeff_bound):
                return _invalid_analysis(values, "coefficient_height_exceeds_bound")

            poly_string = polynomial_string(values)
            squarefree = is_squarefree(values)
            if not squarefree:
                return _invalid_analysis(values, "not_squarefree")
            irreducible = is_irreducible_over_q(values)
            if not irreducible:
                return _invalid_analysis(values, "reducible_over_q")

            discriminant = exact_discriminant(values)
            if discriminant == 0:
                return _invalid_analysis(values, "zero_discriminant")
            log_abs_discriminant = math.log(abs(discriminant))

            roots = real_root_count(values)
            patterns = mod_p_factorization_patterns(values, discriminant, prime_limit)
            canonical, translation = canonicalize_under_translations(values, radius=translation_radius, coeff_bound=coeff_bound)
            canonical_hash = stable_canonical_hash(values, radius=translation_radius, coeff_bound=coeff_bound)
            return CandidateAnalysis(
                coefficients=values,
                exported_coefficients=tuple(export_coefficients(values)),
                polynomial_string=poly_string,
                real_root_count=roots,
                discriminant=discriminant,
                log_abs_discriminant=log_abs_discriminant,
                coefficient_height=height,
                irreducible=irreducible,
                squarefree=squarefree,
                sampled_primes=tuple(pattern.prime for pattern in patterns),
                mod_p_factorization_degree_patterns=patterns,
                canonical_coefficients=canonical,
                canonical_hash=canonical_hash,
                canonical_translation=translation,
                valid=True,
                rejection_reason=None,
                score_components={},
            )
    except ExactScoreTimeout:
        return _invalid_analysis(coefficients, "exact_score_timeout")
    except IGP24Error as exc:
        return _invalid_analysis(coefficients, str(exc))
    except Exception as exc:  # SymPy can raise specialized algebra errors.
        return _invalid_analysis(coefficients, f"analysis_failed:{type(exc).__name__}")


def score_candidate(
    coefficients: Sequence[Any],
    coeff_bound: int,
    target_r: int | None = None,
    target_t: str | None = None,
    target_label: str | None = None,
    target_label_set: Iterable[str] | None = None,
    group_compatibility: Mapping[str, Any] | None = None,
    prime_limit: int = 31,
    discriminant_weight: float = 1.0,
    height_weight: float = 1.0,
    cycle_diversity_weight: float = 5.0,
    exact_score_timeout: float | None = None,
    seen_hashes: Iterable[str] | None = None,
    translation_radius: int = DEFAULT_TRANSLATION_RADIUS,
) -> tuple[float, CandidateAnalysis]:
    """Return an Axplorer-compatible score and the analysis that produced it."""

    analysis = analyze_candidate(
        coefficients,
        coeff_bound=coeff_bound,
        prime_limit=prime_limit,
        exact_score_timeout=exact_score_timeout,
        translation_radius=translation_radius,
    )
    if not analysis.valid:
        return -1.0, analysis

    seen = set(seen_hashes or ())
    diversity = len({pattern.degrees for pattern in analysis.mod_p_factorization_degree_patterns})
    root_component = 0.0
    if target_r is not None:
        target_r_distance = abs(int(target_r) - int(analysis.real_root_count or 0))
        root_component = 250.0 / (1.0 + target_r_distance)
    else:
        target_r_distance = -1
    novelty_component = 25.0 if analysis.canonical_hash not in seen else 0.0

    target_labels = set(str(label) for label in (target_label_set or []) if label)
    if target_label:
        target_labels.add(str(target_label))
    if target_t:
        target_labels.add(str(target_t))

    base_score = 10_000.0
    cycle_component = float(cycle_diversity_weight) * diversity
    discriminant_penalty = float(discriminant_weight) * float(analysis.log_abs_discriminant or 0.0)
    height_penalty = float(height_weight) * float(analysis.coefficient_height or 0.0)
    raw_score = (
        base_score
        + root_component
        + novelty_component
        + cycle_component
        - discriminant_penalty
        - height_penalty
    )
    warnings = list(analysis.warnings)
    compatibility_penalty = 0.0
    target_label_applied = False
    if target_labels:
        if group_compatibility is not None:
            compatible_labels = set(
                str(label)
                for label in (
                    group_compatibility.get("indexed_target_labels_not_ruled_out")
                    or group_compatibility.get("compatible_labels")
                    or []
                )
            )
            target_label_applied = True
            if target_labels.isdisjoint(compatible_labels):
                components = {
                    "base_score": base_score,
                    "target_r_bonus": root_component,
                    "target_r_distance": target_r_distance,
                    "novelty_bonus": novelty_component,
                    "is_novel": analysis.canonical_hash not in seen,
                    "cycle_diversity_count": diversity,
                    "cycle_diversity_bonus": cycle_component,
                    "log_abs_discriminant_penalty": discriminant_penalty,
                    "height_penalty": height_penalty,
                    "target_label_applied": True,
                    "target_label_rejected": True,
                    "raw_score": -1.0,
                    "final_score": -1.0,
                }
                warnings.append("target_label_incompatible_with_group_cycle_evidence")
                return -1.0, replace(analysis, score_components=components, warnings=tuple(warnings))
            compatible_count = int(
                group_compatibility.get("indexed_target_survivor_count")
                or group_compatibility.get("compatible_label_count")
                or len(compatible_labels)
            )
            compatibility_penalty = min(250.0, math.log1p(max(0, compatible_count - 1)) * 25.0)
        else:
            warnings.append("target_label_not_applied_missing_group_compatibility_index")

    raw_score -= compatibility_penalty
    score = max(0.0, raw_score)
    components: dict[str, float | int | bool] = {
        "base_score": base_score,
        "target_r_bonus": root_component,
        "target_r_distance": target_r_distance,
        "novelty_bonus": novelty_component,
        "is_novel": analysis.canonical_hash not in seen,
        "cycle_diversity_count": diversity,
        "cycle_diversity_bonus": cycle_component,
        "log_abs_discriminant_penalty": discriminant_penalty,
        "height_penalty": height_penalty,
        "target_label_requested": bool(target_labels),
        "target_label_applied": target_label_applied,
        "target_label_ambiguity_penalty": compatibility_penalty,
        "raw_score": raw_score,
        "final_score": score,
    }
    return score, replace(analysis, score_components=components, warnings=tuple(warnings))


def analysis_to_record(
    analysis: CandidateAnalysis,
    score: float,
    target_r: int | None = None,
    target_t: str | None = None,
    experiment_name: str | None = None,
    verification_status: str | None = None,
    generation_metadata: dict[str, Any] | None = None,
    local_search_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = verification_status or ("proxy_scored" if analysis.valid else "rejected")
    payload = asdict(analysis)
    payload["mod_p_factorization_degree_patterns"] = [
        {"prime": pattern.prime, "degrees": list(pattern.degrees)} for pattern in analysis.mod_p_factorization_degree_patterns
    ]
    payload["coefficients"] = list(analysis.coefficients)
    payload["canonical_coefficients"] = list(analysis.canonical_coefficients)
    payload["exported_coefficients"] = list(analysis.exported_coefficients)
    payload["score"] = score
    payload["score_components"] = dict(analysis.score_components)
    payload["generation_metadata"] = generation_metadata or {}
    payload["local_search_metadata"] = local_search_metadata or {}
    payload["target_metadata"] = {"target_r": target_r, "target_t": target_t}
    payload["experiment_name"] = experiment_name
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    payload["verification_status"] = status
    payload["verified_group_label"] = None
    payload["errors"] = [] if analysis.valid else [analysis.rejection_reason]
    payload["warnings"] = list(analysis.warnings)
    return payload
