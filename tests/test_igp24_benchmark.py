import json

from scripts.igp24_benchmark import (
    aggregate_results,
    parse_target_rs,
    parse_valid_examples,
    read_jsonl,
    resolve_benchmark_strategy,
    summarize_records,
)


def test_summarize_records_aggregates_scores_and_metadata():
    records = [
        {
            "score": 10.0,
            "canonical_hash": "a",
            "real_root_count": 2,
            "generation_metadata": {"strategy": "uniform"},
            "local_search_metadata": {"attempted": 3, "accepted": 1},
            "score_components": {"final_score": 10.0},
        },
        {
            "score": 14.0,
            "canonical_hash": "b",
            "real_root_count": 4,
            "generation_metadata": {"strategy": "sparse"},
            "local_search_metadata": {"attempted": 2, "accepted": 2},
            "score_components": {"final_score": 14.0},
        },
        {
            "score": 12.0,
            "canonical_hash": "c",
            "real_root_count": 2,
            "generation_metadata": {"strategy": "uniform"},
            "local_search_metadata": {},
            "score_components": {"final_score": 12.0},
        },
    ]

    summary = summarize_records(records)

    assert summary["ledger_records"] == 3
    assert summary["best_score"] == 14.0
    assert summary["mean_score"] == 12.0
    assert summary["median_score"] == 12.0
    assert summary["strategy_mix"] == {"sparse": 1, "uniform": 2}
    assert summary["local_search_attempted"] == 5
    assert summary["local_search_accepted"] == 3
    assert summary["local_search_records"] == 2
    assert summary["best_hash"] == "b"
    assert summary["best_generation_strategy"] == "sparse"
    assert summary["metadata_complete"]

    target_summary = summarize_records(records, target_r=2)
    assert target_summary["target_r"] == 2
    assert target_summary["target_r_match_count"] == 2
    assert target_summary["target_r_match_rate"] == 2 / 3
    assert target_summary["best_matching_score"] == 12.0


def test_read_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(json.dumps({"score": 1}) + "\n\n" + json.dumps({"score": 2}) + "\n", encoding="utf-8")

    assert read_jsonl(path) == [{"score": 1}, {"score": 2}]
    assert read_jsonl(tmp_path / "missing.jsonl") == []


def test_parse_valid_examples_uses_last_reported_count():
    output = "INFO - Valid examples: 3\nINFO - Valid examples: 12\n"

    assert parse_valid_examples(output) == 12
    assert parse_valid_examples("no stats here") is None


def test_parse_target_rs_accepts_untargeted_aliases_and_integers():
    assert parse_target_rs("none,0,2,untargeted,-") == [None, 0, 2, None, None]


def test_resolve_benchmark_strategy_accepts_preset_labels():
    assert resolve_benchmark_strategy("four_real_seed") == ("four_real_seed", "none", None)
    assert resolve_benchmark_strategy("quartic_lift") == ("quartic_lift", "none", None)
    assert resolve_benchmark_strategy("r8_quartic_lift") == ("r8_quartic_lift", "none", None)
    assert resolve_benchmark_strategy("r16_quadratic_lift") == ("r16_quadratic_lift", "none", None)
    assert resolve_benchmark_strategy("fixed_sparse_template") == ("fixed_sparse_template", "none", None)
    assert resolve_benchmark_strategy("preset_r4") == ("mixed", "r4", None)
    assert resolve_benchmark_strategy("mix_r4_yield") == ("mixed", "none", "four_real_seed:1.0")
    assert resolve_benchmark_strategy("mix_r4_balanced") == ("mixed", "none", "four_real_seed:0.8,sparse:0.2")
    assert resolve_benchmark_strategy("mix_r4_diverse") == ("mixed", "none", "four_real_seed:0.6,sparse:0.4")
    assert resolve_benchmark_strategy("mix_r4_dual_yield") == ("mixed", "none", "four_real_seed:0.75,quartic_lift:0.25")
    assert resolve_benchmark_strategy("mix_r4_dual_quality") == ("mixed", "none", "four_real_seed:0.25,quartic_lift:0.75")
    assert resolve_benchmark_strategy("mix_r4_dual_balanced") == (
        "mixed",
        "none",
        "four_real_seed:0.45,quartic_lift:0.45,sparse:0.10",
    )


def test_aggregate_results_groups_strategy_and_target():
    results = [
        {
            "strategy": "sparse",
            "target_r": 2,
            "runtime_seconds": 2.0,
            "valid_candidates": 12,
            "ledger_records": 20,
            "target_r_match_count": 10,
            "target_r_match_rate": 0.5,
            "best_score": 100.0,
            "best_matching_score": 99.0,
            "mean_score": 90.0,
            "local_search_attempted": 10,
            "local_search_accepted": 4,
            "returncode": 0,
            "metadata_complete": True,
        },
        {
            "strategy": "sparse",
            "target_r": 2,
            "runtime_seconds": 4.0,
            "valid_candidates": 11,
            "ledger_records": 30,
            "target_r_match_count": 18,
            "target_r_match_rate": 0.6,
            "best_score": 110.0,
            "best_matching_score": 108.0,
            "mean_score": 95.0,
            "local_search_attempted": 20,
            "local_search_accepted": 8,
            "returncode": 0,
            "metadata_complete": True,
        },
        {
            "strategy": "sparse",
            "target_r": None,
            "runtime_seconds": 3.0,
            "valid_candidates": 12,
            "ledger_records": 25,
            "target_r_match_count": None,
            "target_r_match_rate": None,
            "best_score": 80.0,
            "best_matching_score": None,
            "mean_score": 75.0,
            "local_search_attempted": 5,
            "local_search_accepted": 1,
            "returncode": 0,
            "metadata_complete": True,
        },
    ]

    aggregated = aggregate_results(results)
    targeted = next(row for row in aggregated if row["target_r"] == 2)
    untargeted = next(row for row in aggregated if row["target_r"] is None)

    assert targeted["runs"] == 2
    assert targeted["avg_runtime_seconds"] == 3.0
    assert targeted["valid_candidates_total"] == 23
    assert targeted["ledger_records_total"] == 50
    assert targeted["target_r_match_total"] == 28
    assert targeted["avg_match_rate"] == 0.55
    assert targeted["avg_best_score"] == 105.0
    assert targeted["avg_best_matching_score"] == 103.5
    assert targeted["avg_mean_score"] == 92.5
    assert targeted["best_score"] == 110.0
    assert targeted["local_search_acceptance"] == 0.4
    assert targeted["all_returncode_zero"]
    assert targeted["metadata_complete"]

    assert untargeted["target_r_match_total"] is None
    assert untargeted["avg_match_rate"] is None
    assert untargeted["avg_best_matching_score"] is None
