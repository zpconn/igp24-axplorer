#!/usr/bin/env python3
"""Broad historical group-compatibility backtest for scoreable SAIR rows.

This joins synced SAIR scoreable rows to any local modular-factorization
evidence found by canonical hash, then evaluates indexed target survival
against the current partial or complete group-cycle index.

It is read-only: no SAIR calls, no network, no GAP/Magma/PARI execution, and no
candidate generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.group_compatibility import (  # noqa: E402
    GroupCycleIndex,
    candidate_compatibility,
    observed_cycle_evidence,
    read_jsonl,
    write_json,
    write_jsonl,
)

SUMMARY_JSON = "broad_historical_group_backtest_summary.json"
ROWS_JSONL = "broad_historical_group_backtest_rows.jsonl"
SKIPPED_JSONL = "broad_historical_group_backtest_skipped.jsonl"
REPORT_MD = "broad_historical_group_backtest_report.md"

DEFAULT_SCOREABLE_ROWS = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_scoreable_rows.jsonl"
)
DEFAULT_PROGRESS_ROWS = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_label_progress.jsonl"
)
DEFAULT_INDEX = (
    REPO_ROOT
    / "data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_plus_historical_local_gap_v2/degree24_group_cycle_index.sqlite"
)

SKIP_FILE_NAMES = {
    "sair_label_progress.jsonl",
    "sair_submission_rows.jsonl",
    "sair_scoreable_rows.jsonl",
    "sair_pending_rows.jsonl",
    "sair_failed_rows.jsonl",
    "sair_unmatched_rows.jsonl",
}


def repo_rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def nested_dict(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key)
    return value if isinstance(value, dict) else {}


def candidate_payload(row: dict[str, Any]) -> dict[str, Any]:
    candidate = nested_dict(row, "candidate")
    return candidate if candidate else row


def canonical_hash(row: dict[str, Any]) -> str | None:
    candidate = candidate_payload(row)
    for source in (row, candidate, nested_dict(row, "features")):
        value = source.get("canonical_hash") if isinstance(source, dict) else None
        if value:
            return str(value)
    return None


def coefficient_patterns(row: dict[str, Any]) -> list[dict[str, Any]]:
    return observed_cycle_evidence(row)


def row_features(row: dict[str, Any]) -> dict[str, Any]:
    candidate = candidate_payload(row)
    features = nested_dict(row, "features") or nested_dict(candidate, "features")
    metadata = nested_dict(candidate, "generation_metadata")
    return {
        "construction_family": features.get("construction_family") or metadata.get("construction_family") or row.get("construction_family"),
        "template_family_id": features.get("template_family_id") or metadata.get("template_family_id") or row.get("template_family_id"),
        "perturbation_mode": features.get("perturbation_mode") or metadata.get("perturbation_mode") or row.get("perturbation_mode"),
        "basin_fingerprint": features.get("basin_fingerprint") or metadata.get("basin_fingerprint") or row.get("basin_fingerprint"),
        "mod_p_pattern_signature": candidate.get("mod_p_pattern_signature") or row.get("mod_p_pattern_signature"),
    }


def iter_evidence_files(paths: Iterable[Path], roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.exists() and path.is_file():
            files.append(path)
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            files.append(root)
            continue
        for path in root.rglob("*.jsonl"):
            if path.name in SKIP_FILE_NAMES:
                continue
            files.append(path)
    return sorted(set(files))


def build_evidence_index(files: list[Path], *, max_file_bytes: int = 8_000_000) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    stats = {
        "files_seen": len(files),
        "files_scanned": 0,
        "files_skipped_too_large": 0,
        "rows_seen": 0,
        "rows_with_patterns": 0,
        "hashes_with_evidence": 0,
    }
    for path in files:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue
        if max_file_bytes > 0 and size > max_file_bytes:
            stats["files_skipped_too_large"] += 1
            continue
        stats["files_scanned"] += 1
        try:
            rows = read_jsonl(path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        for row in rows:
            stats["rows_seen"] += 1
            hash_value = canonical_hash(row)
            if not hash_value:
                continue
            patterns = coefficient_patterns(row)
            if not patterns:
                continue
            stats["rows_with_patterns"] += 1
            current = evidence.get(hash_value)
            if current is not None and len(coefficient_patterns(current["row"])) >= len(patterns):
                continue
            evidence[hash_value] = {"row": row, "path": path, "pattern_count": len(patterns)}
    stats["hashes_with_evidence"] = len(evidence)
    return evidence, stats


def scoreable_pair(row: dict[str, Any]) -> str | None:
    pair = row.get("pair_key")
    if pair:
        return str(pair)
    label = row.get("label")
    r_value = row.get("r")
    if label and r_value is not None:
        return f"{label}|r={int(r_value)}"
    return None


def scoreable_to_backtest_row(scoreable: dict[str, Any], evidence: dict[str, Any], *, max_patterns: int | None = None) -> dict[str, Any]:
    evidence_row = dict(evidence["row"])
    patterns = coefficient_patterns(evidence_row)
    if max_patterns is not None:
        patterns = patterns[: max(0, int(max_patterns))]
    features = row_features(evidence_row)
    return {
        **evidence_row,
        "label": scoreable.get("label"),
        "verified_group_label": scoreable.get("label"),
        "t": scoreable.get("t"),
        "r": scoreable.get("r"),
        "pair_key": scoreable_pair(scoreable),
        "canonical_hash": scoreable.get("canonical_hash") or canonical_hash(evidence_row),
        "mod_p_factorization_degree_patterns": [
            {"prime": item.get("prime"), "degrees": item.get("degrees")} for item in patterns
        ],
        "construction_family": features.get("construction_family"),
        "template_family_id": features.get("template_family_id"),
        "perturbation_mode": features.get("perturbation_mode"),
        "basin_fingerprint": features.get("basin_fingerprint"),
        "source": {
            "scoreable_submission_id": scoreable.get("submission_id"),
            "submitted_line_number": scoreable.get("submitted_line_number"),
            "evidence_path": repo_rel(evidence["path"]),
            "evidence_pattern_count": evidence["pattern_count"],
        },
    }


def compatibility_at_budgets(
    base_row: dict[str, Any],
    index: GroupCycleIndex,
    progress_rows: list[dict[str, Any]],
    budgets: list[int],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    patterns = base_row.get("mod_p_factorization_degree_patterns") or []
    for budget in budgets:
        row = {**base_row, "mod_p_factorization_degree_patterns": patterns[: max(0, int(budget))]}
        compat = candidate_compatibility(row, index, progress_rows=progress_rows)
        out[str(budget)] = {
            "status": compat.get("status"),
            "indexed_target_survivor_count": compat.get("indexed_target_survivor_count"),
            "valuable_target_count": len(compat.get("valuable_targets_not_ruled_out") or []),
            "valuable_targets_not_ruled_out": compat.get("valuable_targets_not_ruled_out") or [],
            "true_label_indexed": str(base_row.get("label")) in index.all_labels(),
            "true_label_survived": str(base_row.get("label")) in set(compat.get("indexed_target_labels_not_ruled_out") or []),
        }
    return out


def run_backtest(
    *,
    scoreable_rows: list[dict[str, Any]],
    evidence_index: dict[str, dict[str, Any]],
    group_index: GroupCycleIndex,
    progress_rows: list[dict[str, Any]],
    budgets: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    all_indexed_labels = group_index.all_labels()
    for scoreable in scoreable_rows:
        hash_value = str(scoreable.get("canonical_hash") or "")
        evidence = evidence_index.get(hash_value)
        if evidence is None:
            skipped.append(
                {
                    "canonical_hash": hash_value,
                    "label": scoreable.get("label"),
                    "pair_key": scoreable_pair(scoreable),
                    "reason": "missing_local_modular_evidence",
                }
            )
            continue
        row = scoreable_to_backtest_row(scoreable, evidence)
        compat = candidate_compatibility(row, group_index, progress_rows=progress_rows)
        true_label = str(row.get("label") or "")
        row_result = {
            "schema_version": 1,
            "record_type": "igp24_broad_historical_group_backtest_row",
            "canonical_hash": row.get("canonical_hash"),
            "short_hash": str(row.get("canonical_hash") or "")[:12],
            "label": true_label,
            "r": row.get("r"),
            "pair_key": row.get("pair_key"),
            "true_label_indexed": true_label in all_indexed_labels,
            "true_label_survived": true_label in set(compat.get("indexed_target_labels_not_ruled_out") or []),
            "indexed_target_survivor_count": compat.get("indexed_target_survivor_count"),
            "valuable_targets_not_ruled_out": compat.get("valuable_targets_not_ruled_out") or [],
            "valuable_target_count": len(compat.get("valuable_targets_not_ruled_out") or []),
            "crowded_only": compat.get("crowded_only"),
            "status": compat.get("status"),
            "index_scope": compat.get("index_scope"),
            "global_index_complete": compat.get("global_index_complete"),
            "unindexed_label_mass_unknown": compat.get("unindexed_label_mass_unknown"),
            "evidence_pattern_count": len(row.get("mod_p_factorization_degree_patterns") or []),
            "construction_family": row.get("construction_family"),
            "template_family_id": row.get("template_family_id"),
            "perturbation_mode": row.get("perturbation_mode"),
            "budget_results": compatibility_at_budgets(row, group_index, progress_rows, budgets),
            "source": row.get("source"),
        }
        rows.append(row_result)
    summary = summarize(scoreable_rows=scoreable_rows, rows=rows, skipped=skipped, group_index=group_index, budgets=budgets)
    return rows, skipped, summary


def summarize(
    *,
    scoreable_rows: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    group_index: GroupCycleIndex,
    budgets: list[int],
) -> dict[str, Any]:
    labels = Counter(str(row.get("label")) for row in scoreable_rows)
    pairs = Counter(str(scoreable_pair(row)) for row in scoreable_rows)
    evaluated_labels = Counter(str(row.get("label")) for row in rows)
    evaluated_pairs = Counter(str(row.get("pair_key")) for row in rows)
    skip_counts = Counter(str(row.get("reason")) for row in skipped)
    by_label: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("label"))].append(row)
    for label, label_rows in grouped.items():
        indexed = [row for row in label_rows if row.get("true_label_indexed")]
        by_label[label] = {
            "row_count": len(label_rows),
            "pair_count": len({row.get("pair_key") for row in label_rows}),
            "true_label_indexed": bool(indexed),
            "indexed_containment_failures": sum(1 for row in indexed if not row.get("true_label_survived")),
            "valuable_false_positive_rows": sum(1 for row in label_rows if row.get("valuable_target_count", 0) > 0),
            "median_indexed_target_survivor_count": sorted(int(row.get("indexed_target_survivor_count") or 0) for row in label_rows)[len(label_rows) // 2],
        }
    budget_summary: dict[str, dict[str, Any]] = {}
    for budget in budgets:
        key = str(budget)
        values = [row["budget_results"][key] for row in rows if key in row.get("budget_results", {})]
        budget_summary[key] = {
            "evaluated_rows": len(values),
            "valuable_target_survival_rows": sum(1 for value in values if int(value.get("valuable_target_count") or 0) > 0),
            "indexed_containment_failures": sum(
                1 for value in values if value.get("true_label_indexed") and not value.get("true_label_survived")
            ),
            "median_indexed_target_survivor_count": (
                sorted(int(value.get("indexed_target_survivor_count") or 0) for value in values)[len(values) // 2]
                if values
                else None
            ),
        }
    indexed_rows = [row for row in rows if row.get("true_label_indexed")]
    return {
        "schema_version": 1,
        "record_type": "igp24_broad_historical_group_backtest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_broad_historical_group_backtest.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety": {
            "calls_sair": False,
            "uses_network": False,
            "runs_gap_magma_pari": False,
            "generates_candidates": False,
            "submits": False,
        },
        "index_metadata": group_index.scope_metadata(),
        "scoreable_row_count": len(scoreable_rows),
        "observed_label_count": len(labels),
        "observed_pair_count": len(pairs),
        "observed_label_counts": dict(sorted(labels.items())),
        "observed_pair_counts": dict(sorted(pairs.items())),
        "evaluated_row_count": len(rows),
        "evaluated_label_count": len(evaluated_labels),
        "evaluated_pair_count": len(evaluated_pairs),
        "skipped_row_count": len(skipped),
        "skip_reason_counts": dict(sorted(skip_counts.items())),
        "true_label_indexed_row_count": len(indexed_rows),
        "true_label_outside_index_row_count": len(rows) - len(indexed_rows),
        "indexed_true_label_containment_failures": sum(1 for row in indexed_rows if not row.get("true_label_survived")),
        "valuable_target_false_positive_rows": sum(1 for row in rows if row.get("valuable_target_count", 0) > 0),
        "budget_summary": budget_summary,
        "by_actual_label": by_label,
        "budgets": budgets,
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Broad Historical Group Backtest",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Scoreable rows: `{summary['scoreable_row_count']}`",
        f"- Observed labels/pairs: `{summary['observed_label_count']}` / `{summary['observed_pair_count']}`",
        f"- Evaluated rows: `{summary['evaluated_row_count']}`",
        f"- Skipped rows: `{summary['skipped_row_count']}`",
        f"- True-label outside-index rows: `{summary['true_label_outside_index_row_count']}`",
        f"- Indexed containment failures: `{summary['indexed_true_label_containment_failures']}`",
        f"- Valuable-target false-positive rows: `{summary['valuable_target_false_positive_rows']}`",
        f"- Index metadata: `{summary['index_metadata']}`",
        f"- Safety: `{summary['safety']}`",
        "",
        "Compatibility is necessary target-exclusion evidence only. With a partial index, outside-index labels remain unknown mass.",
        "",
        "## Prime Budget Summary",
        "",
        "| budget | rows | valuable survival rows | containment failures | median indexed survivors |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for budget, row in summary["budget_summary"].items():
        lines.append(
            f"| {budget} | {row['evaluated_rows']} | {row['valuable_target_survival_rows']} | "
            f"{row['indexed_containment_failures']} | {row['median_indexed_target_survivor_count']} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], rows: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / ROWS_JSONL, rows)
    write_jsonl(output_dir / SKIPPED_JSONL, skipped)
    (output_dir / REPORT_MD).write_text(render_report(summary), encoding="utf-8")


def parse_budgets(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scoreable_rows_jsonl", type=Path, default=DEFAULT_SCOREABLE_ROWS)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--progress_jsonl", type=Path, default=DEFAULT_PROGRESS_ROWS)
    parser.add_argument("--evidence_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--evidence_root", type=Path, action="append", default=[])
    parser.add_argument("--max_evidence_file_bytes", type=int, default=8_000_000)
    parser.add_argument("--budgets", default="5,10,20,40,80")
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    scoreable_rows = read_jsonl(args.scoreable_rows_jsonl)
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl and args.progress_jsonl.exists() else []
    files = iter_evidence_files(args.evidence_jsonl, args.evidence_root)
    evidence_index, evidence_stats = build_evidence_index(files, max_file_bytes=int(args.max_evidence_file_bytes))
    group_index = GroupCycleIndex(args.index)
    rows, skipped, summary = run_backtest(
        scoreable_rows=scoreable_rows,
        evidence_index=evidence_index,
        group_index=group_index,
        progress_rows=progress_rows,
        budgets=parse_budgets(args.budgets),
    )
    summary["inputs"] = {
        "scoreable_rows_jsonl": repo_rel(args.scoreable_rows_jsonl),
        "index": repo_rel(args.index),
        "progress_jsonl": repo_rel(args.progress_jsonl),
        "evidence_jsonl": [repo_rel(path) for path in args.evidence_jsonl],
        "evidence_root": [repo_rel(path) for path in args.evidence_root],
        "max_evidence_file_bytes": int(args.max_evidence_file_bytes),
    }
    summary["evidence_index_stats"] = evidence_stats
    summary["output_files"] = {
        "summary_json": str(args.output_dir / SUMMARY_JSON),
        "rows_jsonl": str(args.output_dir / ROWS_JSONL),
        "skipped_jsonl": str(args.output_dir / SKIPPED_JSONL),
        "report_md": str(args.output_dir / REPORT_MD),
    }
    write_outputs(args.output_dir, summary=summary, rows=rows, skipped=skipped)
    print(f"scoreable_row_count\t{summary['scoreable_row_count']}")
    print(f"evaluated_row_count\t{summary['evaluated_row_count']}")
    print(f"skipped_row_count\t{summary['skipped_row_count']}")
    print(f"observed_pair_count\t{summary['observed_pair_count']}")
    print(f"evaluated_pair_count\t{summary['evaluated_pair_count']}")
    print(f"valuable_target_false_positive_rows\t{summary['valuable_target_false_positive_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
