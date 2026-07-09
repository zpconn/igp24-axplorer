import json

from scripts.igp24_anti_basin_feedback import build_feedback, update_pair_status


def _selected_row(candidate_hash, score=123.0):
    return {
        "canonical_hash": candidate_hash,
        "real_root_count": 24,
        "coefficient_height": 1000,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "anti_basin_score": score,
        "anti_basin_classification": "strong_packet_candidate",
        "anti_basin_risk_reasons": [],
        "anti_basin_score_explanation": ["test"],
        "anti_basin_features": {
            "construction_family": "alt_composition_8x3",
            "decomposition_pattern": "8x3",
            "perturbation_mode": "outer_two_coefficient_shift",
            "family_key": f"family:{candidate_hash}",
            "template_family_id": f"template:{candidate_hash}",
            "basin_fingerprint": f"basin:{candidate_hash}",
            "support_gcd": 1,
            "even_support": False,
            "odd_support_exponents": [1],
            "mod_p_pattern_signature": "p5:5-19",
        },
        "generation_metadata": {
            "construction_family": "alt_composition_8x3",
            "decomposition_degree_pattern": "8x3",
            "alt_perturbation_mode": "outer_two_coefficient_shift",
            "alt_composition_family_key": f"family:{candidate_hash}",
            "alt_support_gcd": 1,
            "alt_even_support": False,
            "alt_odd_support_exponents": [1],
        },
    }


def test_anti_basin_feedback_joins_rows_and_updates_pairs(tmp_path):
    selected_path = tmp_path / "selected.jsonl"
    selected_path.write_text(
        "\n".join(json.dumps(row) for row in [_selected_row("hash-a"), _selected_row("hash-b", score=99.0)]) + "\n",
        encoding="utf-8",
    )
    status_path = tmp_path / "status.json"
    status_path.write_text(
        json.dumps(
            {
                "data": {
                    "submissionId": "sub_test",
                    "competitionId": "igp24",
                    "verifiedPolynomials": [
                        {
                            "polynomialIndex": 0,
                            "status": "accepted",
                            "label": "24T24932",
                            "t": 24932,
                            "r": 24,
                            "scoreable": False,
                            "scoringStatus": "pending",
                            "discSource": None,
                            "inBaseline": False,
                            "baselineUnlocked": False,
                        },
                        {
                            "polynomialIndex": 1,
                            "status": "accepted",
                            "label": "24T24932",
                            "t": 24932,
                            "r": 12,
                            "scoreable": False,
                            "scoringStatus": "pending",
                            "discSource": None,
                            "inBaseline": False,
                            "baselineUnlocked": False,
                        },
                    ],
                    "failedPolynomials": [],
                    "payload": {"queuedPolynomials": []},
                }
            }
        ),
        encoding="utf-8",
    )
    output_json = tmp_path / "feedback.json"

    feedback = build_feedback(
        status_response_path=status_path,
        selected_jsonl_path=selected_path,
        output_json_path=output_json,
    )
    assert feedback["summary"]["accepted_rows"] == 2
    assert feedback["summary"]["label_counts"] == {"24T24932": 2}
    assert feedback["summary"]["escaped_known_basins"] is False
    assert feedback["accepted_rows"][0]["anti_basin_classification"] == "strong_packet_candidate"
    assert feedback["accepted_rows"][0]["template_family_id"] == "template:hash-a"
    assert feedback["accepted_rows"][0]["basin_fingerprint"] == "basin:hash-a"

    pair_status, update = update_pair_status(
        {"record_type": "igp24_pair_status_ledger", "pairs": [{"pair_key": "24T24932|r=24", "canonical_hash": "old"}]},
        feedback,
        feedback_path=output_json,
    )

    assert update["new_pairs_added"] == 1
    assert update["alternates_added"] == 1
    pairs = {pair["pair_key"]: pair for pair in pair_status["pairs"]}
    assert pairs["24T24932|r=24"]["canonical_hash"] == "old"
    assert pairs["24T24932|r=24"]["accepted_alternates"][0]["canonical_hash"] == "hash-a"
    assert pairs["24T24932|r=24"]["accepted_alternates"][0]["template_family_id"] == "template:hash-a"
    assert pairs["24T24932|r=24"]["accepted_alternates"][0]["basin_fingerprint"] == "basin:hash-a"
    assert pairs["24T24932|r=12"]["anti_basin_score"] == 99.0
    assert pairs["24T24932|r=12"]["template_family_id"] == "template:hash-b"
    assert pairs["24T24932|r=12"]["basin_fingerprint"] == "basin:hash-b"


