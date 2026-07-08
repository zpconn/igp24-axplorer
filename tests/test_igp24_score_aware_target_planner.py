import json

from scripts.igp24_score_aware_target_planner import (
    build_plan,
    load_basin_summary,
    load_pair_status,
    load_score_snapshot,
    write_outputs,
)
from scripts.igp24_sair_sync import load_sync_progress_snapshot, load_sync_status, load_sync_submission_rows, write_sync_artifacts


def _label(label, t, allowed, discovered, remaining, *, label_teams=0, signature_teams=None):
    signature_teams = signature_teams or {}
    return {
        "label": label,
        "t": t,
        "allowedR": allowed,
        "teamCount": label_teams,
        "minimumDiscAbs": "999" if discovered else None,
        "discoveredSignatures": discovered,
        "remainingSignatures": remaining,
        "signatures": [
            {
                "r": r,
                "teamCount": signature_teams.get(r, 0),
                "minimumDiscAbs": "123" if r in discovered else None,
                "discovered": r in discovered,
            }
            for r in allowed
        ],
    }


def _snapshot():
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": "2026-07-07T16:45:00+00:00",
        "query": {"limit": 5000, "includeEmpty": True},
        "page_count": 1,
        "label_count": 4,
        "pages": [
            {
                "generatedAt": "2026-07-07T16:45:10Z",
                "labels": 4,
                "nextCursorPresent": False,
                "meta": {"published": True},
            }
        ],
        "labels": [
            _label("24T1", 1, [24], [], [24], label_teams=0),
            _label("24T2", 2, [12], [], [12], label_teams=1),
            _label("24T9993", 9993, [8], [8], [], label_teams=53, signature_teams={8: 10}),
            _label("24T24932", 24932, [24], [24], [], label_teams=48, signature_teams={24: 48}),
        ],
    }


def _pair_status():
    return {
        "record_type": "igp24_pair_status_ledger",
        "pairs": [
            {"pair_key": "24T9993|r=8", "label": "24T9993", "r": 8, "status": "accepted"},
            {"pair_key": "24T24932|r=24", "label": "24T24932", "r": 24, "status": "accepted"},
        ],
    }


def _score_snapshot():
    return {
        "record_type": "igp24_user_reported_sair_score_snapshot",
        "rows": [
            {
                "pair_key": "24T9993|r=8",
                "label": "24T9993",
                "r": 8,
                "points": "0.0019",
                "points_numeric": 0.0019,
                "solved_teams": 10,
                "scoring_discriminant_abs": 123,
                "solvable": True,
            }
        ],
    }


def _basin_summary():
    return {
        "record_type": "igp24_label_basin_analysis",
        "observation_count": 12,
        "pair_summary": {
            "24T9993|r=8": {
                "construction_family_counts": {"r8_quartic_lift": 2},
                "global_pair_discovered": True,
                "global_label_fully_covered": True,
            },
            "24T24932|r=24": {
                "construction_family_counts": {"alt_composition_8x3": 8},
                "global_pair_discovered": True,
                "global_label_fully_covered": True,
            },
        },
        "anti_basin_constraints": [
            {
                "name": "stop_plain_8x3_24T24932_lanes",
                "severity": "high",
                "labels": ["24T24932"],
                "rule": "do not widen ordinary 8x3",
            }
        ],
    }


def _basin_summary_with_stopped_r8_followup():
    summary = _basin_summary()
    summary["anti_basin_constraints"] = [
        *summary["anti_basin_constraints"],
        {
            "name": "stop_r8_score_followup_quartic_x6_24T25000_lane",
            "severity": "high",
            "labels": ["24T25000"],
            "r_values": [8],
            "observed_rows": 4,
            "template_family_counts": {
                "r8_score_followup:four_positive_fibers_e:odd_pair_off_core": 3,
                "r8_score_followup:four_positive_fibers_f:odd_pair_off_core": 1,
            },
            "rule": "reject nearby r8 quartic-in-x^6 odd off-core rows",
        },
    ]
    return summary


def test_score_aware_target_plan_joins_scores_progress_and_basins():
    plan = build_plan(
        snapshot=_snapshot(),
        pair_status=_pair_status(),
        score_snapshot=_score_snapshot(),
        basin_summary=_basin_summary(),
        top_limit=10,
    )

    assert plan["top_uncovered_targets"][0]["pair_key"] == "24T1|r=24"
    assert plan["top_score_followup_targets"][0]["pair_key"] == "24T9993|r=8"
    assert plan["top_score_followup_targets"][0]["category"] == "scored_pair_followup"
    assert plan["r_bucket_priorities"][0]["r"] == 8
    assert plan["lane_recommendations"][0]["lane"] == "r8_quartic_lift_score_followup"
    assert plan["lane_recommendations"][0]["recommended_for_submission_now"] is False
    collapsed = next(row for row in plan["ranked_targets"] if row["pair_key"] == "24T24932|r=24")
    assert collapsed["label_in_avoid_basin"] is True
    assert collapsed["target_score"] < plan["top_score_followup_targets"][0]["target_score"]
    assert plan["decision"]["gpu_training_recommended_now"] is False
    assert plan["decision"]["submission_recommended_now"] is False


