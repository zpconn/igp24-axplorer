#!/usr/bin/env python3
"""Build a bounded CPU-only non-composed r=20 linear-real-root probe queue.

This lane is deliberately different from the earlier r20 quadratic-product
family. It starts from

    prod(x-a_i) * prod(x^2+b_j)

with 20 distinct nonzero integer real roots and two no-real-root quadratic
factors, then adds small low-coefficient perturbations. The base seed controls
the target real-root count directly, but the perturbation is needed to recover
irreducibility in local checks.
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

from scripts.igp24_r16_diversity_probe import coefficient_line, known_hashes_from_pair_status, multiply_polynomials
from scripts.igp24_shortlist import get_source_commit
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate


QUEUE_JSONL = "r20_linear_real_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r20_linear_real_candidate_coefficients.txt"
HASHES_TXT = "r20_linear_real_candidate_hashes.txt"
REJECTED_JSONL = "r20_linear_real_rejected_trials.jsonl"
SUMMARY_JSON = "r20_linear_real_summary.json"
REPORT_MD = "r20_linear_real_report.md"

CONSTRUCTION_FAMILY = "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation"
DECOMPOSITION_PATTERN = "20x1_plus_2x2_noncomposed"
SAFETY_NOTE = (
    "CPU-only local r20 non-composed linear-real-root probe. It does not train "
    "models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit "
    "anything."
)


def real_root_layouts() -> list[tuple[int, ...]]:
    """Return asymmetric 20-real-root layouts with small integer roots."""

    return [
        tuple(list(range(-10, 0)) + list(range(1, 10)) + [11]),
        tuple(list(range(-11, -1)) + list(range(1, 11))),
        tuple([-12, -10, -9, -8, -7, -6, -5, -4, -3, -2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        tuple([-11, -9, -8, -7, -6, -5, -4, -3, -2, -1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]),
        tuple([-10, -8, -7, -6, -5, -4, -3, -2, -1, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
    ]


def no_real_quadratic_layouts() -> list[tuple[int, int]]:
    return [(1, 2), (1, 3), (2, 5), (3, 7), (5, 6)]


def perturbation_groups() -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    return [
        ("single_low_coefficient_break", ((1, 1),)),
        ("single_low_coefficient_break", ((1, -1),)),
        ("single_low_coefficient_break", ((2, 1),)),
        ("single_low_coefficient_break", ((3, 1),)),
        ("two_low_coefficient_break", ((1, 1), (5, -1))),
        ("two_low_coefficient_break", ((1, -1), (7, 1))),
        ("two_low_coefficient_break", ((2, 1), (6, -1))),
        ("two_low_coefficient_break", ((3, -1), (9, 1))),
        ("three_low_coefficient_break", ((1, 1), (3, -1), (5, 1))),
        ("three_low_coefficient_break", ((2, -1), (4, 1), (8, -1))),
    ]


def linear_real_product_coefficients(real_roots: Iterable[int], no_real_quadratics: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for prod(x-a_i) * prod(x^2+b_j)."""

    coeffs = [1]
    for root in real_roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    for value in no_real_quadratics:
        coeffs = multiply_polynomials(coeffs, [int(value), 0, 1])
    if len(coeffs) != DEGREE + 1 or coeffs[-1] != 1:
        raise ValueError("expected a monic degree-24 polynomial")
    return [int(value) for value in coeffs[:-1]]


def support_profile(coefficients: Iterable[int]) -> dict[str, Any]:
    support = [index for index, coefficient in enumerate(coefficients) if int(coefficient) != 0]
    support.append(DEGREE)
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, int(exponent))
    return {
        "support": support,
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
        "odd_support_exponents": [exponent for exponent in support if exponent % 2 == 1],
    }


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    roots = ",".join(str(value) for value in metadata.get("r20_linear_real_roots") or [])
    no_real = ",".join(str(value) for value in metadata.get("r20_linear_no_real_quadratics") or [])
    perturbations = ",".join(
        f"{item.get('x_exponent')}:{item.get('delta')}"
        for item in metadata.get("r20_linear_coefficient_perturbations") or []
    )
    return f"{metadata.get('r20_linear_mode')}|roots={roots}|no_real={no_real}|pert={perturbations}"


