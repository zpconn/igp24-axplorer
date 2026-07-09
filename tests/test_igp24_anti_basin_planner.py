import json

from scripts.igp24_anti_basin_planner import (
    DEFAULT_ACCEPTED_FEEDBACK_JSONS,
    build_basin_profile,
    build_submission_recommendation,
    candidate_features,
    is_fatal_risk_reason,
    load_accepted_feedback_observations,
    normalize_progress_cache,
    score_candidate_row,
    select_diverse_scores,
    sample_export_source,
    write_outputs,
)


def _progress_snapshot():
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": "2026-07-07T00:00:00+00:00",
        "query": {"limit": 5000},
        "page_count": 1,
        "label_count": 2,
        "pages": [{"generatedAt": "2026-07-07T00:00:01Z", "meta": {"published": True}}],
        "labels": [
            {
                "label": "24T24932",
                "t": 24932,
                "teamCount": 48,
                "allowedR": [24],
                "discoveredSignatures": [24],
                "remainingSignatures": [],
                "minimumDiscAbs": "123",
                "signatures": [{"r": 24, "teamCount": 48, "minimumDiscAbs": "123"}],
            },
            {
                "label": "24T1",
                "t": 1,
                "teamCount": 0,
                "allowedR": [24, 20],
                "discoveredSignatures": [],
                "remainingSignatures": [24, 20],
                "minimumDiscAbs": None,
                "signatures": [{"r": 24, "teamCount": 0}, {"r": 20, "teamCount": 0}],
            },
        ],
    }


def _observation():
    return {
        "label": "24T24932",
        "pair_key": "24T24932|r=24",
        "r": 24,
        "canonical_hash": "accepted-hash",
        "construction_family": "alt_composition_8x3",
        "decomposition_pattern": "8x3",
        "perturbation_mode": "outer_constant_shift",
        "support_gcd": 1,
        "even_support": False,
        "family_key": "8x3:constant",
        "mod_p_pattern_signature": "p3:6-6-6-6",
    }


def _candidate(candidate_hash, mode, *, mod_sig, family_key=None):
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": 24,
        "coefficient_height": 1000,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": (
            [{"prime": 3, "degrees": [6, 6, 6, 6]}]
            if mod_sig == "p3:6-6-6-6"
            else [{"prime": 5, "degrees": [5, 19]}]
        ),
        "generation_metadata": {
            "construction_family": "alt_composition_8x3",
            "decomposition_degree_pattern": "8x3",
            "alt_perturbation_mode": mode,
            "alt_outer_perturbations": [{"outer_y_exponent": 2, "delta": 1}],
            "alt_support_gcd": 1,
            "alt_even_support": False,
            "alt_odd_support_exponents": [1],
            "alt_composition_family_key": family_key or f"8x3:{candidate_hash}",
        },
    }


def _r8_perturbed_observation(label="24T25000", mode="odd_pair_off_core", mod_sig="p3:3-21;p5:5-19;p7:7-8-9"):
    return {
        "label": label,
        "pair_key": f"{label}|r=8",
        "r": 8,
        "canonical_hash": f"accepted-{label}-{mode}",
        "construction_family": "r8_quartic_lift_perturbed",
        "decomposition_pattern": "quartic_in_x6",
        "perturbation_mode": mode,
        "support_gcd": 1,
        "even_support": False,
        "family_key": f"four_positive_fibers_d:{mode}:accepted",
        "mod_p_pattern_signature": mod_sig,
    }


def _r8_perturbed_candidate(candidate_hash, mode="odd_single_off_core", *, mod_sig="p5:2-22"):
    prime_text, degree_text = mod_sig.split(":", 1)
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": 8,
        "coefficient_height": 16,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [1, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, -1, 16, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, 0, 1],
        "mod_p_factorization_degree_patterns": [
            {"prime": int(prime_text.removeprefix("p")), "degrees": [int(value) for value in degree_text.split("-")]}
        ],
        "generation_metadata": {
            "source_family": "r8_quartic_lift_perturbed",
            "r8_quartic_lift_family_key": f"four_positive_fibers_d:{mode}:{candidate_hash}",
            "r8_quartic_lift_perturbation_mode": mode,
            "r8_quartic_lift_perturbation_exponents": [11],
            "r8_quartic_lift_support_gcd": 1,
            "r8_quartic_lift_even_support": False,
        },
    }


def _r8_score_followup_observation(
    *,
    label="24T25000",
    template="r8_score_followup:four_positive_fibers_e:odd_pair_off_core",
    basin="basin-score-followup-a",
    mod_sig="p2:2-4-18;p3:3-4-17;p5:24;p7:3-5-16",
):
    return {
        "label": label,
        "pair_key": f"{label}|r=8",
        "r": 8,
        "canonical_hash": f"accepted-{label}-{basin}",
        "status": "accepted",
        "scoreable": False,
        "scoring_status": "pending",
        "construction_family": "r8_quartic_lift_score_followup",
        "decomposition_pattern": "quartic_in_x6",
        "family_key": "four_positive_fibers_e:odd_pair_off_core:11:1,13:-1",
        "template_family_id": template,
        "basin_fingerprint": basin,
        "perturbation_mode": "odd_pair_off_core",
        "support_gcd": 1,
        "even_support": False,
        "odd_support_exponents": [11, 13],
        "mod_p_pattern_signature": mod_sig,
    }


