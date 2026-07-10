#!/usr/bin/env python3
"""Run the exact GAP -> group-index -> readiness workflow for IGP24.

This orchestration helper consumes a GAP export manifest from
``scripts/igp24_build_group_cycle_index.py --write_gap_program_dir``. It runs
each GAP program when GAP is available, or reuses already captured GAP JSON
outputs. The resulting rows are imported into the SQLite group-cycle index and
the group-index readiness gate is rerun with the imported index.

If GAP is missing and no captured outputs are available, the script writes a
blocked report and does not fabricate any group data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_build_group_cycle_index import (  # noqa: E402
    GAP_EXPORT_MANIFEST,
    IMPORT_SUMMARY_JSON,
    gap_command,
    import_rows_into_index,
    load_import_rows,
)
from scripts.igp24_group_index_readiness_gate import (  # noqa: E402
    DEFAULT_SCORE_PLAN,
    build_readiness,
    write_outputs as write_readiness_outputs,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.group_compatibility import GroupCycleIndex, write_json, write_jsonl  # noqa: E402


WORKFLOW_SUMMARY_JSON = "gap_group_index_workflow_summary.json"
WORKFLOW_REPORT_MD = "gap_group_index_workflow_report.md"
COMBINED_ROWS_JSONL = "gap_group_cycle_rows_combined.jsonl"
GAP_OUTPUT_DIR = "gap_outputs"

SAFETY_NOTE = (
    "Exact GAP group-index workflow. It runs GAP only when available, reuses "
    "captured GAP JSON outputs when present, calls no SAIR/network APIs, "
    "does not generate candidates, and does not submit anything."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(value: str, *, manifest_path: Path) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        return raw
    candidates = [REPO_ROOT / raw, manifest_path.parent / raw, raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return REPO_ROOT / raw


def gap_output_path(output_dir: Path, program_path: Path) -> Path:
    return output_dir / GAP_OUTPUT_DIR / f"{program_path.stem}.json"


def write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# IGP24 GAP Group-Index Workflow",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Status: `{summary['status']}`",
        f"- GAP path: `{summary['gap_path']}`",
        f"- GAP library path: `{summary.get('gap_library_path')}`",
        f"- Manifest: `{summary['manifest_path']}`",
        f"- Programs: `{summary['program_count']}`",
        f"- Programs loaded from captured output: `{summary['program_status_counts'].get('loaded_existing_output', 0)}`",
        f"- Programs run with GAP: `{summary['program_status_counts'].get('ran_gap', 0)}`",
        f"- Programs blocked: `{summary['program_status_counts'].get('blocked_missing_gap_output', 0)}`",
        f"- Programs failed: `{summary['program_status_counts'].get('failed_gap_output', 0)}`",
        f"- Rows available: `{summary['rows_available']}`",
        f"- Rows imported: `{summary.get('rows_imported')}`",
        f"- Group count: `{summary.get('group_count')}`",
        f"- Readiness output: `{summary.get('readiness_output_dir')}`",
        f"- Readiness blockers: `{summary.get('readiness_blocking_reasons')}`",
        f"- Structurally eligible routes: `{summary.get('structurally_eligible_route_count')}`",
        f"- Generation-ready routes: `{summary.get('generation_ready_route_count')}`",
        f"- Ready for structural route review: `{summary.get('ready_for_structural_route_review')}`",
        f"- Ready for group-directed generation: `{summary.get('ready_for_group_directed_generation')}`",
        f"- No approximation written: `{summary['no_approximation_written']}`",
        f"- Safety: {summary['safety_note']}",
        "",
    ]
    if summary.get("missing_output_files"):
        lines.extend(["## Missing GAP Outputs", ""])
        for path in summary["missing_output_files"][:100]:
            lines.append(f"- `{path}`")
        lines.append("")
    if summary.get("failed_output_files"):
        lines.extend(["## Failed GAP Outputs", ""])
        for row in summary["failed_output_files"][:100]:
            capture = row.get("failed_capture_path") or row.get("output_path")
            lines.append(f"- `{capture}`: {row.get('error')}")
        lines.append("")
    if summary.get("program_results"):
        lines.extend(
            [
                "## Program Results",
                "",
                "| program | status | rows | output |",
                "| --- | --- | ---: | --- |",
            ]
        )
        for row in summary["program_results"]:
            lines.append(
                f"| `{row['program_path']}` | `{row['status']}` | {row.get('row_count', 0)} | `{row.get('output_path')}` |"
            )
        lines.append("")
    (output_dir / WORKFLOW_REPORT_MD).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_summary(output_dir: Path, summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / WORKFLOW_SUMMARY_JSON, summary)
    write_report(output_dir, summary)


def run_gap_program(
    *,
    gap_path: str,
    gap_library_path: Path | None,
    program_path: Path,
    output_path: Path,
    timeout: int,
) -> list[dict[str, Any]]:
    result = subprocess.run(
        gap_command(gap_path, program_path, library_path=gap_library_path),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"GAP failed for {program_path} with code {result.returncode}: {result.stderr[-2000:]}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.stdout, encoding="utf-8")
    return load_import_rows(output_path)


def load_or_run_programs(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    output_dir: Path,
    gap_path: str | None,
    gap_library_path: Path | None,
    timeout: int,
    reuse_existing_outputs: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    program_results: list[dict[str, Any]] = []
    missing_outputs: list[str] = []
    failed_outputs: list[dict[str, Any]] = []
    for program in manifest.get("programs") or []:
        program_path = resolve_path(str(program["path"]), manifest_path=manifest_path)
        output_path = gap_output_path(output_dir, program_path)
        error: str | None = None
        try:
            if reuse_existing_outputs and output_path.exists():
                program_rows = load_import_rows(output_path)
                status = "loaded_existing_output"
            elif gap_path:
                program_rows = run_gap_program(
                    gap_path=gap_path,
                    gap_library_path=gap_library_path,
                    program_path=program_path,
                    output_path=output_path,
                    timeout=timeout,
                )
                status = "ran_gap"
            else:
                program_rows = []
                status = "blocked_missing_gap_output"
                missing_outputs.append(str(output_path))
        except Exception as exc:  # noqa: BLE001 - record failed chunk and stop importing.
            program_rows = []
            status = "failed_gap_output"
            error = f"{type(exc).__name__}: {exc}"
            failed_capture_path = None
            if output_path.exists():
                failed_path = output_path.with_suffix(output_path.suffix + ".failed.txt")
                output_path.replace(failed_path)
                failed_capture_path = str(failed_path)
            failed_outputs.append(
                {
                    "program_path": str(program_path),
                    "output_path": str(output_path),
                    "failed_capture_path": failed_capture_path,
                    "error": error,
                }
            )
        rows.extend(program_rows)
        program_results.append(
            {
                "program_path": str(program_path),
                "output_path": str(output_path),
                "status": status,
                "row_count": len(program_rows),
                **({"error": error} if error else {}),
            }
        )
        if status == "failed_gap_output":
            break
    return rows, program_results, missing_outputs, failed_outputs


def status_counts(program_results: Iterable[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("status")) for row in program_results).items()))


def build_blocked_summary(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    output_dir: Path,
    gap_path: str | None,
    gap_library_path: Path | None,
    rows: list[dict[str, Any]],
    program_results: list[dict[str, Any]],
    missing_outputs: list[str],
    failed_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    blocking_reasons: list[str] = []
    if missing_outputs:
        blocking_reasons.append("missing_gap_and_missing_captured_outputs")
    if failed_outputs:
        blocking_reasons.append("failed_gap_outputs")
    status = "blocked_failed_gap_outputs" if failed_outputs else "blocked_missing_gap_outputs"
    return {
        "schema_version": 1,
        "record_type": "igp24_gap_group_index_workflow",
        "created_at": utc_now(),
        "tool": "scripts/igp24_run_gap_group_index_workflow.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "manifest_path": str(manifest_path),
        "manifest_label_count": manifest.get("label_count"),
        "program_count": len(manifest.get("programs") or []),
        "gap_path": gap_path,
        "gap_library_path": str(gap_library_path) if gap_library_path else None,
        "status": status,
        "blocking_reasons": blocking_reasons,
        "program_status_counts": status_counts(program_results),
        "program_results": program_results,
        "missing_output_files": missing_outputs,
        "failed_output_files": failed_outputs,
        "rows_available": len(rows),
        "rows_imported": 0,
        "group_count": 0,
        "index_path": None,
        "readiness_output_dir": None,
        "readiness_blocking_reasons": None,
        "no_approximation_written": True,
        "live_submission_recommended_now": False,
        "output_files": {
            "summary_json": str(output_dir / WORKFLOW_SUMMARY_JSON),
            "report_md": str(output_dir / WORKFLOW_REPORT_MD),
        },
    }


def run_workflow(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = args.manifest
    manifest = read_json(manifest_path)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    gap_path = args.gap_path or shutil.which("gap")
    gap_library_path = args.gap_library_path
    rows, program_results, missing_outputs, failed_outputs = load_or_run_programs(
        manifest=manifest,
        manifest_path=manifest_path,
        output_dir=output_dir,
        gap_path=gap_path,
        gap_library_path=gap_library_path,
        timeout=int(args.timeout),
        reuse_existing_outputs=not args.no_reuse_existing_outputs,
    )
    if missing_outputs or failed_outputs:
        summary = build_blocked_summary(
            manifest_path=manifest_path,
            manifest=manifest,
            output_dir=output_dir,
            gap_path=gap_path,
            gap_library_path=gap_library_path,
            rows=rows,
            program_results=program_results,
            missing_outputs=missing_outputs,
            failed_outputs=failed_outputs,
        )
        write_summary(output_dir, summary)
        return summary

    write_jsonl(output_dir / COMBINED_ROWS_JSONL, rows)
    index = GroupCycleIndex(args.index)
    import_summary = import_rows_into_index(
        rows,
        index,
        import_source=output_dir / COMBINED_ROWS_JSONL,
        extra_provenance={
            "workflow": "scripts/igp24_run_gap_group_index_workflow.py",
            "manifest": str(manifest_path),
            "manifest_labels": manifest.get("labels"),
        },
        expected_labels=manifest.get("labels"),
    )
    write_json(output_dir / IMPORT_SUMMARY_JSON, import_summary)

    readiness_summary = None
    if not args.skip_readiness:
        readiness_dir = args.readiness_output_dir or (output_dir / "readiness")
        readiness_summary, readiness_routes = build_readiness(
            index_path=args.index,
            score_plan_path=args.score_plan,
            historical_paths=list(args.historical_jsonl or []),
            progress_path=args.progress_jsonl,
            output_dir=readiness_dir,
            top_targets=int(args.top_targets),
            families_per_target=int(args.families_per_target),
            target_category=args.target_category or None,
            avoid_labels=list(args.avoid_label or []),
        )
        write_readiness_outputs(readiness_dir, summary=readiness_summary, routes=readiness_routes)

    blocking_reasons = list((readiness_summary or {}).get("blocking_reasons") or [])
    if args.skip_readiness:
        workflow_status = "index_imported_readiness_skipped"
    elif blocking_reasons:
        workflow_status = "index_imported_readiness_blocked"
    else:
        workflow_status = "index_imported_readiness_ready"
    summary = {
        "schema_version": 1,
        "record_type": "igp24_gap_group_index_workflow",
        "created_at": utc_now(),
        "tool": "scripts/igp24_run_gap_group_index_workflow.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "manifest_path": str(manifest_path),
        "manifest_label_count": manifest.get("label_count"),
        "program_count": len(manifest.get("programs") or []),
        "gap_path": gap_path,
        "gap_library_path": str(gap_library_path) if gap_library_path else None,
        "status": workflow_status,
        "blocking_reasons": blocking_reasons,
        "program_status_counts": status_counts(program_results),
        "program_results": program_results,
        "missing_output_files": [],
        "rows_available": len(rows),
        "rows_imported": import_summary["rows_imported"],
        "import_integrity": import_summary.get("integrity"),
        "group_count": import_summary["group_count"],
        "labels_imported": import_summary["labels_imported"],
        "index_path": str(args.index),
        "import_summary_path": str(output_dir / IMPORT_SUMMARY_JSON),
        "combined_rows_jsonl": str(output_dir / COMBINED_ROWS_JSONL),
        "readiness_output_dir": str(args.readiness_output_dir or (output_dir / "readiness")) if not args.skip_readiness else None,
        "readiness_blocking_reasons": blocking_reasons if not args.skip_readiness else None,
        "structurally_eligible_route_count": (readiness_summary or {}).get("structurally_eligible_route_count"),
        "executable_generator_available_route_count": (readiness_summary or {}).get(
            "executable_generator_available_route_count"
        ),
        "generation_ready_route_count": (readiness_summary or {}).get("generation_ready_route_count"),
        "ready_for_structural_route_review": bool(readiness_summary and readiness_summary.get("ready_for_structural_route_review")),
        "ready_for_group_directed_generation": bool(readiness_summary and readiness_summary.get("ready_for_group_directed_generation")),
        "no_approximation_written": False,
        "live_submission_recommended_now": False,
        "output_files": {
            "summary_json": str(output_dir / WORKFLOW_SUMMARY_JSON),
            "report_md": str(output_dir / WORKFLOW_REPORT_MD),
            "combined_rows_jsonl": str(output_dir / COMBINED_ROWS_JSONL),
            "import_summary_json": str(output_dir / IMPORT_SUMMARY_JSON),
        },
    }
    write_summary(output_dir, summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--gap_path")
    parser.add_argument("--gap_library_path", type=Path)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--no_reuse_existing_outputs", action="store_true")
    parser.add_argument("--score_plan", type=Path, default=DEFAULT_SCORE_PLAN)
    parser.add_argument("--historical_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--progress_jsonl", type=Path)
    parser.add_argument("--readiness_output_dir", type=Path)
    parser.add_argument("--top_targets", type=int, default=25)
    parser.add_argument("--families_per_target", type=int, default=5)
    parser.add_argument("--target_category", default="uncovered_signature")
    parser.add_argument("--avoid_label", action="append", default=[])
    parser.add_argument("--skip_readiness", action="store_true")
    parser.add_argument("--fail_on_block", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_workflow(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.fail_on_block and summary.get("blocking_reasons"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
