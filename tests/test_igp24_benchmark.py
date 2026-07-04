import json

from scripts.igp24_benchmark import read_jsonl, summarize_records


def test_summarize_records_aggregates_scores_and_metadata():
    records = [
        {
            "score": 10.0,
            "canonical_hash": "a",
            "generation_metadata": {"strategy": "uniform"},
            "local_search_metadata": {"attempted": 3, "accepted": 1},
            "score_components": {"final_score": 10.0},
        },
        {
            "score": 14.0,
            "canonical_hash": "b",
            "generation_metadata": {"strategy": "sparse"},
            "local_search_metadata": {"attempted": 2, "accepted": 2},
            "score_components": {"final_score": 14.0},
        },
        {
            "score": 12.0,
            "canonical_hash": "c",
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


def test_read_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(json.dumps({"score": 1}) + "\n\n" + json.dumps({"score": 2}) + "\n", encoding="utf-8")

    assert read_jsonl(path) == [{"score": 1}, {"score": 2}]
    assert read_jsonl(tmp_path / "missing.jsonl") == []
