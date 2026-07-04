import json

from scripts.igp24_benchmark import parse_target_rs, parse_valid_examples, read_jsonl, summarize_records


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
