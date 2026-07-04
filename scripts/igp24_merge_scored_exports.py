#!/usr/bin/env python3
"""Merge scored IGP24 sample exports with canonical-hash dedup reporting."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_OUTPUT_DIR = Path("/tmp/igp24_merged_scored_exports_20260704")
SAFETY = {
    "proxy_only": True,
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


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def default_label(source_path: Path) -> str:
    if source_path.is_dir() and source_path.name == "cpu_scored_export_all":
        return source_path.parent.name
    return source_path.stem if source_path.is_file() else source_path.name


def scored_jsonl_path(source_path: Path) -> Path:
    return source_path / "scored_samples.jsonl" if source_path.is_dir() else source_path


def maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = [record.get("canonical_hash") for record in records if record.get("canonical_hash")]
    hash_counts = Counter(hashes)
    duplicate_hashes = {hash_value: count for hash_value, count in hash_counts.items() if count > 1}
    scores = [score for score in (maybe_float(record.get("score")) for record in records) if score is not None]
    valid = [record for record in records if record.get("verification_status") == "proxy_scored"]
    rejected = [record for record in records if record.get("verification_status") == "rejected"]
    return {
        "scored_records": len(records),
        "valid_records": len(valid),
        "rejected_records": len(rejected),
        "canonical_hash_records": len(hashes),
        "unique_canonical_hashes": len(hash_counts),
        "duplicate_canonical_hash_records": len(hashes) - len(hash_counts),
        "duplicate_canonical_hashes": len(duplicate_hashes),
        "best_score": max(scores) if scores else None,
        "mean_score": (sum(scores) / len(scores)) if scores else None,
    }


def load_score_source(source_path: Path, label: str | None = None) -> dict[str, Any]:
    source_path = source_path.resolve()
    scored_path = scored_jsonl_path(source_path)
    if not scored_path.exists():
        raise FileNotFoundError(f"missing scored JSONL: {scored_path}")

    source_dir = source_path if source_path.is_dir() else source_path.parent
    summary_path = source_dir / "score_summary.json"
    manifest_path = source_dir / "split_workflow_manifest.json"
    split_report_path = source_dir / "split_workflow_report.md"
    score_report_path = source_dir / "score_report.md"
    records = read_jsonl(scored_path)
    source_label = label or default_label(source_path)
    hashes = {record.get("canonical_hash") for record in records if record.get("canonical_hash")}
    return {
        "label": source_label,
        "source_path": str(source_path),
        "scored_jsonl_path": str(scored_path),
        "score_summary_path": str(summary_path) if summary_path.exists() else None,
        "score_report_path": str(score_report_path) if score_report_path.exists() else None,
        "split_manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "split_report_path": str(split_report_path) if split_report_path.exists() else None,
        "score_summary": read_json(summary_path) or {},
        "split_manifest": read_json(manifest_path) or {},
        "records": records,
        "hashes": hashes,
        "record_summary": summarize_records(records),
    }


def top_candidate_projection(record: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    projected: dict[str, Any] = {
        "source_label": source["label"],
        "source_scored_jsonl_path": source["scored_jsonl_path"],
        "canonical_hash": record.get("canonical_hash"),
        "score": record.get("score"),
        "verification_status": record.get("verification_status"),
    }
    for key in [
        "decoded_coefficients",
        "exported_coefficients",
        "coefficients",
        "real_root_count",
        "score_components",
        "generation_metadata",
        "analysis",
    ]:
        if key in record:
            projected[key] = record[key]
    return projected


def source_artifacts(source: dict[str, Any]) -> dict[str, Any]:
    manifest_artifacts = (source.get("split_manifest") or {}).get("artifacts") or {}
    return {
        "label": source["label"],
        "source_path": source["source_path"],
        "scored_jsonl_path": source["scored_jsonl_path"],
        "score_summary_path": source["score_summary_path"],
        "score_report_path": source["score_report_path"],
        "split_manifest_path": source["split_manifest_path"],
        "split_report_path": source["split_report_path"],
        "sample_export_path": manifest_artifacts.get("sample_export_path"),
        "gpu_probe_summary_path": manifest_artifacts.get("gpu_probe_summary_path"),
        "gpu_probe_report_path": manifest_artifacts.get("gpu_probe_report_path"),
        "train_log_path": manifest_artifacts.get("train_log_path"),
    }


def merge_sources(
    score_sources: list[Path],
    *,
    labels: list[str] | None = None,
    top_n: int = 25,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if labels is not None and len(labels) != len(score_sources):
        raise ValueError("--labels must have the same length as score sources")

    sources = [
        load_score_source(source_path, labels[index] if labels is not None else None)
        for index, source_path in enumerate(score_sources)
    ]
    all_records_with_sources: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for source in sources:
        all_records_with_sources.extend((record, source) for record in source["records"])

    all_records = [record for record, _source in all_records_with_sources]
    combined_summary = summarize_records(all_records)
    source_hashes = {source["label"]: set(source["hashes"]) for source in sources}
    pairwise_overlap = [
        {
            "left": left_label,
            "right": right_label,
            "shared_hashes": len(source_hashes[left_label] & source_hashes[right_label]),
        }
        for left_label, right_label in combinations(source_hashes, 2)
    ]

    hash_sources: dict[str, set[str]] = defaultdict(set)
    for source in sources:
        for hash_value in source["hashes"]:
            hash_sources[hash_value].add(source["label"])
    combined_summary["hashes_seen_in_multiple_sources"] = sum(
        1 for labels_for_hash in hash_sources.values() if len(labels_for_hash) > 1
    )

    best_by_hash: dict[str, tuple[float | None, dict[str, Any], dict[str, Any]]] = {}
    for record, source in all_records_with_sources:
        hash_value = record.get("canonical_hash")
        if not hash_value:
            continue
        score = maybe_float(record.get("score"))
        previous = best_by_hash.get(hash_value)
        if previous is None or (score is not None and (previous[0] is None or score > previous[0])):
            best_by_hash[hash_value] = (score, record, source)

    top_records = sorted(
        best_by_hash.values(),
        key=lambda item: (item[0] is not None, item[0] if item[0] is not None else float("-inf")),
        reverse=True,
    )[:top_n]
    top_candidates = [top_candidate_projection(record, source) for _score, record, source in top_records]

    summary = {
        "schema_version": 1,
        "record_type": "igp24_merged_scored_exports",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "safety": SAFETY,
        "source_count": len(sources),
        "top_n": top_n,
        "combined": combined_summary,
        "overlap": {
            "pairwise": pairwise_overlap,
            "hashes_seen_in_multiple_sources": combined_summary["hashes_seen_in_multiple_sources"],
        },
        "sources": [
            {
                "label": source["label"],
                "artifacts": source_artifacts(source),
                "record_summary": source["record_summary"],
                "gpu_phase": (source.get("split_manifest") or {}).get("gpu_phase") or {},
                "cpu_phase": (source.get("split_manifest") or {}).get("cpu_phase") or {},
            }
            for source in sources
        ],
        "top_deduped_candidates": top_candidates,
    }
    return summary, top_candidates


def format_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_report(summary: dict[str, Any]) -> str:
    combined = summary.get("combined") or {}
    lines = [
        "# IGP24 Merged Scored Export Report",
        "",
        f"- Created UTC: `{summary.get('created_at_utc')}`",
        "- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.",
        "",
        "## Combined",
        "",
        "| sources | scored | valid | rejected | unique_hashes | duplicate_hash_records | cross_seed_hashes | best_score | mean_score |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| "
        + " | ".join(
            [
                str(summary.get("source_count")),
                str(combined.get("scored_records")),
                str(combined.get("valid_records")),
                str(combined.get("rejected_records")),
                str(combined.get("unique_canonical_hashes")),
                str(combined.get("duplicate_canonical_hash_records")),
                str(combined.get("hashes_seen_in_multiple_sources")),
                format_number(combined.get("best_score")),
                format_number(combined.get("mean_score")),
            ]
        )
        + " |",
        "",
        "## Sources",
        "",
        "| label | scored | valid | rejected | unique_hashes | duplicate_hash_records | best_score | mean_score |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source in summary.get("sources") or []:
        record_summary = source.get("record_summary") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(source.get("label")),
                    str(record_summary.get("scored_records")),
                    str(record_summary.get("valid_records")),
                    str(record_summary.get("rejected_records")),
                    str(record_summary.get("unique_canonical_hashes")),
                    str(record_summary.get("duplicate_canonical_hash_records")),
                    format_number(record_summary.get("best_score")),
                    format_number(record_summary.get("mean_score")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Cross-Seed Overlap", "", "| left | right | shared_hashes |", "| --- | --- | ---: |"])
    for pair in (summary.get("overlap") or {}).get("pairwise") or []:
        lines.append(f"| {pair.get('left')} | {pair.get('right')} | {pair.get('shared_hashes')} |")

    lines.extend(["", "## Top Deduped Candidates", "", "| rank | source | score | status | canonical_hash |", "| ---: | --- | ---: | --- | --- |"])
    for index, record in enumerate(summary.get("top_deduped_candidates") or [], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    str(record.get("source_label")),
                    format_number(record.get("score")),
                    str(record.get("verification_status")),
                    str(record.get("canonical_hash")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Artifacts", ""])
    for source in summary.get("sources") or []:
        artifacts = source.get("artifacts") or {}
        lines.append(f"- {source.get('label')}: `{artifacts.get('scored_jsonl_path')}`")
    lines.append("")
    return "\n".join(lines)


def write_outputs(summary: dict[str, Any], top_candidates: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "merged_dedup_summary.json"
    report_path = output_dir / "merged_dedup_report.md"
    top_path = output_dir / "top_deduped_candidates.jsonl"
    summary["artifacts"] = {
        "merged_summary_path": str(summary_path),
        "merged_report_path": str(report_path),
        "top_deduped_candidates_path": str(top_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")
    write_jsonl(top_path, top_candidates)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge scored IGP24 exports and report hash dedup/overlap")
    parser.add_argument("score_sources", nargs="+", type=Path, help="scored JSONL files or score output directories")
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--labels", nargs="*", default=None, help="optional labels matching score_sources")
    parser.add_argument("--top_n", type=int, default=25)
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    try:
        summary, top_candidates = merge_sources(args.score_sources, labels=args.labels, top_n=args.top_n)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    write_outputs(summary, top_candidates, args.output_dir.resolve())
    artifacts = summary["artifacts"]
    print(f"merged summary: {artifacts['merged_summary_path']}")
    print(f"merged report: {artifacts['merged_report_path']}")
    print(f"top candidates: {artifacts['top_deduped_candidates_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
