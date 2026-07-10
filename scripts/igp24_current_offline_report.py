#!/usr/bin/env python3
"""Build a consolidated offline go/no-go report for the current IGP24 packet.

This helper is intentionally local/file-only. It reads already-written
artifacts and summarizes whether the current packet satisfies the remediation
go/no-go gates. It does not call SAIR, use network access, run exact
verifiers, train models, generate candidates, or submit anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl  # noqa: E402

SUMMARY_JSON = "current_offline_go_nogo_summary.json"
REPORT_MD = "current_offline_go_nogo_report.md"
TRIAGE_ROWS_JSONL = "current_offline_go_nogo_triage_rows.jsonl"


class OfflineReportError(ValueError):
    """Raised when a required artifact is missing or malformed."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OfflineReportError(f"missing required artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise OfflineReportError(f"{path}: expected JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        return None
    return read_json(path)


def parse_utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def evaluate_sair_sync_status(
    sync_summary: dict[str, Any] | None,
    *,
    max_sync_age_hours: float,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Classify a saved read-only SAIR sync artifact for the go/no-go gate."""

    if sync_summary is None:
        return {
            "provided": False,
            "status": "missing",
            "fresh_complete": False,
            "blockers": ["fresh_sair_sync_required_immediately_before_live_submission"],
            "warnings": [],
            "max_sync_age_hours": max_sync_age_hours,
        }

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    sync_status = sync_summary.get("sync_status") if isinstance(sync_summary.get("sync_status"), dict) else {}
    safety = sync_summary.get("safety") if isinstance(sync_summary.get("safety"), dict) else {}
    created_at = parse_utc_datetime(sync_summary.get("created_at"))
    age_hours = None
    if created_at is not None:
        age_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)

    complete = (
        bool(sync_status.get("global_progress_complete"))
        and bool(sync_status.get("submission_index_complete"))
        and bool(sync_status.get("submission_detail_complete"))
        and bool(sync_status.get("download_complete"))
        and bool(sync_status.get("full_submission_state_complete", sync_status.get("submission_state_complete")))
        and not bool(sync_status.get("partial_sync"))
    )
    fresh = age_hours is not None and age_hours <= max_sync_age_hours
    blockers: list[str] = []
    warnings: list[str] = []
    if bool(safety.get("sair_submission")):
        blockers.append("sair_sync_artifact_claims_submission")
    if not complete:
        blockers.append("fresh_sair_sync_incomplete")
    if created_at is None:
        blockers.append("fresh_sair_sync_timestamp_missing")
    elif not fresh:
        blockers.append("fresh_sair_sync_stale")
    if safety and bool(safety.get("api_key_recorded")):
        blockers.append("sair_sync_artifact_records_api_key")
    if not bool(safety.get("live_fetch")):
        warnings.append("sair_sync_artifact_not_live_fetch")

    status = "fresh_complete" if complete and fresh and not blockers else "not_usable"
    return {
        "provided": True,
        "status": status,
        "fresh_complete": status == "fresh_complete",
        "created_at": sync_summary.get("created_at"),
        "age_hours": round(age_hours, 6) if age_hours is not None else None,
        "max_sync_age_hours": max_sync_age_hours,
        "sync_status": {
            "partial_sync": sync_status.get("partial_sync"),
            "global_progress_complete": sync_status.get("global_progress_complete"),
            "submission_index_complete": sync_status.get("submission_index_complete"),
            "submission_detail_complete": sync_status.get("submission_detail_complete"),
            "download_complete": sync_status.get("download_complete"),
            "full_submission_state_complete": sync_status.get("full_submission_state_complete"),
            "submission_state_complete": sync_status.get("submission_state_complete"),
            "failing_endpoint": sync_status.get("failing_endpoint"),
        },
        "submissions": sync_summary.get("submissions") if isinstance(sync_summary.get("submissions"), dict) else {},
        "progress": sync_summary.get("progress") if isinstance(sync_summary.get("progress"), dict) else {},
        "safety": {
            "api_key_recorded": safety.get("api_key_recorded"),
            "sair_submission": safety.get("sair_submission"),
            "live_fetch": safety.get("live_fetch"),
            "network_calls": safety.get("network_calls"),
        },
        "blockers": blockers,
        "warnings": warnings,
    }


def load_triage_rows(path: Path | None, triage_summary: dict[str, Any]) -> list[dict[str, Any]]:
    if path is None:
        output_files = triage_summary.get("output_files") if isinstance(triage_summary.get("output_files"), dict) else {}
        raw_path = output_files.get("triage_jsonl")
        path = Path(raw_path) if raw_path else None
    if path is None or not path.exists():
        return []
    return read_jsonl(path)


def int_count(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def count_from_status(summary: dict[str, Any], field: str, key: str) -> int:
    value = summary.get(field)
    if not isinstance(value, dict):
        return 0
    try:
        return int(value.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def hash_from_row(row: dict[str, Any]) -> str | None:
    value = row.get("canonical_hash") or row.get("candidate_hash")
    return str(value) if value else None


def short_hash(value: str | None) -> str:
    return str(value or "")[:12]


def build_gate_status(
    *,
    packet: dict[str, Any],
    triage: dict[str, Any],
    adaptive: dict[str, Any],
    index_summary: dict[str, Any],
    historical: dict[str, Any],
    replay: dict[str, Any] | None,
    sair_sync_status: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not bool(index_summary.get("global_index_complete")):
        blockers.append("full_degree24_group_index_not_complete")
    if int_count(index_summary, "group_count") != int(index_summary.get("expected_global_group_count") or 25000):
        blockers.append("full_degree24_group_index_count_mismatch")
    integrity = index_summary.get("integrity") if isinstance(index_summary.get("integrity"), dict) else {}
    if integrity and not bool(integrity.get("integrity_ok")):
        blockers.append("full_degree24_group_index_integrity_failed")

    if int_count(historical, "indexed_true_label_containment_failures") != 0:
        blockers.append("historical_true_label_containment_failure")
    if int_count(historical, "evaluated_row_count") <= 0:
        blockers.append("historical_group_validation_missing")

    if replay and not bool(replay.get("phase7_minimum_gate_passed")):
        blockers.append("chronological_replay_minimum_gate_not_passed")
    elif replay is None:
        warnings.append("chronological_replay_summary_not_supplied")

    if int_count(packet, "selected_rows") <= 0:
        blockers.append("no_packet_rows_selected")
    if str(packet.get("expected_points_status")) != "unavailable_uncalibrated":
        warnings.append("expected_points_status_not_unavailable_uncalibrated_review_needed")
    if bool(packet.get("live_submission_recommended_now")):
        blockers.append("optimizer_should_not_authorize_live_submission")

    triage_reviewed_rows = int_count(triage, "reviewed_rows")
    triage_verified_rows = int_count(triage, "verified_rows")
    triage_exact_labels_complete = triage_reviewed_rows > 0 and triage_verified_rows == triage_reviewed_rows

    if int_count(triage, "known_submission_hash_rows") != 0:
        blockers.append("known_submission_hash_present")
    if not triage_exact_labels_complete:
        blockers.append("exact_magma_labels_missing")
    if count_from_status(triage, "exact_r_status_counts", "ok") != int_count(triage, "reviewed_rows"):
        blockers.append("exact_r_not_complete")
    if count_from_status(triage, "exact_nfdisc_status_counts", "ok") != int_count(triage, "reviewed_rows"):
        blockers.append("exact_nfdisc_not_complete")
    if int_count(triage, "submission_grade_rows") <= 0:
        blockers.append("score_aware_triage_has_no_submission_grade_rows")

    if int_count(adaptive, "failed_row_count") != 0:
        blockers.append("adaptive_frobenius_failures_present")
    if int_count(adaptive, "exact_label_missing_row_count") != 0 and not triage_exact_labels_complete:
        blockers.append("adaptive_rows_still_missing_exact_labels")
    elif int_count(adaptive, "exact_label_missing_row_count") != 0:
        warnings.append("adaptive_exact_label_missing_field_superseded_by_score_aware_triage")
    if int_count(adaptive, "intended_target_failure_rows") != 0:
        blockers.append("intended_target_ruled_out_by_adaptive_evidence")
    if int_count(adaptive, "final_valuable_target_survival_rows") <= 0:
        blockers.append("no_valuable_targets_survive_adaptive_evidence")

    diversity = packet.get("selected_diversity") if isinstance(packet.get("selected_diversity"), dict) else {}
    construction_counts = diversity.get("construction_family") if isinstance(diversity.get("construction_family"), dict) else {}
    if construction_counts and len(construction_counts) == 1 and int_count(packet, "selected_rows") > 1:
        warnings.append("packet_uses_single_construction_family")

    blockers.extend(str(item) for item in sair_sync_status.get("blockers") or [])
    warnings.extend(str(item) for item in sair_sync_status.get("warnings") or [])
    blockers.append("explicit_user_live_submission_approval_missing")

    return {
        "live_submission_recommended_now": False,
        "recommendation": "do_not_submit",
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
    }


def build_summary(
    *,
    packet_summary_path: Path,
    triage_summary_path: Path,
    triage_rows_path: Path | None,
    adaptive_summary_path: Path,
    index_summary_path: Path,
    historical_summary_path: Path,
    baseline_summary_path: Path | None,
    replay_summary_path: Path | None,
    gpu_summary_path: Path | None,
    sair_sync_summary_path: Path | None = None,
    max_sync_age_hours: float = 6.0,
    output_dir: Path,
    command: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    packet = read_json(packet_summary_path)
    triage = read_json(triage_summary_path)
    adaptive = read_json(adaptive_summary_path)
    index_summary = read_json(index_summary_path)
    historical = read_json(historical_summary_path)
    baseline = optional_json(baseline_summary_path)
    replay = optional_json(replay_summary_path)
    gpu = optional_json(gpu_summary_path)
    sair_sync = optional_json(sair_sync_summary_path)
    sair_sync_status = evaluate_sair_sync_status(sair_sync, max_sync_age_hours=max_sync_age_hours)
    triage_rows = load_triage_rows(triage_rows_path, triage)

    selected_hashes = [hash_from_row(row) for row in triage_rows if hash_from_row(row)]
    selected_hashes = selected_hashes or list(triage.get("submission_grade_hashes") or [])
    novel_candidate_hashes = [
        hash_value
        for hash_value, row in zip(selected_hashes, triage_rows)
        if not row.get("known_submission_hash_match")
    ]
    if not triage_rows:
        novel_candidate_hashes = selected_hashes if int_count(triage, "known_submission_hash_rows") == 0 else []

    exact_label_status_counts = triage.get("exact_label_status_counts") or {}
    exact_nfdisc_status_counts = triage.get("exact_nfdisc_status_counts") or {}
    exact_r_status_counts = triage.get("exact_r_status_counts") or {}
    gate = build_gate_status(
        packet=packet,
        triage=triage,
        adaptive=adaptive,
        index_summary=index_summary,
        historical=historical,
        replay=replay,
        sair_sync_status=sair_sync_status,
    )

    selected_rows = []
    for row in triage_rows:
        selected_rows.append(
            {
                "canonical_hash": hash_from_row(row),
                "short_hash": row.get("short_hash") or short_hash(hash_from_row(row)),
                "pair_key": row.get("pair_key"),
                "verified_group_label": row.get("verified_group_label"),
                "computed_r": row.get("computed_r"),
                "exact_label_status": row.get("exact_label_status"),
                "exact_nfdisc_status": row.get("exact_nfdisc_status"),
                "exact_nfdisc_abs": row.get("exact_nfdisc_abs"),
                "sair_progress_state": row.get("sair_progress_state"),
                "sair_score_value_status": row.get("sair_score_value_status"),
                "sair_progress_team_count": row.get("sair_progress_team_count"),
                "known_submission_hash_match": bool(row.get("known_submission_hash_match")),
                "score_aware_classification": row.get("score_aware_classification"),
                "submission_grade_candidate": bool(row.get("submission_grade_candidate")),
            }
        )

    summary = {
        "schema_version": 1,
        "record_type": "igp24_current_offline_go_nogo_report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_current_offline_report.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "command": command,
        "safety": {
            "local_file_only": True,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "magma_executed": False,
            "pari_executed": False,
            "gpu_training": False,
            "candidate_generation": False,
        },
        "inputs": {
            "packet_summary_json": str(packet_summary_path),
            "triage_summary_json": str(triage_summary_path),
            "triage_rows_jsonl": str(triage_rows_path) if triage_rows_path else None,
            "adaptive_summary_json": str(adaptive_summary_path),
            "index_summary_json": str(index_summary_path),
            "historical_summary_json": str(historical_summary_path),
            "baseline_summary_json": str(baseline_summary_path) if baseline_summary_path else None,
            "replay_summary_json": str(replay_summary_path) if replay_summary_path else None,
            "gpu_summary_json": str(gpu_summary_path) if gpu_summary_path else None,
            "sair_sync_summary_json": str(sair_sync_summary_path) if sair_sync_summary_path else None,
        },
        "architecture_status": {
            "full_group_index_complete": bool(index_summary.get("global_index_complete")),
            "indexed_group_count": index_summary.get("group_count"),
            "historical_evaluated_rows": historical.get("evaluated_row_count"),
            "historical_indexed_containment_failures": historical.get("indexed_true_label_containment_failures"),
            "historical_valuable_false_positive_rows_at_10_primes": (
                (historical.get("budget_summary") or {}).get("10") or {}
            ).get("valuable_target_survival_rows"),
            "chronological_replay_minimum_gate_passed": replay.get("phase7_minimum_gate_passed") if replay else None,
            "latest_gpu_probe_summary": {
                "run_id": gpu.get("run_id"),
                "gpu_used": (gpu.get("training_and_sampling") or {}).get("gpu_used"),
                "valid_records": (gpu.get("cpu_proxy_scoring") or {}).get("valid_records"),
                "rejection_reasons": (gpu.get("cpu_proxy_scoring") or {}).get("rejection_reasons"),
            }
            if gpu
            else None,
            "baseline_leaderboard": baseline.get("leaderboard") if baseline else None,
        },
        "sair_sync_status": sair_sync_status,
        "packet_status": {
            "selected_rows": packet.get("selected_rows"),
            "candidate_count": packet.get("candidate_count"),
            "best_case_packet_points": packet.get("best_case_packet_points"),
            "expected_points_status": packet.get("expected_points_status"),
            "expected_points_basis": packet.get("expected_points_basis"),
            "possible_uncovered_pair_count": packet.get("selected_possible_uncovered_pair_count"),
            "possible_low_team_pair_count": packet.get("selected_possible_low_team_pair_count"),
            "construction_family_counts": (packet.get("selected_diversity") or {}).get("construction_family"),
        },
        "verification_status": {
            "reviewed_rows": triage.get("reviewed_rows"),
            "verified_exact_label_rows": triage.get("verified_rows"),
            "pending_exact_label_rows": triage.get("pending_exact_label_rows"),
            "known_submission_hash_rows": triage.get("known_submission_hash_rows"),
            "submission_grade_rows": triage.get("submission_grade_rows"),
            "exact_label_status_counts": exact_label_status_counts,
            "exact_r_status_counts": exact_r_status_counts,
            "exact_nfdisc_status_counts": exact_nfdisc_status_counts,
        },
        "adaptive_packet_status": {
            "max_usable_primes": adaptive.get("max_usable_primes"),
            "evaluated_rows": adaptive.get("evaluated_row_count"),
            "failed_rows": adaptive.get("failed_row_count"),
            "exact_label_missing_rows": adaptive.get("exact_label_missing_row_count"),
            "intended_target_survival_rows": adaptive.get("intended_target_survival_rows"),
            "intended_target_row_count": adaptive.get("intended_target_row_count"),
            "final_valuable_target_survival_rows": adaptive.get("final_valuable_target_survival_rows"),
            "budget_summary": adaptive.get("budget_summary"),
        },
        "candidate_status": {
            "selected_hashes": selected_hashes,
            "selected_short_hashes": [short_hash(item) for item in selected_hashes],
            "novel_candidate_hashes_against_synced_submission_history": novel_candidate_hashes,
            "novel_candidate_count_against_synced_submission_history": len(novel_candidate_hashes),
            "selected_rows": selected_rows,
        },
        "go_no_go": gate,
        "output_files": {
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
            "triage_rows_jsonl": str(output_dir / TRIAGE_ROWS_JSONL),
        },
    }
    return summary, triage_rows


def render_report(summary: dict[str, Any]) -> str:
    packet = summary["packet_status"]
    verification = summary["verification_status"]
    adaptive = summary["adaptive_packet_status"]
    gate = summary["go_no_go"]
    candidates = summary["candidate_status"]
    arch = summary["architecture_status"]
    sync = summary.get("sair_sync_status") or {}
    lines = [
        "# IGP24 Current Offline Go/No-Go Report",
        "",
        "This report is local/file-only. It does not call SAIR, run exact verifiers, train models, generate candidates, or submit.",
        "",
        "## Recommendation",
        "",
        f"- Live submission recommended now: `{gate['live_submission_recommended_now']}`",
        f"- Recommendation: `{gate['recommendation']}`",
        f"- Blockers: `{json.dumps(gate['blockers'], sort_keys=True)}`",
        f"- Warnings: `{json.dumps(gate['warnings'], sort_keys=True)}`",
        "",
        "## Packet",
        "",
        f"- Selected rows: `{packet.get('selected_rows')}`",
        f"- Candidate count considered: `{packet.get('candidate_count')}`",
        f"- Best-case packet points: `{packet.get('best_case_packet_points')}`",
        f"- Expected points status: `{packet.get('expected_points_status')}`",
        f"- Possible uncovered pairs: `{packet.get('possible_uncovered_pair_count')}`",
        f"- Possible low-team pairs: `{packet.get('possible_low_team_pair_count')}`",
        f"- Construction families: `{json.dumps(packet.get('construction_family_counts'), sort_keys=True)}`",
        "",
        "## Verification",
        "",
        f"- Reviewed rows: `{verification.get('reviewed_rows')}`",
        f"- Verified exact-label rows: `{verification.get('verified_exact_label_rows')}`",
        f"- Pending exact-label rows: `{verification.get('pending_exact_label_rows')}`",
        f"- Known-submission hash rows: `{verification.get('known_submission_hash_rows')}`",
        f"- Submission-grade rows: `{verification.get('submission_grade_rows')}`",
        f"- Exact r status counts: `{json.dumps(verification.get('exact_r_status_counts'), sort_keys=True)}`",
        f"- Exact nfdisc status counts: `{json.dumps(verification.get('exact_nfdisc_status_counts'), sort_keys=True)}`",
        "",
        "## Adaptive Evidence",
        "",
        f"- Max usable primes: `{adaptive.get('max_usable_primes')}`",
        f"- Evaluated rows: `{adaptive.get('evaluated_rows')}`",
        f"- Failed rows: `{adaptive.get('failed_rows')}`",
        f"- Intended target survival: `{adaptive.get('intended_target_survival_rows')}/{adaptive.get('intended_target_row_count')}`",
        f"- Valuable target survival rows: `{adaptive.get('final_valuable_target_survival_rows')}`",
        "",
        "## Architecture Calibration",
        "",
        f"- Full group index complete: `{arch.get('full_group_index_complete')}`",
        f"- Indexed group count: `{arch.get('indexed_group_count')}`",
        f"- Historical evaluated rows: `{arch.get('historical_evaluated_rows')}`",
        f"- Historical containment failures: `{arch.get('historical_indexed_containment_failures')}`",
        f"- Historical valuable false-positive rows at 10 primes: `{arch.get('historical_valuable_false_positive_rows_at_10_primes')}`",
        f"- Chronological replay minimum gate passed: `{arch.get('chronological_replay_minimum_gate_passed')}`",
        "",
        "## SAIR Sync",
        "",
        f"- Sync artifact provided: `{sync.get('provided')}`",
        f"- Sync status: `{sync.get('status')}`",
        f"- Created at: `{sync.get('created_at')}`",
        f"- Age hours: `{sync.get('age_hours')}`",
        f"- Full submission state complete: `{(sync.get('sync_status') or {}).get('full_submission_state_complete')}`",
        f"- Pending rows: `{(sync.get('submissions') or {}).get('pending_rows')}`",
        f"- Scoreable rows: `{(sync.get('submissions') or {}).get('scoreable_rows')}`",
        "",
        "## Candidates",
        "",
        f"- Novel candidate count against synced submission history: `{candidates.get('novel_candidate_count_against_synced_submission_history')}`",
        f"- Selected short hashes: `{json.dumps(candidates.get('selected_short_hashes'), sort_keys=True)}`",
        "",
        "| hash | label | r | progress | teams | nfdisc status | known submitted | class | submission-grade |",
        "| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in candidates.get("selected_rows") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('short_hash')}`",
                    str(row.get("verified_group_label") or ""),
                    str(row.get("computed_r") or ""),
                    str(row.get("sair_progress_state") or ""),
                    str(row.get("sair_progress_team_count") or ""),
                    str(row.get("exact_nfdisc_status") or ""),
                    str(row.get("known_submission_hash_match")),
                    str(row.get("score_aware_classification") or ""),
                    str(row.get("submission_grade_candidate")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only. Exact labels, fresh progress, known-hash checks, and score-aware gates must all clear before any live packet.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output_dir: Path, summary: dict[str, Any], triage_rows: list[dict[str, Any]]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    triage_rows_path = output_dir / TRIAGE_ROWS_JSONL
    write_json(summary_path, summary)
    report_path.write_text(render_report(summary), encoding="utf-8")
    write_jsonl(triage_rows_path, triage_rows)
    return {
        "summary_json": summary_path,
        "report_md": report_path,
        "triage_rows_jsonl": triage_rows_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet_summary_json", type=Path, required=True)
    parser.add_argument("--triage_summary_json", type=Path, required=True)
    parser.add_argument("--triage_rows_jsonl", type=Path)
    parser.add_argument("--adaptive_summary_json", type=Path, required=True)
    parser.add_argument("--index_summary_json", type=Path, required=True)
    parser.add_argument("--historical_summary_json", type=Path, required=True)
    parser.add_argument("--baseline_summary_json", type=Path)
    parser.add_argument("--replay_summary_json", type=Path)
    parser.add_argument("--gpu_summary_json", type=Path)
    parser.add_argument("--sair_sync_summary_json", type=Path)
    parser.add_argument("--max_sync_age_hours", type=float, default=6.0)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_current_offline_report.py", *argv]
    summary, triage_rows = build_summary(
        packet_summary_path=args.packet_summary_json.resolve(),
        triage_summary_path=args.triage_summary_json.resolve(),
        triage_rows_path=args.triage_rows_jsonl.resolve() if args.triage_rows_jsonl else None,
        adaptive_summary_path=args.adaptive_summary_json.resolve(),
        index_summary_path=args.index_summary_json.resolve(),
        historical_summary_path=args.historical_summary_json.resolve(),
        baseline_summary_path=args.baseline_summary_json.resolve() if args.baseline_summary_json else None,
        replay_summary_path=args.replay_summary_json.resolve() if args.replay_summary_json else None,
        gpu_summary_path=args.gpu_summary_json.resolve() if args.gpu_summary_json else None,
        sair_sync_summary_path=args.sair_sync_summary_json.resolve() if args.sair_sync_summary_json else None,
        max_sync_age_hours=float(args.max_sync_age_hours),
        output_dir=args.output_dir.resolve(),
        command=command,
    )
    paths = write_outputs(args.output_dir.resolve(), summary, triage_rows)
    print(f"live_submission_recommended_now\t{summary['go_no_go']['live_submission_recommended_now']}")
    print(f"recommendation\t{summary['go_no_go']['recommendation']}")
    print(f"blocker_count\t{len(summary['go_no_go']['blockers'])}")
    print(f"novel_candidate_count\t{summary['candidate_status']['novel_candidate_count_against_synced_submission_history']}")
    print(f"submission_grade_rows\t{summary['verification_status']['submission_grade_rows']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
