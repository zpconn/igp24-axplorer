import json
from pathlib import Path

import pytest

from scripts.igp24_merge_scored_exports import merge_sources, write_outputs


def _write_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _score_dir(tmp_path, seed_label, records):
    score_dir = tmp_path / seed_label / "cpu_scored_export_all"
    _write_jsonl(score_dir / "scored_samples.jsonl", records)
    (score_dir / "score_summary.json").write_text(
        json.dumps({"scored_records": len(records), "source_path": f"/tmp/{seed_label}/samples.jsonl"}),
        encoding="utf-8",
    )
    (score_dir / "split_workflow_manifest.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    "sample_export_path": f"/tmp/{seed_label}/samples.jsonl",
                    "gpu_probe_summary_path": f"/tmp/{seed_label}/gpu_sampler_probe_summary.json",
                    "train_log_path": f"/tmp/{seed_label}/train.log",
                },
                "gpu_phase": {"max_gpu_utilization_percent": 99.0},
                "cpu_phase": {"local_search_enabled": False},
            }
        ),
        encoding="utf-8",
    )
    return score_dir


def test_merge_sources_reports_combined_dedup_and_overlap(tmp_path):
    seed1 = _score_dir(
        tmp_path,
        "seed2301",
        [
            {"canonical_hash": "h1", "score": 10.0, "verification_status": "proxy_scored"},
            {"canonical_hash": "h2", "score": 8.0, "verification_status": "rejected"},
            {"canonical_hash": "h3", "score": 5.0, "verification_status": "proxy_scored"},
        ],
    )
    seed2 = _score_dir(
        tmp_path,
        "seed2302",
        [
            {"canonical_hash": "h1", "score": 12.0, "verification_status": "proxy_scored"},
            {"canonical_hash": "h4", "score": 7.0, "verification_status": "proxy_scored"},
            {"canonical_hash": "h4", "score": 9.0, "verification_status": "proxy_scored"},
        ],
    )

    summary, top_candidates = merge_sources([seed1, seed2], top_n=2)

    assert summary["safety"]["proxy_only"]
    assert summary["source_count"] == 2
    assert [source["label"] for source in summary["sources"]] == ["seed2301", "seed2302"]
    assert summary["combined"]["scored_records"] == 6
    assert summary["combined"]["valid_records"] == 5
    assert summary["combined"]["rejected_records"] == 1
    assert summary["combined"]["unique_canonical_hashes"] == 4
    assert summary["combined"]["duplicate_canonical_hash_records"] == 2
    assert summary["combined"]["hashes_seen_in_multiple_sources"] == 1
    assert summary["overlap"]["pairwise"] == [
        {"left": "seed2301", "right": "seed2302", "shared_hashes": 1}
    ]
    assert summary["combined"]["best_score"] == 12.0
    assert summary["combined"]["mean_score"] == 8.5
    assert [(record["canonical_hash"], record["score"]) for record in top_candidates] == [
        ("h1", 12.0),
        ("h4", 9.0),
    ]


def test_write_outputs_creates_summary_report_and_top_candidates(tmp_path):
    seed1 = _score_dir(
        tmp_path,
        "seed2301",
        [{"canonical_hash": "h1", "score": 10.0, "verification_status": "proxy_scored"}],
    )
    summary, top_candidates = merge_sources([seed1], top_n=1)
    output_dir = tmp_path / "merged"

    write_outputs(summary, top_candidates, output_dir)

    written_summary = json.loads((output_dir / "merged_dedup_summary.json").read_text(encoding="utf-8"))
    report = (output_dir / "merged_dedup_report.md").read_text(encoding="utf-8")
    top_lines = (output_dir / "top_deduped_candidates.jsonl").read_text(encoding="utf-8").splitlines()
    assert written_summary["artifacts"]["merged_report_path"].endswith("merged_dedup_report.md")
    assert "proxy-only" in report
    assert len(top_lines) == 1


def test_merge_sources_rejects_label_count_mismatch(tmp_path):
    seed1 = _score_dir(
        tmp_path,
        "seed2301",
        [{"canonical_hash": "h1", "score": 10.0, "verification_status": "proxy_scored"}],
    )

    with pytest.raises(ValueError):
        merge_sources([seed1], labels=["seed2301", "extra"])