def _r8_score_followup_candidate(
    candidate_hash,
    *,
    template="r8_score_followup:four_positive_fibers_e:odd_pair_off_core",
    basin="basin-score-followup-a",
    mod_sig="p2:2-4-18;p3:3-4-17;p5:24;p7:3-5-16",
):
    prime_patterns = []
    for part in mod_sig.split(";"):
        prime_text, degree_text = part.split(":", 1)
        prime_patterns.append(
            {"prime": int(prime_text.removeprefix("p")), "degrees": [int(value) for value in degree_text.split("-")]}
        )
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": 8,
        "coefficient_height": 16,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [1, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, 1, 16, -1, 0, 0, 0, 0, -9, 0, 0, 0, 0, 0, 1],
        "mod_p_factorization_degree_patterns": prime_patterns,
        "sample_export_source": "lane_generate:r8_score_followup",
        "generation_metadata": {
            "construction_family": "r8_quartic_lift_score_followup",
            "decomposition_pattern": "quartic_in_x6",
            "generation_strategy": "r8_score_followup_24T9993",
            "family_key": "four_positive_fibers_e:odd_pair_off_core:11:1,13:-1",
            "template_family_id": template,
            "basin_fingerprint": basin,
            "perturbation_mode": "odd_pair_off_core",
            "support_pattern": "quartic_in_x6_odd_pair_off_core_support_gcd1",
            "support_gcd": 1,
            "even_support_like": False,
            "odd_support_exponents": [11, 13],
        },
    }


def _alt_r8_candidate(candidate_hash):
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": 8,
        "coefficient_height": 32,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [5, 19]}],
        "sample_export_source": "lane_generate:r8_alt_composition",
        "generation_metadata": {
            "construction_family": "alt_composition_r8_3x8",
            "decomposition_pattern": "3x8",
            "template_family_id": "alt:r8:3x8:new",
            "family_key": "alt:r8:3x8:new:family",
            "basin_fingerprint": "alt-r8-basin-new",
            "perturbation_mode": "inner_level_shift",
            "support_pattern": "non_quartic_in_x6_support_gcd1",
            "support_gcd": 1,
            "even_support_like": False,
            "odd_support_exponents": [1],
        },
    }


def _axg_model_candidate(
    candidate_hash,
    *,
    r=20,
    template="model:mixed:r20:dense_mixed_support_gcd1",
    basin="basin-a",
):
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": r,
        "coefficient_height": 64,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [1, 23]}],
        "generation_metadata": {
            "construction_family": "model_sample_export",
            "generation_strategy": "mixed",
            "template_family_id": template,
            "family_key": f"{template}:{basin}",
            "perturbation_mode": template.rsplit(":", 1)[-1],
            "support_pattern": template.rsplit(":", 1)[-1],
            "support_gcd": 1,
            "even_support_like": False,
            "odd_support_exponents": [1],
            "basin_fingerprint": basin,
        },
    }


def _axg_model_pending_observation(
    label="24T25000",
    *,
    r=20,
    template="model:mixed:r20:dense_mixed_support_gcd1",
    basin="basin-a",
):
    return {
        "label": label,
        "pair_key": f"{label}|r={r}",
        "r": r,
        "canonical_hash": f"pending-{label}-{basin}",
        "status": "accepted",
        "scoreable": False,
        "scoring_status": "pending",
        "construction_family": "model_sample_export",
        "decomposition_pattern": template.rsplit(":", 1)[-1],
        "perturbation_mode": template.rsplit(":", 1)[-1],
        "support_gcd": 1,
        "even_support": False,
        "family_key": f"{template}:{basin}",
        "template_family_id": template,
        "basin_fingerprint": basin,
        "mod_p_pattern_signature": "p5:1-23",
    }


def test_load_accepted_feedback_observations_reads_rows(tmp_path):
    path = tmp_path / "feedback.json"
    path.write_text(json.dumps({"accepted_rows": [_r8_perturbed_observation()]}), encoding="utf-8")

    rows = load_accepted_feedback_observations([path])

    assert len(rows) == 1
    assert rows[0]["label"] == "24T25000"
    assert rows[0]["construction_family"] == "r8_quartic_lift_perturbed"


def test_default_accepted_feedback_includes_latest_r16_refinement_collapse():
    paths = [str(path) for path in DEFAULT_ACCEPTED_FEEDBACK_JSONS]

    assert any("r16_high_real_refinement_sair_accepted_feedback_20260709.json" in path for path in paths)
    assert any("axg16_sair_accepted_feedback_20260709.json" in path for path in paths)
    assert any("axg17_sair_accepted_feedback_20260709.json" in path for path in paths)
    assert any("axg110_sair_accepted_feedback_20260709.json" in path for path in paths)

    observations = load_accepted_feedback_observations(DEFAULT_ACCEPTED_FEEDBACK_JSONS)
    r16_observations = [
        row
        for row in observations
        if row.get("submission_id") == "sub_997ed4ad0f75476b888b42bea2e3a3d0"
        or row.get("pair_key") == "24T25000|r=16"
    ]

    assert {row["template_family_id"] for row in r16_observations} >= {
        "model:mixed:r16:medium_mixed_support_gcd1",
        "model:mixed:r16:dense_mixed_support_gcd1",
    }
    assert {row["basin_fingerprint"] for row in r16_observations} >= {
        "4d91c3d0fe2fa1d3bebf04e0",
        "6f8f07fe7a66bdc7c4d0be58",
        "6034e5dd17ee25c1245534e5",
        "25548a9429bf4bd396091d24",
    }

    axg110_observations = [row for row in observations if row.get("submission_id") == "sub_e558f7c55b3d45a0a926c5a9c6d05d75"]
    assert len(axg110_observations) == 4
    assert {row["pair_key"] for row in axg110_observations} == {"24T25000|r=4", "24T25000|r=8"}


def test_default_accepted_feedback_includes_r24_deterministic_collapse():
    paths = [str(path) for path in DEFAULT_ACCEPTED_FEEDBACK_JSONS]

    assert any("r24_deterministic_sair_accepted_feedback_20260709.json" in path for path in paths)
    assert any("r20_linear_real_sair_accepted_feedback_20260707.json" in path for path in paths)
    assert any("r24_tower_odd_escape_sair_accepted_feedback_20260707.json" in path for path in paths)

    observations = load_accepted_feedback_observations(DEFAULT_ACCEPTED_FEEDBACK_JSONS)
    r24_observations = [row for row in observations if row.get("pair_key") == "24T25000|r=24"]

    assert len(r24_observations) >= 11
    assert {row.get("template_family_id") for row in r24_observations if row.get("template_family_id")} >= {
        "r24_high_real:single_low_odd_break",
        "r24_high_real:two_low_odd_break",
        "r24_high_real:three_low_odd_break",
    }


