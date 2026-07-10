#!/usr/bin/env python3
"""Build exact-label construction-route outcome ledgers.

This helper distills score-aware triage rows into route-level outcomes. It is
local/file-only and does not call SAIR, online calculators, Magma, PARI, GAP,
GPU training, or candidate generation.
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

from scripts.igp24_shortlist import get_source_commit, read_jsonl  # noqa: E402

ROWS_JSONL = "construction_outcome_rows.jsonl"
ROUTE_OUTCOMES_JSONL = "construction_route_outcomes.jsonl"
SUMMARY_JSON = "construction_outcome_ledger_summary.json"
REPORT_MD = "construction_outcome_ledger_report.md"

SAFETY_NOTE = (
    "Construction outcome ledger is local/file-only. It reads exact-label "
    "triage artifacts and writes route outcome summaries; it does not submit "
    "to SAIR or execute algebra systems."
)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _short_hash(row: dict[str, Any]) -> str:
    return str(row.get("short_hash") or str(row.get("canonical_hash") or row.get("candidate_hash") or "")[:12])


def _route_metadata(row: dict[str, Any]) -> dict[str, Any]:
    route = row.get("route") if isinstance(row.get("route"), dict) else {}
    metadata = row.get("target_metadata") if isinstance(row.get("target_metadata"), dict) else {}
    intended_label = route.get("label") or metadata.get("target_t")
    intended_r = route.get("r") or metadata.get("target_r")
    intended_pair = route.get("pair_key")
    if intended_pair is None and intended_label and intended_r is not None:
        intended_pair = f"{intended_label}|r={int(intended_r)}"
    return {
        "family": route.get("family") or row.get("source_strategy") or row.get("construction_family"),
        "intended_pair_key": intended_pair,
        "intended_label": intended_label,
        "intended_r": int(intended_r) if intended_r is not None else None,
        "route_soundness": route.get("soundness"),
        "target_group_block_sizes": route.get("target_group_block_sizes") or [],
    }


def classify_outcome(row: dict[str, Any], *, intended_pair: str | None, observed_pair: str | None) -> str:
    if row.get("known_submission_hash_match"):
        return "known_submission_hash"
    if not row.get("verified_group_label"):
        return "exact_label_missing"
    if not intended_pair:
        return "exact_label_no_intended_route"
    if observed_pair == intended_pair:
        return "exact_target_submission_grade" if row.get("submission_grade_candidate") else "exact_target_not_submission_grade"
    if row.get("score_aware_classification") == "sair_discovered_pair_not_improved":
        return "false_target_discovered_not_improved"
    if row.get("sair_progress_state") == "allowed_discovered":
        return "false_target_discovered"
    if row.get("sair_progress_state") == "allowed_remaining":
        return "false_target_uncovered"
    return "false_target_other"


def row_from_triage(raw: dict[str, Any], *, source_path: Path, source_row: int) -> dict[str, Any]:
    route = _route_metadata(raw)
    observed_pair = raw.get("pair_key")
    outcome = classify_outcome(raw, intended_pair=route["intended_pair_key"], observed_pair=observed_pair)
    exact_label_present = bool(raw.get("verified_group_label"))
    target_hit = bool(route["intended_pair_key"] and observed_pair == route["intended_pair_key"])
    false_target = bool(exact_label_present and route["intended_pair_key"] and observed_pair != route["intended_pair_key"])
    return {
        "record_type": "igp24_construction_outcome_row",
        "schema_version": 1,
        "source_triage_jsonl": str(source_path),
        "source_triage_row": int(source_row),
        "canonical_hash": raw.get("canonical_hash") or raw.get("candidate_hash"),
        "short_hash": _short_hash(raw),
        "family": route["family"],
        "intended_pair_key": route["intended_pair_key"],
        "intended_label": route["intended_label"],
        "intended_r": route["intended_r"],
        "observed_pair_key": observed_pair,
        "observed_label": raw.get("verified_group_label"),
        "observed_r": raw.get("computed_r") or raw.get("signature_r"),
        "target_hit": target_hit,
        "false_target": false_target,
        "exact_label_present": exact_label_present,
        "exact_nfdisc_abs": raw.get("exact_nfdisc_abs"),
        "score_aware_classification": raw.get("score_aware_classification"),
        "sair_progress_state": raw.get("sair_progress_state"),
        "sair_score_value_status": raw.get("sair_score_value_status"),
        "sair_progress_team_count": raw.get("sair_progress_team_count"),
        "sair_progress_discriminant_status": raw.get("sair_progress_discriminant_status"),
        "submission_grade_candidate": bool(raw.get("submission_grade_candidate")),
        "known_submission_hash_match": bool(raw.get("known_submission_hash_match")),
        "route_soundness": route["route_soundness"],
        "target_group_block_sizes": route["target_group_block_sizes"],
        "outcome_class": outcome,
    }


def route_key(row: dict[str, Any]) -> str:
    return f"{row.get('intended_pair_key') or 'unknown'}::{row.get('family') or 'unknown'}"


def summarize_route(rows: list[dict[str, Any]], *, min_exact_rows_to_block: int) -> dict[str, Any]:
    first = rows[0]
    exact_rows = [row for row in rows if row.get("exact_label_present")]
    target_hits = [row for row in rows if row.get("target_hit")]
    false_targets = [row for row in rows if row.get("false_target")]
    submission_grade = [row for row in rows if row.get("submission_grade_candidate")]
    classes = Counter(str(row.get("outcome_class")) for row in rows)
    observed_pairs = Counter(str(row.get("observed_pair_key")) for row in rows if row.get("observed_pair_key"))
    observed_labels = Counter(str(row.get("observed_label")) for row in rows if row.get("observed_label"))
    exact_count = len(exact_rows)
    target_hit_rate = (len(target_hits) / exact_count) if exact_count else None
    if exact_count == 0:
        route_outcome = "pending_exact_labels"
        action = "review_only_pending_exact_labels"
    elif target_hits:
        route_outcome = "has_exact_target_hits"
        action = "keep_with_exact_target_hit_review"
    elif len(false_targets) == exact_count and classes == Counter({"false_target_discovered_not_improved": exact_count}):
        route_outcome = "all_false_target_discovered_not_improved"
        action = "block_repeat_exact_basin" if exact_count >= min_exact_rows_to_block else "review_only_more_exact_rows_needed"
    elif len(false_targets) == exact_count:
        route_outcome = "all_false_target"
        action = "block_repeat_exact_basin" if exact_count >= min_exact_rows_to_block else "review_only_more_exact_rows_needed"
    else:
        route_outcome = "mixed_or_incomplete_exact_outcomes"
        action = "review_only"
    return {
        "record_type": "igp24_construction_route_outcome",
        "schema_version": 1,
        "route_key": route_key(first),
        "family": first.get("family"),
        "intended_pair_key": first.get("intended_pair_key"),
        "intended_label": first.get("intended_label"),
        "intended_r": first.get("intended_r"),
        "row_count": len(rows),
        "exact_label_row_count": exact_count,
        "target_hit_count": len(target_hits),
        "false_target_count": len(false_targets),
        "submission_grade_count": len(submission_grade),
        "known_submission_hash_count": sum(1 for row in rows if row.get("known_submission_hash_match")),
        "target_hit_rate": target_hit_rate,
        "outcome_class_counts": dict(sorted(classes.items())),
        "observed_pair_counts": dict(sorted(observed_pairs.items())),
        "observed_label_counts": dict(sorted(observed_labels.items())),
        "route_outcome": route_outcome,
        "recommended_route_action": action,
        "block_repeat_exact_basin": action == "block_repeat_exact_basin",
        "blocking_reason": "exact_route_false_target_outcome" if action == "block_repeat_exact_basin" else None,
        "soundness": "exact_label_route_outcome_not_group_proof",
    }


def build_ledger(
    triage_paths: list[Path],
    *,
    min_exact_rows_to_block: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    for path in triage_paths:
        resolved = path.resolve()
        loaded = read_jsonl(resolved)
        for index, raw in enumerate(loaded, start=1):
            rows.append(row_from_triage(raw, source_path=resolved, source_row=index))
        inputs.append({"path": str(resolved), "rows_loaded": len(loaded)})
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[route_key(row)].append(row)
    route_outcomes = [
        summarize_route(route_rows, min_exact_rows_to_block=min_exact_rows_to_block)
        for _key, route_rows in sorted(grouped.items())
    ]
    summary = {
        "record_type": "igp24_construction_outcome_ledger_summary",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_construction_outcome_ledger.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "safety_note": SAFETY_NOTE,
        "inputs": inputs,
        "min_exact_rows_to_block": int(min_exact_rows_to_block),
        "row_count": len(rows),
        "route_count": len(route_outcomes),
        "exact_label_row_count": sum(1 for row in rows if row.get("exact_label_present")),
        "target_hit_row_count": sum(1 for row in rows if row.get("target_hit")),
        "false_target_row_count": sum(1 for row in rows if row.get("false_target")),
        "submission_grade_row_count": sum(1 for row in rows if row.get("submission_grade_candidate")),
        "outcome_class_counts": dict(sorted(Counter(str(row.get("outcome_class")) for row in rows).items())),
        "route_outcome_counts": dict(sorted(Counter(str(row.get("route_outcome")) for row in route_outcomes).items())),
        "recommended_route_action_counts": dict(
            sorted(Counter(str(row.get("recommended_route_action")) for row in route_outcomes).items())
        ),
        "blocked_route_count": sum(1 for row in route_outcomes if row.get("block_repeat_exact_basin")),
        "blocked_routes": [
            {
                "intended_pair_key": row.get("intended_pair_key"),
                "family": row.get("family"),
                "exact_label_row_count": row.get("exact_label_row_count"),
                "observed_pair_counts": row.get("observed_pair_counts"),
            }
            for row in route_outcomes
            if row.get("block_repeat_exact_basin")
        ],
        "output_files": {},
    }
    return rows, route_outcomes, summary


def render_report(summary: dict[str, Any], route_outcomes: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Construction Outcome Ledger",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Rows: `{summary['row_count']}`",
        f"- Routes: `{summary['route_count']}`",
        f"- Exact-label rows: `{summary['exact_label_row_count']}`",
        f"- Target-hit rows: `{summary['target_hit_row_count']}`",
        f"- False-target rows: `{summary['false_target_row_count']}`",
        f"- Submission-grade rows: `{summary['submission_grade_row_count']}`",
        f"- Outcome classes: `{json.dumps(summary['outcome_class_counts'], sort_keys=True)}`",
        f"- Recommended actions: `{json.dumps(summary['recommended_route_action_counts'], sort_keys=True)}`",
        f"- Safety: {summary['safety_note']}",
        "",
        "## Route Outcomes",
        "",
        "| route | family | rows | target hits | false targets | action | observed pairs |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in route_outcomes:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('intended_pair_key')}`",
                    f"`{row.get('family')}`",
                    str(row.get("exact_label_row_count")),
                    str(row.get("target_hit_count")),
                    str(row.get("false_target_count")),
                    f"`{row.get('recommended_route_action')}`",
                    f"`{json.dumps(row.get('observed_pair_counts'), sort_keys=True)}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "A blocked route here means an exact-label reviewed basin missed its intended target on every exact row. "
            "It does not prove the target impossible; it says not to repeat the same exact basin without a material structural change.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output_dir: Path, rows: list[dict[str, Any]], route_outcomes: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "rows_jsonl": output_dir / ROWS_JSONL,
        "route_outcomes_jsonl": output_dir / ROUTE_OUTCOMES_JSONL,
        "summary_json": output_dir / SUMMARY_JSON,
        "report_md": output_dir / REPORT_MD,
    }
    summary["output_files"] = {key: str(value) for key, value in paths.items()}
    write_jsonl(paths["rows_jsonl"], rows)
    write_jsonl(paths["route_outcomes_jsonl"], route_outcomes)
    write_json(paths["summary_json"], summary)
    paths["report_md"].write_text(render_report(summary, route_outcomes), encoding="utf-8")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--min_exact_rows_to_block", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows, route_outcomes, summary = build_ledger(
        [path.resolve() for path in args.triage_jsonl],
        min_exact_rows_to_block=int(args.min_exact_rows_to_block),
    )
    paths = write_outputs(args.output_dir.resolve(), rows, route_outcomes, summary)
    print(f"row_count\t{summary['row_count']}")
    print(f"route_count\t{summary['route_count']}")
    print(f"blocked_route_count\t{summary['blocked_route_count']}")
    print(f"outcome_class_counts\t{json.dumps(summary['outcome_class_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
