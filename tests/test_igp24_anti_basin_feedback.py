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
    assert pairs["24T24932|r=12"]["anti_basin_score"] == 99.0