def test_candidate_features_reads_r8_quartic_lift_perturbed_metadata():
    row = {
        "canonical_hash": "r8-hash",
        "real_root_count": 8,
        "coefficient_height": 16,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [1, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, -1, 16, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, 0, 1],
        "mod_p_factorization_degree_patterns": [{"prime": 3, "degrees": [1, 6, 7, 10]}],
        "generation_metadata": {
            "source_family": "r8_quartic_lift_perturbed",
            "r8_quartic_lift_family_key": "four_positive_fibers_d:odd_single_off_core:11:-1",
            "r8_quartic_lift_perturbation_mode": "odd_single_off_core",
            "r8_quartic_lift_perturbation_exponents": [11],
            "r8_quartic_lift_support_gcd": 1,
            "r8_quartic_lift_even_support": False,
        },
    }

    features = candidate_features(row)

    assert features["construction_family"] == "r8_quartic_lift_perturbed"
    assert features["decomposition_pattern"] == "quartic_in_x6"
    assert features["perturbation_mode"] == "odd_single_off_core"
    assert features["perturbation_terms"] == 1
    assert features["family_key"] == "four_positive_fibers_d:odd_single_off_core:11:-1"
    assert features["support_gcd"] == 1
    assert features["even_support"] is False
    assert features["odd_support_exponents"] == [11]


def test_candidate_features_reads_axg14_generic_provenance_metadata():
    row = {
        "canonical_hash": "model-hash",
        "real_root_count": 20,
        "coefficient_height": 7,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [1, 23]}],
        "generation_metadata": {
            "construction_family": "model_sample_export",
            "generation_strategy": "mixed",
            "template_family_id": "model:mixed:r20:sparse_mixed_support_gcd1",
            "family_key": "model:mixed:r20:sparse_mixed_support_gcd1:basin-a",
            "perturbation_mode": "sparse_mixed_support_gcd1",
            "support_pattern": "sparse_mixed_support_gcd1",
            "support_gcd": 1,
            "even_support_like": False,
            "odd_support_exponents": [1],
            "coefficient_hash": "coeff-hash",
            "decoded_hash": "decoded-hash",
            "basin_fingerprint": "basin-a",
            "source_seed_hash": "seed-a",
        },
    }

    features = candidate_features(row)

    assert features["construction_family"] == "model_sample_export"
    assert features["decomposition_pattern"] == "sparse_mixed_support_gcd1"
    assert features["template_family_id"] == "model:mixed:r20:sparse_mixed_support_gcd1"
    assert features["family_key"] == "model:mixed:r20:sparse_mixed_support_gcd1:basin-a"
    assert features["perturbation_mode"] == "sparse_odd_single_e1_support_gcd1"
    assert features["sparse_support_submode"] == "sparse_odd_single_e1_support_gcd1"
    assert features["support_gcd"] == 1
    assert features["even_support"] is False
    assert features["basin_fingerprint"] == "basin-a"
    assert features["coefficient_hash"] == "coeff-hash"


def test_candidate_features_reads_r24_high_real_probe_metadata():
    row = {
        "canonical_hash": "r24-high-real-hash",
        "real_root_count": 24,
        "coefficient_height": 1000,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [1, 0, 1, 0, 1] + [0] * 19 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 7, "degrees": [1, 2, 21]}],
        "generation_metadata": {
            "construction_family": "positive_quadratic_product_plus_low_odd_perturbation",
            "r24_high_real_exact_composed_seed_divisor": 2,
            "r24_high_real_family_key": "single_low_odd_break|roots=1,2|odd=9",
            "r24_high_real_mode": "single_low_odd_break",
            "r24_high_real_odd_perturbations": [{"x_exponent": 9, "delta": 1}],
            "r24_high_real_odd_support_after_perturbation": [9],
        },
    }

    features = candidate_features(row)

    assert features["construction_family"] == "positive_quadratic_product_plus_low_odd_perturbation"
    assert features["decomposition_pattern"] == "near_composed_quadratic_product_d2"
    assert features["perturbation_mode"] == "single_low_odd_break"
    assert features["perturbation_terms"] == 1
    assert features["template_family_id"] == "r24_high_real:single_low_odd_break"
    assert features["basin_fingerprint"] == "single_low_odd_break|roots=1,2|odd=9"
    assert features["family_key"] == "single_low_odd_break|roots=1,2|odd=9"
    assert features["odd_support_exponents"] == [9]
    assert sample_export_source({"source_strategy": "r24_high_real_quadratic_product_probe"}) == (
        "r24_high_real_quadratic_product_probe"
    )


