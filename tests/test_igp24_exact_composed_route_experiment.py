import json

import pytest

from scripts import igp24_exact_composed_route_experiment as experiment


def _route(*, executable=True):
    return {
        "pair_key": "24T9993|r=8",
        "label": "24T9993",
        "r": 8,
        "family": "quartic_in_x6",
        "structurally_eligible": True,
        "executable_generator_available": executable,
        "combined_priority_score": 10.0,
        "target_group_block_sizes": [6, 12],
        "soundness": "test",
    }


def _record(index, *, target=False, valuable=False):
    valuable_pairs = ["24T9993|r=8"] if valuable else []
    return {
        "canonical_hash": f"hash-{index}",
        "exported_coefficients": [index + 1, *([0] * 23), 1],
        "coefficient_height": index + 1,
        "target_label_not_ruled_out": target,
        "target_pair_valuable_not_ruled_out": target,
        "sufficient_adaptive_frobenius_evidence": True,
        "group_compatibility": {"valuable_targets_not_ruled_out": valuable_pairs},
        "adaptive_frobenius": {"usable_prime_count": 10},
        "submission_recommendation": "offline_review_only_target_compatible"
        if target
        else "false_target_label_ruled_out_by_adaptive_evidence",
    }


def _patch_common(monkeypatch, records):
    monkeypatch.setattr(experiment, "load_routes", lambda _path: [_route()])
    monkeypatch.setattr(experiment, "load_known_submissions", lambda _paths: {})
    monkeypatch.setattr(experiment, "read_jsonl", lambda _path: [])
    monkeypatch.setattr(experiment, "get_source_commit", lambda _repo: "test-commit")
    monkeypatch.setattr(
        experiment,
        "iter_trials_for_family",
        lambda **_kwargs: ({"trial_index": index} for index in range(len(records))),
    )

    def fake_evaluate_trial(**kwargs):
        trial_index = int(kwargs["trial"]["trial_index"])
        return records[trial_index], None

    monkeypatch.setattr(experiment, "evaluate_trial", fake_evaluate_trial)


def test_select_route_requires_executable_route():
    with pytest.raises(ValueError, match="no executable"):
        experiment.select_route([_route(executable=False)], family_name="quartic_in_x6", target_pair="24T9993|r=8")


def test_exact_composed_experiment_can_continue_after_candidate_limit(tmp_path, monkeypatch):
    _patch_common(monkeypatch, [_record(0), _record(1), _record(2)])

    assert (
        experiment.main(
            [
                "--routes_jsonl",
                str(tmp_path / "routes.jsonl"),
                "--family",
                "quartic_in_x6",
                "--target_pair",
                "24T9993|r=8",
                "--output_dir",
                str(tmp_path / "out"),
                "--limit",
                "1",
                "--max_trials",
                "3",
                "--continue_after_candidate_limit",
                "--target_compatible_limit",
                "0",
            ]
        )
        == 0
    )

    summary = json.loads(
        (tmp_path / "out" / "exact_composed_route_experiment_summary.json").read_text(encoding="utf-8")
    )
    assert summary["construction_family"] == "quartic_in_x6"
    assert summary["trials_attempted"] == 3
    assert summary["local_valid_evaluated_count"] == 3
    assert summary["local_valid_candidate_count"] == 1
    assert summary["local_valid_overflow_count"] == 2
    assert summary["adaptive_target_compatible_seen_count"] == 0


def test_exact_composed_experiment_retains_target_compatible_rows_after_limit(tmp_path, monkeypatch):
    _patch_common(monkeypatch, [_record(0), _record(1), _record(2, target=True, valuable=True)])

    assert (
        experiment.main(
            [
                "--routes_jsonl",
                str(tmp_path / "routes.jsonl"),
                "--family",
                "quartic_in_x6",
                "--target_pair",
                "24T9993|r=8",
                "--output_dir",
                str(tmp_path / "out"),
                "--limit",
                "1",
                "--max_trials",
                "3",
                "--continue_after_candidate_limit",
                "--target_compatible_limit",
                "1",
            ]
        )
        == 0
    )

    rows = [
        json.loads(line)
        for line in (tmp_path / "out" / "exact_composed_route_candidates.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    summary = json.loads(
        (tmp_path / "out" / "exact_composed_route_experiment_summary.json").read_text(encoding="utf-8")
    )

    assert summary["trials_attempted"] == 3
    assert summary["local_valid_evaluated_count"] == 3
    assert summary["local_valid_candidate_count"] == 2
    assert summary["adaptive_target_compatible_seen_count"] == 1
    assert summary["adaptive_target_compatible_count"] == 1
    assert rows[-1]["canonical_hash"] == "hash-2"
    assert rows[-1]["retention_reason"] == "target_compatible_after_candidate_limit"


def test_exact_composed_experiment_prefilter_only_does_not_claim_local_validity(tmp_path):
    routes = tmp_path / "routes.jsonl"
    routes.write_text(
        json.dumps(
            {
                "pair_key": "24T24134|r=8",
                "label": "24T24134",
                "r": 8,
                "family": "composition_8x3",
                "structurally_eligible": True,
                "executable_generator_available": True,
                "combined_priority_score": 10.0,
                "target_group_block_sizes": [3, 6],
                "soundness": "test",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    assert (
        experiment.main(
            [
                "--routes_jsonl",
                str(routes),
                "--family",
                "composition_8x3",
                "--target_pair",
                "24T24134|r=8",
                "--output_dir",
                str(tmp_path / "out"),
                "--max_trials",
                "3",
                "--limit",
                "2",
                "--prefilter_only",
            ]
        )
        == 0
    )

    summary = json.loads(
        (tmp_path / "out" / "exact_composed_route_experiment_summary.json").read_text(encoding="utf-8")
    )
    rows = [
        json.loads(line)
        for line in (tmp_path / "out" / "exact_composed_route_candidates.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert summary["prefilter_only"] is True
    assert summary["prefilter_candidate_count"] == 2
    assert summary["local_valid_candidate_count"] == 0
    assert summary["local_valid_evaluated_count"] == 0
    assert rows[0]["local_validation_status"] == "not_run_prefilter_only"
    assert rows[0]["eligible_for_packet"] is False
    assert rows[0]["submission_recommendation"] == "false_prefilter_only_exact_validation_not_run"
