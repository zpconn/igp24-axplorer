import json

from scripts.igp24_gpu_sampler_probe import (
    DIVERSITY_EXPORT_VARIANTS,
    build_recommendation,
    build_sampler_command,
    build_sample_export_diversity_command,
    build_sample_export_split_command,
    build_sample_export_split_medium_command,
    build_train_only_utilization_command,
    load_baseline_summary,
    parse_gpu_utilization_sample,
    parse_sample_sections,
    parse_train_log,
    summarize_sample_export,
    summarize_model_sample_records,
)


def test_parse_sample_sections_counts_sample_validity():
    text = """
INFO - Sample with temperature 0.9 to 0.9
INFO - 0 / 512 samples generated, 0 scored
INFO - ### Score distribution ###
INFO - Invalid examples: before local search: 510, after: 509
INFO - Valid examples: 3
INFO - [Epoch 0 AFTER_SAMPLE] CPU: 0.0% | RAM: 1.0MB
"""

    sections = parse_sample_sections(text)

    assert sections == [
        {
            "requested": 512,
            "progress": [{"generated": 0, "requested": 512, "scored": 0}],
            "valid": 3,
            "invalid_before_local_search": 510,
            "invalid_after_local_search": 509,
            "no_valid_examples_logged": False,
        }
    ]


def test_parse_train_log_extracts_loss_memory_and_sampling():
    text = """
INFO - device: cuda
INFO - ==== Starting Epoch 0 =====
INFO - Memory allocated: 10.00MB, reserved: 20.00MB
INFO - step 25 train loss: 1.5 test loss: 1.6
INFO - step 100 | loss 1.1000 | steps time 123.45ms
INFO - step 100 train loss: 1.0 test loss: 1.2
INFO - Sample with temperature 0.9 to 0.9
INFO - 0 / 512 samples generated, 0 scored
INFO - Invalid examples: before local search: 512, after: 512
INFO - No valid examples
INFO - [Epoch 0 AFTER_SAMPLE] CPU: 0.0% | RAM: 1.0MB
"""

    parsed = parse_train_log(text)

    assert parsed["logged_device"] == "cuda"
    assert parsed["epoch_count"] == 1
    assert parsed["cuda_memory_logged"]
    assert parsed["max_cuda_reserved_mb"] == 20.0
    assert parsed["eval_losses"][-1] == {"step": 100, "train_loss": 1.0, "test_loss": 1.2}
    assert parsed["step_losses"] == [{"step": 100, "loss": 1.1, "step_time_ms": 123.45}]
    assert parsed["sample_requested_total"] == 512
    assert parsed["sample_valid_total"] == 0


def test_parse_train_log_detects_train_only_skip():
    text = """
INFO - device: cuda
INFO - ==== Starting Epoch 0 =====
INFO - Memory allocated: 30.00MB, reserved: 90.00MB
INFO - step 60 train loss: 1.5 test loss: 1.6
INFO - Train-only mode. Skipping sampling, scoring, local search, and dataset update for this epoch.
"""

    parsed = parse_train_log(text)

    assert parsed["train_only_skip_logged"]
    assert parsed["sample_requested_total"] == 0
    assert parsed["sample_valid_total"] == 0


def test_parse_train_log_detects_sample_export_only():
    text = """
INFO - device: cuda
INFO - ==== Starting Epoch 0 =====
INFO - Memory allocated: 30.00MB, reserved: 90.00MB
INFO - step 60 train loss: 1.5 test loss: 1.6
INFO - Export-only model sampling to /tmp/samples.jsonl
INFO - Export-only model sampling wrote 16 records to /tmp/samples.jsonl; decoded=12 invalid_decode=4
"""

    parsed = parse_train_log(text)

    assert parsed["sample_export_only_logged"]
    assert parsed["sample_requested_total"] == 0
    assert parsed["sample_valid_total"] == 0