def test_candidate_features_reads_escape_lane_probe_metadata():
    r20_row = {
        "canonical_hash": "r20-linear-hash",
        "real_root_count": 20,
        "coefficient_height": 1000,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [1, 23]}],
        "generation_metadata": {
            "construction_family": "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation",
            "decomposition_degree_pattern": "20x1_plus_2x2_noncomposed",
            "r20_linear_mode": "three_low_coefficient_break",
            "r20_linear_family_key": "three_low_coefficient_break|roots=-1,1|no_real=1,3|pert=1:1,3:-1,5:1",
            "r20_linear_coefficient_perturbations": [
                {"x_exponent": 1, "delta": 1},
                {"x_exponent": 3, "delta": -1},
                {"x_exponent": 5, "delta": 1},
            ],
            "r20_linear_support_gcd": 1,
            "r20_linear_even_support": False,
            "r20_linear_odd_support_exponents": [1, 3, 5],
        },
    }
    r16_row = {
        "canonical_hash": "r16-diversity-hash",
        "real_root_count": 16,
        "coefficient_height": 1000,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 7, "degrees": [2, 22]}],
        "generation_metadata": {
            "strategy": "r16_diversified_root_layout_probe",
            "r16_diversity_mode": "mixed_even_odd_perturbed",
            "r16_diversity_family_key": "mixed_even_odd_perturbed|roots=1,2|quads=1-1,1-2|odd=1,5|y=5",
            "r16_diversity_off_block_perturbation_exponents": [1, 5],
            "r16_diversity_divisor2_off_block_terms": 2,
        },
    }
    r24_tower_row = {
        "canonical_hash": "r24-tower-escape-hash",
        "real_root_count": 24,
        "coefficient_height": 1000,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "mod_p_factorization_degree_patterns": [{"prime": 3, "degrees": [1, 23]}],
        "generation_metadata": {
            "construction_family": "odd_perturbed_r24_6x4_tower_escape",
            "decomposition_degree_pattern": "6x4_seed_plus_odd_x_perturbation",
            "r24_tower_odd_escape_mode": "single_odd_tower_escape",
            "r24_tower_odd_escape_family_key": "s=6|mode=single_odd_tower_escape|real=-1,-2|odd_x=1:1",
            "r24_tower_odd_escape_odd_perturbations": [{"x_exponent": 1, "delta": 1}],
            "r24_tower_odd_escape_support_gcd": 1,
            "r24_tower_odd_escape_even_support_after_perturbation": False,
            "r24_tower_odd_escape_odd_support_exponents": [1],
        },
    }

    r20_features = candidate_features(r20_row)
    r16_features = candidate_features(r16_row)
    r24_features = candidate_features(r24_tower_row)

    assert r20_features["template_family_id"].startswith(
        "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation:"
    )
    assert r20_features["basin_fingerprint"] == r20_features["family_key"]
    assert r20_features["perturbation_mode"] == "three_low_coefficient_break"
    assert r20_features["odd_support_exponents"] == [1, 3, 5]

    assert r16_features["template_family_id"] == "r16_diversified_root_layout_probe::mixed_even_odd_perturbed"
    assert r16_features["basin_fingerprint"] == r16_features["family_key"]
    assert r16_features["support_gcd"] == 1
    assert r16_features["even_support"] is False

    assert r24_features["template_family_id"] == (
        "odd_perturbed_r24_6x4_tower_escape:6x4_seed_plus_odd_x_perturbation:single_odd_tower_escape"
    )
    assert r24_features["basin_fingerprint"] == r24_features["family_key"]
    assert r24_features["perturbation_terms"] == 1


def test_construction_family_feedback_holds_older_crowded_lane_repeat():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[20])
    basin_profile = build_basin_profile(
        [
            {
                "label": "24T25000",
                "pair_key": "24T25000|r=20",
                "r": 20,
                "canonical_hash": "accepted-r20-linear",
                "construction_family": "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation",
                "family_key": "accepted-r20-linear-family",
                "support_gcd": 1,
                "mod_p_pattern_signature": "p5:1-23",
            }
        ],
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 52}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )
    repeat = score_candidate_row(
        {
            "canonical_hash": "r20-linear-repeat",
            "real_root_count": 20,
            "coefficient_height": 1000,
            "irreducible": True,
            "squarefree": True,
            "exported_coefficients": [2, 1] + [0] * 22 + [1],
            "mod_p_factorization_degree_patterns": [{"prime": 7, "degrees": [1, 23]}],
            "generation_metadata": {
                "construction_family": "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation",
                "decomposition_degree_pattern": "20x1_plus_2x2_noncomposed",
                "r20_linear_mode": "single_low_coefficient_break",
                "r20_linear_family_key": "new-r20-linear-family",
                "r20_linear_coefficient_perturbations": [{"x_exponent": 1, "delta": 1}],
                "r20_linear_support_gcd": 1,
                "r20_linear_even_support": False,
            },
        },
        target_rs={20},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert repeat["eligible_for_packet"] is False
    assert "construction_family_known_high_label_collapse=24T25000" in repeat["risk_reasons"]


def test_r8_quartic_in_x6_feedback_holds_repeat_packet_even_with_new_modp_signature():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[8])
    basin_profile = build_basin_profile(
        [
            _r8_perturbed_observation("24T25000", "odd_pair_off_core"),
            _r8_perturbed_observation("24T24979", "odd_single_off_core", "p7:8-16"),
        ],
        {
            "24T25000": {"global_progress": {"fully_covered": True, "team_count": 49}},
            "24T24979": {"global_progress": {"fully_covered": True, "team_count": 54}},
        },
        avoid_labels={"24T25000", "24T24979"},
        crowded_team_threshold=20,
    )

    scored = [
        score_candidate_row(
            _r8_perturbed_candidate(f"r8-repeat-{index}", mode="odd_triple_off_core", mod_sig=f"p{index + 3}:1-23"),
            target_rs={8},
            progress_cache=progress,
            basin_profile=basin_profile,
        )
        for index in range(8)
    ]
    selected = select_diverse_scores(scored, packet_limit=8, per_mode_cap=8, per_pattern_cap=8)
    recommendation = build_submission_recommendation(selected, min_packet_rows=8)

    assert selected == []
    assert recommendation["recommended_for_sair_packet"] is False
    assert all(row["eligible_for_packet"] is False for row in scored)
    assert all(
        any(reason.startswith("r8_quartic_in_x6_known_label_collapse=24T24979,24T25000") for reason in row["risk_reasons"])
        for row in scored
    )


