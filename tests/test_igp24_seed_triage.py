import argparse
import json

from scripts.igp24_seed_triage import (
    RECOMMEND_AMBIGUOUS,
    RECOMMEND_PROMOTE,
    RECOMMEND_REJECT,
    build_probe_command,
    build_report,
    build_summary,
    load_seed_result,
    parse_known_outcomes,
    recommend_seed,
    thresholds_from_args,
)


def _thresholds():
    return {
        "promote_max_attempts_per_unique": 1.08,
        "promote_max_duplicate_skip_rate": 0.05,
        "reject_min_attempts_per_unique": 1.15,
        "reject_min_duplicate_skip_rate": 0.12,
        "reject_max_unique_fraction_on_budget_exhausted": 0.90,
    }


def test_build_probe_command_uses_existing_dedup_helper_mode(tmp_path):
    command = build_probe_command(
        python_executable="python3",
        seed=2404,
        output_dir=tmp_path,
        diversity_variant="fixed_template_t11_open_topk",
        unique_target=256,
        max_attempts=1024,
        progress_interval=128,
        timeout_seconds=900,
        monitor_interval_seconds=2.0,
    )

    assert command[:2] == ["python3", "scripts/igp24_gpu_sampler_probe.py"]
    assert command[command.index("--probe_mode") + 1] == "sample_export_split_dedup"
    assert command[command.index("--diversity_variant") + 1] == "fixed_template_t11_open_topk"
    assert command[command.index("--diversity_seed") + 1] == "2404"
    assert command[command.index("--dedup_unique_target") + 1] == "256"
    assert command[command.index("--dedup_max_attempts") + 1] == "1024"
    assert command[command.index("--dedup_progress_interval") + 1] == "128"
    assert "seed2404" in command[command.index("--output_dir") + 1]
    assert all("sair" not in part.lower() for part in command)
    assert all("magma" not in part.lower() for part in command)
    assert all("pari" not in part.lower() for part in command)


def test_recommend_seed_promotes_rejects_and_marks_ambiguous():
    thresholds = _thresholds()

    promote, promote_reason = recommend_seed(
        {
            "returncode": 0,
            "unique_decoded_count": 256,
            "unique_target": 256,
            "stop_reason": "unique_target_reached",
            "attempts_per_unique": 1.047,
            "duplicate_skip_rate": 0.041,
        },
        thresholds,
    )
    assert promote == RECOMMEND_PROMOTE
    assert "target reached" in promote_reason

    reject, reject_reason = recommend_seed(
        {
            "returncode": 0,
            "unique_decoded_count": 180,
            "unique_target": 256,
            "stop_reason": "attempt_budget_exhausted",
            "attempts_per_unique": 4.2,
            "duplicate_skip_rate": 0.72,
        },
        thresholds,
    )
    assert reject == RECOMMEND_REJECT
    assert "below the unique target" in reject_reason

    ambiguous, ambiguous_reason = recommend_seed(
        {
            "returncode": 0,
            "unique_decoded_count": 256,
            "unique_target": 256,
            "stop_reason": "unique_target_reached",
            "attempts_per_unique": 1.109,
            "duplicate_skip_rate": 0.072,
        },
        thresholds,
    )
    assert ambiguous == RECOMMEND_AMBIGUOUS
    assert "not clearly low" in ambiguous_reason

    early_duplicate_heavy, early_duplicate_heavy_reason = recommend_seed(
        {
            "returncode": 0,
            "unique_decoded_count": 256,
            "unique_target": 256,
            "stop_reason": "unique_target_reached",
            "attempts_per_unique": 1.160,
            "duplicate_skip_rate": 0.138,
        },
        thresholds,
    )
    assert early_duplicate_heavy == RECOMMEND_REJECT
    assert "high duplicate pressure" in early_duplicate_heavy_reason


