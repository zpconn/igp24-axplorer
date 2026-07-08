#!/usr/bin/env python3
"""Generate a small exact-checked r=8 score-followup pool around 24T9993."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from scripts.igp24_r8_score_followup_lane import coefficient_line
from src.igp24.polynomial import DEGREE, analysis_to_record, score_candidate


CORE_SUPPORT = (0, 6, 12, 18)
DEFAULT_TEMPLATES = ("four_positive_fibers_e", "four_positive_fibers_f")
QUARTIC_TEMPLATES = {
    "four_positive_fibers_a": {
        "coefficients_y": (1, -7, 14, -8, 1),
        "positive_quartic_roots": 4,
        "minimum_coeff_bound": 14,
        "source_pair_hint": "24T1310|r=8",
    },
    "four_positive_fibers_b": {
        "coefficients_y": (1, -8, 14, -7, 1),
        "positive_quartic_roots": 4,
        "minimum_coeff_bound": 14,
        "source_pair_hint": "24T1310|r=8",
    },
    "four_positive_fibers_c": {
        "coefficients_y": (1, -8, 15, -8, 1),
        "positive_quartic_roots": 4,
        "minimum_coeff_bound": 15,
        "source_pair_hint": "24T657|r=8",
    },
    "four_positive_fibers_d": {
        "coefficients_y": (1, -8, 16, -8, 1),
        "positive_quartic_roots": 4,
        "minimum_coeff_bound": 16,
        "source_pair_hint": "24T661|r=8",
    },
    "four_positive_fibers_e": {
        "coefficients_y": (1, -8, 16, -9, 1),
        "positive_quartic_roots": 4,
        "minimum_coeff_bound": 16,
        "source_pair_hint": "24T9993|r=8",
    },
    "four_positive_fibers_f": {
        "coefficients_y": (1, -9, 16, -8, 1),
        "positive_quartic_roots": 4,
        "minimum_coeff_bound": 16,
        "source_pair_hint": "24T9993|r=8",
    },
}


def parse_csv(value: str) -> list[str]:
    return [part.strip() for part in str(value).split(",") if part.strip()]


def support_profile(coeffs: Iterable[int]) -> dict[str, Any]:
    support = [index for index, coefficient in enumerate(coeffs) if int(coefficient) != 0]
    support.append(DEGREE)
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, int(exponent))
    return {
        "support": support,
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
    }


def base_coefficients(template_name: str) -> list[int]:
    template = QUARTIC_TEMPLATES[template_name]
    coeffs = [0] * DEGREE
    for exponent, coefficient in zip(CORE_SUPPORT, template["coefficients_y"][:4]):
        coeffs[exponent] = int(coefficient)
    return coeffs


def perturbation_mode(count: int) -> str:
    return {
        1: "odd_single_off_core",
        2: "odd_pair_off_core",
        3: "odd_triple_off_core",
    }.get(count, "odd_multi_off_core")


def sample_perturbations(rng: random.Random, *, max_terms: int) -> list[tuple[int, int]]:
    odd_exponents = [exponent for exponent in range(1, DEGREE, 2) if exponent not in CORE_SUPPORT]
    weights = [0.45, 0.40, 0.15]
    choices = list(range(1, max_terms + 1))
    while len(weights) < len(choices):
        weights.append(0.05)
    count = rng.choices(choices, weights=weights[: len(choices)], k=1)[0]
    exponents = rng.sample(odd_exponents, k=count)
    return [(exponent, rng.choice([-1, 1])) for exponent in sorted(exponents)]


def metadata_for(
    *,
    template_name: str,
    perturbations: list[tuple[int, int]],
    trial_index: int,
    seed: int,
    coeff_bound: int,
    analysis_r: int | None,
) -> dict[str, Any]:
    template = QUARTIC_TEMPLATES[template_name]
    mode = perturbation_mode(len(perturbations))
    perturbation_key = ",".join(f"{exponent}:{coefficient}" for exponent, coefficient in perturbations)
    return {
        "strategy": "r8_quartic_lift_score_followup",
        "resolved_generation_strategy": "r8_quartic_lift_score_followup",
        "source_family": "r8_quartic_lift_score_followup",
        "generation_strategy": "r8_score_followup_24T9993",
        "seed_template": "perturbed_g(y)_with_four_positive_roots_and_y=x^6",
        "source_signal_pair": "24T9993|r=8",
        "source_pair_hint": template["source_pair_hint"],
        "r8_quartic_lift_family_key": f"{template_name}:{mode}:{perturbation_key}",
        "r8_quartic_lift_template_name": template_name,
        "r8_quartic_lift_core_support": list(CORE_SUPPORT),
        "r8_quartic_lift_coefficients_y": list(template["coefficients_y"]),
        "r8_quartic_lift_positive_quartic_roots": int(template["positive_quartic_roots"]),
        "r8_quartic_lift_minimum_coeff_bound": int(template["minimum_coeff_bound"]),
        "r8_quartic_lift_perturbation": "score_signal_template_odd_off_core_support_gcd_1",
        "r8_quartic_lift_perturbation_mode": mode,
        "r8_quartic_lift_perturbation_exponents": [int(exponent) for exponent, _ in perturbations],
        "r8_quartic_lift_perturbation_coefficients": {
            str(exponent): int(coefficient) for exponent, coefficient in perturbations
        },
        "r8_quartic_lift_support_gcd": 1,
        "r8_quartic_lift_even_support": False,
        "target_r_heuristic": 8,
        "validated_real_root_count": analysis_r,
        "generation_seed": int(seed),
        "generation_trial_index": int(trial_index),
        "coeff_bound": int(coeff_bound),
    }


def generate_records(
    *,
    seed: int,
    templates: list[str],
    max_trials: int,
    limit: int,
    coeff_bound: int,
    prime_limit: int,
    exact_score_timeout: float,
    max_terms: int,
    max_rejected_records: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(seed)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    seen_lines: set[str] = set()
    rejection_counts: Counter[str] = Counter()
    trial_template_counts: Counter[str] = Counter()
    for trial_index in range(max_trials):
        template_name = rng.choice(templates)
        trial_template_counts[template_name] += 1
        coeffs = base_coefficients(template_name)
        perturbations = sample_perturbations(rng, max_terms=max_terms)
        for exponent, coefficient in perturbations:
            coeffs[int(exponent)] = int(coefficient)
        profile = support_profile(coeffs)
        if profile["support_gcd"] != 1 or profile["even_support"]:
            rejection_counts["support_profile_rejected"] += 1
            continue
        score, analysis = score_candidate(
            coeffs,
            coeff_bound=coeff_bound,
            target_r=8,
            prime_limit=prime_limit,
            exact_score_timeout=exact_score_timeout,
            seen_hashes=seen_hashes,
        )
        metadata = metadata_for(
            template_name=template_name,
            perturbations=perturbations,
            trial_index=trial_index,
            seed=seed,
            coeff_bound=coeff_bound,
            analysis_r=analysis.real_root_count,
        )
        record = analysis_to_record(
            analysis,
            score,
            target_r=8,
            experiment_name="r8_score_followup_24T9993",
            verification_status="proxy_scored" if analysis.valid else "rejected",
            generation_metadata=metadata,
            local_search_metadata={"attempted": 0, "accepted": 0, "status": "not_run"},
        )
        line = coefficient_line(record.get("exported_coefficients"))
        if not analysis.valid:
            rejection_counts[analysis.rejection_reason or "invalid"] += 1
            if len(rejected) < max_rejected_records:
                rejected.append(record)
            continue
        if analysis.real_root_count != 8:
            rejection_counts[f"real_root_count_{analysis.real_root_count}"] += 1
            if len(rejected) < max_rejected_records:
                rejected.append(record)
            continue
        if analysis.canonical_hash in seen_hashes or line in seen_lines:
            rejection_counts["duplicate"] += 1
            continue
        accepted.append(record)
        seen_hashes.add(analysis.canonical_hash)
        seen_lines.add(line)
        if len(accepted) >= limit:
            break
    summary = {
        "record_type": "igp24_r8_score_followup_generation_summary",
        "seed": int(seed),
        "templates": templates,
        "max_trials": int(max_trials),
        "trials_run": sum(trial_template_counts.values()),
        "accepted_rows": len(accepted),
        "rejected_rows_recorded": len(rejected),
        "rejection_reason_counts": dict(rejection_counts),
        "trial_template_counts": dict(trial_template_counts),
        "accepted_template_counts": dict(
            Counter((row.get("generation_metadata") or {}).get("r8_quartic_lift_template_name") for row in accepted)
        ),
        "accepted_perturbation_mode_counts": dict(
            Counter((row.get("generation_metadata") or {}).get("r8_quartic_lift_perturbation_mode") for row in accepted)
        ),
        "accepted_mod_p_signature_counts": dict(
            Counter(
                ";".join(
                    f"p{pat['prime']}:{'-'.join(str(v) for v in pat.get('degrees') or [])}"
                    for pat in row.get("mod_p_factorization_degree_patterns") or []
                )
                for row in accepted
            )
        ),
        "requires_sympy": True,
        "calls_sair": False,
        "auto_submits": False,
    }
    return accepted, rejected, summary


def write_report(summary: dict[str, Any], output_files: dict[str, str]) -> str:
    return "\n".join(
        [
            "# r8 Score-Followup Generation",
            "",
            f"- Source signal pair: `24T9993|r=8`",
            f"- Templates: `{json.dumps(summary['templates'])}`",
            f"- Trials run: `{summary['trials_run']}`",
            f"- Accepted exact r8 rows: `{summary['accepted_rows']}`",
            f"- Rejection counts: `{json.dumps(summary['rejection_reason_counts'], sort_keys=True)}`",
            f"- Accepted templates: `{json.dumps(summary['accepted_template_counts'], sort_keys=True)}`",
            f"- Accepted perturbation modes: `{json.dumps(summary['accepted_perturbation_mode_counts'], sort_keys=True)}`",
            "",
            "## Outputs",
            *(f"- {name}: `{path}`" for name, path in output_files.items()),
            "",
            "This generator performs local exact checks only and does not call SAIR.",
            "",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a bounded r8 score-followup pool around 24T9993")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3201)
    parser.add_argument("--templates", default=",".join(DEFAULT_TEMPLATES))
    parser.add_argument("--max_trials", type=int, default=240)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--coeff_bound", type=int, default=16)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=3.0)
    parser.add_argument("--max_terms", type=int, default=3)
    parser.add_argument("--max_rejected_records", type=int, default=100)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    templates = parse_csv(args.templates)
    unknown = [template for template in templates if template not in QUARTIC_TEMPLATES]
    if unknown:
        raise SystemExit(f"unknown templates: {','.join(unknown)}")
    accepted, rejected, summary = generate_records(
        seed=int(args.seed),
        templates=templates,
        max_trials=int(args.max_trials),
        limit=int(args.limit),
        coeff_bound=int(args.coeff_bound),
        prime_limit=int(args.prime_limit),
        exact_score_timeout=float(args.exact_score_timeout),
        max_terms=int(args.max_terms),
        max_rejected_records=int(args.max_rejected_records),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "candidates_jsonl": str(args.output_dir / "generated_candidates.jsonl"),
        "rejected_jsonl": str(args.output_dir / "generated_rejected.jsonl"),
        "summary_json": str(args.output_dir / "generation_summary.json"),
        "report_md": str(args.output_dir / "generation_report.md"),
    }
    for name, rows in (("candidates_jsonl", accepted), ("rejected_jsonl", rejected)):
        with Path(output_files[name]).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    summary = {
        **summary,
        "output_files": output_files,
        "command": [sys.executable, "scripts/igp24_r8_score_followup_generate.py", *(argv or sys.argv[1:])],
    }
    Path(output_files["summary_json"]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(output_files["report_md"]).write_text(write_report(summary, output_files), encoding="utf-8")
    print(f"trials_run\t{summary['trials_run']}")
    print(f"accepted_rows\t{summary['accepted_rows']}")
    print(f"candidates_jsonl\t{output_files['candidates_jsonl']}")
    print(f"summary_json\t{output_files['summary_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
