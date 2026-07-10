import json

from scripts.igp24_construction_target_router import (
    build_routes,
    load_score_plan,
    main as router_main,
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
