#!/usr/bin/env python3
"""Build a feedback-aware CPU-only r=12 exact-composed follow-up queue.

This is a second pass after the first r12 structured queue was accepted by
SAIR with labels 24T22770, 24T24970, and mostly 24T24979. The construction
keeps exact ``g(x^2)`` support and uses the accepted rows as negative feedback:
avoid known hashes, avoid exact accepted structural family keys, and prefer
base layouts/perturbations that are farther from the accepted r12 rows.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_r12_structured_probe import (
    base_polynomial_coefficients_y,
    lift_base_to_degree24,
)
from scripts.igp24_r16_diversity_probe import coefficient_line, known_hashes_from_pair_status
from scripts.igp24_shortlist import get_source_commit
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate


QUEUE_JSONL = "r12_structured_followup_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r12_structured_followup_candidate_coefficients.txt"
HASHES_TXT = "r12_structured_followup_candidate_hashes.txt"
REJECTED_JSONL = "r12_structured_followup_rejected_trials.jsonl"
SUMMARY_JSON = "r12_structured_followup_summary.json"
REPORT_MD = "r12_structured_followup_report.md"

SAFETY_NOTE = (
    "CPU-only local r12 exact-composed feedback-aware follow-up. It does not "
    "train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or "
    "submit anything."
)


@dataclass(frozen=True)
class AcceptedR12Row:
    row_number: int
    label: str
    pair_key: str
    canonical_hash: str
    exported_coefficients: tuple[int, ...]
    base_coefficients_y: tuple[int, ...]
    structural_family_key: str
    source_family_key: str


def l1_distance(left: Iterable[int], right: Iterable[int]) -> int:
    return sum(abs(int(a) - int(b)) for a, b in zip(left, right))


def normalize_perturbations(raw: Any) -> list[tuple[int, int]]:
    perturbations: list[tuple[int, int]] = []
    for item in raw or []:
        if isinstance(item, dict):
            perturbations.append((int(item["y_exponent"]), int(item["delta"])))
        else:
            perturbations.append((int(item[0]), int(item[1])))
    return perturbations


def structural_family_key(
    positive_roots: Iterable[int],
    negative_roots: Iterable[int],
    perturbations: Iterable[tuple[int, int]],
) -> str:
    positives = ",".join(str(int(value)) for value in positive_roots)
    negatives = ",".join(str(int(value)) for value in negative_roots)
    exponents = ",".join(str(int(item[0])) for item in perturbations)
    return f"pos={positives}|neg={negatives}|y={exponents}"


def load_r12_feedback(path: Path) -> list[AcceptedR12Row]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[AcceptedR12Row] = []
    for raw in payload.get("rows") or []:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("status") or "").strip().lower() != "accepted":
            continue
        if int(raw.get("r") or 0) != 12:
            continue
        label = str(raw.get("verified_group_label") or raw.get("label") or "").strip()
        exported = tuple(int(value) for value in raw.get("exported_coefficients") or [])
        base = tuple(int(value) for value in raw.get("source_base_coefficients_y") or [])
        perturbations = normalize_perturbations(raw.get("source_base_perturbations"))
        positives = tuple(int(value) for value in raw.get("source_positive_base_roots") or [])
        negatives = tuple(int(value) for value in raw.get("source_negative_base_roots") or [])
        if not label or len(exported) != DEGREE + 1 or len(base) != 13:
            raise ValueError(f"malformed accepted r12 feedback row {raw.get('row_number')}")
        rows.append(
            AcceptedR12Row(
                row_number=int(raw.get("row_number") or len(rows) + 1),
                label=label,
                pair_key=str(raw.get("pair_key") or f"{label}|r=12"),
                canonical_hash=str(raw.get("canonical_hash") or ""),
                exported_coefficients=exported,
                base_coefficients_y=base,
                structural_family_key=structural_family_key(positives, negatives, perturbations),
                source_family_key=str(raw.get("source_family_key") or ""),
            )
        )
    return rows


def accepted_hashes(rows: Iterable[AcceptedR12Row]) -> set[str]:
    return {row.canonical_hash for row in rows if row.canonical_hash}


def accepted_structural_family_keys(rows: Iterable[AcceptedR12Row]) -> set[str]:
    return {row.structural_family_key for row in rows if row.structural_family_key}


def nearest_accepted_by_base(base: list[int], accepted: list[AcceptedR12Row]) -> tuple[AcceptedR12Row | None, int | None]:
    if not accepted:
        return None, None
    best = min(accepted, key=lambda row: l1_distance(base, row.base_coefficients_y))
    return best, l1_distance(base, best.base_coefficients_y)


def nearest_accepted_by_exported(
    exported: list[int],
    accepted: list[AcceptedR12Row],
) -> tuple[AcceptedR12Row | None, int | None]:
    if not accepted:
        return None, None
    best = min(accepted, key=lambda row: l1_distance(exported, row.exported_coefficients))
    return best, l1_distance(exported, best.exported_coefficients)


def followup_positive_base_root_layouts() -> list[tuple[int, ...]]:
    """Return six-positive-root layouts not used by the first r12 queue."""

    return [
        (1, 2, 3, 4, 5, 8),
        (1, 2, 3, 4, 6, 8),
        (1, 2, 3, 5, 6, 8),
        (1, 2, 3, 5, 7, 8),
        (1, 2, 4, 5, 6, 8),
        (1, 2, 4, 5, 7, 8),
        (1, 2, 3, 4, 5, 9),
        (1, 2, 3, 4, 6, 9),
        (1, 2, 3, 5, 7, 9),
        (1, 2, 4, 5, 7, 9),
    ]


def followup_negative_base_root_layouts() -> list[tuple[int, ...]]:
    """Return six-negative-root layouts encoded as positive ``b`` in ``y+b``."""

    return [
        (1, 2, 3, 4, 5, 8),
        (1, 2, 3, 4, 6, 8),
        (1, 2, 3, 5, 6, 8),
        (1, 2, 3, 5, 7, 8),
        (1, 2, 4, 5, 6, 8),
        (1, 2, 4, 5, 7, 8),
        (1, 2, 3, 4, 5, 9),
        (1, 2, 3, 4, 6, 9),
        (1, 2, 3, 5, 7, 9),
        (1, 2, 4, 5, 7, 9),
    ]


def followup_perturbation_groups() -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    groups: list[tuple[str, tuple[tuple[int, int], ...]]] = []
    two_base = [
        ((0, 7), (5, -3)),
        ((0, -7), (5, 3)),
        ((1, 5), (6, -4)),
        ((1, -5), (6, 4)),
        ((2, 7), (7, -5)),
        ((2, -7), (7, 5)),
        ((3, 5), (8, -4)),
        ((3, -5), (8, 4)),
        ((4, 7), (9, -3)),
        ((4, -7), (9, 3)),
        ((5, 6), (10, -2)),
        ((5, -6), (10, 2)),
    ]
    three_base = [
        ((0, 5), (4, -4), (8, 3)),
        ((0, -5), (4, 4), (8, -3)),
        ((1, 4), (5, -5), (9, 3)),
        ((1, -4), (5, 5), (9, -3)),
        ((2, 5), (6, -4), (10, 2)),
        ((2, -5), (6, 4), (10, -2)),
        ((3, 4), (7, -5), (11, 1)),
        ((3, -4), (7, 5), (11, -1)),
    ]
    four_base = [
        ((0, 3), (3, -4), (6, 5), (9, -2)),
        ((0, -3), (3, 4), (6, -5), (9, 2)),
        ((1, 3), (4, -5), (7, 4), (10, -2)),
        ((1, -3), (4, 5), (7, -4), (10, 2)),
        ((2, 4), (5, -3), (8, 5), (11, -1)),
        ((2, -4), (5, 3), (8, -5), (11, 1)),
    ]
    groups.extend(("two_base_wide_perturbation", tuple(group)) for group in two_base)
    groups.extend(("three_base_balanced_perturbation", tuple(group)) for group in three_base)
    groups.extend(("four_base_balanced_perturbation", tuple(group)) for group in four_base)
    return groups


def trial_variants(*, rng: random.Random, max_trials: int) -> Iterable[dict[str, Any]]:
    positives = followup_positive_base_root_layouts()
    negatives = followup_negative_base_root_layouts()
    groups = followup_perturbation_groups()
    rng.shuffle(positives)
    rng.shuffle(negatives)
    rng.shuffle(groups)

    plans: list[dict[str, Any]] = []
    for positive_roots in positives:
        for negative_roots in negatives:
            base = base_polynomial_coefficients_y(positive_roots, negative_roots)
            for mode, group in groups:
                plans.append(
                    {
                        "mode": mode,
                        "positive_base_roots": positive_roots,
                        "negative_base_roots": negative_roots,
                        "base_coefficients_y": list(base),
                        "base_perturbations": list(group),
                    }
                )
    rng.shuffle(plans)
    for item in plans[: int(max_trials)]:
        yield item


def coefficients_from_trial(
    trial: dict[str, Any],
    *,
    accepted: list[AcceptedR12Row] | None = None,
) -> tuple[list[int], dict[str, Any]]:
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
        if not 0 <= int(y_exponent) <= 11:
            raise ValueError("follow-up perturbations may not change the leading y^12 coefficient")
        base_after[int(y_exponent)] += int(delta)
    coeffs = lift_base_to_degree24(base_after)
    exported = coeffs + [1]
    support = sorted(index for index, value in enumerate(coeffs) if int(value) != 0)
    accepted_rows = accepted or []
    nearest_base_row, nearest_base_distance = nearest_accepted_by_base(base_after, accepted_rows)
    nearest_exported_row, nearest_exported_distance = nearest_accepted_by_exported(exported, accepted_rows)
    family_key = structural_family_key(positive_roots, negative_roots, perturbations)
    metadata = {
        "strategy": "r12_exact_composed_feedback_aware_followup",
        "construction_family": "degree12_base_six_positive_roots_lifted_by_x2",
        "seed_template": "g(x^2), g(y)=prod_{a in positives}(y-a)*prod_{b in negatives}(y+b)",
        "r12_followup_mode": str(trial["mode"]),
        "r12_followup_positive_base_roots": list(positive_roots),
        "r12_followup_negative_base_roots": list(negative_roots),
        "r12_followup_base_coefficients_y_before_perturbation": list(base_before),
        "r12_followup_base_coefficients_y": list(base_after),
        "r12_followup_base_degree": 12,
        "r12_followup_base_positive_real_roots": 6,
        "r12_followup_base_negative_real_roots": 6,
        "r12_followup_lift": "x_squared",
        "r12_followup_base_perturbations": [
            {"y_exponent": int(y_exponent), "delta": int(delta)} for y_exponent, delta in perturbations
        ],
        "r12_followup_perturbation_terms": len(perturbations),
        "r12_followup_support_after_lift": support,
        "r12_followup_exact_composed_support_divisor": 2,
        "r12_followup_structural_family_key": family_key,
        "r12_followup_min_l1_to_accepted_base_y": nearest_base_distance,
        "r12_followup_nearest_accepted_base_label": nearest_base_row.label if nearest_base_row else None,
        "r12_followup_nearest_accepted_base_row": nearest_base_row.row_number if nearest_base_row else None,
        "r12_followup_min_l1_to_accepted_exported": nearest_exported_distance,
        "r12_followup_nearest_accepted_exported_label": nearest_exported_row.label if nearest_exported_row else None,
        "r12_followup_nearest_accepted_exported_row": nearest_exported_row.row_number if nearest_exported_row else None,
        "r12_followup_diversify_away_from_24T24979": (
            nearest_base_row is None or nearest_base_row.label == "24T24979"
        ),
        "composed_support": True,
        "exact_composed_support_divisor": 2,
        "target_r_heuristic": 12,
        "solvable_family_hint": "exact g(x^2) composed support with feedback-aware base-level perturbations",
    }
    return coeffs, metadata


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    return str(metadata.get("r12_followup_structural_family_key") or "")


def exact_even_support(coeffs: Iterable[int]) -> bool:
    return all(index % 2 == 0 for index, coeff in enumerate(coeffs) if int(coeff) != 0)


def sort_key(record: dict[str, Any]) -> tuple[int, int, int, float, float, int]:
    metadata = record.get("generation_metadata") or {}
    components = record.get("score_components") or {}
    nearest_label = metadata.get("r12_followup_nearest_accepted_base_label")
    away_from_24979 = 1 if nearest_label != "24T24979" else 0
    base_distance = int(metadata.get("r12_followup_min_l1_to_accepted_base_y") or 0)
    exported_distance = int(metadata.get("r12_followup_min_l1_to_accepted_exported") or 0)
    return (
        away_from_24979,
        base_distance,
        exported_distance,
        -float(record.get("coefficient_height") or 0.0),
        float(record.get("score") or 0.0),
        int(components.get("cycle_diversity_count") or 0),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key, reverse=True)
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for record in rows:
        mode = str((record.get("generation_metadata") or {}).get("r12_followup_mode") or "unknown")
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
        record["r12_followup_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R12 Structured Follow-Up Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid r=12 candidates: {summary.get('valid_r12_candidates')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Accepted feedback rows loaded: {summary.get('accepted_feedback_rows_loaded')}",
        f"- Accepted label counts: `{json.dumps(summary.get('accepted_label_counts'), sort_keys=True)}`",
        f"- Selected mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Selected nearest-label counts: `{json.dumps(summary.get('selected_nearest_base_label_counts'), sort_keys=True)}`",
        f"- Rows intentionally diversifying away from 24T24979: {summary.get('selected_diversify_away_from_24T24979_intent_count')}",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "| rank | hash | mode | positive y-roots | negative y-roots | base perturbations | nearest label | base L1 | exported L1 | height |",
        "| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        perturbations = ",".join(
            f"{item.get('y_exponent')}:{item.get('delta')}"
            for item in metadata.get("r12_followup_base_perturbations") or []
        )
        positives = ",".join(str(value) for value in metadata.get("r12_followup_positive_base_roots") or [])
        negatives = ",".join(str(value) for value in metadata.get("r12_followup_negative_base_roots") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("r12_followup_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r12_followup_mode')}`",
                    f"`{positives}`",
                    f"`{negatives}`",
                    f"`{perturbations}`",
                    f"`{metadata.get('r12_followup_nearest_accepted_base_label')}`",
                    str(metadata.get("r12_followup_min_l1_to_accepted_base_y")),
                    str(metadata.get("r12_followup_min_l1_to_accepted_exported")),
                    str(row.get("coefficient_height")),
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
        "".join(f"{record.get('r12_followup_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r12 feedback-aware exact-composed queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument(
        "--accepted_feedback_json",
        type=Path,
        default=REPO_ROOT / "data/igp24/r12_structured_probe_sair_accepted_feedback_20260706.json",
    )
    parser.add_argument("--seed", type=int, default=1213)
    parser.add_argument("--max_trials", type=int, default=240)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=20_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--min_l1_to_accepted_exported", type=int, default=4)
    parser.add_argument("--min_l1_to_accepted_base_y", type=int, default=4)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    rng = random.Random(int(args.seed))
    accepted_rows = load_r12_feedback(args.accepted_feedback_json)
    accepted_family_keys = accepted_structural_family_keys(accepted_rows)
    known_hashes = known_hashes_from_pair_status(args.pair_status_json) | accepted_hashes(accepted_rows)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    rejected_counts: Counter[str] = Counter()
    observed_root_count_counts: Counter[str] = Counter()

    for trial in trial_variants(rng=rng, max_trials=int(args.max_trials)):
        trials_attempted += 1
        coeffs, metadata = coefficients_from_trial(trial, accepted=accepted_rows)
        metadata["r12_followup_probe_seed"] = int(args.seed)
        metadata["r12_followup_coefficient_height"] = coefficient_height(coeffs)
        family_key = str(metadata["r12_followup_structural_family_key"])
        metadata["r12_followup_accepted_family_key_overlap"] = family_key in accepted_family_keys
        if family_key in accepted_family_keys:
            rejected_counts["accepted_family_key_overlap"] += 1
            rejected.append({"trial": trial, "rejection_reason": "accepted_family_key_overlap", "metadata": metadata})
            continue
        if metadata["r12_followup_min_l1_to_accepted_base_y"] is not None and int(
            metadata["r12_followup_min_l1_to_accepted_base_y"]
        ) < int(args.min_l1_to_accepted_base_y):
            rejected_counts["too_close_to_accepted_base_y"] += 1
            rejected.append({"trial": trial, "rejection_reason": "too_close_to_accepted_base_y", "metadata": metadata})
            continue
        if metadata["r12_followup_min_l1_to_accepted_exported"] is not None and int(
            metadata["r12_followup_min_l1_to_accepted_exported"]
        ) < int(args.min_l1_to_accepted_exported):
            rejected_counts["too_close_to_accepted_exported"] += 1
            rejected.append({"trial": trial, "rejection_reason": "too_close_to_accepted_exported", "metadata": metadata})
            continue
        if not exact_even_support(coeffs):
            rejected_counts["not_exact_even_support"] += 1
            rejected.append({"trial": trial, "rejection_reason": "not_exact_even_support", "metadata": metadata})
            continue
        if coefficient_height(coeffs) > int(args.coeff_bound):
            rejected_counts["coefficient_height_exceeds_bound"] += 1
            rejected.append({"trial": trial, "rejection_reason": "coefficient_height_exceeds_bound", "metadata": metadata})
            continue
        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=12,
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        metadata["r12_followup_local_validation"] = {
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
            rejected.append({"trial": trial, "rejection_reason": "known_or_duplicate_hash", "metadata": metadata})
            continue
        record = analysis_to_record(
            analysis,
            score,
            target_r=12,
            experiment_name="r12_exact_composed_feedback_aware_followup",
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
        seen_hashes.add(str(analysis.canonical_hash))

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    queue_status = "manual_queue_ready" if len(selected) >= min(6, int(args.limit)) else "diagnostic_too_few_valid_rows"
    selected_metadata = [row.get("generation_metadata") or {} for row in selected]
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r12_structured_followup.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r12_structured_followup.py", *argv],
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
        "construction_family": "degree12_base_six_positive_roots_lifted_by_x2_feedback_aware",
        "accepted_feedback_json": str(args.accepted_feedback_json),
        "accepted_feedback_rows_loaded": len(accepted_rows),
        "accepted_label_counts": dict(sorted(Counter(row.label for row in accepted_rows).items())),
        "accepted_structural_family_keys_loaded": len(accepted_family_keys),
        "known_hashes_loaded": len(known_hashes),
        "min_l1_to_accepted_exported": int(args.min_l1_to_accepted_exported),
        "min_l1_to_accepted_base_y": int(args.min_l1_to_accepted_base_y),
        "trials_attempted": trials_attempted,
        "valid_r12_candidates": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_mode_counts": dict(
            Counter(str(metadata.get("r12_followup_mode") or "unknown") for metadata in selected_metadata)
        ),
        "valid_mode_counts": dict(
            Counter(str((row.get("generation_metadata") or {}).get("r12_followup_mode") or "unknown") for row in candidates)
        ),
        "selected_nearest_base_label_counts": dict(
            Counter(str(metadata.get("r12_followup_nearest_accepted_base_label") or "none") for metadata in selected_metadata)
        ),
        "selected_diversify_away_from_24T24979_intent_count": sum(
            1 for metadata in selected_metadata if metadata.get("r12_followup_diversify_away_from_24T24979")
        ),
        "selected_nearest_non_24T24979_count": sum(
            1 for metadata in selected_metadata if metadata.get("r12_followup_nearest_accepted_base_label") != "24T24979"
        ),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "selected_family_keys": [candidate_family_key(row) for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "structure_preservation": "exact g(x^2) composed support; no odd x-power perturbations",
        "recommendation": "manual_review_then_submit_small_r12_feedback_followup"
        if selected
        else "diagnostic_only_try_new_exact_composition_family",
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
