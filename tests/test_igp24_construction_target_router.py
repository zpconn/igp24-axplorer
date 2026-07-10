import json

from scripts.igp24_construction_target_router import (
    build_routes,
    explicit_targets_from_pairs,
    load_score_plan,
    main as router_main,
    select_targets,
    summarize_routes,
)
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord


def _score_plan(tmp_path):
    path = tmp_path / "score_plan.json"
    path.write_text(
        json.dumps(
            {
                "record_type": "igp24_score_aware_target_plan",
                "created_at": "2026-07-09T00:00:00+00:00",
                "ranked_targets": [
                    {
                        "pair_key": "24T101|r=16",
                        "label": "24T101",
                        "t": 101,
                        "r": 16,
                        "category": "uncovered_signature",
                        "progress_state": "remaining",
                        "target_score": 500.0,
                        "maximum_possible_points": 1.0,
                        "estimated_expected_points": 1.0,
                        "score_ceiling_class": "uncovered_first_team_one_point",
                        "signature_team_count": 0,
                    },
                    {
                        "pair_key": "24T102|r=24",
                        "label": "24T102",
                        "t": 102,
                        "r": 24,
                        "category": "uncovered_signature",
                        "progress_state": "remaining",
                        "target_score": 450.0,
                        "maximum_possible_points": 1.0,
                        "estimated_expected_points": 1.0,
                        "score_ceiling_class": "uncovered_first_team_one_point",
                        "signature_team_count": 0,
                    },
                    {
                        "pair_key": "24T25000|r=16",
                        "label": "24T25000",
                        "t": 25000,
                        "r": 16,
                        "category": "covered_or_crowded",
                        "progress_state": "discovered",
                        "target_score": 1.0,
                        "maximum_possible_points": 0.0,
                        "estimated_expected_points": 0.0,
                        "score_ceiling_class": "crowded_near_zero_ceiling",
                        "signature_team_count": 50,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _index(path):
    index = GroupCycleIndex(path)
    index.initialize(provenance={"test": True})
    index.upsert_group(
        GroupRecord(
            label="24T101",
            t=101,
            primitive=False,
            solvable=True,
            block_sizes=(2, 12),
            cycle_types=("1.23", "2.22"),
        )
    )
    index.upsert_group(
        GroupRecord(
            label="24T102",
            t=102,
            primitive=True,
            solvable=False,
            block_sizes=(),
            cycle_types=("24",),
        )
    )
    return index


def test_router_blocks_proxy_routes_when_group_invariants_are_missing(tmp_path):
    score_plan_path = _score_plan(tmp_path)
    score_plan = load_score_plan(score_plan_path)

    routes = build_routes(
        score_plan=score_plan,
        group_index=None,
        avoid_labels=["24T25000"],
        top_targets=1,
        families_per_target=3,
        require_group_invariants=True,
    )

    assert len(routes) == 3
    assert {row["structurally_eligible"] for row in routes} == {False}
    assert {row["executable_generation_ready"] for row in routes} == {False}
    assert {row["generation_ready"] for row in routes} == {False}
    assert all(row["blocking_reasons"] == ["missing_group_invariants"] for row in routes)
    summary = summarize_routes(
        score_plan_path=score_plan_path,
        group_index_path=None,
        score_plan=score_plan,
        routes=routes,
        avoid_labels=["24T25000"],
        top_targets=1,
        families_per_target=3,
        category="uncovered_signature",
        require_group_invariants=True,
    )
    assert summary["target_group_record_missing_count"] == 1
    assert summary["structurally_eligible_route_count"] == 0
    assert summary["blocking_reason_counts"] == {"missing_group_invariants": 3}
    assert summary["live_submission_recommended_now"] is False


def test_router_uses_group_invariants_to_rank_imprimitive_and_primitive_targets(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    index = _index(tmp_path / "groups.sqlite")

    routes = build_routes(
        score_plan=score_plan,
        group_index=index,
        avoid_labels=["24T25000"],
        top_targets=2,
        families_per_target=8,
        require_group_invariants=True,
    )

    imprimitive_routes = [row for row in routes if row["pair_key"] == "24T101|r=16"]
    primitive_routes = [row for row in routes if row["pair_key"] == "24T102|r=24"]
    assert any(row["structurally_eligible"] for row in imprimitive_routes)
    assert not any(row["executable_generation_ready"] for row in routes)
    gx2 = next(row for row in imprimitive_routes if row["family"] == "gx2_degree12_lift")
    assert gx2["structurally_eligible"] is True
    assert gx2["executable_generator_available"] is True
    assert gx2["executable_generator_name"] == "gx2_exact_composed_lift_v1"
    assert gx2["target_parameters_instantiated"] is True
    assert gx2["target_generator_parameters"]["positive_y_root_count"] == 8
    assert gx2["generation_ready"] is False
    assert "generated_outputs_not_validated" in gx2["generation_ready_blocking_reasons"]
    assert "adaptive_target_exclusion_not_run" in gx2["generation_ready_blocking_reasons"]
    assert "executable_generator_not_bound_to_target" not in gx2["generation_ready_blocking_reasons"]
    assert "matching_block_sizes=2,12" in gx2["family_reasons"]

    primitive_generic = next(row for row in primitive_routes if row["family"] == "generic_sparse_random")
    primitive_gx2 = next(row for row in primitive_routes if row["family"] == "gx2_degree12_lift")
    assert primitive_generic["structurally_eligible"] is True
    assert primitive_generic["generation_ready"] is False
    assert primitive_gx2["structurally_eligible"] is False
    assert "forced_imprimitive_family_for_primitive_target" in primitive_gx2["blocking_reasons"]
    assert primitive_generic["combined_priority_score"] > primitive_gx2["combined_priority_score"]


def test_router_marks_quartic_x6_exact_generator_only_for_supported_low_r(tmp_path):
    score_plan_path = tmp_path / "score_plan.json"
    score_plan_path.write_text(
        json.dumps(
            {
                "record_type": "igp24_score_aware_target_plan",
                "created_at": "2026-07-09T00:00:00+00:00",
                "ranked_targets": [
                    {
                        "pair_key": "24T103|r=8",
                        "label": "24T103",
                        "t": 103,
                        "r": 8,
                        "category": "uncovered_signature",
                        "progress_state": "remaining",
                        "target_score": 300.0,
                        "maximum_possible_points": 1.0,
                        "signature_team_count": 0,
                    },
                    {
                        "pair_key": "24T104|r=24",
                        "label": "24T104",
                        "t": 104,
                        "r": 24,
                        "category": "uncovered_signature",
                        "progress_state": "remaining",
                        "target_score": 299.0,
                        "maximum_possible_points": 1.0,
                        "signature_team_count": 0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    index = GroupCycleIndex(tmp_path / "groups.sqlite")
    index.initialize(provenance={"test": True})
    for label, t_value in (("24T103", 103), ("24T104", 104)):
        index.upsert_group(
            GroupRecord(
                label=label,
                t=t_value,
                primitive=False,
                solvable=True,
                block_sizes=(6, 12),
                cycle_types=("1.23",),
            )
        )

    routes = build_routes(
        score_plan=load_score_plan(score_plan_path),
        group_index=index,
        avoid_labels=[],
        top_targets=2,
        families_per_target=8,
        require_group_invariants=True,
    )

    low_r_quartic = next(row for row in routes if row["pair_key"] == "24T103|r=8" and row["family"] == "quartic_in_x6")
    high_r_quartic = next(row for row in routes if row["pair_key"] == "24T104|r=24" and row["family"] == "quartic_in_x6")

    assert low_r_quartic["structurally_eligible"] is True
    assert low_r_quartic["executable_generator_available"] is True
    assert low_r_quartic["executable_generator_name"] == "quartic_x6_exact_lift_v1"
    assert low_r_quartic["target_generator_parameters"]["positive_y_root_count"] == 4
    assert high_r_quartic["structurally_eligible"] is True
    assert high_r_quartic["executable_generator_available"] is False
    assert "generator_unsupported_target_r" in high_r_quartic["generation_ready_blocking_reasons"]


def test_select_targets_uses_explicit_score_plan_category_buckets():
    plan = {
        "record_type": "igp24_score_aware_target_plan",
        "ranked_targets": [
            {
                "pair_key": "24T104|r=24",
                "label": "24T104",
                "r": 24,
                "category": "uncovered_signature",
            }
        ],
        "top_api_scoreable_targets": [
            {
                "pair_key": "24T9993|r=8",
                "label": "24T9993",
                "r": 8,
                "category": "api_scoreable_pair_followup",
            }
        ],
    }

    targets = select_targets(plan, top_targets=5, category="api_scoreable_pair_followup")

    assert [row["pair_key"] for row in targets] == ["24T9993|r=8"]


def test_explicit_targets_use_progress_without_treating_missing_as_uncovered():
    plan = {"record_type": "igp24_score_aware_target_plan", "ranked_targets": []}
    progress = [
        {
            "label": "24T103",
            "t": 103,
            "allowedR": [8],
            "remainingSignatures": [],
            "discoveredSignatures": [8],
            "signatures": [
                {
                    "r": 8,
                    "discovered": True,
                    "teamCount": 2,
                    "minimumDiscAbs": "123456789",
                }
            ],
        }
    ]

    targets = explicit_targets_from_pairs(
        plan,
        target_pairs=["24T103|r=8", "24T103|r=24", "24T104|r=8"],
        progress_rows=progress,
    )
    by_pair = {row["pair_key"]: row for row in targets}

    assert by_pair["24T103|r=8"]["progress_state"] == "allowed_discovered"
    assert by_pair["24T103|r=8"]["category"] == "explicit_low_team_signature"
    assert by_pair["24T103|r=8"]["signature_team_count"] == 2
    assert by_pair["24T103|r=8"]["maximum_possible_points"] == 0.5
    assert by_pair["24T103|r=24"]["progress_state"] == "signature_not_allowed"
    assert by_pair["24T103|r=24"]["maximum_possible_points"] == 0.0
    assert by_pair["24T104|r=8"]["progress_state"] == "progress_data_missing_unknown"
    assert by_pair["24T104|r=8"]["category"] == "explicit_progress_unknown"
    assert by_pair["24T104|r=8"]["maximum_possible_points"] == 0.0
    assert by_pair["24T104|r=8"]["estimated_expected_points"] is None


def test_router_routes_explicit_low_team_x6_pair_from_progress(tmp_path):
    plan = {"record_type": "igp24_score_aware_target_plan", "ranked_targets": []}
    progress = [
        {
            "label": "24T103",
            "t": 103,
            "allowedR": [8],
            "remainingSignatures": [],
            "discoveredSignatures": [8],
            "signatures": [{"r": 8, "discovered": True, "teamCount": 1, "minimumDiscAbs": "123"}],
        }
    ]
    index = GroupCycleIndex(tmp_path / "groups.sqlite")
    index.initialize(provenance={"test": True})
    index.upsert_group(
        GroupRecord(
            label="24T103",
            t=103,
            primitive=False,
            solvable=True,
            block_sizes=(3, 6),
            cycle_types=("1.23",),
        )
    )

    routes = build_routes(
        score_plan=plan,
        group_index=index,
        avoid_labels=[],
        top_targets=25,
        families_per_target=8,
        target_pairs=["24T103|r=8"],
        progress_rows=progress,
        require_group_invariants=True,
    )

    quartic = next(row for row in routes if row["family"] == "quartic_in_x6")
    assert quartic["explicit_target_requested"] is True
    assert quartic["explicit_target_source"] == "progress_jsonl"
    assert quartic["progress_state"] == "allowed_discovered"
    assert quartic["signature_team_count"] == 1
    assert quartic["maximum_possible_points"] == 1.0
    assert quartic["target_group_block_sizes"] == [3, 6]
    assert quartic["structurally_eligible"] is True
    assert quartic["executable_generator_available"] is True
    assert quartic["executable_generator_name"] == "quartic_x6_exact_lift_v1"


def test_router_downranks_exact_false_target_route_outcome(tmp_path):
    plan = {"record_type": "igp24_score_aware_target_plan", "ranked_targets": []}
    progress = [
        {
            "label": "24T103",
            "t": 103,
            "allowedR": [8],
            "remainingSignatures": [],
            "discoveredSignatures": [8],
            "signatures": [{"r": 8, "discovered": True, "teamCount": 1, "minimumDiscAbs": "123"}],
        }
    ]
    route_outcomes = [
        {
            "intended_pair_key": "24T103|r=8",
            "family": "quartic_in_x6",
            "block_repeat_exact_basin": True,
            "blocking_reason": "exact_route_false_target_outcome",
            "recommended_route_action": "block_repeat_exact_basin",
            "route_outcome": "all_false_target_discovered_not_improved",
        }
    ]
    index = GroupCycleIndex(tmp_path / "groups.sqlite")
    index.initialize(provenance={"test": True})
    index.upsert_group(
        GroupRecord(
            label="24T103",
            t=103,
            primitive=False,
            solvable=True,
            block_sizes=(3, 6),
            cycle_types=("1.23",),
        )
    )

    routes = build_routes(
        score_plan=plan,
        group_index=index,
        avoid_labels=[],
        top_targets=25,
        families_per_target=8,
        target_pairs=["24T103|r=8"],
        progress_rows=progress,
        route_outcomes=route_outcomes,
        require_group_invariants=True,
    )

    quartic = next(row for row in routes if row["family"] == "quartic_in_x6")
    assert quartic["structurally_eligible"] is True
    assert quartic["executable_generator_available"] is True
    assert quartic["route_stage"] == "outcome_blocked"
    assert quartic["construction_outcome_blocking_reasons"] == ["exact_route_false_target_outcome"]
    assert "exact_route_false_target_outcome" in quartic["generation_ready_blocking_reasons"]
    summary = summarize_routes(
        score_plan_path=tmp_path / "score_plan.json",
        group_index_path=tmp_path / "groups.sqlite",
        score_plan=plan,
        routes=routes,
        avoid_labels=[],
        top_targets=25,
        families_per_target=8,
        category=None,
        target_pairs_requested=["24T103|r=8"],
        route_outcome_count=len(route_outcomes),
        require_group_invariants=True,
    )
    assert summary["construction_outcome_blocked_route_count"] == 1
    assert summary["construction_outcome_blocking_reason_counts"] == {"exact_route_false_target_outcome": 1}


def test_construction_target_router_cli_writes_parseable_outputs(tmp_path):
    score_plan_path = _score_plan(tmp_path)
    _index(tmp_path / "groups.sqlite")
    output_dir = tmp_path / "routes"

    assert (
        router_main(
            [
                "--score_plan",
                str(score_plan_path),
                "--group_index",
                str(tmp_path / "groups.sqlite"),
                "--output_dir",
                str(output_dir),
                "--top_targets",
                "2",
                "--families_per_target",
                "4",
                "--avoid_label",
                "24T25000",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "construction_target_router_summary.json").read_text(encoding="utf-8"))
    assert summary["target_pair_count"] == 2
    assert summary["target_group_record_hit_count"] == 2
    assert summary["structurally_eligible_route_count"] >= 1
    assert summary["executable_generator_available_route_count"] >= 1
    assert summary["generation_ready_route_count"] == 0
    rows = [
        json.loads(line)
        for line in (output_dir / "construction_target_routes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 8
    assert any(row["structurally_eligible"] for row in rows)
    assert any(row["executable_generator_available"] for row in rows)
    assert all(row["generation_ready"] is False for row in rows)
    assert all(row["live_submission_recommended_now"] is False for row in rows)
    report = (output_dir / "construction_target_router_report.md").read_text(encoding="utf-8")
    assert "IGP24 Construction Target Router" in report
