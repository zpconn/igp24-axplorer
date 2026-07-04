#!/usr/bin/env python3
"""Export proxy-scored IGP24 candidate shortlists from existing ledgers.

This helper is intentionally file-only. It does not call PARI, MAGMA, SAIR, or
any network API; it prepares auditable candidate exports for later manual
offline verification.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SHORTLIST_JSONL = "shortlist.jsonl"
COEFFICIENTS_JSON = "coefficients.json"
COEFFICIENTS_TXT = "coefficients.txt"
MANIFEST_JSON = "manifest.json"


def parse_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _ledger_paths_from_summary(summary_path: Path) -> list[Path]:
    rows = json.loads(summary_path.read_text(encoding="utf-8"))
    paths: list[Path] = []
    for row in rows:
        ledger_path = row.get("ledger_path")
        if not ledger_path:
            continue
        path = Path(ledger_path)
        if not path.is_absolute():
            path = summary_path.parent / path
        paths.append(path)
    return paths


def resolve_ledger_paths(inputs: Iterable[str | Path]) -> list[Path]:
    """Resolve ledger JSONL paths from files, summary files, or directories."""

    resolved: list[Path] = []
    seen: set[Path] = set()
    for raw in inputs:
        path = Path(raw)
        candidates: list[Path] = []
        if path.is_file() and path.name == "summary.json":
            candidates = _ledger_paths_from_summary(path)
        elif path.is_file():
            candidates = [path]
        elif path.is_dir() and (path / "summary.json").exists():
            candidates = _ledger_paths_from_summary(path / "summary.json")
        elif path.is_dir():
            candidates = sorted(path.glob("**/candidates.jsonl"))
        else:
            raise FileNotFoundError(f"input path does not exist: {path}")

        for candidate in candidates:
            absolute = candidate.resolve()
            if absolute not in seen:
                resolved.append(absolute)
                seen.add(absolute)
    return resolved


def load_records(ledger_paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for raw in ledger_paths:
        path = Path(raw).resolve()
        for record in read_jsonl(path):
            item = dict(record)
            item["source_ledger_path"] = str(path)
            loaded.append(item)
    return loaded


def _sort_value(record: dict[str, Any], sort_by: str, ascending: bool) -> tuple[float, str]:
    value = record.get(sort_by)
    if value is None:
        score_components = record.get("score_components") or {}
        value = score_components.get(sort_by)
    try:
        numeric = float(value)
        if math.isnan(numeric):
            raise ValueError
    except Exception:
        numeric = math.inf if ascending else -math.inf
    return numeric, str(record.get("canonical_hash") or "")


def select_records(
    records: Iterable[dict[str, Any]],
    target_r: int | None = None,
    strategies: set[str] | None = None,
    limit: int | None = None,
    sort_by: str = "score",
    ascending: bool = False,
) -> list[dict[str, Any]]:
    """Filter, sort, deduplicate by canonical hash, and limit records."""

    filtered: list[dict[str, Any]] = []
    for record in records:
        if target_r is not None and record.get("real_root_count") != target_r:
            continue
        strategy = (record.get("generation_metadata") or {}).get("strategy")
        if strategies and strategy not in strategies:
            continue
        if not record.get("canonical_hash"):
            continue
        filtered.append(record)

    filtered.sort(key=lambda record: _sort_value(record, sort_by, ascending), reverse=not ascending)
    by_hash: dict[str, dict[str, Any]] = {}
    for record in filtered:
        by_hash.setdefault(str(record["canonical_hash"]), record)

    selected = list(by_hash.values())
    if limit is not None:
        selected = selected[: max(0, int(limit))]
    return selected


def shortlist_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return the audit-safe subset written to shortlist outputs."""

    return {
        "canonical_hash": record.get("canonical_hash"),
        "exported_coefficients": record.get("exported_coefficients"),
        "score": record.get("score"),
        "real_root_count": record.get("real_root_count"),
        "log_abs_discriminant": record.get("log_abs_discriminant"),
        "coefficient_height": record.get("coefficient_height"),
        "score_components": record.get("score_components") or {},
        "generation_metadata": record.get("generation_metadata") or {},
        "verification_status": record.get("verification_status", "unverified"),
        "experiment_name": record.get("experiment_name"),
        "source_ledger_path": record.get("source_ledger_path"),
    }