def test_anti_basin_feedback_unwraps_proposal_loop_selected_rows(tmp_path):
    candidate = _selected_row("hash-wrapper")
    candidate["generation_metadata"] = {
        "construction_family": "model_sample_export",
        "template_family_id": "model:sparse:r8:sparse_mixed_support_gcd1",
        "family_key": "model:sparse:r8:sparse_mixed_support_gcd1:basin-wrapper",
        "support_gcd": 1,
        "even_support_like": False,
        "odd_support_exponents": [11],
    }
    selected_path = tmp_path / "selected.jsonl"
    selected_path.write_text(
        json.dumps(
            {
                "candidate": candidate,
                "score": 118.5,
                "anti_basin_classification": "strong_packet_candidate",
                "features": {
                    "construction_family": "model_sample_export",
                    "decomposition_pattern": "sparse_mixed_support_gcd1",
                    "perturbation_mode": "sparse_odd_single_e11_support_gcd1",
                    "family_key": "model:sparse:r8:sparse_mixed_support_gcd1:basin-wrapper",
                    "template_family_id": "model:sparse:r8:sparse_mixed_support_gcd1",
                    "basin_fingerprint": "basin-wrapper",
                    "support_gcd": 1,
                    "even_support": False,
                    "odd_support_exponents": [11],
                    "mod_p_pattern_signature": "p3:3-21",
                },
                "risk_reasons": [],
                "score_explanation": ["test"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    status_path = tmp_path / "status.json"
    status_path.write_text(
        json.dumps(
            {
                "data": {
                    "submissionId": "sub_wrapper",
                    "competitionId": "igp24",
                    "verifiedPolynomials": [
                        {
                            "polynomialIndex": 0,
                            "status": "accepted",
                            "label": "24T25000",
                            "t": 25000,
                            "r": 8,
                            "scoreable": True,
                            "scoringStatus": "scoreable",
                            "discSource": "exact_nfdisc",
                            "fieldDiscAbs": "123",
                            "inBaseline": False,
                            "baselineUnlocked": False,
                        }
                    ],
                    "failedPolynomials": [],
                    "payload": {"queuedPolynomials": []},
                }
            }
        ),
        encoding="utf-8",
    )

    feedback = build_feedback(
        status_response_path=status_path,
        selected_jsonl_path=selected_path,
        output_json_path=tmp_path / "feedback.json",
    )

    row = feedback["accepted_rows"][0]
    assert row["canonical_hash"] == "hash-wrapper"
    assert row["submission_line"] == "2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1"
    assert row["anti_basin_score"] == 118.5
    assert row["perturbation_mode"] == "sparse_odd_single_e11_support_gcd1"
    assert row["template_family_id"] == "model:sparse:r8:sparse_mixed_support_gcd1"
    assert row["disc_source"] == "exact_nfdisc"


def test_update_pair_status_enriches_existing_alternate_metadata(tmp_path):
    feedback = {
        "accepted_rows": [
            {
                "pair_key": "24T25000|r=8",
                "label": "24T25000",
                "r": 8,
                "canonical_hash": "known-alt",
                "short_hash": "known-alt",
                "row_number": 1,
                "family_key": "four_positive_fibers_e:odd_pair_off_core:11:1,13:-1",
                "template_family_id": "r8_score_followup:four_positive_fibers_e:odd_pair_off_core",
                "basin_fingerprint": "basin-score-followup-a",
                "perturbation_mode": "odd_pair_off_core",
                "scoring_status": "pending",
            }
        ]
    }

    pair_status, update = update_pair_status(
        {
            "record_type": "igp24_pair_status_ledger",
            "pairs": [
                {
                    "pair_key": "24T25000|r=8",
                    "canonical_hash": "primary",
                    "accepted_alternates": [{"canonical_hash": "known-alt"}],
                }
            ],
        },
        feedback,
        feedback_path=tmp_path / "feedback.json",
    )

    alternate = pair_status["pairs"][0]["accepted_alternates"][0]
    assert update["already_present"] == 1
    assert update["alternates_added"] == 0
    assert update["metadata_updates"] == 4
    assert update["pair_status_updated"] is True
    assert alternate["template_family_id"] == "r8_score_followup:four_positive_fibers_e:odd_pair_off_core"
    assert alternate["basin_fingerprint"] == "basin-score-followup-a"
