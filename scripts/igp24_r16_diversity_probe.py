#!/usr/bin/env python3
"""Build a small CPU-only r=16 diversification queue.

The probe is deliberately local and bounded. It constructs degree-12 base
polynomials with eight positive roots, lifts them to degree 24 through
``g(x^2)``, optionally adds small perturbations, and keeps only rows whose
existing exact local checks accept them as irreducible degree-24 polynomials
with real-root count 16.
"""

from __future__ import annotations

import argparse
import csv
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

from scripts.igp24_non_generic_diagnostic import diagnose_record
from scripts.igp24_shortlist import get_source_commit
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate


QUEUE_JSONL = "r16_diversified_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r16_diversified_candidate_coefficients.txt"
HASHES_TXT = "r16_diversified_candidate_hashes.txt"
REJECTED_JSONL = "r16_diversified_rejected_trials.jsonl"
SUMMARY_JSON = "r16_diversified_summary.json"
REPORT_MD = "r16_diversified_report.md"

SAFETY_NOTE = (
    "CPU-only local r16 diversification probe. It does not train models, use a "
    "GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything."
)


def multiply_polynomials(left: Iterable[int], right: Iterable[int]) -> list[int]:
    """Multiply ascending-order integer coefficient lists."""

    a = [int(value) for value in left]
    b = [int(value) for value in right]
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


def base_polynomial_from_layout(
    positive_roots: Iterable[int],
    quadratics: Iterable[tuple[int, int]],
) -> list[int]:
    """Return monic base ``g(y)`` coefficients in ascending order."""

    coeffs = [1]
    for root in positive_roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    for linear, constant in quadratics:
        coeffs = multiply_polynomials(coeffs, [int(constant), int(linear), 1])
    if len(coeffs) != 13 or coeffs[-1] != 1:
        raise ValueError("base layout did not produce a monic degree-12 polynomial")
    return coeffs


