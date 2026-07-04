#!/usr/bin/env python3
"""Score exported IGP24 model samples with the CPU proxy pipeline.

This helper consumes JSONL written by train.py --sample_export_only. It stays
proxy-only: no exact verifier execution, no SAIR/network calls, and no
submission behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.envs.igp24 import IGP24DataPoint
from src.igp24.polynomial import DEGREE, analysis_to_record, validate_coefficients
from src.utils import bool_flag


DEFAULT_OUTPUT_DIR = Path("/tmp/igp24_scored_sample_export_20260704")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def extract_decoded_coefficients(record: dict[str, Any]) -> list[int] | None:
    coeffs = record.get("decoded_coefficients")
    if coeffs is None:
        exported = record.get("exported_coefficients")
        if isinstance(exported, list) and len(exported) == DEGREE + 1 and exported[-1] == 1:
            coeffs = exported[:-1]
    if coeffs is None:
        return None
    try:
        return [int(value) for value in validate_coefficients(coeffs)]
    except Exception:
        return None


def configure_datapoint(args: argparse.Namespace) -> None:
    IGP24DataPoint.COEFF_BOUND = int(args.coeff_bound)
    IGP24DataPoint.TARGET_R = args.target_r
    IGP24DataPoint.TARGET_T = args.target_t
    IGP24DataPoint.PRIME_LIMIT = int(args.prime_limit)
    IGP24DataPoint.MAX_LOCAL_SEARCH_STEPS = int(args.max_local_search_steps)
    IGP24DataPoint.DISCRIMINANT_WEIGHT = float(args.discriminant_weight)
    IGP24DataPoint.HEIGHT_WEIGHT = float(args.height_weight)
    IGP24DataPoint.CYCLE_DIVERSITY_WEIGHT = float(args.cycle_diversity_weight)
    IGP24DataPoint.EXACT_SCORE_TIMEOUT = float(args.exact_score_timeout)
    IGP24DataPoint.WRITE_LEDGER = False
    IGP24DataPoint.LEDGER_PATH = ""
    IGP24DataPoint.EXPERIMENT_NAME = args.exp_name
    IGP24DataPoint.SEED = int(args.seed)
    IGP24DataPoint.TRANSLATION_RADIUS = int(args.translation_radius)
    IGP24DataPoint.KNOWN_HASHES = set()
    IGP24DataPoint.ALWAYS_SEARCH = False
    IGP24DataPoint.REDEEM_ONLY = False


def score_export_records(
    records: list[dict[str, Any]],
    *,
    args: argparse.Namespace,
    source_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    configure_datapoint(args)

    max_records = len(records) if args.max_records is None else min(len(records), int(args.max_records))
    scored: list[dict[str, Any]] = []
    skipped_decode = 0
    invalid_input = 0
    valid_records = 0
    rejected_records = 0

    for record in records[:max_records]:
        coeffs = extract_decoded_coefficients(record)
        if coeffs is None:
            skipped_decode += 1
            continue
        try:
            datapoint = IGP24DataPoint(N=DEGREE, coeffs=coeffs, generation_strategy="model_sample_export")
        except Exception:
            invalid_input += 1
            continue

        datapoint.calc_features()
        datapoint.calc_score()
        if args.local_search:
            datapoint.local_search(improve_with_local_search=True)

        if datapoint.analysis is None:
            invalid_input += 1
            continue

        if datapoint.analysis.valid:
            valid_records += 1
        else:
            rejected_records += 1

        generation_metadata = {
            "strategy": "model_sample_export",
            "source": "sample_export_import_score",
            "source_export_path": str(source_path),
            "source_sample_index": record.get("sample_index"),
            "source_batch_index": record.get("batch_index"),
            "source_temperature": record.get("temperature"),
            "source_top_k": record.get("top_k"),
            "source_device": record.get("device"),
            "local_search_enabled": bool(args.local_search),
        }
        scored_record = analysis_to_record(
            datapoint.analysis,
            datapoint.score,
            target_r=args.target_r,
            target_t=args.target_t,
            experiment_name=args.exp_name,
            generation_metadata=generation_metadata,
            local_search_metadata=datapoint.local_search_stats,
        )
        scored_record["source_sample_export"] = {
            "path": str(source_path),
            "sample_index": record.get("sample_index"),
            "record_type": record.get("record_type"),
            "schema_version": record.get("schema_version"),
        }
        scored_record["safety"] = {
            "proxy_only": True,
            "runs_exact_verifiers": False,
            "calls_sair": False,
            "uses_network": False,
            "auto_submits": False,
        }
        scored.append(scored_record)

    summary = {
        "source_path": str(source_path),
        "records_read": len(records),
        "records_selected": max_records,
        "decoded_input_records": max_records - skipped_decode - invalid_input,
        "skipped_decode_records": skipped_decode,
        "invalid_input_records": invalid_input,
        "scored_records": len(scored),
        "valid_records": valid_records,
        "rejected_records": rejected_records,
        "local_search_enabled": bool(args.local_search),
        "safety": {
            "proxy_only": True,
            "runs_exact_verifiers": False,
            "calls_sair": False,
            "uses_network": False,
            "auto_submits": False,
        },
    }
    return scored, summary


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# IGP24 Sample Export Scoring Report",
            "",
            f"- Created UTC: `{summary.get('created_at_utc')}`",
            f"- Source export: `{summary.get('source_path')}`",
            f"- Scored JSONL: `{summary.get('scored_jsonl_path')}`",
            "- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.",
            "",
            "## Counts",
            "",
            "| read | selected | decoded_input | skipped_decode | invalid_input | scored | valid | rejected | local_search |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            "| "
            + " | ".join(
                [
                    str(summary.get("records_read")),
                    str(summary.get("records_selected")),
                    str(summary.get("decoded_input_records")),
                    str(summary.get("skipped_decode_records")),
                    str(summary.get("invalid_input_records")),
                    str(summary.get("scored_records")),
                    str(summary.get("valid_records")),
                    str(summary.get("rejected_records")),
                    str(summary.get("local_search_enabled")),
                ]
            )
            + " |",
            "",
        ]
    )


def write_outputs(scored_records: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scored_path = output_dir / "scored_samples.jsonl"
    summary_path = output_dir / "score_summary.json"
    report_path = output_dir / "score_report.md"
    with scored_path.open("w", encoding="utf-8") as handle:
        for record in scored_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    summary["scored_jsonl_path"] = str(scored_path)
    summary["summary_path"] = str(summary_path)
    summary["report_path"] = str(report_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score exported IGP24 model samples with the CPU proxy scorer")
    parser.add_argument("sample_export", type=Path)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max_records", type=int, default=None)
    parser.add_argument("--coeff_bound", type=int, default=4)
    parser.add_argument("--target_r", type=int, default=None)
    parser.add_argument("--target_t", type=str, default=None)
    parser.add_argument("--prime_limit", type=int, default=11)
    parser.add_argument("--exact_score_timeout", type=float, default=2.0)
    parser.add_argument("--discriminant_weight", type=float, default=1.0)
    parser.add_argument("--height_weight", type=float, default=1.0)
    parser.add_argument("--cycle_diversity_weight", type=float, default=5.0)
    parser.add_argument("--translation_radius", type=int, default=2)
    parser.add_argument("--local_search", type=bool_flag, default="false")
    parser.add_argument("--max_local_search_steps", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--exp_name", type=str, default="igp24_sample_export_score")
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    source_path = args.sample_export.resolve()
    output_dir = args.output_dir.resolve()
    records = read_jsonl(source_path)
    scored_records, summary = score_export_records(records, args=args, source_path=source_path)
    summary["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    summary["output_dir"] = str(output_dir)
    write_outputs(scored_records, summary, output_dir)
    print(build_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