def test_r8_score_followup_24t25000_collapse_holds_same_template_and_basin():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[8])
    basin_profile = build_basin_profile(
        [_r8_score_followup_observation()],
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 58}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )

    repeat = score_candidate_row(
        _r8_score_followup_candidate("repeat-score-followup"),
        target_rs={8},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert repeat["eligible_for_packet"] is False
    assert "r8_quartic_in_x6_known_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "template_family_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "basin_fingerprint_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "exact_crowded_basin_fingerprint_hits=1" in repeat["risk_reasons"]


def test_r8_score_followup_collapse_does_not_block_materially_different_r8_construction():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[8])
    basin_profile = build_basin_profile(
        [_r8_score_followup_observation()],
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 58}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )

    novel = score_candidate_row(
        _alt_r8_candidate("novel-alt-r8"),
        target_rs={8},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert novel["eligible_for_packet"] is True
    assert novel["risk_reasons"] == []
    assert novel["anti_basin_classification"] == "strong_packet_candidate"


def test_model_template_and_basin_feedback_hold_24t25000_repeat():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[20])
    basin_profile = build_basin_profile(
        [_axg_model_pending_observation()],
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 52}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )

    repeat = score_candidate_row(
        _axg_model_candidate("repeat-model", template="model:mixed:r20:dense_mixed_support_gcd1", basin="basin-a"),
        target_rs={20},
        progress_cache=progress,
        basin_profile=basin_profile,
    )
    novel = score_candidate_row(
        _axg_model_candidate("novel-model", template="model:mixed:r20:new_support_gcd1", basin="basin-b"),
        target_rs={20},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert repeat["eligible_for_packet"] is False
    assert "model_template_family_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "model_basin_fingerprint_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert novel["eligible_for_packet"] is True
    assert novel["score"] > repeat["score"]


def test_axg17_r8_model_mixed_feedback_holds_24t25000_repeats():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[8])
    observations = load_accepted_feedback_observations(DEFAULT_ACCEPTED_FEEDBACK_JSONS)
    basin_profile = build_basin_profile(
        observations,
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 59}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )

    repeat = score_candidate_row(
        _axg_model_candidate(
            "r8-repeat-axg17",
            r=8,
            template="model:mixed:r8:dense_mixed_support_gcd1",
            basin="62e1fe77acd58f753d31e517",
        ),
        target_rs={8},
        progress_cache=progress,
        basin_profile=basin_profile,
    )
    novel = score_candidate_row(
        _axg_model_candidate(
            "r8-novel-axg17",
            r=8,
            template="model:mixed:r8:novel_support_gcd1",
            basin="fresh-r8-basin",
        ),
        target_rs={8},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert repeat["eligible_for_packet"] is False
    assert "model_template_family_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "model_basin_fingerprint_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert novel["eligible_for_packet"] is True
    assert novel["score"] > repeat["score"]


def test_axg16_model_mixed_high_real_pattern_is_fatal_even_without_exact_feedback():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[12, 20, 24])
    basin_profile = build_basin_profile([], {}, avoid_labels={"24T25000"}, crowded_team_threshold=20)

    for r_value in (12, 20, 24):
        blocked = score_candidate_row(
            _axg_model_candidate(
                f"axg16-pattern-r{r_value}",
                r=r_value,
                template=f"model:mixed:r{r_value}:medium_mixed_support_gcd1",
                basin=f"fresh-basin-r{r_value}",
            ),
            target_rs={12, 20, 24},
            progress_cache=progress,
            basin_profile=basin_profile,
        )
        reason_prefix = f"model_mixed_high_real_24T25000_collapse_pattern:r{r_value}:medium_mixed_support_gcd1"

        assert blocked["eligible_for_packet"] is False
        assert reason_prefix in blocked["fatal_risk_reasons"]

    r16_candidate = score_candidate_row(
        _axg_model_candidate(
            "axg16-pattern-r16-not-global-fatal",
            r=16,
            template="model:mixed:r16:medium_mixed_support_gcd1",
            basin="fresh-basin-r16",
        ),
        target_rs={16},
        progress_cache=normalize_progress_cache(_progress_snapshot(), target_rs=[16]),
        basin_profile=basin_profile,
    )
    assert r16_candidate["eligible_for_packet"] is True
    assert not any(
        str(reason).startswith("model_mixed_high_real_24T25000_collapse_pattern")
        for reason in r16_candidate["risk_reasons"]
    )


def test_axg18_model_fixed_sparse_high_real_pattern_is_fatal_even_without_exact_feedback():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[16, 20, 24])
    basin_profile = build_basin_profile([], {}, avoid_labels={"24T25000"}, crowded_team_threshold=20)

    for r_value in (16, 20, 24):
        blocked = score_candidate_row(
            _axg_model_candidate(
                f"axg18-fixed-sparse-pattern-r{r_value}",
                r=r_value,
                template=f"model:fixed_sparse_template:r{r_value}:medium_mixed_support_gcd1",
                basin=f"fresh-fixed-sparse-basin-r{r_value}",
            ),
            target_rs={16, 20, 24},
            progress_cache=progress,
            basin_profile=basin_profile,
        )
        reason_prefix = (
            f"model_fixed_sparse_high_real_24T25000_collapse_pattern:r{r_value}:medium_mixed_support_gcd1"
        )

        assert blocked["eligible_for_packet"] is False
        assert reason_prefix in blocked["fatal_risk_reasons"]

    sparse_variant = score_candidate_row(
        _axg_model_candidate(
            "axg18-fixed-sparse-sparse-mode-not-global-fatal",
            r=16,
            template="model:fixed_sparse_template:r16:sparse_mixed_support_gcd1",
            basin="fresh-fixed-sparse-sparse-basin-r16",
        ),
        target_rs={16},
        progress_cache=normalize_progress_cache(_progress_snapshot(), target_rs=[16]),
        basin_profile=basin_profile,
    )
    assert sparse_variant["eligible_for_packet"] is True
    assert not any(
        str(reason).startswith("model_fixed_sparse_high_real_24T25000_collapse_pattern")
        for reason in sparse_variant["risk_reasons"]
    )


