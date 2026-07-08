import json

from scripts.igp24_anti_basin_planner import (
    build_basin_profile,
    build_submission_recommendation,
    candidate_features,
    load_accepted_feedback_observations,
    normalize_progress_cache,
    score_candidate_row,
    select_diverse_scores,
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


def _axg_model_candidate(candidate_hash, *, template="model:mixed:r20:dense_mixed_support_gcd1", basin="basin-a"):
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": 20,
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


def _axg_model_pending_observation(label="24T25000", template="model:mixed:r20:dense_mixed_support_gcd1", basin="basin-a"):
    return {
        "label": label,
        "pair_key": f"{label}|r=20",
        "r": 20,
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
    assert features["perturbation_mode"] == "sparse_mixed_support_gcd1"
    assert features["support_gcd"] == 1
    assert features["even_support"] is False
    assert features["basin_fingerprint"] == "basin-a"
    assert features["coefficient_hash"] == "coeff-hash"


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
