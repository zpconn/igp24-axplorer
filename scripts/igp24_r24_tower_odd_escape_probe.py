#!/usr/bin/env python3
"""Build a CPU-only r=24 odd-perturbed tower escape queue.

The previous exact r24 tower queue avoided generic ``24T25000`` but landed in
the globally covered ``24T23883/24T24651`` tower basin. This helper keeps the
same all-real degree-6-by-degree-4 tower seed, then adds small odd-power
perturbations in ``x`` itself. That deliberately breaks exact even support
while preserving local exact ``r=24`` when the perturbation is gentle enough.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_r12_tower_probe import compose_outer_inner, inner_quartic_coefficients, outer_from_roots  # noqa: E402
from scripts.igp24_r16_diversity_probe import coefficient_line, known_hashes_from_pair_status  # noqa: E402
from scripts.igp24_r24_tower_probe import r24_outer_root_layouts  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate  # noqa: E402


QUEUE_JSONL = "r24_tower_odd_escape_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r24_tower_odd_escape_candidate_coefficients.txt"
HASHES_TXT = "r24_tower_odd_escape_candidate_hashes.txt"
REJECTED_JSONL = "r24_tower_odd_escape_rejected_trials.jsonl"
SUMMARY_JSON = "r24_tower_odd_escape_summary.json"
REPORT_MD = "r24_tower_odd_escape_report.md"

SAFETY_NOTE = (
    "CPU-only local r24 odd-perturbed tower escape probe. It does not train "
    "models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit "
    "anything."
)


def support_summary(coeffs: Iterable[int]) -> dict[str, Any]:
    support = [index for index, value in enumerate(coeffs) if int(value) != 0]
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


def odd_escape_groups() -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    groups: list[tuple[str, tuple[tuple[int, int], ...]]] = []
    for exponent in (1, 3, 5, 7, 9, 11, 13, 15):
        for delta in (-3, -2, -1, 1, 2, 3):
            groups.append(("single_odd_tower_escape", ((exponent, delta),)))
    for exponent_a, exponent_b in ((1, 5), (1, 9), (3, 7), (5, 11), (7, 13), (9, 15)):
        for delta_a, delta_b in ((1, -1), (1, 1), (-1, 1), (2, -1), (-2, 1)):
            groups.append(("two_odd_tower_escape", ((exponent_a, delta_a), (exponent_b, delta_b))))
    return groups


def trial_variants(*, rng: random.Random, max_trials: int) -> Iterable[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    groups = odd_escape_groups()
    inner_parameters = [6, 7, 8, 9, 10, 11, 12, 13]
    rng.shuffle(inner_parameters)
    rng.shuffle(groups)
    for s_value in inner_parameters:
        inner = inner_quartic_coefficients(s_value)
        layouts = r24_outer_root_layouts(s_value, max_layouts=100)
        rng.shuffle(layouts)
        for layout in layouts[:25]:
            roots = tuple(int(value) for value in layout["outer_roots"])
            outer = outer_from_roots(roots)
            base_coeffs = compose_outer_inner(outer, inner)
            for mode, group in groups:
                plans.append(
                    {
                        "mode": mode,
                        "inner_parameter_s": int(s_value),
                        "inner_coefficients": list(inner),
                        "outer_roots": roots,
                        "four_real_preimage_levels": list(layout["four_real_preimage_levels"]),
                        "outer_coefficients": list(outer),
                        "base_tower_coefficients": list(base_coeffs),
                        "odd_perturbations": list(group),
                    }
                )
    rng.shuffle(plans)
    for item in plans[: int(max_trials)]:
        yield item


def normalize_perturbations(raw: Any) -> list[tuple[int, int]]:
    perturbations: list[tuple[int, int]] = []
    for item in raw or []:
        if isinstance(item, dict):
            perturbations.append((int(item["x_exponent"]), int(item["delta"])))
        else:
            perturbations.append((int(item[0]), int(item[1])))
    return perturbations


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    inner = [int(value) for value in trial.get("inner_coefficients") or inner_quartic_coefficients(trial["inner_parameter_s"])]
    outer = [int(value) for value in trial.get("outer_coefficients") or outer_from_roots(trial["outer_roots"])]
    base_coeffs = [
        int(value)
        for value in trial.get("base_tower_coefficients")
        or compose_outer_inner(outer, inner)
    ]
    coeffs = list(base_coeffs)
    perturbations = normalize_perturbations(trial.get("odd_perturbations"))
    for exponent, delta in perturbations:
        if not 0 <= int(exponent) < DEGREE:
            raise ValueError("odd tower escape perturbations must target free degree-24 coefficients")
        if int(exponent) % 2 == 0:
            raise ValueError("odd tower escape perturbations must use odd x exponents")
        coeffs[int(exponent)] += int(delta)

    support = support_summary(coeffs)
    metadata = {
        "strategy": "r24_tower_odd_escape_probe",
        "construction_family": "odd_perturbed_r24_6x4_tower_escape",
        "base_construction_family": "outer_degree6_all_four_real_preimage_composed_with_even_quartic_double_well",
        "decomposition_type": "near_composition_after_odd_escape",
        "decomposition_degree_pattern": "6x4_seed_plus_odd_x_perturbation",
        "tower_expression": "h(q(x)) + odd x-power perturbations, q(x)=x^4-s*x^2",
        "r24_tower_odd_escape_mode": str(trial["mode"]),
        "r24_tower_odd_escape_inner_parameter_s": int(trial["inner_parameter_s"]),
        "r24_tower_odd_escape_inner_polynomial_coefficients": list(inner),
        "r24_tower_odd_escape_outer_roots_before_perturbation": [int(value) for value in trial["outer_roots"]],
        "r24_tower_odd_escape_outer_four_real_preimage_levels": [
            int(value) for value in trial.get("four_real_preimage_levels") or []
        ],
        "r24_tower_odd_escape_outer_coefficients": list(outer),
        "r24_tower_odd_escape_base_tower_coefficients": list(base_coeffs),
        "r24_tower_odd_escape_odd_perturbations": [
            {"x_exponent": int(exponent), "delta": int(delta)} for exponent, delta in perturbations
        ],
        "r24_tower_odd_escape_perturbation_terms": len(perturbations),
        "r24_tower_odd_escape_support_after_perturbation": support["support_exponents"],
        "r24_tower_odd_escape_odd_support_exponents": support["odd_support_exponents"],
        "r24_tower_odd_escape_support_gcd": support["support_gcd"],
        "r24_tower_odd_escape_even_support_after_perturbation": support["even_support"],
        "r24_tower_odd_escape_base_exact_composition": True,
        "r24_tower_odd_escape_exact_composition_after_perturbation": False,
        "r24_tower_odd_escape_all_outer_levels_have_four_real_preimages": True,
        "r24_tower_odd_escape_expected_real_root_count": 24,
        "target_r_heuristic": 24,
        "composed_support": False,
        "near_composed_support_divisor": 2,
        "anti_basin_features": [
            "breaks_exact_even_support",
            "support_gcd_one_after_odd_perturbation",
            "not_outer_constant_shift_only",
            "retains_all_real_6x4_tower_seed",
        ],
        "structural_difference_from_previous_r24_tower_lane": (
            "starts from the accepted all-real 6x4 tower seed but adds odd x-power perturbations, "
            "so the selected row is no longer exact even support or an outer constant shift"
        ),
        "target_plan_alignment": "live SAIR target plan ranks r=24 as the largest remaining bucket",
    }
    metadata["r24_tower_odd_escape_family_key"] = candidate_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    levels = ",".join(str(value) for value in metadata.get("r24_tower_odd_escape_outer_four_real_preimage_levels") or [])
    perturbations = ",".join(
        f"{item.get('x_exponent')}:{item.get('delta')}"
        for item in metadata.get("r24_tower_odd_escape_odd_perturbations") or []
    )
    return (
        f"s={metadata.get('r24_tower_odd_escape_inner_parameter_s')}"
        f"|mode={metadata.get('r24_tower_odd_escape_mode')}"
        f"|real={levels}|odd_x={perturbations}"
    )


def sort_key(record: dict[str, Any]) -> tuple[int, int, float, int]:
    components = record.get("score_components") or {}
    metadata = record.get("generation_metadata") or {}
    return (
        int(record.get("coefficient_height") or 0),
        -int(components.get("cycle_diversity_count") or 0),
        float(record.get("log_abs_discriminant") or 0.0),
        int(metadata.get("r24_tower_odd_escape_perturbation_terms") or 0),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key)
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for record in rows:
        mode = str((record.get("generation_metadata") or {}).get("r24_tower_odd_escape_mode") or "unknown")
        by_mode.setdefault(mode, []).append(record)
    mode_order = sorted(by_mode, key=lambda mode: sort_key(by_mode[mode][0]))

    progressed = True
    while len(selected) < int(limit) and progressed:
        progressed = False
        for mode in mode_order:
            candidates = by_mode.get(mode) or []
            while candidates:
                record = candidates.pop(0)
                family = candidate_family_key(record)
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
        family = candidate_family_key(record)
        hash_value = str(record.get("canonical_hash") or "")
        if family_counts[family] >= int(per_family_cap) or hash_value in selected_hashes:
            continue
        selected.append(record)
        selected_hashes.add(hash_value)
        family_counts[family] += 1
    for rank, record in enumerate(selected, start=1):
        record["r24_tower_odd_escape_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R24 Tower Odd-Escape Candidate Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid r=24 candidates: {summary.get('valid_r24_candidates')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Selected mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Selected inner-s counts: `{json.dumps(summary.get('selected_inner_s_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "Anti-basin rationale: every selected row has odd support, support gcd 1, and is not an exact even outer-constant-shift tower.",
        "",
        "| rank | hash | mode | s | levels | odd perturbations | height | log disc |",
        "| ---: | --- | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        perturbations = ",".join(
            f"{item.get('x_exponent')}:{item.get('delta')}"
            for item in metadata.get("r24_tower_odd_escape_odd_perturbations") or []
        )
        levels = ",".join(
            str(value) for value in metadata.get("r24_tower_odd_escape_outer_four_real_preimage_levels") or []
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("r24_tower_odd_escape_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r24_tower_odd_escape_mode')}`",
                    str(metadata.get("r24_tower_odd_escape_inner_parameter_s")),
                    f"`{levels}`",
                    f"`{perturbations}`",
                    str(row.get("coefficient_height")),
                    f"{float(row.get('log_abs_discriminant') or 0.0):.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.",
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
            f"{record.get('r24_tower_odd_escape_queue_rank')}\t{record.get('canonical_hash')}\n"
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r24 odd-perturbed tower escape queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument(
        "--target_plan_json",
        type=Path,
        default=REPO_ROOT / "data/igp24/sair_live_target_plan_20260707/sair_live_target_plan_summary.json",
    )
    parser.add_argument("--seed", type=int, default=242405)
    parser.add_argument("--max_trials", type=int, default=900)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=2_000_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    rng = random.Random(int(args.seed))
    known_hashes = known_hashes_from_pair_status(args.pair_status_json)
    target_plan = json.loads(args.target_plan_json.read_text(encoding="utf-8")) if args.target_plan_json.exists() else {}
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    rejected_counts: Counter[str] = Counter()
    observed_root_count_counts: Counter[str] = Counter()

    for trial in trial_variants(rng=rng, max_trials=int(args.max_trials)):
        trials_attempted += 1
        coeffs, metadata = coefficients_from_trial(trial)
        metadata["r24_tower_odd_escape_probe_seed"] = int(args.seed)
        metadata["r24_tower_odd_escape_coefficient_height"] = coefficient_height(coeffs)
        if metadata["r24_tower_odd_escape_even_support_after_perturbation"] is not False:
            rejected_counts["did_not_break_even_support"] += 1
            rejected.append({"trial": trial, "rejection_reason": "did_not_break_even_support", "metadata": metadata})
            continue
        if metadata["r24_tower_odd_escape_support_gcd"] != 1:
            rejected_counts["support_gcd_not_one"] += 1
            rejected.append({"trial": trial, "rejection_reason": "support_gcd_not_one", "metadata": metadata})
            continue
        if coefficient_height(coeffs) > int(args.coeff_bound):
            rejected_counts["coefficient_height_exceeds_bound"] += 1
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
        metadata["r24_tower_odd_escape_local_validation"] = {
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
            rejected_counts[str(analysis.rejection_reason or "invalid")] += 1
            rejected.append({"trial": trial, "rejection_reason": analysis.rejection_reason, "metadata": metadata})
            continue
        if analysis.real_root_count != 24:
            rejected_counts["real_root_count_mismatch"] += 1
            rejected.append(
                {
                    "trial": trial,
                    "real_root_count": analysis.real_root_count,
                    "canonical_hash": analysis.canonical_hash,
                    "metadata": metadata,
                }
            )
            continue
        if analysis.canonical_hash in known_hashes or analysis.canonical_hash in seen_hashes:
            rejected_counts["known_or_duplicate_hash"] += 1
            rejected.append({"trial": trial, "rejection_reason": "known_or_duplicate_hash", "metadata": metadata})
            continue
        record = analysis_to_record(
            analysis,
            score,
            target_r=24,
            experiment_name="r24_tower_odd_escape_probe",
            verification_status="proxy_scored",
            generation_metadata=metadata,
            local_search_metadata={"attempted": 0, "accepted": 0, "enabled": False},
        )
        record.update(
            {
                "source_strategy": metadata["strategy"],
                "proxy_only_caveat": SAFETY_NOTE,
                "exact_label_claimed_by_helper": False,
                "submission_path": "api_dry_run_then_explicit_small_probe_only",
                "score1_target_caveat": "Local r24 odd-perturbed tower row; exact 24T label must come from SAIR/Magma.",
            }
        )
        candidates.append(record)
        seen_hashes.add(str(analysis.canonical_hash))

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    selected_metadata = [row.get("generation_metadata") or {} for row in selected]
    queue_status = "api_dry_run_ready" if len(selected) >= min(6, int(args.limit)) else "diagnostic_too_few_valid_rows"
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r24_tower_odd_escape_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r24_tower_odd_escape_probe.py", *argv],
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
        "target_plan_json": str(args.target_plan_json),
        "target_plan_primary_target": target_plan.get("primary_target"),
        "target_plan_top_remaining_rs": target_plan.get("top_remaining_rs"),
        "target_r": 24,
        "construction_family": "odd_perturbed_r24_6x4_tower_escape",
        "decomposition_degree_pattern": "6x4_seed_plus_odd_x_perturbation",
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "valid_r24_candidates": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_mode_counts": dict(
            Counter(str(metadata.get("r24_tower_odd_escape_mode") or "unknown") for metadata in selected_metadata)
        ),
        "valid_mode_counts": dict(
            Counter(
                str((row.get("generation_metadata") or {}).get("r24_tower_odd_escape_mode") or "unknown")
                for row in candidates
            )
        ),
        "selected_inner_s_counts": dict(
            Counter(str(metadata.get("r24_tower_odd_escape_inner_parameter_s") or "unknown") for metadata in selected_metadata)
        ),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "selected_family_keys": [candidate_family_key(row) for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "anti_basin_constraints_satisfied": [
            "non_even_support",
            "support_gcd_one",
            "not_outer_constant_shift_only",
            "not_exact_even_6x4_tower_after_perturbation",
        ],
        "structure_preservation": "starts from all-real h(q(x)) degree-6-by-degree-4 tower seed, then breaks exact even support with odd x perturbations",
        "recommendation": "api_dry_run_then_small_submission_probe"
        if selected
        else "diagnostic_only_try_alternate_composition_pattern",
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
