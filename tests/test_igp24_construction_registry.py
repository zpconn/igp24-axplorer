import json

from scripts.igp24_construction_registry_report import main as registry_report_main
from src.igp24.constructions.generators import (
    coefficients_from_composition_8x3_trial,
    coefficients_from_gx2_trial,
    coefficients_from_quartic_x6_trial,
    coefficients_from_tower_6x4_trial,
    generation_status_for_route,
    iter_composition_8x3_trials,
    iter_gx2_trials,
    iter_quartic_x6_trials,
    iter_tower_6x4_trials,
)
from src.igp24.constructions.registry import (
    SOUNDNESS_NOTE,
    default_registry,
    rank_families_for_target,
    registry_summary,
)
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord


def _fixture_index(path):
    index = GroupCycleIndex(path)
    index.initialize(provenance={"test": True})
    index.upsert_group(
        GroupRecord(
            label="24T101",
            t=101,
            order=48,
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
            order=24,
            primitive=True,
            solvable=False,
            block_sizes=(),
            cycle_types=("24",),
        )
    )
    return index


def test_default_registry_covers_required_phase5_families_without_exact_label_claims():
    registry = default_registry()
    family_names = {family.name for family in registry.families()}

    assert {
        "gx2_degree12_lift",
        "quartic_in_x6",
        "tower_6x4",
        "composition_8x3",
        "composition_4x6",
        "linear_real_product",
        "positive_quadratic_product",
        "generic_sparse_random",
    } <= family_names
    summary = registry_summary(registry)
    assert summary["exact_label_claimed_count"] == 0
    assert summary["soundness"] == SOUNDNESS_NOTE
    assert summary["supported_r_family_counts"]["24"] >= 4


def test_registry_resolves_existing_metadata_aliases():
    registry = default_registry()

    assert registry.resolve("degree12_base_six_positive_roots_lifted_by_x2").name == "gx2_degree12_lift"
    assert registry.resolve("r8_quartic_lift_score_followup").name == "quartic_in_x6"
    assert registry.resolve("positive_quadratic_product_plus_low_odd_perturbation").name == (
        "positive_quadratic_product"
    )
    assert registry.from_metadata({"template_family_id": "model:mixed:r20:sparse_mixed_support_gcd1"}).name == (
        "generic_sparse_random"
    )


def test_family_ranking_warns_on_forced_imprimitive_family_for_primitive_target():
    primitive = GroupRecord(
        label="24T102",
        t=102,
        primitive=True,
        solvable=False,
        cycle_types=("24",),
    )

    rows = rank_families_for_target(r_value=24, group_record=primitive, avoid_labels=["24T25000"])
    gx2 = next(row for row in rows if row["family"] == "gx2_degree12_lift")
    generic = next(row for row in rows if row["family"] == "generic_sparse_random")

    assert "forced_imprimitive_family_for_primitive_target" in gx2["warnings"]
    assert generic["routing_score"] > gx2["routing_score"]
    assert generic["exact_label_claimed"] is False


def test_family_ranking_prefers_matching_block_family_for_imprimitive_target():
    imprimitive = GroupRecord(
        label="24T101",
        t=101,
        primitive=False,
        solvable=True,
        block_sizes=(2, 12),
        cycle_types=("1.23",),
    )

    rows = rank_families_for_target(r_value=16, group_record=imprimitive)
    gx2 = next(row for row in rows if row["family"] == "gx2_degree12_lift")

    assert gx2["supports_target_r"] is True
    assert "imprimitive_target_matches_family" in gx2["reasons"]
    assert "matching_block_sizes=2,12" in gx2["reasons"]


def test_gx2_executable_generator_instantiates_target_r_and_preserves_even_support():
    imprimitive = GroupRecord(
        label="24T101",
        t=101,
        primitive=False,
        solvable=True,
        block_sizes=(2, 12),
        cycle_types=("1.23",),
    )
    status = generation_status_for_route(
        family_name="gx2_degree12_lift",
        r_value=16,
        group_record=imprimitive,
        structurally_eligible=True,
    )

    assert status["executable_generator_available"] is True
    assert status["target_generator_parameters"]["positive_y_root_count"] == 8
    assert status["target_generator_parameters"]["negative_y_root_count"] == 4
    assert status["executable_generation_ready"] is False
    assert "generated_outputs_not_validated" in status["generation_ready_blocking_reasons"]

    trial = next(iter_gx2_trials(target_r=16, seed=7, max_trials=1))
    coefficients, metadata = coefficients_from_gx2_trial(trial)

    assert len(coefficients) == 24
    assert metadata["positive_y_root_count"] == 8
    assert metadata["negative_y_root_count"] == 4
    assert metadata["odd_x_power_terms_present"] is False
    assert all(index % 2 == 0 for index in metadata["support_after_lift"])


