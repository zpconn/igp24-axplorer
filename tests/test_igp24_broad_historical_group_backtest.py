import json

from scripts.igp24_broad_historical_group_backtest import main as backtest_main
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _index(path):
    index = GroupCycleIndex(path)
    index.initialize(provenance={"test": True})
    index.upsert_group(GroupRecord(label="24T1", t=1, parity="mixed", cycle_types=("1.23", "3.21")))
    index.upsert_group(GroupRecord(label="24T25000", t=25000, parity="mixed", cycle_types=("1.23", "3.21")))
    return index


def test_broad_historical_backtest_joins_scoreable_rows_to_local_evidence(tmp_path):
    index_path = tmp_path / "groups.sqlite"
    _index(index_path)
    scoreable_path = tmp_path / "scoreable.jsonl"
    evidence_path = tmp_path / "evidence.jsonl"
    progress_path = tmp_path / "progress.jsonl"
    output_dir = tmp_path / "out"
    _write_jsonl(
        scoreable_path,
        [
            {"canonical_hash": "known-a", "label": "24T25000", "t": 25000, "r": 24, "pair_key": "24T25000|r=24"},
            {"canonical_hash": "known-b", "label": "24T24932", "t": 24932, "r": 24, "pair_key": "24T24932|r=24"},
            {"canonical_hash": "missing", "label": "24T1", "t": 1, "r": 24, "pair_key": "24T1|r=24"},
        ],
    )
    _write_jsonl(
        evidence_path,
        [
            {
                "canonical_hash": "known-a",
                "record_type": "igp24_adaptive_frobenius_benchmark_row",
                "features": {"construction_family": "fam", "perturbation_mode": "mode"},
                "mod_p_factorization_degree_patterns": [
                    {"prime": 5, "degrees": [1, 23]},
                    {"prime": 7, "degrees": [3, 21]},
                ],
                "final_indexed_target_survivor_count": 1,
                "final_valuable_targets_not_ruled_out": ["24T1|r=24"],
                "true_label_survived": True,
                "budget_results": {
                    "1": {
                        "status": "ok",
                        "indexed_target_survivor_count": 2,
                        "valuable_target_count": 1,
                        "valuable_targets_not_ruled_out": ["24T1|r=24"],
                        "true_label_indexed": True,
                        "true_label_survived": True,
                    },
                    "2": {
                        "status": "ok",
                        "indexed_target_survivor_count": 1,
                        "valuable_target_count": 1,
                        "valuable_targets_not_ruled_out": ["24T1|r=24"],
                        "true_label_indexed": True,
                        "true_label_survived": True,
                    },
                },
            },
            {
                "canonical_hash": "known-b",
                "features": {"construction_family": "fam", "perturbation_mode": "mode"},
                "mod_p_factorization_degree_patterns": [
                    {"prime": 5, "degrees": [1, 23]},
                    {"prime": 7, "degrees": [3, 21]},
                ],
            },
        ],
    )
    _write_jsonl(
        progress_path,
        [
            {"label": "24T1", "allowedR": [24], "remainingSignatures": [24], "discoveredSignatures": [], "signatures": [{"r": 24, "discovered": False, "teamCount": 0}]},
            {"label": "24T25000", "allowedR": [24], "remainingSignatures": [], "discoveredSignatures": [24], "signatures": [{"r": 24, "discovered": True, "teamCount": 40}]},
        ],
    )

    assert (
        backtest_main(
            [
                "--scoreable_rows_jsonl",
                str(scoreable_path),
                "--index",
                str(index_path),
                "--progress_jsonl",
                str(progress_path),
                "--evidence_jsonl",
                str(evidence_path),
                "--budgets",
                "1,2",
                "--output_dir",
                str(output_dir),
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "broad_historical_group_backtest_summary.json").read_text(encoding="utf-8"))
    assert summary["scoreable_row_count"] == 3
    assert summary["observed_pair_count"] == 3
    assert summary["evaluated_row_count"] == 2
    assert summary["skipped_row_count"] == 1
    assert summary["skip_reason_counts"] == {"missing_local_modular_evidence": 1}
    assert summary["true_label_indexed_row_count"] == 1
    assert summary["true_label_outside_index_row_count"] == 1
    assert summary["indexed_true_label_containment_failures"] == 0
    assert summary["valuable_target_false_positive_rows"] == 2
    assert summary["budget_summary"]["1"]["evaluated_rows"] == 2
    assert summary["budget_summary"]["2"]["evaluated_rows"] == 2

    rows = [
        json.loads(line)
        for line in (output_dir / "broad_historical_group_backtest_rows.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    outside = [row for row in rows if row["label"] == "24T24932"][0]
    precomputed = [row for row in rows if row["canonical_hash"] == "known-a"][0]
    recomputed = [row for row in rows if row["canonical_hash"] == "known-b"][0]
    assert precomputed["compatibility_source"] == "precomputed_adaptive_evidence"
    assert recomputed["compatibility_source"] == "recomputed_from_patterns"
    assert outside["true_label_indexed"] is False
    assert outside["unindexed_label_mass_unknown"] is True
    assert outside["valuable_target_count"] == 1
