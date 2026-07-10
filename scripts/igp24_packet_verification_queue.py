#!/usr/bin/env python3
"""Materialize packet-optimizer selections into an exact-verification queue.

The packet optimizer intentionally strips bulky source records from its
selected JSONL. This helper joins those selected rows back to one or more
full candidate JSONL files, validates the exported coefficient vectors, and
writes the review-batch format consumed by ``scripts/igp24_offline_verify.py``.

It is local/file-only: it does not call SAIR, does not use network access, and
does not run Magma/PARI/SymPy verification itself.
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

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.group_compatibility import read_jsonl, write_json, write_jsonl  # noqa: E402

VERIFICATION_BATCH_JSONL = "verification_batch.jsonl"
VERIFICATION_COEFFICIENTS_TXT = "verification_coefficients.txt"
MANIFEST_JSON = "manifest.json"
REPORT_MD = "verification_queue_report.md"


class VerificationQueueError(ValueError):
    """Raised when the queue would be incomplete or unsafe."""


def _validate_exported_coefficients(value: Any, *, context: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 25:
        raise VerificationQueueError(f"{context}: expected 25 exported coefficients")
    if any(not isinstance(item, int) for item in value):
        raise VerificationQueueError(f"{context}: coefficients must be integers")
    if int(value[-1]) != 1:
        raise VerificationQueueError(f"{context}: leading coefficient must be 1")
    return [int(item) for item in value]


def _hash(row: dict[str, Any]) -> str:
    return str(row.get("canonical_hash") or row.get("candidate_hash") or "")


def index_source_rows(paths: Iterable[Path]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    by_hash: dict[str, dict[str, Any]] = {}
    source_summaries: list[dict[str, Any]] = []
    for path in paths:
        rows = read_jsonl(path)
        usable = 0
        for row_index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            canonical_hash = _hash(row)
            if not canonical_hash:
                continue
            if "exported_coefficients" not in row:
                continue
            _validate_exported_coefficients(row.get("exported_coefficients"), context=f"{path}:{row_index}")
            candidate = {**row, "source_candidate_jsonl": str(path), "source_candidate_row_index": row_index}
            prior = by_hash.get(canonical_hash)
            if prior is not None and prior.get("exported_coefficients") != candidate.get("exported_coefficients"):
                raise VerificationQueueError(f"{canonical_hash[:12]}: conflicting source coefficient rows")
            by_hash[canonical_hash] = candidate
            usable += 1
        source_summaries.append({"path": str(path), "rows": len(rows), "coefficient_rows_indexed": usable})
    return by_hash, source_summaries


def materialize_queue(
    *,
    selected_rows: list[dict[str, Any]],
    source_rows_by_hash: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    materialized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, selected in enumerate(selected_rows, start=1):
        canonical_hash = _hash(selected)
        if not canonical_hash:
            raise VerificationQueueError(f"selected row {index}: missing canonical_hash")
        if canonical_hash in seen:
            raise VerificationQueueError(f"selected row {index}: duplicate canonical_hash {canonical_hash}")
        seen.add(canonical_hash)
        source = source_rows_by_hash.get(canonical_hash)
        if source is None:
            raise VerificationQueueError(f"{canonical_hash[:12]}: selected hash missing from coefficient sources")
        coefficients = _validate_exported_coefficients(
            source.get("exported_coefficients"),
            context=f"{canonical_hash[:12]}.source.exported_coefficients",
        )
        record = dict(source)
        record["exported_coefficients"] = coefficients
        record["verification_queue_index"] = index
        record["optimizer_rank"] = selected.get("optimizer_rank", index)
        record["packet_optimizer_selected_row"] = selected
        record["packet_optimizer_short_hash"] = selected.get("short_hash") or canonical_hash[:12]
        record["packet_optimizer_best_case_points"] = selected.get("best_case_points")
        record["packet_optimizer_marginal_best_case_points"] = selected.get("marginal_best_case_points")
        record["packet_optimizer_expected_points_status"] = selected.get("expected_points_status")
        record["packet_optimizer_valuable_targets_not_ruled_out"] = selected.get("valuable_targets_not_ruled_out") or []
        record["offline_verification_status"] = "prepared_unverified"
        record["verified_group_label"] = None
        materialized.append(record)
    return materialized


def build_manifest(
    *,
    selected_jsonl: Path,
    source_candidate_jsonls: list[Path],
    source_summaries: list[dict[str, Any]],
    records: list[dict[str, Any]],
    output_dir: Path,
    command: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "record_type": "igp24_packet_verification_queue",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_packet_verification_queue.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "command": command,
        "selected_jsonl": str(selected_jsonl),
        "source_candidate_jsonls": [str(path) for path in source_candidate_jsonls],
        "source_summaries": source_summaries,
        "output_dir": str(output_dir),
        "selected_records": len(records),
        "selected_hashes": [str(row.get("canonical_hash")) for row in records],
        "selected_short_hashes": [str(row.get("canonical_hash") or "")[:12] for row in records],
        "optimizer_ranks": [row.get("optimizer_rank") for row in records],
        "safety": {
            "network_calls": False,
            "sair_submission": False,
            "auto_submission": False,
            "exact_group_claims": False,
            "exact_nfdisc_claims": False,
            "review_queue_only": True,
        },
        "output_files": {
            "verification_batch_jsonl": str(output_dir / VERIFICATION_BATCH_JSONL),
            "verification_coefficients_txt": str(output_dir / VERIFICATION_COEFFICIENTS_TXT),
            "manifest_json": str(output_dir / MANIFEST_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
    }


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Packet Verification Queue",
        "",
        f"- Created: `{manifest['created_at']}`",
        f"- Source commit: `{manifest['source_commit']}`",
        f"- Selected JSONL: `{manifest['selected_jsonl']}`",
        f"- Selected records: `{manifest['selected_records']}`",
        f"- Safety: no network, no SAIR submission, no exact label claims.",
        "",
        "## Queue",
        "",
        "| index | rank | hash |",
        "| ---: | ---: | --- |",
    ]
    for index, (rank, short_hash) in enumerate(
        zip(manifest["optimizer_ranks"], manifest["selected_short_hashes"]),
        start=1,
    ):
        lines.append(f"| {index} | {rank} | `{short_hash}` |")
    lines.extend(["", "Run this directory through `scripts/igp24_offline_verify.py` for exact-r/nfdisc/Magma review artifacts.", ""])
    return "\n".join(lines)


def write_outputs(output_dir: Path, *, records: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_path = output_dir / VERIFICATION_BATCH_JSONL
    coefficients_path = output_dir / VERIFICATION_COEFFICIENTS_TXT
    manifest_path = output_dir / MANIFEST_JSON
    report_path = output_dir / REPORT_MD
    write_jsonl(batch_path, records)
    coefficients_path.write_text(
        "".join(json.dumps(row["exported_coefficients"], separators=(",", ":")) + "\n" for row in records),
        encoding="utf-8",
    )
    write_json(manifest_path, manifest)
    report_path.write_text(render_report(manifest), encoding="utf-8")
    return {
        "verification_batch_jsonl": batch_path,
        "verification_coefficients_txt": coefficients_path,
        "manifest_json": manifest_path,
        "report_md": report_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected_jsonl", type=Path, required=True)
    parser.add_argument("--source_candidate_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args(argv)

    selected_rows = read_jsonl(args.selected_jsonl)
    sources_by_hash, source_summaries = index_source_rows(args.source_candidate_jsonl)
    records = materialize_queue(selected_rows=selected_rows, source_rows_by_hash=sources_by_hash)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_packet_verification_queue.py", *argv]
    manifest = build_manifest(
        selected_jsonl=args.selected_jsonl,
        source_candidate_jsonls=list(args.source_candidate_jsonl),
        source_summaries=source_summaries,
        records=records,
        output_dir=args.output_dir,
        command=command,
    )
    paths = write_outputs(args.output_dir, records=records, manifest=manifest)
    print(f"selected_records\t{manifest['selected_records']}")
    print(f"selected_hashes\t{','.join(manifest['selected_short_hashes'])}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
