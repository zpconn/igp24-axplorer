#!/usr/bin/env python3
"""Build a small CPU-only r=20 high-real-root probe queue.

The construction starts from products of ten positive quadratic factors and
two no-real-root quadratic factors:

    prod(x^2-a) * prod(x^2+b)

The base seed has exactly 20 real roots but is reducible. Small low-odd
perturbations are then used to test whether irreducibility can be recovered
while preserving the high-real-root count.
"""

from __future__ import annotations

import argparse
import json
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


QUEUE_JSONL = "r20_high_real_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r20_high_real_candidate_coefficients.txt"
HASHES_TXT = "r20_high_real_candidate_hashes.txt"
REJECTED_JSONL = "r20_high_real_rejected_trials.jsonl"
SUMMARY_JSON = "r20_high_real_summary.json"
REPORT_MD = "r20_high_real_report.md"

SAFETY_NOTE = (
    "CPU-only local r20 high-real-root probe. It does not train models, use a "
    "GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything."
)


def positive_quadratic_root_layouts() -> list[tuple[int, ...]]:
    """Return bounded ten-positive-root layouts for ``prod(x^2-a)`` seeds."""

    return [
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 11),
        (1, 2, 3, 4, 5, 6, 7, 8, 10, 11),
        (1, 2, 3, 4, 5, 6, 7, 9, 10, 11),
        (1, 2, 3, 4, 5, 6, 8, 9, 10, 11),
        (1, 2, 3, 4, 5, 7, 8, 9, 10, 11),
        (1, 2, 3, 4, 6, 7, 8, 9, 10, 11),
        (1, 2, 3, 5, 6, 7, 8, 9, 10, 11),
    ]


def negative_quadratic_layouts() -> list[tuple[int, int]]:
    """Return two-factor layouts for the no-real-root factors ``x^2+b``."""

    return [
        (1, 2),
        (1, 3),
        (2, 3),
        (1, 5),
        (2, 5),
        (3, 5),
    ]


def mixed_quadratic_product_coefficients(
    positive_roots: Iterable[int],
    negative_roots: Iterable[int],
) -> list[int]:
    """Return [a0, ..., a23] for ``prod(x^2-a) * prod(x^2+b)``."""

    coeffs = [1]
    for root in positive_roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 0, 1])
    for root in negative_roots:
        coeffs = multiply_polynomials(coeffs, [int(root), 0, 1])
    if len(coeffs) != DEGREE + 1 or coeffs[-1] != 1:
        raise ValueError("expected a monic degree-24 mixed quadratic product")
    return [int(value) for value in coeffs[:-1]]


def low_odd_perturbations() -> list[tuple[int, int]]:
    return [(exponent, delta) for exponent in (1, 3, 5, 7, 9, 11) for delta in (-2, -1, 1, 2)]


