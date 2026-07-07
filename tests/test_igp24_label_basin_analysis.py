import json

from scripts.igp24_label_basin_analysis import (
    build_summary,
    load_observations,
    support_summary,
    write_outputs,
)


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_support_summary_handles_missing_coefficients():
    summary = support_summary(None)

    assert summary["support_exponents"] == []
    assert summary["support_gcd"] is None
    assert summary["even_support"] is None
    assert summary["odd_support_exponents"] == []


def test_label_basin_analysis_joins_queues_and_derives_constraints(tmp_path):
    feedback_path = tmp_path / "r24_tower_probe_sair_accepted_feedback_20260707.json"
    queue_path = tmp_path / "r24_tower_candidate_queue.jsonl"

    even_tower_coefficients = [
        2,
        0,
        -3,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        -1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        2,
        0,
        -3,
        0,
        1,
    ]
    mixed_generic_coefficients = [
        3,
        1,
        0,
        0,
        -1,
        0,
        2,
        0,
        0,
        0,
        0,
        0,
        -4,
        0,
        0,
        0,
        0,
        0,
        -2,
        0,
        0,
        0,
        -1,
        0,
        1,
    ]

    feedback = {
        "record_type": "igp24_sair_accepted_label_feedback",
        "accepted_rows": [
            {
                "row_number": 1,
                "status": "accepted",
                "label": "24T24651",
                "r": 24,
                "canonical_hash": "hash-tower",
            },
            {
                "row_number": 2,
                "status": "accepted",
                "label": "24T25000",
                "r": 16,
                "canonical_hash": "hash-generic",
            },
        ],
    }
    _write_json(feedback_path, feedback)

    queue_rows = [
        {
            "canonical_hash": "hash-tower",
            "exported_coefficients": even_tower_coefficients,
            "coefficient_height": 443384,
            "real_root_count": 24,
            "irreducible": True,
            "squarefree": True,
            "mod_p_factorization_degree_patterns": [
                {"prime": 5, "degrees": [4, 4, 4, 4, 4, 4]},
                {"prime": 7, "degrees": [6, 6, 6, 6]},
            ],
            "generation_metadata": {
                "construction_family": "r24_tower_probe",
                "decomposition_degree_pattern": "6x4",
                "r24_tower_mode": "outer_constant_shift",
                "r24_tower_inner_parameter_s": 6,
                "r24_tower_outer_perturbations": [{"outer_y_exponent": 0, "delta": 2}],
                "r24_tower_family_key": "tower:s6:roots",
            },
        },
        {
            "canonical_hash": "hash-generic",
            "exported_coefficients": mixed_generic_coefficients,
            "coefficient_height": 703,
            "real_root_count": 16,
            "irreducible": True,
            "squarefree": True,
            "generation_metadata": {
                "construction_family": "r16_diversity_probe",
                "decomposition_degree_pattern": "quadratic-product",
                "r16_diversity_mode": "odd_y_perturbation",
                "r16_diversity_family_key": "generic:r16",
            },
        },
    ]
    queue_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in queue_rows) + "\n",
        encoding="utf-8",
    )

    observations = load_observations([feedback_path], [queue_path])
    assert len(observations) == 2
    tower = next(row for row in observations if row["label"] == "24T24651")
    assert tower["queue_joined"] is True
    assert tower["support_gcd"] == 2
    assert tower["even_support"] is True
    assert tower["mod_p_pattern_signature"] == "p5:4-4-4-4-4-4;p7:6-6-6-6"

    summary = build_summary(
        observations,
        pair_status={"record_type": "igp24_pair_status_ledger", "pairs": []},
        target_plan={"remaining_signature_count": 52335, "top_remaining_rs": [24, 16]},
        progress_by_label={
            "24T24651": {
                "label": "24T24651",
                "teamCount": 10,
                "allowedR": [24],
                "discoveredSignatures": [24],
                "remainingSignatures": [],
            },
            "24T25000": {
                "label": "24T25000",
                "teamCount": 80,
                "allowedR": [16, 24],
                "discoveredSignatures": [16],
                "remainingSignatures": [24],
            },
        },
        feedback_paths=[feedback_path],
        queue_paths=[queue_path],
    )

    assert summary["observation_count"] == 2
    assert summary["label_summary"]["24T24651"]["global_progress"]["fully_covered"] is True
    assert summary["pair_summary"]["24T24651|r=24"]["global_pair_discovered"] is True
    constraint_names = {item["name"] for item in summary["anti_basin_constraints"]}
    assert "stop_exact_even_6x4_constant_shift_towers" in constraint_names
    assert "avoid_generic_24T25000_perturbation_lanes" in constraint_names
    assert summary["next_lane_decision"]["gpu_training_recommended_now"] is False

    paths = write_outputs(observations=observations, summary=summary, output_dir=tmp_path / "out")
    reloaded = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    assert reloaded["record_type"] == "igp24_label_basin_analysis"
    assert "IGP24 Label Basin Analysis" in paths["report_md"].read_text(encoding="utf-8")
