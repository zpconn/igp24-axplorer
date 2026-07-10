import json

from scripts import igp24_gx2_route_experiment as gx2


def _route():
    return {
        "pair_key": "24T22631|r=24",
        "label": "24T22631",
        "r": 24,
        "family": "gx2_degree12_lift",
        "structurally_eligible": True,
        "executable_generator_available": True,
        "combined_priority_score": 10.0,
        "target_group_block_sizes": [2, 12],
        "soundness": "test",
    }


def _record(index, *, target=False, valuable=False):
    valuable_pairs = ["24T22631|r=24"] if valuable else []
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
    monkeypatch.setattr(gx2, "load_routes", lambda _path: [_route()])
    monkeypatch.setattr(gx2, "load_known_submissions", lambda _paths: {})
    monkeypatch.setattr(gx2, "read_jsonl", lambda _path: [])
    monkeypatch.setattr(gx2, "get_source_commit", lambda _repo: "test-commit")
    monkeypatch.setattr(
        gx2,
        "iter_gx2_trials",
        lambda **_kwargs: ({"trial_index": index} for index in range(len(records))),
    )

    def fake_evaluate_trial(**kwargs):
        trial_index = int(kwargs["trial"]["trial_index"])
        return records[trial_index], None

    monkeypatch.setattr(gx2, "evaluate_trial", fake_evaluate_trial)


def test_gx2_experiment_can_continue_after_candidate_limit(tmp_path, monkeypatch):
    _patch_common(monkeypatch, [_record(0), _record(1), _record(2)])

    assert (
        gx2.main(
            [
                "--routes_jsonl",
                str(tmp_path / "routes.jsonl"),
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

    summary = json.loads((tmp_path / "out" / "gx2_route_experiment_summary.json").read_text(encoding="utf-8"))
    assert summary["trials_attempted"] == 3
    assert summary["local_valid_evaluated_count"] == 3
    assert summary["local_valid_candidate_count"] == 1
    assert summary["local_valid_overflow_count"] == 2
    assert summary["adaptive_target_compatible_seen_count"] == 0


def test_gx2_experiment_retains_target_compatible_rows_after_candidate_limit(tmp_path, monkeypatch):
    _patch_common(monkeypatch, [_record(0), _record(1), _record(2, target=True, valuable=True)])

    assert (
        gx2.main(
            [
                "--routes_jsonl",
                str(tmp_path / "routes.jsonl"),
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
        for line in (tmp_path / "out" / "gx2_route_candidates.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = json.loads((tmp_path / "out" / "gx2_route_experiment_summary.json").read_text(encoding="utf-8"))

    assert summary["trials_attempted"] == 3
    assert summary["local_valid_evaluated_count"] == 3
    assert summary["local_valid_candidate_count"] == 2
    assert summary["adaptive_target_compatible_seen_count"] == 1
    assert summary["adaptive_target_compatible_count"] == 1
    assert rows[-1]["canonical_hash"] == "hash-2"
    assert rows[-1]["retention_reason"] == "target_compatible_after_candidate_limit"