def test_score_aware_target_plan_stops_r8_score_followup_lane_after_collapse():
    plan = build_plan(
        snapshot=_snapshot(),
        pair_status=_pair_status(),
        score_snapshot=_score_snapshot(),
        basin_summary=_basin_summary_with_stopped_r8_followup(),
        top_limit=10,
    )

    r8_lane = next(row for row in plan["lane_recommendations"] if row["lane"] == "r8_quartic_lift_score_followup")
    assert r8_lane["recommended_for_generation_now"] is False
    assert r8_lane["recommended_for_submission_now"] is False
    assert r8_lane["stopped_by_constraint"] == "stop_r8_score_followup_quartic_x6_24T25000_lane"
    assert "reject nearby r8 quartic-in-x^6" in r8_lane["rank_reason"]
    assert plan["avoidance_constraints"]["stopped_lanes"] == ["r8_quartic_lift_score_followup"]
    assert plan["decision"]["recommended_next_lane"]["lane"] == "materially_different_high_real_lane_after_basin_stop"
    assert plan["decision"]["recommended_next_lane"]["target_r_buckets"] == "24"
    assert plan["decision"]["clear_bounded_generation_lane"] is True


def test_score_aware_target_plan_prefers_api_sync_state_over_manual_scores():
    plan = build_plan(
        snapshot=_snapshot(),
        pair_status=_pair_status(),
        score_snapshot=_score_snapshot(),
        basin_summary=_basin_summary(),
        sync_submission_rows=[
            {
                "submission_id": "sub_sync",
                "submitted_line_number": 1,
                "pair_key": "24T9993|r=8",
                "label": "24T9993",
                "r": 8,
                "status": "accepted",
                "status_class": "scoreable",
                "scoreable": True,
                "scoring_status": "scoreable",
                "field_disc_abs": "900",
                "disc_source": "exact_nfdisc",
                "local_match_status": "matched",
            }
        ],
        top_limit=10,
    )

    assert plan["inputs"]["sync_submission_rows"] == 1
    assert plan["inputs"]["sync_pairs"] == 1
    assert plan["top_api_scoreable_targets"][0]["pair_key"] == "24T9993|r=8"
    assert plan["top_api_scoreable_targets"][0]["score_snapshot_points"] == "0.0019"
    assert plan["top_api_scoreable_targets"][0]["api_field_disc_abs"] == "900"
    assert plan["top_api_scoreable_targets"][0]["api_field_vs_global_min_log10_delta"] is not None
    assert not plan["top_score_followup_targets"]
    assert any(lane["lane"] == "api_scoreable_discriminant_review" for lane in plan["lane_recommendations"])


def test_score_aware_target_outputs_round_trip(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    pair_status_path = tmp_path / "pairs.json"
    score_snapshot_path = tmp_path / "scores.json"
    basin_summary_path = tmp_path / "basins.json"
    output_dir = tmp_path / "plan"
    snapshot_path.write_text(json.dumps(_snapshot()), encoding="utf-8")
    pair_status_path.write_text(json.dumps(_pair_status()), encoding="utf-8")
    score_snapshot_path.write_text(json.dumps(_score_snapshot()), encoding="utf-8")
    basin_summary_path.write_text(json.dumps(_basin_summary()), encoding="utf-8")

    plan = build_plan(
        snapshot=json.loads(snapshot_path.read_text(encoding="utf-8")),
        pair_status=load_pair_status(pair_status_path),
        score_snapshot=load_score_snapshot(score_snapshot_path),
        basin_summary=load_basin_summary(basin_summary_path),
        top_limit=10,
    )
    paths = write_outputs(plan, output_dir)

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    ranked_rows = [json.loads(line) for line in paths["ranked_targets_jsonl"].read_text(encoding="utf-8").splitlines()]
    lanes = json.loads(paths["lanes_json"].read_text(encoding="utf-8"))

    assert summary["decision"]["recommended_next_lane"]["lane"] == "r8_quartic_lift_score_followup"
    assert ranked_rows[0]["category"] in {"uncovered_signature", "scored_pair_followup"}
    assert lanes[0]["source_pair"] == "24T9993|r=8"
    assert "IGP24 Score-Aware Target Plan" in paths["report_md"].read_text(encoding="utf-8")


def test_score_aware_target_plan_handles_empty_sync_rows(tmp_path):
    partial_status = {
        "partial_sync": True,
        "submission_state_complete": False,
        "failing_endpoint": "submissions/me",
        "error_code": "IGP24_SERVICE_UNAVAILABLE",
        "error_message": "submissions/me: temporarily unavailable",
    }
    sync_paths = write_sync_artifacts(
        output_dir=tmp_path / "sync",
        competition={"competitionId": "igp24"},
        me={"team": {"role": "activeMember"}},
        progress_snapshot=_snapshot(),
        submission_index={
            "record_type": "igp24_sair_submission_index",
            "submission_count": 0,
            "submissions": [],
            "pages": [],
            "rate_limit_observations": [],
        },
        submission_rows=[],
        command=["pytest"],
        live_fetch=False,
        sync_status=partial_status,
    )
    plan = build_plan(
        snapshot=load_sync_progress_snapshot(sync_paths["summary_json"].parent),
        pair_status=_pair_status(),
        score_snapshot=_score_snapshot(),
        basin_summary=_basin_summary(),
        sync_submission_rows=load_sync_submission_rows(sync_paths["summary_json"].parent),
        sync_status=load_sync_status(sync_paths["summary_json"].parent),
        top_limit=10,
    )
    paths = write_outputs(plan, tmp_path / "plan")

    assert plan["inputs"]["sync_submission_rows"] == 0
    assert plan["inputs"]["sync_partial"] is True
    assert plan["inputs"]["sync_submission_state_complete"] is False
    assert plan["inputs"]["sync_failing_endpoint"] == "submissions/me"
    assert plan["decision"]["full_sync_required_before_submission"] is True
    assert plan["decision"]["submission_recommended_now"] is False
    assert plan["top_api_scoreable_targets"] == []
    assert plan["top_api_pending_targets"] == []
    assert "API Scoreable Targets" in paths["report_md"].read_text(encoding="utf-8")
