#!/usr/bin/env python3
"""Extract SAIR-verified rows for group-index containment validation.

This helper joins accepted-feedback JSON files with their source selected
packet JSONL files, then emits rows with both a verified 24T label and modular
factorization degree patterns. The output is suitable for
``scripts/igp24_group_index_readiness_gate.py --historical_jsonl`` and
``scripts/igp24_candidate_group_compatibility.py --historical_validation``.

It is read-only. It does not call SAIR, run algebra systems, generate
candidates, or submit anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_replay_benchmark import (  # noqa: E402
    DEFAULT_REPLAY_FEEDBACKS,
    infer_source_selected_path,
)
from scripts.igp24_shortlist import get_source_commit  # noqa: E402


SUMMARY_JSON = "historical_group_validation_summary.json"
ROWS_JSONL = "historical_group_validation_rows.jsonl"
SKIPPED_JSONL = "historical_group_validation_skipped.jsonl"
REPORT_MD = "historical_group_validation_report.md"

SAFETY_NOTE = (
    "Read-only historical group-validation row extractor. It does not call "
    "SAIR/network APIs, run GAP/Magma/PARI, generate candidates, or submit anything."
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def nested_dict(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key)
    return value if isinstance(value, dict) else {}


def candidate_payload(row: dict[str, Any]) -> dict[str, Any]:
    candidate = nested_dict(row, "candidate")
    return candidate if candidate else row


def first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def canonical_hash(row: dict[str, Any]) -> str | None:
    candidate = candidate_payload(row)
    value = first_value(row.get("canonical_hash"), candidate.get("canonical_hash"), candidate.get("coefficient_hash"))
    return str(value) if value else None


def pattern_evidence(row: dict[str, Any]) -> list[dict[str, Any]]:
    candidate = candidate_payload(row)
    patterns = first_value(
        row.get("mod_p_factorization_degree_patterns"),
        candidate.get("mod_p_factorization_degree_patterns"),
    )
    out: list[dict[str, Any]] = []
    for item in patterns or []:
        if not isinstance(item, dict) or not isinstance(item.get("degrees"), list):
            continue
        prime = item.get("prime")
        out.append(
            {
                "prime": int(prime) if prime is not None else None,
                "degrees": [int(value) for value in item["degrees"]],
            }
        )
    return out


def index_selected_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[int, dict[str, Any]]]:
    by_hash: dict[str, dict[str, Any]] = {}
    by_index: dict[int, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        value = canonical_hash(row)
        if value and value not in by_hash:
            by_hash[value] = row
        by_index[index] = row
    return by_hash, by_index


def accepted_rows(feedback: dict[str, Any]) -> list[dict[str, Any]]:
    rows = feedback.get("accepted_rows") or feedback.get("rows") or []
    return [row for row in rows if isinstance(row, dict) and str(row.get("status") or "accepted") == "accepted"]


def match_selected(
    accepted: dict[str, Any],
    *,
    by_hash: dict[str, dict[str, Any]],
    by_index: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    value = canonical_hash(accepted)
    if value and value in by_hash:
        return by_hash[value], "canonical_hash"
    polynomial_index = accepted.get("polynomial_index")
    try:
        if polynomial_index is not None and int(polynomial_index) in by_index:
            return by_index[int(polynomial_index)], "polynomial_index"
    except (TypeError, ValueError):
        pass
    row_number = accepted.get("row_number") or accepted.get("submitted_line_number")
    try:
        if row_number is not None and int(row_number) - 1 in by_index:
            return by_index[int(row_number) - 1], "row_number"
    except (TypeError, ValueError):
        pass
    return None, None


def build_validation_row(
    accepted: dict[str, Any],
    selected: dict[str, Any],
    *,
    feedback_path: Path,
    selected_path: Path,
    match_method: str,
) -> dict[str, Any]:
    selected_candidate = candidate_payload(selected)
    metadata = nested_dict(selected_candidate, "generation_metadata")
    label = str(first_value(accepted.get("label"), accepted.get("verified_group_label")))
    r_value = first_value(accepted.get("r"), accepted.get("real_root_count"), selected_candidate.get("real_root_count"))
    hash_value = canonical_hash(accepted) or canonical_hash(selected)
    patterns = pattern_evidence(selected)
    return {
        "schema_version": 1,
        "record_type": "igp24_historical_group_validation_row",
        "label": label,
        "verified_group_label": label,
        "t": int(first_value(accepted.get("t"), label.removeprefix("24T"))),
        "r": int(r_value) if r_value is not None else None,
        "pair_key": first_value(accepted.get("pair_key"), f"{label}|r={int(r_value)}" if r_value is not None else None),
        "canonical_hash": hash_value,
        "short_hash": str(hash_value or "")[:12],
        "discriminant": first_value(selected_candidate.get("discriminant"), accepted.get("field_disc_abs"), accepted.get("fieldDiscAbs")),
        "field_disc_abs": first_value(accepted.get("field_disc_abs"), accepted.get("fieldDiscAbs")),
        "exported_coefficients": first_value(
            selected_candidate.get("exported_coefficients"),
            accepted.get("exported_coefficients"),
        ),
        "mod_p_factorization_degree_patterns": patterns,
        "mod_p_pattern_signature": first_value(
            selected_candidate.get("mod_p_pattern_signature"),
            accepted.get("mod_p_pattern_signature"),
        ),
        "construction_family": first_value(
            selected.get("features", {}).get("construction_family") if isinstance(selected.get("features"), dict) else None,
            metadata.get("construction_family"),
            accepted.get("construction_family"),
        ),
        "template_family_id": first_value(
            selected.get("features", {}).get("template_family_id") if isinstance(selected.get("features"), dict) else None,
            metadata.get("template_family_id"),
            accepted.get("template_family_id"),
        ),
        "perturbation_mode": first_value(
            selected.get("features", {}).get("perturbation_mode") if isinstance(selected.get("features"), dict) else None,
            metadata.get("perturbation_mode"),
            accepted.get("perturbation_mode"),
        ),
        "basin_fingerprint": first_value(
            selected.get("features", {}).get("basin_fingerprint") if isinstance(selected.get("features"), dict) else None,
            metadata.get("basin_fingerprint"),
            accepted.get("basin_fingerprint"),
        ),
        "source": {
            "feedback_path": rel(feedback_path),
            "selected_path": rel(selected_path),
            "submission_id": accepted.get("submission_id"),
            "submitted_at": accepted.get("submitted_at"),
            "row_number": accepted.get("row_number") or accepted.get("submitted_line_number"),
            "polynomial_index": accepted.get("polynomial_index"),
            "match_method": match_method,
        },
        "soundness": "sair_verified_label_plus_local_modular_factorization_evidence",
    }


def process_feedback(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    feedback = read_json(path)
    selected_path = infer_source_selected_path(path, feedback)
    accepted = accepted_rows(feedback)
    if selected_path is None or not selected_path.exists():
        skipped = [
            {
                "feedback_path": rel(path),
                "canonical_hash": canonical_hash(row),
                "label": row.get("label"),
                "reason": "missing_source_selected_jsonl",
            }
            for row in accepted
        ]
        return [], skipped, {"feedback_path": rel(path), "accepted_rows": len(accepted), "selected_rows": 0}
    selected_rows = read_jsonl(selected_path)
    by_hash, by_index = index_selected_rows(selected_rows)
    out: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in accepted:
        label = row.get("label")
        if not label:
            skipped.append({"feedback_path": rel(path), "canonical_hash": canonical_hash(row), "reason": "missing_label"})
            continue
        selected, method = match_selected(row, by_hash=by_hash, by_index=by_index)
        if selected is None or method is None:
            skipped.append(
                {
                    "feedback_path": rel(path),
                    "canonical_hash": canonical_hash(row),
                    "label": label,
                    "reason": "selected_row_not_matched",
                }
            )
            continue
        patterns = pattern_evidence(selected)
        if not patterns:
            skipped.append(
                {
                    "feedback_path": rel(path),
                    "selected_path": rel(selected_path),
                    "canonical_hash": canonical_hash(row),
                    "label": label,
                    "reason": "missing_modular_factorization_evidence",
                }
            )
            continue
        validation_row = build_validation_row(
            row,
            selected,
            feedback_path=path,
            selected_path=selected_path,
            match_method=method,
        )
        key = (str(validation_row["canonical_hash"]), str(validation_row["label"]))
        if key in seen:
            skipped.append(
                {
                    "feedback_path": rel(path),
                    "canonical_hash": validation_row["canonical_hash"],
                    "label": label,
                    "reason": "duplicate_hash_label",
                }
            )
            continue
        seen.add(key)
        out.append(validation_row)
    return out, skipped, {
        "feedback_path": rel(path),
        "selected_path": rel(selected_path),
        "accepted_rows": len(accepted),
        "selected_rows": len(selected_rows),
        "validation_rows": len(out),
        "skipped_rows": len(skipped),
    }


def summarize(
    *,
    feedback_paths: list[Path],
    rows: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    per_feedback: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    label_counts = Counter(str(row.get("label")) for row in rows)
    pair_counts = Counter(str(row.get("pair_key")) for row in rows)
    skip_counts = Counter(str(row.get("reason")) for row in skipped)
    return {
        "schema_version": 1,
        "record_type": "igp24_historical_group_validation_extract",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_historical_group_validation_rows.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "input_feedback_paths": [rel(path) for path in feedback_paths],
        "feedback_file_count": len(feedback_paths),
        "accepted_rows_seen": sum(int(item.get("accepted_rows") or 0) for item in per_feedback),
        "validation_row_count": len(rows),
        "skipped_row_count": len(skipped),
        "skip_reason_counts": dict(sorted(skip_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "pair_counts": dict(sorted(pair_counts.items())),
        "per_feedback": per_feedback,
        "output_files": {
            "summary_json": str(output_dir / SUMMARY_JSON),
            "rows_jsonl": str(output_dir / ROWS_JSONL),
            "skipped_jsonl": str(output_dir / SKIPPED_JSONL),
            "report_md": str(output_dir / REPORT_MD),
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Historical Group-Validation Rows",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Feedback files: `{summary['feedback_file_count']}`",
        f"- Accepted rows seen: `{summary['accepted_rows_seen']}`",
        f"- Validation rows: `{summary['validation_row_count']}`",
        f"- Skipped rows: `{summary['skipped_row_count']}`",
        f"- Skip reasons: `{summary['skip_reason_counts']}`",
        f"- Labels: `{summary['label_counts']}`",
        f"- Safety: {summary['safety_note']}",
        "",
        "Rows in `historical_group_validation_rows.jsonl` have SAIR-verified labels joined to local modular factorization evidence. They are containment-test inputs, not exact verifier outputs.",
        "",
        "## Per Feedback",
        "",
        "| feedback | accepted | selected | validation | skipped |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["per_feedback"]:
        lines.append(
            f"| `{item.get('feedback_path')}` | {item.get('accepted_rows')} | {item.get('selected_rows')} | "
            f"{item.get('validation_rows')} | {item.get('skipped_rows')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], rows: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / ROWS_JSONL, rows)
    write_jsonl(output_dir / SKIPPED_JSONL, skipped)
    (output_dir / REPORT_MD).write_text(render_report(summary), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted_feedback_json", type=Path, action="append")
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    feedback_paths = args.accepted_feedback_json or list(DEFAULT_REPLAY_FEEDBACKS)
    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    per_feedback: list[dict[str, Any]] = []
    for path in feedback_paths:
        if not path.exists():
            skipped.append({"feedback_path": rel(path), "reason": "feedback_file_missing"})
            per_feedback.append({"feedback_path": rel(path), "accepted_rows": 0, "selected_rows": 0, "validation_rows": 0, "skipped_rows": 1})
            continue
        extracted, skipped_rows, stats = process_feedback(path)
        rows.extend(extracted)
        skipped.extend(skipped_rows)
        per_feedback.append(stats)
    summary = summarize(
        feedback_paths=feedback_paths,
        rows=rows,
        skipped=skipped,
        per_feedback=per_feedback,
        output_dir=args.output_dir,
    )
    write_outputs(args.output_dir, summary=summary, rows=rows, skipped=skipped)
    print(f"feedback_file_count {summary['feedback_file_count']}")
    print(f"accepted_rows_seen {summary['accepted_rows_seen']}")
    print(f"validation_row_count {summary['validation_row_count']}")
    print(f"skipped_row_count {summary['skipped_row_count']}")
    print(f"skip_reason_counts {json.dumps(summary['skip_reason_counts'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
