import json

from scripts.igp24_r24_odd_escape_feedback import (
    build_feedback_artifact,
    compare_discriminants,
    update_pair_status_with_alternates,
)


def _queue_row(hash_value, *, height=100, support_gcd=1):
    return {
        "canonical_hash": hash_value,
        "coefficient_height": height,
        "real_root_count": 24,
        "irreducible": True,
        "squarefree": True,
        "exported_coefficients": [2, -1] + [0] * 22 + [1],
        "generation_metadata": {
            "construction_family": "odd_perturbed_r24_6x4_tower_escape",
            "decomposition_degree_pattern": "6x4_seed_plus_odd_x_perturbation",
            "r24_tower_odd_escape_family_key": f"family:{hash_value}",
            "r24_tower_odd_escape_support_gcd": support_gcd,
            "r24_tower_odd_escape_even_support_after_perturbation": False,
            "r24_tower_odd_escape_odd_support_exponents": [1],
            "r24_tower_odd_escape_odd_perturbations": [{"x_exponent": 1, "delta": -1}],
            "r24_tower_odd_escape_mode": "single_odd_tower_escape",
            "r24_tower_odd_escape_inner_parameter_s": 6,
            "r24_tower_odd_escape_outer_four_real_preimage_levels": [-1, -2, -3, -4, -5, -6],
            "anti_basin_features": ["breaks_exact_even_support"],
            "r24_tower_odd_escape_exact_composition_after_perturbation": False,
        },
    }