def test_quartic_x6_exact_generator_is_low_r_and_preserves_x6_support():
    imprimitive = GroupRecord(
        label="24T103",
        t=103,
        primitive=False,
        solvable=True,
        block_sizes=(6, 12),
        cycle_types=("1.23",),
    )
    status = generation_status_for_route(
        family_name="quartic_in_x6",
        r_value=8,
        group_record=imprimitive,
        structurally_eligible=True,
    )

    assert status["executable_generator_available"] is True
    assert status["executable_generator_name"] == "quartic_x6_exact_lift_v1"
    assert status["target_generator_parameters"]["positive_y_root_count"] == 4
    assert status["target_generator_parameters"]["negative_y_root_count"] == 0
    assert status["executable_generation_ready"] is False
    assert "generated_outputs_not_validated" in status["generation_ready_blocking_reasons"]

    trial = next(iter_quartic_x6_trials(target_r=8, seed=11, max_trials=1))
    coefficients, metadata = coefficients_from_quartic_x6_trial(trial)

    assert len(coefficients) == 24
    assert metadata["positive_y_root_count"] == 4
    assert metadata["negative_y_root_count"] == 0
    assert metadata["exact_composed_support_divisor"] == 6
    assert metadata["non_x6_power_terms_present"] is False
    assert all(index % 6 == 0 for index in metadata["support_after_lift"])


def test_quartic_x6_exact_generator_refuses_high_real_routes():
    imprimitive = GroupRecord(
        label="24T104",
        t=104,
        primitive=False,
        solvable=True,
        block_sizes=(6, 12),
        cycle_types=("1.23",),
    )
    status = generation_status_for_route(
        family_name="quartic_in_x6",
        r_value=24,
        group_record=imprimitive,
        structurally_eligible=True,
    )

    assert status["executable_generator_available"] is False
    assert status["target_parameters_instantiated"] is False
    assert "generator_unsupported_target_r" in status["generation_ready_blocking_reasons"]


def test_composition_8x3_exact_generator_instantiates_and_preserves_composition():
    imprimitive = GroupRecord(
        label="24T105",
        t=105,
        primitive=False,
        solvable=True,
        block_sizes=(3, 8),
        cycle_types=("1.23",),
    )
    status = generation_status_for_route(
        family_name="composition_8x3",
        r_value=16,
        group_record=imprimitive,
        structurally_eligible=True,
    )

    assert status["executable_generator_available"] is True
    assert status["executable_generator_name"] == "composition_8x3_exact_cubic_lift_v1"
    assert status["target_generator_parameters"]["inside_y_root_count"] == 4
    assert status["target_generator_parameters"]["outside_y_root_count"] == 4
    assert status["executable_generation_ready"] is False
    assert "generated_outputs_not_validated" in status["generation_ready_blocking_reasons"]

    trial = next(iter_composition_8x3_trials(target_r=16, seed=13, max_trials=1))
    coefficients, metadata = coefficients_from_composition_8x3_trial(trial)

    assert len(coefficients) == 24
    assert metadata["inside_y_root_count"] == 4
    assert metadata["outside_y_root_count"] == 4
    assert metadata["exact_composition_degree_pattern"] == "8x3"
    assert metadata["composed_support"] is True
    assert metadata["inner_cubic_coefficients_x"] == [0, -12, 0, 1]
    assert max(metadata["support_after_lift"]) <= 23


def test_tower_6x4_exact_generator_instantiates_and_preserves_composition():
    imprimitive = GroupRecord(
        label="24T106",
        t=106,
        primitive=False,
        solvable=True,
        block_sizes=(4, 6),
        cycle_types=("1.23",),
    )
    status = generation_status_for_route(
        family_name="tower_6x4",
        r_value=12,
        group_record=imprimitive,
        structurally_eligible=True,
    )

    assert status["executable_generator_available"] is True
    assert status["executable_generator_name"] == "tower_6x4_exact_quartic_inner_v1"
    assert status["target_generator_parameters"]["four_real_preimage_level_count"] == 3
    assert status["target_generator_parameters"]["no_real_preimage_level_count"] == 3
    assert status["executable_generation_ready"] is False
    assert "generated_outputs_not_validated" in status["generation_ready_blocking_reasons"]

    trial = next(iter_tower_6x4_trials(target_r=12, seed=17, max_trials=1))
    coefficients, metadata = coefficients_from_tower_6x4_trial(trial)

    assert len(coefficients) == 24
    assert metadata["four_real_preimage_level_count"] == 3
    assert metadata["no_real_preimage_level_count"] == 3
    assert metadata["exact_composition_degree_pattern"] == "6x4"
    assert metadata["tower_expression"] == "h(q(x)), q(x)=x^4-s*x^2"
    assert metadata["composed_support"] is True
    assert metadata["inner_quartic_coefficients_x"][-1] == 1
    assert metadata["odd_x_power_terms_present"] is False
    assert all(index % 2 == 0 for index in metadata["support_after_lift"])


def test_construction_registry_report_cli_writes_artifacts(tmp_path):
    index = _fixture_index(tmp_path / "groups.sqlite")
    assert index.group_count() == 2
    output_dir = tmp_path / "out"

    assert (
        registry_report_main(
            [
                "--output_dir",
                str(output_dir),
                "--target_r",
                "16",
                "--target_label",
                "24T101",
                "--group_index",
                str(tmp_path / "groups.sqlite"),
                "--avoid_label",
                "24T25000",
                "--top_limit",
                "5",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "construction_registry_summary.json").read_text(encoding="utf-8"))
    assert summary["target"]["group_record_available"] is True
    assert summary["target"]["block_sizes"] == [2, 12]
    assert summary["live_submission_recommended_now"] is False
    assert summary["exact_label_claimed_count"] == 0
    rankings = [
        json.loads(line)
        for line in (output_dir / "construction_family_rankings.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rankings) == 5
    assert rankings[0]["soundness"] == SOUNDNESS_NOTE
    report = (output_dir / "construction_registry_report.md").read_text(encoding="utf-8")
    assert "IGP24 Construction Registry" in report
    assert "Live submission recommended now: `False`" in report
