#!/usr/bin/env python3
"""Compare model-projected and random structural candidates with exact cycles.

The comparison uses a complete degree-24 group-cycle index, fresh local
progress data, exact modular squarefreeness checks, and a matched family mix.
It performs no network access and no submission. Frobenius compatibility is
necessary target-exclusion evidence, never an exact group identification.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.adaptive_frobenius import (  # noqa: E402
    coefficients_from_record,
    small_primes,
    unramified_factorization_degrees_mod_prime,
)
from src.igp24.group_compatibility import (  # noqa: E402
    GroupCycleIndex,
    cycle_type_key,
    progress_states_for_pairs,
)


SCHEMA_VERSION = "igp24_axg_projection_frobenius_comparison_v1"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def structure_compatible_labels(index: GroupCycleIndex, block_size: int) -> set[str]:
    labels: set[str] = set()
    with index.connect() as connection:
        rows = connection.execute(
            "SELECT label, primitive, block_sizes_json FROM groups WHERE status = 'complete'"
        ).fetchall()
    for row in rows:
        block_sizes = {int(value) for value in json.loads(row["block_sizes_json"] or "[]")}
        if row["primitive"] == 0 and int(block_size) in block_sizes:
            labels.add(str(row["label"]))
    return labels


def select_matched_rows(
    model_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    sample_per_lane: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    model_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    baseline_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        model_by_family[str((row.get("features") or {}).get("construction_family"))].append(row)
    for row in baseline_rows:
        baseline_by_family[str((row.get("features") or {}).get("construction_family"))].append(row)
    families = sorted(set(model_by_family) & set(baseline_by_family))
    if not families:
        raise ValueError("no_common_construction_families")
    base, remainder = divmod(int(sample_per_lane), len(families))
    quotas = {family: base + int(index < remainder) for index, family in enumerate(families)}
    selected_model: list[dict[str, Any]] = []
    selected_baseline: list[dict[str, Any]] = []
    for family in families:
        quota = min(quotas[family], len(model_by_family[family]), len(baseline_by_family[family]))
        model_by_family[family].sort(
            key=lambda row: (
                float((row.get("features") or {}).get("normalized_projection_error") or math.inf),
                str(row.get("canonical_hash")),
            )
        )
        baseline_by_key = {
            (
                str(row.get("source_model_hash")),
                int(row.get("projection_variant") or 0),
            ): row
            for row in baseline_by_family[family]
        }
        family_model: list[dict[str, Any]] = []
        family_baseline: list[dict[str, Any]] = []
        for model_row in model_by_family[family]:
            key = (
                str(model_row.get("source_model_hash")),
                int(model_row.get("projection_variant") or 0),
            )
            baseline_row = baseline_by_key.get(key)
            if baseline_row is None:
                continue
            family_model.append(model_row)
            family_baseline.append(baseline_row)
            if len(family_model) >= quota:
                break
        quotas[family] = len(family_model)
        selected_model.extend(family_model)
        selected_baseline.extend(family_baseline)
    return selected_model, selected_baseline, quotas


def screen_candidate(
    row: dict[str, Any],
    *,
    index: GroupCycleIndex,
    initial_labels: set[str],
    valuable_labels: set[str],
    cycle_cache: dict[str, set[str]],
    max_usable_primes: int,
    stable_after: int,
    min_usable_primes: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    coefficients = coefficients_from_record(row)
    survivors = set(initial_labels)
    previous_survivors: frozenset[str] | None = None
    stable_count = 0
    observations: list[dict[str, Any]] = []
    skipped_ramified: list[int] = []
    stop_reason = "evidence_budget_exhausted"
    primes_examined = 0
    for prime in small_primes():
        if len(observations) >= int(max_usable_primes):
            break
        primes_examined += 1
        degrees = unramified_factorization_degrees_mod_prime(coefficients, prime)
        if degrees is None:
            skipped_ramified.append(int(prime))
            continue
        cycle_type = cycle_type_key(degrees)
        if cycle_type not in cycle_cache:
            cycle_cache[cycle_type] = index.labels_for_cycle_type(cycle_type)
        survivors &= cycle_cache[cycle_type]
        valuable_survivors = survivors & valuable_labels
        frozen = frozenset(survivors)
        if previous_survivors is not None and frozen == previous_survivors:
            stable_count += 1
        else:
            stable_count = 0
        previous_survivors = frozen
        observations.append(
            {
                "prime": int(prime),
                "degrees": list(degrees),
                "cycle_type": cycle_type,
                "indexed_target_survivor_count": len(survivors),
                "valuable_target_count": len(valuable_survivors),
                "unramified_verification": "squarefree_mod_p_factor_multiplicities",
            }
        )
        if len(observations) >= int(min_usable_primes) and not valuable_survivors:
            stop_reason = "valuable_targets_ruled_out"
            break
        if int(stable_after) > 0 and stable_count >= int(stable_after):
            stop_reason = "survivor_set_stable"
            break

    valuable_survivors = sorted(survivors & valuable_labels)
    survivor_labels = sorted(survivors)
    return {
        "schema_version": SCHEMA_VERSION,
        "canonical_hash": row.get("canonical_hash"),
        "source_lane": row.get("source_lane"),
        "construction_family": (row.get("features") or {}).get("construction_family"),
        "r": 24,
        "usable_prime_count": len(observations),
        "primes_examined": primes_examined,
        "skipped_ramified_primes": skipped_ramified,
        "stop_reason": stop_reason,
        "observations": observations,
        "indexed_target_survivor_count": len(survivor_labels),
        "indexed_target_labels_not_ruled_out": survivor_labels[:200],
        "indexed_target_labels_truncated": len(survivor_labels) > 200,
        "valuable_target_count": len(valuable_survivors),
        "valuable_targets_not_ruled_out": [f"{label}|r=24" for label in valuable_survivors[:200]],
        "valuable_targets_truncated": len(valuable_survivors) > 200,
        "best_case_points": 1 if valuable_survivors else 0,
        "expected_points_status": "unavailable_uncalibrated",
        "evidence_strength": "adaptive_unramified_frobenius_cycle_target_exclusion",
        "soundness": "necessary_target_exclusion_only_not_exact_label",
        "runtime_seconds": time.perf_counter() - started,
        "packet_eligible": False,
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * (len(ordered) - 1)))]


def lane_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivor_counts = [float(row["indexed_target_survivor_count"]) for row in rows]
    valuable_counts = [float(row["valuable_target_count"]) for row in rows]
    runtimes = [float(row["runtime_seconds"]) for row in rows]
    usable_primes = [float(row["usable_prime_count"]) for row in rows]
    valuable_union = {
        target
        for row in rows
        for target in row.get("valuable_targets_not_ruled_out") or []
    }
    target_counts = Counter(
        target
        for row in rows
        for target in row.get("valuable_targets_not_ruled_out") or []
    )
    family_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        family_rows[str(row.get("construction_family"))].append(row)
    return {
        "row_count": len(rows),
        "rows_with_valuable_target": sum(value > 0 for value in valuable_counts),
        "valuable_target_survival_rate": sum(value > 0 for value in valuable_counts) / len(rows) if rows else None,
        "indexed_survivor_count": {
            "median": statistics.median(survivor_counts) if survivor_counts else None,
            "p90": percentile(survivor_counts, 0.9),
            "maximum": max(survivor_counts) if survivor_counts else None,
        },
        "valuable_target_count": {
            "median": statistics.median(valuable_counts) if valuable_counts else None,
            "p90": percentile(valuable_counts, 0.9),
            "maximum": max(valuable_counts) if valuable_counts else None,
        },
        "distinct_valuable_targets_in_untruncated_outputs": len(valuable_union),
        "valuable_target_row_counts": dict(sorted(target_counts.items())),
        "rows_with_valuable_target_by_family": {
            family: {
                "row_count": len(items),
                "rows_with_valuable_target": sum(int(item["valuable_target_count"] > 0) for item in items),
                "valuable_target_survival_rate": sum(int(item["valuable_target_count"] > 0) for item in items)
                / len(items),
            }
            for family, items in sorted(family_rows.items())
        },
        "stop_reason_counts": dict(sorted(Counter(str(row["stop_reason"]) for row in rows).items())),
        "usable_primes_median": statistics.median(usable_primes) if usable_primes else None,
        "runtime_seconds_total": sum(runtimes),
        "sum_of_per_row_best_case_point_ceilings": sum(int(row["best_case_points"]) for row in rows),
        "best_case_packet_points": sum(int(row["best_case_points"]) for row in rows),
        "best_case_packet_points_note": "logical ceiling only; not an expectation and not evidence that mutually redundant rows all score",
        "expected_points_status": "unavailable_uncalibrated",
    }


def survival_rate_comparison(
    model_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    model_hits = sum(int(row["valuable_target_count"] > 0) for row in model_rows)
    baseline_hits = sum(int(row["valuable_target_count"] > 0) for row in baseline_rows)
    model_rate = model_hits / len(model_rows) if model_rows else 0.0
    baseline_rate = baseline_hits / len(baseline_rows) if baseline_rows else 0.0
    difference = model_rate - baseline_rate
    standard_error = math.sqrt(
        model_rate * (1.0 - model_rate) / max(1, len(model_rows))
        + baseline_rate * (1.0 - baseline_rate) / max(1, len(baseline_rows))
    )
    return {
        "model_hits": model_hits,
        "baseline_hits": baseline_hits,
        "absolute_rate_difference": difference,
        "approximate_95_percent_ci": [difference - 1.96 * standard_error, difference + 1.96 * standard_error],
        "statistically_clear_positive_difference": bool(standard_error and difference - 1.96 * standard_error > 0),
        "interpretation": "descriptive matched comparison; target survival is not official score probability",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_candidates_jsonl", type=Path, required=True)
    parser.add_argument("--baseline_candidates_jsonl", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--progress_jsonl", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--sample_per_lane", type=int, default=256)
    parser.add_argument("--max_usable_primes", type=int, default=40)
    parser.add_argument("--stable_after", type=int, default=10)
    parser.add_argument("--min_usable_primes", type=int, default=5)
    parser.add_argument("--progress_interval", type=int, default=32)
    args = parser.parse_args()

    started = time.perf_counter()
    index = GroupCycleIndex(args.index)
    scope = index.scope_metadata()
    if not scope.get("global_index_complete"):
        raise ValueError("comparison_requires_complete_degree24_group_index")
    all_labels = index.all_labels()
    structure_labels = structure_compatible_labels(index, block_size=2)
    progress_rows = read_jsonl(args.progress_jsonl)
    states = progress_states_for_pairs((f"{label}|r=24" for label in all_labels), progress_rows)
    valuable_labels = {
        str(state["label"])
        for state in states.values()
        if state.get("progress_state") == "allowed_remaining"
        or (
            state.get("progress_state") == "allowed_discovered"
            and int(state.get("team_count") or 0) <= 20
        )
    }
    initial_labels = all_labels & structure_labels
    valuable_labels &= initial_labels

    model_rows, baseline_rows, quotas = select_matched_rows(
        read_jsonl(args.model_candidates_jsonl),
        read_jsonl(args.baseline_candidates_jsonl),
        args.sample_per_lane,
    )
    cycle_cache: dict[str, set[str]] = {}
    screened: list[dict[str, Any]] = []
    for lane_rows in (model_rows, baseline_rows):
        for row in lane_rows:
            screened.append(
                screen_candidate(
                    row,
                    index=index,
                    initial_labels=initial_labels,
                    valuable_labels=valuable_labels,
                    cycle_cache=cycle_cache,
                    max_usable_primes=args.max_usable_primes,
                    stable_after=args.stable_after,
                    min_usable_primes=args.min_usable_primes,
                )
            )
            if args.progress_interval > 0 and len(screened) % args.progress_interval == 0:
                print(
                    json.dumps(
                        {
                            "event": "adaptive_projection_progress",
                            "completed": len(screened),
                            "total": len(model_rows) + len(baseline_rows),
                            "cycle_cache_size": len(cycle_cache),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

    model_screened = [row for row in screened if row["source_lane"] == "model_projected"]
    baseline_screened = [row for row in screened if row["source_lane"] == "matched_random_baseline"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": get_source_commit(REPO_ROOT),
        "index": str(args.index),
        "index_scope": scope,
        "progress_jsonl": str(args.progress_jsonl),
        "selection": {
            "requested_rows_per_lane": int(args.sample_per_lane),
            "actual_model_rows": len(model_rows),
            "actual_baseline_rows": len(baseline_rows),
            "family_quotas": quotas,
            "model_selection": "lowest normalized projection error within each family",
            "baseline_selection": "same source-model hash, family, and variant as each selected model projection",
        },
        "evidence_budget": {
            "max_usable_primes": int(args.max_usable_primes),
            "stable_after": int(args.stable_after),
            "min_usable_primes": int(args.min_usable_primes),
            "ramification_check": "exact squarefree reduction modulo each sampled prime",
        },
        "universe": {
            "all_indexed_labels": len(all_labels),
            "block_size_2_structure_compatible_labels": len(initial_labels),
            "current_valuable_r24_structure_compatible_labels": len(valuable_labels),
            "structure_filter_soundness": "h(x^2) preserves the Galois-invariant root pairs {alpha,-alpha}",
        },
        "model_projected": lane_summary(model_screened),
        "matched_random_baseline": lane_summary(baseline_screened),
        "comparison": {
            "numeric_expected_points_available": False,
            "target_coverage_is_not_additive_score": True,
            "valuable_target_survival": survival_rate_comparison(model_screened, baseline_screened),
            "model_promotion_recommendation": False,
            "reason": "projection comparison measures parameter proposals; direct AXG decoding still yielded zero exact-r24 valid rows",
        },
        "cycle_type_cache_size": len(cycle_cache),
        "runtime_seconds": time.perf_counter() - started,
        "safety": {
            "network_reads": False,
            "network_posts": False,
            "sair_calls": False,
            "live_submission": False,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "screened_candidates.jsonl", screened)
    write_json(args.output_dir / "comparison_summary.json", summary)
    report = "\n".join(
        [
            "# AXG projection Frobenius comparison",
            "",
            f"- Complete indexed groups: {len(all_labels)}",
            f"- Block-size-2 structural universe: {len(initial_labels)}",
            f"- Current valuable structural r=24 targets: {len(valuable_labels)}",
            f"- Model rows screened: {len(model_screened)}",
            f"- Baseline rows screened: {len(baseline_screened)}",
            "- Compatibility is necessary exclusion evidence, not exact label verification.",
            "- Expected points remain unavailable because no calibrated outcome model exists.",
            "- No network access or submission was performed.",
            "",
        ]
    )
    (args.output_dir / "comparison_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