def test_build_feedback_artifact_joins_verified_response_and_compares_discriminants(tmp_path):
    response_path = tmp_path / "response.json"
    queue_path = tmp_path / "queue.jsonl"
    coeffs_path = tmp_path / "coeffs.txt"
    summary_path = tmp_path / "summary.json"
    pair_status_path = tmp_path / "pairs.json"

    response_path.write_text(
        json.dumps(
            {
                "data": {
                    "submissionId": "sub_test",
                    "createdAt": "2026-07-07T00:00:00Z",
                    "updatedAt": "2026-07-07T00:01:00Z",
                    "competitionId": "igp24",
                    "verifiedPolynomials": [
                        {
                            "polynomialIndex": 0,
                            "status": "accepted",
                            "label": "24T25000",
                            "t": 25000,
                            "r": 24,
                            "scoreable": True,
                            "scoringStatus": "scoreable",
                            "discSource": "exact_nfdisc",
                            "fieldDiscAbs": "90",
                            "inBaseline": False,
                            "baselineUnlocked": False,
                        },
                        {
                            "polynomialIndex": 1,
                            "status": "accepted",
                            "label": "24T25000",
                            "t": 25000,
                            "r": 24,
                            "scoreable": True,
                            "scoringStatus": "scoreable",
                            "discSource": "mixed_disc",
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
    queue_path.write_text(
        "\n".join(json.dumps(row) for row in [_queue_row("hash-a"), _queue_row("hash-b", height=200)])
        + "\n",
        encoding="utf-8",
    )
    coeffs_path.write_text("2,-1," + ",".join(["0"] * 22) + ",1\n3,-1," + ",".join(["0"] * 22) + ",1\n", encoding="utf-8")
    summary_path.write_text(json.dumps({"valid_r24_candidates": 9, "selected_rows": 2}), encoding="utf-8")
    pair_status_path.write_text(
        json.dumps({"pairs": [{"pair_key": "24T25000|r=24", "status": "accepted", "accepted_alternates": []}]}),
        encoding="utf-8",
    )

    feedback = build_feedback_artifact(
        response_path=response_path,
        queue_path=queue_path,
        coefficients_path=coeffs_path,
        summary_path=summary_path,
        pair_status_path=pair_status_path,
        prior_feedback_paths=[],
    )

    assert feedback["summary"]["accepted_rows"] == 2
    assert feedback["summary"]["label_counts"] == {"24T25000": 2}
    assert feedback["summary"]["exact_nfdisc_rows"] == 1
    assert feedback["summary"]["mixed_disc_rows"] == 1
    assert feedback["summary"]["all_scoreable"] is True
    assert feedback["accepted_rows"][0]["canonical_hash"] == "hash-a"
    assert feedback["accepted_rows"][0]["support_gcd"] == 1
    assert feedback["accepted_rows"][0]["even_support"] is False
    assert feedback["accepted_rows"][0]["field_disc_abs"] == 90
    assert feedback["discriminant_comparison"]["comparison_status"] == "no_prior_exact_nfdisc_available"
    assert feedback["discriminant_comparison"]["improvement_claimed"] is False


def test_compare_discriminants_detects_real_improvement():
    comparison = compare_discriminants(
        pair_status={
            "pairs": [
                {
                    "pair_key": "24T25000|r=24",
                    "status": "accepted",
                    "exact_nfdisc_abs": 100,
                    "canonical_hash": "old",
                    "short_hash": "old",
                }
            ]
        },
        pair_key="24T25000|r=24",
        new_rows=[
            {
                "row_number": 1,
                "canonical_hash": "new",
                "short_hash": "new",
                "disc_source": "exact_nfdisc",
                "field_disc_abs": 90,
            }
        ],
        prior_feedback_paths=[],
    )

    assert comparison["comparison_status"] == "new_exact_nfdisc_improves_prior_best"
    assert comparison["improvement_claimed"] is True
    assert comparison["best_new_exact_nfdisc"]["exact_nfdisc_abs"] == 90


def test_compare_discriminants_ignores_current_hashes_already_in_pair_status():
    comparison = compare_discriminants(
        pair_status={
            "pairs": [
                {
                    "pair_key": "24T25000|r=24",
                    "status": "accepted",
                    "accepted_alternates": [
                        {
                            "canonical_hash": "current",
                            "short_hash": "current",
                            "field_disc_abs": 90,
                        }
                    ],
                }
            ]
        },
        pair_key="24T25000|r=24",
        new_rows=[
            {
                "row_number": 1,
                "canonical_hash": "current",
                "short_hash": "current",
                "disc_source": "exact_nfdisc",
                "field_disc_abs": 90,
            }
        ],
        prior_feedback_paths=[],
    )

    assert comparison["prior_exact_nfdisc_count"] == 0
    assert comparison["comparison_status"] == "no_prior_exact_nfdisc_available"
    assert comparison["improvement_claimed"] is False


def test_update_pair_status_appends_alternates_without_replacing_primary(tmp_path):
    feedback_path = tmp_path / "feedback.json"
    pair_status = {
        "record_type": "igp24_pair_status_ledger",
        "pairs": [
            {
                "pair_key": "24T25000|r=24",
                "label": "24T25000",
                "r": 24,
                "canonical_hash": "primary",
                "short_hash": "primary",
                "status": "accepted",
                "accepted_alternates": [],
            }
        ],
    }
    feedback = {
        "accepted_rows": [
            {
                "canonical_hash": "alt",
                "short_hash": "alt",
                "row_number": 1,
                "family_key": "family:alt",
                "disc_source": "exact_nfdisc",
                "field_disc_abs": 90,
                "scoreable": True,
                "scoring_status": "scoreable",
                "tower_odd_escape_metadata": {"mode": "single_odd_tower_escape"},
            }
        ]
    }

    updated, summary = update_pair_status_with_alternates(pair_status, feedback, feedback_path=feedback_path)

    pair = updated["pairs"][0]
    assert summary["alternates_added"] == 1
    assert summary["primary_pair_unchanged"] is True
    assert pair["canonical_hash"] == "primary"
    assert pair["accepted_alternates"][0]["canonical_hash"] == "alt"
    assert pair["accepted_alternates"][0]["score_status"] == "scoreable"
