#!/usr/bin/env python3
"""Run a small proxy-only GPU readiness smoke for IGP24 Axplorer.

The helper checks GPU visibility, PyTorch CUDA support, a tiny CPU
data-generation baseline, and a tiny CUDA training path when PyTorch reports a
usable CUDA device. It does not run exact verifiers, call SAIR, use the network,
or promote exact group labels.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_benchmark import parse_valid_examples, read_jsonl, summarize_records


DEFAULT_OUTPUT_DIR = Path("/tmp/igp24_gpu_smoke_20260704")

TORCH_PROBE_CODE = r"""
import json

out = {
    "torch_imported": False,
    "torch_version": None,
    "cuda_available": False,
    "cuda_device_count": 0,
    "cuda_device_name": None,
    "cuda_total_memory_bytes": None,
    "cuda_capability": None,
    "cuda_tensor_ok": False,
    "error": None,
}

try:
    import torch

    out["torch_imported"] = True
    out["torch_version"] = torch.__version__
    out["cuda_available"] = bool(torch.cuda.is_available())
    out["cuda_device_count"] = int(torch.cuda.device_count())
    if out["cuda_available"]:
        props = torch.cuda.get_device_properties(0)
        out["cuda_device_name"] = torch.cuda.get_device_name(0)
        out["cuda_total_memory_bytes"] = int(props.total_memory)
        out["cuda_capability"] = list(torch.cuda.get_device_capability(0))
        tensor = torch.ones((1,), device="cuda")
        out["cuda_tensor_ok"] = bool(tensor.item() == 1.0)
        torch.cuda.synchronize()
except Exception as exc:
    out["error"] = repr(exc)