def trial_variants(*, rng: random.Random, max_trials: int) -> Iterable[dict[str, Any]]:
    layouts = real_root_layouts()
    no_real = no_real_quadratic_layouts()
    groups = perturbation_groups()
    rng.shuffle(layouts)
    rng.shuffle(no_real)
    rng.shuffle(groups)
    plans: list[dict[str, Any]] = []
    for roots in layouts:
        for no_real_values in no_real:
            base = linear_real_product_coefficients(roots, no_real_values)
            for mode, perturbations in groups:
                plans.append(
                    {
                        "mode": mode,
                        "real_roots": tuple(int(value) for value in roots),
                        "no_real_quadratics": tuple(int(value) for value in no_real_values),
                        "base_coefficients": list(base),
                        "coefficient_perturbations": tuple(perturbations),
                    }
                )
    rng.shuffle(plans)
    for item in plans[: int(max_trials)]:
        yield item


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    real_roots = tuple(int(value) for value in trial["real_roots"])
    no_real = tuple(int(value) for value in trial["no_real_quadratics"])
    coeffs = [
        int(value)
        for value in trial.get("base_coefficients")
        or linear_real_product_coefficients(real_roots, no_real)
    ]
    perturbations = [(int(exponent), int(delta)) for exponent, delta in trial.get("coefficient_perturbations") or []]
    for exponent, delta in perturbations:
        coeffs[int(exponent)] += int(delta)
    profile = support_profile(coeffs)
    metadata = {
        "strategy": "r20_linear_real_roots_probe",
        "construction_family": CONSTRUCTION_FAMILY,
        "decomposition_degree_pattern": DECOMPOSITION_PATTERN,
        "seed_template": "prod_{a in real_roots}(x-a) * prod_{b in no_real_quadratics}(x^2+b)",
        "r20_linear_mode": str(trial["mode"]),
        "r20_linear_real_roots": list(real_roots),
        "r20_linear_no_real_quadratics": list(no_real),
        "r20_linear_base_real_root_count": 20,
        "r20_linear_base_no_real_quadratic_count": len(no_real),
        "r20_linear_base_is_reducible": True,
        "r20_linear_base_coefficients_before_perturbation": list(
            trial.get("base_coefficients")
            or linear_real_product_coefficients(real_roots, no_real)
        ),
        "r20_linear_coefficient_perturbations": [
            {"x_exponent": int(exponent), "delta": int(delta)} for exponent, delta in perturbations
        ],
        "r20_linear_perturbation_terms": len(perturbations),
        "r20_linear_support_after_perturbation": profile["support"],
        "r20_linear_support_gcd": profile["support_gcd"],
        "r20_linear_even_support": profile["even_support"],
        "r20_linear_odd_support_exponents": profile["odd_support_exponents"],
        "composed_support": False,
        "exact_composed_support_divisor": 1,
        "target_r_heuristic": 20,
        "solvable_family_hint": "non-composed integer-linear-root seed before irreducibility-breaking perturbation",
    }
    metadata["r20_linear_family_key"] = candidate_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def sort_key(record: dict[str, Any]) -> tuple[int, int, float, float]:
    components = record.get("score_components") or {}
    return (
        int(components.get("cycle_diversity_count") or 0),
        -int(record.get("coefficient_height") or 0),
        -float(record.get("log_abs_discriminant") or 0.0),
        float(record.get("score") or 0.0),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_mode_cap: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    for record in sorted(records, key=sort_key, reverse=True):
        metadata = record.get("generation_metadata") or {}
        family = candidate_family_key(record)
        mode = str(metadata.get("r20_linear_mode") or "unknown")
        hash_value = str(record.get("canonical_hash") or "")
        if hash_value in selected_hashes:
            continue
        if family_counts[family] >= int(per_family_cap) or mode_counts[mode] >= int(per_mode_cap):
            continue
        selected.append(record)
        selected_hashes.add(hash_value)
        family_counts[family] += 1
        mode_counts[mode] += 1
        if len(selected) >= int(limit):
            break
    for rank, record in enumerate(selected, start=1):
        record["r20_linear_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R20 Linear-Real-Root Candidate Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid r=20 candidates: {summary.get('valid_r20_candidates')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "| rank | hash | mode | no-real quadratics | perturbations | height | log disc | score |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        perturbations = ",".join(
            f"{item.get('x_exponent')}:{item.get('delta')}"
            for item in metadata.get("r20_linear_coefficient_perturbations") or []
        )
        no_real = ",".join(str(value) for value in metadata.get("r20_linear_no_real_quadratics") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("r20_linear_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r20_linear_mode')}`",
                    f"`{no_real}`",
                    f"`{perturbations}`",
                    str(row.get("coefficient_height")),
                    f"{float(row.get('log_abs_discriminant') or 0.0):.3f}",
                    f"{float(row.get('score') or 0.0):.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Caveat: these rows have local exact `r=20`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.",
            "",
            "Artifacts:",
            f"- Queue JSONL: `{summary.get('output_files', {}).get('queue_jsonl')}`",
            f"- Coefficients TXT: `{summary.get('output_files', {}).get('coefficients_txt')}`",
            f"- Hashes TXT: `{summary.get('output_files', {}).get('hashes_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
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
        "".join(f"{record.get('r20_linear_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r20 linear-real-root queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument("--seed", type=int, default=2920)
    parser.add_argument("--max_trials", type=int, default=160)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per_mode_cap", type=int, default=4)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=10**16)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    rng = random.Random(int(args.seed))
    known_hashes = known_hashes_from_pair_status(args.pair_status_json)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    rejected_counts: Counter[str] = Counter()
    observed_root_count_counts: Counter[str] = Counter()

    for trial in trial_variants(rng=rng, max_trials=int(args.max_trials)):
        trials_attempted += 1
        coeffs, metadata = coefficients_from_trial(trial)
        metadata["r20_linear_probe_seed"] = int(args.seed)
        metadata["r20_linear_coefficient_height"] = coefficient_height(coeffs)
        metadata["r20_linear_family_key"] = candidate_family_key({"generation_metadata": metadata})
        if coefficient_height(coeffs) > int(args.coeff_bound):
            rejected_counts["coefficient_height_exceeds_bound"] += 1
            rejected.append({"trial": trial, "rejection_reason": "coefficient_height_exceeds_bound", "metadata": metadata})
            continue
        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=20,
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        metadata["r20_linear_local_validation"] = {
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
        if analysis.real_root_count != 20:
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
            continue
        record = analysis_to_record(
            analysis,
            score,
            target_r=20,
            experiment_name="r20_linear_real_roots_probe",
            verification_status="proxy_scored",
            generation_metadata=metadata,
            local_search_metadata={"attempted": 0, "accepted": 0, "enabled": False},
        )
        record.update(
            {
                "source_strategy": metadata["strategy"],
                "proxy_only_caveat": SAFETY_NOTE,
                "exact_label_claimed_by_helper": False,
                "submission_path": "manual_review_only",
                "score1_target_caveat": "Local r20 non-composed row; exact 24T label must come from SAIR/Magma.",
            }
        )
        candidates.append(record)
        seen_hashes.add(analysis.canonical_hash)

    selected = select_diverse(
        candidates,
        limit=int(args.limit),
        per_mode_cap=int(args.per_mode_cap),
        per_family_cap=int(args.per_family_cap),
    )
    queue_status = "review_only_queue_ready" if selected else "diagnostic_too_few_valid_rows"
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r20_linear_real_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r20_linear_real_probe.py", *argv],
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
        "target_r": 20,
        "construction_family": CONSTRUCTION_FAMILY,
        "decomposition_pattern": DECOMPOSITION_PATTERN,
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "valid_r20_candidates": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_mode_counts": dict(Counter(str(row.get("generation_metadata", {}).get("r20_linear_mode")) for row in selected)),
        "valid_mode_counts": dict(Counter(str(row.get("generation_metadata", {}).get("r20_linear_mode")) for row in candidates)),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "recommendation": "review_only_gate_before_any_submission" if selected else "no_packet_from_this_probe",
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
