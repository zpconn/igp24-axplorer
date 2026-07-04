import argparse

from scripts.igp24_score_sample_export import (
    build_report,
    build_split_manifest,
    build_split_report,
    extract_decoded_coefficients,
    get_parser,
    score_export_records,
    summarize_scored_records,
)
from src.evaluator import build_sample_export_record


def test_build_sample_export_record_marks_unscored_and_safe():
    args = argparse.Namespace(
        env_name="igp24",
        exp_name="exp",
        exp_id="run",
        device="cuda",
        max_len=24,
        coeff_bound=4,
        igp24_generation_strategy="fixed_sparse_template",
        igp24_generation_preset="none",
    )

    record = build_sample_export_record(
        sample_index=3,
        batch_index=1,
        batch_row=2,
        token_ids=[1, 2, 3],
        decoded_coefficients=[0] * 24,
        args=args,
        temperature=0.9,
        top_k=9,
    )

    assert record["record_type"] == "igp24_model_sample_export"
    assert record["decoded"]
    assert record["exported_coefficients"] == [0] * 24 + [1]
    assert record["score"] is None
    assert record["scoring_status"] == "unscored"
    assert record["local_search_status"] == "not_run"
    assert not record["safety"]["scored"]
    assert not record["safety"]["local_search_run"]
    assert not record["safety"]["runs_exact_verifiers"]
    assert not record["safety"]["calls_sair"]
    assert not record["safety"]["auto_submits"]


def test_extract_decoded_coefficients_accepts_decoded_or_exported():
    decoded = {"decoded_coefficients": list(range(24))}
    exported = {"exported_coefficients": list(range(24)) + [1]}

    assert extract_decoded_coefficients(decoded) == list(range(24))
    assert extract_decoded_coefficients(exported) == list(range(24))
    assert extract_decoded_coefficients({"decoded_coefficients": [1, 2]}) is None
    assert extract_decoded_coefficients({"exported_coefficients": list(range(25))}) is None


def test_score_export_records_consumes_decoded_samples_without_local_search():
    args = argparse.Namespace(
        coeff_bound=4,
        target_r=None,
        target_t=None,
        prime_limit=5,
        max_local_search_steps=0,
        discriminant_weight=1.0,
        height_weight=1.0,
        cycle_diversity_weight=5.0,
        exact_score_timeout=1.0,
        exp_name="test_score_export",
        seed=123,
        translation_radius=1,
        max_records=2,
        score_all=False,
        local_search=False,
    )
    records = [
        {"sample_index": 0, "decoded_coefficients": [1] + [0] * 23, "temperature": 0.9, "top_k": 9, "device": "cuda"},
        {"sample_index": 1, "decoded_coefficients": None},
    ]

    scored, summary = score_export_records(records, args=args, source_path="samples.jsonl")

    assert summary["records_read"] == 2
    assert summary["records_selected"] == 2
    assert summary["skipped_decode_records"] == 1
    assert summary["scored_records"] == len(scored)
    assert summary["selection_mode"] == "capped"
    assert summary["local_search_enabled"] is False
    assert summary["safety"]["proxy_only"]
    assert not summary["safety"]["runs_exact_verifiers"]
    assert not summary["safety"]["calls_sair"]
    assert not summary["safety"]["auto_submits"]
    assert all(record["generation_metadata"]["strategy"] == "model_sample_export" for record in scored)


def test_score_all_mode_selects_every_exported_record_and_manifest_records_mode():
    args = argparse.Namespace(
        coeff_bound=4,
        target_r=None,
        target_t=None,
        prime_limit=5,
        max_local_search_steps=0,
        discriminant_weight=1.0,
        height_weight=1.0,
        cycle_diversity_weight=5.0,
        exact_score_timeout=1.0,
        exp_name="test_score_export_all",
        seed=123,
        translation_radius=1,
        max_records=None,
        score_all=True,
        local_search=False,
    )
    records = [
        {"sample_index": 0, "decoded_coefficients": [1] + [0] * 23, "temperature": 0.9, "top_k": 9, "device": "cuda"},
        {"sample_index": 1, "decoded_coefficients": [0, 1] + [0] * 22, "temperature": 0.9, "top_k": 9, "device": "cuda"},
        {"sample_index": 2, "decoded_coefficients": None, "temperature": 0.9, "top_k": 9, "device": "cuda"},
    ]

    scored, summary = score_export_records(records, args=args, source_path="samples.jsonl")
    manifest = build_split_manifest(
        score_summary=summary,
        gpu_summary=None,
        gpu_summary_path=None,
        source_commit="abc123",
        score_command="python3 scripts/igp24_score_sample_export.py --score_all true",
    )

    assert summary["records_read"] == 3
    assert summary["records_selected"] == 3
    assert summary["selection_mode"] == "all_explicit"
    assert summary["score_all"] is True
    assert summary["max_records"] is None
    assert summary["skipped_decode_records"] == 1
    assert summary["scored_records"] == len(scored)
    assert manifest["cpu_phase"]["selection_mode"] == "all_explicit"
    assert manifest["cpu_phase"]["max_records"] is None
    assert manifest["cpu_phase"]["records_selected"] == 3
    assert "--score_all true" in manifest["commands"]["cpu_score"]


