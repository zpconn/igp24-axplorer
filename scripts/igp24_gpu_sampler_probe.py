#!/usr/bin/env python3
"""Run a short proxy-only GPU training/sampling probe for IGP24 Axplorer.

This is intentionally smaller than a full training run. It reuses the real
`train.py` path with explicit caps, then summarizes CUDA, loss, sampling, and
ledger signals so the next step can be chosen from evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_benchmark import read_jsonl, summarize_records
from scripts.igp24_gpu_smoke import (
    command_text,
    nvidia_smi_command,
    parse_nvidia_smi_gpus,
    parse_torch_probe_stdout,
    run_command,
    torch_probe_command,
    utc_run_id,
)


DEFAULT_OUTPUT_DIR = Path("/tmp/igp24_gpu_sampler_probe_20260704")
DEFAULT_BASELINE_SUMMARY = Path("/tmp/igp24_gpu_smoke_20260704/gpu_smoke_summary.json")


def _float(value: str) -> float:
    return float(value)


def _finite(value: Any) -> bool:
    return isinstance(value, (float, int)) and math.isfinite(float(value))


def parse_train_log(text: str) -> dict[str, Any]:
    device_matches = re.findall(r"\bdevice:\s*([^\n\r]+)", text)
    eval_losses = [
        {
            "step": int(match.group("step")),
            "train_loss": _float(match.group("train")),
            "test_loss": _float(match.group("test")),
        }
        for match in re.finditer(
            r"step\s+(?P<step>\d+)\s+train loss:\s+(?P<train>[-+0-9.eE]+)\s+test loss:\s+(?P<test>[-+0-9.eE]+)",
            text,
        )
    ]
    step_losses = [
        {
            "step": int(match.group("step")),
            "loss": _float(match.group("loss")),
            "step_time_ms": _float(match.group("time")),
        }
        for match in re.finditer(
            r"step\s+(?P<step>\d+)\s+\|\s+loss\s+(?P<loss>[-+0-9.eE]+)\s+\|\s+steps time\s+(?P<time>[-+0-9.eE]+)ms",
            text,
        )
    ]
    cuda_memory = [
        {
            "allocated_mb": _float(match.group("allocated")),
            "reserved_mb": _float(match.group("reserved")),
        }
        for match in re.finditer(
            r"Memory allocated:\s+(?P<allocated>[-+0-9.eE]+)MB,\s+reserved:\s+(?P<reserved>[-+0-9.eE]+)MB",
            text,
        )
    ]
    sample_sections = parse_sample_sections(text)
    return {
        "logged_device": device_matches[-1].strip() if device_matches else None,
        "epoch_count": len(re.findall(r"==== Starting Epoch", text)),
        "eval_losses": eval_losses,
        "step_losses": step_losses,
        "cuda_memory": cuda_memory,
        "cuda_memory_logged": bool(cuda_memory),
        "max_cuda_allocated_mb": max((row["allocated_mb"] for row in cuda_memory), default=None),
        "max_cuda_reserved_mb": max((row["reserved_mb"] for row in cuda_memory), default=None),
        "sample_sections": sample_sections,
        "sample_requested_total": sum(section.get("requested", 0) for section in sample_sections),
        "sample_valid_total": sum(section.get("valid", 0) for section in sample_sections),
        "sample_invalid_before_local_search_total": sum(
            section.get("invalid_before_local_search", 0) for section in sample_sections
        ),
        "line_count": len(text.splitlines()),
    }


def parse_sample_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    chunks = re.split(r"Sample with temperature [^\n\r]+", text)
    for chunk in chunks[1:]:
        before_after_sample = chunk.split("AFTER_SAMPLE", 1)[0]
        progress = [
            {
                "generated": int(match.group("generated")),
                "requested": int(match.group("requested")),
                "scored": int(match.group("scored")),
            }
            for match in re.finditer(
                r"(?P<generated>\d+)\s+/\s+(?P<requested>\d+)\s+samples generated,\s+(?P<scored>\d+)\s+scored",
                before_after_sample,
            )
        ]
        invalid_match = re.search(
            r"Invalid examples:\s+before local search:\s+(?P<before>\d+),\s+after:\s+(?P<after>\d+)",
            before_after_sample,
        )
        valid_matches = re.findall(r"Valid examples:\s+(\d+)", before_after_sample)
        valid = int(valid_matches[-1]) if valid_matches else 0
        requested = max((row["requested"] for row in progress), default=0)
        sections.append(
            {
                "requested": requested,
                "progress": progress,
                "valid": valid,
                "invalid_before_local_search": int(invalid_match.group("before")) if invalid_match else 0,
                "invalid_after_local_search": int(invalid_match.group("after")) if invalid_match else 0,
                "no_valid_examples_logged": "No valid examples" in before_after_sample,
            }
        )
    return sections


def summarize_model_sample_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    sampled = [
        record
        for record in records
        if (record.get("generation_metadata") or {}).get("strategy") is None
    ]
    scores = [float(record["score"]) for record in sampled if record.get("score") is not None]
    return {
        "model_sample_ledger_records": len(sampled),
        "model_sample_best_score": max(scores) if scores else None,
        "model_sample_mean_score": (sum(scores) / len(scores)) if scores else None,
        "model_sample_hashes": [record.get("canonical_hash") for record in sampled[:10]],
    }


def inspect_sampler_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        parsed = parse_train_log("")
        parsed["exists"] = False
        return parsed
    parsed = parse_train_log(path.read_text(encoding="utf-8", errors="replace"))
    parsed["exists"] = True
    return parsed


def build_sampler_command(
    *,
    python_executable: str,
    output_dir: Path,
    run_id: str,
) -> dict[str, Any]:
    exp_name = "igp24_gpu_sampler_probe"
    dump_root = output_dir / "gpu_sampler_dump"
    ledger_path = output_dir / "gpu_sampler_candidates.jsonl"
    train_log_path = dump_root / exp_name / run_id / "train.log"
    cmd = [
        python_executable,
        "train.py",
        "--env_name",
        "igp24",
        "--exp_name",
        exp_name,
        "--dump_path",
        str(dump_root),
        "--exp_id",
        run_id,
        "--seed",
        "1801",
        "--coeff_bound",
        "4",
        "--gensize",
        "64",
        "--pop_size",
        "40",
        "--ntest",
        "8",
        "--gen_batch_size",
        "16",
        "--max_epochs",
        "2",
        "--max_steps",
        "100",
        "--num_eval_steps",
        "25",
        "--num_samples_from_model",
        "512",
        "--batch_size",
        "16",
        "--n_layer",
        "2",
        "--n_head",
        "4",
        "--n_embd",
        "128",
        "--max_len",
        "24",
        "--temperature",
        "0.9",
        "--top_k",
        "9",
        "--always_search",
        "true",
        "--max_local_search_steps",
        "2",
        "--prime_limit",
        "11",
        "--exact_score_timeout",
        "3",
        "--process_pool",
        "false",
        "--num_workers",
        "1",
        "--cpu",
        "false",
        "--igp24_generation_strategy",
        "fixed_sparse_template",
        "--igp24_ledger_path",
        str(ledger_path),
    ]
    return {
        "command": cmd,
        "command_text": command_text(cmd),
        "dump_root": str(dump_root),
        "ledger_path": str(ledger_path),
        "train_log_path": str(train_log_path),
        "exp_name": exp_name,
        "exp_id": run_id,
        "caps": {
            "timeout_seconds": 600,
            "max_epochs": 2,
            "max_steps_per_epoch": 100,
            "num_eval_steps": 25,
            "num_samples_from_model_per_epoch": 512,
        },
    }


def load_baseline_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs", {})
    return {
        "path": str(path),
        "recommendation": data.get("recommendation", {}),
        "cpu_baseline": {
            "returncode": runs.get("cpu_baseline", {}).get("returncode"),
            "runtime_seconds": runs.get("cpu_baseline", {}).get("runtime_seconds"),
            "valid_candidates": runs.get("cpu_baseline", {}).get("valid_candidates"),
            "ledger_records": runs.get("cpu_baseline", {}).get("ledger_records"),
        },
        "gpu_smoke": {
            "returncode": runs.get("gpu_train", {}).get("returncode"),
            "runtime_seconds": runs.get("gpu_train", {}).get("runtime_seconds"),
            "valid_candidates": runs.get("gpu_train", {}).get("valid_candidates"),
            "ledger_records": runs.get("gpu_train", {}).get("ledger_records"),
            "gpu_used": runs.get("gpu_train", {}).get("gpu_used"),
        },
    }


def summarize_sampler_run(command_config: dict[str, Any], command_result: dict[str, Any]) -> dict[str, Any]:
    ledger_path = Path(command_config["ledger_path"])
    train_log_path = Path(command_config["train_log_path"])
    records = read_jsonl(ledger_path)
    train_log = inspect_sampler_log(train_log_path)
    return {
        "status": "completed",
        "returncode": command_result.get("returncode"),
        "timed_out": command_result.get("timed_out"),
        "runtime_seconds": command_result.get("runtime_seconds"),
        "command": command_config["command"],
        "command_text": command_config["command_text"],
        "ledger_path": str(ledger_path),
        "train_log_path": str(train_log_path),
        "train_log": train_log,
        "gpu_used": (
            command_result.get("returncode") == 0
            and train_log.get("logged_device") == "cuda"
            and bool(train_log.get("cuda_memory_logged"))
        ),
        "stdout_tail": command_result.get("stdout_tail", []),
        "stderr_tail": command_result.get("stderr_tail", []),
        **summarize_records(records),
        **summarize_model_sample_records(records),
    }


def build_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    torch_probe = summary.get("probes", {}).get("torch_cuda", {}).get("parsed") or {}
    run = summary.get("runs", {}).get("gpu_sampler_probe") or {}
    train_log = run.get("train_log") or {}
    eval_losses = train_log.get("eval_losses") or []
    final_eval = eval_losses[-1] if eval_losses else {}
    sample_valid_total = int(train_log.get("sample_valid_total") or 0)
    model_sample_records = int(run.get("model_sample_ledger_records") or 0)

    if not torch_probe.get("cuda_available"):
        return {
            "action": "stay_with_cpu_proxy_search_only_for_now",
            "reason": "PyTorch CUDA is unavailable in this execution context.",
        }
    if run.get("timed_out"):
        return {
            "action": "run_another_short_gpu_probe_with_adjusted_settings",
            "reason": "The short probe hit its timeout cap; reduce settings before any longer run.",
        }
    if run.get("returncode") != 0:
        return {
            "action": "run_another_short_gpu_probe_with_adjusted_settings",
            "reason": "The GPU sampler probe did not exit cleanly.",
        }
    if not run.get("gpu_used"):
        return {
            "action": "run_another_short_gpu_probe_with_adjusted_settings",
            "reason": "The probe completed, but the log did not prove CUDA execution.",
        }
    if len(eval_losses) < 2 or not _finite(final_eval.get("test_loss")):
        return {
            "action": "run_another_short_gpu_probe_with_adjusted_settings",
            "reason": "The run was CUDA-clean but did not produce enough finite eval-loss evidence.",
        }
    if sample_valid_total == 0 and model_sample_records == 0:
        return {
            "action": "run_another_short_gpu_probe_with_adjusted_settings",
            "reason": "Training was stable, but model sampling produced no valid IGP24 candidates.",
        }
    if model_sample_records > 0:
        return {
            "action": "proceed_to_medium_30_60_minute_gpu_run_later",
            "reason": (
                "The short CUDA run was stable and produced valid model-sampled proxy candidates; "
                "a later medium run is justified, while CPU proxy-search remains primary."
            ),
        }
    return {
        "action": "run_another_short_gpu_probe_with_adjusted_settings",
        "reason": "The run completed, but sampled-candidate usefulness was still ambiguous.",
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_report(summary: dict[str, Any]) -> str:
    probes = summary.get("probes", {})
    torch_probe = probes.get("torch_cuda", {}).get("parsed") or {}
    nvidia = probes.get("nvidia_smi", {})
    run = summary.get("runs", {}).get("gpu_sampler_probe", {})
    train_log = run.get("train_log") or {}
    final_eval = (train_log.get("eval_losses") or [{}])[-1]
    recommendation = summary.get("recommendation", {})
    baseline = summary.get("baseline")
    lines = [
        "# IGP24 GPU Sampler Probe Report",
        "",
        f"- Created UTC: `{summary.get('created_at_utc')}`",
        f"- Output directory: `{summary.get('output_dir')}`",
        "- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.",
        "",
        "## Probes",
        "",
        f"- `nvidia-smi` return code: `{nvidia.get('returncode')}`",
        f"- GPUs: `{json.dumps(nvidia.get('gpus', []), sort_keys=True)}`",
        f"- PyTorch: `{torch_probe.get('torch_version')}`",
        f"- CUDA available: `{torch_probe.get('cuda_available')}`",
        f"- CUDA device: `{torch_probe.get('cuda_device_name')}`",
        "",
        "## GPU Sampler Run",
        "",
        "| returncode | timeout | runtime_s | device | evals | final_train_loss | final_test_loss | max_reserved_mb | sample_requested | sample_valid | model_sample_ledger | ledger_rows | metadata |",
        "| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        "| "
        + " | ".join(
            [
                str(run.get("returncode")),
                str(run.get("timed_out")),
                _fmt(run.get("runtime_seconds")),
                str(train_log.get("logged_device")),
                str(len(train_log.get("eval_losses") or [])),
                _fmt(final_eval.get("train_loss")),
                _fmt(final_eval.get("test_loss")),
                _fmt(train_log.get("max_cuda_reserved_mb")),
                str(train_log.get("sample_requested_total")),
                str(train_log.get("sample_valid_total")),
                str(run.get("model_sample_ledger_records")),
                str(run.get("ledger_records")),
                str(run.get("metadata_complete")),
            ]
        )
        + " |",
        "",
    ]
    if baseline:
        lines.extend(
            [
                "## Baseline Context",
                "",
                f"- Baseline summary: `{baseline.get('path')}`",
                f"- Tiny CPU smoke valid/ledger/runtime: `{baseline.get('cpu_baseline', {}).get('valid_candidates')}` / `{baseline.get('cpu_baseline', {}).get('ledger_records')}` / `{_fmt(baseline.get('cpu_baseline', {}).get('runtime_seconds'))}s`",
                f"- Tiny GPU smoke valid/ledger/runtime: `{baseline.get('gpu_smoke', {}).get('valid_candidates')}` / `{baseline.get('gpu_smoke', {}).get('ledger_records')}` / `{_fmt(baseline.get('gpu_smoke', {}).get('runtime_seconds'))}s`",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendation",
            "",
            f"- Action: `{recommendation.get('action')}`",
            f"- Reason: {recommendation.get('reason')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifacts(summary: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "gpu_sampler_probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "gpu_sampler_probe_report.md").write_text(build_report(summary), encoding="utf-8")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Short proxy-only GPU sampler probe for IGP24")
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    parser.add_argument("--python_executable", default=sys.executable)
    parser.add_argument("--timeout_seconds", type=int, default=600)
    parser.add_argument("--run_id", default="", help="Optional fixed experiment id; defaults to a UTC timestamp")
    parser.add_argument("--baseline_summary", type=Path, default=DEFAULT_BASELINE_SUMMARY)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero unless the recommendation advances to a medium run")
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    args.output_dir = args.output_dir.resolve()
    args.repo_root = args.repo_root.resolve()
    run_id = args.run_id or utc_run_id()

    summary: dict[str, Any] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(args.repo_root),
        "output_dir": str(args.output_dir),
        "run_id": run_id,
        "safety": {
            "proxy_only": True,
            "runs_exact_verifiers": False,
            "calls_sair": False,
            "uses_network": False,
            "auto_submits": False,
        },
        "baseline": load_baseline_summary(args.baseline_summary.resolve()),
        "probes": {},
        "runs": {},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)

    nvidia_result = run_command(nvidia_smi_command(), args.repo_root, min(args.timeout_seconds, 60))
    nvidia_result["gpus"] = parse_nvidia_smi_gpus("\n".join(nvidia_result.get("stdout_tail", [])))
    summary["probes"]["nvidia_smi"] = nvidia_result
    write_artifacts(summary, args.output_dir)

    torch_result = run_command(torch_probe_command(args.python_executable), args.repo_root, min(args.timeout_seconds, 60))
    torch_result["parsed"] = parse_torch_probe_stdout("\n".join(torch_result.get("stdout_tail", [])))
    summary["probes"]["torch_cuda"] = torch_result
    write_artifacts(summary, args.output_dir)

    torch_parsed = torch_result.get("parsed") or {}
    if torch_parsed.get("cuda_available"):
        command_config = build_sampler_command(
            python_executable=args.python_executable,
            output_dir=args.output_dir,
            run_id=run_id,
        )
        command_config["caps"]["timeout_seconds"] = args.timeout_seconds
        Path(command_config["ledger_path"]).unlink(missing_ok=True)
        command_result = run_command(command_config["command"], args.repo_root, args.timeout_seconds)
        summary["runs"]["gpu_sampler_probe"] = summarize_sampler_run(command_config, command_result)
    else:
        summary["runs"]["gpu_sampler_probe"] = {
            "status": "skipped",
            "returncode": None,
            "timed_out": False,
            "runtime_seconds": 0.0,
            "gpu_used": False,
            "reason": "PyTorch CUDA probe did not report an available CUDA device.",
            "train_log": parse_train_log(""),
            "ledger_records": 0,
            "metadata_complete": False,
            "model_sample_ledger_records": 0,
        }

    summary["recommendation"] = build_recommendation(summary)
    write_artifacts(summary, args.output_dir)
    print(build_report(summary))

    run = summary["runs"]["gpu_sampler_probe"]
    if run.get("returncode") not in {0, None}:
        return int(run.get("returncode") or 1)
    if args.strict and summary["recommendation"]["action"] != "proceed_to_medium_30_60_minute_gpu_run_later":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