def test_r16_model_mixed_dense_medium_feedback_holds_24t25000_repeats():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[16])
    observations = load_accepted_feedback_observations(DEFAULT_ACCEPTED_FEEDBACK_JSONS)
    basin_profile = build_basin_profile(
        observations,
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 49}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )

    medium_repeat = score_candidate_row(
        _axg_model_candidate(
            "r16-repeat-medium",
            r=16,
            template="model:mixed:r16:medium_mixed_support_gcd1",
            basin="4d91c3d0fe2fa1d3bebf04e0",
        ),
        target_rs={16},
        progress_cache=progress,
        basin_profile=basin_profile,
    )
    dense_repeat = score_candidate_row(
        _axg_model_candidate(
            "r16-repeat-dense",
            r=16,
            template="model:mixed:r16:dense_mixed_support_gcd1",
            basin="6034e5dd17ee25c1245534e5",
        ),
        target_rs={16},
        progress_cache=progress,
        basin_profile=basin_profile,
    )
    novel = score_candidate_row(
        _axg_model_candidate(
            "r16-novel-sparse",
            r=16,
            template="model:mixed:r16:sparse_mixed_support_gcd1",
            basin="novel-r16-basin",
        ),
        target_rs={16},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert medium_repeat["eligible_for_packet"] is False
    assert dense_repeat["eligible_for_packet"] is False
    assert "model_template_family_known_high_label_collapse=24T25000" in medium_repeat["risk_reasons"]
    assert "model_basin_fingerprint_known_high_label_collapse=24T25000" in medium_repeat["risk_reasons"]
    assert "model_template_family_known_high_label_collapse=24T25000" in dense_repeat["risk_reasons"]
    assert "model_basin_fingerprint_known_high_label_collapse=24T25000" in dense_repeat["risk_reasons"]
    assert novel["eligible_for_packet"] is True
    assert novel["score"] > medium_repeat["score"]
    assert novel["score"] > dense_repeat["score"]


def test_r24_high_real_feedback_holds_24t25000_repeat():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[24])
    observations = load_accepted_feedback_observations(DEFAULT_ACCEPTED_FEEDBACK_JSONS)
    basin_profile = build_basin_profile(
        observations,
        {"24T25000": {"global_progress": {"fully_covered": True, "team_count": 45}}},
        avoid_labels={"24T25000"},
        crowded_team_threshold=20,
    )
    repeat = score_candidate_row(
        {
            "canonical_hash": "r24-repeat-three-low-odd",
            "real_root_count": 24,
            "coefficient_height": 1931559552,
            "irreducible": True,
            "squarefree": True,
            "exported_coefficients": [
                479001600,
                1,
                -1486442880,
                0,
                1931559552,
                -1,
                -1414014888,
                0,
                657206836,
                1,
                -206070150,
                0,
                44990231,
                0,
                -6926634,
                0,
                749463,
                0,
                -55770,
                0,
                2717,
                0,
                -78,
                0,
                1,
            ],
            "mod_p_factorization_degree_patterns": [
                {"prime": 2, "degrees": [1, 23]},
                {"prime": 3, "degrees": [1, 23]},
                {"prime": 5, "degrees": [1, 3, 3, 4, 6, 7]},
                {"prime": 7, "degrees": [1, 23]},
            ],
            "generation_metadata": {
                "construction_family": "positive_quadratic_product_plus_low_odd_perturbation",
                "r24_high_real_exact_composed_seed_divisor": 2,
                "r24_high_real_family_key": "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=1,5,9",
                "r24_high_real_mode": "three_low_odd_break",
                "r24_high_real_odd_perturbations": [
                    {"x_exponent": 1, "delta": 1},
                    {"x_exponent": 5, "delta": -1},
                    {"x_exponent": 9, "delta": 1},
                ],
                "r24_high_real_odd_support_after_perturbation": [1, 5, 9],
            },
        },
        target_rs={24},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert repeat["eligible_for_packet"] is False
    assert "template_family_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "basin_fingerprint_known_high_label_collapse=24T25000" in repeat["risk_reasons"]
    assert "exact_crowded_basin_fingerprint_hits=1" in repeat["risk_reasons"]


def test_submission_recommendation_can_require_model_generated_rows():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[8])
    basin_profile = build_basin_profile([], {}, avoid_labels=set(), crowded_team_threshold=20)
    selected = []
    for index in range(4):
        mode = "odd_single_off_core" if index % 2 else "odd_triple_off_core"
        candidate = _r8_perturbed_candidate(f"clean-{index}", mode=mode, mod_sig=f"p{index + 3}:1-23")
        candidate["sample_export_source"] = "target_r_seed_bank"
        selected.append(
            score_candidate_row(
                candidate,
                target_rs={8},
                progress_cache=progress,
                basin_profile=basin_profile,
            )
        )

    seed_bank_recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
    )
    assert seed_bank_recommendation["recommended_for_sair_packet"] is False
    assert "model_generated" in seed_bank_recommendation["reason"]
    assert seed_bank_recommendation["model_generated_selected_rows"] == 0

    for row in selected:
        row["candidate"]["sample_export_source"] = "model_generate"
    model_recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
    )

    assert model_recommendation["recommended_for_sair_packet"] is True
    assert model_recommendation["model_generated_selected_rows"] == 4
    assert model_recommendation["selected_source_counts"] == {"model_generate": 4}


def test_submission_recommendation_can_require_axg14_family_and_basin_diversity():
    selected = []
    for index in range(4):
        selected.append(
            {
                "risk_reasons": [],
                "candidate": {"sample_export_source": "model_generate"},
                "features": {
                    "perturbation_mode": "sparse_mixed_support_gcd1" if index % 2 else "medium_mixed_support_gcd1",
                    "mod_p_pattern_signature": f"p{index + 3}:1-23",
                    "template_family_id": "model:mixed:r20:sparse_mixed_support_gcd1",
                    "family_key": f"family-{index}",
                    "basin_fingerprint": f"basin-{index}",
                },
            }
        )

    held = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )
    assert held["recommended_for_sair_packet"] is False
    assert "template_family" in held["reason"]
    assert held["selected_basin_fingerprint_counts"] == {
        "basin-0": 1,
        "basin-1": 1,
        "basin-2": 1,
        "basin-3": 1,
    }

    selected[1]["features"]["template_family_id"] = "model:mixed:r20:medium_mixed_support_gcd1"
    passed = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )
    assert passed["recommended_for_sair_packet"] is True


