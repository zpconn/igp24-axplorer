import json

from scripts.igp24_group_index_readiness_gate import main as readiness_main
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


def _historical_rows(tmp_path, label="24T101"):
    path = tmp_path / "historical.jsonl"
    path.write_text(
        json.dumps(
            {
                "canonical_hash": "hist-a",
                "label": label,
                "r": 16,
                "discriminant": 12345,
                "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [1, 23]}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_readiness_gate_reports_missing_index_without_crashing(tmp_path):
    output_dir = tmp_path / "out"

    assert (
        readiness_main(
            [
                "--score_plan",
                str(_score_plan(tmp_path)),
                "--output_dir",
                str(output_dir),
                "--top_targets",
                "1",
                "--families_per_target",
                "2",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "group_index_readiness_summary.json").read_text(encoding="utf-8"))
    assert summary["group_index_exists"] is False
    assert "missing_group_index" in summary["blocking_reasons"]
    assert "target_label_coverage_incomplete" in summary["blocking_reasons"]
    assert summary["ready_for_group_directed_generation"] is False
    assert summary["live_submission_recommended_now"] is False


def test_readiness_gate_reports_structural_routes_but_blocks_executable_generation(tmp_path):
    score_plan = _score_plan(tmp_path)
    index_path = tmp_path / "groups.sqlite"
    _index(index_path)
    historical = _historical_rows(tmp_path, "24T101")
    output_dir = tmp_path / "ready"

    assert (
        readiness_main(
            [
                "--score_plan",
                str(score_plan),
                "--index",
                str(index_path),
                "--historical_jsonl",
                str(historical),
                "--output_dir",
                str(output_dir),
                "--top_targets",
                "2",
                "--families_per_target",
                "8",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "group_index_readiness_summary.json").read_text(encoding="utf-8"))
    assert summary["index_coverage"]["complete"] is True
    assert summary["historical_containment"]["failure_count"] == 0
    assert summary["structurally_eligible_route_count"] > 0
    assert summary["generation_ready_route_count"] == 0
    assert "no_executable_generation_ready_routes" in summary["blocking_reasons"]
    assert summary["ready_for_structural_route_review"] is True
    assert summary["ready_for_group_directed_generation"] is False
    routes = [
        json.loads(line)
        for line in (output_dir / "group_index_readiness_routes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(row["structurally_eligible"] for row in routes)
    assert all(row["generation_ready"] is False for row in routes)
    assert all(row["executable_generation_ready"] is False for row in routes)


def test_readiness_gate_blocks_true_label_outside_partial_index(tmp_path):
    score_plan = _score_plan(tmp_path)
    index_path = tmp_path / "groups.sqlite"
    _index(index_path)
    historical = _historical_rows(tmp_path, "24T999")
    output_dir = tmp_path / "blocked"

    assert (
        readiness_main(
            [
                "--score_plan",
                str(score_plan),
                "--index",
                str(index_path),
                "--historical_jsonl",
                str(historical),
                "--output_dir",
                str(output_dir),
                "--top_targets",
                "2",
                "--families_per_target",
                "8",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "group_index_readiness_summary.json").read_text(encoding="utf-8"))
    assert summary["historical_containment"]["failure_count"] == 0
    assert summary["historical_containment"]["true_label_outside_index_count"] == 1
    assert summary["historical_containment"]["true_label_containment"] is None
    assert "historical_true_label_containment_not_100pct" in summary["blocking_reasons"]
    assert summary["ready_for_group_directed_generation"] is False
