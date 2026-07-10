#!/usr/bin/env python3
"""Run an offline target-bound g(x^2) construction experiment.

This script connects a structurally eligible router row to an executable
generator. It is offline-only: it does not call SAIR, does not use network
access, and cannot submit. Generated rows are review artifacts unless they
also pass local validation, known-submission exclusion, and adaptive
Frobenius target-exclusion evidence.
"""

from __future__ import annotations

import argparse
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
    GX2_GENERATOR_NAME,
    coefficients_from_gx2_trial,
    iter_gx2_trials,
)
from src.igp24.group_compatibility import GroupCycleIndex, read_jsonl  # noqa: E402
from src.igp24.polynomial import analysis_to_record, coefficient_height, score_candidate  # noqa: E402


DEFAULT_ROUTES = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/group_index_readiness_gate_phase3/full_degree24_universe_20260709/group_index_readiness_routes.jsonl"
)
DEFAULT_PROGRESS = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_label_progress.jsonl"
)
DEFAULT_SUBMISSIONS = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_submission_rows.jsonl"
)

CANDIDATES_JSONL = "gx2_route_candidates.jsonl"
REJECTED_JSONL = "gx2_route_rejected.jsonl"
COEFFICIENTS_TXT = "gx2_route_candidate_coefficients.txt"
HASHES_TXT = "gx2_route_candidate_hashes.txt"
SUMMARY_JSON = "gx2_route_experiment_summary.json"
REPORT_MD = "gx2_route_experiment_report.md"

SAFETY_NOTE = (
    "Offline g(x^2) route experiment. It does not call SAIR/network APIs and "
    "does not make a live submission."
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


def select_route(routes: list[dict[str, Any]], *, target_pair: str | None) -> dict[str, Any]:
    candidates = [
        row
        for row in routes
        if row.get("family") == "gx2_degree12_lift"
        and bool(row.get("structurally_eligible"))
        and (target_pair is None or row.get("pair_key") == target_pair)
    ]
    if not candidates:
        suffix = f" for {target_pair}" if target_pair else ""
        raise ValueError(f"no structurally eligible gx2 route found{suffix}")
    candidates.sort(
        key=lambda row: (
            bool(row.get("executable_generator_available")),
            float(row.get("combined_priority_score") or 0.0),
        ),
        reverse=True,
    )
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
    return {
        "canonical_hash": record.get("canonical_hash"),
        "short_hash": str(record.get("canonical_hash") or "")[:12],
        "construction_family": "gx2_degree12_lift",
        "executable_generator_name": GX2_GENERATOR_NAME,
        "pair_key": route.get("pair_key"),
        "label": route.get("label"),
        "r": route.get("r"),
        "coefficient_height": record.get("coefficient_height"),
        "decomposition_pattern": "g_of_x_squared",
        "composed_support": True,
        "exact_composed_support_divisor": 2,
        "odd_x_power_terms_present": metadata.get("odd_x_power_terms_present"),
        "support_after_lift": metadata.get("support_after_lift"),
        "positive_y_root_count": metadata.get("positive_y_root_count"),
        "negative_y_root_count": metadata.get("negative_y_root_count"),
    }


def evaluate_trial(
    *,
    trial: dict[str, Any],
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
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    coeffs, metadata = coefficients_from_gx2_trial(trial)
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
        seen_hashes=set(known_submissions) | seen_hashes,
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

    record = analysis_to_record(
        analysis,
        score,
        target_r=int(route["r"]),
        target_t=str(route["label"]),
        experiment_name="gx2_exact_composed_route_experiment",
        verification_status="local_valid_pending_adaptive_review",
        generation_metadata=metadata,
        local_search_metadata={"generator": GX2_GENERATOR_NAME, "offline": True},
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


def render_report(summary: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 g(x^2) Route Experiment",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Safety: {SAFETY_NOTE}",
        f"- Target route: `{summary['target_pair']}` via `{summary['construction_family']}`",
        f"- Trials attempted: `{summary['trials_attempted']}`",
        f"- Local-valid candidates: `{summary['local_valid_candidate_count']}`",
        f"- Adaptive target-compatible candidates: `{summary['adaptive_target_compatible_count']}`",
        f"- Any valuable-target survivor candidates: `{summary['adaptive_any_valuable_survivor_count']}`",
        f"- Known-submission rejections: `{summary['rejected_counts'].get('known_submission_canonical_hash', 0)}`",
        f"- Live submission recommended now: `{summary['live_submission_recommended_now']}`",
        "",
        "## Candidate Rows",
        "",
        "| rank | hash | height | usable primes | target retained | valuable target | recommendation |",
        "| ---: | --- | ---: | ---: | --- | --- | --- |",
    ]
    for index, row in enumerate(candidates[:25], start=1):
        adaptive = row.get("adaptive_frobenius") or {}
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


def write_outputs(output_dir: Path, *, summary: dict[str, Any], candidates: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> None:
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
    parser.add_argument("--target_pair")
    parser.add_argument("--group_index", type=Path)
    parser.add_argument("--progress_jsonl", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--known_submission_jsonl", type=Path, action="append", default=None)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--max_trials", type=int, default=80)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--coeff_bound", type=int, default=1_000_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=5.0)
    parser.add_argument("--adaptive_max_primes", type=int, default=10)
    parser.add_argument("--adaptive_min_primes", type=int, default=10)
    parser.add_argument("--adaptive_stable_after", type=int, default=0)
    args = parser.parse_args(argv)

    routes = load_routes(args.routes_jsonl)
    route = select_route(routes, target_pair=args.target_pair)
    group_index = GroupCycleIndex(args.group_index) if args.group_index and args.group_index.exists() else None
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl and args.progress_jsonl.exists() else []
    known_submission_paths = args.known_submission_jsonl or [DEFAULT_SUBMISSIONS]
    known_submissions = load_known_submissions(known_submission_paths)

    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    trials_attempted = 0
    for trial in iter_gx2_trials(target_r=int(route["r"]), seed=int(args.seed), max_trials=int(args.max_trials)):
        trials_attempted += 1
        record, rejection = evaluate_trial(
            trial=trial,
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
        )
        if rejection is not None:
            rejected.append(rejection)
            continue
        if record is None:
            continue
        candidates.append(record)
        seen_hashes.add(str(record["canonical_hash"]))
        if len(candidates) >= int(args.limit):
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
        "record_type": "igp24_gx2_route_experiment",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_gx2_route_experiment.py",
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
        "executable_generator_name": GX2_GENERATOR_NAME,
        "structure_preservation": "exact g(x^2) support; no odd x-power perturbations",
        "trials_attempted": trials_attempted,
        "local_valid_candidate_count": len(candidates),
        "adaptive_target_compatible_count": len(adaptive_target_compatible),
        "adaptive_any_valuable_survivor_count": len(adaptive_any_valuable),
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