def strategy_counts(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = Counter((record.get("generation_metadata") or {}).get("strategy", "missing") for record in records)
    return dict(sorted(counts.items()))


def get_source_commit(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def build_manifest(
    *,
    input_paths: list[Path],
    ledger_paths: list[Path],
    output_dir: Path,
    selected: list[dict[str, Any]],
    total_records_loaded: int,
    filters: dict[str, Any],
    sort: dict[str, Any],
    command: list[str],
    source_commit: str | None,
) -> dict[str, Any]:
    top_score = max((float(record["score"]) for record in selected if record.get("score") is not None), default=None)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_shortlist.py",
        "source_commit": source_commit,
        "command": command,
        "input_paths": [str(path) for path in input_paths],
        "resolved_ledger_paths": [str(path) for path in ledger_paths],
        "filters": filters,
        "sort": sort,
        "total_records_loaded": total_records_loaded,
        "selected_records": len(selected),
        "top_score": top_score,
        "strategy_counts": strategy_counts(selected),
        "output_files": {
            "shortlist_jsonl": str(output_dir / SHORTLIST_JSONL),
            "coefficients_json": str(output_dir / COEFFICIENTS_JSON),
            "coefficients_txt": str(output_dir / COEFFICIENTS_TXT),
            "manifest_json": str(output_dir / MANIFEST_JSON),
        },
        "safety": {
            "proxy_only": True,
            "verifier_executed": False,
            "submission_executed": False,
            "exact_group_claims": False,
            "note": "Export-only shortlist for later human-reviewed offline exact verification.",
        },
    }


def write_outputs(
    selected_records: list[dict[str, Any]],
    output_dir: Path,
    manifest: dict[str, Any],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shortlist = [shortlist_record(record) for record in selected_records]

    shortlist_path = output_dir / SHORTLIST_JSONL
    with shortlist_path.open("w", encoding="utf-8") as handle:
        for record in shortlist:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    coefficients = [
        {
            "canonical_hash": record["canonical_hash"],
            "score": record["score"],
            "real_root_count": record["real_root_count"],
            "exported_coefficients": record["exported_coefficients"],
            "source_ledger_path": record["source_ledger_path"],
        }
        for record in shortlist
    ]
    coefficients_json_path = output_dir / COEFFICIENTS_JSON
    coefficients_json_path.write_text(json.dumps(coefficients, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    coefficients_txt_path = output_dir / COEFFICIENTS_TXT
    with coefficients_txt_path.open("w", encoding="utf-8") as handle:
        for record in coefficients:
            handle.write(json.dumps(record["exported_coefficients"], separators=(",", ":")) + "\n")

    manifest_path = output_dir / MANIFEST_JSON
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "shortlist_jsonl": shortlist_path,
        "coefficients_json": coefficients_json_path,
        "coefficients_txt": coefficients_txt_path,
        "manifest_json": manifest_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a proxy-scored IGP24 candidate shortlist from existing ledgers or benchmark directories"
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Ledger JSONL files, benchmark summary.json files, or benchmark directories")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_r", type=int, default=None, help="Keep only records with this real-root count")
    parser.add_argument("--strategies", default=None, help="Comma-separated generation_metadata.strategy filter")
    parser.add_argument("--limit", type=int, default=25, help="Maximum deduplicated records to export")
    parser.add_argument("--sort_by", default="score", help="Record field or score_components key to sort by")
    parser.add_argument("--ascending", action="store_true", help="Sort ascending instead of descending")
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    input_paths = [path.resolve() for path in args.inputs]
    output_dir = args.output_dir.resolve()
    strategies = set(parse_csv(args.strategies))

    try:
        ledger_paths = resolve_ledger_paths(input_paths)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    records = load_records(ledger_paths)
    selected = select_records(
        records,
        target_r=args.target_r,
        strategies=strategies or None,
        limit=args.limit,
        sort_by=args.sort_by,
        ascending=args.ascending,
    )
    manifest = build_manifest(
        input_paths=input_paths,
        ledger_paths=ledger_paths,
        output_dir=output_dir,
        selected=selected,
        total_records_loaded=len(records),
        filters={
            "target_r": args.target_r,
            "strategies": sorted(strategies),
            "deduplicate_by": "canonical_hash",
            "limit": args.limit,
        },
        sort={"sort_by": args.sort_by, "ascending": args.ascending},
        command=[sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_shortlist.py", *argv],
        source_commit=get_source_commit(args.repo_root.resolve()),
    )
    paths = write_outputs(selected, output_dir, manifest)

    print(f"loaded_records\t{len(records)}")
    print(f"selected_records\t{len(selected)}")
    print(f"top_score\t{manifest['top_score'] if manifest['top_score'] is not None else 'NA'}")
    print(f"strategy_counts\t{json.dumps(manifest['strategy_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
