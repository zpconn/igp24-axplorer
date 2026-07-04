import json

from scripts.igp24_gpu_smoke import (
    build_recommendation,
    build_train_command,
    inspect_train_log,
    parse_nvidia_smi_gpus,
    parse_torch_probe_stdout,
    summarize_train_result,
)


def test_parse_nvidia_smi_gpus_extracts_query_rows():
    rows = "NVIDIA GeForce RTX 5090, 32607 MiB, 575.64.03\n"

    assert parse_nvidia_smi_gpus(rows) == [
        {
            "name": "NVIDIA GeForce RTX 5090",
            "memory_total_mib": 32607,
            "driver_version": "575.64.03",
        }
    ]


def test_parse_torch_probe_stdout_uses_last_json_line():
    stdout = "noise\n" + json.dumps({"cuda_available": True, "torch_version": "2.x"}) + "\n"

    assert parse_torch_probe_stdout(stdout) == {"cuda_available": True, "torch_version": "2.x"}
    assert parse_torch_probe_stdout("no json here") is None


def test_build_train_command_keeps_cpu_and_gpu_modes_separate(tmp_path):
    cpu = build_train_command(
        python_executable="python3",
        output_dir=tmp_path,
        run_id="run",
        label="cpu_baseline",
    )
    gpu = build_train_command(
        python_executable="python3",
        output_dir=tmp_path,
        run_id="run",
        label="gpu_train",
    )

    assert "--cpu" in cpu["command"]
    assert cpu["command"][cpu["command"].index("--cpu") + 1] == "true"
    assert "--data_generation_only" in cpu["command"]
    assert "--cpu" in gpu["command"]
    assert gpu["command"][gpu["command"].index("--cpu") + 1] == "false"
    assert "--data_generation_only" not in gpu["command"]
    assert "fixed_sparse_template" in cpu["command"]
    assert "fixed_sparse_template" in gpu["command"]
    assert all("sair" not in str(part).lower() for part in cpu["command"] + gpu["command"])
    assert all("magma" not in str(part).lower() for part in cpu["command"] + gpu["command"])
    assert all("pari" not in str(part).lower() for part in cpu["command"] + gpu["command"])


def test_inspect_train_log_and_summarize_train_result(tmp_path):
    ledger = tmp_path / "candidates.jsonl"
    ledger.write_text(
        json.dumps(
            {
                "score": 12.0,
                "canonical_hash": "abc",
                "generation_metadata": {"strategy": "fixed_sparse_template"},
                "local_search_metadata": {"attempted": 2, "accepted": 1},
                "score_components": {"final_score": 12.0},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    log = tmp_path / "train.log"
    log.write_text(
        "INFO - 07/04/26 11:21:29 - 0:00:01 - device: cuda\n"
        "INFO - 07/04/26 11:21:29 - 0:00:01 - Memory allocated: 1.00MB, reserved: 2.00MB\n",
        encoding="utf-8",
    )
    result = {
        "returncode": 0,
        "runtime_seconds": 1.25,
        "timed_out": False,
        "stdout_tail": ["INFO - Valid examples: 1"],
        "stderr_tail": [],
    }

    assert inspect_train_log(log)["logged_device"] == "cuda"
    summary = summarize_train_result("gpu_train", result, ledger, log)

    assert summary["returncode"] == 0
    assert summary["valid_candidates"] == 1
    assert summary["ledger_records"] == 1
    assert summary["metadata_complete"]
    assert summary["gpu_used"]


def test_build_recommendation_keeps_cpu_when_cuda_unavailable():
    summary = {
        "probes": {"torch_cuda": {"parsed": {"cuda_available": False}}},
        "runs": {"cpu_baseline": {"returncode": 0}, "gpu_train": {"status": "skipped"}},
    }

    recommendation = build_recommendation(summary)

    assert recommendation["action"] == "keep_cpu_proxy_search_primary"


def test_build_recommendation_runs_both_after_clean_gpu_smoke():
    summary = {
        "probes": {"torch_cuda": {"parsed": {"cuda_available": True}}},
        "runs": {
            "cpu_baseline": {"returncode": 0},
            "gpu_train": {
                "status": "completed",
                "returncode": 0,
                "timed_out": False,
                "gpu_used": True,
            },
        },
    }

    recommendation = build_recommendation(summary)

    assert recommendation["action"] == "run_both_in_parallel"
