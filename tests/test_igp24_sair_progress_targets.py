import json

from scripts.igp24_sair_progress_targets import (
    build_plan,
    load_pair_status,
    load_progress_snapshot,
    write_outputs,
)


def _label(label, t, allowed, discovered, remaining, *, team_count=0):
    return {
        "label": label,
        "t": t,
        "allowedR": allowed,
        "teamCount": team_count,
        "minimumDiscAbs": None,
        "discoveredSignatures": discovered,
        "remainingSignatures": remaining,
        "signatures": [
            {
                "r": r,
                "teamCount": 1 if r in discovered else 0,
                "minimumDiscAbs": "123" if r in discovered else None,
                "discovered": r in discovered,
            }
            for r in allowed
        ],
    }


def _snapshot():
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": "2026-07-07T01:20:00+00:00",
        "query": {"limit": 5000, "includeEmpty": True},
        "page_count": 1,
        "label_count": 3,
        "pages": [
            {
                "generatedAt": "2026-07-07T01:20:36Z",
                "labels": 3,
                "nextCursorPresent": False,
                "meta": {"published": True},
            }
        ],
        "labels": [
            _label("24T1", 1, [0, 24], [0], [24], team_count=0),
            _label("24T2", 2, [8, 12], [8], [12], team_count=1),
            _label("24T25000", 25000, [16, 24], [16], [24], team_count=50),
        ],
    }


def _pair_status():
    return {
        "record_type": "igp24_pair_status_ledger",
        "pairs": [
            {"pair_key": "24T25000|r=24", "label": "24T25000", "r": 24, "status": "accepted"},
        ],
    }


def test_live_progress_target_plan_ranks_uncovered_low_team_targets():
    plan = build_plan(_snapshot(), _pair_status(), top_limit=5, per_r_limit=3)

    assert plan["remaining_signature_count"] == 3
    assert plan["input_snapshot"]["published"] is True
    assert plan["coverage_by_r"][-1]["r"] == 24
    assert plan["coverage_by_r"][-1]["remaining"] == 2
    assert plan["top_remaining_targets"][0]["pair_key"] == "24T1|r=24"
    assert plan["top_remaining_targets"][0]["signature_team_count"] == 0
    assert plan["top_remaining_targets"][-1]["local_pair_already_accepted"] is True
    assert plan["strategic_decision"]["gpu_training_recommended_now"] is False
    assert plan["strategic_decision"]["auto_submission_recommended_now"] is False


def test_loaders_and_outputs_round_trip(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    pair_status_path = tmp_path / "pairs.json"
    output_dir = tmp_path / "plan"
    snapshot_path.write_text(json.dumps(_snapshot()), encoding="utf-8")
    pair_status_path.write_text(json.dumps(_pair_status()), encoding="utf-8")

    plan = build_plan(load_progress_snapshot(snapshot_path), load_pair_status(pair_status_path), top_limit=2)
    paths = write_outputs(plan, output_dir)

    reloaded = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    top_targets = [json.loads(line) for line in paths["top_targets_jsonl"].read_text(encoding="utf-8").splitlines()]

    assert reloaded["remaining_signature_count"] == 3
    assert reloaded["top_remaining_rs"][0] == 24
    assert top_targets[0]["pair_key"] == "24T1|r=24"
    assert "SAIR Live Target Plan" in paths["report_md"].read_text(encoding="utf-8")
