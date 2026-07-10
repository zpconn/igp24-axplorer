#!/usr/bin/env python3
"""Search exact ``h(x^6)`` families for lower-discriminant 24T9993 candidates.

This is an offline construction experiment.  It performs exact local algebra,
reads a local SAIR snapshot, and may read a local complete GAP cycle index.  It
does not call SAIR, does not call the public Magma service, and cannot submit.
Compatibility is necessary target-exclusion evidence only; the exact degree-24
label remains pending until a separate exact verifier resolves it.
"""

from __future__ import annotations

import argparse
import json
import math
import signal
import sys
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import sympy as sp

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.adaptive_frobenius import factorization_degrees_mod_prime, small_primes  # noqa: E402
from src.igp24.constructions.quartic_x6_descent import (  # noqa: E402
    TARGET_9993_LABEL,
    TARGET_9993_OUTER_ACTION,
    TARGET_9993_PAIR,
    QuarticX6Parameters,
    coefficient_support,
    is_exact_quartic_x6_support,
    iter_alternating_sign_grid,
    lift_quartic_x6,
    outer_galois_profile,
    positive_real_root_count,
    quartic_discriminant,
    quartic_x6_polynomial_discriminant_abs,
)
from src.igp24.group_compatibility import (  # noqa: E402
    GroupCycleIndex,
    candidate_compatibility,
    cycle_type_key,
    progress_states_for_pairs,
    read_jsonl,
)
from src.igp24.polynomial import analysis_to_record, score_candidate  # noqa: E402


DEFAULT_GROUP_INDEX = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/group_index_workflow_phase3/"
    "full_degree24_universe_local_gap_20260709/degree24_group_cycle_index.sqlite"
)
DEFAULT_PROGRESS = (
    REPO_ROOT
    / "data/igp24/axg122_quartic9993_descent_20260710/sair_sync_initial/sair_label_progress.jsonl"
)
DEFAULT_SUBMISSIONS = (
    REPO_ROOT
    / "data/igp24/axg122_quartic9993_descent_20260710/sair_sync_initial/sair_submission_rows.jsonl"
)

SUMMARY_JSON = "quartic_x6_discriminant_descent_summary.json"
REPORT_MD = "quartic_x6_discriminant_descent_report.md"
CANDIDATES_JSONL = "quartic_x6_discriminant_descent_candidates.jsonl"
REJECTED_JSONL = "quartic_x6_discriminant_descent_rejected.jsonl"
EXACT_LABEL_QUEUE_JSONL = "quartic_x6_exact_label_queue.jsonl"
EXACT_LABEL_QUEUE_TXT = "quartic_x6_exact_label_queue_coefficients.txt"

SAFETY_NOTE = (
    "Offline exact h(x^6) discriminant descent. No network call, public-calculator POST, "
    "SAIR POST, or live submission is implemented by this script."
)


class NfdiscTimeout(TimeoutError):
    pass


@contextmanager
def nfdisc_timeout(seconds: float | None) -> Iterator[None]:
    if seconds is None or float(seconds) <= 0:
        yield
        return

    def handler(_signum: int, _frame: Any) -> None:
        raise NfdiscTimeout("sympy_nfdisc_timeout")

    previous_handler = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def coefficient_line(values: Iterable[int]) -> str:
    return ",".join(str(int(value)) for value in values)


def parameters_from_exported_coefficients(values: Iterable[int]) -> QuarticX6Parameters | None:
    coefficients = [int(value) for value in values]
    if len(coefficients) != 25 or coefficients[-1] != 1:
        return None
    if not is_exact_quartic_x6_support(coefficients):
        return None
    return QuarticX6Parameters(
        a=coefficients[18],
        b=coefficients[12],
        c=coefficients[6],
        d=coefficients[0],
    )


