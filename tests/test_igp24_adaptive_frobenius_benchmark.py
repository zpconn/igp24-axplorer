from scripts.igp24_adaptive_frobenius_benchmark import (
    exact_label_from_record,
    intended_target_label_from_record,
    intended_target_pair_from_record,
    summarize,
)
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord


def _index(path):
    index = GroupCycleIndex(path)
    index.initialize(provenance={"test": True})
    index.upsert_group(GroupRecord(label="24T1", t=1, parity="mixed", cycle_types=("24",)))
    return index


def test_candidate_rows_with_missing_exact_label_are_not_outside_index(tmp_path):
    index = _index(tmp_path / "groups.sqlite")
    evaluated = [
        {
            "label": None,
            "exact_label_status": "missing",
            "true_label_indexed": False,
            "true_label_survived": None,
            "intended_target_label": "24T1",
            "intended_target_pair": "24T1|r=8",
            "intended_target_survived": True,
            "final_valuable_target_count": 1,
            "final_indexed_target_survivor_count": 3,
            "discriminant_source": "discriminant",
            "budget_results": {
                "5": {
                    "usable_prime_count": 5,
                    "valuable_target_count": 1,
                    "indexed_target_survivor_count": 3,
                    "exact_label_status": "missing",
                    "true_label_indexed": False,
                    "true_label_survived": None,
                    "intended_target_survived": True,
                }
            },
        }
    ]

    summary = summarize(
        input_rows=[{"canonical_hash": "candidate"}],
        evaluated=evaluated,
        failed=[],
        index=index,
        budgets=[5],
        max_usable_primes=5,
        output_dir=tmp_path / "out",
    )

    assert summary["true_label_outside_index_row_count"] == 0
    assert summary["exact_label_missing_row_count"] == 1
    assert summary["true_label_indexed_row_count"] == 0
    assert summary["intended_target_row_count"] == 1
    assert summary["intended_target_survival_rows"] == 1
    assert summary["budget_summary"]["5"]["intended_target_survival_rows"] == 1
    assert summary["by_actual_label"]["exact_label_missing"]["missing_exact_label_rows"] == 1


def test_target_helpers_prefer_explicit_and_route_metadata():
    assert exact_label_from_record({"label": "24T7"}) == "24T7"
    assert exact_label_from_record({"verified_group_label": "24T8"}) == "24T8"
    assert exact_label_from_record({"label": ""}) is None
    assert intended_target_label_from_record({"target_label": "24T1"}) == "24T1"
    assert intended_target_label_from_record({"target_metadata": {"target_t": "24T2"}}) == "24T2"
    assert intended_target_label_from_record({"route": {"label": "24T3"}}) == "24T3"
    assert intended_target_pair_from_record({"route": {"pair_key": "24T3|r=8"}}) == "24T3|r=8"
    assert intended_target_pair_from_record({"target_metadata": {"target_t": "24T4", "target_r": 8}}) == "24T4|r=8"
