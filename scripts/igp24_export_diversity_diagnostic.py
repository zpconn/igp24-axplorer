#!/usr/bin/env python3
"""Diagnose IGP24 sample-export diversity without scoring candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.igp24.polynomial import DEGREE, stable_canonical_hash, validate_coefficients


DEFAULT_OUTPUT_DIR = Path("/tmp/igp24_export_diversity_diagnostic_20260704")
SAFETY = {
    "proxy_only": True,
    "scores_candidates": False,
    "local_search_run": False,
    "runs_exact_verifiers": False,
    "calls_sair": False,
    "uses_network": False,
    "auto_submits": False,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def command_text(argv: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def default_label(path: Path) -> str:
    name = path.name
    for suffix in [
        ".jsonl",
        ".json",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    prefix = "gpu_model_sample_export_diversity_"
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def extract_decoded_coefficients(record: dict[str, Any]) -> list[int] | None:
    coeffs = record.get("decoded_coefficients")
    if coeffs is None:
        exported = record.get("exported_coefficients")
        if isinstance(exported, list) and len(exported) == DEGREE + 1 and exported[-1] == 1:
            coeffs = exported[:-1]
    if coeffs is None:
        return None
    try:
        values = [int(value) for value in coeffs]
    except (TypeError, ValueError):
        return None
    if len(values) != DEGREE:
        return None
    return values


def coefficient_key(coefficients: list[int]) -> str:
    return json.dumps(coefficients, separators=(",", ":"))


def token_key(record: dict[str, Any]) -> str | None:
    token_ids = record.get("token_ids")
    if not isinstance(token_ids, list):
        return None
    try:
        values = [int(value) for value in token_ids]
    except (TypeError, ValueError):
        return None
    return json.dumps(values, separators=(",", ":"))


def key_digest(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def canonical_hash(
    coefficients: list[int],
    *,
    translation_radius: int,
    coeff_bound: int | None,
) -> str:
    values = validate_coefficients(coefficients)
    return stable_canonical_hash(values, radius=translation_radius, coeff_bound=coeff_bound)


def duplicate_count(counts: Counter[str]) -> int:
    return sum(count - 1 for count in counts.values() if count > 1)


def build_duplicate_groups(
    rows_by_key: dict[str, list[dict[str, Any]]],
    *,
    key_type: str,
    top_n: int,
) -> list[dict[str, Any]]:
    groups = []
    for key, rows in rows_by_key.items():
        if len(rows) <= 1:
            continue
        rows = sorted(rows, key=lambda row: int(row["sample_index"]))
        group = {
            "key_type": key_type,
            "key_digest": key_digest(key),
            "count": len(rows),
            "first_sample_index": rows[0]["sample_index"],
            "last_sample_index": rows[-1]["sample_index"],
            "first_batch_index": rows[0]["batch_index"],
            "last_batch_index": rows[-1]["batch_index"],
            "sample_indices": [row["sample_index"] for row in rows[:20]],
            "batch_indices": sorted({row["batch_index"] for row in rows}),
            "example_decoded_coefficients": rows[0].get("decoded_coefficients"),
        }
        if key_type == "canonical_hash":
            group["canonical_hash"] = key
        groups.append(group)
    return sorted(groups, key=lambda group: (-group["count"], group["first_sample_index"]))[:top_n]


def build_checkpoints(
    decoded_rows: list[dict[str, Any]],
    *,
    checkpoint_interval: int,
) -> list[dict[str, Any]]:
    if checkpoint_interval <= 0:
        return []
    exact_seen: set[str] = set()
    canonical_seen: set[str] = set()
    checkpoints: list[dict[str, Any]] = []
    for index, row in enumerate(decoded_rows, start=1):
        exact_seen.add(row["exact_key"])
        canonical_hash_value = row.get("canonical_hash")
        if canonical_hash_value:
            canonical_seen.add(canonical_hash_value)
        if index % checkpoint_interval == 0 or index == len(decoded_rows):
            checkpoints.append(
                {
                    "decoded_records": index,
                    "last_sample_index": row["sample_index"],
                    "exact_unique": len(exact_seen),
                    "exact_duplicate_records": index - len(exact_seen),
                    "canonical_unique": len(canonical_seen),
                    "canonical_duplicate_records": index - len(canonical_seen),
                }
            )
    return checkpoints


def summarize_batches(decoded_rows: list[dict[str, Any]], invalid_decode_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_batch: dict[int, list[dict[str, Any]]] = defaultdict(list)
    invalid_by_batch: Counter[int] = Counter()
    for row in decoded_rows:
        rows_by_batch[int(row["batch_index"])].append(row)
    for row in invalid_decode_rows:
        invalid_by_batch[int(row["batch_index"])] += 1

    batch_indices = sorted(set(rows_by_batch) | set(invalid_by_batch))
    batches = []
    for batch_index in batch_indices:
        rows = rows_by_batch.get(batch_index, [])
        exact_counts = Counter(row["exact_key"] for row in rows)
        canonical_counts = Counter(row["canonical_hash"] for row in rows if row.get("canonical_hash"))
        sample_indices = [int(row["sample_index"]) for row in rows]
        batches.append(
            {
                "batch_index": batch_index,
                "decoded_records": len(rows),
                "invalid_decode_records": invalid_by_batch[batch_index],
                "exact_unique": len(exact_counts),
                "exact_duplicate_records": duplicate_count(exact_counts),
                "canonical_unique": len(canonical_counts),
                "canonical_duplicate_records": duplicate_count(canonical_counts),
                "first_sample_index": min(sample_indices) if sample_indices else None,
                "last_sample_index": max(sample_indices) if sample_indices else None,
            }
        )
    return batches


def summarize_export(
    sample_export_path: Path,
    *,
    label: str | None = None,
    translation_radius: int = 2,
    coeff_bound: int | None = 4,
    checkpoint_interval: int = 256,
    top_n: int = 20,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sample_export_path = sample_export_path.resolve()
    records = read_jsonl(sample_export_path)
    decoded_rows: list[dict[str, Any]] = []
    invalid_decode_rows: list[dict[str, Any]] = []
    exact_rows_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    canonical_rows_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    token_rows_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    canonical_error_count = 0

    for record_index, record in enumerate(records):
        coeffs = extract_decoded_coefficients(record)
        row = {
            "record_index": record_index,
            "sample_index": int(record.get("sample_index", record_index)),
            "batch_index": int(record.get("batch_index", -1)),
            "batch_row": int(record.get("batch_row", -1)),
        }
        if coeffs is None:
            invalid_decode_rows.append(row)
            continue

        exact_key = coefficient_key(coeffs)
        try:
            canonical_hash_value = canonical_hash(
                coeffs,
                translation_radius=translation_radius,
                coeff_bound=coeff_bound,
            )
        except Exception:
            canonical_hash_value = None
            canonical_error_count += 1

        token_hash = token_key(record)
        decoded_row = {
            **row,
            "decoded_coefficients": coeffs,
            "exact_key": exact_key,
            "canonical_hash": canonical_hash_value,
            "token_key": token_hash,
        }
        decoded_rows.append(decoded_row)
        exact_rows_by_key[exact_key].append(decoded_row)
        if canonical_hash_value:
            canonical_rows_by_key[canonical_hash_value].append(decoded_row)
        if token_hash:
            token_rows_by_key[token_hash].append(decoded_row)

    exact_counts = Counter(row["exact_key"] for row in decoded_rows)
    canonical_counts = Counter(row["canonical_hash"] for row in decoded_rows if row.get("canonical_hash"))
    token_counts = Counter(row["token_key"] for row in decoded_rows if row.get("token_key"))
    source_label = label or default_label(sample_export_path)
    first_record = records[0] if records else {}
    summary = {
        "label": source_label,
        "sample_export_path": str(sample_export_path),
        "records_read": len(records),
        "decoded_records": len(decoded_rows),
        "invalid_decode_records": len(invalid_decode_rows),
        "exact_unique_coefficients": len(exact_counts),
        "exact_duplicate_records": duplicate_count(exact_counts),
        "exact_duplicate_groups": sum(1 for count in exact_counts.values() if count > 1),
        "canonical_unique_hashes": len(canonical_counts),
        "canonical_duplicate_records": duplicate_count(canonical_counts),
        "canonical_duplicate_hashes": sum(1 for count in canonical_counts.values() if count > 1),
        "canonical_error_records": canonical_error_count,
        "token_unique_sequences": len(token_counts),
        "token_duplicate_records": duplicate_count(token_counts),
        "exact_coefficient_key_digests": sorted(key_digest(key) for key in exact_counts),
        "canonical_hashes": sorted(canonical_counts),
        "top_exact_duplicate_groups": build_duplicate_groups(exact_rows_by_key, key_type="exact_coefficients", top_n=top_n),
        "top_canonical_duplicate_groups": build_duplicate_groups(
            canonical_rows_by_key,
            key_type="canonical_hash",
            top_n=top_n,
        ),
        "top_token_duplicate_groups": build_duplicate_groups(token_rows_by_key, key_type="token_ids", top_n=top_n),
        "batch_summaries": summarize_batches(decoded_rows, invalid_decode_rows),
        "checkpoints": build_checkpoints(decoded_rows, checkpoint_interval=checkpoint_interval),
        "metadata": {
            "device": first_record.get("device"),
            "temperature": first_record.get("temperature"),
            "top_k": first_record.get("top_k"),
            "exp_name": first_record.get("exp_name"),
            "exp_id": first_record.get("exp_id"),
            "generation_metadata": first_record.get("generation_metadata") or {},
        },
        "diagnostic_scope": {
            "translation_radius": translation_radius,
            "coeff_bound": coeff_bound,
            "scoring_run": False,
            "local_search_run": False,
        },
    }
    duplicate_records = [
        {"source_label": source_label, **group}
        for group in summary["top_canonical_duplicate_groups"]
        + summary["top_exact_duplicate_groups"]
        + summary["top_token_duplicate_groups"]
    ]
    return summary, duplicate_records


def pairwise_overlap(source_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details = []
    canonical_sets = {
        source["label"]: set(source.get("canonical_hashes") or [])
        for source in source_summaries
    }
    exact_sets = {
        source["label"]: set(source.get("exact_coefficient_key_digests") or [])
        for source in source_summaries
    }
    for left, right in combinations(source_summaries, 2):
        left_label = left["label"]
        right_label = right["label"]
        details.append(
            {
                "left": left_label,
                "right": right_label,
                "shared_canonical_hashes": len(canonical_sets[left_label] & canonical_sets[right_label]),
                "shared_exact_coefficient_digests": len(exact_sets[left_label] & exact_sets[right_label]),
            }
        )
    return details


def build_summary(
    sample_exports: list[Path],
    *,
    labels: list[str] | None,
    translation_radius: int,
    coeff_bound: int | None,
    checkpoint_interval: int,
    top_n: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if labels is not None and len(labels) != len(sample_exports):
        raise ValueError("--labels must have the same length as sample exports")

    source_summaries: list[dict[str, Any]] = []
    duplicate_records: list[dict[str, Any]] = []
    for index, sample_export in enumerate(sample_exports):
        source_summary, source_duplicates = summarize_export(
            sample_export,
            label=labels[index] if labels is not None else None,
            translation_radius=translation_radius,
            coeff_bound=coeff_bound,
            checkpoint_interval=checkpoint_interval,
            top_n=top_n,
        )
        source_summaries.append(source_summary)
        duplicate_records.extend(source_duplicates)

    return (
        {
            "schema_version": 1,
            "record_type": "igp24_export_diversity_diagnostic",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "command": command_text(sys.argv),
            "safety": SAFETY,
            "source_count": len(source_summaries),
            "sources": source_summaries,
            "overlap": {
                "pairwise": pairwise_overlap(source_summaries),
            },
        },
        duplicate_records,
    )


def format_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Export Diversity Diagnostic",
        "",
        f"- Created UTC: `{summary.get('created_at_utc')}`",
        "- Safety: proxy-only diagnostic; no scoring, local search, exact verifier execution, SAIR calls, network calls, or submission.",
        "",
        "## Sources",
        "",
        "| label | records | decoded | invalid_decode | exact_unique | exact_dup_records | canonical_unique | canonical_dup_records | token_unique | token_dup_records |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source in summary.get("sources") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(source.get("label")),
                    str(source.get("records_read")),
                    str(source.get("decoded_records")),
                    str(source.get("invalid_decode_records")),
                    str(source.get("exact_unique_coefficients")),
                    str(source.get("exact_duplicate_records")),
                    str(source.get("canonical_unique_hashes")),
                    str(source.get("canonical_duplicate_records")),
                    str(source.get("token_unique_sequences")),
                    str(source.get("token_duplicate_records")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Top Canonical Duplicate Groups", ""])
    for source in summary.get("sources") or []:
        lines.append(f"### {source.get('label')}")
        groups = source.get("top_canonical_duplicate_groups") or []
        if not groups:
            lines.append("")
            lines.append("- No duplicate canonical groups in the top list.")
            lines.append("")
            continue
        lines.extend(["", "| rank | count | first_sample | last_sample | batches | canonical_hash |", "| ---: | ---: | ---: | ---: | --- | --- |"])
        for index, group in enumerate(groups, start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        str(group.get("count")),
                        str(group.get("first_sample_index")),
                        str(group.get("last_sample_index")),
                        ",".join(str(batch) for batch in group.get("batch_indices", [])),
                        str(group.get("canonical_hash")),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(["## Checkpoints", ""])
    for source in summary.get("sources") or []:
        checkpoints = source.get("checkpoints") or []
        if not checkpoints:
            continue
        lines.append(f"### {source.get('label')}")
        lines.extend(
            [
                "",
                "| decoded | last_sample | exact_unique | exact_dup_records | canonical_unique | canonical_dup_records |",
                "| ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for checkpoint in checkpoints:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(checkpoint.get("decoded_records")),
                        str(checkpoint.get("last_sample_index")),
                        str(checkpoint.get("exact_unique")),
                        str(checkpoint.get("exact_duplicate_records")),
                        str(checkpoint.get("canonical_unique")),
                        str(checkpoint.get("canonical_duplicate_records")),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def write_outputs(summary: dict[str, Any], duplicate_records: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "export_diversity_summary.json"
    report_path = output_dir / "export_diversity_report.md"
    duplicates_path = output_dir / "top_duplicate_groups.jsonl"
    summary["artifacts"] = {
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "top_duplicate_groups_path": str(duplicates_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")
    write_jsonl(duplicates_path, duplicate_records)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose raw IGP24 sample-export diversity without scoring")
    parser.add_argument("sample_exports", nargs="+", type=Path)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--labels", nargs="*", default=None, help="optional labels matching sample_exports")
    parser.add_argument("--translation_radius", type=int, default=2)
    parser.add_argument("--coeff_bound", type=int, default=4)
    parser.add_argument("--checkpoint_interval", type=int, default=256)
    parser.add_argument("--top_n", type=int, default=20)
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    start = time.perf_counter()
    try:
        summary, duplicate_records = build_summary(
            args.sample_exports,
            labels=args.labels,
            translation_radius=args.translation_radius,
            coeff_bound=args.coeff_bound,
            checkpoint_interval=args.checkpoint_interval,
            top_n=args.top_n,
        )
    except ValueError as exc:
        parser.error(str(exc))
    summary["runtime_seconds"] = time.perf_counter() - start
    write_outputs(summary, duplicate_records, args.output_dir.resolve())
    artifacts = summary["artifacts"]
    print(f"export diversity summary: {artifacts['summary_path']}")
    print(f"export diversity report: {artifacts['report_path']}")
    print(f"top duplicate groups: {artifacts['top_duplicate_groups_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