def load_known_submission_state(paths: Iterable[Path]) -> dict[str, Any]:
    by_hash: dict[str, dict[str, Any]] = {}
    by_reciprocal_outer: dict[tuple[int, int, int, int], list[dict[str, Any]]] = {}
    for path in paths:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            hash_value = str(row.get("canonical_hash") or row.get("candidate_hash") or "")
            if hash_value:
                by_hash[hash_value] = {
                    "canonical_hash": hash_value,
                    "submission_id": row.get("submission_id") or row.get("submissionId"),
                    "status": row.get("status"),
                    "label": row.get("label") or row.get("verified_group_label"),
                    "r": row.get("r") or row.get("real_root_count"),
                    "pair_key": row.get("pair_key"),
                    "field_disc_abs": row.get("field_disc_abs") or row.get("fieldDiscAbs"),
                    "source_path": str(path),
                }
            polynomial = row.get("polynomial")
            if not isinstance(polynomial, str):
                continue
            try:
                parameters = parameters_from_exported_coefficients(
                    int(part.strip()) for part in polynomial.split(",") if part.strip()
                )
            except (TypeError, ValueError):
                parameters = None
            if parameters is None or parameters.d != 1:
                continue
            by_reciprocal_outer.setdefault(parameters.reciprocal_key, []).append(
                {
                    "canonical_hash": hash_value or None,
                    "submission_id": row.get("submission_id") or row.get("submissionId"),
                    "label": row.get("label"),
                    "r": row.get("r"),
                    "field_disc_abs": row.get("field_disc_abs") or row.get("fieldDiscAbs"),
                    "outer_parameters": {
                        "a": parameters.a,
                        "b": parameters.b,
                        "c": parameters.c,
                        "d": parameters.d,
                    },
                    "source_path": str(path),
                }
            )
    return {
        "by_hash": by_hash,
        "by_reciprocal_outer": by_reciprocal_outer,
    }


def current_pair_progress(progress_rows: list[dict[str, Any]], pair_key: str) -> dict[str, Any]:
    return progress_states_for_pairs([pair_key], progress_rows)[pair_key]


