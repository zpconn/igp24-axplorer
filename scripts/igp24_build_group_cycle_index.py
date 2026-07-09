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

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/remediation_20260709/group_compatibility_phase3"
DEFAULT_INDEX = DEFAULT_OUTPUT_DIR / "degree24_group_cycle_index.sqlite"


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
        "required_dependency": "GAP with TransitiveGroup(24,t), ConjugacyClasses, CycleLengthsPerm, SignPerm",
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
  Print("\\"status\\":\\"complete\\",\\"block_sizes\\":[],\\"cycle_types\\":[");
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--labels", default="1-10", help="Comma/range labels, e.g. 24T1,24T2 or 1-100")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--report_missing_gap_ok", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    gap_path = shutil.which("gap")
    if not gap_path:
        write_dependency_report(
            args.output_dir,
            gap_path=None,
            note="GAP is not available on PATH; full Phase 3 index precomputation is blocked.",
        )
        print(json.dumps({"status": "blocked_missing_gap", "output_dir": str(args.output_dir)}, indent=2, sort_keys=True))
        return 0 if args.report_missing_gap_ok else 2

    labels = parse_label_range(args.labels)
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
