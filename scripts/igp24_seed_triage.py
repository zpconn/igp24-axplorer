#!/usr/bin/env python3
"""Run small dedup-aware seed triage probes for IGP24 GPU exports."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_gpu_sampler_probe import DIVERSITY_EXPORT_VARIANTS
from scripts.igp24_gpu_smoke import command_text


DEFAULT_OUTPUT_DIR = Path("/tmp/igp24_seed_triage_20260705")
DEFAULT_SEEDS = [2404, 2405, 2406, 2402]
DEFAULT_DIVERSITY_VARIANT = "fixed_template_t11_open_topk"
RECOMMEND_PROMOTE = "promote_seed_to_1024_run"
RECOMMEND_REJECT = "reject_seed_for_full_1024_run"
RECOMMEND_AMBIGUOUS = "ambiguous_needs_more_evidence"
SAFETY = {
    "proxy_only": True,
    "gpu_phase_export_only": True,
    "scores_during_gpu_sampling": False,
    "local_search_during_gpu_sampling": False,
    "dataset_update_during_gpu_sampling": False,
    "runs_exact_verifiers": False,
    "calls_sair": False,
    "uses_network": False,
    "auto_submits": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def seed_dir(output_dir: Path, seed: int) -> Path:
    return output_dir / f"seed{seed}"


def seed_summary_path(output_dir: Path, seed: int) -> Path:
    return seed_dir(output_dir, seed) / "gpu_sampler_probe_summary.json"


def build_probe_command(
    *,
    python_executable: str,
    seed: int,
    output_dir: Path,
    diversity_variant: str,
    unique_target: int,
    max_attempts: int,
    progress_interval: int,
    timeout_seconds: int,
    monitor_interval_seconds: float,
) -> list[str]:
    if diversity_variant not in DIVERSITY_EXPORT_VARIANTS:
        raise ValueError(f"unknown diversity variant: {diversity_variant}")
    return [
        python_executable,
        "scripts/igp24_gpu_sampler_probe.py",
        "--probe_mode",
        "sample_export_split_dedup",
        "--diversity_variant",
        diversity_variant,
        "--diversity_seed",
        str(seed),
        "--dedup_unique_target",
        str(unique_target),
        "--dedup_max_attempts",
        str(max_attempts),
        "--dedup_progress_interval",
        str(progress_interval),
        "--output_dir",
        str(seed_dir(output_dir, seed)),
        "--timeout_seconds",
        str(timeout_seconds),
        "--monitor_interval_seconds",
        str(monitor_interval_seconds),
    ]


def run_probe_command(cmd: list[str], *, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds + 180,
            check=False,
        )
        return {
            "command": cmd,
            "command_text": command_text(cmd),
            "returncode": completed.returncode,
            "runtime_seconds": time.perf_counter() - start,
            "timed_out": False,
            "stdout_tail": completed.stdout.splitlines()[-30:],
            "stderr_tail": completed.stderr.splitlines()[-30:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "command_text": command_text(cmd),
            "returncode": 124,
            "runtime_seconds": time.perf_counter() - start,
            "timed_out": True,
            "stdout_tail": (exc.stdout or "").splitlines()[-30:] if isinstance(exc.stdout, str) else [],
            "stderr_tail": (exc.stderr or "").splitlines()[-30:] if isinstance(exc.stderr, str) else [],
        }


def duplicate_skip_rate(*, duplicate_skipped: int, decoded_attempts: int, invalid_decode_attempts: int, attempted: int) -> float | None:
    denominator = decoded_attempts if decoded_attempts > 0 else max(attempted - invalid_decode_attempts, 0)
    if denominator <= 0:
        return None
    return duplicate_skipped / denominator


def recommend_seed(metrics: dict[str, Any], thresholds: dict[str, float]) -> tuple[str, str]:
    returncode = metrics.get("returncode")
    if returncode not in {0, None}:
        return RECOMMEND_REJECT, f"probe return code was {returncode}"
    if metrics.get("timed_out") or metrics.get("interrupted"):
        return RECOMMEND_REJECT, "probe timed out or was interrupted"

    unique = safe_int(metrics.get("unique_decoded_count"))
    target = safe_int(metrics.get("unique_target"))
    if unique <= 0:
        return RECOMMEND_REJECT, "no unique decoded coefficients were exported"

    stop_reason = str(metrics.get("stop_reason"))
    attempts_per_unique = finite_float(metrics.get("attempts_per_unique"))
    skip_rate = finite_float(metrics.get("duplicate_skip_rate"))
    unique_fraction = unique / target if target > 0 else 1.0

    if stop_reason == "unique_target_reached":
        if (
            attempts_per_unique is not None
            and skip_rate is not None
            and attempts_per_unique <= thresholds["promote_max_attempts_per_unique"]
            and skip_rate <= thresholds["promote_max_duplicate_skip_rate"]
        ):
            return (
                RECOMMEND_PROMOTE,
                "target reached with low attempts per unique and low duplicate skip rate",
            )
        if (
            attempts_per_unique is not None
            and attempts_per_unique >= thresholds["reject_min_attempts_per_unique"]
        ) or (skip_rate is not None and skip_rate >= thresholds["reject_min_duplicate_skip_rate"]):
            return RECOMMEND_REJECT, "target reached only after high duplicate pressure"
        return RECOMMEND_AMBIGUOUS, "target reached, but duplicate pressure is not clearly low"

    if unique_fraction < thresholds["reject_max_unique_fraction_on_budget_exhausted"]:
        return RECOMMEND_REJECT, "attempt budget exhausted far below the unique target"
    if (
        attempts_per_unique is not None
        and attempts_per_unique >= thresholds["reject_min_attempts_per_unique"]
    ) or (skip_rate is not None and skip_rate >= thresholds["reject_min_duplicate_skip_rate"]):
        return RECOMMEND_REJECT, "attempt budget exhausted with high duplicate pressure"
    return RECOMMEND_AMBIGUOUS, "attempt budget exhausted, but partial unique coverage was not catastrophic"


def load_seed_result(
    *,
    seed: int,
    summary_path: Path,
    thresholds: dict[str, float],
    invocation: dict[str, Any] | None = None,
    known_outcome: str | None = None,
) -> dict[str, Any]:
    summary = read_json(summary_path)
    run = (summary.get("runs") or {}).get("gpu_sampler_probe") or {}
    sidecar_text = run.get("sample_export_summary_path")
    sidecar = read_json(Path(sidecar_text)) if sidecar_text else {}
    train_log = run.get("train_log") or {}
    gpu_monitor = run.get("gpu_monitor") or {}

    attempted = safe_int(run.get("sample_export_attempted_samples", sidecar.get("attempted_samples")))
    unique = safe_int(run.get("sample_export_unique_decoded_coefficients", sidecar.get("unique_decoded_coefficients")))
    duplicate_skipped = safe_int(
        run.get("sample_export_duplicate_decoded_records_skipped", sidecar.get("duplicate_decoded_records_skipped"))
    )
    invalid_decode = safe_int(run.get("sample_export_invalid_decode_records", sidecar.get("invalid_decode_records")))
    decoded_attempts = safe_int(sidecar.get("decoded_attempts"))
    invalid_decode_attempts = safe_int(sidecar.get("invalid_decode_attempts"), invalid_decode)
    target = safe_int(run.get("sample_export_unique_target", sidecar.get("unique_target")))
    attempts_per_unique = attempted / unique if unique > 0 else None
    skip_rate = duplicate_skip_rate(
        duplicate_skipped=duplicate_skipped,
        decoded_attempts=decoded_attempts,
        invalid_decode_attempts=invalid_decode_attempts,
        attempted=attempted,
    )

    metrics = {
        "seed": int(seed),
        "known_full_run_outcome": known_outcome,
        "summary_path": str(summary_path),
        "summary_exists": summary_path.exists(),
        "sample_export_path": run.get("sample_export_path"),
        "sample_export_summary_path": run.get("sample_export_summary_path"),
        "returncode": run.get("returncode"),
        "timed_out": run.get("timed_out"),
        "interrupted": run.get("interrupted"),
        "runtime_seconds": run.get("runtime_seconds"),
        "device": train_log.get("logged_device"),
        "max_gpu_utilization_percent": gpu_monitor.get("max_gpu_utilization_percent"),
        "avg_gpu_utilization_percent": gpu_monitor.get("avg_gpu_utilization_percent"),
        "max_memory_used_mib": gpu_monitor.get("max_memory_used_mib"),
        "attempt_budget": safe_int(run.get("sample_export_attempt_budget", sidecar.get("attempt_budget"))),
        "attempted_samples": attempted,
        "records_written": safe_int(run.get("sample_export_records", sidecar.get("records_written"))),
        "decoded_written": safe_int(run.get("sample_export_decoded_records", sidecar.get("decoded_records"))),
        "invalid_decode_count": invalid_decode,
        "unique_target": target,
        "unique_decoded_count": unique,
        "duplicate_skipped_count": duplicate_skipped,
        "stop_reason": run.get("sample_export_stop_reason", sidecar.get("stop_reason")),
        "attempts_per_unique": attempts_per_unique,
        "duplicate_skip_rate": skip_rate,
        "unique_fraction": unique / target if target > 0 else None,
        "scoring_avoided": run.get("sample_export_scoring_avoided"),
        "local_search_avoided": run.get("sample_export_local_search_avoided"),
        "dataset_update_avoided": sidecar.get("dataset_update_avoided"),
        "probe_command": (summary.get("runs") or {}).get("gpu_sampler_probe", {}).get("command_text"),
        "triage_invocation": invocation or {},
    }
    recommendation, reason = recommend_seed(metrics, thresholds)
    metrics["recommendation"] = recommendation
    metrics["recommendation_reason"] = reason
    return metrics


def fmt(value: Any) -> str:
    number = finite_float(value)
    if number is not None:
        return f"{number:.3f}"
    if value is None:
        return ""
    return str(value)


def build_summary(
    *,
    seeds: list[int],
    results: list[dict[str, Any]],
    args: argparse.Namespace,
    thresholds: dict[str, float],
    commands: dict[int, list[str]],
) -> dict[str, Any]:
    counts = {
        "promote": sum(1 for result in results if result.get("recommendation") == RECOMMEND_PROMOTE),
        "reject": sum(1 for result in results if result.get("recommendation") == RECOMMEND_REJECT),
        "ambiguous": sum(1 for result in results if result.get("recommendation") == RECOMMEND_AMBIGUOUS),
    }
    return {
        "schema_version": 1,
        "record_type": "igp24_seed_triage",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(args.output_dir),
        "repo_root": str(args.repo_root),
        "seeds": seeds,
        "diversity_variant": args.diversity_variant,
        "unique_target": args.unique_target,
        "max_attempts": args.max_attempts,
        "progress_interval": args.progress_interval,
        "timeout_seconds": args.timeout_seconds,
        "monitor_interval_seconds": args.monitor_interval_seconds,
        "thresholds": thresholds,
        "safety": SAFETY,
        "commands": {str(seed): command_text(command) for seed, command in commands.items()},
        "counts": counts,
        "results": results,
    }


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Seed Triage Report",
        "",
        f"- Created UTC: `{summary.get('created_at_utc')}`",
        f"- Output directory: `{summary.get('output_dir')}`",
        f"- Diversity variant: `{summary.get('diversity_variant')}`",
        f"- Unique target: `{summary.get('unique_target')}`",
        f"- Attempt budget: `{summary.get('max_attempts')}`",
        "- Safety: export-only/proxy-only; no GPU-phase scoring, local search, exact verifier, SAIR, network, or submission.",
        "",
        "## Summary",
        "",
        "| seed | known full-run outcome | recommendation | attempted | unique | duplicate skipped | invalid | stop reason | attempts/unique | duplicate skip rate | max GPU util | avg GPU util |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for result in summary.get("results", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(result.get("seed")),
                    str(result.get("known_full_run_outcome") or ""),
                    str(result.get("recommendation")),
                    str(result.get("attempted_samples")),
                    str(result.get("unique_decoded_count")),
                    str(result.get("duplicate_skipped_count")),
                    str(result.get("invalid_decode_count")),
                    str(result.get("stop_reason")),
                    fmt(result.get("attempts_per_unique")),
                    fmt(result.get("duplicate_skip_rate")),
                    fmt(result.get("max_gpu_utilization_percent")),
                    fmt(result.get("avg_gpu_utilization_percent")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation Reasons", ""])
    for result in summary.get("results", []):
        lines.append(
            f"- Seed `{result.get('seed')}` -> `{result.get('recommendation')}`: {result.get('recommendation_reason')}"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON summary: `{summary.get('artifacts', {}).get('summary_path')}`",
            f"- JSONL records: `{summary.get('artifacts', {}).get('records_path')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifacts(summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "seed_triage_summary.json"
    report_path = output_dir / "seed_triage_report.md"
    records_path = output_dir / "seed_triage_records.jsonl"
    summary["artifacts"] = {
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "records_path": str(records_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")
    write_jsonl(records_path, summary.get("results", []))


def parse_known_outcomes(values: list[str]) -> dict[int, str]:
    outcomes: dict[int, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"known outcome must be SEED=LABEL, got {value!r}")
        seed_text, label = value.split("=", 1)
        outcomes[int(seed_text)] = label
    return outcomes


def thresholds_from_args(args: argparse.Namespace) -> dict[str, float]:
    return {
        "promote_max_attempts_per_unique": float(args.promote_max_attempts_per_unique),
        "promote_max_duplicate_skip_rate": float(args.promote_max_duplicate_skip_rate),
        "reject_min_attempts_per_unique": float(args.reject_min_attempts_per_unique),
        "reject_min_duplicate_skip_rate": float(args.reject_min_duplicate_skip_rate),
        "reject_max_unique_fraction_on_budget_exhausted": float(args.reject_max_unique_fraction_on_budget_exhausted),
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run small dedup-aware seed triage probes for IGP24")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    parser.add_argument("--python_executable", default=sys.executable)
    parser.add_argument("--diversity_variant", choices=sorted(DIVERSITY_EXPORT_VARIANTS), default=DEFAULT_DIVERSITY_VARIANT)
    parser.add_argument("--unique_target", type=int, default=256)
    parser.add_argument("--max_attempts", type=int, default=1024)
    parser.add_argument("--progress_interval", type=int, default=128)
    parser.add_argument("--timeout_seconds", type=int, default=900)
    parser.add_argument("--monitor_interval_seconds", type=float, default=2.0)
    parser.add_argument("--skip_existing", action="store_true", help="Reuse an existing per-seed GPU probe summary when present")
    parser.add_argument("--summarize_existing", action="store_true", help="Do not run GPU probes; summarize existing per-seed outputs only")
    parser.add_argument("--known_outcome", action="append", default=[], help="Optional SEED=LABEL full-run outcome for report comparison")
    parser.add_argument("--promote_max_attempts_per_unique", type=float, default=1.75)
    parser.add_argument("--promote_max_duplicate_skip_rate", type=float, default=0.40)
    parser.add_argument("--reject_min_attempts_per_unique", type=float, default=3.0)
    parser.add_argument("--reject_min_duplicate_skip_rate", type=float, default=0.65)
    parser.add_argument("--reject_max_unique_fraction_on_budget_exhausted", type=float, default=0.90)
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    args.output_dir = args.output_dir.resolve()
    args.repo_root = args.repo_root.resolve()
    thresholds = thresholds_from_args(args)
    known_outcomes = parse_known_outcomes(args.known_outcome)

    results: list[dict[str, Any]] = []
    commands: dict[int, list[str]] = {}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for seed in args.seeds:
        command = build_probe_command(
            python_executable=args.python_executable,
            seed=seed,
            output_dir=args.output_dir,
            diversity_variant=args.diversity_variant,
            unique_target=args.unique_target,
            max_attempts=args.max_attempts,
            progress_interval=args.progress_interval,
            timeout_seconds=args.timeout_seconds,
            monitor_interval_seconds=args.monitor_interval_seconds,
        )
        commands[seed] = command
        summary_path = seed_summary_path(args.output_dir, seed)
        invocation: dict[str, Any] = {
            "skipped": False,
            "reason": None,
            "command_text": command_text(command),
        }
        if args.summarize_existing:
            invocation.update({"skipped": True, "reason": "summarize_existing"})
        elif args.skip_existing and summary_path.exists():
            invocation.update({"skipped": True, "reason": "skip_existing_summary_present"})
        else:
            invocation.update(run_probe_command(command, cwd=args.repo_root, timeout_seconds=args.timeout_seconds))

        result = load_seed_result(
            seed=seed,
            summary_path=summary_path,
            thresholds=thresholds,
            invocation=invocation,
            known_outcome=known_outcomes.get(seed),
        )
        results.append(result)
        summary = build_summary(
            seeds=list(args.seeds),
            results=results,
            args=args,
            thresholds=thresholds,
            commands=commands,
        )
        write_artifacts(summary, args.output_dir)

    final_summary = build_summary(
        seeds=list(args.seeds),
        results=results,
        args=args,
        thresholds=thresholds,
        commands=commands,
    )
    write_artifacts(final_summary, args.output_dir)
    print(build_report(final_summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
