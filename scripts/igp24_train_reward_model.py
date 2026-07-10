#!/usr/bin/env python3
"""Train the Phase 2 advisory IGP24 reward/collapse-risk model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.reward_model import (  # noqa: E402
    build_training_artifacts,
    read_jsonl,
    write_json,
)

DEFAULT_DATASET = REPO_ROOT / "data/igp24/active_learning/axg_training_dataset_20260709_axg113_high_real.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/remediation_20260709/reward_model_phase2"


def _format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_report(path: Path, *, manifest: dict[str, Any], metrics: dict[str, Any]) -> None:
    eval_metrics = metrics["eval"]
    all_calibration = metrics["all_records"]["calibration"]
    positive = metrics["positive_vs_crowded"]
    family_risk = metrics["family_risk_ranking"][:10]

    lines = [
        "# IGP24 Phase 2 Reward/Risk Model",
        "",
        f"- Created UTC: `{manifest['created_at']}`",
        f"- Source dataset: `{manifest.get('source_path')}`",
        f"- Rows: `{manifest['row_count']}`",
        f"- Advisory status: `{manifest['advisory_status']}`",
        f"- Train rows: `{manifest['split']['train_rows']}`",
        f"- Eval rows: `{manifest['split']['eval_rows']}`",
        f"- Train/eval group overlap: `{manifest['split']['group_overlap']}`",
        f"- Outcome counts: `{json.dumps(manifest['outcome_counts'], sort_keys=True)}`",
        "",
        "## Eval Metrics",
        "",
        f"- Supervised eval rows: `{eval_metrics['supervised_evaluated_count']}`",
        f"- Unknown eval rows excluded: `{eval_metrics['unknown_excluded_count']}`",
        f"- Mean uncertainty entropy: `{_format_metric(eval_metrics['calibration']['mean_entropy'])}`",
        f"- Abstention rate: `{_format_metric(eval_metrics['calibration']['abstention_rate'])}`",
        "",
        "## Per-Class Eval Metrics",
        "",
        "| class | precision | recall | f1 | support |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, row in sorted(eval_metrics["per_class_metrics"].items()):
        lines.append(
            f"| `{label}` | {_format_metric(row['precision'])} | {_format_metric(row['recall'])} | "
            f"{_format_metric(row['f1'])} | {row['support']} |"
        )
    lines.extend(
        [
            "",
            "## Uncertainty",
            "",
            f"- All-record evaluated rows: `{all_calibration['evaluated_count']}`",
            f"- All-record mean entropy: `{_format_metric(all_calibration['mean_entropy'])}`",
            f"- All-record abstention rate: `{_format_metric(all_calibration['abstention_rate'])}`",
            "",
            "## Positive vs Crowded Diagnostic",
            "",
            f"- Score-positive rows: `{positive['score_positive_count']}`",
            f"- Crowded-collapse rows: `{positive['crowded_collapse_count']}`",
            f"- Total collapse-risk rows: `{positive['collapse_risk_count']}`",
            f"- Mean positive reward probability: `{_format_metric(positive['mean_positive_reward_probability'])}`",
            f"- Mean crowded reward probability: `{_format_metric(positive['mean_crowded_reward_probability'])}`",
            f"- Mean collapse-risk reward probability: `{_format_metric(positive['mean_collapse_risk_reward_probability'])}`",
            f"- Positive mean ranks above crowded mean: `{positive['positive_ranks_above_crowded_mean']}`",
            f"- Positive mean ranks above collapse-risk mean: `{positive['positive_ranks_above_collapse_risk_mean']}`",
            "",
            "## Highest Historical Collapse-Risk Families",
            "",
            "| family | rows | mean collapse risk | mean reward prob | observed outcomes |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in family_risk:
        lines.append(
            f"| `{row['family']}` | {row['row_count']} | "
            f"{_format_metric(row['mean_collapse_risk_probability'])} | "
            f"{_format_metric(row['mean_reward_probability'])} | "
            f"`{json.dumps(row['observed_outcomes'], sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in manifest["limitations"])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input_jsonl", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = read_jsonl(args.input_jsonl)
    artifacts = build_training_artifacts(rows, source_path=str(args.input_jsonl))
    manifest = artifacts["manifest"]
    manifest["git_commit"] = get_source_commit(REPO_ROOT)
    model = artifacts["model"]
    metrics = artifacts["metrics"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "reward_model.json", model.to_json())
    write_json(args.output_dir / "training_manifest.json", manifest)
    write_json(args.output_dir / "training_metrics.json", metrics)
    write_report(args.output_dir / "training_report.md", manifest=manifest, metrics=metrics)
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "row_count": manifest["row_count"],
                "advisory_status": manifest["advisory_status"],
                "group_overlap": manifest["split"]["group_overlap"],
                "eval_supervised": metrics["eval"]["supervised_evaluated_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
