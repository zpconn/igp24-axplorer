#!/usr/bin/env python3
"""Build a small CPU-only r=12 exact-composed structured probe queue.

The construction keeps exact divisor-2 composed support. It starts from a
degree-12 base polynomial ``g(y)`` with six positive and six negative real
roots, then perturbs coefficients inside ``g`` before lifting to ``g(x^2)``.
This is deliberately different from the r16/r20/r24 low-odd perturbation
lanes: no odd powers of ``x`` are introduced.
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


QUEUE_JSONL = "r12_structured_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r12_structured_candidate_coefficients.txt"
HASHES_TXT = "r12_structured_candidate_hashes.txt"
REJECTED_JSONL = "r12_structured_rejected_trials.jsonl"
SUMMARY_JSON = "r12_structured_summary.json"
REPORT_MD = "r12_structured_report.md"

SAFETY_NOTE = (
    "CPU-only local r12 exact-composed structured probe. It does not train "
    "models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit "
    "anything."
)


def positive_base_root_layouts() -> list[tuple[int, ...]]:
    """Return six-positive-root layouts for the degree-12 base ``g(y)``."""

    return [
        (1, 2, 3, 4, 5, 6),
        (1, 2, 3, 4, 5, 7),
        (1, 2, 3, 4, 6, 7),
        (1, 2, 3, 5, 6, 7),
        (1, 2, 4, 5, 6, 8),
        (1, 3, 4, 5, 7, 8),
    ]


def negative_base_root_layouts() -> list[tuple[int, ...]]:
    """Return six-negative-root layouts encoded as positive ``b`` in ``y+b``."""

    return [
        (1, 2, 3, 4, 5, 6),
        (1, 2, 3, 4, 5, 7),
        (1, 2, 3, 4, 6, 7),
        (1, 2, 3, 5, 6, 7),
        (1, 2, 4, 5, 6, 8),
        (1, 3, 4, 5, 7, 8),
    ]


def base_polynomial_coefficients_y(
    positive_roots: Iterable[int],
    negative_roots: Iterable[int],
) -> list[int]:
    """Return ascending coefficients for ``prod(y-a) * prod(y+b)``."""

    coeffs = [1]
    for root in positive_roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    for root in negative_roots:
        coeffs = multiply_polynomials(coeffs, [int(root), 1])
    if len(coeffs) != 13 or coeffs[-1] != 1:
        raise ValueError("expected a monic degree-12 base polynomial")
    return [int(value) for value in coeffs]


def lift_base_to_degree24(base_coefficients_y: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for ``g(x^2)`` from ascending base coefficients."""

    base = [int(value) for value in base_coefficients_y]
    if len(base) != 13 or base[-1] != 1:
        raise ValueError("expected monic degree-12 base coefficients")
    coeffs = [0] * DEGREE
    for y_exponent, coefficient in enumerate(base[:-1]):
        coeffs[2 * y_exponent] = int(coefficient)
    return coeffs


def single_base_perturbations() -> list[tuple[int, int]]:
    return [(index, delta) for index in range(0, 12) for delta in (-5, -3, -2, -1, 1, 2, 3, 5)]


def structured_base_perturbation_groups() -> list[tuple[tuple[int, int], ...]]:
    return [
        ((1, 2), (5, -1)),
        ((1, -2), (5, 1)),
        ((0, 1), (6, -1)),
        ((0, -1), (6, 1)),
        ((2, 1), (7, -1)),
        ((2, -1), (7, 1)),
        ((3, 1), (8, -1)),
        ((3, -1), (8, 1)),
        ((1, 1), (4, -1), (7, 1)),
        ((2, 1), (5, -1), (8, 1)),
    ]


def trial_variants(*, rng: random.Random, max_trials: int) -> Iterable[dict[str, Any]]:
    """Yield deterministic bounded exact-composed perturbation plans."""

    positives = positive_base_root_layouts()
    negatives = negative_base_root_layouts()
    singles = single_base_perturbations()
    groups = structured_base_perturbation_groups()
    rng.shuffle(positives)
    rng.shuffle(negatives)
    rng.shuffle(singles)
    rng.shuffle(groups)

    plans: list[dict[str, Any]] = []
    for positive_roots in positives:
        for negative_roots in negatives:
            base = base_polynomial_coefficients_y(positive_roots, negative_roots)
            for index, delta in singles:
                plans.append(
                    {
                        "mode": "single_base_coefficient_perturbation",
                        "positive_base_roots": positive_roots,
                        "negative_base_roots": negative_roots,
                        "base_coefficients_y": list(base),
                        "base_perturbations": [(index, delta)],
                    }
                )
            for group in groups:
                plans.append(
                    {
                        "mode": "structured_base_coefficient_perturbation",
                        "positive_base_roots": positive_roots,
                        "negative_base_roots": negative_roots,
                        "base_coefficients_y": list(base),
                        "base_perturbations": list(group),
                    }
                )

    rng.shuffle(plans)
    for item in plans[: int(max_trials)]:
        yield item


