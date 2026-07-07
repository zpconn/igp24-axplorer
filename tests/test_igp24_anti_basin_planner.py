import json

from scripts.igp24_anti_basin_planner import (
    build_basin_profile,
    build_submission_recommendation,
    candidate_features,
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
