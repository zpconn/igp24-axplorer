#!/usr/bin/env python3
"""Score exported IGP24 model samples with the CPU proxy pipeline.

This helper consumes JSONL written by train.py --sample_export_only. It stays
proxy-only: no exact verifier execution, no SAIR/network calls, and no
submission behavior.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from collections import Counter
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


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def command_text(argv: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def git_commit(repo_root: Path = REPO_ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


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
    score_all = bool(getattr(args, "score_all", False))
    selection_mode = "all_explicit" if score_all else ("all_default" if args.max_records is None else "capped")
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
        "selection_mode": selection_mode,
        "max_records": args.max_records,
        "score_all": score_all,
        "scored_record_summary": summarize_scored_records(scored),
        "safety": {
            "proxy_only": True,
            "runs_exact_verifiers": False,
            "calls_sair": False,
            "uses_network": False,
            "auto_submits": False,
        },
    }
    return scored, summary


def summarize_scored_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = [record.get("canonical_hash") for record in records if record.get("canonical_hash")]
    hash_counts = Counter(hashes)
    duplicate_hashes = {hash_value: count for hash_value, count in hash_counts.items() if count > 1}
    scores = [float(record["score"]) for record in records if record.get("score") is not None]
    valid = [record for record in records if record.get("verification_status") == "proxy_scored"]
    rejected = [record for record in records if record.get("verification_status") == "rejected"]
    return {
        "scored_records": len(records),
        "proxy_scored_records": len(valid),
        "rejected_records": len(rejected),
        "canonical_hash_records": len(hashes),
        "unique_canonical_hashes": len(hash_counts),
        "duplicate_canonical_hash_records": len(hashes) - len(hash_counts),
        "duplicate_canonical_hashes": len(duplicate_hashes),
        "duplicate_canonical_hash_examples": [
            {"canonical_hash": hash_value, "count": count}
            for hash_value, count in sorted(duplicate_hashes.items())[:10]
        ],
        "best_score": max(scores) if scores else None,
        "mean_score": (sum(scores) / len(scores)) if scores else None,
    }


def default_gpu_probe_summary_path(source_export_path: Path) -> Path:
    return source_export_path.parent / "gpu_sampler_probe_summary.json"


def build_split_manifest(
    *,
    score_summary: dict[str, Any],
    gpu_summary: dict[str, Any] | None,
    gpu_summary_path: Path | None,
    source_commit: str | None,
    score_command: str,
) -> dict[str, Any]:
    gpu_run = ((gpu_summary or {}).get("runs") or {}).get("gpu_sampler_probe") or {}
    gpu_train_log = gpu_run.get("train_log") or {}
    gpu_monitor = gpu_run.get("gpu_monitor") or {}
    gpu_report_path = None
    if gpu_summary_path is not None:
        candidate_report = gpu_summary_path.with_name("gpu_sampler_probe_report.md")
        gpu_report_path = str(candidate_report) if candidate_report.exists() else None

    safety = {
        "proxy_only": True,
        "runs_exact_verifiers": False,
        "calls_sair": False,
        "uses_network": False,
        "auto_submits": False,
    }
    return {
        "schema_version": 1,
        "record_type": "igp24_split_workflow_manifest",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "commands": {
            "gpu_probe": gpu_run.get("command_text"),
            "cpu_score": score_command,
        },
        "artifacts": {
            "sample_export_path": score_summary.get("source_path"),
            "gpu_probe_summary_path": str(gpu_summary_path) if gpu_summary_path else None,
            "gpu_probe_report_path": gpu_report_path,
            "train_log_path": gpu_run.get("train_log_path"),
            "cpu_score_summary_path": score_summary.get("summary_path"),
            "cpu_score_report_path": score_summary.get("report_path"),
            "scored_jsonl_path": score_summary.get("scored_jsonl_path"),
        },
        "gpu_phase": {
            "present": gpu_summary is not None,
            "returncode": gpu_run.get("returncode"),
            "timed_out": gpu_run.get("timed_out"),
            "interrupted": gpu_run.get("interrupted"),
            "runtime_seconds": gpu_run.get("runtime_seconds"),
            "device": gpu_train_log.get("logged_device"),
            "eval_count": len(gpu_train_log.get("eval_losses") or []),
            "max_cuda_reserved_mb": gpu_train_log.get("max_cuda_reserved_mb"),
            "max_gpu_utilization_percent": gpu_monitor.get("max_gpu_utilization_percent"),
            "avg_gpu_utilization_percent": gpu_monitor.get("avg_gpu_utilization_percent"),
            "max_memory_used_mib": gpu_monitor.get("max_memory_used_mib"),
            "sample_export_records": gpu_run.get("sample_export_records"),
            "sample_export_decoded_records": gpu_run.get("sample_export_decoded_records"),
            "scoring_local_search_avoided": gpu_run.get("post_train_cpu_sampling_scoring_avoided"),
        },
        "cpu_phase": {
            "runtime_seconds": score_summary.get("runtime_seconds"),
            "records_read": score_summary.get("records_read"),
            "records_selected": score_summary.get("records_selected"),
            "selection_mode": score_summary.get("selection_mode"),
            "max_records": score_summary.get("max_records"),
            "decoded_input_records": score_summary.get("decoded_input_records"),
            "scored_records": score_summary.get("scored_records"),
            "valid_records": score_summary.get("valid_records"),
            "rejected_records": score_summary.get("rejected_records"),
            "local_search_enabled": score_summary.get("local_search_enabled"),
        },
        "dedup": score_summary.get("scored_record_summary", {}),
        "safety": safety,
    }


def build_split_report(manifest: dict[str, Any]) -> str:
    gpu = manifest.get("gpu_phase") or {}
    cpu = manifest.get("cpu_phase") or {}
    dedup = manifest.get("dedup") or {}
    artifacts = manifest.get("artifacts") or {}
    return "\n".join(
        [
            "# IGP24 Split Workflow Report",
            "",
            f"- Created UTC: `{manifest.get('created_at_utc')}`",
            f"- Source commit: `{manifest.get('source_commit')}`",
            "- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.",
            "",
            "## Artifacts",
            "",
            f"- Sample export JSONL: `{artifacts.get('sample_export_path')}`",
            f"- GPU probe summary: `{artifacts.get('gpu_probe_summary_path')}`",
            f"- GPU train log: `{artifacts.get('train_log_path')}`",
            f"- CPU score summary: `{artifacts.get('cpu_score_summary_path')}`",
            f"- CPU scored JSONL: `{artifacts.get('scored_jsonl_path')}`",
            "",
            "## Counts",
            "",
            "| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            "| "
            + " | ".join(
                [
                    str(gpu.get("runtime_seconds")),
                    str(gpu.get("max_gpu_utilization_percent")),
                    str(gpu.get("sample_export_records")),
                    str(gpu.get("sample_export_decoded_records")),
                    str(cpu.get("runtime_seconds")),
                    str(cpu.get("records_selected")),
                    str(cpu.get("scored_records")),
                    str(cpu.get("valid_records")),
                    str(cpu.get("rejected_records")),
                    str(dedup.get("unique_canonical_hashes")),
                    str(dedup.get("duplicate_canonical_hash_records")),
                    str(cpu.get("local_search_enabled")),
                ]
            )
            + " |",
            "",
            "## Commands",
            "",
            f"- GPU probe: `{(manifest.get('commands') or {}).get('gpu_probe')}`",
            f"- CPU score: `{(manifest.get('commands') or {}).get('cpu_score')}`",
            "",
        ]
    )


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# IGP24 Sample Export Scoring Report",
            "",
            f"- Created UTC: `{summary.get('created_at_utc')}`",
            f"- Source export: `{summary.get('source_path')}`",
            f"- Scored JSONL: `{summary.get('scored_jsonl_path')}`",
            f"- Split manifest: `{summary.get('split_manifest_path')}`",
            "- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.",
            "",
            "## Counts",
            "",
            "| read | selected | decoded_input | skipped_decode | invalid_input | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
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
                    str((summary.get("scored_record_summary") or {}).get("unique_canonical_hashes")),
                    str((summary.get("scored_record_summary") or {}).get("duplicate_canonical_hash_records")),
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
    manifest_path = output_dir / "split_workflow_manifest.json"
    split_report_path = output_dir / "split_workflow_report.md"
    with scored_path.open("w", encoding="utf-8") as handle:
        for record in scored_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    summary["scored_jsonl_path"] = str(scored_path)
    summary["summary_path"] = str(summary_path)
    summary["report_path"] = str(report_path)
    summary["split_manifest_path"] = str(manifest_path)
    summary["split_report_path"] = str(split_report_path)
    gpu_summary_path = Path(summary["gpu_probe_summary_path"]) if summary.get("gpu_probe_summary_path") else None
    gpu_summary = read_json(gpu_summary_path) if gpu_summary_path is not None else None
    manifest = build_split_manifest(
        score_summary=summary,
        gpu_summary=gpu_summary,
        gpu_summary_path=gpu_summary_path,
        source_commit=summary.get("source_commit"),
        score_command=summary.get("score_command") or "",
    )
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    split_report_path.write_text(build_split_report(manifest), encoding="utf-8")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score exported IGP24 model samples with the CPU proxy scorer")
    parser.add_argument("sample_export", type=Path)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max_records", type=int, default=None)
    parser.add_argument("--score_all", type=bool_flag, default=False, help="explicitly score all decoded export rows")
    parser.add_argument("--gpu_probe_summary", type=Path, default=None, help="optional GPU probe summary JSON; defaults to sibling gpu_sampler_probe_summary.json when present")
    parser.add_argument("--coeff_bound", type=int, default=4)
    parser.add_argument("--target_r", type=int, default=None)
    parser.add_argument("--target_t", type=str, default=None)
    parser.add_argument("--prime_limit", type=int, default=11)
    parser.add_argument("--exact_score_timeout", type=float, default=2.0)
    parser.add_argument("--discriminant_weight", type=float, default=1.0)
    parser.add_argument("--height_weight", type=float, default=1.0)
    parser.add_argument("--cycle_diversity_weight", type=float, default=5.0)
    parser.add_argument("--translation_radius", type=int, default=2)
    parser.add_argument("--local_search", type=bool_flag, default=False)
    parser.add_argument("--max_local_search_steps", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--exp_name", type=str, default="igp24_sample_export_score")
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    if args.score_all and args.max_records is not None:
        parser.error("--score_all cannot be combined with --max_records")
    source_path = args.sample_export.resolve()
    output_dir = args.output_dir.resolve()
    records = read_jsonl(source_path)
    start = time.perf_counter()
    scored_records, summary = score_export_records(records, args=args, source_path=source_path)
    summary["runtime_seconds"] = time.perf_counter() - start
    summary["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    summary["output_dir"] = str(output_dir)
    gpu_probe_summary = args.gpu_probe_summary.resolve() if args.gpu_probe_summary else default_gpu_probe_summary_path(source_path)
    summary["gpu_probe_summary_path"] = str(gpu_probe_summary) if gpu_probe_summary.exists() else None
    summary["source_commit"] = git_commit()
    summary["score_command"] = command_text([sys.executable, *sys.argv])
    write_outputs(scored_records, summary, output_dir)
    print(build_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
