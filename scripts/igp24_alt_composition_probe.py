#!/usr/bin/env python3
"""Build a CPU-only alternate-composition diagnostic queue.

The r24 degree-6-by-degree-4 tower neighborhood is now a known local basin:
exact even towers landed in ``24T23883/24T24651`` and odd-escaped towers landed
in generic ``24T25000``. This helper pivots to different degree patterns:

* ``8x3``: a degree-8 outer polynomial composed with ``q(x)=x^3-s*x``.
* ``3x8``: a degree-3 outer polynomial composed with an all-real degree-8
  inner polynomial.

The output is a local diagnostic queue only. It does not call SAIR, Magma,
PARI, the network, a GPU sampler, or any training routine.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

try:  # Keep the module importable in environments before the SymPy deps load.
    import sympy as sp
except ModuleNotFoundError:  # pragma: no cover - only exercised without deps
    sp = None

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_r16_diversity_probe import coefficient_line, known_hashes_from_pair_status, multiply_polynomials  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate  # noqa: E402


QUEUE_JSONL = "alt_composition_candidate_queue.jsonl"
COEFFICIENTS_TXT = "alt_composition_candidate_coefficients.txt"
HASHES_TXT = "alt_composition_candidate_hashes.txt"
REJECTED_JSONL = "alt_composition_rejected_trials.jsonl"
SUMMARY_JSON = "alt_composition_summary.json"
REPORT_MD = "alt_composition_report.md"

SAFETY_NOTE = (
    "CPU-only local alternate-composition diagnostic. It does not train models, "
    "use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything."
)

BAD_DEGREE_PATTERNS = {"6x4", "6x4_seed_plus_odd_x_perturbation", "g(x^2)"}
PREFERRED_R_ORDER = {24: 0, 20: 1, 16: 2, 12: 3, 8: 4}


def parse_target_rs(value: str) -> list[int]:
    out: list[int] = []
    for raw in str(value).split(","):
        raw = raw.strip()
        if not raw:
            continue
        out.append(int(raw))
    return out or [24, 20, 16, 12, 8]


def support_summary(coefficients: Iterable[int]) -> dict[str, Any]:
    support = [index for index, value in enumerate(coefficients) if int(value) != 0]
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, exponent)
    return {
        "support_exponents": support,
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
        "odd_support_exponents": [exponent for exponent in support if exponent % 2 == 1],
    }


def outer_from_roots(roots: Iterable[int]) -> list[int]:
    coeffs = [1]
    for root in roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    return [int(value) for value in coeffs]


def compose_outer_inner(outer_coefficients: Iterable[int], inner_coefficients: Iterable[int]) -> list[int]:
    outer = [int(value) for value in outer_coefficients]
    inner = [int(value) for value in inner_coefficients]
    if len(outer) < 2 or outer[-1] != 1:
        raise ValueError("expected monic outer polynomial")
    if len(inner) < 2 or inner[-1] != 1:
        raise ValueError("expected monic inner polynomial")
    if (len(outer) - 1) * (len(inner) - 1) != DEGREE:
        raise ValueError("outer and inner degrees must multiply to 24")
    out = [0]
    power = [1]
    for coefficient in outer:
        if coefficient:
            term = [int(coefficient) * value for value in power]
            if len(out) < len(term):
                out.extend([0] * (len(term) - len(out)))
            for index, value in enumerate(term):
                out[index] += value
        power = multiply_polynomials(power, inner)
    if len(out) != DEGREE + 1 or out[-1] != 1:
        raise ValueError("composition did not produce a monic degree-24 polynomial")
    return [int(value) for value in out[:-1]]


def cubic_inner_coefficients(s_value: int) -> list[int]:
    """Return ascending coefficients for ``q(x)=x^3-s*x``."""

    return [0, -int(s_value), 0, 1]


def cubic_three_real_band_radius(s_value: int) -> float:
    # For q=x^3-s*x, levels strictly between +/- 2*s*sqrt(s/3)/3 have
    # three real preimages.
    s_float = float(s_value)
    return 2.0 * s_float * math.sqrt(s_float / 3.0) / 3.0


def cubic_three_real_levels(s_value: int) -> list[int]:
    radius = cubic_three_real_band_radius(s_value)
    bound = int(math.floor(radius - 1e-9))
    return [value for value in range(-bound, bound + 1) if value != 0]


def centered_level_layouts(levels: list[int], width: int, *, max_layouts: int) -> list[tuple[int, ...]]:
    layouts: list[tuple[int, ...]] = []
    if len(levels) < width:
        return layouts
    by_abs = tuple(sorted(levels, key=lambda item: (abs(item), item))[:width])
    layouts.append(tuple(sorted(by_abs)))
    step = max(1, len(levels) // max(1, max_layouts))
    for start in range(0, len(levels) - width + 1, step):
        layouts.append(tuple(levels[start : start + width]))
        if len(layouts) >= max_layouts:
            break
    unique: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    for layout in layouts:
        canonical = tuple(sorted(int(value) for value in layout))
        if canonical in seen:
            continue
        seen.add(canonical)
        unique.append(canonical)
    return unique[:max_layouts]


def outer_perturbation_groups(max_exponent: int) -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    groups: list[tuple[str, tuple[tuple[int, int], ...]]] = []
    for delta in (-20, -10, -5, -3, -2, -1, 1, 2, 3, 5, 10, 20):
        groups.append(("outer_constant_shift", ((0, delta),)))
    templates = [
        ("outer_two_coefficient_shift", ((0, 1), (2, -1))),
        ("outer_two_coefficient_shift", ((0, -1), (2, 1))),
        ("outer_two_coefficient_shift", ((1, 1), (3, -1))),
        ("outer_two_coefficient_shift", ((1, -1), (3, 1))),
        ("outer_three_coefficient_shift", ((0, 1), (2, -2), (4, 1))),
        ("outer_three_coefficient_shift", ((0, -1), (2, 2), (4, -1))),
        ("outer_high_coefficient_shift", ((0, 10), (5, -1))),
        ("outer_high_coefficient_shift", ((1, 3), (6, -1))),
        ("outer_mixed_high_shift", ((0, 5), (1, -2), (7, 1))),
    ]
    for mode, group in templates:
        if all(0 <= exponent <= max_exponent for exponent, _ in group):
            groups.append((mode, tuple(group)))
    return groups


def apply_outer_perturbations(outer_before: list[int], perturbations: Iterable[tuple[int, int]]) -> list[int]:
    outer_after = list(outer_before)
    max_free = len(outer_after) - 2
    for exponent, delta in perturbations:
        if not 0 <= int(exponent) <= max_free:
            raise ValueError("outer perturbations may not change the leading coefficient")
        outer_after[int(exponent)] += int(delta)
    return outer_after


def octic_inner_root_layouts() -> list[tuple[int, ...]]:
    return [
        (-4, -3, -2, -1, 1, 2, 3, 4),
        (-5, -3, -2, -1, 1, 2, 3, 5),
        (-6, -4, -2, -1, 1, 2, 4, 6),
        (-7, -5, -3, -1, 1, 3, 5, 7),
        (-8, -6, -4, -2, 1, 3, 5, 7),
        (1, 2, 3, 4, 5, 6, 7, 8),
    ]


def level_real_root_count(inner_coefficients: Iterable[int], level: int) -> int:
    if sp is None:
        raise RuntimeError("sympy is required for 3x8 level root counts")
    x = sp.Symbol("x")
    coeffs = [int(value) for value in inner_coefficients]
    coeffs[0] -= int(level)
    expr = sum(coefficient * x**index for index, coefficient in enumerate(coeffs))
    return int(sp.Poly(expr, x, domain=sp.ZZ).count_roots(inf=-sp.oo, sup=sp.oo))


def octic_eight_real_levels(inner_coefficients: Iterable[int], *, level_bound: int, max_levels: int) -> list[int]:
    levels: list[int] = []
    candidates = sorted(range(-int(level_bound), int(level_bound) + 1), key=lambda item: (abs(item), item))
    for level in candidates:
        if level_real_root_count(inner_coefficients, level) == 8:
            levels.append(int(level))
            if len(levels) >= int(max_levels):
                break
    return levels


def alt_composition_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    if metadata.get("decomposition_degree_pattern") == "8x3":
        levels = ",".join(str(value) for value in metadata.get("alt_outer_three_real_levels") or [])
        perturbations = ",".join(
            f"{item.get('outer_y_exponent')}:{item.get('delta')}"
            for item in metadata.get("alt_outer_perturbations") or []
        )
        return (
            f"8x3|s={metadata.get('alt_inner_parameter_s')}"
            f"|mode={metadata.get('alt_perturbation_mode')}|levels={levels}|outer_y={perturbations}"
        )
    levels = ",".join(str(value) for value in metadata.get("alt_outer_eight_real_levels") or [])
    roots = ",".join(str(value) for value in metadata.get("alt_inner_roots") or [])
    perturbations = ",".join(
        f"{item.get('outer_y_exponent')}:{item.get('delta')}"
        for item in metadata.get("alt_outer_perturbations") or []
    )
    return (
        f"3x8|inner_roots={roots}|mode={metadata.get('alt_perturbation_mode')}"
        f"|levels={levels}|outer_y={perturbations}"
    )


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    pattern = str(trial["decomposition_degree_pattern"])
    inner = [int(value) for value in trial["inner_coefficients"]]
    outer_before = [int(value) for value in trial["outer_coefficients_before_perturbation"]]
    perturbations = [(int(exp), int(delta)) for exp, delta in trial["outer_perturbations"]]
    outer_after = apply_outer_perturbations(outer_before, perturbations)
    coeffs = compose_outer_inner(outer_after, inner)
    support = support_summary(coeffs)
    metadata: dict[str, Any] = {
        "strategy": "alt_composition_probe",
        "construction_family": f"alt_composition_{pattern}",
        "decomposition_type": "exact_composition",
        "decomposition_degree_pattern": pattern,
        "alt_perturbation_mode": str(trial["mode"]),
        "alt_outer_coefficients_before_perturbation": list(outer_before),
        "alt_outer_coefficients": list(outer_after),
        "alt_outer_perturbations": [
            {"outer_y_exponent": int(exponent), "delta": int(delta)} for exponent, delta in perturbations
        ],
        "alt_perturbation_terms": len(perturbations),
        "alt_support_exponents": support["support_exponents"],
        "alt_support_gcd": support["support_gcd"],
        "alt_even_support": support["even_support"],
        "alt_odd_support_exponents": support["odd_support_exponents"],
        "target_r_heuristic": int(trial.get("expected_real_root_count") or 24),
        "composed_support": True,
        "exact_composition_after_perturbation": True,
        "anti_basin_features": [
            "degree_pattern_not_6x4",
            "not_g_x_squared_even_support",
            "support_gcd_one",
            "not_product_quadratic_low_odd_perturbation",
            "not_r24_tower_odd_escape",
        ],
        "structural_difference_from_exhausted_lanes": (
            "changes the composition degree pattern away from 6x4 and avoids exact even g(x^2) support"
        ),
        "target_plan_alignment": "high-real-root diagnostic for r=24/20/16/12/8 remaining buckets",
    }
    if pattern == "8x3":
        metadata.update(
            {
                "alt_inner_expression": f"x^3 - {int(trial['inner_parameter_s'])}*x",
                "alt_inner_parameter_s": int(trial["inner_parameter_s"]),
                "alt_inner_polynomial_coefficients": list(inner),
                "alt_inner_three_real_band_radius": trial["three_real_band_radius"],
                "alt_outer_roots_before_perturbation": list(trial["outer_roots"]),
                "alt_outer_three_real_levels": list(trial["outer_roots"]),
                "alt_expected_preimages_per_outer_root": 3,
                "alt_expected_real_root_count": 24,
            }
        )
    elif pattern == "3x8":
        metadata.update(
            {
                "alt_inner_expression": "monic degree-8 all-real-root polynomial",
                "alt_inner_roots": list(trial["inner_roots"]),
                "alt_inner_polynomial_coefficients": list(inner),
                "alt_outer_roots_before_perturbation": list(trial["outer_roots"]),
                "alt_outer_eight_real_levels": list(trial["outer_roots"]),
                "alt_expected_preimages_per_outer_root": 8,
                "alt_expected_real_root_count": 24,
            }
        )
    else:
        raise ValueError(f"unsupported pattern {pattern}")
    metadata["alt_composition_family_key"] = alt_composition_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def passes_structural_gates(coeffs: list[int], metadata: dict[str, Any]) -> tuple[bool, list[str]]:
    failed: list[str] = []
    pattern = str(metadata.get("decomposition_degree_pattern") or "")
    if pattern in BAD_DEGREE_PATTERNS:
        failed.append("bad_degree_pattern")
    if pattern not in {"8x3", "3x8"}:
        failed.append("not_alt_degree_pattern")
    if metadata.get("alt_even_support") is True:
        failed.append("even_support_g_x_squared_like")
    if metadata.get("alt_support_gcd") != 1:
        failed.append("support_gcd_not_one")
    if coefficient_height(coeffs) <= 0:
        failed.append("invalid_coefficient_height")
    if "6x4" in str(metadata.get("construction_family") or ""):
        failed.append("construction_family_mentions_6x4")
    return not failed, failed


def trial_variants(*, rng: random.Random, max_trials: int, lanes: Iterable[str]) -> Iterable[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    lane_set = {str(lane).strip() for lane in lanes}
    if "8x3" in lane_set:
        groups = outer_perturbation_groups(max_exponent=7)
        inner_parameters = [8, 9, 10, 11, 12, 13, 14]
        rng.shuffle(inner_parameters)
        rng.shuffle(groups)
        for s_value in inner_parameters:
            levels = cubic_three_real_levels(s_value)
            layouts = centered_level_layouts(levels, 8, max_layouts=18)
            rng.shuffle(layouts)
            for layout in layouts:
                outer = outer_from_roots(layout)
                for mode, group in groups:
                    plans.append(
                        {
                            "decomposition_degree_pattern": "8x3",
                            "mode": mode,
                            "inner_parameter_s": int(s_value),
                            "inner_coefficients": cubic_inner_coefficients(s_value),
                            "three_real_band_radius": cubic_three_real_band_radius(s_value),
                            "outer_roots": list(layout),
                            "outer_coefficients_before_perturbation": list(outer),
                            "outer_perturbations": list(group),
                            "expected_real_root_count": 24,
                        }
                    )
    if "3x8" in lane_set:
        groups = outer_perturbation_groups(max_exponent=2)
        rng.shuffle(groups)
        for roots in octic_inner_root_layouts():
            inner = outer_from_roots(roots)
            try:
                levels = octic_eight_real_levels(inner, level_bound=48, max_levels=14)
            except RuntimeError:
                levels = []
            if len(levels) < 3:
                continue
            layouts = [tuple(levels[index : index + 3]) for index in range(0, max(1, len(levels) - 2))]
            layouts.extend(combinations(levels[: min(8, len(levels))], 3))
            unique_layouts: list[tuple[int, ...]] = []
            seen_layouts: set[tuple[int, ...]] = set()
            for layout in layouts:
                canonical = tuple(sorted(int(value) for value in layout))
                if canonical in seen_layouts:
                    continue
                seen_layouts.add(canonical)
                unique_layouts.append(canonical)
                if len(unique_layouts) >= 20:
                    break
            rng.shuffle(unique_layouts)
            for layout in unique_layouts:
                outer = outer_from_roots(layout)
                for mode, group in groups:
                    plans.append(
                        {
                            "decomposition_degree_pattern": "3x8",
                            "mode": mode,
                            "inner_roots": list(roots),
                            "inner_coefficients": list(inner),
                            "outer_roots": list(layout),
                            "outer_coefficients_before_perturbation": list(outer),
                            "outer_perturbations": list(group),
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


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key)
    by_pattern: dict[str, list[dict[str, Any]]] = {}
    for record in rows:
        pattern = str((record.get("generation_metadata") or {}).get("decomposition_degree_pattern") or "unknown")
        by_pattern.setdefault(pattern, []).append(record)
    pattern_order = sorted(by_pattern, key=lambda pattern: sort_key(by_pattern[pattern][0]))

    progressed = True
    while len(selected) < int(limit) and progressed:
        progressed = False
        for pattern in pattern_order:
            candidates = by_pattern.get(pattern) or []
            while candidates:
                record = candidates.pop(0)
                family = alt_composition_family_key(record)
                hash_value = str(record.get("canonical_hash") or "")
                if family_counts[family] >= int(per_family_cap) or hash_value in selected_hashes:
                    continue
                selected.append(record)
                selected_hashes.add(hash_value)
                family_counts[family] += 1
                progressed = True
                break
            if len(selected) >= int(limit):
                break
    for record in rows:
        if len(selected) >= int(limit):
            break
        family = alt_composition_family_key(record)
        hash_value = str(record.get("canonical_hash") or "")
        if family_counts[family] >= int(per_family_cap) or hash_value in selected_hashes:
            continue
        selected.append(record)
        selected_hashes.add(hash_value)
        family_counts[family] += 1
    for rank, record in enumerate(selected, start=1):
        record["alt_composition_queue_rank"] = rank
    return selected


def build_submission_readiness(selected: list[dict[str, Any]], target_rs: list[int]) -> dict[str, Any]:
    patterns = sorted(
        set(str((row.get("generation_metadata") or {}).get("decomposition_degree_pattern") or "unknown") for row in selected)
    )
    selected_rs = sorted(set(int(row.get("real_root_count") or -1) for row in selected))
    ready = len(selected) >= 8 and all(r_value in target_rs for r_value in selected_rs)
    return {
        "status": "manual_review_ready_not_submitted" if ready else "diagnostic_only_not_ready",
        "worth_submitting_later": bool(ready),
        "submitted_by_this_tool": False,
        "reason": (
            "Selected rows are locally valid, structurally outside the exhausted 6x4 tower neighborhood, "
            "and hit high-real-root target buckets; hold for human/next-goal review before SAIR."
        )
        if ready
        else "Too few locally valid structurally novel rows were selected.",
        "known_basins_avoided": [
            "exact_even_6x4_tower_24T23883_24T24651",
            "odd_escaped_6x4_tower_24T25000",
            "product_quadratic_low_odd_perturbation_24T25000",
            "exact_g_x_squared_even_support",
        ],
        "selected_patterns": patterns,
        "selected_r_values": selected_rs,
        "candidate_rows_to_consider": [
            {
                "rank": row.get("alt_composition_queue_rank"),
                "short_hash": str(row.get("canonical_hash") or "")[:12],
                "r": row.get("real_root_count"),
                "pattern": (row.get("generation_metadata") or {}).get("decomposition_degree_pattern"),
                "height": row.get("coefficient_height"),
            }
            for row in selected
        ],
    }


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    readiness = summary.get("submission_readiness") or {}
    lines = [
        "# IGP24 Alternate Composition Diagnostic",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid candidates: {summary.get('valid_candidate_count')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Selected pattern counts: `{json.dumps(summary.get('selected_pattern_counts'), sort_keys=True)}`",
        f"- Valid pattern counts: `{json.dumps(summary.get('valid_pattern_counts'), sort_keys=True)}`",
        f"- Trial pattern counts: `{json.dumps(summary.get('trial_pattern_counts'), sort_keys=True)}`",
        f"- Selected r counts: `{json.dumps(summary.get('selected_r_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        f"- Rejected counts by pattern: `{json.dumps(summary.get('rejected_counts_by_pattern'), sort_keys=True)}`",
        "",
        "## Submission Readiness",
        "",
        f"- Status: `{readiness.get('status')}`",
        f"- Worth submitting later: `{readiness.get('worth_submitting_later')}`",
        f"- Submitted by this tool: `{readiness.get('submitted_by_this_tool')}`",
        f"- Reason: {readiness.get('reason')}",
        "",
        "## Selected Rows",
        "",
        "| rank | hash | pattern | r | mode | family | height | log disc |",
        "| ---: | --- | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("alt_composition_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('decomposition_degree_pattern')}`",
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
        "".join(f"{record.get('alt_composition_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a CPU-only 8x3/3x8 alternate-composition diagnostic queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument("--seed", type=int, default=243083)
    parser.add_argument("--max_trials", type=int, default=700)
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=2_000_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--target_rs", default="24,20,16,12,8")
    parser.add_argument("--lanes", default="8x3,3x8")
    parser.add_argument("--stop_after_candidates", type=int, default=80)
    parser.add_argument("--max_rejected_records", type=int, default=250)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = get_parser().parse_args(argv)
    rng = random.Random(int(args.seed))
    target_rs = parse_target_rs(str(args.target_rs))
    lanes = [lane.strip() for lane in str(args.lanes).split(",") if lane.strip()]
    known_hashes = known_hashes_from_pair_status(args.pair_status_json)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    rejected_counts: Counter[str] = Counter()
    rejected_counts_by_pattern: dict[str, Counter[str]] = {}
    observed_root_count_counts: Counter[str] = Counter()
    trial_pattern_counts: Counter[str] = Counter()
    trials_attempted = 0

    def bump_rejection(pattern: str, reason: str) -> None:
        rejected_counts[reason] += 1
        rejected_counts_by_pattern.setdefault(pattern, Counter())[reason] += 1

    for trial in trial_variants(rng=rng, max_trials=int(args.max_trials), lanes=lanes):
        trials_attempted += 1
        trial_pattern = str(trial.get("decomposition_degree_pattern") or "unknown")
        trial_pattern_counts[trial_pattern] += 1
        try:
            coeffs, metadata = coefficients_from_trial(trial)
        except Exception as exc:
            bump_rejection(trial_pattern, f"construction_failed:{type(exc).__name__}")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": f"construction_failed:{type(exc).__name__}"})
            continue
        metadata["alt_probe_seed"] = int(args.seed)
        metadata["alt_coefficient_height"] = coefficient_height(coeffs)
        gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)
        if not gate_ok:
            reason = ",".join(gate_failures)
            bump_rejection(trial_pattern, reason)
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": reason, "metadata": metadata})
            continue
        if coefficient_height(coeffs) > int(args.coeff_bound):
            bump_rejection(trial_pattern, "coefficient_height_exceeds_bound")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": "coefficient_height_exceeds_bound", "metadata": metadata})
            continue

        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=24,
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        pattern = str(metadata.get("decomposition_degree_pattern") or trial_pattern)
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
            bump_rejection(pattern, str(analysis.rejection_reason or "invalid"))
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": analysis.rejection_reason, "metadata": metadata})
            continue
        if int(analysis.real_root_count or -1) not in target_rs:
            bump_rejection(pattern, "real_root_count_not_target_bucket")
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
            bump_rejection(pattern, "known_or_duplicate_hash")
            if len(rejected) < int(args.max_rejected_records):
                rejected.append({"trial": trial, "rejection_reason": "known_or_duplicate_hash", "metadata": metadata})
            continue

        record = analysis_to_record(
            analysis,
            score,
            target_r=int(analysis.real_root_count or 24),
            experiment_name="alt_composition_probe",
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

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    selected_metadata = [row.get("generation_metadata") or {} for row in selected]
    selected_r_counts = Counter(str(row.get("real_root_count")) for row in selected)
    submission_readiness = build_submission_readiness(selected, target_rs)
    queue_status = (
        "manual_review_ready_not_submitted"
        if submission_readiness["worth_submitting_later"]
        else "diagnostic_too_few_valid_rows"
    )
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_alt_composition_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_alt_composition_probe.py", *argv],
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
        "lanes": lanes,
        "target_rs": target_rs,
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "trial_pattern_counts": dict(trial_pattern_counts),
        "valid_candidate_count": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_pattern_counts": dict(
            Counter(str(metadata.get("decomposition_degree_pattern") or "unknown") for metadata in selected_metadata)
        ),
        "valid_pattern_counts": dict(
            Counter(
                str((row.get("generation_metadata") or {}).get("decomposition_degree_pattern") or "unknown")
                for row in candidates
            )
        ),
        "selected_r_counts": dict(selected_r_counts),
        "valid_r_counts": dict(Counter(str(row.get("real_root_count")) for row in candidates)),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "rejected_counts_by_pattern": {
            pattern: dict(counts) for pattern, counts in sorted(rejected_counts_by_pattern.items())
        },
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "selected_family_keys": [alt_composition_family_key(row) for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "anti_basin_constraints_satisfied": [
            "degree_pattern_not_6x4",
            "not_g_x_squared_even_support",
            "support_gcd_one",
            "not_product_quadratic_low_odd_perturbation",
            "not_r24_tower_odd_escape",
        ],
        "submission_readiness": submission_readiness,
        "recommendation": (
            "prepare_for_small_manual_sair_submission_in_next_goal"
            if submission_readiness["worth_submitting_later"]
            else "diagnostic_only_refine_alternate_composition_search"
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
