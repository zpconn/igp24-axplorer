#!/usr/bin/env python3
"""Dry-run AXG proposal loop for GPU-generated or saved IGP24 candidates.

The loop is intentionally submission-free: model samples are treated as a
proposal pool, then exact local fields and feedback-aware basin scoring decide
whether a small reviewed packet is worth preparing.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_active_learning_dataset import (
    DEFAULT_COLLAPSED_LABELS,
    DEFAULT_PAIR_STATUS,
    DEFAULT_SAIR_SYNC_DIR,
    coefficient_list,
    default_feedback_paths,
    feedback_rows,
    load_sair_sync,
    parse_csv_set,
    parse_int_set,
)
from scripts.igp24_anti_basin_planner import (
    build_basin_profile,
    build_submission_recommendation,
    is_model_generated_source,
    normalize_progress_cache,
    score_candidate_row,
    select_diverse_scores,
)
from scripts.igp24_model_registry import DEFAULT_REGISTRY, validate_version
from scripts.igp24_sair_sync import load_sync_status, load_sync_submission_rows
from scripts.igp24_shortlist import get_source_commit
from src.igp24.verifiers.sair_api import format_polynomial_line

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/axg_proposal_runs"
DEFAULT_ACCEPTED_FEEDBACK_ROOT = REPO_ROOT / "data/igp24"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def default_run_id() -> str:
    return "run_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def load_model_manifest(registry: Path, version: str) -> dict[str, Any]:
    validate_version(version)
    path = registry / "models" / version / "model_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"missing model manifest: {path}")
    return read_json(path)


def load_candidate_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        for index, row in enumerate(read_jsonl(path)):
            copied = dict(row)
            copied.setdefault("axg_source_path", str(path))
            copied.setdefault("axg_source_index", index)
            rows.append(copied)
    return rows


def coefficient_gcd(coefficients: list[int]) -> int:
    result = 0
    for value in coefficients:
        result = math.gcd(result, abs(int(value)))
    return result


def exact_filter_row(row: dict[str, Any], target_rs: set[int]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    coefficients = coefficient_list(row)
    if coefficients is None or len(coefficients) != 25:
        reasons.append("missing_25_integer_coefficients")
    else:
        if coefficients[0] == 0:
            reasons.append("zero_constant_coefficient")
        if coefficients[-1] != 1:
            reasons.append("not_monic_degree_24")
        if coefficient_gcd(coefficients) != 1:
            reasons.append("coefficient_gcd_not_one")
    r_value = row.get("real_root_count", row.get("r"))
    if target_rs:
        if r_value is None:
            reasons.append("missing_real_root_count")
        elif int(r_value) not in target_rs:
            reasons.append("real_root_count_not_target")
    if row.get("irreducible") is False:
        reasons.append("not_irreducible")
    if row.get("squarefree") is False:
        reasons.append("not_squarefree")
    if row.get("valid") is False:
        reasons.append("local_valid_false")
    return not reasons, reasons


def progress_snapshot_from_sync(sync_dir: Path | None) -> dict[str, Any]:
    if sync_dir and (sync_dir / "sair_label_progress.jsonl").exists():
        labels = read_jsonl(sync_dir / "sair_label_progress.jsonl")
        summary_path = sync_dir / "sair_sync_summary.json"
        summary = read_json(summary_path) if summary_path.exists() else {}
        return {
            "record_type": "igp24_sair_label_progress_snapshot",
            "created_at": summary.get("created_at") or utc_now(),
            "query": {"source": str(sync_dir)},
            "page_count": None,
            "label_count": len(labels),
            "pages": [{"generatedAt": summary.get("created_at"), "meta": {"published": True}}],
            "labels": labels,
        }
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": utc_now(),
        "query": {"source": "not_loaded"},
        "page_count": 0,
        "label_count": 0,
        "pages": [],
        "labels": [],
    }


def label_summary_from_sync(sync_dir: Path | None) -> dict[str, Any]:
    sync = load_sair_sync(sync_dir)
    summary: dict[str, Any] = {}
    for label, row in sync.get("progress_by_label", {}).items():
        summary[label] = {
            "global_progress": {
                "fully_covered": row.get("fully_covered"),
                "team_count": row.get("team_count"),
            }
        }
    return summary


def accepted_observations(paths: list[Path]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for path in paths:
        for row in feedback_rows(path):
            label = row.get("label") or row.get("verified_group_label")
            r_value = row.get("r") or row.get("real_root_count")
            if not label or r_value is None:
                continue
            observations.append(
                {
                    "label": str(label),
                    "pair_key": row.get("pair_key") or f"{label}|r={int(r_value)}",
                    "r": int(r_value),
                    "canonical_hash": row.get("canonical_hash"),
                    "construction_family": row.get("construction_family") or "",
                    "decomposition_pattern": row.get("decomposition_pattern") or "",
                    "perturbation_mode": row.get("perturbation_mode") or "",
                    "support_gcd": row.get("support_gcd"),
                    "even_support": row.get("even_support"),
                    "family_key": row.get("family_key") or "",
                    "template_family_id": row.get("template_family_id") or "",
                    "basin_fingerprint": row.get("basin_fingerprint") or "",
                    "mod_p_pattern_signature": row.get("mod_p_pattern_signature"),
                }
            )
    return observations


def row_status_class_from_submission_status(row: dict[str, Any]) -> str:
    if row.get("status") == "failed" or row.get("failed_reason"):
        return "failed"
    if row.get("queued"):
        return "pending"
    if row.get("scoring_status") == "pending":
        return "pending"
    if row.get("scoreable") is True or row.get("scoring_status") == "scoreable":
        return "scoreable"
    if row.get("status") == "accepted":
        return "accepted_not_scoreable_or_unknown"
    return "unknown"


def submission_status_rows_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return []
    rows: list[dict[str, Any]] = []
    submission_id = str(data.get("submissionId") or "")
    base = {
        "submission_id": submission_id,
        "competition_id": data.get("competitionId"),
        "created_at": data.get("createdAt"),
        "updated_at": data.get("updatedAt"),
        "kind": data.get("kind"),
        "description": (data.get("meta") or {}).get("description") or data.get("description"),
    }
    for row in data.get("verifiedPolynomials") or []:
        if not isinstance(row, dict):
            continue
        pair_key = None
        if row.get("label") and row.get("r") is not None:
            try:
                pair_key = f"{row['label']}|r={int(row['r'])}"
            except (TypeError, ValueError):
                pair_key = None
        normalized = {
            **base,
            "polynomial_index": row.get("polynomialIndex"),
            "submitted_line_number": int(row.get("polynomialIndex") or 0) + 1,
            "status": row.get("status") or "accepted",
            "label": row.get("label"),
            "t": row.get("t"),
            "r": row.get("r"),
            "pair_key": pair_key,
            "scoreable": row.get("scoreable"),
            "scoring_status": row.get("scoringStatus"),
            "scoring_reason": row.get("scoringReason"),
            "no_score_reason": row.get("noScoreReason"),
            "in_baseline": row.get("inBaseline"),
            "baseline_unlocked": row.get("baselineUnlocked"),
            "baseline_disc_abs": row.get("baselineDiscAbs"),
            "field_disc_abs": row.get("fieldDiscAbs"),
            "disc_source": row.get("discSource"),
        }
        normalized["status_class"] = row_status_class_from_submission_status(normalized)
        rows.append(normalized)
    for row in (data.get("payload") or {}).get("queuedPolynomials") or []:
        if not isinstance(row, dict):
            continue
        normalized = {
            **base,
            "polynomial_index": row.get("polynomialIndex"),
            "submitted_line_number": int(row.get("polynomialIndex") or 0) + 1,
            "status": row.get("status") or "queued",
            "queued": True,
        }
        normalized["status_class"] = row_status_class_from_submission_status(normalized)
        rows.append(normalized)
    for row in data.get("failedPolynomials") or []:
        if not isinstance(row, dict):
            continue
        normalized = {
            **base,
            "polynomial_index": row.get("polynomialIndex"),
            "submitted_line_number": int(row.get("polynomialIndex") or 0) + 1,
            "status": row.get("status") or "failed",
            "failed_reason": row.get("reason") or row.get("message") or row.get("error"),
        }
        normalized["status_class"] = row_status_class_from_submission_status(normalized)
        rows.append(normalized)
    return rows


def load_extra_submission_status_rows(paths: list[Path] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths or []:
        if path.exists():
            rows.extend(submission_status_rows_from_payload(read_json(path)))
    return rows


def score_filtered_candidates(
    filtered_rows: list[dict[str, Any]],
    *,
    target_rs: set[int],
    sync_dir: Path | None,
    feedback_paths: list[Path],
    collapsed_labels: set[str],
    crowded_team_threshold: int,
) -> list[dict[str, Any]]:
    progress_cache = normalize_progress_cache(
        progress_snapshot_from_sync(sync_dir),
        target_rs=sorted(target_rs) if target_rs else [24, 20, 16, 12, 8],
        max_pair_progress=5000,
    )
    basin_profile = build_basin_profile(
        accepted_observations(feedback_paths),
        label_summary_from_sync(sync_dir),
        avoid_labels=collapsed_labels,
        crowded_team_threshold=crowded_team_threshold,
    )
    return [
        score_candidate_row(
            row,
            target_rs=target_rs or set(progress_cache.get("target_rs") or []),
            progress_cache=progress_cache,
            basin_profile=basin_profile,
        )
        for row in filtered_rows
    ]


def selected_coefficients_rows(selected: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for row in selected:
        coeffs = coefficient_list(row.get("candidate") or {})
        if coeffs is not None:
            lines.append(format_polynomial_line(coeffs))
    return lines


def sample_export_source(row: dict[str, Any]) -> str:
    source = row.get("sample_export_source")
    if source:
        return str(source)
    source_sample_export = row.get("source_sample_export")
    if isinstance(source_sample_export, dict):
        source = source_sample_export.get("sample_export_source")
        if source:
            return str(source)
    generation_metadata = row.get("generation_metadata")
    if isinstance(generation_metadata, dict):
        source = generation_metadata.get("source")
        if source:
            return str(source)
    return "unknown"


def selected_sample_export_source(row: dict[str, Any]) -> str:
    candidate = row.get("candidate")
    if isinstance(candidate, dict):
        return sample_export_source(candidate)
    return sample_export_source(row)


def _counter_map(counter_by_key: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: dict(counter) for key, counter in sorted(counter_by_key.items())}


def build_source_basin_summary(
    *,
    candidates: list[dict[str, Any]],
    filtered_rows: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    selected: list[dict[str, Any]],
) -> dict[str, Any]:
    classification_by_source: dict[str, Counter[str]] = {}
    risk_by_source: dict[str, Counter[str]] = {}
    mode_by_source: dict[str, Counter[str]] = {}
    template_family_by_source: dict[str, Counter[str]] = {}
    basin_fingerprint_by_source: dict[str, Counter[str]] = {}
    eligible_by_source: Counter[str] = Counter()
    rejected_basin_by_source: Counter[str] = Counter()

    for row in scores:
        source = selected_sample_export_source(row)
        features = row.get("features") or {}
        classification_by_source.setdefault(source, Counter())[str(row.get("anti_basin_classification") or "unknown")] += 1
        mode_by_source.setdefault(source, Counter())[str(features.get("perturbation_mode") or "unknown")] += 1
        template_family_by_source.setdefault(source, Counter())[str(features.get("template_family_id") or "unknown")] += 1
        basin_fingerprint_by_source.setdefault(source, Counter())[str(features.get("basin_fingerprint") or "unknown")] += 1
        if row.get("eligible_for_packet"):
            eligible_by_source[source] += 1
        else:
            rejected_basin_by_source[source] += 1
        for reason in row.get("risk_reasons") or []:
            risk_by_source.setdefault(source, Counter())[str(reason)] += 1

    survivor_source_counts = Counter(sample_export_source(row) for row in filtered_rows)
    selected_source_counts = Counter(selected_sample_export_source(row) for row in selected)
    model_generated_survivors = sum(
        count for source, count in survivor_source_counts.items() if is_model_generated_source(source)
    )
    seed_bank_survivors = sum(
        count for source, count in survivor_source_counts.items() if "seed_bank" in source
    )
    return {
        "candidate_rows_by_source": dict(Counter(sample_export_source(row) for row in candidates)),
        "target_r_survivor_rows_by_source": dict(survivor_source_counts),
        "scored_rows_by_source": dict(Counter(selected_sample_export_source(row) for row in scores)),
        "eligible_rows_by_source": dict(eligible_by_source),
        "rejected_basin_rows_by_source": dict(rejected_basin_by_source),
        "selected_rows_by_source": dict(selected_source_counts),
        "classification_counts_by_source": _counter_map(classification_by_source),
        "risk_reason_counts_by_source": _counter_map(risk_by_source),
        "perturbation_mode_counts_by_source": _counter_map(mode_by_source),
        "template_family_counts_by_source": _counter_map(template_family_by_source),
        "basin_fingerprint_counts_by_source": _counter_map(basin_fingerprint_by_source),
        "model_generated_target_r_survivor_rows": model_generated_survivors,
        "seed_bank_target_r_survivor_rows": seed_bank_survivors,
        "model_generated_eligible_rows": sum(
            count for source, count in eligible_by_source.items() if is_model_generated_source(source)
        ),
        "model_generated_selected_rows": sum(
            count for source, count in selected_source_counts.items() if is_model_generated_source(source)
        ),
    }


def run_proposal_loop(
    *,
    version: str,
    registry: Path,
    run_id: str,
    candidate_paths: list[Path],
    feedback_paths: list[Path],
    sync_dir: Path | None,
    output_dir: Path,
    target_rs: set[int],
    collapsed_labels: set[str],
    packet_limit: int,
    min_packet_rows: int,
    per_mode_cap: int,
    per_pattern_cap: int,
    crowded_team_threshold: int,
    dry_run: bool,
    min_model_generated_rows: int = 0,
    min_template_family_count: int = 0,
    min_basin_fingerprint_count: int = 0,
    reject_unknown_provenance: bool = False,
    extra_submission_status_paths: list[Path] | None = None,
) -> dict[str, Any]:
    manifest = load_model_manifest(registry, version)
    candidates = load_candidate_rows(candidate_paths)
    filtered_rows: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in candidates:
        ok, reasons = exact_filter_row(row, target_rs)
        if ok:
            filtered_rows.append(row)
        else:
            rejected.append(
                {
                    "canonical_hash": row.get("canonical_hash"),
                    "source_path": row.get("axg_source_path"),
                    "source_index": row.get("axg_source_index"),
                    "reasons": reasons,
                }
            )

    scores = score_filtered_candidates(
        filtered_rows,
        target_rs=target_rs,
        sync_dir=sync_dir,
        feedback_paths=feedback_paths,
        collapsed_labels=collapsed_labels,
        crowded_team_threshold=crowded_team_threshold,
    )
    selected = select_diverse_scores(
        scores,
        packet_limit=packet_limit,
        per_mode_cap=per_mode_cap,
        per_pattern_cap=per_pattern_cap,
    )
    sync_status = load_sync_status(sync_dir) if sync_dir and (sync_dir / "sair_sync_summary.json").exists() else None
    sync_submission_rows = load_sync_submission_rows(sync_dir) if sync_dir and sync_dir.exists() else []
    extra_submission_rows = load_extra_submission_status_rows(extra_submission_status_paths)
    sync_submission_rows = [*sync_submission_rows, *extra_submission_rows]
    recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=min_packet_rows,
        min_model_generated_rows=min_model_generated_rows,
        min_template_family_count=min_template_family_count,
        min_basin_fingerprint_count=min_basin_fingerprint_count,
        reject_unknown_provenance=reject_unknown_provenance,
        sync_status=sync_status,
        sync_submission_rows=sync_submission_rows,
        pending_collision_labels=collapsed_labels,
    )
    decision = "reviewed_packet_ready_for_dry_run" if recommendation["recommended_for_sair_packet"] else "hold_no_submission"

    run_output = output_dir / run_id
    run_output.mkdir(parents=True, exist_ok=True)
    filtered_path = run_output / "filtered_candidates.jsonl"
    rejected_path = run_output / "rejected_candidates.jsonl"
    score_path = run_output / "basin_risk_scores.jsonl"
    selected_path = run_output / "selected_review_packet.jsonl"
    coeff_path = run_output / "selected_review_coefficients.txt"
    summary_path = run_output / "proposal_loop_summary.json"
    report_path = run_output / "proposal_loop_report.md"
    run_manifest_path = run_output / "run_manifest.json"

    write_jsonl(filtered_path, filtered_rows)
    write_jsonl(rejected_path, rejected)
    write_jsonl(score_path, scores)
    write_jsonl(selected_path, selected)
    coeff_lines = selected_coefficients_rows(selected)
    coeff_path.write_text("\n".join(coeff_lines) + ("\n" if coeff_lines else ""), encoding="utf-8")

    rejection_counts = Counter(reason for row in rejected for reason in row["reasons"])
    score_class_counts = Counter(row["anti_basin_classification"] for row in scores)
    risk_counts = Counter(reason for row in scores for reason in row.get("risk_reasons") or [])
    source_basin_summary = build_source_basin_summary(
        candidates=candidates,
        filtered_rows=filtered_rows,
        scores=scores,
        selected=selected,
    )
    summary = {
        "schema_version": 1,
        "record_type": "igp24_axg_proposal_loop_summary",
        "created_at": utc_now(),
        "source_commit": get_source_commit(REPO_ROOT),
        "model_version": version,
        "run_id": run_id,
        "dry_run": dry_run,
        "model_manifest_description": manifest.get("description"),
        "candidate_source_count": len(candidate_paths),
        "candidate_rows": len(candidates),
        "filtered_rows": len(filtered_rows),
        "rejected_rows": len(rejected),
        "scored_rows": len(scores),
        "selected_rows": len(selected),
        "coefficient_lines": len(coeff_lines),
        "target_rs": sorted(target_rs),
        "decision": decision,
        "recommendation": recommendation,
        "sair_sync": {
            "sync_dir": str(sync_dir) if sync_dir else None,
            "submission_rows_loaded": len(sync_submission_rows),
            "extra_submission_status_paths": [str(path) for path in extra_submission_status_paths or []],
            "extra_submission_rows_loaded": len(extra_submission_rows),
            "sync_status": sync_status,
            "sync_gate": recommendation.get("sync_submission_gate"),
        },
        "rejection_reason_counts": dict(rejection_counts),
        "score_classification_counts": dict(score_class_counts),
        "risk_reason_counts": dict(risk_counts),
        "candidate_sample_export_source_counts": dict(Counter(sample_export_source(row) for row in candidates)),
        "filtered_sample_export_source_counts": dict(Counter(sample_export_source(row) for row in filtered_rows)),
        "selected_sample_export_source_counts": dict(Counter(selected_sample_export_source(row) for row in selected)),
        "source_basin_summary": source_basin_summary,
        "diversity_gates": {
            "packet_limit": int(packet_limit),
            "min_packet_rows": int(min_packet_rows),
            "min_model_generated_rows": int(min_model_generated_rows),
            "min_template_family_count": int(min_template_family_count),
            "min_basin_fingerprint_count": int(min_basin_fingerprint_count),
            "reject_unknown_provenance": bool(reject_unknown_provenance),
            "per_mode_cap": int(per_mode_cap),
            "per_pattern_cap": int(per_pattern_cap),
            "crowded_team_threshold": int(crowded_team_threshold),
        },
        "artifacts": {
            "filtered_candidates": str(filtered_path),
            "rejected_candidates": str(rejected_path),
            "basin_risk_scores": str(score_path),
            "selected_review_packet": str(selected_path),
            "selected_review_coefficients": str(coeff_path),
            "summary": str(summary_path),
            "report": str(report_path),
            "run_manifest": str(run_manifest_path),
        },
        "safety": {
            "raw_gpu_samples_submitted": False,
            "calls_sair_post": False,
            "auto_submits": False,
            "dry_run_only": bool(dry_run),
            "api_key_recorded": False,
        },
    }
    write_json(summary_path, summary)

    report_path.write_text(
        "\n".join(
            [
                "# AXG Proposal Loop",
                "",
                f"- Model version: `{version}`",
                f"- Run id: `{run_id}`",
                f"- Candidate rows: {len(candidates)}",
                f"- Filtered rows: {len(filtered_rows)}",
                f"- Rejected rows: {len(rejected)}",
                f"- Selected rows: {len(selected)}",
                f"- Decision: `{decision}`",
                f"- Recommendation reason: {recommendation['reason']}",
                f"- Local packet ready: `{recommendation.get('local_recommended_for_sair_packet')}`",
                f"- Sync gate: `{json.dumps(recommendation.get('sync_submission_gate') or {}, sort_keys=True)}`",
                f"- Model-generated target-r survivors: `{source_basin_summary['model_generated_target_r_survivor_rows']}`",
                f"- Model-generated eligible rows: `{source_basin_summary['model_generated_eligible_rows']}`",
                f"- Source basin summary: `{json.dumps(source_basin_summary, sort_keys=True)}`",
                f"- SAIR live submission: `false`",
                "",
                "This run is a proposal-selection dry run. It does not submit raw GPU",
                "samples or reviewed packets to SAIR.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_json(
        run_manifest_path,
        {
            "schema_version": 1,
            "record_type": "igp24_axg_proposal_run",
            "created_at": utc_now(),
            "source_commit": get_source_commit(REPO_ROOT),
            "model_version": version,
            "run_id": run_id,
            "registry": str(registry),
            "candidate_paths": [str(path) for path in candidate_paths],
            "accepted_feedback_paths": [str(path) for path in feedback_paths],
            "sair_sync_dir": str(sync_dir) if sync_dir else None,
            "extra_submission_status_paths": [str(path) for path in extra_submission_status_paths or []],
            "training_phase": {
                "status": "not_started_in_this_run",
                "uses_existing_candidate_files": True,
            },
            "gpu_phase": {
                "status": "not_executed_in_dry_run",
                "command_templates": [
                    "python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup ...",
                    "python3 scripts/igp24_score_sample_export.py --source_export_path ...",
                ],
            },
            "outputs": summary["artifacts"],
            "decision": decision,
            "recommendation": recommendation,
            "sair_sync_gate": recommendation.get("sync_submission_gate"),
            "diversity_gates": summary["diversity_gates"],
            "source_basin_summary": source_basin_summary,
            "safety": summary["safety"],
        },
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--run_id", default=default_run_id())
    parser.add_argument("--candidate_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--accepted_feedback_json", type=Path, action="append", default=[])
    parser.add_argument("--auto_feedback_root", type=Path, default=DEFAULT_ACCEPTED_FEEDBACK_ROOT)
    parser.add_argument("--sair_sync_dir", type=Path, default=DEFAULT_SAIR_SYNC_DIR)
    parser.add_argument("--extra_submission_status_json", type=Path, action="append", default=[])
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target_rs", default="24,20,16,12,8")
    parser.add_argument("--collapsed_labels", default=",".join(sorted(DEFAULT_COLLAPSED_LABELS)))
    parser.add_argument("--packet_limit", type=int, default=12)
    parser.add_argument("--min_packet_rows", type=int, default=8)
    parser.add_argument(
        "--min_model_generated_rows",
        type=int,
        default=0,
        help="minimum selected rows that must come from model-generated sample export sources before recommending a packet",
    )
    parser.add_argument("--per_mode_cap", type=int, default=4)
    parser.add_argument("--per_pattern_cap", type=int, default=4)
    parser.add_argument("--min_template_family_count", type=int, default=0)
    parser.add_argument("--min_basin_fingerprint_count", type=int, default=0)
    parser.add_argument("--reject_unknown_provenance", action="store_true", default=False)
    parser.add_argument("--crowded_team_threshold", type=int, default=20)
    parser.add_argument("--dry_run", action="store_true", default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    feedback_paths = list(args.accepted_feedback_json)
    if args.auto_feedback_root:
        feedback_paths.extend(default_feedback_paths(args.auto_feedback_root))
    summary = run_proposal_loop(
        version=args.version,
        registry=args.registry,
        run_id=args.run_id,
        candidate_paths=args.candidate_jsonl,
        feedback_paths=sorted(set(feedback_paths)),
        sync_dir=args.sair_sync_dir,
        output_dir=args.output_dir,
        target_rs=parse_int_set(args.target_rs),
        collapsed_labels=parse_csv_set(args.collapsed_labels),
        packet_limit=args.packet_limit,
        min_packet_rows=args.min_packet_rows,
        per_mode_cap=args.per_mode_cap,
        per_pattern_cap=args.per_pattern_cap,
        crowded_team_threshold=args.crowded_team_threshold,
        dry_run=bool(args.dry_run),
        min_model_generated_rows=args.min_model_generated_rows,
        min_template_family_count=args.min_template_family_count,
        min_basin_fingerprint_count=args.min_basin_fingerprint_count,
        reject_unknown_provenance=bool(args.reject_unknown_provenance),
        extra_submission_status_paths=list(args.extra_submission_status_json),
    )
    print(f"summary\t{summary['artifacts']['summary']}")
    print(f"run_manifest\t{summary['artifacts']['run_manifest']}")
    print(f"candidate_rows\t{summary['candidate_rows']}")
    print(f"filtered_rows\t{summary['filtered_rows']}")
    print(f"selected_rows\t{summary['selected_rows']}")
    print(f"decision\t{summary['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
