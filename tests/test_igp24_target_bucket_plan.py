import json

from scripts.igp24_target_bucket_plan import (
    build_plan,
    load_discovery_snapshot,
    load_pair_status,
)


def _snapshot_payload():
    return {
        "schema_version": 1,
        "record_type": "sair_igp24_discovery_page_snapshot",
        "captured_at": "2026-07-06T16:48:00-05:00",
        "capture_method": "pytest fixture",
        "coverage_summary": {
            "total_valid_signatures": 100,
            "uncovered_signatures": 60,
            "uncovered_solvable": 58,
            "uncovered_solvable_pct": 96.7,
            "lmfdb_baseline": 3,
        },
        "per_r": [
            {"r": 8, "solved": 20, "total": 40, "remaining": 20, "solved_pct": 50.0, "remaining_pct": 50.0},
            {"r": 16, "solved": 10, "total": 40, "remaining": 30, "solved_pct": 25.0, "remaining_pct": 75.0},
            {"r": 24, "solved": 0, "total": 10, "remaining": 10, "solved_pct": 0.0, "remaining_pct": 100.0},
        ],
    }


def _pair_status_payload():
    return {
        "record_type": "igp24_pair_status_ledger",
        "pairs": [
            {"pair_key": "24T657|r=8", "label": "24T657", "r": 8, "status": "accepted"},
            {"pair_key": "24T661|r=8", "label": "24T661", "r": 8, "status": "accepted"},
            {"pair_key": "24T1310|r=8", "label": "24T1310", "r": 8, "status": "accepted"},
            {"pair_key": "24T9993|r=8", "label": "24T9993", "r": 8, "status": "accepted"},
            {"pair_key": "24T24979|r=16", "label": "24T24979", "r": 16, "status": "accepted"},
            {"pair_key": "24T25000|r=16", "label": "24T25000", "r": 16, "status": "accepted"},
        ],
    }


def test_load_discovery_snapshot_validates_per_r_rows(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")

    snapshot = load_discovery_snapshot(path)

    assert snapshot["per_r"][0]["r"] == 8
    assert snapshot["per_r"][1]["remaining_pct"] == 75.0


def test_target_bucket_plan_marks_missing_api_targets_and_ranks_actions(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    pair_status_path = tmp_path / "pairs.json"
    snapshot_path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")
    pair_status_path.write_text(json.dumps(_pair_status_payload()), encoding="utf-8")

    plan = build_plan(load_discovery_snapshot(snapshot_path), load_pair_status(pair_status_path))

    assert plan["api_target_list_available"] is False
    assert "not derivable" in plan["api_caveat"]
    assert plan["largest_remaining_buckets"][0]["r"] == 16
    assert plan["recommended_action_buckets"][0]["r"] == 24
    assert plan["no_gpu_training_recommended"] is True


def test_local_pair_status_affects_bucket_recommendation_evidence(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    pair_status_path = tmp_path / "pairs.json"
    snapshot_path.write_text(json.dumps(_snapshot_payload()), encoding="utf-8")
    pair_status_path.write_text(json.dumps(_pair_status_payload()), encoding="utf-8")

    plan = build_plan(load_discovery_snapshot(snapshot_path), load_pair_status(pair_status_path))
    by_r = {row["r"]: row for row in plan["bucket_rankings"]}

    assert by_r[8]["local_accepted_pair_count"] == 4
    assert "multiple accepted labels" in by_r[8]["collapse_or_success_evidence"][0]
    assert by_r[16]["local_accepted_pair_count"] == 2
    assert any("24T25000" in item for item in by_r[16]["collapse_or_success_evidence"])
    assert "do not widen" in by_r[16]["recommendation"].lower()