def test_summarize_model_sample_records_filters_null_strategy():
    records = [
        {"score": 10.0, "canonical_hash": "a", "generation_metadata": {"strategy": "fixed_sparse_template"}},
        {"score": 12.0, "canonical_hash": "b", "generation_metadata": {"strategy": None}},
        {"score": 14.0, "canonical_hash": "c", "generation_metadata": {"strategy": "manual"}},
    ]

    summary = summarize_model_sample_records(records)

    assert summary["model_sample_ledger_records"] == 2
    assert summary["model_sample_best_score"] == 14.0
    assert summary["model_sample_mean_score"] == 13.0
    assert summary["model_sample_hashes"] == ["b", "c"]


def test_parse_gpu_utilization_sample_reads_nvidia_smi_query():
    sample = parse_gpu_utilization_sample("42, 2676, 71.23\n")

    assert sample == {
        "gpu_utilization_percent": 42.0,
        "memory_used_mib": 2676.0,
        "power_draw_watts": 71.23,
    }
    assert parse_gpu_utilization_sample("not csv") is None


def test_build_sampler_command_is_capped_gpu_and_proxy_only(tmp_path):
    config = build_sampler_command(python_executable="python3", output_dir=tmp_path, run_id="run")
    command = config["command"]

    assert command[command.index("--cpu") + 1] == "false"
    assert command[command.index("--max_epochs") + 1] == "2"
    assert command[command.index("--max_steps") + 1] == "100"
    assert command[command.index("--num_samples_from_model") + 1] == "512"
    assert command[command.index("--igp24_generation_strategy") + 1] == "fixed_sparse_template"
    assert all("sair" not in str(part).lower() for part in command)
    assert all("magma" not in str(part).lower() for part in command)
    assert all("pari" not in str(part).lower() for part in command)


def test_build_train_only_utilization_command_skips_sampling(tmp_path):
    config = build_train_only_utilization_command(python_executable="python3", output_dir=tmp_path, run_id="run")
    command = config["command"]

    assert config["probe_mode"] == "train_only_utilization"
    assert config["post_train_cpu_sampling_scoring_avoided"]
    assert command[command.index("--cpu") + 1] == "false"
    assert command[command.index("--train_only") + 1] == "true"
    assert command[command.index("--num_samples_from_model") + 1] == "0"
    assert command[command.index("--always_search") + 1] == "false"
    assert command[command.index("--max_local_search_steps") + 1] == "0"
    assert int(command[command.index("--batch_size") + 1]) >= 128
    assert int(command[command.index("--n_embd") + 1]) >= 512
    assert all("sair" not in str(part).lower() for part in command)
    assert all("magma" not in str(part).lower() for part in command)
    assert all("pari" not in str(part).lower() for part in command)


def test_build_sample_export_split_command_is_export_only(tmp_path):
    config = build_sample_export_split_command(python_executable="python3", output_dir=tmp_path, run_id="run")
    command = config["command"]

    assert config["probe_mode"] == "sample_export_split"
    assert config["post_train_cpu_sampling_scoring_avoided"]
    assert command[command.index("--cpu") + 1] == "false"
    assert command[command.index("--sample_export_only") + 1] == "true"
    assert command[command.index("--num_samples_from_model") + 1] == "1024"
    assert command[command.index("--always_search") + 1] == "false"
    assert command[command.index("--max_local_search_steps") + 1] == "0"
    assert int(command[command.index("--batch_size") + 1]) >= 256
    assert "--sample_export_path" in command
    assert all("sair" not in str(part).lower() for part in command)
    assert all("magma" not in str(part).lower() for part in command)
    assert all("pari" not in str(part).lower() for part in command)


