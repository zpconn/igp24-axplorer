#!/usr/bin/env python3
"""Build a CPU-only 4x6 alternate-composition diagnostic queue.

The 6x4 tower and plain 8x3 neighborhoods are now known SAIR label basins.
This helper pivots to degree pattern 4x6: a degree-4 outer polynomial composed
with a degree-6 inner polynomial. It performs only local SymPy/proxy checks and
writes review artifacts; it does not call SAIR, Magma, PARI, the network, a
GPU sampler, or any training routine.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

try:
    import sympy as sp
except ModuleNotFoundError:  # pragma: no cover - only exercised without deps
    sp = None

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_alt_composition_probe import (  # noqa: E402
    apply_outer_perturbations,
    centered_level_layouts,
    compose_outer_inner,
    outer_from_roots,
    parse_csv_set,
    parse_target_rs,
    support_summary,
)
from scripts.igp24_r16_diversity_probe import coefficient_line, known_hashes_from_pair_status  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate  # noqa: E402


QUEUE_JSONL = "alt_composition_4x6_candidate_queue.jsonl"
COEFFICIENTS_TXT = "alt_composition_4x6_candidate_coefficients.txt"
HASHES_TXT = "alt_composition_4x6_candidate_hashes.txt"
REJECTED_JSONL = "alt_composition_4x6_rejected_trials.jsonl"
SUMMARY_JSON = "alt_composition_4x6_summary.json"
REPORT_MD = "alt_composition_4x6_report.md"

SAFETY_NOTE = (
    "CPU-only local 4x6 alternate-composition diagnostic. It does not train "
    "models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything."
)

PREFERRED_R_ORDER = {24: 0, 20: 1, 16: 2, 12: 3, 8: 4}


def require_sympy() -> Any:
    if sp is None:
        raise RuntimeError("sympy is required for the 4x6 diagnostic generator")
    return sp


def sextic_inner_root_layouts() -> list[tuple[int, ...]]:
    return [
        (-4, -2, -1, 1, 3, 4),
        (-5, -3, -1, 2, 4, 6),
        (-6, -4, -2, 1, 3, 5),
        (-5, -4, -2, 1, 3, 6),
        (-4, -3, -1, 2, 5, 7),
        (-6, -5, -3, -1, 2, 4),
        (-7, -4, -2, 1, 5, 8),
        (-3, -2, -1, 1, 2, 4),
        (1, 2, 3, 4, 5, 6),
        (-3, -2, -1, 1, 2, 3),
    ]


def level_real_root_count(inner_coefficients: Iterable[int], level: int) -> int:
    sympy = require_sympy()
    x = sympy.Symbol("x")
    coeffs = [int(value) for value in inner_coefficients]
    coeffs[0] -= int(level)
    expr = sum(coefficient * x**index for index, coefficient in enumerate(coeffs))
    return int(sympy.Poly(expr, x, domain=sympy.ZZ).count_roots(inf=-sympy.oo, sup=sympy.oo))


def sextic_six_real_levels(inner_coefficients: Iterable[int], *, level_bound: int, max_levels: int) -> list[int]:
    levels: list[int] = []
    candidates = sorted(range(-int(level_bound), int(level_bound) + 1), key=lambda value: (abs(value), value))
    for level in candidates:
        if level_real_root_count(inner_coefficients, level) == 6:
            levels.append(int(level))
            if len(levels) >= int(max_levels):
                break
    return sorted(levels)


def level_layouts(levels: list[int], *, width: int = 4, max_layouts: int = 24) -> list[tuple[int, ...]]:
    if len(levels) < width:
        return []
    layouts = centered_level_layouts(levels, width, max_layouts=max_layouts // 2)
    windows = [
        tuple(levels[index : index + width])
        for index in range(0, max(1, len(levels) - width + 1), max(1, len(levels) // max(1, max_layouts)))
    ]
    middle = len(levels) // 2
    windows.extend(
        [
            tuple(levels[:width]),
            tuple(levels[max(0, middle - width // 2) : max(0, middle - width // 2) + width]),
            tuple(levels[-width:]),
        ]
    )
    windows.extend(combinations(levels[: min(len(levels), 8)], width))
    unique: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for layout in [*layouts, *windows]:
        if len(layout) != width:
            continue
        canonical = tuple(sorted(int(value) for value in layout))
        if canonical in seen:
            continue
        seen.add(canonical)
        unique.append(canonical)
        if len(unique) >= max_layouts:
            break
    return unique


def outer_perturbation_groups() -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    return [
        ("outer_constant_shift", ((0, 1),)),
        ("outer_constant_shift", ((0, -1),)),
        ("outer_linear_quadratic_shift", ((1, 1), (2, -1))),
        ("outer_linear_quadratic_shift", ((1, -1), (2, 1))),
        ("outer_two_coefficient_shift", ((0, 1), (2, -1))),
        ("outer_two_coefficient_shift", ((0, -1), (2, 1))),
        ("outer_cubic_mixed_shift", ((0, 2), (1, -1), (3, 1))),
        ("outer_cubic_mixed_shift", ((0, -2), (1, 1), (3, -1))),
        ("outer_balanced_shift", ((0, 1), (1, -2), (2, 1))),
        ("outer_balanced_shift", ((0, -1), (1, 2), (2, -1))),
    ]


def alt_4x6_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    roots = ",".join(str(value) for value in metadata.get("alt_inner_roots") or [])
    levels = ",".join(str(value) for value in metadata.get("alt_outer_six_real_levels") or [])
    perturbations = ",".join(
        f"{item.get('outer_y_exponent')}:{item.get('delta')}"
        for item in metadata.get("alt_outer_perturbations") or []
    )
    return (
        f"4x6|inner_roots={roots}|mode={metadata.get('alt_perturbation_mode')}"
        f"|levels={levels}|outer_y={perturbations}"
    )


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    inner = [int(value) for value in trial["inner_coefficients"]]
    outer_before = [int(value) for value in trial["outer_coefficients_before_perturbation"]]
    perturbations = [(int(exp), int(delta)) for exp, delta in trial["outer_perturbations"]]
    outer_after = apply_outer_perturbations(outer_before, perturbations)
    coeffs = compose_outer_inner(outer_after, inner)
    support = support_summary(coeffs)
    metadata: dict[str, Any] = {
        "strategy": "alt_composition_4x6_probe",
        "construction_family": "alt_composition_4x6",
        "decomposition_type": "exact_composition",
        "decomposition_degree_pattern": "4x6",
        "alt_inner_expression": "monic degree-6 all-real-root polynomial",
        "alt_inner_roots": list(trial["inner_roots"]),
        "alt_inner_polynomial_coefficients": list(inner),
        "alt_outer_roots_before_perturbation": list(trial["outer_roots"]),
        "alt_outer_six_real_levels": list(trial["outer_roots"]),
        "alt_outer_coefficients_before_perturbation": list(outer_before),
        "alt_outer_coefficients": list(outer_after),
        "alt_outer_perturbations": [
            {"outer_y_exponent": int(exponent), "delta": int(delta)} for exponent, delta in perturbations
        ],
        "alt_perturbation_mode": str(trial["mode"]),
        "alt_perturbation_terms": len(perturbations),
        "alt_expected_preimages_per_outer_root": 6,
        "alt_expected_real_root_count": int(trial.get("expected_real_root_count") or 24),
        "alt_available_six_real_level_count": int(trial.get("available_six_real_level_count") or 0),
        "alt_support_exponents": support["support_exponents"],
        "alt_support_gcd": support["support_gcd"],
        "alt_even_support": support["even_support"],
        "alt_odd_support_exponents": support["odd_support_exponents"],
        "target_r_heuristic": int(trial.get("expected_real_root_count") or 24),
        "composed_support": True,
        "exact_composition_after_perturbation": True,
        "anti_basin_features": [
            "degree_pattern_4x6",
            "degree_pattern_not_6x4",
            "degree_pattern_not_plain_8x3",
            "not_g_x_squared_even_support",
            "support_gcd_one",
        ],
        "structural_difference_from_exhausted_lanes": (
            "changes the composition degree pattern to 4x6 after 6x4 and 8x3 collapsed"
        ),
        "target_plan_alignment": "high-real-root diagnostic for r=24/20/16/12/8 remaining buckets",
    }
    metadata["alt_composition_family_key"] = alt_4x6_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def passes_structural_gates(coeffs: list[int], metadata: dict[str, Any]) -> tuple[bool, list[str]]:
    failed: list[str] = []
    pattern = str(metadata.get("decomposition_degree_pattern") or "")
    if pattern != "4x6":
        failed.append("not_4x6_degree_pattern")
    if pattern in {"6x4", "8x3", "3x8", "g(x^2)"}:
        failed.append("known_exhausted_degree_pattern")
    if metadata.get("alt_even_support") is True:
        failed.append("even_support_g_x_squared_like")
    if metadata.get("alt_support_gcd") != 1:
        failed.append("support_gcd_not_one")
    if coefficient_height(coeffs) <= 0:
        failed.append("invalid_coefficient_height")
    return not failed, failed


def trial_variants(
    *,
    rng: random.Random,
    max_trials: int,
    level_bound: int,
    max_levels_per_inner: int,
    max_layouts_per_inner: int,
    excluded_modes: set[str] | None = None,
) -> Iterable[dict[str, Any]]:
    excluded = excluded_modes or set()
    plans: list[dict[str, Any]] = []
    groups = [item for item in outer_perturbation_groups() if item[0] not in excluded]
    rng.shuffle(groups)
    roots_list = list(sextic_inner_root_layouts())
    rng.shuffle(roots_list)
    for roots in roots_list:
        inner = outer_from_roots(roots)
        try:
            levels = sextic_six_real_levels(
                inner,
                level_bound=int(level_bound),
                max_levels=int(max_levels_per_inner),
            )
        except RuntimeError:
            levels = []
        if len(levels) < 4:
            continue
        layouts = level_layouts(levels, width=4, max_layouts=int(max_layouts_per_inner))
        rng.shuffle(layouts)
        for layout in layouts:
            outer = outer_from_roots(layout)
            for mode, group in groups:
                plans.append(
                    {
                        "decomposition_degree_pattern": "4x6",
                        "mode": mode,
                        "inner_roots": list(roots),
                        "inner_coefficients": list(inner),
                        "outer_roots": list(layout),
                        "outer_coefficients_before_perturbation": list(outer),
                        "outer_perturbations": list(group),
                        "available_six_real_level_count": len(levels),
                        "expected_real_root_count": 24,
                    }
                )
    rng.shuffle(plans)
    for item in plans[: int(max_trials)]:
        yield item


def sort_key(record: dict[str, Any]) -> tuple[int, int, int, float, int, str]:
    metadata = record.get("generation_metadata") or {}
    r_value = int(record.get("real_root_count") or 0)
    components = record.get("score_components") or {}
    return (
        PREFERRED_R_ORDER.get(r_value, 99),
        int(record.get("coefficient_height") or 0),
        -int(components.get("cycle_diversity_count") or 0),
        float(record.get("log_abs_discriminant") or 0.0),
        int(metadata.get("alt_perturbation_terms") or 0),
        str(record.get("canonical_hash") or ""),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int, per_mode_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key)
    for record in rows:
        if len(selected) >= int(limit):
            break
        metadata = record.get("generation_metadata") or {}
        family = alt_4x6_family_key(record)
        mode = str(metadata.get("alt_perturbation_mode") or "")
        hash_value = str(record.get("canonical_hash") or "")
        if family_counts[family] >= int(per_family_cap):
            continue
        if mode_counts[mode] >= int(per_mode_cap):
            continue
        if hash_value in selected_hashes:
            continue
        selected.append(record)
        selected_hashes.add(hash_value)
        family_counts[family] += 1
        mode_counts[mode] += 1
    for record in rows:
        if len(selected) >= int(limit):
            break
        metadata = record.get("generation_metadata") or {}
        family = alt_4x6_family_key(record)
        hash_value = str(record.get("canonical_hash") or "")
        if family_counts[family] >= int(per_family_cap) or hash_value in selected_hashes:
            continue
        selected.append(record)
        selected_hashes.add(hash_value)
        family_counts[family] += 1
    for rank, record in enumerate(selected, start=1):
        record["alt_composition_4x6_queue_rank"] = rank
    return selected


def build_submission_readiness(selected: list[dict[str, Any]], target_rs: list[int]) -> dict[str, Any]:
    selected_rs = sorted(set(int(row.get("real_root_count") or -1) for row in selected))
    mode_counts = Counter(str((row.get("generation_metadata") or {}).get("alt_perturbation_mode")) for row in selected)
    ready = len(selected) >= 8 and all(r_value in target_rs for r_value in selected_rs) and len(mode_counts) >= 2
    return {
        "status": "planner_review_ready_not_submitted" if ready else "diagnostic_only_not_ready",
        "worth_scoring_with_anti_basin_planner": bool(ready),
        "submitted_by_this_tool": False,
        "reason": (
            "Selected rows are locally valid 4x6 candidates with multiple perturbation modes; score with the anti-basin planner before any SAIR dry-run."
        )
        if ready
        else "Too few locally valid/diverse 4x6 rows survived local gates.",
        "known_basins_avoided": [
            "exact_even_6x4_tower_24T23883_24T24651",
            "odd_escaped_6x4_tower_24T25000",
            "plain_8x3_24T24932",
            "exact_g_x_squared_even_support",
        ],
        "selected_patterns": ["4x6"] if selected else [],
        "selected_r_values": selected_rs,
        "selected_mode_counts": dict(mode_counts),
        "candidate_rows_to_consider": [
            {
                "rank": row.get("alt_composition_4x6_queue_rank"),
                "short_hash": str(row.get("canonical_hash") or "")[:12],
                "r": row.get("real_root_count"),
                "mode": (row.get("generation_metadata") or {}).get("alt_perturbation_mode"),
                "height": row.get("coefficient_height"),
            }
            for row in selected
        ],
    }


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    readiness = summary.get("submission_readiness") or {}
    lines = [
        "# IGP24 4x6 Alternate Composition Diagnostic",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid candidates: {summary.get('valid_candidate_count')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Selected r counts: `{json.dumps(summary.get('selected_r_counts'), sort_keys=True)}`",
        f"- Selected mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Valid mode counts: `{json.dumps(summary.get('valid_mode_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "## Submission Readiness",
        "",
        f"- Status: `{readiness.get('status')}`",
        f"- Planner scoring recommended: `{readiness.get('worth_scoring_with_anti_basin_planner')}`",
        f"- Submitted by this tool: `{readiness.get('submitted_by_this_tool')}`",
        f"- Reason: {readiness.get('reason')}",
        "",
        "## Selected Rows",
        "",
        "| rank | hash | r | mode | family | height | log disc |",
        "| ---: | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("alt_composition_4x6_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    str(row.get("real_root_count")),
                    f"`{metadata.get('alt_perturbation_mode')}`",
                    f"`{metadata.get('alt_composition_family_key')}`",
                    str(row.get("coefficient_height")),
                    f"{float(row.get('log_abs_discriminant') or 0.0):.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Caveat: these rows have local exact real-root, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    *,
    output_dir: Path,
    selected: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    queue_path = output_dir / QUEUE_JSONL
    coeffs_path = output_dir / COEFFICIENTS_TXT
    hashes_path = output_dir / HASHES_TXT
    rejected_path = output_dir / REJECTED_JSONL
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    with queue_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with coeffs_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(coefficient_line(record["exported_coefficients"]) + "\n")
    hashes_path.write_text(
        "".join(
            f"{record.get('alt_composition_4x6_queue_rank')}\t{record.get('canonical_hash')}\n"
            for record in selected
        ),
        encoding="utf-8",
    )
    with rejected_path.open("w", encoding="utf-8") as handle:
        for record in rejected:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, selected), encoding="utf-8")
    return {
        "queue_jsonl": queue_path,
        "coefficients_txt": coeffs_path,
        "hashes_txt": hashes_path,
        "rejected_jsonl": rejected_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a CPU-only 4x6 alternate-composition diagnostic queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument("--seed", type=int, default=244601)
    parser.add_argument("--max_trials", type=int, default=1600)
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--per_mode_cap", type=int, default=8)
    parser.add_argument("--coeff_bound", type=int, default=2_000_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--target_rs", default="24,20,16,12,8")
    parser.add_argument("--level_bound", type=int, default=200)
    parser.add_argument("--max_levels_per_inner", type=int, default=80)
    parser.add_argument("--max_layouts_per_inner", type=int, default=24)
    parser.add_argument("--exclude_perturbation_modes", default="outer_constant_shift")
    parser.add_argument("--stop_after_candidates", type=int, default=120)
    parser.add_argument("--max_rejected_records", type=int, default=300)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = get_parser().parse_args(argv)
    rng = random.Random(int(args.seed))
    target_rs = parse_target_rs(str(args.target_rs))
    excluded_modes = parse_csv_set(str(args.exclude_perturbation_modes))
    known_hashes = known_hashes_from_pair_status(args.pair_status_json)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    rejected_counts: Counter[str] = Counter()
    rejected_counts_by_mode: dict[str, Counter[str]] = {}
    observed_root_count_counts: Counter[str] = Counter()
    trial_mode_counts: Counter[str] = Counter()
    trials_attempted = 0

    def bump_rejection(mode: str, reason: str) -> None:
        rejected_counts[reason] += 1
        rejected_counts_by_mode.setdefault(mode, Counter())[reason] += 1

    for trial in trial_variants(
        rng=rng,
        max_trials=int(args.max_trials),
        level_bound=int(args.level_bound),
        max_levels_per_inner=int(args.max_levels_per_inner),
        max_layouts_per_inner=int(args.max_layouts_per_inner),
        excluded_modes=excluded_modes,
    ):
        trials_attempted += 1
        mode = str(trial.get("mode") or "unknown")
        trial_mode_counts[mode] += 1
        try:
            coeffs, metadata = coefficients_from_trial(trial)
        except Exception as exc:
            bump_rejection(mode, f"construction_failed:{type(exc).__name__}")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": f"construction_failed:{type(exc).__name__}"})
            continue
        metadata["alt_4x6_probe_seed"] = int(args.seed)
        metadata["alt_coefficient_height"] = coefficient_height(coeffs)
        gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)
        if not gate_ok:
            reason = ",".join(gate_failures)
            bump_rejection(mode, reason)
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": reason, "metadata": metadata})
            continue
        if coefficient_height(coeffs) > int(args.coeff_bound):
            bump_rejection(mode, "coefficient_height_exceeds_bound")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": "coefficient_height_exceeds_bound", "metadata": metadata})
            continue

        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=int(metadata.get("target_r_heuristic") or 24),
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        metadata["alt_local_validation"] = {
            "valid": bool(analysis.valid),
            "real_root_count": analysis.real_root_count,
            "irreducible": analysis.irreducible,
            "squarefree": analysis.squarefree,
            "canonical_hash": analysis.canonical_hash,
            "rejection_reason": analysis.rejection_reason,
        }
        if analysis.real_root_count is not None:
            observed_root_count_counts[str(analysis.real_root_count)] += 1
        if not analysis.valid:
            bump_rejection(mode, str(analysis.rejection_reason or "invalid"))
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": analysis.rejection_reason, "metadata": metadata})
            continue
        if int(analysis.real_root_count or -1) not in target_rs:
            bump_rejection(mode, "real_root_count_not_target_bucket")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append(
                    {
                        "trial": trial,
                        "rejection_reason": "real_root_count_not_target_bucket",
                        "real_root_count": analysis.real_root_count,
                        "metadata": metadata,
                    }
                )
            continue
        if analysis.canonical_hash in known_hashes or analysis.canonical_hash in seen_hashes:
            bump_rejection(mode, "known_or_duplicate_hash")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": "known_or_duplicate_hash", "metadata": metadata})
            continue

        record = analysis_to_record(
            analysis,
            score,
            target_r=int(analysis.real_root_count or 24),
            experiment_name="alt_composition_4x6_probe",
            verification_status="proxy_scored",
            generation_metadata=metadata,
            local_search_metadata={"attempted": 0, "accepted": 0, "enabled": False},
        )
        record.update(
            {
                "source_strategy": metadata["strategy"],
                "proxy_only_caveat": SAFETY_NOTE,
                "exact_label_claimed_by_helper": False,
                "submission_path": "diagnostic_queue_only_no_submission",
                "score1_target_caveat": "Exact 24T label must come from SAIR/Magma; local checks only prove degree/r/irreducible/squarefree.",
            }
        )
        candidates.append(record)
        seen_hashes.add(str(analysis.canonical_hash))
        if len(candidates) >= int(args.stop_after_candidates):
            break

    selected = select_diverse(
        candidates,
        limit=int(args.limit),
        per_family_cap=int(args.per_family_cap),
        per_mode_cap=int(args.per_mode_cap),
    )
    selected_metadata = [row.get("generation_metadata") or {} for row in selected]
    readiness = build_submission_readiness(selected, target_rs)
    queue_status = (
        "planner_review_ready_not_submitted"
        if readiness["worth_scoring_with_anti_basin_planner"]
        else "diagnostic_too_few_valid_rows"
    )
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_alt_composition_4x6_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_alt_composition_4x6_probe.py", *argv],
        "safety": {
            "cpu_only": True,
            "gpu_training": False,
            "model_training": False,
            "sair_api": False,
            "magma": False,
            "pari": False,
            "network": False,
            "automatic_submission": False,
        },
        "target_rs": target_rs,
        "excluded_perturbation_modes": sorted(excluded_modes),
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "trial_mode_counts": dict(trial_mode_counts),
        "valid_candidate_count": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_pattern_counts": {"4x6": len(selected)} if selected else {},
        "selected_mode_counts": dict(Counter(str(metadata.get("alt_perturbation_mode") or "unknown") for metadata in selected_metadata)),
        "valid_mode_counts": dict(
            Counter(str((row.get("generation_metadata") or {}).get("alt_perturbation_mode") or "unknown") for row in candidates)
        ),
        "selected_r_counts": dict(Counter(str(row.get("real_root_count")) for row in selected)),
        "valid_r_counts": dict(Counter(str(row.get("real_root_count")) for row in candidates)),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "rejected_counts_by_mode": {mode: dict(counts) for mode, counts in sorted(rejected_counts_by_mode.items())},
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "selected_family_keys": [alt_4x6_family_key(row) for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "anti_basin_constraints_satisfied": [
            "degree_pattern_4x6",
            "not_6x4",
            "not_plain_8x3",
            "not_g_x_squared_even_support",
            "support_gcd_one",
        ],
        "submission_readiness": readiness,
        "recommendation": (
            "score_with_anti_basin_planner_before_any_sair_submission"
            if readiness["worth_scoring_with_anti_basin_planner"]
            else "diagnostic_only_refine_4x6_search"
        ),
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
