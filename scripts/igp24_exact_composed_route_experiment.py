#!/usr/bin/env python3
"""Run an offline exact-composed construction route experiment.

This script connects a structurally eligible router row to an executable
target-bound generator such as g(x^2) or h(x^6). It is offline-only: it does
not call SAIR, does not use network access, and cannot submit. Generated rows
are review artifacts unless they also pass local validation, known-submission
exclusion, and adaptive Frobenius target-exclusion evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.adaptive_frobenius import adaptive_frobenius_evidence  # noqa: E402
from src.igp24.constructions.generators import (  # noqa: E402
    coefficients_from_trial_for_family,
    executable_generator_for_family,
    iter_trials_for_family,
)
from src.igp24.group_compatibility import GroupCycleIndex, read_jsonl  # noqa: E402
from src.igp24.polynomial import DEGREE, analysis_to_record, coefficient_height, export_coefficients, score_candidate  # noqa: E402


DEFAULT_ROUTES = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/construction_router_phase5/api_scoreable_followup_quartic_x6_exact_20260710/construction_target_routes.jsonl"
)
DEFAULT_PROGRESS = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_label_progress.jsonl"
)
DEFAULT_SUBMISSIONS = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_submission_rows.jsonl"
)

CANDIDATES_JSONL = "exact_composed_route_candidates.jsonl"
REJECTED_JSONL = "exact_composed_route_rejected.jsonl"
COEFFICIENTS_TXT = "exact_composed_route_candidate_coefficients.txt"
HASHES_TXT = "exact_composed_route_candidate_hashes.txt"
SUMMARY_JSON = "exact_composed_route_experiment_summary.json"
REPORT_MD = "exact_composed_route_experiment_report.md"

SAFETY_NOTE = (
    "Offline exact-composed route experiment. It does not call SAIR/network "
    "APIs and does not make a live submission."
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def coefficient_line(exported_coefficients: Iterable[int]) -> str:
    return ",".join(str(int(value)) for value in exported_coefficients)


def load_routes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    return read_jsonl(path)


def select_route(
    routes: list[dict[str, Any]],
    *,
    family_name: str,
    target_pair: str | None,
) -> dict[str, Any]:
    candidates = [
        row
        for row in routes
        if row.get("family") == family_name
        and bool(row.get("structurally_eligible"))
        and bool(row.get("executable_generator_available"))
        and (target_pair is None or row.get("pair_key") == target_pair)
    ]
    if not candidates:
        suffix = f" for {target_pair}" if target_pair else ""
        raise ValueError(f"no executable structurally eligible {family_name} route found{suffix}")
    candidates.sort(key=lambda row: float(row.get("combined_priority_score") or 0.0), reverse=True)
    return candidates[0]


def load_known_submissions(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    known: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            hash_value = row.get("canonical_hash") or row.get("candidate_hash")
            if not isinstance(hash_value, str) or not hash_value:
                continue
            known[hash_value] = {
                "canonical_hash": hash_value,
                "source_path": str(path),
                "submission_id": row.get("submissionId") or row.get("submission_id"),
                "status": row.get("status"),
                "label": row.get("label") or row.get("verified_group_label"),
                "r": row.get("r") or row.get("real_root_count"),
                "pair_key": row.get("pair_key")
                or (
                    f"{row.get('label')}|r={row.get('r')}"
                    if row.get("label") not in (None, "") and row.get("r") not in (None, "")
                    else None
                ),
            }
    return known


def row_features(record: dict[str, Any], route: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    divisor = metadata.get("exact_composed_support_divisor")
    decomposition_pattern = metadata.get("exact_composition_degree_pattern")
    if decomposition_pattern is None and divisor is not None:
        decomposition_pattern = f"base_polynomial_of_x_to_{divisor}"
    return {
        "canonical_hash": record.get("canonical_hash"),
        "short_hash": str(record.get("canonical_hash") or "")[:12],
        "construction_family": route.get("family"),
        "executable_generator_name": metadata.get("executable_generator_name"),
        "pair_key": route.get("pair_key"),
        "label": route.get("label"),
        "r": route.get("r"),
        "coefficient_height": record.get("coefficient_height"),
        "decomposition_pattern": decomposition_pattern,
        "composed_support": bool(metadata.get("composed_support")),
        "exact_composed_support_divisor": divisor,
        "exact_composition_degree_pattern": metadata.get("exact_composition_degree_pattern"),
        "support_after_lift": metadata.get("support_after_lift"),
        "positive_y_root_count": metadata.get("positive_y_root_count"),
        "negative_y_root_count": metadata.get("negative_y_root_count"),
        "inside_y_root_count": metadata.get("inside_y_root_count"),
        "outside_y_root_count": metadata.get("outside_y_root_count"),
        "four_real_preimage_level_count": metadata.get("four_real_preimage_level_count"),
        "no_real_preimage_level_count": metadata.get("no_real_preimage_level_count"),
        "odd_x_power_terms_present": metadata.get("odd_x_power_terms_present"),
        "non_x6_power_terms_present": metadata.get("non_x6_power_terms_present"),
    }


def evaluate_trial(
    *,
    trial: dict[str, Any],
    family_name: str,
    route: dict[str, Any],
    known_submissions: dict[str, dict[str, Any]],
    seen_hashes: set[str],
    group_index: GroupCycleIndex | None,
    progress_rows: list[dict[str, Any]],
    coeff_bound: int,
    prime_limit: int,
    exact_score_timeout: float,
    adaptive_max_primes: int,
    adaptive_min_primes: int,
    adaptive_stable_after: int,
    translation_radius: int,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    coeffs, metadata = coefficients_from_trial_for_family(family_name=family_name, trial=trial)
    metadata.update(
        {
            "target_pair": route.get("pair_key"),
            "target_label": route.get("label"),
            "target_group_block_sizes": route.get("target_group_block_sizes") or [],
            "route_combined_priority_score": route.get("combined_priority_score"),
        }
    )
    if coefficient_height(coeffs) > int(coeff_bound):
        return None, {"trial": trial, "metadata": metadata, "rejection_reason": "coefficient_height_exceeds_bound"}

    score, analysis = score_candidate(
        coeffs,
        coeff_bound=int(coeff_bound),
        target_r=int(route["r"]),
        prime_limit=int(prime_limit),
        exact_score_timeout=float(exact_score_timeout),
        seen_hashes=seen_hashes,
        translation_radius=int(translation_radius),
    )
    metadata["local_validation"] = {
        "valid": bool(analysis.valid),
        "real_root_count": analysis.real_root_count,
        "irreducible": analysis.irreducible,
        "squarefree": analysis.squarefree,
        "canonical_hash": analysis.canonical_hash,
        "rejection_reason": analysis.rejection_reason,
    }
    if not analysis.valid:
        return None, {"trial": trial, "metadata": metadata, "rejection_reason": analysis.rejection_reason}
    if analysis.real_root_count != int(route["r"]):
        return None, {
            "trial": trial,
            "metadata": metadata,
            "canonical_hash": analysis.canonical_hash,
            "real_root_count": analysis.real_root_count,
            "rejection_reason": "real_root_count_mismatch",
        }
    if analysis.canonical_hash in known_submissions:
        return None, {
            "trial": trial,
            "metadata": metadata,
            "canonical_hash": analysis.canonical_hash,
            "known_submission": known_submissions[analysis.canonical_hash],
            "rejection_reason": "known_submission_canonical_hash",
        }
    if analysis.canonical_hash in seen_hashes:
        return None, {
            "trial": trial,
            "metadata": metadata,
            "canonical_hash": analysis.canonical_hash,
            "rejection_reason": "duplicate_generated_canonical_hash",
        }

    generator_name = str(metadata.get("executable_generator_name") or trial.get("generator_name") or "")
    record = analysis_to_record(
        analysis,
        score,
        target_r=int(route["r"]),
        target_t=str(route["label"]),
        experiment_name="exact_composed_route_experiment",
        verification_status="local_valid_pending_adaptive_review",
        generation_metadata=metadata,
        local_search_metadata={"generator": generator_name, "offline": True},
    )
    record["features"] = row_features(record, route, metadata)
    record["route"] = {
        "pair_key": route.get("pair_key"),
        "label": route.get("label"),
        "r": route.get("r"),
        "family": route.get("family"),
        "target_group_block_sizes": route.get("target_group_block_sizes") or [],
        "soundness": route.get("soundness"),
    }
    record["live_submission_recommended_now"] = False
    record["submission_recommendation"] = "false_pending_adaptive_evidence"

    if group_index is not None:
        adaptive = adaptive_frobenius_evidence(
            {**record, "r": int(route["r"]), "pair_key": route.get("pair_key"), "label": route.get("label")},
            group_index,
            progress_rows=progress_rows,
            max_usable_primes=int(adaptive_max_primes),
            min_usable_primes=int(adaptive_min_primes),
            stable_after=int(adaptive_stable_after),
            stop_when_no_valuable_targets=False,
        )
        compatibility = adaptive.get("final_compatibility") or {}
        target_label = str(route.get("label") or "")
        target_pair = str(route.get("pair_key") or "")
        survivors = set(str(label) for label in compatibility.get("indexed_target_labels_not_ruled_out") or [])
        valuable = set(str(pair) for pair in compatibility.get("valuable_targets_not_ruled_out") or [])
        record["adaptive_frobenius"] = adaptive
        record["group_compatibility"] = compatibility
        record["target_label_not_ruled_out"] = target_label in survivors
        record["target_pair_valuable_not_ruled_out"] = target_pair in valuable
        record["sufficient_adaptive_frobenius_evidence"] = int(adaptive.get("usable_prime_count") or 0) >= int(
            adaptive_min_primes
        )
        if not record["target_label_not_ruled_out"]:
            record["submission_recommendation"] = "false_target_label_ruled_out_by_adaptive_evidence"
        elif not record["target_pair_valuable_not_ruled_out"]:
            record["submission_recommendation"] = "false_target_pair_not_valuable_under_progress"
        elif not record["sufficient_adaptive_frobenius_evidence"]:
            record["submission_recommendation"] = "false_insufficient_adaptive_evidence"
        else:
            record["submission_recommendation"] = "offline_review_only_target_compatible"
    else:
        record["adaptive_frobenius"] = None
        record["group_compatibility"] = None
        record["target_label_not_ruled_out"] = None
        record["target_pair_valuable_not_ruled_out"] = None
        record["sufficient_adaptive_frobenius_evidence"] = False
        record["submission_recommendation"] = "false_missing_group_index"

    return record, None


def raw_coefficients_hash(coefficients: Iterable[int]) -> str:
    payload = json.dumps(
        {"degree": DEGREE, "coefficients": [int(value) for value in coefficients]},
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_prefilter_trial(
    *,
    trial: dict[str, Any],
    family_name: str,
    route: dict[str, Any],
    coeff_bound: int,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    coeffs, metadata = coefficients_from_trial_for_family(family_name=family_name, trial=trial)
    metadata.update(
        {
            "target_pair": route.get("pair_key"),
            "target_label": route.get("label"),
            "target_group_block_sizes": route.get("target_group_block_sizes") or [],
            "route_combined_priority_score": route.get("combined_priority_score"),
        }
    )
    height = coefficient_height(coeffs)
    if height > int(coeff_bound):
        return None, {"trial": trial, "metadata": metadata, "rejection_reason": "coefficient_height_exceeds_bound"}
    if int(coeffs[0]) == 0:
        return None, {"trial": trial, "metadata": metadata, "rejection_reason": "zero_constant_term"}
    raw_hash = raw_coefficients_hash(coeffs)
    record = {
        "record_type": "igp24_exact_composed_route_prefilter_candidate",
        "schema_version": 1,
        "canonical_hash": raw_hash,
        "raw_coefficients_hash": raw_hash,
        "canonical_hash_status": "not_computed_prefilter_only",
        "exported_coefficients": export_coefficients(coeffs),
        "coefficient_height": height,
        "features": {
            "canonical_hash": raw_hash,
            "short_hash": raw_hash[:12],
            "construction_family": route.get("family"),
            "executable_generator_name": metadata.get("executable_generator_name"),
            "pair_key": route.get("pair_key"),
            "label": route.get("label"),
            "r": route.get("r"),
            "coefficient_height": height,
            "decomposition_pattern": metadata.get("exact_composition_degree_pattern"),
            "composed_support": bool(metadata.get("composed_support")),
            "support_after_lift": metadata.get("support_after_lift"),
            "inside_y_root_count": metadata.get("inside_y_root_count"),
            "outside_y_root_count": metadata.get("outside_y_root_count"),
            "four_real_preimage_level_count": metadata.get("four_real_preimage_level_count"),
            "no_real_preimage_level_count": metadata.get("no_real_preimage_level_count"),
        },
        "route": {
            "pair_key": route.get("pair_key"),
            "label": route.get("label"),
            "r": route.get("r"),
            "family": route.get("family"),
            "target_group_block_sizes": route.get("target_group_block_sizes") or [],
            "soundness": route.get("soundness"),
        },
        "generation_metadata": metadata,
        "local_validation_status": "not_run_prefilter_only",
        "adaptive_frobenius": None,
        "group_compatibility": None,
        "target_label_not_ruled_out": None,
        "target_pair_valuable_not_ruled_out": None,
        "sufficient_adaptive_frobenius_evidence": False,
        "eligible_for_packet": False,
        "live_submission_recommended_now": False,
        "submission_recommendation": "false_prefilter_only_exact_validation_not_run",
    }
    return record, None


def render_report(summary: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Exact-Composed Route Experiment",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Safety: {SAFETY_NOTE}",
        f"- Target route: `{summary['target_pair']}` via `{summary['construction_family']}`",
        f"- Executable generator: `{summary['executable_generator_name']}`",
        f"- Structure preservation: `{summary['structure_preservation']}`",
        f"- Trials attempted: `{summary['trials_attempted']}`",
        f"- Local-valid candidates stored: `{summary['local_valid_candidate_count']}`",
        f"- Local-valid candidates evaluated: `{summary['local_valid_evaluated_count']}`",
        f"- Local-valid overflow not stored: `{summary['local_valid_overflow_count']}`",
        f"- Adaptive target-compatible candidates: `{summary['adaptive_target_compatible_count']}`",
        f"- Any valuable-target survivor candidates: `{summary['adaptive_any_valuable_survivor_count']}`",
        f"- Known-submission rejections: `{summary['rejected_counts'].get('known_submission_canonical_hash', 0)}`",
        f"- Live submission recommended now: `{summary['live_submission_recommended_now']}`",
        "",
        "## Candidate Rows",
        "",
        "| rank | hash | height | usable primes | target label retained | target pair valuable | any valuable pairs | recommendation |",
        "| ---: | --- | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for index, row in enumerate(candidates[:25], start=1):
        adaptive = row.get("adaptive_frobenius") or {}
        compatibility = row.get("group_compatibility") or {}
        valuable_pair_count = len(compatibility.get("valuable_targets_not_ruled_out") or [])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    str(row.get("coefficient_height")),
                    str(adaptive.get("usable_prime_count")),
                    f"`{row.get('target_label_not_ruled_out')}`",
                    f"`{row.get('target_pair_valuable_not_ruled_out')}`",
                    str(valuable_pair_count),
                    f"`{row.get('submission_recommendation')}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Compatibility here is necessary target-exclusion evidence only; it is not exact 24T label verification.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    output_dir: Path,
    *,
    summary: dict[str, Any],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / CANDIDATES_JSONL, candidates)
    write_jsonl(output_dir / REJECTED_JSONL, rejected)
    (output_dir / COEFFICIENTS_TXT).write_text(
        "".join(coefficient_line(row["exported_coefficients"]) + "\n" for row in candidates),
        encoding="utf-8",
    )
    (output_dir / HASHES_TXT).write_text(
        "".join(f"{index}\t{row.get('canonical_hash')}\n" for index, row in enumerate(candidates, start=1)),
        encoding="utf-8",
    )
    (output_dir / REPORT_MD).write_text(render_report(summary, candidates), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes_jsonl", type=Path, default=DEFAULT_ROUTES)
    parser.add_argument("--family", default="quartic_in_x6")
    parser.add_argument("--target_pair")
    parser.add_argument("--group_index", type=Path)
    parser.add_argument("--progress_jsonl", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--known_submission_jsonl", type=Path, action="append", default=None)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--max_trials", type=int, default=120)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--continue_after_candidate_limit",
        action="store_true",
        help=(
            "Continue evaluating trials after --limit local-valid rows have been stored. "
            "Any later target-compatible or valuable-survivor row is still retained."
        ),
    )
    parser.add_argument(
        "--target_compatible_limit",
        type=int,
        default=1,
        help="Stop early after this many target-compatible rows are found; use 0 to disable.",
    )
    parser.add_argument("--coeff_bound", type=int, default=1_000_000_000)
    parser.add_argument("--prime_limit", type=int, default=11)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--translation_radius", type=int, default=2)
    parser.add_argument("--adaptive_max_primes", type=int, default=20)
    parser.add_argument("--adaptive_min_primes", type=int, default=10)
    parser.add_argument("--adaptive_stable_after", type=int, default=0)
    parser.add_argument(
        "--prefilter_only",
        action="store_true",
        help="Only generate cheap coefficient/height/hash rows; skip exact local validation and adaptive evidence.",
    )
    args = parser.parse_args(argv)

    family_name = str(args.family)
    spec = executable_generator_for_family(family_name)
    if spec is None:
        raise ValueError(f"no executable generator registered for family {family_name!r}")

    routes = load_routes(args.routes_jsonl)
    route = select_route(routes, family_name=family_name, target_pair=args.target_pair)
    group_index = GroupCycleIndex(args.group_index) if args.group_index and args.group_index.exists() else None
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl and args.progress_jsonl.exists() else []
    known_submission_paths = args.known_submission_jsonl or [DEFAULT_SUBMISSIONS]
    known_submissions = load_known_submissions(known_submission_paths)

    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    local_valid_evaluated_count = 0
    local_valid_overflow_count = 0
    prefilter_evaluated_count = 0
    prefilter_overflow_count = 0
    target_compatible_seen_count = 0
    any_valuable_seen_count = 0
    for trial in iter_trials_for_family(
        family_name=family_name,
        target_r=int(route["r"]),
        seed=int(args.seed),
        max_trials=int(args.max_trials),
    ):
        trials_attempted += 1
        if bool(args.prefilter_only):
            record, rejection = evaluate_prefilter_trial(
                trial=trial,
                family_name=family_name,
                route=route,
                coeff_bound=int(args.coeff_bound),
            )
        else:
            record, rejection = evaluate_trial(
                trial=trial,
                family_name=family_name,
                route=route,
                known_submissions=known_submissions,
                seen_hashes=seen_hashes,
                group_index=group_index,
                progress_rows=progress_rows,
                coeff_bound=int(args.coeff_bound),
                prime_limit=int(args.prime_limit),
                exact_score_timeout=float(args.exact_score_timeout),
                adaptive_max_primes=int(args.adaptive_max_primes),
                adaptive_min_primes=int(args.adaptive_min_primes),
                adaptive_stable_after=int(args.adaptive_stable_after),
                translation_radius=int(args.translation_radius),
            )
        if rejection is not None:
            rejected.append(rejection)
            continue
        if record is None:
            continue
        if bool(args.prefilter_only):
            prefilter_evaluated_count += 1
            seen_hashes.add(str(record["canonical_hash"]))
            if len(candidates) < int(args.limit):
                record["retention_reason"] = "prefilter_within_candidate_limit"
                candidates.append(record)
            else:
                prefilter_overflow_count += 1
            if not bool(args.continue_after_candidate_limit) and len(candidates) >= int(args.limit):
                break
            continue
        local_valid_evaluated_count += 1
        seen_hashes.add(str(record["canonical_hash"]))
        target_compatible = (
            record.get("target_label_not_ruled_out") is True
            and record.get("target_pair_valuable_not_ruled_out") is True
            and record.get("sufficient_adaptive_frobenius_evidence") is True
        )
        any_valuable = (
            record.get("sufficient_adaptive_frobenius_evidence") is True
            and bool((record.get("group_compatibility") or {}).get("valuable_targets_not_ruled_out"))
        )
        target_compatible_seen_count += int(target_compatible)
        any_valuable_seen_count += int(any_valuable)
        retain_record = len(candidates) < int(args.limit) or target_compatible or any_valuable
        if retain_record:
            record["retention_reason"] = (
                "within_candidate_limit"
                if len(candidates) < int(args.limit)
                else "target_compatible_after_candidate_limit"
                if target_compatible
                else "valuable_survivor_after_candidate_limit"
            )
            candidates.append(record)
        else:
            local_valid_overflow_count += 1
        if int(args.target_compatible_limit) > 0 and target_compatible_seen_count >= int(args.target_compatible_limit):
            break
        if not bool(args.continue_after_candidate_limit) and len(candidates) >= int(args.limit):
            break

    rejected_counts = Counter(str(row.get("rejection_reason") or "unknown") for row in rejected)
    recommendation_counts = Counter(str(row.get("submission_recommendation") or "") for row in candidates)
    adaptive_target_compatible = [
        row
        for row in candidates
        if row.get("target_label_not_ruled_out") is True
        and row.get("target_pair_valuable_not_ruled_out") is True
        and row.get("sufficient_adaptive_frobenius_evidence") is True
    ]
    adaptive_any_valuable = [
        row
        for row in candidates
        if row.get("sufficient_adaptive_frobenius_evidence") is True
        and (row.get("group_compatibility") or {}).get("valuable_targets_not_ruled_out")
    ]
    summary = {
        "record_type": "igp24_exact_composed_route_experiment",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_exact_composed_route_experiment.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "routes_jsonl": str(args.routes_jsonl),
        "group_index": str(args.group_index) if args.group_index else None,
        "group_index_available": group_index is not None,
        "progress_jsonl": str(args.progress_jsonl) if args.progress_jsonl else None,
        "known_submission_jsonl": [str(path) for path in known_submission_paths],
        "known_submission_hash_count": len(known_submissions),
        "target_pair": route.get("pair_key"),
        "target_label": route.get("label"),
        "target_r": route.get("r"),
        "construction_family": route.get("family"),
        "executable_generator_name": spec.generator_name,
        "structure_preservation": spec.structure_preservation,
        "trials_attempted": trials_attempted,
        "max_trials": int(args.max_trials),
        "candidate_output_limit": int(args.limit),
        "continue_after_candidate_limit": bool(args.continue_after_candidate_limit),
        "target_compatible_limit": int(args.target_compatible_limit),
        "prefilter_only": bool(args.prefilter_only),
        "translation_radius": int(args.translation_radius),
        "local_valid_candidate_count": 0 if bool(args.prefilter_only) else len(candidates),
        "local_valid_evaluated_count": local_valid_evaluated_count,
        "local_valid_overflow_count": local_valid_overflow_count,
        "prefilter_candidate_count": len(candidates) if bool(args.prefilter_only) else 0,
        "prefilter_evaluated_count": prefilter_evaluated_count,
        "prefilter_overflow_count": prefilter_overflow_count,
        "prefilter_exact_validation_status": "not_run" if bool(args.prefilter_only) else "run",
        "adaptive_target_compatible_count": len(adaptive_target_compatible),
        "adaptive_target_compatible_seen_count": target_compatible_seen_count,
        "adaptive_any_valuable_survivor_count": len(adaptive_any_valuable),
        "adaptive_any_valuable_survivor_seen_count": any_valuable_seen_count,
        "candidate_recommendation_counts": dict(sorted(recommendation_counts.items())),
        "rejected_counts": dict(sorted(rejected_counts.items())),
        "selected_hashes": [row.get("canonical_hash") for row in candidates],
        "adaptive_target_compatible_hashes": [row.get("canonical_hash") for row in adaptive_target_compatible],
        "adaptive_any_valuable_survivor_hashes": [row.get("canonical_hash") for row in adaptive_any_valuable],
        "live_submission_recommended_now": False,
        "submission_recommendation": (
            "false_offline_review_only_even_if_target_compatible"
            if adaptive_target_compatible
            else "false_no_adaptive_target_compatible_candidates"
        ),
        "output_files": {
            "summary_json": str(args.output_dir / SUMMARY_JSON),
            "candidates_jsonl": str(args.output_dir / CANDIDATES_JSONL),
            "rejected_jsonl": str(args.output_dir / REJECTED_JSONL),
            "coefficients_txt": str(args.output_dir / COEFFICIENTS_TXT),
            "hashes_txt": str(args.output_dir / HASHES_TXT),
            "report_md": str(args.output_dir / REPORT_MD),
        },
    }
    write_outputs(args.output_dir, summary=summary, candidates=candidates, rejected=rejected)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