def trial_variants(*, rng: random.Random, max_trials: int) -> Iterable[dict[str, Any]]:
    """Yield deterministic bounded perturbation plans."""

    positive_layouts = positive_quadratic_root_layouts()
    negative_layouts = negative_quadratic_layouts()
    singles = low_odd_perturbations()
    rng.shuffle(positive_layouts)
    rng.shuffle(negative_layouts)
    rng.shuffle(singles)

    plans: list[dict[str, Any]] = []
    for positive_roots in positive_layouts:
        for negative_roots in negative_layouts:
            base = mixed_quadratic_product_coefficients(positive_roots, negative_roots)
            for exponent, delta in singles:
                plans.append(
                    {
                        "mode": "single_low_odd_break",
                        "positive_quadratic_roots": positive_roots,
                        "negative_quadratic_roots": negative_roots,
                        "base_coefficients": list(base),
                        "odd_perturbations": [(exponent, delta)],
                    }
                )

            two_groups = [
                ((1, 1), (5, 1)),
                ((1, -1), (5, 1)),
                ((1, 1), (7, -1)),
                ((3, 1), (7, 1)),
                ((3, -1), (9, 1)),
                ((5, 1), (11, -1)),
            ]
            three_groups = [
                ((1, 1), (3, -1), (5, 1)),
                ((1, -1), (3, 1), (7, 1)),
                ((1, 1), (5, -1), (9, 1)),
                ((3, 1), (7, -1), (11, 1)),
            ]
            for group in two_groups:
                plans.append(
                    {
                        "mode": "two_low_odd_break",
                        "positive_quadratic_roots": positive_roots,
                        "negative_quadratic_roots": negative_roots,
                        "base_coefficients": list(base),
                        "odd_perturbations": list(group),
                    }
                )
            for group in three_groups:
                plans.append(
                    {
                        "mode": "three_low_odd_break",
                        "positive_quadratic_roots": positive_roots,
                        "negative_quadratic_roots": negative_roots,
                        "base_coefficients": list(base),
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
    positive_roots = tuple(int(value) for value in trial["positive_quadratic_roots"])
    negative_roots = tuple(int(value) for value in trial["negative_quadratic_roots"])
    coeffs = [
        int(value)
        for value in trial.get("base_coefficients")
        or mixed_quadratic_product_coefficients(positive_roots, negative_roots)
    ]
    perturbations = normalize_perturbations(trial.get("odd_perturbations"))
    for exponent, delta in perturbations:
        coeffs[int(exponent)] += int(delta)
    support = sorted(index for index, value in enumerate(coeffs) if int(value) != 0)
    odd_support = sorted(index for index in support if index % 2 == 1)
    metadata = {
        "strategy": "r20_high_real_mixed_quadratic_product_probe",
        "construction_family": "ten_positive_two_negative_quadratic_product_plus_low_odd_perturbation",
        "seed_template": "prod_{a in positive_roots}(x^2-a) * prod_{b in negative_roots}(x^2+b)",
        "r20_high_real_mode": str(trial["mode"]),
        "r20_high_real_positive_quadratic_roots": list(positive_roots),
        "r20_high_real_negative_quadratic_roots": list(negative_roots),
        "r20_high_real_base_coefficients_before_perturbation": list(
            trial.get("base_coefficients")
            or mixed_quadratic_product_coefficients(positive_roots, negative_roots)
        ),
        "r20_high_real_base_degree": 24,
        "r20_high_real_base_real_root_count": 20,
        "r20_high_real_base_is_reducible": True,
        "r20_high_real_odd_perturbations": [
            {"x_exponent": int(exponent), "delta": int(delta)} for exponent, delta in perturbations
        ],
        "r20_high_real_perturbation_mode": str(trial["mode"]),
        "r20_high_real_perturbation_terms": len(perturbations),
        "r20_high_real_odd_support_after_perturbation": odd_support,
        "r20_high_real_support_after_perturbation": support,
        "r20_high_real_exact_composed_seed_divisor": 2,
        "r20_high_real_near_composed_support_divisor": 2,
        "composed_support": False,
        "near_composed_support_divisor": 2,
        "target_r_heuristic": 20,
        "solvable_family_hint": "reducible high-real mixed quadratic product seed before irreducibility-breaking perturbation",
    }
    metadata["r20_high_real_family_key"] = candidate_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    positives = ",".join(str(value) for value in metadata.get("r20_high_real_positive_quadratic_roots") or [])
    negatives = ",".join(str(value) for value in metadata.get("r20_high_real_negative_quadratic_roots") or [])
    exponents = ",".join(
        str(item.get("x_exponent")) for item in metadata.get("r20_high_real_odd_perturbations") or []
    )
    return f"{metadata.get('r20_high_real_mode')}|pos={positives}|neg={negatives}|odd={exponents}"


def sort_key(record: dict[str, Any]) -> tuple[float, float, int, float, int]:
    components = record.get("score_components") or {}
    return (
        -float(record.get("coefficient_height") or 0.0),
        -float(record.get("log_abs_discriminant") or 0.0),
        int(components.get("cycle_diversity_count") or 0),
        float(record.get("score") or 0.0),
        -int(record.get("generation_metadata", {}).get("r20_high_real_perturbation_terms") or 0),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key, reverse=True)
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for record in rows:
        mode = str((record.get("generation_metadata") or {}).get("r20_high_real_mode") or "unknown")
        by_mode.setdefault(mode, []).append(record)
    mode_order = sorted(by_mode, key=lambda mode: sort_key(by_mode[mode][0]), reverse=True)

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

    if len(selected) < int(limit):
        for record in rows:
            family = candidate_family_key(record)
            hash_value = str(record.get("canonical_hash") or "")
            if family_counts[family] >= int(per_family_cap) or hash_value in selected_hashes:
                continue
            selected.append(record)
            selected_hashes.add(hash_value)
            family_counts[family] += 1
            if len(selected) >= int(limit):
                break
    for rank, record in enumerate(selected, start=1):
        record["r20_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R20 High-Real-Root Candidate Queue",
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
        "| rank | hash | mode | positive roots | negative roots | odd perturbations | height | log disc | score |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        perturbations = ",".join(
            f"{item.get('x_exponent')}:{item.get('delta')}"
            for item in metadata.get("r20_high_real_odd_perturbations") or []
        )
        positives = ",".join(str(value) for value in metadata.get("r20_high_real_positive_quadratic_roots") or [])
        negatives = ",".join(str(value) for value in metadata.get("r20_high_real_negative_quadratic_roots") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("r20_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r20_high_real_mode')}`",
                    f"`{positives}`",
                    f"`{negatives}`",
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
        "".join(f"{record.get('r20_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r20 high-real-root queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument("--seed", type=int, default=2020)
    parser.add_argument("--max_trials", type=int, default=160)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=100_000_000)
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
    best_root_count_counts: Counter[str] = Counter()

    for trial in trial_variants(rng=rng, max_trials=int(args.max_trials)):
        trials_attempted += 1
        coeffs, metadata = coefficients_from_trial(trial)
        metadata["r20_high_real_probe_seed"] = int(args.seed)
        metadata["r20_high_real_coefficient_height"] = coefficient_height(coeffs)
        metadata["r20_high_real_family_key"] = candidate_family_key({"generation_metadata": metadata})
        if coefficient_height(coeffs) > int(args.coeff_bound):
            rejected_counts["coefficient_height_exceeds_bound"] += 1
            rejected.append({"trial": trial, "rejection_reason": "coefficient_height_exceeds_bound"})
            continue
        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=20,
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        metadata["r20_high_real_local_validation"] = {
            "valid": bool(analysis.valid),
            "real_root_count": analysis.real_root_count,
            "irreducible": analysis.irreducible,
            "squarefree": analysis.squarefree,
            "canonical_hash": analysis.canonical_hash,
            "rejection_reason": analysis.rejection_reason,
        }
        if analysis.real_root_count is not None:
            best_root_count_counts[str(analysis.real_root_count)] += 1
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
            experiment_name="r20_high_real_mixed_quadratic_product_probe",
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
                "score1_target_caveat": "Local r20 high-real-root row; exact 24T label must come from SAIR/Magma.",
            }
        )
        candidates.append(record)
        seen_hashes.add(analysis.canonical_hash)

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    queue_status = "manual_queue_ready" if len(selected) >= min(6, int(args.limit)) else "diagnostic_too_few_valid_rows"
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r20_high_real_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r20_high_real_probe.py", *argv],
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
        "construction_family": "ten_positive_two_negative_quadratic_product_plus_low_odd_perturbation",
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "valid_r20_candidates": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_mode_counts": dict(Counter(str(row.get("generation_metadata", {}).get("r20_high_real_mode")) for row in selected)),
        "valid_mode_counts": dict(Counter(str(row.get("generation_metadata", {}).get("r20_high_real_mode")) for row in candidates)),
        "observed_root_count_counts": dict(best_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "recommendation": "manual_review_then_submit_small_r20_probe"
        if selected
        else "r20_prototype_failed_try_structure_preserving_r24_or_return_to_r8",
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
