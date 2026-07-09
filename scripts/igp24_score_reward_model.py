#!/usr/bin/env python3
"""Score IGP24 candidate rows with the advisory reward/collapse-risk model."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.igp24.reward_model import (  # noqa: E402
    AdvisoryRewardModel,
    COLLAPSE_RISK_OUTCOMES,
    POSITIVE_OUTCOMES,
    group_family_from_record,
    outcome_from_record,
    read_jsonl,
    write_json,
    write_jsonl,
)

DEFAULT_MODEL = REPO_ROOT / "data/igp24/remediation_20260709/reward_model_phase2/reward_model.json"
DEFAULT_INPUT = REPO_ROOT / "data/igp24/active_learning/axg_training_dataset_20260709_axg113_high_real.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/remediation_20260709/reward_model_phase2/scored_training_rows"


def load_model(path: Path) -> AdvisoryRewardModel:
    return AdvisoryRewardModel.from_json(json.loads(path.read_text(encoding="utf-8")))


def score_rows(model: AdvisoryRewardModel, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    for index, row in enumerate(rows):
        prediction = model.predict(row)
        outcome = outcome_from_record(row)
        family = group_family_from_record(row)
        decision_counts[prediction.decision] += 1
        outcome_counts[outcome] += 1
        family_counts[family] += 1
        scored.append(
            {
                "row_index": index,
                "canonical_hash": row.get("canonical_hash"),
                "dataset_row_id": row.get("dataset_row_id"),
                "observed_outcome": outcome,
                "family": family,
                "r": row.get("r"),
                "features": row.get("features"),
                "reward_model": prediction.as_dict(),
            }
        )
    reward_ranked_rows = sorted(
        (
            {
                "row_index": row["row_index"],
                "canonical_hash": row["canonical_hash"],
                "observed_outcome": row["observed_outcome"],
                "family": row["family"],
                "reward_probability": row["reward_model"]["reward_probability"],
                "collapse_risk_probability": row["reward_model"]["collapse_risk_probability"],
                "decision": row["reward_model"]["decision"],
            }
            for row in scored
        ),
        key=lambda item: (-float(item["reward_probability"]), float(item["collapse_risk_probability"])),
    )
    collapse_ranked_rows = sorted(
        (
            {
                "row_index": row["row_index"],
                "canonical_hash": row["canonical_hash"],
                "observed_outcome": row["observed_outcome"],
                "family": row["family"],
                "reward_probability": row["reward_model"]["reward_probability"],
                "collapse_risk_probability": row["reward_model"]["collapse_risk_probability"],
                "decision": row["reward_model"]["decision"],
            }
            for row in scored
        ),
        key=lambda item: (-float(item["collapse_risk_probability"]), -float(item["reward_probability"])),
    )
    top_reward_rows = reward_ranked_rows[:50]
    top_reward_known_risk_rows = [row for row in top_reward_rows if row["observed_outcome"] in COLLAPSE_RISK_OUTCOMES]
    summary = {
        "schema_version": 1,
        "record_type": "igp24_reward_model_score_summary",
        "row_count": len(rows),
        "decision_counts": dict(sorted(decision_counts.items())),
        "observed_outcome_counts": dict(sorted(outcome_counts.items())),
        "top_families": dict(family_counts.most_common(20)),
        "top_reward_rows": top_reward_rows,
        "top_reward_known_risk_count": len(top_reward_known_risk_rows),
        "top_reward_known_risk_rows": top_reward_known_risk_rows[:20],
        "top_reward_safe_or_unknown_rows": [
            row for row in reward_ranked_rows if row["observed_outcome"] in POSITIVE_OUTCOMES or row["observed_outcome"] == "unknown"
        ][:50],
        "top_collapse_risk_rows": collapse_ranked_rows[:50],
    }
    return scored, summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# IGP24 Reward Model Scoring Report",
        "",
        f"- Rows scored: `{summary['row_count']}`",
        f"- Decision counts: `{json.dumps(summary['decision_counts'], sort_keys=True)}`",
        f"- Observed outcome counts: `{json.dumps(summary['observed_outcome_counts'], sort_keys=True)}`",
        f"- Known risk rows among top 50 reward-ranked rows: `{summary['top_reward_known_risk_count']}`",
        "",
        "## Top Reward Rows",
        "",
        "| row | outcome | reward p | collapse p | decision | family |",
        "| ---: | --- | ---: | ---: | --- | --- |",
    ]
    for row in summary["top_reward_rows"][:20]:
        lines.append(
            f"| {row['row_index']} | `{row['observed_outcome']}` | "
            f"{float(row['reward_probability']):.3f} | {float(row['collapse_risk_probability']):.3f} | "
            f"`{row['decision']}` | `{row['family']}` |"
        )
    if summary["top_reward_known_risk_rows"]:
        lines.extend(
            [
                "",
                "## Reward-Rank False-Positive Warning",
                "",
                "Known risk rows still appear in the reward-ranked shortlist. Treat the model as advisory until group compatibility and richer labels are available.",
                "",
                "| row | outcome | reward p | collapse p | decision | family |",
                "| ---: | --- | ---: | ---: | --- | --- |",
            ]
        )
        for row in summary["top_reward_known_risk_rows"][:20]:
            lines.append(
                f"| {row['row_index']} | `{row['observed_outcome']}` | "
                f"{float(row['reward_probability']):.3f} | {float(row['collapse_risk_probability']):.3f} | "
                f"`{row['decision']}` | `{row['family']}` |"
            )
    lines.extend(
        [
            "",
            "## Top Collapse-Risk Rows",
            "",
            "| row | outcome | reward p | collapse p | decision | family |",
            "| ---: | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in summary["top_collapse_risk_rows"][:20]:
        lines.append(
            f"| {row['row_index']} | `{row['observed_outcome']}` | "
            f"{float(row['reward_probability']):.3f} | {float(row['collapse_risk_probability']):.3f} | "
            f"`{row['decision']}` | `{row['family']}` |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_json", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--input_jsonl", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    model = load_model(args.model_json)
    rows = read_jsonl(args.input_jsonl)
    scored, summary = score_rows(model, rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "reward_model_scored_rows.jsonl", scored)
    write_json(args.output_dir / "reward_model_score_summary.json", summary)
    write_report(args.output_dir / "reward_model_score_report.md", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