def test_load_seed_result_reads_probe_and_sidecar_summary(tmp_path):
    seed_dir = tmp_path / "seed2405"
    seed_dir.mkdir()
    export_path = seed_dir / "samples.jsonl"
    sidecar_path = seed_dir / "samples.jsonl.summary.json"
    sidecar_path.write_text(
        json.dumps(
            {
                "attempt_budget": 1024,
                "attempted_samples": 268,
                "decoded_attempts": 267,
                "invalid_decode_attempts": 1,
                "invalid_decode_records": 1,
                "records_written": 257,
                "decoded_records": 256,
                "unique_target": 256,
                "unique_decoded_coefficients": 256,
                "duplicate_decoded_records_skipped": 11,
                "stop_reason": "unique_target_reached",
                "dataset_update_avoided": True,
            }
        ),
        encoding="utf-8",
    )
    summary_path = seed_dir / "gpu_sampler_probe_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "runs": {
                    "gpu_sampler_probe": {
                        "returncode": 0,
                        "timed_out": False,
                        "interrupted": False,
                        "runtime_seconds": 12.5,
                        "sample_export_path": str(export_path),
                        "sample_export_summary_path": str(sidecar_path),
                        "sample_export_attempt_budget": 1024,
                        "sample_export_attempted_samples": 268,
                        "sample_export_records": 257,
                        "sample_export_decoded_records": 256,
                        "sample_export_invalid_decode_records": 1,
                        "sample_export_unique_target": 256,
                        "sample_export_unique_decoded_coefficients": 256,
                        "sample_export_duplicate_decoded_records_skipped": 11,
                        "sample_export_stop_reason": "unique_target_reached",
                        "sample_export_scoring_avoided": True,
                        "sample_export_local_search_avoided": True,
                        "train_log": {"logged_device": "cuda"},
                        "gpu_monitor": {
                            "max_gpu_utilization_percent": 99.0,
                            "avg_gpu_utilization_percent": 80.0,
                            "max_memory_used_mib": 10000,
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = load_seed_result(
        seed=2405,
        summary_path=summary_path,
        thresholds=_thresholds(),
        known_outcome="acceptable_full_run_seed",
    )

    assert result["seed"] == 2405
    assert result["known_full_run_outcome"] == "acceptable_full_run_seed"
    assert result["attempted_samples"] == 268
    assert result["unique_decoded_count"] == 256
    assert result["duplicate_skipped_count"] == 11
    assert result["attempts_per_unique"] == 268 / 256
    assert result["duplicate_skip_rate"] == 11 / 267
    assert result["recommendation"] == RECOMMEND_PROMOTE
    assert result["scoring_avoided"] is True
    assert result["local_search_avoided"] is True
    assert result["dataset_update_avoided"] is True


def test_build_report_includes_metrics_and_known_outcomes(tmp_path):
    args = argparse.Namespace(
        output_dir=tmp_path,
        repo_root=tmp_path,
        diversity_variant="fixed_template_t11_open_topk",
        unique_target=256,
        max_attempts=1024,
        progress_interval=128,
        timeout_seconds=900,
        monitor_interval_seconds=2.0,
    )
    result = {
        "seed": 2406,
        "known_full_run_outcome": "duplicate_heavy_full_run_seed",
        "recommendation": RECOMMEND_REJECT,
        "recommendation_reason": "attempt budget exhausted with high duplicate pressure",
        "attempted_samples": 1024,
        "unique_decoded_count": 180,
        "duplicate_skipped_count": 830,
        "invalid_decode_count": 14,
        "stop_reason": "attempt_budget_exhausted",
        "attempts_per_unique": 5.688,
        "duplicate_skip_rate": 0.82,
        "max_gpu_utilization_percent": 99.0,
        "avg_gpu_utilization_percent": 81.0,
    }
    summary = build_summary(
        seeds=[2406],
        results=[result],
        args=args,
        thresholds=_thresholds(),
        commands={2406: ["python3", "scripts/igp24_gpu_sampler_probe.py"]},
    )
    summary["artifacts"] = {"summary_path": "summary.json", "records_path": "records.jsonl"}

    report = build_report(summary)

    assert "IGP24 Seed Triage Report" in report
    assert "duplicate_heavy_full_run_seed" in report
    assert RECOMMEND_REJECT in report
    assert "5.688" in report
    assert "0.820" in report


def test_parse_known_outcomes_and_thresholds_from_args():
    assert parse_known_outcomes(["2404=good", "2406=duplicate_heavy"]) == {
        2404: "good",
        2406: "duplicate_heavy",
    }

    args = argparse.Namespace(
        promote_max_attempts_per_unique=1.5,
        promote_max_duplicate_skip_rate=0.25,
        reject_min_attempts_per_unique=2.5,
        reject_min_duplicate_skip_rate=0.55,
        reject_max_unique_fraction_on_budget_exhausted=0.8,
    )
    assert thresholds_from_args(args) == {
        "promote_max_attempts_per_unique": 1.5,
        "promote_max_duplicate_skip_rate": 0.25,
        "reject_min_attempts_per_unique": 2.5,
        "reject_min_duplicate_skip_rate": 0.55,
        "reject_max_unique_fraction_on_budget_exhausted": 0.8,
    }
