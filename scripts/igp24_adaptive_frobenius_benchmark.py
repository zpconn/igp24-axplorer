#!/usr/bin/env python3
"""Benchmark adaptive Frobenius evidence on historical IGP24 rows.

This script recomputes modular factorization evidence from polynomial
coefficients. It is read-only: no SAIR calls, no network, no exact Galois
verification, no candidate generation, and no submission.
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
from src.igp24.adaptive_frobenius import collect_frobenius_observations, compatibility_for_patterns  # noqa: E402
from src.igp24.group_compatibility import GroupCycleIndex, read_jsonl, write_json, write_jsonl  # noqa: E402
from src.igp24.polynomial import _timeout  # noqa: E402

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

SUMMARY_JSON = "adaptive_frobenius_benchmark_summary.json"
ROWS_JSONL = "adaptive_frobenius_benchmark_rows.jsonl"
FAILED_JSONL = "adaptive_frobenius_benchmark_failed.jsonl"
REPORT_MD = "adaptive_frobenius_benchmark_report.md"


def repo_rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_budgets(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def pattern_prefix(collected: dict[str, Any], budget: int) -> list[dict[str, Any]]:
    return list(collected.get("mod_p_factorization_degree_patterns") or [])[: int(budget)]


def evaluate_budgets(
    record: dict[str, Any],
    collected: dict[str, Any],
    index: GroupCycleIndex,
    progress_rows: list[dict[str, Any]],
    budgets: list[int],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for budget in budgets:
        patterns = pattern_prefix(collected, budget)
        compat = compatibility_for_patterns(record, patterns, index, progress_rows) if patterns else collected["final_compatibility"]
        out[str(budget)] = {
            "usable_prime_count": len(patterns),
            "status": compat.get("status"),
            "indexed_target_survivor_count": compat.get("indexed_target_survivor_count"),
            "valuable_target_count": len(compat.get("valuable_targets_not_ruled_out") or []),
            "valuable_targets_not_ruled_out": compat.get("valuable_targets_not_ruled_out") or [],
            "true_label_indexed": str(record.get("label")) in index.all_labels(),
            "true_label_survived": str(record.get("label")) in set(compat.get("indexed_target_labels_not_ruled_out") or []),
        }
    return out


def run_rows(
    rows: list[dict[str, Any]],
    *,
    index: GroupCycleIndex,
    progress_rows: list[dict[str, Any]],
    budgets: list[int],
    max_usable_primes: int,
    max_rows: int | None = None,
    row_timeout_seconds: float | None = None,
    progress_interval: int = 25,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evaluated: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    selected_rows = rows[: int(max_rows)] if max_rows else rows
    indexed_labels = index.all_labels()
    for row_index, row in enumerate(selected_rows, start=1):
        try:
            with _timeout(row_timeout_seconds):
                collected = collect_frobenius_observations(
                    row,
                    index,
                    progress_rows=progress_rows,
                    max_usable_primes=max_usable_primes,
                )
        except Exception as exc:
            failed.append(
                {
                    "row_index": row_index,
                    "canonical_hash": row.get("canonical_hash"),
                    "label": row.get("label"),
                    "pair_key": row.get("pair_key"),
                    "reason": f"{type(exc).__name__}:{exc}",
                }
            )
            continue
        final = collected["final_compatibility"]
        budget_results = evaluate_budgets(row, collected, index, progress_rows, budgets)
        evaluated.append(
            {
                "schema_version": 1,
                "record_type": "igp24_adaptive_frobenius_benchmark_row",
                "row_index": row_index,
                "canonical_hash": row.get("canonical_hash"),
                "short_hash": str(row.get("canonical_hash") or "")[:12],
                "label": row.get("label"),
                "r": row.get("r"),
                "pair_key": row.get("pair_key"),
                "true_label_indexed": str(row.get("label")) in indexed_labels,
                "true_label_survived": str(row.get("label")) in set(final.get("indexed_target_labels_not_ruled_out") or []),
                "usable_prime_count": collected.get("usable_prime_count"),
                "primes_examined": collected.get("primes_examined"),
                "skipped_ramified_primes": collected.get("skipped_ramified_primes"),
                "mod_p_factorization_degree_patterns": collected.get("mod_p_factorization_degree_patterns") or [],
                "observations": collected.get("observations") or [],
                "final_indexed_target_survivor_count": final.get("indexed_target_survivor_count"),
                "final_valuable_target_count": len(final.get("valuable_targets_not_ruled_out") or []),
                "final_valuable_targets_not_ruled_out": final.get("valuable_targets_not_ruled_out") or [],
                "budget_results": budget_results,
                "discriminant_source": collected.get("discriminant_source"),
                "runtime_seconds": collected.get("runtime_seconds"),
            }
        )
        if progress_interval > 0 and row_index % int(progress_interval) == 0:
            print(
                f"progress\t{row_index}/{len(selected_rows)}\tevaluated={len(evaluated)}\tfailed={len(failed)}",
                flush=True,
            )
    return evaluated, failed


def summarize(
    *,
    input_rows: list[dict[str, Any]],
    evaluated: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    index: GroupCycleIndex,
    budgets: list[int],
    max_usable_primes: int,
    output_dir: Path,
) -> dict[str, Any]:
    label_counts = Counter(str(row.get("label")) for row in input_rows)
    pair_counts = Counter(str(row.get("pair_key")) for row in input_rows)
    evaluated_label_counts = Counter(str(row.get("label")) for row in evaluated)
    discriminant_source_counts = Counter(str(row.get("discriminant_source")) for row in evaluated)
    indexed_rows = [row for row in evaluated if row.get("true_label_indexed")]
    by_label: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evaluated:
        grouped[str(row.get("label"))].append(row)
    for label, rows in grouped.items():
        by_label[label] = {
            "row_count": len(rows),
            "true_label_indexed_rows": sum(1 for row in rows if row.get("true_label_indexed")),
            "indexed_containment_failures": sum(1 for row in rows if row.get("true_label_indexed") and not row.get("true_label_survived")),
            "final_valuable_target_survival_rows": sum(1 for row in rows if int(row.get("final_valuable_target_count") or 0) > 0),
            "median_final_indexed_target_survivor_count": sorted(int(row.get("final_indexed_target_survivor_count") or 0) for row in rows)[len(rows) // 2],
        }
    budget_summary: dict[str, dict[str, Any]] = {}
    for budget in budgets:
        key = str(budget)
        values = [row["budget_results"][key] for row in evaluated]
        budget_summary[key] = {
            "evaluated_rows": len(values),
            "rows_with_budget_reached": sum(1 for value in values if int(value.get("usable_prime_count") or 0) >= int(budget)),
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
    return {
        "schema_version": 1,
        "record_type": "igp24_adaptive_frobenius_benchmark",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_adaptive_frobenius_benchmark.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety": {
            "calls_sair": False,
            "uses_network": False,
            "runs_gap_magma_pari": False,
            "generates_candidates": False,
            "submits": False,
        },
        "index_metadata": index.scope_metadata(),
        "input_row_count": len(input_rows),
        "evaluated_row_count": len(evaluated),
        "failed_row_count": len(failed),
        "observed_label_count": len(label_counts),
        "observed_pair_count": len(pair_counts),
        "evaluated_label_count": len(evaluated_label_counts),
        "discriminant_source_counts": dict(sorted(discriminant_source_counts.items())),
        "true_label_indexed_row_count": len(indexed_rows),
        "true_label_outside_index_row_count": len(evaluated) - len(indexed_rows),
        "indexed_true_label_containment_failures": sum(1 for row in indexed_rows if not row.get("true_label_survived")),
        "final_valuable_target_survival_rows": sum(1 for row in evaluated if int(row.get("final_valuable_target_count") or 0) > 0),
        "max_usable_primes": int(max_usable_primes),
        "budgets": budgets,
        "budget_summary": budget_summary,
        "by_actual_label": by_label,
        "output_files": {
            "summary_json": str(output_dir / SUMMARY_JSON),
            "rows_jsonl": str(output_dir / ROWS_JSONL),
            "failed_jsonl": str(output_dir / FAILED_JSONL),
            "report_md": str(output_dir / REPORT_MD),
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Adaptive Frobenius Benchmark",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Input rows: `{summary['input_row_count']}`",
        f"- Evaluated rows: `{summary['evaluated_row_count']}`",
        f"- Failed rows: `{summary['failed_row_count']}`",
        f"- True-label outside-index rows: `{summary['true_label_outside_index_row_count']}`",
        f"- Indexed containment failures: `{summary['indexed_true_label_containment_failures']}`",
        f"- Final valuable-target survival rows: `{summary['final_valuable_target_survival_rows']}`",
        f"- Discriminant sources: `{summary['discriminant_source_counts']}`",
        f"- Max usable primes: `{summary['max_usable_primes']}`",
        f"- Index metadata: `{summary['index_metadata']}`",
        "",
        "Evidence uses only primes that do not divide the polynomial discriminant. Compatibility remains necessary target-exclusion evidence only.",
        "",
        "## Budget Summary",
        "",
        "| budget | rows | reached budget | valuable survival rows | containment failures | median indexed survivors |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for budget, row in summary["budget_summary"].items():
        lines.append(
            f"| {budget} | {row['evaluated_rows']} | {row['rows_with_budget_reached']} | "
            f"{row['valuable_target_survival_rows']} | {row['indexed_containment_failures']} | "
            f"{row['median_indexed_target_survivor_count']} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], rows: list[dict[str, Any]], failed: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / ROWS_JSONL, rows)
    write_jsonl(output_dir / FAILED_JSONL, failed)
    (output_dir / REPORT_MD).write_text(render_report(summary), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scoreable_rows_jsonl", type=Path, default=DEFAULT_SCOREABLE_ROWS)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--progress_jsonl", type=Path, default=DEFAULT_PROGRESS_ROWS)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--budgets", default="5,10,20,40,80")
    parser.add_argument("--max_usable_primes", type=int, default=80)
    parser.add_argument("--max_rows", type=int)
    parser.add_argument("--row_timeout_seconds", type=float, default=20.0)
    parser.add_argument("--progress_interval", type=int, default=25)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = read_jsonl(args.scoreable_rows_jsonl)
    if args.max_rows:
        rows = rows[: int(args.max_rows)]
    progress_rows = read_jsonl(args.progress_jsonl) if args.progress_jsonl and args.progress_jsonl.exists() else []
    index = GroupCycleIndex(args.index)
    budgets = parse_budgets(args.budgets)
    evaluated, failed = run_rows(
        rows,
        index=index,
        progress_rows=progress_rows,
        budgets=budgets,
        max_usable_primes=int(args.max_usable_primes),
        row_timeout_seconds=args.row_timeout_seconds,
        progress_interval=int(args.progress_interval),
    )
    summary = summarize(
        input_rows=rows,
        evaluated=evaluated,
        failed=failed,
        index=index,
        budgets=budgets,
        max_usable_primes=int(args.max_usable_primes),
        output_dir=args.output_dir,
    )
    summary["inputs"] = {
        "scoreable_rows_jsonl": repo_rel(args.scoreable_rows_jsonl),
        "index": repo_rel(args.index),
        "progress_jsonl": repo_rel(args.progress_jsonl),
        "max_rows": args.max_rows,
        "row_timeout_seconds": args.row_timeout_seconds,
        "progress_interval": int(args.progress_interval),
    }
    write_outputs(args.output_dir, summary=summary, rows=evaluated, failed=failed)
    print(f"input_row_count\t{summary['input_row_count']}")
    print(f"evaluated_row_count\t{summary['evaluated_row_count']}")
    print(f"failed_row_count\t{summary['failed_row_count']}")
    print(f"final_valuable_target_survival_rows\t{summary['final_valuable_target_survival_rows']}")
    print(f"indexed_true_label_containment_failures\t{summary['indexed_true_label_containment_failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
