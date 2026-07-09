#!/usr/bin/env python3
"""Build or probe the IGP24 degree-24 group cycle-type index.

This script requires GAP with the transitive-groups library. If GAP is missing,
it writes a dependency report and exits without fabricating any group data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.igp24.group_compatibility import (  # noqa: E402
    DEGREE,
    GroupCycleIndex,
    GroupRecord,
    utc_now,
    write_json,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/remediation_20260709/group_compatibility_phase3"
DEFAULT_INDEX = DEFAULT_OUTPUT_DIR / "degree24_group_cycle_index.sqlite"

GAP_EXPORT_PROGRAM = "degree24_group_cycle_export.g"
GAP_EXPORT_MANIFEST = "gap_export_manifest.json"
IMPORT_SUMMARY_JSON = "group_cycle_index_import_summary.json"


def parse_label(value: str) -> tuple[str, int]:
    text = value.strip()
    if text.startswith("24T"):
        return text, int(text[3:])
    number = int(text)
    return f"24T{number}", number


def parse_label_range(value: str) -> list[str]:
    labels: list[str] = []
    for part in value.split(","):
        raw = part.strip()
        if not raw:
            continue
        if "-" in raw:
            start_text, end_text = raw.split("-", 1)
            _start_label, start = parse_label(start_text)
            _end_label, end = parse_label(end_text)
            labels.extend(f"24T{number}" for number in range(start, end + 1))
        else:
            labels.append(parse_label(raw)[0])
    return labels


def write_dependency_report(output_dir: Path, *, gap_path: str | None, note: str) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "record_type": "igp24_group_cycle_index_dependency_report",
        "created_at": utc_now(),
        "gap_path": gap_path,
        "dependency_available": bool(gap_path),
        "status": "blocked_missing_gap" if not gap_path else "gap_available",
        "note": note,
        "required_dependency": (
            "GAP with TransitiveGroup(24,t), ConjugacyClasses, CycleLengthsPerm, "
            "SignPerm, AllBlocks"
        ),
        "no_approximation_written": not bool(gap_path),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "gap_dependency_report.json", payload)
    lines = [
        "# IGP24 Group Cycle Index Dependency Report",
        "",
        f"- Created UTC: `{payload['created_at']}`",
        f"- GAP path: `{payload['gap_path']}`",
        f"- Status: `{payload['status']}`",
        f"- Note: {payload['note']}",
        "",
        "No approximate group-cycle index was written.",
        "",
    ]
    (output_dir / "gap_dependency_report.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def gap_program(labels: list[str]) -> str:
    label_numbers = [parse_label(label)[1] for label in labels]
    numbers_text = ",".join(str(value) for value in label_numbers)
    domain_text = ",".join(str(i) for i in range(1, DEGREE + 1))
    return f"""
LoadPackage("transgrp");
Print("[\\n");
first := true;
for t in [{numbers_text}] do
  label := Concatenation("24T", String(t));
  g := TransitiveGroup({DEGREE}, t);
  classes := ConjugacyClasses(g);
  cycles := [];
  all_even := true;
  block_sizes := [];
  if not IsPrimitive(g, [{domain_text}]) then
    for b in AllBlocks(g, [{domain_text}]) do
      if Length(b) > 1 and Length(b) < {DEGREE} and {DEGREE} mod Length(b) = 0 then
        AddSet(block_sizes, Length(b));
      fi;
    od;
  fi;
  for c in classes do
    rep := Representative(c);
    lengths := SortedList(CycleLengthsPerm(rep, [{domain_text}]));
    cycle_text := "";
    for i in [1..Length(lengths)] do
      if i > 1 then
        Append(cycle_text, ".");
      fi;
      Append(cycle_text, String(lengths[i]));
    od;
    AddSet(cycles, cycle_text);
    if SignPerm(rep) = -1 then
      all_even := false;
    fi;
  od;
  if not first then
    Print(",\\n");
  fi;
  first := false;
  Print("{{\\"label\\":\\"", label, "\\",\\"t\\":", t, ",\\"degree\\":{DEGREE},");
  Print("\\"group_order\\":\\"", String(Size(g)), "\\",");
  Print("\\"primitive\\":", IsPrimitive(g, [{domain_text}]), ",");
  Print("\\"solvable\\":", IsSolvableGroup(g), ",");
  if all_even then
    Print("\\"parity\\":\\"even\\",");
  else
    Print("\\"parity\\":\\"mixed\\",");
  fi;
  Print("\\"status\\":\\"complete\\",\\"block_sizes\\":[");
  for i in [1..Length(block_sizes)] do
    if i > 1 then
      Print(",");
    fi;
    Print(block_sizes[i]);
  od;
  Print("],\\"cycle_types\\":[");
  for i in [1..Length(cycles)] do
    if i > 1 then
      Print(",");
    fi;
    Print("\\"", cycles[i], "\\"");
  od;
  Print("]}}");
