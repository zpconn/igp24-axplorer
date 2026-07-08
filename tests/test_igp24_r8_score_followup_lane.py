from scripts.igp24_anti_basin_planner import is_model_generated_source
from scripts.igp24_r8_score_followup_generate import base_coefficients, metadata_for
from scripts.igp24_r8_score_followup_lane import prepare_lane


def _raw_candidate(hash_value="h1", *, coeff_shift=0, r=8):
    coeffs = [2 + coeff_shift] + [0] * 24
    coeffs[1] = 1
    coeffs[6] = -8
    coeffs[12] = 16
    coeffs[18] = -8
    coeffs[24] = 1
    return {
        "canonical_hash": hash_value,
        "exported_coefficients": coeffs,
        "real_root_count": r,
        "valid": True,
        "irreducible": True,
        "squarefree": True,
        "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [1, 23]}],
        "generation_metadata": {
            "strategy": "r8_quartic_lift_perturbed",
            "resolved_generation_strategy": "r8_quartic_lift_perturbed",
            "source_family": "r8_quartic_lift_perturbed",
            "r8_quartic_lift_template_name": "four_positive_fibers_d",
            "r8_quartic_lift_family_key": f"four_positive_fibers_d:odd_single_off_core:{1 + coeff_shift}:1",
            "r8_quartic_lift_perturbation_mode": "odd_single_off_core",
            "r8_quartic_lift_support_gcd": 1,
            "r8_quartic_lift_even_support": False,
        },
    }


def test_prepare_lane_enriches_required_generic_provenance(tmp_path):
    accepted, rejected, summary = prepare_lane(
        [(tmp_path / "candidates.jsonl", _raw_candidate())],
        target_r=8,
        source_signal_pair="24T9993|r=8",
    )

    assert len(accepted) == 1
    assert rejected == []
    row = accepted[0]
    assert row["sample_export_source"] == "lane_generate:r8_score_followup"
    assert row["construction_family"] == "r8_quartic_lift_perturbed"
    assert row["generation_strategy"] == "r8_score_followup_24T9993"
    assert row["template_family_id"] == "r8_score_followup:four_positive_fibers_d:odd_single_off_core"
    assert row["basin_fingerprint"]
    assert row["perturbation_mode"] == "odd_single_off_core"
    assert row["support_pattern"] == "quartic_in_x6_odd_single_off_core_support_gcd1"
    assert row["generation_metadata"]["template_family_id"] == row["template_family_id"]
    assert summary["accepted_rows"] == 1
    assert summary["basin_fingerprint_count"] == 1


def test_prepare_lane_rejects_duplicates_and_wrong_real_root_count(tmp_path):
    path = tmp_path / "candidates.jsonl"
    accepted, rejected, summary = prepare_lane(
        [
            (path, _raw_candidate("h1")),
            (path, _raw_candidate("h1")),
            (path, _raw_candidate("h2", coeff_shift=1, r=6)),
        ],
        target_r=8,
        source_signal_pair="24T9993|r=8",
    )

    assert len(accepted) == 1
    assert len(rejected) == 2
    assert summary["rejection_reason_counts"]["duplicate_canonical_hash"] == 1
    assert summary["rejection_reason_counts"]["duplicate_coefficient_line"] == 1
    assert summary["rejection_reason_counts"]["real_root_count_not_target"] == 1


def test_lane_generate_counts_as_generated_source():
    assert is_model_generated_source("lane_generate:r8_score_followup")


def test_score_followup_generator_targets_24t9993_templates():
    coeffs_e = base_coefficients("four_positive_fibers_e")
    coeffs_f = base_coefficients("four_positive_fibers_f")

    assert [coeffs_e[index] for index in (0, 6, 12, 18)] == [1, -8, 16, -9]
    assert [coeffs_f[index] for index in (0, 6, 12, 18)] == [1, -9, 16, -8]

    metadata = metadata_for(
        template_name="four_positive_fibers_e",
        perturbations=[(11, -1), (15, 1)],
        trial_index=7,
        seed=3201,
        coeff_bound=16,
        analysis_r=8,
    )

    assert metadata["source_signal_pair"] == "24T9993|r=8"
    assert metadata["source_pair_hint"] == "24T9993|r=8"
    assert metadata["source_family"] == "r8_quartic_lift_score_followup"
    assert metadata["r8_quartic_lift_perturbation_mode"] == "odd_pair_off_core"
