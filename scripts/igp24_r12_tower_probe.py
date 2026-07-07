#!/usr/bin/env python3
"""Build a CPU-only r=12 exact-composed tower probe queue.

The r12 ``g(x^2)`` lane has now produced accepted non-generic rows twice, but
the feedback-aware widening repeated already-known pair keys. This helper
switches to a true degree-pattern ``6 x 4`` composition:

    f(x) = h(q(x)), where q(x) = x^4 - s*x^2 and deg(h)=6.

The seed outer polynomial has three roots in the four-real-preimage band of
``q`` and three roots below the minimum of ``q``. Small outer-coefficient
perturbations make the composed polynomial irreducible in local checks while
preserving the exact tower structure.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_r16_diversity_probe import coefficient_line, known_hashes_from_pair_status, multiply_polynomials
from scripts.igp24_shortlist import get_source_commit
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, score_candidate


QUEUE_JSONL = "r12_tower_candidate_queue.jsonl"
COEFFICIENTS_TXT = "r12_tower_candidate_coefficients.txt"
HASHES_TXT = "r12_tower_candidate_hashes.txt"
REJECTED_JSONL = "r12_tower_rejected_trials.jsonl"
SUMMARY_JSON = "r12_tower_summary.json"
REPORT_MD = "r12_tower_report.md"

SAFETY_NOTE = (
    "CPU-only local r12 degree-6-by-degree-4 exact-composed tower probe. It "
    "does not train models, use a GPU sampler, call SAIR/Magma/PARI/network "
    "APIs, or submit anything."
)


@dataclass(frozen=True)
class AcceptedFollowupRow:
    row_number: int
    label: str
    pair_key: str
    canonical_hash: str
    source_mode: str
    source_family_key: str


def load_r12_followup_feedback(path: Path) -> list[AcceptedFollowupRow]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[AcceptedFollowupRow] = []
    for raw in payload.get("rows") or []:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("status") or "").strip().lower() != "accepted":
            continue
        if int(raw.get("r") or 0) != 12:
            continue
        label = str(raw.get("verified_group_label") or raw.get("label") or "").strip()
        if not label:
            raise ValueError(f"malformed accepted r12 follow-up row {raw.get('row_number')}")
        rows.append(
            AcceptedFollowupRow(
                row_number=int(raw.get("row_number") or len(rows) + 1),
                label=label,
                pair_key=str(raw.get("pair_key") or f"{label}|r=12"),
                canonical_hash=str(raw.get("canonical_hash") or ""),
                source_mode=str(raw.get("source_mode") or ""),
                source_family_key=str(raw.get("source_family_key") or ""),
            )
        )
    return rows


def accepted_hashes(rows: Iterable[AcceptedFollowupRow]) -> set[str]:
    return {row.canonical_hash for row in rows if row.canonical_hash}


def inner_quartic_coefficients(s: int) -> list[int]:
    """Return ascending coefficients for ``q(x)=x^4-s*x^2``."""

    return [0, 0, -int(s), 0, 1]


def outer_from_roots(roots: Iterable[int]) -> list[int]:
    """Return ascending coefficients for ``prod(y-r)``."""

    coeffs = [1]
    for root in roots:
        coeffs = multiply_polynomials(coeffs, [-int(root), 1])
    if len(coeffs) != 7 or coeffs[-1] != 1:
        raise ValueError("expected a monic degree-6 outer polynomial")
    return [int(value) for value in coeffs]


def compose_outer_inner(outer_coefficients: Iterable[int], inner_coefficients: Iterable[int]) -> list[int]:
    """Return [a0, ..., a23] for ``h(q(x))``."""

    outer = [int(value) for value in outer_coefficients]
    inner = [int(value) for value in inner_coefficients]
    if len(outer) != 7 or outer[-1] != 1:
        raise ValueError("expected a monic degree-6 outer polynomial")
    if len(inner) != 5 or inner[-1] != 1:
        raise ValueError("expected a monic degree-4 inner polynomial")
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


def outer_root_layouts(s: int) -> list[dict[str, Any]]:
    """Return seed outer roots for target r=12 under ``q=x^4-s*x^2``."""

    # q has minimum -s^2/4. Integer levels in (-s^2/4, 0) have four real
    # preimages; integer levels below the minimum have no real preimages.
    min_floor = (int(s) * int(s)) // 4
    inside_pool = list(range(1, max(4, min(min_floor, 8))))
    no_real_pool = list(range(min_floor + 1, min_floor + 7))
    layouts: list[dict[str, Any]] = []
    for inside in list(combinations(inside_pool, 3))[:10]:
        for no_real in list(combinations(no_real_pool, 3))[:4]:
            layouts.append(
                {
                    "outer_roots": tuple([-value for value in inside] + [-value for value in no_real]),
                    "four_real_preimage_levels": tuple(-value for value in inside),
                    "no_real_preimage_levels": tuple(-value for value in no_real),
                }
            )
    return layouts


def outer_perturbation_groups() -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    groups: list[tuple[str, tuple[tuple[int, int], ...]]] = []
    constant = [((0, delta),) for delta in (-3, -2, -1, 1, 2, 3, 5, -5)]
    two = [
        ((0, 1), (2, -1)),
        ((0, -1), (2, 1)),
        ((1, 1), (3, -1)),
        ((1, -1), (3, 1)),
        ((0, 2), (4, -1)),
        ((0, -2), (4, 1)),
        ((2, 2), (5, -1)),
        ((2, -2), (5, 1)),
    ]
    three = [
        ((0, 1), (2, -2), (4, 1)),
        ((0, -1), (2, 2), (4, -1)),
        ((1, 2), (3, -1), (5, 1)),
        ((1, -2), (3, 1), (5, -1)),
        ((0, 3), (1, -2), (5, 1)),
        ((0, -3), (1, 2), (5, -1)),
    ]
    groups.extend(("outer_constant_shift", tuple(group)) for group in constant)
    groups.extend(("outer_two_coefficient_shift", tuple(group)) for group in two)
    groups.extend(("outer_three_coefficient_shift", tuple(group)) for group in three)
    return groups


def trial_variants(*, rng: random.Random, max_trials: int) -> Iterable[dict[str, Any]]:
    """Yield deterministic bounded degree-6-by-degree-4 tower plans."""

    plans: list[dict[str, Any]] = []
    groups = outer_perturbation_groups()
    inner_parameters = [4, 5, 6, 7, 8]
    rng.shuffle(inner_parameters)
    rng.shuffle(groups)
    for s in inner_parameters:
        inner = inner_quartic_coefficients(s)
        layouts = outer_root_layouts(s)
        rng.shuffle(layouts)
        for layout in layouts:
            roots = tuple(int(value) for value in layout["outer_roots"])
            outer = outer_from_roots(roots)
            for mode, group in groups:
                plans.append(
                    {
                        "mode": mode,
                        "inner_parameter_s": int(s),
                        "inner_coefficients": list(inner),
                        "outer_roots": roots,
                        "four_real_preimage_levels": list(layout["four_real_preimage_levels"]),
                        "no_real_preimage_levels": list(layout["no_real_preimage_levels"]),
                        "outer_coefficients_before_perturbation": list(outer),
                        "outer_perturbations": list(group),
                    }
                )
    rng.shuffle(plans)
    for item in plans[: int(max_trials)]:
        yield item


def normalize_perturbations(raw: Any) -> list[tuple[int, int]]:
    perturbations: list[tuple[int, int]] = []
    for item in raw or []:
        if isinstance(item, dict):
            perturbations.append((int(item["outer_y_exponent"]), int(item["delta"])))
        else:
            perturbations.append((int(item[0]), int(item[1])))
    return perturbations


def coefficients_from_trial(trial: dict[str, Any]) -> tuple[list[int], dict[str, Any]]:
    inner = [int(value) for value in trial.get("inner_coefficients") or inner_quartic_coefficients(trial["inner_parameter_s"])]
    outer_before = [
        int(value)
        for value in trial.get("outer_coefficients_before_perturbation")
        or outer_from_roots(trial["outer_roots"])
    ]
    outer_after = list(outer_before)
    perturbations = normalize_perturbations(trial.get("outer_perturbations"))
    for exponent, delta in perturbations:
        if not 0 <= int(exponent) <= 5:
            raise ValueError("tower perturbations may not change the leading outer y^6 coefficient")
        outer_after[int(exponent)] += int(delta)
    coeffs = compose_outer_inner(outer_after, inner)
    support = sorted(index for index, value in enumerate(coeffs) if int(value) != 0)
    metadata = {
        "strategy": "r12_degree6_by_degree4_tower_probe",
        "construction_family": "outer_degree6_composed_with_even_quartic_double_well",
        "decomposition_type": "exact_composition",
        "decomposition_degree_pattern": "6x4",
        "tower_expression": "h(q(x)), q(x)=x^4-s*x^2",
        "r12_tower_mode": str(trial["mode"]),
        "r12_tower_inner_parameter_s": int(trial["inner_parameter_s"]),
        "r12_tower_inner_polynomial_coefficients": list(inner),
        "r12_tower_inner_polynomial": f"x^4 - {int(trial['inner_parameter_s'])}*x^2",
        "r12_tower_outer_roots_before_perturbation": [int(value) for value in trial["outer_roots"]],
        "r12_tower_outer_four_real_preimage_levels": [
            int(value) for value in trial.get("four_real_preimage_levels") or []
        ],
        "r12_tower_outer_no_real_preimage_levels": [
            int(value) for value in trial.get("no_real_preimage_levels") or []
        ],
        "r12_tower_outer_coefficients_before_perturbation": list(outer_before),
        "r12_tower_outer_coefficients": list(outer_after),
        "r12_tower_outer_perturbations": [
            {"outer_y_exponent": int(exponent), "delta": int(delta)} for exponent, delta in perturbations
        ],
        "r12_tower_perturbation_terms": len(perturbations),
        "r12_tower_support_after_composition": support,
        "r12_tower_exact_composition": True,
        "r12_tower_even_inner": True,
        "r12_tower_expected_real_root_count": 12,
        "target_r_heuristic": 12,
        "composed_support": True,
        "exact_composed_support_divisor": 2,
        "structural_difference_from_previous_r12_lane": (
            "uses a degree-6 outer polynomial composed with a quartic double-well inner polynomial; "
            "not a direct degree-12 root-product base merely lifted as g(x^2)"
        ),
        "solvable_family_hint": "exact h(q(x)) tower with controlled real-preimage levels",
    }
    metadata["r12_tower_family_key"] = candidate_family_key({"generation_metadata": metadata})
    return coeffs, metadata


def candidate_family_key(record: dict[str, Any]) -> str:
    metadata = record.get("generation_metadata") or {}
    levels = ",".join(str(value) for value in metadata.get("r12_tower_outer_four_real_preimage_levels") or [])
    no_real = ",".join(str(value) for value in metadata.get("r12_tower_outer_no_real_preimage_levels") or [])
    exponents = ",".join(
        str(item.get("outer_y_exponent")) for item in metadata.get("r12_tower_outer_perturbations") or []
    )
    return (
        f"s={metadata.get('r12_tower_inner_parameter_s')}|mode={metadata.get('r12_tower_mode')}"
        f"|real={levels}|none={no_real}|outer_y={exponents}"
    )


def exact_tower_support(coeffs: Iterable[int]) -> bool:
    """The chosen inner q is even, so the exact tower should have even support."""

    return all(index % 2 == 0 for index, coeff in enumerate(coeffs) if int(coeff) != 0)


def sort_key(record: dict[str, Any]) -> tuple[float, int, float, int]:
    components = record.get("score_components") or {}
    return (
        float(record.get("coefficient_height") or 0.0),
        -int(components.get("cycle_diversity_count") or 0),
        float(record.get("log_abs_discriminant") or 0.0),
        int(record.get("generation_metadata", {}).get("r12_tower_perturbation_terms") or 0),
    )


def select_diverse(records: list[dict[str, Any]], *, limit: int, per_family_cap: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    selected_hashes: set[str] = set()
    rows = sorted(records, key=sort_key)
    by_s: dict[int, list[dict[str, Any]]] = {}
    for record in rows:
        s_value = int((record.get("generation_metadata") or {}).get("r12_tower_inner_parameter_s") or 0)
        by_s.setdefault(s_value, []).append(record)
    s_order = sorted(by_s, key=lambda s_value: sort_key(by_s[s_value][0]))

    progressed = True
    while len(selected) < int(limit) and progressed:
        progressed = False
        for s_value in s_order:
            candidates = by_s.get(s_value) or []
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
        record["r12_tower_queue_rank"] = rank
    return selected


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 R12 Tower Candidate Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Trials attempted: {summary.get('trials_attempted')}",
        f"- Valid r=12 candidates: {summary.get('valid_r12_candidates')}",
        f"- Selected rows: {summary.get('selected_rows')}",
        f"- Queue status: `{summary.get('queue_status')}`",
        f"- Selected mode counts: `{json.dumps(summary.get('selected_mode_counts'), sort_keys=True)}`",
        f"- Selected inner-s counts: `{json.dumps(summary.get('selected_inner_s_counts'), sort_keys=True)}`",
        f"- Rejected counts: `{json.dumps(summary.get('rejected_counts'), sort_keys=True)}`",
        "",
        "| rank | hash | mode | s | four-real levels | no-real levels | outer perturbations | height | log disc |",
        "| ---: | --- | --- | ---: | --- | --- | --- | ---: | ---: |",
    ]
    for row in selected:
        metadata = row.get("generation_metadata") or {}
        perturbations = ",".join(
            f"{item.get('outer_y_exponent')}:{item.get('delta')}"
            for item in metadata.get("r12_tower_outer_perturbations") or []
        )
        real_levels = ",".join(str(value) for value in metadata.get("r12_tower_outer_four_real_preimage_levels") or [])
        no_real_levels = ",".join(str(value) for value in metadata.get("r12_tower_outer_no_real_preimage_levels") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("r12_tower_queue_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    f"`{metadata.get('r12_tower_mode')}`",
                    str(metadata.get("r12_tower_inner_parameter_s")),
                    f"`{real_levels}`",
                    f"`{no_real_levels}`",
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
        "".join(f"{record.get('r12_tower_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
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
    parser = argparse.ArgumentParser(description="Build a bounded CPU-only r12 exact-composed 6x4 tower queue")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, default=REPO_ROOT / "data/igp24/pair_status_20260706.json")
    parser.add_argument(
        "--followup_feedback_json",
        type=Path,
        default=REPO_ROOT / "data/igp24/r12_structured_followup_sair_accepted_feedback_20260706.json",
    )
    parser.add_argument("--seed", type=int, default=1246)
    parser.add_argument("--max_trials", type=int, default=240)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--per_family_cap", type=int, default=1)
    parser.add_argument("--coeff_bound", type=int, default=20_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    rng = random.Random(int(args.seed))
    feedback_rows = load_r12_followup_feedback(args.followup_feedback_json)
    known_hashes = known_hashes_from_pair_status(args.pair_status_json) | accepted_hashes(feedback_rows)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    rejected_counts: Counter[str] = Counter()
    observed_root_count_counts: Counter[str] = Counter()

    for trial in trial_variants(rng=rng, max_trials=int(args.max_trials)):
        trials_attempted += 1
        coeffs, metadata = coefficients_from_trial(trial)
        metadata["r12_tower_probe_seed"] = int(args.seed)
        metadata["r12_tower_coefficient_height"] = coefficient_height(coeffs)
        if not exact_tower_support(coeffs):
            rejected_counts["not_exact_even_tower_support"] += 1
            rejected.append({"trial": trial, "rejection_reason": "not_exact_even_tower_support", "metadata": metadata})
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
        metadata["r12_tower_local_validation"] = {
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
            experiment_name="r12_degree6_by_degree4_tower_probe",
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
                "score1_target_caveat": "Local r12 exact-composed tower row; exact 24T label must come from SAIR/Magma.",
            }
        )
        candidates.append(record)
        seen_hashes.add(str(analysis.canonical_hash))

    selected = select_diverse(candidates, limit=int(args.limit), per_family_cap=int(args.per_family_cap))
    queue_status = "manual_queue_ready" if len(selected) >= min(6, int(args.limit)) else "diagnostic_too_few_valid_rows"
    selected_metadata = [row.get("generation_metadata") or {} for row in selected]
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_r12_tower_probe.py",
        "source_commit": get_source_commit(args.repo_root.resolve()),
        "command": [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, "scripts/igp24_r12_tower_probe.py", *argv],
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
        "construction_family": "outer_degree6_composed_with_even_quartic_double_well",
        "decomposition_degree_pattern": "6x4",
        "followup_feedback_json": str(args.followup_feedback_json),
        "followup_feedback_rows_loaded": len(feedback_rows),
        "followup_feedback_label_counts": dict(sorted(Counter(row.label for row in feedback_rows).items())),
        "known_hashes_loaded": len(known_hashes),
        "trials_attempted": trials_attempted,
        "valid_r12_candidates": len(candidates),
        "selected_rows": len(selected),
        "queue_status": queue_status,
        "selected_mode_counts": dict(
            Counter(str(metadata.get("r12_tower_mode") or "unknown") for metadata in selected_metadata)
        ),
        "valid_mode_counts": dict(
            Counter(str((row.get("generation_metadata") or {}).get("r12_tower_mode") or "unknown") for row in candidates)
        ),
        "selected_inner_s_counts": dict(
            Counter(str(metadata.get("r12_tower_inner_parameter_s") or "unknown") for metadata in selected_metadata)
        ),
        "observed_root_count_counts": dict(observed_root_count_counts),
        "rejected_counts": dict(rejected_counts),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in selected],
        "selected_family_keys": [candidate_family_key(row) for row in selected],
        "coefficient_height_min": min((row.get("coefficient_height") for row in selected), default=None),
        "coefficient_height_max": max((row.get("coefficient_height") for row in selected), default=None),
        "structure_preservation": "exact h(q(x)) degree-6-by-degree-4 composition; q(x)=x^4-s*x^2",
        "recommendation": "manual_review_then_submit_small_r12_tower_probe"
        if selected
        else "diagnostic_only_try_alternate_tower_or_non_even_inner",
    }
    paths = write_outputs(output_dir=args.output_dir, selected=selected, rejected=rejected, summary=summary)
    summary["output_files"] = {key: str(path) for key, path in paths.items()}
    (args.output_dir / SUMMARY_JSON).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / REPORT_MD).write_text(build_report(summary, selected), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