def lift_base_to_degree24(base_coefficients: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for ``g(x^2)`` from ascending base coefficients."""

    base = [int(value) for value in base_coefficients]
    if len(base) != 13 or base[-1] != 1:
        raise ValueError("expected monic degree-12 base coefficients")
    coeffs = [0] * DEGREE
    for y_exponent, coefficient in enumerate(base[:-1]):
        coeffs[2 * y_exponent] = int(coefficient)
    return coeffs


def coefficient_line(exported_coefficients: Iterable[int]) -> str:
    return ",".join(str(int(value)) for value in exported_coefficients)


def parse_polynomial_csv_row(value: str) -> list[int]:
    values = [int(item.strip()) for item in str(value).split(",") if item.strip()]
    if len(values) != DEGREE + 1:
        raise ValueError("expected 25 coefficients in SAIR polynomial field")
    return values


def accepted_full_vectors_from_csv(path: Path | None) -> list[list[int]]:
    if path is None or not path.exists():
        return []
    vectors: list[list[int]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            status = str(row.get("status") or "").strip().lower()
            if status and status != "accepted":
                continue
            r_value = str(row.get("r") or "").strip()
            if r_value and r_value != "16":
                continue
            vectors.append(parse_polynomial_csv_row(str(row.get("polynomial") or "")))
    return vectors


def accepted_even_vectors_from_csv(path: Path | None) -> list[list[int]]:
    return accepted_even_vectors_from_full(accepted_full_vectors_from_csv(path))


def accepted_hashes_from_feedback(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    hashes: set[str] = set()
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("status") or "").strip().lower() != "accepted":
            continue
        if int(row.get("r") or 0) != 16:
            continue
        value = row.get("canonical_hash") or row.get("candidate_hash")
        if isinstance(value, str) and value:
            hashes.add(value)
    return hashes


def accepted_full_vectors_from_queue(path: Path | None, accepted_hashes: set[str] | None = None) -> list[list[int]]:
    if path is None or not path.exists():
        return []
    vectors: list[list[int]] = []
    accepted = accepted_hashes or set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            hash_value = str(row.get("canonical_hash") or "")
            if accepted and hash_value not in accepted:
                continue
            exported = row.get("exported_coefficients")
            if not isinstance(exported, list) or len(exported) != DEGREE + 1:
                continue
            vectors.append([int(value) for value in exported])
    return vectors


def accepted_even_vectors_from_full(vectors: list[list[int]]) -> list[list[int]]:
    return [[int(poly[index]) for index in range(0, DEGREE + 1, 2)] for poly in vectors]


def known_hashes_from_pair_status(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    hashes: set[str] = set()
    for pair in payload.get("pairs") or []:
        if not isinstance(pair, dict):
            continue
        for field in ("canonical_hash", "candidate_hash"):
            value = pair.get(field)
            if isinstance(value, str) and value:
                hashes.add(value)
        for alternate in pair.get("accepted_alternates") or []:
            if isinstance(alternate, dict):
                value = alternate.get("canonical_hash") or alternate.get("candidate_hash")
                if isinstance(value, str) and value:
                    hashes.add(value)
    return hashes


def l1_distance(left: Iterable[int], right: Iterable[int]) -> int:
    return sum(abs(int(a) - int(b)) for a, b in zip(left, right))


def min_accepted_even_l1(base: list[int], accepted_even_vectors: list[list[int]]) -> int | None:
    if not accepted_even_vectors:
        return None
    return min(l1_distance(base, accepted) for accepted in accepted_even_vectors)


def min_accepted_full_l1(exported_coefficients: list[int], accepted_full_vectors: list[list[int]]) -> int | None:
    if not accepted_full_vectors:
        return None
    return min(l1_distance(exported_coefficients, accepted) for accepted in accepted_full_vectors)


def off_block_exponents(exported_coefficients: list[int], divisor: int = 2) -> list[int]:
    return [
        index
        for index, coefficient in enumerate(exported_coefficients)
        if int(coefficient) != 0 and index % int(divisor) != 0
    ]


def root_layouts() -> list[tuple[int, ...]]:
    return [
        (1, 2, 3, 4, 5, 6, 7, 8),
        (1, 2, 3, 4, 5, 6, 8, 9),
        (1, 2, 3, 4, 5, 7, 8, 10),
        (1, 2, 3, 4, 6, 7, 9, 11),
        (1, 2, 3, 4, 6, 8, 10, 12),
        (1, 2, 3, 5, 7, 9, 11, 13),
        (1, 2, 4, 5, 8, 10, 13, 16),
        (1, 3, 4, 6, 7, 10, 12, 15),
        (2, 3, 5, 6, 8, 11, 14, 17),
        (1, 3, 5, 7, 8, 11, 13, 16),
        (2, 4, 5, 7, 9, 12, 15, 18),
        (1, 2, 5, 6, 9, 12, 14, 18),
    ]


def quadratic_layouts() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    # y^2 + linear*y + constant; positive linear/constant gives no positive roots.
    return [
        ((1, 1), (1, 2)),
        ((1, 2), (2, 2)),
        ((2, 2), (2, 3)),
        ((2, 3), (3, 3)),
        ((1, 1), (3, 4)),
        ((2, 5), (4, 5)),
    ]


def trial_variants(
    *,
    rng: random.Random,
    max_trials: int,
    include_exact: bool,
    include_odd: bool,
    include_two_odd: bool = False,
    include_three_odd: bool = False,
    include_four_odd: bool = False,
    include_mixed_even_odd: bool = False,
    perturbations_per_family_mode: int = 6,
) -> Iterable[dict[str, Any]]:
    """Yield bounded candidate construction plans."""

    layouts = root_layouts()
    quadratics = quadratic_layouts()
    rng.shuffle(layouts)
    rng.shuffle(quadratics)
    y_perturbations = [(index, delta) for index in range(1, 12) for delta in (-5, -3, -2, -1, 1, 2, 3, 5)]
    odd_perturbations = [(index, delta) for index in range(1, DEGREE, 2) for delta in (-2, -1, 1, 2)]
    rng.shuffle(y_perturbations)
    rng.shuffle(odd_perturbations)
    modes: list[str] = []
    if include_exact:
        modes.append("exact_composed_new_base")
    if include_odd:
        modes.append("odd_perturbed_near_composed")
    if include_two_odd:
        modes.append("two_odd_perturbed_near_composed")
    if include_three_odd:
        modes.append("three_odd_perturbed_near_composed")
    if include_four_odd:
        modes.append("four_odd_perturbed_near_composed")
    if include_mixed_even_odd:
        modes.append("mixed_even_odd_perturbed")
    if not modes:
        raise ValueError("at least one variant mode must be enabled")

    plans: list[dict[str, Any]] = []
    per_mode = max(1, int(perturbations_per_family_mode))
    for roots in layouts:
        for quads in quadratics:
            base = base_polynomial_from_layout(roots, quads)
            for mode in modes:
                if mode == "exact_composed_new_base":
                    for index, delta in y_perturbations[:per_mode]:
                        plans.append(
                            {
                                "mode": mode,
                                "positive_roots": roots,
                                "quadratics": quads,
                                "base_coefficients": list(base),
                                "y_perturbations": [(index, delta)],
                                "perturb_index": index,
                                "perturb_delta": delta,
                            }
                        )
                    continue
                if mode == "odd_perturbed_near_composed":
                    for index, delta in odd_perturbations[:per_mode]:
                        plans.append(
                            {
                                "mode": mode,
                                "positive_roots": roots,
                                "quadratics": quads,
                                "base_coefficients": list(base),
                                "odd_perturbations": [(index, delta)],
                                "perturb_index": index,
                                "perturb_delta": delta,
                            }
                        )
                    continue
                odd_width = {
                    "two_odd_perturbed_near_composed": 2,
                    "three_odd_perturbed_near_composed": 3,
                    "four_odd_perturbed_near_composed": 4,
                    "mixed_even_odd_perturbed": 2,
                }[mode]
                odd_groups = distinct_odd_perturbation_groups(
                    odd_perturbations, width=odd_width, limit=per_mode
                )
                if mode == "mixed_even_odd_perturbed":
                    for y_item, odd_group in zip(y_perturbations[:per_mode], odd_groups):
                        plans.append(
                            {
                                "mode": mode,
                                "positive_roots": roots,
                                "quadratics": quads,
                                "base_coefficients": list(base),
                                "y_perturbations": [y_item],
                                "odd_perturbations": list(odd_group),
                            }
                        )
                    continue
                for odd_group in odd_groups:
                    plans.append(
                        {
                            "mode": mode,
                            "positive_roots": roots,
                            "quadratics": quads,
                            "base_coefficients": list(base),
                            "odd_perturbations": list(odd_group),
                        }
                    )
    rng.shuffle(plans)
    for item in plans[:max_trials]:
        yield item


def distinct_odd_perturbation_groups(
    odd_perturbations: list[tuple[int, int]],
    *,
    width: int,
    limit: int,
) -> list[tuple[tuple[int, int], ...]]:
    groups: list[tuple[tuple[int, int], ...]] = []
    seen_keys: set[tuple[int, ...]] = set()
    for start, first in enumerate(odd_perturbations):
        used_exponents = {int(first[0])}
        group = [first]
        for item in odd_perturbations[start + 1 :]:
            exponent = int(item[0])
            if exponent in used_exponents:
                continue
            group.append(item)
            used_exponents.add(exponent)
            if len(group) == int(width):
                break
        if len(group) != int(width):
            continue
        key = tuple(sorted(int(item[0]) for item in group))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        groups.append(tuple(group))
        if len(groups) >= int(limit):
            break
    return groups


def normalize_perturbations(raw: Any, *, exponent_key: str) -> list[tuple[int, int]]:
    perturbations: list[tuple[int, int]] = []
    for item in raw or []:
        if isinstance(item, dict):
            perturbations.append((int(item[exponent_key]), int(item["delta"])))
        else:
            perturbations.append((int(item[0]), int(item[1])))
    return perturbations


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    base = list(trial["base_coefficients"])
    mode = str(trial["mode"])
    y_perturbations = normalize_perturbations(trial.get("y_perturbations"), exponent_key="index")
    odd_perturbations = normalize_perturbations(trial.get("odd_perturbations"), exponent_key="x_exponent")
    if not y_perturbations and not odd_perturbations and "perturb_index" in trial:
        fallback = (int(trial["perturb_index"]), int(trial["perturb_delta"]))
        if mode == "exact_composed_new_base":
            y_perturbations = [fallback]
        else:
            odd_perturbations = [fallback]
    metadata = {
        "strategy": "r16_diversified_root_layout_probe",
        "seed_template": "diversified_degree12_base_with_eight_positive_roots",
        "r16_diversity_mode": mode,
        "r16_diversity_positive_roots": list(trial["positive_roots"]),
        "r16_diversity_quadratics_y": [list(pair) for pair in trial["quadratics"]],
        "r16_diversity_base_coefficients_y_before_perturbation": list(base),
        "r16_diversity_base_degree": 12,
        "r16_diversity_positive_base_roots": 8,
        "r16_diversity_y_perturbations": [
            {"index": int(index), "delta": int(delta)} for index, delta in y_perturbations
        ],
        "r16_diversity_odd_perturbations": [
            {"x_exponent": int(index), "delta": int(delta)} for index, delta in odd_perturbations
        ],
        "r16_diversity_off_block_perturbation_exponents": sorted(
            {int(index) for index, delta in odd_perturbations if int(delta) != 0}
        ),
        "r16_diversity_off_block_perturbation_terms": len(
            {int(index) for index, delta in odd_perturbations if int(delta) != 0}
        ),
        "target_r_heuristic": 16,
    }
    known_modes = {
        "exact_composed_new_base",
        "odd_perturbed_near_composed",
        "two_odd_perturbed_near_composed",
        "three_odd_perturbed_near_composed",
        "four_odd_perturbed_near_composed",
        "mixed_even_odd_perturbed",
    }
    if mode not in known_modes:
        raise ValueError(f"unknown mode: {mode}")
    for index, delta in y_perturbations:
        base[int(index)] += int(delta)
    coeffs = lift_base_to_degree24(base)
    for index, delta in odd_perturbations:
        coeffs[int(index)] += int(delta)
    metadata["r16_diversity_base_coefficients_y"] = list(base)
    if len(y_perturbations) == 1:
        metadata["r16_diversity_y_perturbation"] = {
            "index": int(y_perturbations[0][0]),
            "delta": int(y_perturbations[0][1]),
        }
    if len(odd_perturbations) == 1:
        metadata["r16_diversity_odd_perturbation"] = {
            "x_exponent": int(odd_perturbations[0][0]),
            "delta": int(odd_perturbations[0][1]),
        }
    metadata["composed_support_divisor"] = 2
    metadata["composed_support"] = not odd_perturbations
    if odd_perturbations:
        metadata["near_composed_support_divisor"] = 2
    else:
        metadata["exact_composed_support_divisor"] = 2
    return coeffs, metadata


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    roots = ",".join(str(value) for value in metadata.get("r16_diversity_positive_roots") or [])
    quads = ",".join("-".join(str(item) for item in pair) for pair in metadata.get("r16_diversity_quadratics_y") or [])
    odd_exponents = ",".join(str(value) for value in metadata.get("r16_diversity_off_block_perturbation_exponents") or [])
    y_indices = ",".join(str(item.get("index")) for item in metadata.get("r16_diversity_y_perturbations") or [])
    return f"{metadata.get('r16_diversity_mode')}|roots={roots}|quads={quads}|odd={odd_exponents}|y={y_indices}"


def sort_key(record: dict[str, Any]) -> tuple[float, float, float, int, int]:
    return (
        float(record.get("non_generic_score") or 0.0),
        -float(record.get("coefficient_height") or 0.0),
        float(record.get("score") or 0.0),
        int(record.get("generation_metadata", {}).get("r16_diversity_min_l1_to_accepted_full_coefficients") or 0),
        int(record.get("generation_metadata", {}).get("r16_diversity_min_l1_to_accepted_even_coefficients") or 0),
    )


def _sorted_by_quality(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=sort_key, reverse=True)


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        mode = str((record.get("generation_metadata") or {}).get("r16_diversity_mode") or "unknown")
        by_mode.setdefault(mode, []).append(record)
    for mode, rows in list(by_mode.items()):
        by_mode[mode] = _sorted_by_quality(rows)

    mode_order = sorted(
        by_mode,
        key=lambda mode: sort_key(by_mode[mode][0]) if by_mode[mode] else (0.0, 0.0, 0.0, 0, 0),
        reverse=True,
    )
    progressed = True
    while len(selected) < limit and progressed:
        progressed = False
        for mode in mode_order:
            rows = by_mode.get(mode) or []
            while rows:
                record = rows.pop(0)
                family = candidate_family_key(record)
                hash_value = str(record.get("canonical_hash") or "")
                if family_counts[family] >= per_family_cap or hash_value in selected_hashes:
                    continue
                selected.append(record)
                selected_hashes.add(hash_value)
                family_counts[family] += 1
                progressed = True
                break
            if len(selected) >= limit:
                break

    if len(selected) < limit:
        for record in _sorted_by_quality(records):
            family = candidate_family_key(record)
            hash_value = str(record.get("canonical_hash") or "")
            if family_counts[family] >= per_family_cap or hash_value in selected_hashes:
                continue
            selected.append(record)
            selected_hashes.add(hash_value)
            family_counts[family] += 1
            if len(selected) >= limit:
                break
    for rank, record in enumerate(selected, start=1):
        record["diversity_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R16 Diversified Candidate Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid r=16 candidates: {summary.get('valid_r16_candidates')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "| rank | hash | mode | off-block | height | score | non-generic | flags | min full L1 |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        flags = ",".join(row.get("non_generic_flags") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("diversity_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r16_diversity_mode')}`",
                    str(metadata.get("r16_diversity_divisor2_off_block_terms")),
                    str(row.get("coefficient_height")),
                    f"{float(row.get('score') or 0.0):.3f}",
                    f"{float(row.get('non_generic_score') or 0.0):.3f}",
                    flags,
                    str(metadata.get("r16_diversity_min_l1_to_accepted_full_coefficients")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
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
        "".join(f"{record.get('diversity_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r16 diversification queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument(
        "--accepted_status_csv",
        type=Path,
        default=REPO_ROOT / "data/igp24/r16_quadratic_lift_sair_status_export_20260706.csv",
    )
    parser.add_argument(
        "--accepted_feedback_json",
        type=Path,
        default=REPO_ROOT / "data/igp24/r16_diversity_probe_sair_accepted_feedback_20260706.json",
    )
    parser.add_argument(
        "--accepted_feedback_queue_jsonl",
        type=Path,
        default=REPO_ROOT / "data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_queue.jsonl",
    )
    parser.add_argument("--seed", type=int, default=1616)
    parser.add_argument("--max_trials", type=int, default=240)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=20_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=4.0)
    parser.add_argument("--min_l1_to_accepted_even", type=int, default=5000)
    parser.add_argument("--min_l1_to_accepted_full", type=int, default=5000)
    parser.add_argument("--min_off_block_terms", type=int, default=0)
    parser.add_argument("--max_off_block_terms", type=int, default=DEGREE)
    parser.add_argument("--perturbations_per_family_mode", type=int, default=6)
    parser.add_argument("--include_exact", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include_odd", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include_two_odd", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--include_three_odd", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--include_four_odd", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--include_mixed_even_odd", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    rng = random.Random(int(args.seed))
    accepted_feedback_hashes = accepted_hashes_from_feedback(args.accepted_feedback_json)
    known_hashes = known_hashes_from_pair_status(args.pair_status_json) | accepted_feedback_hashes
    accepted_full = accepted_full_vectors_from_csv(args.accepted_status_csv)
    accepted_full.extend(
        accepted_full_vectors_from_queue(args.accepted_feedback_queue_jsonl, accepted_feedback_hashes)
    )
    accepted_even = accepted_even_vectors_from_full(accepted_full)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    rejected_counts: Counter[str] = Counter()

    for trial in trial_variants(
        rng=rng,
        max_trials=int(args.max_trials),
        include_exact=bool(args.include_exact),
        include_odd=bool(args.include_odd),
        include_two_odd=bool(args.include_two_odd),
        include_three_odd=bool(args.include_three_odd),
        include_four_odd=bool(args.include_four_odd),
        include_mixed_even_odd=bool(args.include_mixed_even_odd),
        perturbations_per_family_mode=int(args.perturbations_per_family_mode),
    ):
        trials_attempted += 1
        coeffs, metadata = coefficients_from_trial(trial)
        exported_coeffs = [*coeffs, 1]
        base_l1 = min_accepted_even_l1(metadata["r16_diversity_base_coefficients_y"], accepted_even)
        full_l1 = min_accepted_full_l1(exported_coeffs, accepted_full)
        divisor2_off_exponents = off_block_exponents(exported_coeffs, divisor=2)
        metadata["r16_diversity_min_l1_to_accepted_even_coefficients"] = base_l1
        metadata["r16_diversity_min_l1_to_accepted_full_coefficients"] = full_l1
        metadata["r16_diversity_divisor2_off_block_exponents"] = divisor2_off_exponents
        metadata["r16_diversity_divisor2_off_block_terms"] = len(divisor2_off_exponents)
        metadata["r16_diversity_probe_seed"] = int(args.seed)
        metadata["r16_diversity_family_key"] = candidate_family_key({"generation_metadata": metadata})
        if base_l1 is not None and base_l1 < int(args.min_l1_to_accepted_even):
            rejected_counts["too_close_to_accepted_even_coefficients"] += 1
            continue
        if full_l1 is not None and full_l1 < int(args.min_l1_to_accepted_full):
            rejected_counts["too_close_to_accepted_full_coefficients"] += 1
            continue
        if len(divisor2_off_exponents) < int(args.min_off_block_terms):
            rejected_counts["too_few_divisor2_off_block_terms"] += 1
            continue
        if len(divisor2_off_exponents) > int(args.max_off_block_terms):
            rejected_counts["too_many_divisor2_off_block_terms"] += 1
            continue
        if coefficient_height(coeffs) > int(args.coeff_bound):
            rejected_counts["coefficient_height_exceeds_bound"] += 1
            continue
        score, analysis = score_candidate(
            coeffs,
            coeff_bound=int(args.coeff_bound),
            target_r=16,
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            seen_hashes=known_hashes | seen_hashes,
        )
        if not analysis.valid:
            rejected_counts[str(analysis.rejection_reason or "invalid")] += 1
            rejected.append({"trial": trial, "rejection_reason": analysis.rejection_reason})
            continue
        if analysis.real_root_count != 16:
            rejected_counts["real_root_count_mismatch"] += 1
            rejected.append({"trial": trial, "real_root_count": analysis.real_root_count})
            continue
        if analysis.canonical_hash in known_hashes or analysis.canonical_hash in seen_hashes:
            rejected_counts["known_or_duplicate_hash"] += 1
            continue
        record = analysis_to_record(
            analysis,
            score,
            target_r=16,
            experiment_name="r16_diversified_root_layout_probe",
            verification_status="proxy_scored",
            generation_metadata=metadata,
            local_search_metadata={"attempted": 0, "accepted": 0, "enabled": False},
        )
        diagnostic = diagnose_record(record)
        record.update(
            {
                "source_strategy": metadata["strategy"],
                "non_generic_score": diagnostic["non_generic_score"],
                "non_generic_flags": diagnostic["non_generic_flags"],
                "non_generic_evidence": diagnostic["non_generic_evidence"],
                "proxy_only_caveat": SAFETY_NOTE,
                "exact_label_claimed_by_helper": False,
                "score1_target_caveat": "Proxy-only r16 diversification row; exact 24T label must come from SAIR/Magma.",
            }
        )
        candidates.append(record)
        seen_hashes.add(analysis.canonical_hash)

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r16_diversity_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r16_diversity_probe.py", *argv],
        "safety": {
            "local_file_only": True,
            "cpu_only": True,
            "gpu_training": False,
            "gpu_sampling": False,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "magma_executed": False,
            "pari_executed": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
        "inputs": {
            "pair_status_json": str(args.pair_status_json),
            "accepted_status_csv": str(args.accepted_status_csv),
            "accepted_feedback_json": str(args.accepted_feedback_json),
            "accepted_feedback_queue_jsonl": str(args.accepted_feedback_queue_jsonl),
            "known_hashes": len(known_hashes),
            "accepted_even_vectors": len(accepted_even),
            "accepted_full_vectors": len(accepted_full),
        },
        "parameters": {
            "seed": int(args.seed),
            "max_trials": int(args.max_trials),
            "limit": int(args.limit),
            "per_family_cap": int(args.per_family_cap),
            "coeff_bound": int(args.coeff_bound),
            "prime_limit": int(args.prime_limit),
            "exact_score_timeout": float(args.exact_score_timeout),
            "min_l1_to_accepted_even": int(args.min_l1_to_accepted_even),
            "min_l1_to_accepted_full": int(args.min_l1_to_accepted_full),
            "min_off_block_terms": int(args.min_off_block_terms),
            "max_off_block_terms": int(args.max_off_block_terms),
            "perturbations_per_family_mode": int(args.perturbations_per_family_mode),
            "include_exact": bool(args.include_exact),
            "include_odd": bool(args.include_odd),
            "include_two_odd": bool(args.include_two_odd),
            "include_three_odd": bool(args.include_three_odd),
            "include_four_odd": bool(args.include_four_odd),
            "include_mixed_even_odd": bool(args.include_mixed_even_odd),
        },
        "trials_attempted": trials_attempted,
        "valid_r16_candidates": len(candidates),
        "selected_rows": len(selected),
        "selected_mode_counts": dict(
            sorted(Counter((row.get("generation_metadata") or {}).get("r16_diversity_mode") for row in selected).items())
        ),
        "selected_family_keys": [candidate_family_key(row) for row in selected],
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "rejected_counts": dict(sorted(rejected_counts.items())),
        "queue_status": "produced" if len(selected) >= 6 else "too_few_valid_rows",
        "recommendation": (
            "Manual-submit this diversified r16 queue before widening the probe."
            if len(selected) >= 6
            else "Do not submit yet; widen root layouts or coefficient bounds first."
        ),
        "output_files": {
            "queue_jsonl": str(args.output_dir / QUEUE_JSONL),
            "coefficients_txt": str(args.output_dir / COEFFICIENTS_TXT),
            "hashes_txt": str(args.output_dir / HASHES_TXT),
            "rejected_jsonl": str(args.output_dir / REJECTED_JSONL),
            "summary_json": str(args.output_dir / SUMMARY_JSON),
            "report_md": str(args.output_dir / REPORT_MD),
        },
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    print(f"trials_attempted\t{summary['trials_attempted']}")
    print(f"valid_r16_candidates\t{summary['valid_r16_candidates']}")
    print(f"selected_rows\t{summary['selected_rows']}")
    print(f"selected_mode_counts\t{json.dumps(summary['selected_mode_counts'], sort_keys=True)}")
    print(f"rejected_counts\t{json.dumps(summary['rejected_counts'], sort_keys=True)}")
    print(f"queue_status\t{summary['queue_status']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