print(json.dumps(out, sort_keys=True))
"""


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def command_text(cmd: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in cmd)


def run_command(cmd: list[str], cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        timed_out = True
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

    elapsed = time.perf_counter() - start
    return {
        "command": [str(part) for part in cmd],
        "command_text": command_text(cmd),
        "returncode": returncode,
        "runtime_seconds": elapsed,
        "timed_out": timed_out,
        "stdout_tail": stdout.splitlines()[-30:],
        "stderr_tail": stderr.splitlines()[-30:],
        "stdout": stdout,
        "stderr": stderr,
    }


def nvidia_smi_command() -> list[str]:
    return [
        "nvidia-smi",
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader",
    ]


def parse_nvidia_smi_gpus(stdout: str) -> list[dict[str, Any]]:
    gpus = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(?P<name>.*?),\s*(?P<memory>\d+)\s+MiB,\s*(?P<driver>.*)$", line)
        if match:
            gpus.append(
                {
                    "name": match.group("name").strip(),
                    "memory_total_mib": int(match.group("memory")),
                    "driver_version": match.group("driver").strip(),
                }
            )
        else:
            gpus.append({"raw": line})
    return gpus


def torch_probe_command(python_executable: str) -> list[str]:
    return [python_executable, "-c", TORCH_PROBE_CODE]


def parse_torch_probe_stdout(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "cuda_available" in parsed:
            return parsed
    return None


def build_train_command(
    *,
    python_executable: str,
    output_dir: Path,
    run_id: str,
    label: str,
) -> dict[str, Any]:
    if label not in {"cpu_baseline", "gpu_train"}:
        raise ValueError(f"unknown smoke label: {label}")

    is_gpu = label == "gpu_train"
    exp_name = "igp24_gpu_smoke_train" if is_gpu else "igp24_gpu_smoke_cpu_baseline"
    dump_root = output_dir / f"{label}_dump"
    ledger_path = output_dir / ("gpu_candidates.jsonl" if is_gpu else "cpu_candidates.jsonl")
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
        "1701",
        "--coeff_bound",
        "4",
        "--gensize",
        "8",
        "--pop_size",
        "6",
        "--ntest",
        "2",
        "--gen_batch_size",
        "2",
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
        "--n_layer",
        "1",
        "--n_head",
        "2",
        "--n_embd",
        "32",
        "--max_len",
        "24",
        "--igp24_generation_strategy",
        "fixed_sparse_template",
        "--igp24_ledger_path",
        str(ledger_path),
    ]

    if is_gpu:
        cmd.extend(
            [
                "--max_epochs",
                "1",
                "--max_steps",
                "2",
                "--num_eval_steps",
                "2",
                "--num_samples_from_model",
                "4",
                "--batch_size",
                "2",
                "--cpu",
                "false",
            ]
        )
    else:
        cmd.extend(["--data_generation_only", "true", "--cpu", "true"])

    return {
        "label": label,
        "command": cmd,
        "dump_root": str(dump_root),
        "ledger_path": str(ledger_path),
        "train_log_path": str(train_log_path),
        "exp_name": exp_name,
        "exp_id": run_id,
    }


def inspect_train_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "logged_device": None,
            "cuda_memory_logged": False,
            "line_count": 0,
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    device_matches = re.findall(r"^device:\s*(.+)$", text, flags=re.MULTILINE)
    return {
        "exists": True,
        "logged_device": device_matches[-1].strip() if device_matches else None,
        "cuda_memory_logged": "Memory allocated:" in text and "reserved:" in text,
        "line_count": len(text.splitlines()),
    }


def summarize_train_result(label: str, command_result: dict[str, Any], ledger_path: Path, train_log_path: Path) -> dict[str, Any]:
    records = read_jsonl(ledger_path)
    ledger_summary = summarize_records(records)
    output = "\n".join(command_result.get("stdout_tail", []) + command_result.get("stderr_tail", []))
    log_summary = inspect_train_log(train_log_path)
    gpu_used = (
        label == "gpu_train"
        and command_result.get("returncode") == 0
        and log_summary.get("logged_device") == "cuda"
        and bool(log_summary.get("cuda_memory_logged"))
    )
    return {
        "label": label,
        "status": "completed",
        "returncode": command_result.get("returncode"),
        "timed_out": bool(command_result.get("timed_out")),
        "runtime_seconds": command_result.get("runtime_seconds"),
        "valid_candidates": parse_valid_examples(output),
        "ledger_path": str(ledger_path),
        "train_log_path": str(train_log_path),
        "train_log": log_summary,
        "gpu_used": gpu_used,
        "stdout_tail": command_result.get("stdout_tail", []),
        "stderr_tail": command_result.get("stderr_tail", []),
        **ledger_summary,
    }


def build_recommendation(summary: dict[str, Any]) -> dict[str, Any]:
    torch_probe = summary.get("probes", {}).get("torch_cuda", {}).get("parsed") or {}
    cpu_run = summary.get("runs", {}).get("cpu_baseline") or {}
    gpu_run = summary.get("runs", {}).get("gpu_train") or {}

    if cpu_run.get("returncode") not in {0, None}:
        return {
            "action": "fix_cpu_baseline_first",
            "reason": "The CPU proxy/data-generation baseline failed, so GPU training should wait.",
        }
    if not torch_probe.get("cuda_available"):
        return {
            "action": "keep_cpu_proxy_search_primary",
            "reason": "PyTorch does not report a usable CUDA device in this environment.",
        }
    if gpu_run.get("status") == "skipped":
        return {
            "action": "keep_cpu_proxy_search_primary",
            "reason": gpu_run.get("reason", "GPU training smoke was skipped."),
        }
    if gpu_run.get("returncode") != 0 or gpu_run.get("timed_out"):
        return {
            "action": "keep_cpu_proxy_search_primary",
            "reason": "The GPU-enabled training smoke did not complete cleanly.",
        }
    if not gpu_run.get("gpu_used"):
        return {
            "action": "keep_cpu_proxy_search_primary",
            "reason": "The training smoke completed, but the log did not prove CUDA execution.",
        }
    return {
        "action": "run_both_in_parallel",
        "reason": (
            "CUDA training works on the tiny smoke. Keep CPU proxy-search and exact-tool prep "
            "as the main candidate pipeline while using GPU training as a parallel sampler path."
        ),
    }


def _format_optional_float(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.2f}"


def build_report(summary: dict[str, Any]) -> str:
    probes = summary.get("probes", {})
    nvidia = probes.get("nvidia_smi", {})
    torch_probe = probes.get("torch_cuda", {}).get("parsed") or {}
    runs = summary.get("runs", {})
    recommendation = summary.get("recommendation", {})

    lines = [
        "# IGP24 GPU Smoke Report",
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
        f"- CUDA tensor smoke: `{torch_probe.get('cuda_tensor_ok')}`",
        "",
        "## Runs",
        "",
        "| run | status | returncode | runtime_s | valid | ledger | metadata | device | gpu_used |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for label in ["cpu_baseline", "gpu_train"]:
        run = runs.get(label, {})
        train_log = run.get("train_log") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    str(run.get("status", "missing")),
                    str(run.get("returncode", "NA")),
                    _format_optional_float(run.get("runtime_seconds")),
                    str(run.get("valid_candidates")),
                    str(run.get("ledger_records", "NA")),
                    str(run.get("metadata_complete", "NA")),
                    str(train_log.get("logged_device")),
                    str(run.get("gpu_used", "NA")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
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
    (output_dir / "gpu_smoke_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "gpu_smoke_report.md").write_text(build_report(summary), encoding="utf-8")


def run_train_smoke(
    *,
    args: argparse.Namespace,
    label: str,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = build_train_command(
        python_executable=args.python_executable,
        output_dir=args.output_dir,
        run_id=run_id,
        label=label,
    )
    ledger_path = Path(config["ledger_path"])
    ledger_path.unlink(missing_ok=True)
    result = run_command(config["command"], args.repo_root, args.timeout_seconds)
    summary = summarize_train_result(label, result, ledger_path, Path(config["train_log_path"]))
    summary["command"] = config["command"]
    summary["command_text"] = command_text(config["command"])
    return config, summary


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Proxy-only IGP24 GPU readiness and training smoke")
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    parser.add_argument("--python_executable", default=sys.executable)
    parser.add_argument("--timeout_seconds", type=int, default=180)
    parser.add_argument("--run_id", default="", help="Optional fixed experiment id; defaults to a UTC timestamp")
    parser.add_argument("--force_gpu_train", action="store_true", help="Run GPU train command even if the torch probe is negative")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when CUDA or the GPU training smoke fails")
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
        "probes": {},
        "runs": {},
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if shutil.which("nvidia-smi"):
        nvidia_result = run_command(nvidia_smi_command(), args.repo_root, args.timeout_seconds)
        nvidia_result["gpus"] = parse_nvidia_smi_gpus("\n".join(nvidia_result.get("stdout_tail", [])))
    else:
        nvidia_result = {
            "command": nvidia_smi_command(),
            "command_text": command_text(nvidia_smi_command()),
            "returncode": None,
            "runtime_seconds": 0.0,
            "timed_out": False,
            "stdout_tail": [],
            "stderr_tail": [],
            "gpus": [],
            "skipped": True,
            "reason": "nvidia-smi was not found on PATH",
        }
    summary["probes"]["nvidia_smi"] = nvidia_result
    write_artifacts(summary, args.output_dir)

    torch_result = run_command(torch_probe_command(args.python_executable), args.repo_root, args.timeout_seconds)
    torch_result["parsed"] = parse_torch_probe_stdout("\n".join(torch_result.get("stdout_tail", [])))
    summary["probes"]["torch_cuda"] = torch_result
    write_artifacts(summary, args.output_dir)

    _, cpu_summary = run_train_smoke(args=args, label="cpu_baseline", run_id=run_id)
    summary["runs"]["cpu_baseline"] = cpu_summary
    write_artifacts(summary, args.output_dir)

    torch_parsed = torch_result.get("parsed") or {}
    if args.force_gpu_train or torch_parsed.get("cuda_available"):
        _, gpu_summary = run_train_smoke(args=args, label="gpu_train", run_id=run_id)
        summary["runs"]["gpu_train"] = gpu_summary
    else:
        summary["runs"]["gpu_train"] = {
            "label": "gpu_train",
            "status": "skipped",
            "returncode": None,
            "runtime_seconds": 0.0,
            "timed_out": False,
            "valid_candidates": None,
            "ledger_records": 0,
            "metadata_complete": False,
            "gpu_used": False,
            "reason": "PyTorch CUDA probe did not report an available CUDA device.",
        }

    summary["recommendation"] = build_recommendation(summary)
    write_artifacts(summary, args.output_dir)
    print(build_report(summary))

    cpu_failed = summary["runs"]["cpu_baseline"].get("returncode") != 0
    gpu_action = summary["recommendation"].get("action")
    if cpu_failed:
        return int(summary["runs"]["cpu_baseline"].get("returncode") or 1)
    if args.strict and gpu_action != "run_both_in_parallel":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