def test_summarize_scored_records_counts_duplicate_hashes():
    records = [
        {"canonical_hash": "a", "score": 10.0, "verification_status": "proxy_scored"},
        {"canonical_hash": "a", "score": 12.0, "verification_status": "proxy_scored"},
        {"canonical_hash": "b", "score": -1.0, "verification_status": "rejected"},
    ]

    summary = summarize_scored_records(records)

    assert summary["scored_records"] == 3
    assert summary["proxy_scored_records"] == 2
    assert summary["rejected_records"] == 1
    assert summary["unique_canonical_hashes"] == 2
    assert summary["duplicate_canonical_hash_records"] == 1
    assert summary["duplicate_canonical_hashes"] == 1
    assert summary["best_score"] == 12.0


def test_build_split_manifest_links_gpu_and_cpu_artifacts(tmp_path):
    gpu_summary_path = tmp_path / "gpu_sampler_probe_summary.json"
    score_summary = {
        "source_path": str(tmp_path / "samples.jsonl"),
        "summary_path": str(tmp_path / "score_summary.json"),
        "report_path": str(tmp_path / "score_report.md"),
        "scored_jsonl_path": str(tmp_path / "scored_samples.jsonl"),
        "runtime_seconds": 2.5,
        "records_read": 1024,
        "records_selected": 512,
        "selection_mode": "capped",
        "max_records": 512,
        "decoded_input_records": 512,
        "scored_records": 512,
        "valid_records": 400,
        "rejected_records": 112,
        "local_search_enabled": False,
        "scored_record_summary": {"unique_canonical_hashes": 390, "duplicate_canonical_hash_records": 10},
    }
    gpu_summary = {
        "runs": {
            "gpu_sampler_probe": {
                "command_text": "python3 scripts/igp24_gpu_sampler_probe.py",
                "train_log_path": str(tmp_path / "train.log"),
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "runtime_seconds": 20.0,
                "sample_export_records": 1024,
                "sample_export_decoded_records": 1024,
                "post_train_cpu_sampling_scoring_avoided": True,
                "train_log": {"logged_device": "cuda", "eval_losses": [{}, {}], "max_cuda_reserved_mb": 100.0},
                "gpu_monitor": {
                    "max_gpu_utilization_percent": 90.0,
                    "avg_gpu_utilization_percent": 20.0,
                    "max_memory_used_mib": 5000.0,
                },
            }
        }
    }

    manifest = build_split_manifest(
        score_summary=score_summary,
        gpu_summary=gpu_summary,
        gpu_summary_path=gpu_summary_path,
        source_commit="abc123",
        score_command="python3 scripts/igp24_score_sample_export.py",
    )

    assert manifest["record_type"] == "igp24_split_workflow_manifest"
    assert manifest["source_commit"] == "abc123"
    assert manifest["artifacts"]["sample_export_path"].endswith("samples.jsonl")
    assert manifest["artifacts"]["train_log_path"].endswith("train.log")
    assert manifest["gpu_phase"]["sample_export_records"] == 1024
    assert manifest["gpu_phase"]["scoring_local_search_avoided"]
    assert manifest["cpu_phase"]["records_selected"] == 512
    assert manifest["cpu_phase"]["local_search_enabled"] is False
    assert manifest["dedup"]["unique_canonical_hashes"] == 390
    assert not manifest["safety"]["runs_exact_verifiers"]


def test_build_split_report_includes_manifest_counts():
    manifest = {
        "created_at_utc": "2026-07-04T00:00:00+00:00",
        "source_commit": "abc123",
        "commands": {"gpu_probe": "gpu cmd", "cpu_score": "cpu cmd"},
        "artifacts": {
            "sample_export_path": "samples.jsonl",
            "gpu_probe_summary_path": "gpu_summary.json",
            "train_log_path": "train.log",
            "cpu_score_summary_path": "score_summary.json",
            "scored_jsonl_path": "scored.jsonl",
        },
        "gpu_phase": {"runtime_seconds": 20.0, "max_gpu_utilization_percent": 90.0, "sample_export_records": 1024, "sample_export_decoded_records": 1024},
        "cpu_phase": {"runtime_seconds": 2.5, "records_selected": 512, "scored_records": 512, "valid_records": 400, "rejected_records": 112, "local_search_enabled": False},
        "dedup": {"unique_canonical_hashes": 390, "duplicate_canonical_hash_records": 10},
    }

    report = build_split_report(manifest)

    assert "IGP24 Split Workflow Report" in report
    assert "samples.jsonl" in report
    assert "scored.jsonl" in report
    assert "gpu cmd" in report
    assert "cpu cmd" in report


def test_build_score_report_includes_counts():
    summary = {
        "created_at_utc": "2026-07-04T00:00:00+00:00",
        "source_path": "samples.jsonl",
        "scored_jsonl_path": "scored.jsonl",
        "records_read": 2,
        "records_selected": 2,
        "decoded_input_records": 1,
        "skipped_decode_records": 1,
        "invalid_input_records": 0,
        "scored_records": 1,
        "valid_records": 1,
        "rejected_records": 0,
        "split_manifest_path": "manifest.json",
        "scored_record_summary": {"unique_canonical_hashes": 1, "duplicate_canonical_hash_records": 0},
        "local_search_enabled": False,
    }

    report = build_report(summary)

    assert "IGP24 Sample Export Scoring Report" in report
    assert "samples.jsonl" in report
    assert "scored.jsonl" in report
    assert "manifest.json" in report
    assert "no exact verifier execution" in report


def test_parser_false_boolean_defaults_are_not_truthy():
    parser = get_parser()

    args = parser.parse_args(["samples.jsonl", "--max_records", "2"])

    assert args.score_all is False
    assert args.local_search is False