od;
Print("\\n]\\n");
QUIT;
"""


def run_gap(gap_path: str, labels: list[str], *, timeout: int) -> list[dict[str, Any]]:
    program = gap_program(labels)
    with tempfile.NamedTemporaryFile("w", suffix=".g", encoding="utf-8", delete=False) as handle:
        handle.write(program)
        program_path = Path(handle.name)
    try:
        result = subprocess.run(
            [gap_path, "-q", str(program_path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    finally:
        program_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"GAP failed with code {result.returncode}: {result.stderr[-2000:]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GAP returned non-JSON output: {result.stdout[-2000:]}") from exc
    if not isinstance(payload, list):
        raise RuntimeError("GAP output was not a JSON list")
    return [row for row in payload if isinstance(row, dict)]


def iter_chunks(values: list[str], chunk_size: int) -> list[list[str]]:
    size = max(1, int(chunk_size))
    return [values[index : index + size] for index in range(0, len(values), size)]


def write_gap_export_programs(
    output_dir: Path,
    labels: list[str],
    *,
    chunk_size: int,
    source_commit: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = iter_chunks(labels, chunk_size)
    programs: list[dict[str, Any]] = []
    for chunk_index, chunk in enumerate(chunks, start=1):
        first = parse_label(chunk[0])[1]
        last = parse_label(chunk[-1])[1]
        path = output_dir / f"degree24_group_cycle_export_{chunk_index:04d}_{first}_{last}.g"
        path.write_text(gap_program(chunk), encoding="utf-8")
        programs.append(
            {
                "path": str(path),
                "chunk_index": chunk_index,
                "label_count": len(chunk),
                "first_label": chunk[0],
                "last_label": chunk[-1],
                "command": f"gap -q {path}",
                "expected_output": "JSON array on stdout; redirect to a .json file and import with --import_rows",
            }
        )
    single_path = output_dir / GAP_EXPORT_PROGRAM
    if len(chunks) == 1:
        single_path.write_text(gap_program(labels), encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "record_type": "igp24_gap_group_cycle_export_manifest",
        "created_at": utc_now(),
        "source_commit": source_commit,
        "degree": DEGREE,
        "label_count": len(labels),
        "labels": labels,
        "chunk_size": int(chunk_size),
        "program_count": len(programs),
        "programs": programs,
        "safety": {
            "runs_gap_only": True,
            "calls_sair": False,
            "calls_network": False,
            "writes_repo_index": False,
            "output_format": "JSON rows accepted by scripts/igp24_build_group_cycle_index.py --import_rows",
        },
    }
    write_json(output_dir / GAP_EXPORT_MANIFEST, manifest)
    return manifest


def load_import_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("expected JSON list of GAP group rows")
        return [row for row in payload if isinstance(row, dict)]
    if text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            if isinstance(payload.get("groups"), list):
                return [row for row in payload["groups"] if isinstance(row, dict)]
            if isinstance(payload.get("rows"), list):
                return [row for row in payload["rows"] if isinstance(row, dict)]
            return [payload]
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.strip():
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def record_from_gap(row: dict[str, Any]) -> GroupRecord:
    return GroupRecord(
        label=str(row["label"]),
        t=int(row["t"]),
        degree=int(row.get("degree", DEGREE)),
        order=int(row["group_order"]) if row.get("group_order") not in (None, "") else None,
        primitive=bool(row["primitive"]) if row.get("primitive") is not None else None,
        solvable=bool(row["solvable"]) if row.get("solvable") is not None else None,
        parity=str(row.get("parity") or "unknown"),
        block_sizes=tuple(int(value) for value in row.get("block_sizes") or []),
        cycle_types=tuple(str(value) for value in row.get("cycle_types") or []),
        status=str(row.get("status") or "complete"),
        provenance={"source": "gap_transitive_group_library", "gap_row": row},
    )


def import_rows_into_index(
    rows: list[dict[str, Any]],
    index: GroupCycleIndex,
    *,
    import_source: Path | None,
    extra_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    index.initialize(
        provenance={
            "builder": "scripts/igp24_build_group_cycle_index.py",
            "mode": "import_rows",
            "import_source": str(import_source) if import_source else None,
            **(extra_provenance or {}),
        }
    )
    imported: list[str] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=1):
        try:
            record = record_from_gap(row)
            index.upsert_group(record)
            imported.append(record.label)
        except Exception as exc:  # noqa: BLE001 - preserve bad-row context in summary.
            errors.append({"row_number": row_number, "error": str(exc), "row": row})
    if errors:
        raise ValueError(f"failed to import {len(errors)} group rows: {errors[:3]}")
    return {
        "schema_version": 1,
        "record_type": "igp24_group_cycle_index_import_summary",
        "created_at": utc_now(),
        "index": str(index.path),
        "import_source": str(import_source) if import_source else None,
        "rows_read": len(rows),
        "rows_imported": len(imported),
        "labels_imported": sorted(imported, key=lambda label: parse_label(label)[1]),
        "group_count": index.group_count(),
        "source": "gap_json_rows",
        "no_approximation_written": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--labels", default="1-10", help="Comma/range labels, e.g. 24T1,24T2 or 1-100")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--report_missing_gap_ok", action="store_true")
    parser.add_argument("--import_rows", type=Path, help="Import GAP JSON/JSONL rows instead of running GAP")
    parser.add_argument("--write_gap_program_dir", type=Path, help="Write chunked GAP export programs and exit")
    parser.add_argument("--gap_program_chunk_size", type=int, default=250)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    labels = parse_label_range(args.labels)
    if args.write_gap_program_dir:
        manifest = write_gap_export_programs(
            args.write_gap_program_dir,
            labels,
            chunk_size=int(args.gap_program_chunk_size),
            source_commit=get_source_commit(REPO_ROOT),
        )
        print(json.dumps({"status": "gap_programs_written", "manifest": str(args.write_gap_program_dir / GAP_EXPORT_MANIFEST), "program_count": manifest["program_count"]}, indent=2, sort_keys=True))
        return 0

    if args.import_rows:
        rows = load_import_rows(args.import_rows)
        index = GroupCycleIndex(args.index)
        summary = import_rows_into_index(
            rows,
            index,
            import_source=args.import_rows,
            extra_provenance={"labels": labels},
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / IMPORT_SUMMARY_JSON, summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    gap_path = shutil.which("gap")
    if not gap_path:
        write_dependency_report(
            args.output_dir,
            gap_path=None,
            note="GAP is not available on PATH; full Phase 3 index precomputation is blocked.",
        )
        print(json.dumps({"status": "blocked_missing_gap", "output_dir": str(args.output_dir)}, indent=2, sort_keys=True))
        return 0 if args.report_missing_gap_ok else 2

    index = GroupCycleIndex(args.index)
    index.initialize(
        provenance={
            "builder": "scripts/igp24_build_group_cycle_index.py",
            "gap_path": gap_path,
            "labels": labels,
        }
    )
    rows = run_gap(gap_path, labels, timeout=args.timeout)
    for row in rows:
        index.upsert_group(record_from_gap(row))
    summary = {
        "schema_version": 1,
        "record_type": "igp24_group_cycle_index_build_summary",
        "created_at": utc_now(),
        "index": str(args.index),
        "labels_requested": labels,
        "rows_returned": len(rows),
        "group_count": index.group_count(),
        "gap_path": gap_path,
    }
    write_json(args.output_dir / "group_cycle_index_build_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