def compute_exact_nfdisc(
    exported_coefficients: list[int],
    *,
    polynomial_discriminant_abs: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    x = sp.Symbol("x")
    polynomial = sp.Poly(
        sum(int(coefficient) * x**power for power, coefficient in enumerate(exported_coefficients)),
        x,
        domain=sp.ZZ,
    )
    try:
        with nfdisc_timeout(timeout_seconds):
            field = sp.QQ.alg_field_from_poly(polynomial)
            exact_nfdisc_abs = abs(int(field.discriminant()))
        index_square = int(polynomial_discriminant_abs) // exact_nfdisc_abs
        index_factor = math.isqrt(index_square)
        if index_factor * index_factor != index_square:
            raise ValueError("polynomial_discriminant_to_nfdisc_quotient_not_square")
        return {
            "status": "ok",
            "exact_nfdisc_abs": exact_nfdisc_abs,
            "exact_nfdisc_source": "sympy_algebraic_field_discriminant",
            "polynomial_discriminant_abs": int(polynomial_discriminant_abs),
            "index_square": index_square,
            "index_factor": index_factor,
            "runtime_seconds": time.perf_counter() - started,
        }
    except Exception as exc:
        return {
            "status": "timeout" if isinstance(exc, NfdiscTimeout) else "error",
            "exact_nfdisc_abs": None,
            "exact_nfdisc_source": None,
            "polynomial_discriminant_abs": int(polynomial_discriminant_abs),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "runtime_seconds": time.perf_counter() - started,
        }


def target_specific_frobenius_screen(
    record: dict[str, Any],
    *,
    target_label: str,
    group_index: GroupCycleIndex,
    usable_prime_budget: int,
    minimum_usable_primes: int,
) -> dict[str, Any]:
    """Use unramified primes to rule out one exact indexed target cheaply."""

    target = group_index.records_for_labels([target_label]).get(target_label)
    if target is None:
        raise ValueError(f"target label {target_label} is absent from the group index")
    coefficients = tuple(int(value) for value in record["coefficients"])
    discriminant_abs = abs(int(record["polynomial_discriminant_abs"]))
    discriminant_square = math.isqrt(discriminant_abs) ** 2 == discriminant_abs
    if target.parity == "even" and not discriminant_square:
        return {
            "target_label": target_label,
            "target_label_not_ruled_out": False,
            "sufficient_evidence": False,
            "stop_reason": "target_even_but_polynomial_discriminant_nonsquare",
            "usable_prime_count": 0,
            "skipped_ramified_primes": [],
            "patterns": [],
            "soundness": "necessary_target_exclusion_only",
        }

    target_cycles = set(target.cycle_types)
    patterns: list[dict[str, Any]] = []
    skipped_ramified: list[int] = []
    incompatible: dict[str, Any] | None = None
    for prime in small_primes():
        if len(patterns) >= int(usable_prime_budget):
            break
        if discriminant_abs % int(prime) == 0:
            skipped_ramified.append(int(prime))
            continue
        degrees = factorization_degrees_mod_prime(coefficients, int(prime))
        cycle = cycle_type_key(degrees)
        observation = {"prime": int(prime), "degrees": list(degrees), "cycle_type": cycle}
        patterns.append(observation)
        if cycle not in target_cycles:
            incompatible = observation
            break

    target_retained = incompatible is None
    sufficient = target_retained and len(patterns) >= int(minimum_usable_primes)
    return {
        "target_label": target_label,
        "target_group_order": target.order,
        "target_group_parity": target.parity,
        "target_group_block_sizes": list(target.block_sizes),
        "target_label_not_ruled_out": target_retained,
        "sufficient_evidence": sufficient,
        "stop_reason": (
            "incompatible_unramified_cycle"
            if incompatible is not None
            else "evidence_budget_exhausted"
            if sufficient
            else "insufficient_usable_primes"
        ),
        "usable_prime_count": len(patterns),
        "skipped_ramified_primes": skipped_ramified,
        "incompatible_observation": incompatible,
        "patterns": patterns,
        "soundness": "adaptive_unramified_frobenius_cycle_target_exclusion_only",
    }


def rejection_row(parameters: QuarticX6Parameters, reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "outer_parameters": {"a": parameters.a, "b": parameters.b, "c": parameters.c, "d": parameters.d},
        "outer_reciprocal_key": list(parameters.reciprocal_key),
        "outer_quartic_discriminant": quartic_discriminant(parameters),
        "rejection_reason": reason,
        **extra,
    }


def render_report(summary: dict[str, Any], candidates: list[dict[str, Any]], queue: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Quartic-in-x6 Discriminant Descent",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Safety: {SAFETY_NOTE}",
        f"- Target: `{summary['target_pair']}`",
        f"- Fresh pair state: `{summary['target_progress_state']}`; teams `{summary['target_team_count']}`",
        f"- Current best nfdisc: `{summary['current_best_nfdisc_abs']}`",
        f"- Exact outer action required: `{summary['target_outer_action']['induced_action_transitive_id']}` / `S4`",
        f"- Grid rows considered: `{summary['grid_candidate_count']}`",
        f"- Four-positive-root rows: `{summary['four_positive_outer_count']}`",
        f"- Exact outer-S4 rows: `{summary['outer_s4_count']}`",
        f"- Exact nfdisc rows: `{summary['exact_nfdisc_count']}`",
        f"- Target-cycle survivors: `{summary['target_cycle_survivor_count']}`",
        f"- Material nfdisc-improvement queues: `{summary['exact_label_queue_count']}`",
        f"- Live submission recommended: `{summary['live_submission_recommended_now']}`",
        "",
        "## Best Exact Local Rows",
        "",
        "| rank | hash | outer (a,b,c,d) | outer disc | nfdisc | ratio to best | index | target retained | exact label |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for index, row in enumerate(candidates[:30], start=1):
        outer = row["outer_parameters"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`({outer['a']},{outer['b']},{outer['c']},{outer['d']})`",
                    str(row.get("outer_quartic_discriminant")),
                    str(row.get("exact_nfdisc_abs")),
                    f"{float(row.get('nfdisc_ratio_to_current_best') or 0.0):.6g}",
                    str(row.get("polynomial_order_index")),
                    f"`{row.get('target_label_not_ruled_out')}`",
                    "pending",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Exact-Label Queue",
            "",
            f"`{len(queue)}` rows beat the current nfdisc locally while retaining the target through the configured prime budget.",
            "They are review-only until an exact degree-24 label is obtained. Compatibility is not an exact-label claim.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--group_index", type=Path, default=DEFAULT_GROUP_INDEX)
    parser.add_argument("--progress_jsonl", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--known_submission_jsonl", type=Path, action="append")
    parser.add_argument("--target_label", default=TARGET_9993_LABEL)
    parser.add_argument("--target_pair", default=TARGET_9993_PAIR)
    parser.add_argument("--a_abs_min", type=int, default=2)
    parser.add_argument("--a_abs_max", type=int, default=40)
    parser.add_argument("--b_min", type=int, default=1)
    parser.add_argument("--b_max", type=int, default=160)
    parser.add_argument("--c_abs_min", type=int, default=2)
    parser.add_argument("--c_abs_max", type=int, default=40)
    parser.add_argument("--maximum_quartic_discriminant", type=int, default=500_000)
    parser.add_argument("--maximum_nfdisc_evaluations", type=int, default=256)
    parser.add_argument("--nfdisc_timeout", type=float, default=3.0)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--usable_prime_budget", type=int, default=40)
    parser.add_argument("--minimum_usable_primes", type=int, default=20)
    parser.add_argument(
        "--frobenius_screen_ratio",
        type=float,
        default=2.0,
        help="Run target-cycle evidence only when exact nfdisc/current-best is at most this ratio.",
    )
    parser.add_argument("--candidate_limit", type=int, default=60)
    parser.add_argument("--material_improvement_ratio", type=float, default=1.0)
    parser.add_argument(
        "--internal_frontier_nfdisc",
        type=int,
        default=10723488292100241361294296648700284370944,
        help="Previous exact local family frontier; improvements may become weight-1 exploration evidence.",
    )
    args = parser.parse_args(argv)

    if not args.group_index.exists():
        raise FileNotFoundError(args.group_index)
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl.exists() else []
    progress = current_pair_progress(progress_rows, args.target_pair)
    current_best_nfdisc = progress.get("minimum_disc_abs")
    if current_best_nfdisc in (None, ""):
        raise ValueError(f"fresh progress has no current discriminant for {args.target_pair}")
    current_best_nfdisc_abs = int(current_best_nfdisc)

    known_paths = args.known_submission_jsonl or [DEFAULT_SUBMISSIONS]
    known = load_known_submission_state(known_paths)
    group_index = GroupCycleIndex(args.group_index)
    scope = group_index.scope_metadata()
    if not scope.get("global_index_complete"):
        raise ValueError("quartic x6 descent requires the complete degree-24 group index")

    rejection_counts: Counter[str] = Counter()
    rejected: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()

    grid = list(
        iter_alternating_sign_grid(
            a_abs_min=args.a_abs_min,
            a_abs_max=args.a_abs_max,
            b_min=args.b_min,
            b_max=args.b_max,
            c_abs_min=args.c_abs_min,
            c_abs_max=args.c_abs_max,
            d=1,
            maximum_quartic_discriminant=args.maximum_quartic_discriminant,
            deduplicate_reciprocals=True,
        )
    )
    stage_counts["grid_candidate"] = len(grid)
    nfdisc_evaluations = 0
    seen_hashes: set[str] = set()
    for parameters in grid:
        if positive_real_root_count(parameters) != 4:
            rejection_counts["outer_not_four_positive_roots"] += 1
            continue
        stage_counts["four_positive_outer"] += 1

        profile = outer_galois_profile(parameters)
        if not profile.get("outer_action_matches_24T9993"):
            reason = "outer_action_not_s4"
            rejection_counts[reason] += 1
            if len(rejected) < 500:
                rejected.append(rejection_row(parameters, reason, outer_galois_profile=profile))
            continue
        stage_counts["outer_s4"] += 1
        if nfdisc_evaluations >= int(args.maximum_nfdisc_evaluations):
            rejection_counts["nfdisc_evaluation_budget_exhausted"] += 1
            continue

        coefficients = lift_quartic_x6(parameters)
        polynomial_discriminant_abs = quartic_x6_polynomial_discriminant_abs(parameters)
        score, analysis = score_candidate(
            coefficients,
            coeff_bound=max(abs(value) for value in coefficients),
            target_r=8,
            target_label_set=[args.target_label],
            prime_limit=11,
            exact_score_timeout=float(args.exact_score_timeout),
            translation_radius=2,
        )
        if not analysis.valid or analysis.real_root_count != 8 or not analysis.irreducible or not analysis.squarefree:
            reason = str(analysis.rejection_reason or "degree24_local_invalid")
            rejection_counts[reason] += 1
            if len(rejected) < 500:
                rejected.append(rejection_row(parameters, reason))
            continue
        stage_counts["degree24_local_valid"] += 1

        known_submission = known["by_hash"].get(analysis.canonical_hash)
        if known_submission is not None:
            reason = "known_submission_canonical_hash"
            rejection_counts[reason] += 1
            if len(rejected) < 500:
                rejected.append(
                    rejection_row(
                        parameters,
                        reason,
                        canonical_hash=analysis.canonical_hash,
                        known_submission=known_submission,
                    )
                )
            continue
        if analysis.canonical_hash in seen_hashes:
            rejection_counts["duplicate_generated_canonical_hash"] += 1
            continue
        seen_hashes.add(analysis.canonical_hash)

        reciprocal_history = known["by_reciprocal_outer"].get(parameters.reciprocal_key) or []
        if reciprocal_history:
            reason = "known_reciprocal_outer_field_equivalent"
            rejection_counts[reason] += 1
            if len(rejected) < 500:
                rejected.append(
                    rejection_row(
                        parameters,
                        reason,
                        canonical_hash=analysis.canonical_hash,
                        known_submission_equivalents=reciprocal_history,
                    )
                )
            continue

        nfdisc_evaluations += 1
        exact_nfdisc = compute_exact_nfdisc(
            list(analysis.exported_coefficients),
            polynomial_discriminant_abs=polynomial_discriminant_abs,
            timeout_seconds=float(args.nfdisc_timeout),
        )
        if exact_nfdisc["status"] != "ok":
            reason = f"exact_nfdisc_{exact_nfdisc['status']}"
            rejection_counts[reason] += 1
            if len(rejected) < 500:
                rejected.append(rejection_row(parameters, reason, exact_nfdisc=exact_nfdisc))
            continue
        stage_counts["exact_nfdisc"] += 1

        metadata = {
            "construction_family": "quartic_in_x6_discriminant_descent",
            "template_family": "exact_h_x6_outer_s4",
            "perturbation_mode": "outer_quartic_integer_grid",
            "structure_preservation": "exact h(x^6) support with no off-core perturbations",
            "target_pair": args.target_pair,
            "target_label": args.target_label,
            "target_outer_action": dict(TARGET_9993_OUTER_ACTION),
            "outer_parameters": {
                "a": parameters.a,
                "b": parameters.b,
                "c": parameters.c,
                "d": parameters.d,
            },
            "outer_reciprocal_key": list(parameters.reciprocal_key),
            "outer_quartic_discriminant": quartic_discriminant(parameters),
            "outer_galois_profile": profile,
            "support_after_lift": list(coefficient_support(coefficients)),
            "exact_composed_support_divisor": 6,
        }
        record = analysis_to_record(
            analysis,
            score,
            target_r=8,
            target_t=args.target_label,
            experiment_name="quartic_x6_discriminant_descent",
            verification_status="exact_local_pending_degree24_label",
            generation_metadata=metadata,
            local_search_metadata={"offline": True, "grid_rank": nfdisc_evaluations},
        )
        record["record_type"] = "igp24_quartic_x6_discriminant_descent_candidate"
        record["schema_version"] = 1
        record["outer_parameters"] = metadata["outer_parameters"]
        record["outer_reciprocal_key"] = metadata["outer_reciprocal_key"]
        record["outer_quartic_discriminant"] = metadata["outer_quartic_discriminant"]
        record["outer_galois_profile"] = profile
        record["polynomial_discriminant_abs"] = polynomial_discriminant_abs
        record["exact_nfdisc_status"] = "ok"
        record["exact_nfdisc_abs"] = int(exact_nfdisc["exact_nfdisc_abs"])
        record["exact_nfdisc_source"] = exact_nfdisc["exact_nfdisc_source"]
        record["polynomial_order_index"] = int(exact_nfdisc["index_factor"])
        record["nfdisc_runtime_seconds"] = exact_nfdisc["runtime_seconds"]
        record["nfdisc_ratio_to_current_best"] = record["exact_nfdisc_abs"] / current_best_nfdisc_abs
        record["internal_frontier_nfdisc_abs"] = int(args.internal_frontier_nfdisc)
        record["internal_frontier_ratio"] = record["exact_nfdisc_abs"] / int(args.internal_frontier_nfdisc)
        record["internal_frontier_improvement"] = record["exact_nfdisc_abs"] < int(args.internal_frontier_nfdisc)
        record["exact_degree24_label_status"] = "pending"
        record["verified_group_label"] = None

        should_screen = bool(
            record["nfdisc_ratio_to_current_best"] <= float(args.frobenius_screen_ratio)
            or record["internal_frontier_improvement"]
        )
        if should_screen:
            screen = target_specific_frobenius_screen(
                record,
                target_label=args.target_label,
                group_index=group_index,
                usable_prime_budget=int(args.usable_prime_budget),
                minimum_usable_primes=int(args.minimum_usable_primes),
            )
        else:
            screen = {
                "target_label": args.target_label,
                "target_label_not_ruled_out": None,
                "sufficient_evidence": False,
                "stop_reason": "not_run_nfdisc_outside_competitive_screen_ratio",
                "usable_prime_count": 0,
                "skipped_ramified_primes": [],
                "patterns": [],
                "soundness": "not_run",
            }
        record["target_specific_frobenius"] = screen
        record["mod_p_factorization_degree_patterns"] = [
            {"prime": item["prime"], "degrees": item["degrees"]} for item in screen["patterns"]
        ]
        record["target_label_not_ruled_out"] = screen["target_label_not_ruled_out"]
        record["sufficient_adaptive_frobenius_evidence"] = bool(screen["sufficient_evidence"])
        if record["target_label_not_ruled_out"] is True:
            stage_counts["target_cycle_survivor"] += 1

        compatibility = (
            candidate_compatibility(record, group_index, progress_rows=progress_rows)
            if screen["patterns"]
            else None
        )
        record["group_compatibility"] = compatibility
        record["target_pair_valuable_not_ruled_out"] = (
            args.target_pair in set(compatibility.get("valuable_targets_not_ruled_out") or [])
            if compatibility is not None
            else None
        )
        material = record["nfdisc_ratio_to_current_best"] < float(args.material_improvement_ratio)
        record["material_nfdisc_improvement_possible"] = material
        record["best_case_points_status"] = "target_outcome_only_exact_label_pending"
        record["expected_points_status"] = "unavailable_uncalibrated"
        record["estimated_expected_points"] = None
        queue_eligible = bool(
            material
            and record["target_label_not_ruled_out"] is True
            and record["sufficient_adaptive_frobenius_evidence"]
            and record["target_pair_valuable_not_ruled_out"] is True
        )
        record["exact_label_queue_eligible"] = queue_eligible
        record["eligible_for_packet"] = False
        record["live_submission_recommended_now"] = False
        record["submission_recommendation"] = (
            "false_pending_exact_degree24_label"
            if queue_eligible
            else "false_no_material_exact_nfdisc_improvement"
            if not material
            else "false_target_ruled_out_or_insufficient_evidence"
        )
        candidates.append(record)

    candidates.sort(
        key=lambda row: (
            int(row.get("exact_nfdisc_abs") or 10**1000),
            int(row.get("outer_quartic_discriminant") or 10**1000),
            str(row.get("canonical_hash") or ""),
        )
    )
    frontier_rows = [
        row
        for row in candidates
        if row.get("internal_frontier_improvement")
        and row.get("target_label_not_ruled_out") is True
        and row.get("sufficient_adaptive_frobenius_evidence") is True
    ]
    for row in candidates:
        row["generator_exploration_eligible"] = False
        row["generator_exploration_role"] = None
    if frontier_rows:
        frontier_rows[0]["generator_exploration_eligible"] = True
        frontier_rows[0]["generator_exploration_role"] = "exact_local_exploration"
        frontier_rows[0]["generator_exploration_reason"] = (
            "Exact local h(x^6) row improves the previous family nfdisc frontier, has exact outer S4, "
            "and retains the intended target under adaptive evidence; official exact label remains pending."
        )
    queue = [row for row in candidates if row.get("exact_label_queue_eligible")]
    retained = candidates[: int(args.candidate_limit)]
    retained_hashes = {str(row["canonical_hash"]) for row in retained}
    for row in queue:
        if str(row["canonical_hash"]) not in retained_hashes:
            retained.append(row)
            retained_hashes.add(str(row["canonical_hash"]))

    summary = {
        "record_type": "igp24_quartic_x6_discriminant_descent_summary",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": get_source_commit(REPO_ROOT),
        "tool": "scripts/igp24_quartic_x6_discriminant_descent.py",
        "safety_note": SAFETY_NOTE,
        "target_label": args.target_label,
        "target_pair": args.target_pair,
        "target_outer_action": dict(TARGET_9993_OUTER_ACTION),
        "target_progress_state": progress.get("progress_state"),
        "target_score_value_status": progress.get("score_value_status"),
        "target_team_count": progress.get("team_count"),
        "current_best_nfdisc_abs": current_best_nfdisc_abs,
        "internal_frontier_nfdisc_abs": int(args.internal_frontier_nfdisc),
        "progress_jsonl": str(args.progress_jsonl),
        "known_submission_jsonl": [str(path) for path in known_paths],
        "known_submission_hash_count": len(known["by_hash"]),
        "known_reciprocal_outer_count": len(known["by_reciprocal_outer"]),
        "group_index": str(args.group_index),
        "group_index_scope": scope,
        "grid_bounds": {
            "a_abs": [args.a_abs_min, args.a_abs_max],
            "b": [args.b_min, args.b_max],
            "c_abs": [args.c_abs_min, args.c_abs_max],
            "d": 1,
            "maximum_quartic_discriminant": args.maximum_quartic_discriminant,
        },
        "maximum_nfdisc_evaluations": args.maximum_nfdisc_evaluations,
        "nfdisc_evaluations": nfdisc_evaluations,
        "nfdisc_timeout_seconds": args.nfdisc_timeout,
        "usable_prime_budget": args.usable_prime_budget,
        "minimum_usable_primes": args.minimum_usable_primes,
        "frobenius_screen_ratio": args.frobenius_screen_ratio,
        "grid_candidate_count": stage_counts["grid_candidate"],
        "four_positive_outer_count": stage_counts["four_positive_outer"],
        "outer_s4_count": stage_counts["outer_s4"],
        "degree24_local_valid_count": stage_counts["degree24_local_valid"],
        "exact_nfdisc_count": stage_counts["exact_nfdisc"],
        "target_cycle_survivor_count": stage_counts["target_cycle_survivor"],
        "retained_candidate_count": len(retained),
        "exact_label_queue_count": len(queue),
        "generator_exploration_eligible_count": sum(
            1 for row in candidates if row.get("generator_exploration_eligible")
        ),
        "generator_exploration_hashes": [
            row.get("canonical_hash") for row in candidates if row.get("generator_exploration_eligible")
        ],
        "exact_label_queue_hashes": [row.get("canonical_hash") for row in queue],
        "best_exact_nfdisc_abs": retained[0]["exact_nfdisc_abs"] if retained else None,
        "best_nfdisc_ratio_to_current": retained[0]["nfdisc_ratio_to_current_best"] if retained else None,
        "rejected_counts": dict(sorted(rejection_counts.items())),
        "expected_points_status": "unavailable_uncalibrated",
        "live_submission_recommended_now": False,
        "submission_recommendation": (
            "false_exact_label_review_required"
            if queue
            else "false_no_material_nfdisc_improvement_candidate"
        ),
        "output_files": {
            "summary_json": str(args.output_dir / SUMMARY_JSON),
            "report_md": str(args.output_dir / REPORT_MD),
            "candidates_jsonl": str(args.output_dir / CANDIDATES_JSONL),
            "rejected_jsonl": str(args.output_dir / REJECTED_JSONL),
            "exact_label_queue_jsonl": str(args.output_dir / EXACT_LABEL_QUEUE_JSONL),
            "exact_label_queue_coefficients_txt": str(args.output_dir / EXACT_LABEL_QUEUE_TXT),
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / SUMMARY_JSON, summary)
    write_jsonl(args.output_dir / CANDIDATES_JSONL, retained)
    write_jsonl(args.output_dir / REJECTED_JSONL, rejected)
    write_jsonl(args.output_dir / EXACT_LABEL_QUEUE_JSONL, queue)
    (args.output_dir / EXACT_LABEL_QUEUE_TXT).write_text(
        "".join(coefficient_line(row["exported_coefficients"]) + "\n" for row in queue),
        encoding="utf-8",
    )
    (args.output_dir / REPORT_MD).write_text(render_report(summary, retained, queue), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
