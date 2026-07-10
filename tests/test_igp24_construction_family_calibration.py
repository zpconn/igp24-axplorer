import json

from scripts.igp24_construction_family_calibration import main as calibration_main


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_family_calibration_normalizes_aliases_and_blocks_exact_false_target_route(tmp_path):
    router_rows = [
        {
            "family": "quartic_in_x6",
            "pair_key": "24T24134|r=8",
            "structurally_eligible": True,
            "executable_generator_available": True,
            "executable_generation_ready": False,
            "construction_outcome_blocking_reasons": ["exact_route_false_target_outcome"],
            "generation_ready_blocking_reasons": ["exact_route_false_target_outcome"],
        },
        {
            "family": "tower_6x4",
            "pair_key": "24T24134|r=8",
            "structurally_eligible": True,
            "executable_generator_available": False,
            "executable_generation_ready": False,
            "generation_ready_blocking_reasons": ["executable_generator_not_bound_to_target"],
        },
    ]
    outcomes = [
        {
            "family": "quartic_in_x6",
            "intended_pair_key": "24T24134|r=8",
            "exact_label_row_count": 4,
            "target_hit_count": 0,
            "false_target_count": 4,
            "submission_grade_count": 0,
            "block_repeat_exact_basin": True,
            "recommended_route_action": "block_repeat_exact_basin",
            "observed_pair_counts": {"24T7635|r=8": 1, "24T10010|r=8": 1, "24T12493|r=8": 1, "24T9962|r=8": 1},
        }
    ]
    replay_summary = {
        "cases": [
            {
                "remediated_replay": {
                    "source_candidate_metrics": {
                        "source_candidate_count": 4,
                        "construction_family_counts": {"r8_quartic_lift_score_followup": 4},
                        "valuable_survival_row_count": 0,
                        "true_label_containment_evaluated_count": 4,
                        "true_label_containment_success_count": 4,
                        "family_outcomes": {"r8_quartic_lift_score_followup": {"24T25000": 4}},
                    }
                }
            }
        ]
    }
    adaptive_rows = [
        {
            "generation_metadata": {"construction_family": "alt_composition_4x6"},
            "eligible_for_packet": False,
            "any_valuable_target_not_ruled_out": False,
            "adaptive_review": {"final_indexed_target_survivor_count": 2, "usable_prime_count": 40},
            "group_compatibility": {"indexed_target_survivor_count": 2, "valuable_targets_not_ruled_out": []},
        },
        {
            "generation_metadata": {"construction_family": "alt_composition_4x6"},
            "eligible_for_packet": False,
            "any_valuable_target_not_ruled_out": False,
            "adaptive_review": {"final_indexed_target_survivor_count": 3, "usable_prime_count": 40},
            "group_compatibility": {"indexed_target_survivor_count": 3, "valuable_targets_not_ruled_out": []},
        },
    ]
    rejected_rows = [
        {
            "features": {"construction_family": "quartic_in_x6"},
            "construction_route_metadata": {"family": "quartic_in_x6", "intended_pair_key": "24T24134|r=8"},
            "reject_reasons": ["construction_route_outcome_blocked"],
        }
    ]

    router = tmp_path / "routes.jsonl"
    route_outcomes = tmp_path / "route_outcomes.jsonl"
    replay = tmp_path / "replay.json"
    adaptive = tmp_path / "adaptive.jsonl"
    rejected = tmp_path / "rejected.jsonl"
    output = tmp_path / "calibration"
    _write_jsonl(router, router_rows)
    _write_jsonl(route_outcomes, outcomes)
    replay.write_text(json.dumps(replay_summary), encoding="utf-8")
    _write_jsonl(adaptive, adaptive_rows)
    _write_jsonl(rejected, rejected_rows)

    assert (
        calibration_main(
            [
                "--router_routes_jsonl",
                str(router),
                "--route_outcomes_jsonl",
                str(route_outcomes),
                "--replay_summary_json",
                str(replay),
                "--adaptive_candidates_jsonl",
                str(adaptive),
                "--packet_rejected_jsonl",
                str(rejected),
                "--output_dir",
                str(output),
            ]
        )
        == 0
    )

    summary = json.loads((output / "construction_family_calibration_summary.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (output / "construction_family_calibration_rows.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_family = {row["family"]: row for row in rows}

    assert summary["live_submission_recommended_now"] is False
    assert summary["expected_points_status"] == "unavailable_uncalibrated"
    assert by_family["quartic_in_x6"]["recommended_action"] == "block_repeat_exact_basin"
    assert by_family["quartic_in_x6"]["exact_label_row_count"] == 4
    assert by_family["quartic_in_x6"]["replay_source_candidate_count"] == 4
    assert by_family["quartic_in_x6"]["raw_family_names"]["r8_quartic_lift_score_followup"] == 2
    assert by_family["composition_4x6"]["recommended_action"] == "do_not_widen_without_material_structural_change"
    assert by_family["composition_4x6"]["adaptive_candidate_count"] == 2
    assert by_family["tower_6x4"]["recommended_action"] == "candidate_for_generator_implementation"
    assert by_family["tower_6x4"]["score_estimate_status"] == "unavailable_uncalibrated"
    report = (output / "construction_family_calibration_report.md").read_text(encoding="utf-8")
    assert "Construction Family Calibration" in report
    assert "block_repeat_exact_basin" in report


def test_family_calibration_marks_executable_unblocked_route_for_bounded_experiment(tmp_path):
    router = tmp_path / "routes.jsonl"
    output = tmp_path / "calibration"
    _write_jsonl(
        router,
        [
            {
                "family": "gx2_degree12_lift",
                "pair_key": "24T101|r=16",
                "structurally_eligible": True,
                "executable_generator_available": True,
                "executable_generation_ready": False,
                "generation_ready_blocking_reasons": ["generated_outputs_not_validated"],
            }
        ],
    )

    assert calibration_main(["--router_routes_jsonl", str(router), "--output_dir", str(output)]) == 0

    rows = [
        json.loads(line)
        for line in (output / "construction_family_calibration_rows.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows[0]["family"] == "gx2_degree12_lift"
    assert rows[0]["recommended_action"] == "run_bounded_adaptive_experiment"
    assert "needs_bounded_adaptive_experiment" in rows[0]["recommendation_reasons"]


def test_family_calibration_reparameterizes_routed_family_with_only_non_target_survivors(tmp_path):
    router = tmp_path / "routes.jsonl"
    adaptive = tmp_path / "adaptive.jsonl"
    output = tmp_path / "calibration"
    _write_jsonl(
        router,
        [
            {
                "family": "composition_8x3",
                "pair_key": "24T24134|r=8",
                "structurally_eligible": True,
                "executable_generator_available": True,
                "executable_generation_ready": False,
            }
        ],
    )
    _write_jsonl(
        adaptive,
        [
            {
                "route": {"family": "composition_8x3", "pair_key": "24T24134|r=8"},
                "eligible_for_packet": True,
                "target_label_not_ruled_out": False,
                "any_valuable_target_not_ruled_out": True,
                "adaptive_review": {"final_indexed_target_survivor_count": 15, "usable_prime_count": 80},
            },
            {
                "route": {"family": "composition_8x3", "pair_key": "24T24134|r=8"},
                "eligible_for_packet": False,
                "target_label_not_ruled_out": False,
                "any_valuable_target_not_ruled_out": False,
                "adaptive_review": {"final_indexed_target_survivor_count": 2, "usable_prime_count": 80},
            },
            {
                "route": {"family": "composition_8x3", "pair_key": "24T24134|r=8"},
                "eligible_for_packet": False,
                "target_label_not_ruled_out": False,
                "any_valuable_target_not_ruled_out": False,
                "adaptive_review": {"final_indexed_target_survivor_count": 2, "usable_prime_count": 80},
            },
        ],
    )

    assert (
        calibration_main(
            [
                "--router_routes_jsonl",
                str(router),
                "--adaptive_candidates_jsonl",
                str(adaptive),
                "--output_dir",
                str(output),
            ]
        )
        == 0
    )

    rows = [
        json.loads(line)
        for line in (output / "construction_family_calibration_rows.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows[0]["family"] == "composition_8x3"
    assert rows[0]["adaptive_valuable_survival_count"] == 1
    assert rows[0]["adaptive_target_compatible_count"] == 0
    assert rows[0]["recommended_action"] == "review_only_until_reparameterized"
    assert "adaptive_review_found_no_target_compatible_survivors" in rows[0]["recommendation_reasons"]