def normalize_perturbations(raw: Any) -> list[tuple[int, int]]:
    perturbations: list[tuple[int, int]] = []
    for item in raw or []:
        if isinstance(item, dict):
            perturbations.append((int(item["y_exponent"]), int(item["delta"])))
        else:
            perturbations.append((int(item[0]), int(item[1])))
    return perturbations


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    positive_roots = tuple(int(value) for value in trial["positive_base_roots"])
    negative_roots = tuple(int(value) for value in trial["negative_base_roots"])
    base_before = [
        int(value)
        for value in trial.get("base_coefficients_y")
        or base_polynomial_coefficients_y(positive_roots, negative_roots)
    ]
    base_after = list(base_before)
    perturbations = normalize_perturbations(trial.get("base_perturbations"))
    for y_exponent, delta in perturbations:
        base_after[int(y_exponent)] += int(delta)
    coeffs = lift_base_to_degree24(base_after)
    support = sorted(index for index, value in enumerate(coeffs) if int(value) != 0)
    metadata = {
        "strategy": "r12_exact_composed_base_perturbation_probe",
        "construction_family": "degree12_base_six_positive_roots_lifted_by_x2",
        "seed_template": "g(x^2), g(y)=prod_{a in positives}(y-a)*prod_{b in negatives}(y+b)",
        "r12_structured_mode": str(trial["mode"]),
        "r12_structured_positive_base_roots": list(positive_roots),
        "r12_structured_negative_base_roots": list(negative_roots),
        "r12_structured_base_coefficients_y_before_perturbation": list(base_before),
        "r12_structured_base_coefficients_y": list(base_after),
        "r12_structured_base_degree": 12,
        "r12_structured_base_positive_real_roots": 6,
        "r12_structured_base_negative_real_roots": 6,
        "r12_structured_lift": "x_squared",
        "r12_structured_base_perturbations": [
            {"y_exponent": int(y_exponent), "delta": int(delta)} for y_exponent, delta in perturbations
        ],
        "r12_structured_perturbation_terms": len(perturbations),
        "r12_structured_support_after_lift": support,
        "r12_structured_exact_composed_support_divisor": 2,
        "composed_support": True,
        "exact_composed_support_divisor": 2,
        "target_r_heuristic": 12,
        "solvable_family_hint": "exact g(x^2) composed support with base-level coefficient perturbations",
    }
    metadata["r12_structured_family_key"] = candidate_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    positives = ",".join(str(value) for value in metadata.get("r12_structured_positive_base_roots") or [])
    negatives = ",".join(str(value) for value in metadata.get("r12_structured_negative_base_roots") or [])
    exponents = ",".join(
        str(item.get("y_exponent")) for item in metadata.get("r12_structured_base_perturbations") or []
    )
    return f"{metadata.get('r12_structured_mode')}|pos={positives}|neg={negatives}|y={exponents}"


def sort_key(record: dict[str, Any]) -> tuple[float, float, int, float, int]:
    components = record.get("score_components") or {}
    return (
        -float(record.get("coefficient_height") or 0.0),
        -float(record.get("log_abs_discriminant") or 0.0),
        int(components.get("cycle_diversity_count") or 0),
        float(record.get("score") or 0.0),
        -int(record.get("generation_metadata", {}).get("r12_structured_perturbation_terms") or 0),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key, reverse=True)
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for record in rows:
        mode = str((record.get("generation_metadata") or {}).get("r12_structured_mode") or "unknown")
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
        record["r12_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R12 Structured Candidate Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid r=12 candidates: {summary.get('valid_r12_candidates')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "| rank | hash | mode | positive y-roots | negative y-roots | base perturbations | height | log disc | score |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        perturbations = ",".join(
            f"{item.get('y_exponent')}:{item.get('delta')}"
            for item in metadata.get("r12_structured_base_perturbations") or []
        )
        positives = ",".join(str(value) for value in metadata.get("r12_structured_positive_base_roots") or [])
        negatives = ",".join(str(value) for value in metadata.get("r12_structured_negative_base_roots") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("r12_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r12_structured_mode')}`",
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
            "Caveat: these rows have local exact `r=12`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.",
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
        "".join(f"{record.get('r12_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r12 exact-composed structured queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument("--seed", type=int, default=1212)
    parser.add_argument("--max_trials", type=int, default=180)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=5_000_000)
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
        metadata["r12_structured_probe_seed"] = int(args.seed)
        metadata["r12_structured_coefficient_height"] = coefficient_height(coeffs)
        metadata["r12_structured_family_key"] = candidate_family_key({"generation_metadata": metadata})
        if coefficient_height(coeffs) > int(args.coeff_bound):
            rejected_counts["coefficient_height_exceeds_bound"] += 1
            rejected.append({"trial": trial, "rejection_reason": "coefficient_height_exceeds_bound"})
            continue
        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=12,
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        metadata["r12_structured_local_validation"] = {
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
        if analysis.real_root_count != 12:
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
            target_r=12,
            experiment_name="r12_exact_composed_base_perturbation_probe",
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
                "score1_target_caveat": "Local r12 exact-composed row; exact 24T label must come from SAIR/Magma.",
            }
        )
        candidates.append(record)
        seen_hashes.add(analysis.canonical_hash)

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    queue_status = "manual_queue_ready" if len(selected) >= min(6, int(args.limit)) else "diagnostic_too_few_valid_rows"
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r12_structured_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r12_structured_probe.py", *argv],
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
        "target_r": 12,
        "construction_family": "degree12_base_six_positive_roots_lifted_by_x2",
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "valid_r12_candidates": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_mode_counts": dict(Counter(str(row.get("generation_metadata", {}).get("r12_structured_mode")) for row in selected)),
        "valid_mode_counts": dict(Counter(str(row.get("generation_metadata", {}).get("r12_structured_mode")) for row in candidates)),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "structure_preservation": "exact g(x^2) composed support; no odd x-power perturbations",
        "recommendation": "manual_review_then_submit_small_r12_probe"
        if selected
        else "r12_structured_prototype_failed_try_chebyshev_or_return_to_r8",
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