def test_build_sample_export_split_medium_command_is_bounded_export_only(tmp_path):
    config = build_sample_export_split_medium_command(python_executable="python3", output_dir=tmp_path, run_id="run")
    command = config["command"]

    assert config["probe_mode"] == "sample_export_split_medium"
    assert config["post_train_cpu_sampling_scoring_avoided"]
    assert config["caps"]["timeout_seconds"] == 3600
    assert config["caps"]["max_epochs"] == 1
    assert 1024 < config["caps"]["num_samples_from_model_per_epoch"] <= 10000
    assert config["caps"]["max_steps_per_epoch"] <= 12000
    assert command[command.index("--cpu") + 1] == "false"
    assert command[command.index("--sample_export_only") + 1] == "true"
    assert command[command.index("--num_samples_from_model") + 1] == "8192"
    assert command[command.index("--always_search") + 1] == "false"
    assert command[command.index("--max_local_search_steps") + 1] == "0"
    assert command[command.index("--process_pool") + 1] == "false"
    assert int(command[command.index("--gensize") + 1]) <= 512
    assert int(command[command.index("--pop_size") + 1]) <= 384
    assert command[command.index("--max_epochs") + 1] == "1"
    assert int(command[command.index("--batch_size") + 1]) >= 512
    assert int(command[command.index("--n_embd") + 1]) >= 768
    assert "--sample_export_path" in command
    assert all("sair" not in str(part).lower() for part in command)
    assert all("magma" not in str(part).lower() for part in command)
    assert all("pari" not in str(part).lower() for part in command)


def test_build_sample_export_diversity_commands_are_bounded_export_only(tmp_path):
    configs = [
        build_sample_export_diversity_command(
            python_executable="python3",
            output_dir=tmp_path / variant,
            run_id="run",
            diversity_variant=variant,
        )
        for variant in DIVERSITY_EXPORT_VARIANTS
    ]

    assert {config["diversity_variant"] for config in configs} == set(DIVERSITY_EXPORT_VARIANTS)
    strategies = {
        config["diversity_variant"]: config["command"][config["command"].index("--igp24_generation_strategy") + 1]
        for config in configs
    }
    assert strategies["fixed_template_t09_top9"] == "fixed_sparse_template"
    assert strategies["fixed_template_t10_top32"] == "fixed_sparse_template"
    assert strategies["fixed_template_t11_open_topk"] == "fixed_sparse_template"
    assert strategies["mixed_t12_open_topk"] == "mixed"
    by_variant = {config["diversity_variant"]: config for config in configs}
    assert by_variant["fixed_template_t10_top32"]["caps"]["temperature"] == 1.0
    assert by_variant["fixed_template_t10_top32"]["caps"]["top_k"] == 32
    assert by_variant["fixed_template_t11_open_topk"]["caps"]["temperature"] == 1.1
    assert by_variant["fixed_template_t11_open_topk"]["caps"]["top_k"] == -1
    for config in configs:
        command = config["command"]
        assert config["probe_mode"] == "sample_export_split_diversity"
        assert config["post_train_cpu_sampling_scoring_avoided"]
        assert config["caps"]["timeout_seconds"] == 900
        assert config["caps"]["max_epochs"] == 1
        assert config["caps"]["num_samples_from_model_per_epoch"] == 2048
        assert config["caps"]["max_steps_per_epoch"] == 1200
        assert command[command.index("--cpu") + 1] == "false"
        assert command[command.index("--sample_export_only") + 1] == "true"
        assert command[command.index("--num_samples_from_model") + 1] == "2048"
        assert command[command.index("--always_search") + 1] == "false"
        assert command[command.index("--max_local_search_steps") + 1] == "0"
        assert command[command.index("--process_pool") + 1] == "false"
        assert "--sample_export_path" in command
        assert all("sair" not in str(part).lower() for part in command)
        assert all("magma" not in str(part).lower() for part in command)
        assert all("pari" not in str(part).lower() for part in command)