def test_submission_recommendation_can_allow_single_mode_with_template_diversity_for_lane_generated_rows():
    selected = []
    for index in range(4):
        selected.append(
            {
                "risk_reasons": [],
                "candidate": {"sample_export_source": "lane_generate:r8_score_followup"},
                "features": {
                    "r": 8,
                    "perturbation_mode": "odd_pair_off_core",
                    "mod_p_pattern_signature": f"p{index + 3}:1-23",
                    "template_family_id": "r8_score_followup:four_positive_fibers_e:odd_pair_off_core"
                    if index < 2
                    else "r8_score_followup:four_positive_fibers_f:odd_pair_off_core",
                    "family_key": f"family-{index}",
                    "basin_fingerprint": f"basin-{index}",
                },
            }
        )

    default_held = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )
    assert default_held["recommended_for_sair_packet"] is False
    assert "min_perturbation_mode_count_2" in default_held["reason"]

    r8_lane_passed = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_perturbation_mode_count=1,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )
    assert r8_lane_passed["recommended_for_sair_packet"] is True
    assert r8_lane_passed["model_generated_selected_rows"] == 4
    assert r8_lane_passed["min_perturbation_mode_count"] == 1


def test_submission_recommendation_counts_sparse_model_submodes_as_mode_diversity():
    selected = []
    odd_supports = ([11], [13], [9, 11], [9, 13])
    for index, odd_support in enumerate(odd_supports):
        row = {
            "canonical_hash": f"sparse-{index}",
            "sample_export_source": "model_generate",
            "real_root_count": 8,
            "irreducible": True,
            "squarefree": True,
            "exported_coefficients": [1, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, -1, 16, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, 0, 1],
            "mod_p_factorization_degree_patterns": [{"prime": index + 3, "degrees": [1, 23]}],
            "generation_metadata": {
                "construction_family": "model_sample_export",
                "template_family_id": "model:mixed:r8:sparse_mixed_support_gcd1",
                "family_key": f"model:mixed:r8:sparse_mixed_support_gcd1:basin-{index}",
                "basin_fingerprint": f"basin-{index}",
                "perturbation_mode": "sparse_mixed_support_gcd1",
                "support_pattern": "sparse_mixed_support_gcd1",
                "support_gcd": 1,
                "even_support_like": False,
                "odd_support_exponents": list(odd_support),
            },
        }
        selected.append(
            {
                "risk_reasons": [],
                "fatal_risk_reasons": [],
                "advisory_risk_reasons": [],
                "candidate": row,
                "features": candidate_features(row),
            }
        )

    recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=1,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )

    assert recommendation["recommended_for_sair_packet"] is True
    assert recommendation["selected_mode_counts"] == {
        "sparse_odd_pair_gap2_support_gcd1": 1,
        "sparse_odd_pair_gap4_support_gcd1": 1,
        "sparse_odd_single_e11_support_gcd1": 1,
        "sparse_odd_single_e13_support_gcd1": 1,
    }


def test_submission_recommendation_treats_loose_crowded_risk_as_advisory():
    selected = []
    for index in range(4):
        selected.append(
            {
                "risk_reasons": ["loose_crowded_basin_fingerprint_hits=2"],
                "fatal_risk_reasons": [],
                "advisory_risk_reasons": ["loose_crowded_basin_fingerprint_hits=2"],
                "candidate": {"sample_export_source": "model_generate"},
                "features": {
                    "r": 20 if index < 2 else 24,
                    "perturbation_mode": "dense_mixed_support_gcd1" if index % 2 else "medium_mixed_support_gcd1",
                    "mod_p_pattern_signature": f"p{index + 3}:1-23",
                    "template_family_id": "model:mixed:r20:dense_mixed_support_gcd1"
                    if index < 2
                    else "model:mixed:r24:medium_mixed_support_gcd1",
                    "family_key": f"family-{index}",
                    "basin_fingerprint": f"basin-{index}",
                },
            }
        )

    recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )

    assert is_fatal_risk_reason("loose_crowded_basin_fingerprint_hits=2") is False
    assert recommendation["recommended_for_sair_packet"] is True
    assert recommendation["risk_count"] == 0
    assert recommendation["fatal_risk_count"] == 0
    assert recommendation["advisory_risk_count"] == 4
    assert recommendation["reason"] == "anti-basin gates passed"


def test_submission_recommendation_still_blocks_fatal_known_collapse_risk():
    selected = []
    for index in range(4):
        selected.append(
            {
                "risk_reasons": ["model_template_family_known_high_label_collapse=24T25000"],
                "fatal_risk_reasons": ["model_template_family_known_high_label_collapse=24T25000"],
                "advisory_risk_reasons": [],
                "candidate": {"sample_export_source": "model_generate"},
                "features": {
                    "r": 20,
                    "perturbation_mode": "dense_mixed_support_gcd1" if index % 2 else "medium_mixed_support_gcd1",
                    "mod_p_pattern_signature": f"p{index + 3}:1-23",
                    "template_family_id": "model:mixed:r20:dense_mixed_support_gcd1"
                    if index < 2
                    else "model:mixed:r20:medium_mixed_support_gcd1",
                    "family_key": f"family-{index}",
                    "basin_fingerprint": f"basin-{index}",
                },
            }
        )

    recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
    )

    assert is_fatal_risk_reason("model_template_family_known_high_label_collapse=24T25000") is True
    assert recommendation["recommended_for_sair_packet"] is False
    assert recommendation["risk_count"] == 4
    assert recommendation["fatal_risk_count"] == 4
    assert recommendation["advisory_risk_count"] == 0
    assert "fatal_risk_reasons" in recommendation["reason"]


