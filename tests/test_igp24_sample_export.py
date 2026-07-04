import argparse

from scripts.igp24_score_sample_export import build_report, extract_decoded_coefficients, score_export_records
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
    assert summary["local_search_enabled"] is False
    assert summary["safety"]["proxy_only"]
    assert not summary["safety"]["runs_exact_verifiers"]
    assert not summary["safety"]["calls_sair"]
    assert not summary["safety"]["auto_submits"]
    assert all(record["generation_metadata"]["strategy"] == "model_sample_export" for record in scored)


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
        "local_search_enabled": False,
    }

    report = build_report(summary)

    assert "IGP24 Sample Export Scoring Report" in report
    assert "samples.jsonl" in report
    assert "scored.jsonl" in report
    assert "no exact verifier execution" in report