def test_build_sample_export_diversity_command_accepts_seed_override(tmp_path):
    config = build_sample_export_diversity_command(
        python_executable="python3",
        output_dir=tmp_path,
        run_id="run",
        diversity_variant="fixed_template_t09_top9",
        diversity_seed=2301,
    )

    command = config["command"]
    assert command[command.index("--seed") + 1] == "2301"
    assert config["diversity_seed"] == "2301"
    assert config["caps"]["seed"] == 2301
    assert "seed2301" in config["sample_export_path"]
    assert "seed2301" in config["command_text"]
    assert command[command.index("--sample_export_only") + 1] == "true"
    assert command[command.index("--always_search") + 1] == "false"
    assert command[command.index("--max_local_search_steps") + 1] == "0"


def test_summarize_sample_export_reads_safety_flags(tmp_path):
    path = tmp_path / "samples.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "sample_index": 0,
                        "decoded": True,
                        "safety": {
                            "scored": False,
                            "local_search_run": False,
                            "runs_exact_verifiers": False,
                        },
                    }
                ),
                json.dumps(
                    {
                        "sample_index": 1,
                        "decoded": False,
                        "safety": {
                            "scored": False,
                            "local_search_run": False,
                            "runs_exact_verifiers": False,
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = summarize_sample_export(path)

    assert summary["sample_export_records"] == 2
    assert summary["sample_export_decoded_records"] == 1
    assert summary["sample_export_invalid_decode_records"] == 1
    assert summary["sample_export_scoring_avoided"]
    assert summary["sample_export_local_search_avoided"]
    assert summary["sample_export_exact_verifiers_avoided"]


def test_build_recommendation_advances_only_with_valid_model_samples():
    base = {
        "probes": {"torch_cuda": {"parsed": {"cuda_available": True}}},
        "runs": {
            "gpu_sampler_probe": {
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "gpu_used": True,
                "gpu_monitor": {"max_gpu_utilization_percent": 0.0},
                "model_sample_ledger_records": 0,
                "train_log": {
                    "eval_losses": [
                        {"step": 25, "train_loss": 2.0, "test_loss": 2.1},
                        {"step": 50, "train_loss": 1.8, "test_loss": 1.9},
                    ],
                    "sample_valid_total": 0,
                },
            }
        },
    }

    assert build_recommendation(base)["action"] == "run_another_short_gpu_probe_with_adjusted_settings"
    base["runs"]["gpu_sampler_probe"]["interrupted"] = True
    assert build_recommendation(base)["action"] == "run_another_short_gpu_probe_with_adjusted_settings"
    base["runs"]["gpu_sampler_probe"]["interrupted"] = False
    base["runs"]["gpu_sampler_probe"]["model_sample_ledger_records"] = 2
    base["runs"]["gpu_sampler_probe"]["train_log"]["sample_valid_total"] = 2
    assert build_recommendation(base)["action"] == "run_another_short_gpu_probe_with_adjusted_settings"
    base["runs"]["gpu_sampler_probe"]["gpu_monitor"]["max_gpu_utilization_percent"] = 25.0
    assert build_recommendation(base)["action"] == "proceed_to_medium_30_60_minute_gpu_run_later"


def test_build_recommendation_for_train_only_utilization():
    base = {
        "probe_mode": "train_only_utilization",
        "probes": {"torch_cuda": {"parsed": {"cuda_available": True}}},
        "runs": {
            "gpu_sampler_probe": {
                "probe_mode": "train_only_utilization",
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "gpu_used": True,
                "post_train_cpu_sampling_scoring_avoided": True,
                "gpu_monitor": {"max_gpu_utilization_percent": 0.0},
                "model_sample_ledger_records": 0,
                "train_log": {
                    "eval_losses": [
                        {"step": 60, "train_loss": 2.0, "test_loss": 2.1},
                        {"step": 120, "train_loss": 1.8, "test_loss": 1.9},
                    ],
                    "sample_valid_total": 0,
                },
            }
        },
    }

    assert build_recommendation(base)["action"] == "investigate_gpu_workload_shape_before_gpu_training"
    base["runs"]["gpu_sampler_probe"]["gpu_monitor"]["max_gpu_utilization_percent"] = 25.0
    assert build_recommendation(base)["action"] == "decouple_gpu_training_from_cpu_scoring"


def test_build_recommendation_for_sample_export_split():
    base = {
        "probe_mode": "sample_export_split",
        "probes": {"torch_cuda": {"parsed": {"cuda_available": True}}},
        "runs": {
            "gpu_sampler_probe": {
                "probe_mode": "sample_export_split",
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "gpu_used": True,
                "post_train_cpu_sampling_scoring_avoided": True,
                "sample_export_records": 16,
                "sample_export_decoded_records": 12,
                "model_sample_ledger_records": 0,
                "train_log": {
                    "eval_losses": [
                        {"step": 60, "train_loss": 2.0, "test_loss": 2.1},
                        {"step": 120, "train_loss": 1.8, "test_loss": 1.9},
                    ],
                    "sample_valid_total": 0,
                },
            }
        },
    }

    assert build_recommendation(base)["action"] == "consume_exported_samples_with_cpu_proxy_helper"
    base["runs"]["gpu_sampler_probe"]["sample_export_decoded_records"] = 0
    assert build_recommendation(base)["action"] == "run_another_short_gpu_probe_with_adjusted_settings"


def test_build_recommendation_for_sample_export_split_medium():
    base = {
        "probe_mode": "sample_export_split_medium",
        "probes": {"torch_cuda": {"parsed": {"cuda_available": True}}},
        "runs": {
            "gpu_sampler_probe": {
                "probe_mode": "sample_export_split_medium",
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "gpu_used": True,
                "post_train_cpu_sampling_scoring_avoided": True,
                "sample_export_records": 8192,
                "sample_export_decoded_records": 8100,
                "model_sample_ledger_records": 0,
                "train_log": {
                    "eval_losses": [
                        {"step": 600, "train_loss": 2.0, "test_loss": 2.1},
                        {"step": 1200, "train_loss": 1.8, "test_loss": 1.9},
                    ],
                    "sample_valid_total": 0,
                },
            }
        },
    }

    assert build_recommendation(base)["action"] == "consume_exported_samples_with_cpu_proxy_helper"


def test_build_recommendation_for_sample_export_diversity_variant():
    base = {
        "probe_mode": "sample_export_split_diversity",
        "probes": {"torch_cuda": {"parsed": {"cuda_available": True}}},
        "runs": {
            "gpu_sampler_probe": {
                "probe_mode": "sample_export_split_diversity",
                "diversity_variant": "mixed_t12_open_topk",
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "gpu_used": True,
                "post_train_cpu_sampling_scoring_avoided": True,
                "sample_export_records": 2048,
                "sample_export_decoded_records": 1900,
                "model_sample_ledger_records": 0,
                "train_log": {
                    "eval_losses": [
                        {"step": 300, "train_loss": 2.0, "test_loss": 2.1},
                        {"step": 600, "train_loss": 1.8, "test_loss": 1.9},
                    ],
                    "sample_valid_total": 0,
                },
            }
        },
    }

    assert build_recommendation(base)["action"] == "consume_exported_samples_with_cpu_proxy_helper"


def test_load_baseline_summary_reads_relevant_context(tmp_path):
    path = tmp_path / "summary.json"
    path.write_text(
        json.dumps(
            {
                "recommendation": {"action": "run_both_in_parallel"},
                "runs": {
                    "cpu_baseline": {"returncode": 0, "runtime_seconds": 2.0, "valid_candidates": 7, "ledger_records": 12},
                    "gpu_train": {
                        "returncode": 0,
                        "runtime_seconds": 4.0,
                        "valid_candidates": 4,
                        "ledger_records": 12,
                        "gpu_used": True,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_baseline_summary(path)

    assert loaded["recommendation"]["action"] == "run_both_in_parallel"
    assert loaded["cpu_baseline"]["valid_candidates"] == 7
    assert loaded["gpu_smoke"]["gpu_used"]