def test_submission_recommendation_holds_local_ready_packet_on_partial_sync_and_pending_basin():
    selected = []
    for index in range(4):
        selected.append(
            {
                "risk_reasons": [],
                "candidate": {"sample_export_source": "model_generate"},
                "features": {
                    "r": 20,
                    "perturbation_mode": "sparse_mixed_support_gcd1" if index % 2 else "medium_mixed_support_gcd1",
                    "mod_p_pattern_signature": f"p{index + 3}:1-23",
                    "template_family_id": "model:mixed:r20:sparse_mixed_support_gcd1"
                    if index < 2
                    else "model:mixed:r20:medium_mixed_support_gcd1",
                    "family_key": f"family-{index}",
                    "basin_fingerprint": f"basin-{index}",
                },
            }
        )
    selected[0]["candidate"]["pair_key"] = "24T25000|r=20"

    recommendation = build_submission_recommendation(
        selected,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
        sync_status={
            "partial_sync": True,
            "submission_index_complete": True,
            "submission_detail_complete": False,
            "download_complete": False,
            "full_submission_state_complete": False,
            "degraded_mode_summary": "19/20 details recovered",
        },
        sync_submission_rows=[
            {
                "status_class": "pending",
                "pair_key": "24T25000|r=20",
                "label": "24T25000",
                "r": 20,
                "scoring_status": "pending",
            }
            for _ in range(8)
        ],
        pending_collision_labels={"24T25000"},
    )

    assert recommendation["local_recommended_for_sair_packet"] is True
    assert recommendation["recommended_for_sair_packet"] is False
    assert recommendation["sync_submission_gate"]["pending_pair_counts"] == {"24T25000|r=20": 8}
    assert "incomplete_sair_state" in recommendation["reason"]
    assert "pending_collision_risk:24T25000|r=20=8" in recommendation["reason"]
    assert "pending_rows_resolve:24T25000|r=20=8" in recommendation["reason"]


def test_anti_basin_score_rejects_constant_shift_and_accepts_novel_nonconstant():
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[24, 20])
    basin_profile = build_basin_profile(
        [_observation()],
        {"24T24932": {"global_progress": {"fully_covered": True, "team_count": 48}}},
        avoid_labels={"24T24932"},
        crowded_team_threshold=20,
    )

    constant = score_candidate_row(
        _candidate("constant-hash", "outer_constant_shift", mod_sig="p3:6-6-6-6"),
        target_rs={24, 20},
        progress_cache=progress,
        basin_profile=basin_profile,
    )
    novel = score_candidate_row(
        _candidate("novel-hash", "outer_two_coefficient_shift", mod_sig="p5:5-19"),
        target_rs={24, 20},
        progress_cache=progress,
        basin_profile=basin_profile,
    )

    assert constant["eligible_for_packet"] is False
    assert "outer_constant_shift_after_24T24932_collapse" in constant["risk_reasons"]
    assert novel["eligible_for_packet"] is True
    assert novel["score"] > constant["score"]
    assert novel["anti_basin_classification"] == "strong_packet_candidate"


def test_anti_basin_selection_and_outputs_round_trip(tmp_path):
    progress = normalize_progress_cache(_progress_snapshot(), target_rs=[24, 20])
    basin_profile = build_basin_profile(
        [_observation()],
        {"24T24932": {"global_progress": {"fully_covered": True, "team_count": 48}}},
        avoid_labels={"24T24932"},
        crowded_team_threshold=20,
    )
    rows = [
        score_candidate_row(
            _candidate(f"hash-{index}", "outer_two_coefficient_shift" if index % 2 else "outer_high_coefficient_shift", mod_sig="p5:5-19"),
            target_rs={24, 20},
            progress_cache=progress,
            basin_profile=basin_profile,
        )
        for index in range(6)
    ]

    selected = select_diverse_scores(rows, packet_limit=4, per_mode_cap=3, per_pattern_cap=4)
    recommendation = build_submission_recommendation(selected, min_packet_rows=4)

    assert len(selected) == 4
    assert recommendation["selected_rows"] == 4
    assert recommendation["recommended_for_sair_packet"] is False
    assert "mod_p" in recommendation["reason"]

    summary = {
        "record_type": "igp24_anti_basin_planner",
        "candidate_count": len(rows),
        "eligible_candidate_count": len([row for row in rows if row["eligible_for_packet"]]),
        "selected_rows": len(selected),
        "inputs": {"progress_source": {"label_count": 2}},
        "basin_profile": {"avoid_labels": ["24T24932"], "crowded_labels": ["24T24932"]},
        "submission_recommendation": recommendation,
        "selected_rows_summary": [
            {"rank": i + 1, "short_hash": row["short_hash"], "score": row["score"], "features": row["features"]}
            for i, row in enumerate(selected)
        ],
        "top_scored_rows": [
            {
                "rank": i + 1,
                "short_hash": row["short_hash"],
                "score": row["score"],
                "eligible_for_packet": row["eligible_for_packet"],
                "classification": row["anti_basin_classification"],
                "risk_reasons": row["risk_reasons"],
            }
            for i, row in enumerate(rows)
        ],
        "next_decision": "test",
    }
    paths = write_outputs(
        output_dir=tmp_path,
        progress_cache=progress,
        scored_rows=rows,
        selected=selected,
        summary_without_outputs=summary,
    )

    assert json.loads(paths["summary_json"].read_text(encoding="utf-8"))["record_type"] == "igp24_anti_basin_planner"
    assert len(paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()) == 4
    assert "IGP24 Anti-Basin Planner" in paths["report_md"].read_text(encoding="utf-8")
