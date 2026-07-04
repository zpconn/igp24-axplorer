#!/usr/bin/env python3
"""Prepare human-review batches from proxy-only IGP24 shortlists.

This tool is intentionally review/export-only. It reads existing shortlist and
ledger files, then writes audit artifacts for later manual offline exact
verification. It does not call PARI, MAGMA, SAIR, network APIs, or submission
paths.
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

from scripts.igp24_shortlist import get_source_commit, read_jsonl, strategy_counts


REVIEW_REPORT_MD = "review_report.md"
VERIFICATION_BATCH_JSONL = "verification_batch.jsonl"
VERIFICATION_COEFFICIENTS_TXT = "verification_coefficients.txt"
MANIFEST_JSON = "manifest.json"
PROXY_CAVEAT = (
    "Proxy-only review batch for later human-reviewed offline exact "
    "verification. No exact group label is claimed."
)


def load_shortlist(shortlist_input: str | Path) -> tuple[list[dict[str, Any]], Path, dict[str, Any]]:
    """Load records and manifest from a shortlist export directory or JSONL."""

    path = Path(shortlist_input).resolve()
    if path.is_dir():
        shortlist_path = path / "shortlist.jsonl"
        manifest_path = path / "manifest.json"
    else:
        shortlist_path = path
        manifest_path = path.parent / "manifest.json"
    records = read_jsonl(shortlist_path)
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in records:
        record["source_shortlist_path"] = str(shortlist_path)
    return records, shortlist_path, manifest


def _read_ledgers_by_hash(ledger_paths: Iterable[str | Path]) -> dict[str, dict[str, Any]]:
    by_hash: dict[str, dict[str, Any]] = {}
    for raw in sorted({str(path) for path in ledger_paths if path}):
        path = Path(raw)
        if not path.exists():
            continue
        for record in read_jsonl(path):
            canonical_hash = record.get("canonical_hash")
            if canonical_hash:
                enriched = dict(record)
                enriched["source_ledger_path"] = str(path.resolve())
                by_hash.setdefault(str(canonical_hash), enriched)
    return by_hash


def hydrate_from_source_ledgers(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge shortlist records with full source-ledger records when present."""

    records = [dict(record) for record in records]
    ledger_records = _read_ledgers_by_hash(record.get("source_ledger_path") for record in records)
    hydrated: list[dict[str, Any]] = []
    for record in records:
        canonical_hash = str(record.get("canonical_hash") or "")
        source_shortlist_path = record.get("source_shortlist_path")
        merged = dict(ledger_records.get(canonical_hash, record))
        merged["source_ledger_path"] = record.get("source_ledger_path") or merged.get("source_ledger_path")
        merged["source_shortlist_path"] = source_shortlist_path
        merged["shortlist_score"] = record.get("score")
        hydrated.append(merged)
    return hydrated


def _strategy(record: dict[str, Any]) -> str:
    return str((record.get("generation_metadata") or {}).get("strategy") or "missing")


def _numeric_sort_value(record: dict[str, Any], sort_by: str, ascending: bool) -> tuple[float, str]:
    value = record.get(sort_by)
    if value is None:
        value = (record.get("score_components") or {}).get(sort_by)
    try:
        numeric = float(value)
        if math.isnan(numeric):
            raise ValueError
    except Exception:
        numeric = math.inf if ascending else -math.inf
    return numeric, str(record.get("canonical_hash") or "")


def _dedupe_best(records: Iterable[dict[str, Any]], sort_by: str, ascending: bool) -> list[dict[str, Any]]:
    sorted_records = sorted(records, key=lambda record: _numeric_sort_value(record, sort_by, ascending), reverse=not ascending)
    by_hash: dict[str, dict[str, Any]] = {}
    for record in sorted_records:
        canonical_hash = record.get("canonical_hash")
        if canonical_hash:
            by_hash.setdefault(str(canonical_hash), record)
    return list(by_hash.values())


def select_review_batch(
    records: Iterable[dict[str, Any]],
    batch_size: int,
    sort_by: str = "score",
    ascending: bool = False,
    per_strategy_cap: int | None = None,
    min_strategies: int = 0,
) -> list[dict[str, Any]]:
    """Select a deduplicated batch, nudging toward strategy diversity."""

    unique = _dedupe_best(records, sort_by=sort_by, ascending=ascending)
    batch_size = max(0, int(batch_size))
    if batch_size == 0:
        return []
    per_strategy_cap = None if per_strategy_cap is None else max(1, int(per_strategy_cap))
    min_strategies = max(0, int(min_strategies))

    selected: list[dict[str, Any]] = []
    selected_hashes: set[str] = set()
    counts: Counter[str] = Counter()

    def can_add(record: dict[str, Any], enforce_cap: bool = True) -> bool:
        canonical_hash = str(record.get("canonical_hash") or "")
        if not canonical_hash or canonical_hash in selected_hashes:
            return False
        if enforce_cap and per_strategy_cap is not None and counts[_strategy(record)] >= per_strategy_cap:
            return False
        return True

    def add(record: dict[str, Any]) -> None:
        selected.append(record)
        selected_hashes.add(str(record["canonical_hash"]))
        counts[_strategy(record)] += 1

    if min_strategies:
        best_by_strategy: dict[str, dict[str, Any]] = {}
        for record in unique:
            best_by_strategy.setdefault(_strategy(record), record)
        for _, record in sorted(best_by_strategy.items(), key=lambda item: _numeric_sort_value(item[1], sort_by, ascending), reverse=not ascending):
            if len(selected) >= batch_size or len(counts) >= min(min_strategies, len(best_by_strategy)):
                break
            if can_add(record):
                add(record)

    for record in unique:
        if len(selected) >= batch_size:
            break
        if can_add(record):
            add(record)

    if len(selected) < batch_size:
        for record in unique:
            if len(selected) >= batch_size:
                break
            if can_add(record, enforce_cap=False):
                add(record)

    return sorted(selected, key=lambda record: _numeric_sort_value(record, sort_by, ascending), reverse=not ascending)


def review_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a provenance-rich but review-safe record."""

    return {
        "canonical_hash": record.get("canonical_hash"),
        "score": record.get("score"),
        "real_root_count": record.get("real_root_count"),
        "log_abs_discriminant": record.get("log_abs_discriminant"),
        "coefficient_height": record.get("coefficient_height"),
        "source_strategy": _strategy(record),
        "source_ledger_path": record.get("source_ledger_path"),
        "source_shortlist_path": record.get("source_shortlist_path"),
        "exported_coefficients": record.get("exported_coefficients"),
        "score_components": record.get("score_components") or {},
        "generation_metadata": record.get("generation_metadata") or {},
        "target_metadata": record.get("target_metadata") or {},
        "verification_status": record.get("verification_status", "unverified"),
        "verified_group_label": None,
        "proxy_only_caveat": PROXY_CAVEAT,
    }


def build_review_report(records: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Proxy Review Batch",
        "",
        PROXY_CAVEAT,
        "",
        f"- Selected records: {len(records)}",
        f"- Top score: {manifest.get('top_score') if manifest.get('top_score') is not None else 'NA'}",
        f"- Strategy counts: `{json.dumps(manifest.get('strategy_counts', {}), sort_keys=True)}`",
        f"- Source shortlist: `{manifest.get('source_shortlist_path')}`",
        "",
        "| Rank | Score | Hash | r | Strategy | Height | log abs disc | Source Ledger |",
        "| ---: | ---: | --- | ---: | --- | ---: | ---: | --- |",
    ]
    for rank, record in enumerate(records, start=1):
        score = record.get("score")
        score_text = f"{float(score):.6f}" if score is not None else "NA"
        log_disc = record.get("log_abs_discriminant")
        log_disc_text = f"{float(log_disc):.3f}" if log_disc is not None else "NA"
        source = record.get("source_ledger_path") or ""
        lines.append(
            "| "
            f"{rank} | {score_text} | `{str(record.get('canonical_hash') or '')[:12]}` | "
            f"{record.get('real_root_count')} | `{record.get('source_strategy')}` | "
            f"{record.get('coefficient_height')} | {log_disc_text} | `{source}` |"
        )
    lines.extend(
        [
            "",
            "Safety:",
            "- No PARI, MAGMA, SAIR, network API, exact group verification, or submission was run.",
            "- Records are proxy-scored candidates only.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_manifest(
    *,
    source_shortlist_path: Path,
    source_shortlist_manifest: dict[str, Any],
    selected: list[dict[str, Any]],
    total_shortlist_records: int,
    output_dir: Path,
    command: list[str],
    criteria: dict[str, Any],
    source_commit: str | None,
) -> dict[str, Any]:
    source_ledgers = sorted({str(record.get("source_ledger_path")) for record in selected if record.get("source_ledger_path")})
    top_score = max((float(record["score"]) for record in selected if record.get("score") is not None), default=None)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_review_shortlist.py",
        "source_commit": source_commit,
        "command": command,
        "source_shortlist_path": str(source_shortlist_path),
        "source_shortlist_manifest": source_shortlist_manifest,
        "source_ledger_paths": source_ledgers,
        "criteria": criteria,
        "total_shortlist_records": total_shortlist_records,
        "selected_records": len(selected),
        "top_score": top_score,
        "strategy_counts": strategy_counts(selected),
        "output_files": {
            "review_report_md": str(output_dir / REVIEW_REPORT_MD),
            "verification_batch_jsonl": str(output_dir / VERIFICATION_BATCH_JSONL),
            "verification_coefficients_txt": str(output_dir / VERIFICATION_COEFFICIENTS_TXT),
            "manifest_json": str(output_dir / MANIFEST_JSON),
        },
        "safety": {
            "proxy_only": True,
            "review_export_only": True,
            "verifier_executed": False,
            "submission_executed": False,
            "network_calls": False,
            "exact_group_claims": False,
            "note": PROXY_CAVEAT,
        },
    }


def write_review_outputs(selected: list[dict[str, Any]], output_dir: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    review_records = [review_record(record) for record in selected]

    batch_path = output_dir / VERIFICATION_BATCH_JSONL
    with batch_path.open("w", encoding="utf-8") as handle:
        for record in review_records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    coefficients_path = output_dir / VERIFICATION_COEFFICIENTS_TXT
    with coefficients_path.open("w", encoding="utf-8") as handle:
        for record in review_records:
            handle.write(json.dumps(record.get("exported_coefficients"), separators=(",", ":")) + "\n")

    report_path = output_dir / REVIEW_REPORT_MD
    report_path.write_text(build_review_report(review_records, manifest), encoding="utf-8")

    manifest_path = output_dir / MANIFEST_JSON
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "review_report_md": report_path,
        "verification_batch_jsonl": batch_path,
        "verification_coefficients_txt": coefficients_path,
        "manifest_json": manifest_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a proxy-only IGP24 shortlist review batch")
    parser.add_argument("shortlist", type=Path, help="Shortlist export directory or shortlist.jsonl")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--sort_by", default="score")
    parser.add_argument("--ascending", action="store_true")
    parser.add_argument("--per_strategy_cap", type=int, default=None)
    parser.add_argument("--min_strategies", type=int, default=0)
    parser.add_argument("--no_follow_source_ledgers", action="store_true")
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    records, source_shortlist_path, source_manifest = load_shortlist(args.shortlist)
    candidates = records if args.no_follow_source_ledgers else hydrate_from_source_ledgers(records)
    selected = select_review_batch(
        candidates,
        batch_size=args.batch_size,
        sort_by=args.sort_by,
        ascending=args.ascending,
        per_strategy_cap=args.per_strategy_cap,
        min_strategies=args.min_strategies,
    )
    output_dir = args.output_dir.resolve()
    criteria = {
        "batch_size": args.batch_size,
        "sort_by": args.sort_by,
        "ascending": args.ascending,
        "per_strategy_cap": args.per_strategy_cap,
        "min_strategies": args.min_strategies,
        "deduplicate_by": "canonical_hash",
        "follow_source_ledgers": not args.no_follow_source_ledgers,
    }
    manifest = build_manifest(
        source_shortlist_path=source_shortlist_path,
        source_shortlist_manifest=source_manifest,
        selected=selected,
        total_shortlist_records=len(records),
        output_dir=output_dir,
        command=[sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_review_shortlist.py", *argv],
        criteria=criteria,
        source_commit=get_source_commit(args.repo_root.resolve()),
    )
    paths = write_review_outputs(selected, output_dir, manifest)

    print(f"loaded_shortlist_records\t{len(records)}")
    print(f"selected_records\t{len(selected)}")
    print(f"top_score\t{manifest['top_score'] if manifest['top_score'] is not None else 'NA'}")
    print(f"strategy_counts\t{json.dumps(manifest['strategy_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
