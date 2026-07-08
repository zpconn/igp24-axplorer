import json

from scripts.igp24_axg_proposal_loop import build_source_basin_summary, exact_filter_row, run_proposal_loop
from scripts.igp24_model_registry import create_version


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _candidate(index):
    row = {
        "canonical_hash": f"candidate-{index}",
        "exported_coefficients": [1, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, -1, 16, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, 0, 1],
        "real_root_count": 8,
        "valid": True,
        "irreducible": True,
        "squarefree": True,
        "coefficient_height": 16,
        "mod_p_factorization_degree_patterns": [{"prime": 3 + index, "degrees": [1, 23]}],
        "generation_metadata": {
            "source_family": "r8_quartic_lift_perturbed",
            "r8_quartic_lift_family_key": f"r8-family-{index}",
            "r8_quartic_lift_perturbation_mode": "odd_single_off_core",
            "r8_quartic_lift_perturbation_exponents": [11],
            "r8_quartic_lift_support_gcd": 1,
            "r8_quartic_lift_even_support": False,
        },
    }
    if index % 2:
        row["generation_metadata"]["r8_quartic_lift_perturbation_mode"] = "odd_triple_off_core"
    return row


def test_exact_filter_rejects_bad_submission_shape():
    ok, reasons = exact_filter_row(
        {
            "exported_coefficients": [0] + [0] * 23 + [1],
            "real_root_count": 8,
            "irreducible": True,
            "squarefree": True,
        },
        {8},
    )

    assert ok is False
    assert "zero_constant_coefficient" in reasons


def test_proposal_loop_dry_run_holds_known_collapsed_family(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1", "none", "baseline")
    candidate_path = tmp_path / "candidate_queue.jsonl"
    _write_jsonl(candidate_path, [_candidate(index) for index in range(8)])
    feedback_path = tmp_path / "accepted_feedback.json"
    _write_json(
        feedback_path,
        {
            "accepted_rows": [
                {
                    "canonical_hash": "accepted-r8",
                    "label": "24T25000",
                    "pair_key": "24T25000|r=8",
                    "r": 8,
                    "status": "accepted",
                    "exported_coefficients": [1, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, -1, 16, 0, 0, 0, 0, 0, -8, 0, 0, 0, 0, 0, 1],
                    "construction_family": "r8_quartic_lift_perturbed",
                    "decomposition_pattern": "quartic_in_x6",
                    "perturbation_mode": "odd_pair_off_core",
                    "support_gcd": 1,
                    "even_support": False,
                    "family_key": "accepted-r8-family",
                    "mod_p_pattern_signature": "p3:1-23",
                }
            ]
        },
    )
    sync_dir = tmp_path / "sync"
    _write_jsonl(
        sync_dir / "sair_label_progress.jsonl",
        [
            {
                "label": "24T25000",
                "t": 25000,
                "teamCount": 50,
                "allowedR": [8],
                "discoveredSignatures": [8],
                "remainingSignatures": [],
                "signatures": [{"r": 8, "teamCount": 50, "discovered": True}],
            }
        ],
    )

    summary = run_proposal_loop(
        version="AXG-1",
        registry=registry,
        run_id="run_20260707_000000",
        candidate_paths=[candidate_path],
        feedback_paths=[feedback_path],
        sync_dir=sync_dir,
        output_dir=tmp_path / "proposal_runs",
        target_rs={8},
        collapsed_labels={"24T25000"},
        packet_limit=8,
        min_packet_rows=8,
        per_mode_cap=8,
        per_pattern_cap=8,
        crowded_team_threshold=20,
        dry_run=True,
    )

    assert summary["candidate_rows"] == 8
    assert summary["filtered_rows"] == 8
    assert summary["selected_rows"] == 0
    assert summary["decision"] == "hold_no_submission"
    assert summary["safety"]["calls_sair_post"] is False
    assert summary["safety"]["auto_submits"] is False
    run_manifest = json.loads((tmp_path / "proposal_runs" / "run_20260707_000000" / "run_manifest.json").read_text())
    assert run_manifest["safety"]["auto_submits"] is False


def test_proposal_loop_reports_seed_bank_only_when_no_model_generated_survivors(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1.1", "none", "seeded")
    candidate_path = tmp_path / "seed_bank_scored.jsonl"
    seed_rows = []
    for index in range(4):
        row = _candidate(index)
        row["canonical_hash"] = "accepted-r8"
        row["source_sample_export"] = {"sample_export_source": "target_r_seed_bank"}
        row["generation_metadata"]["target_r_conditioning_mode"] = "seed_bank_prefix"
        seed_rows.append(row)
    _write_jsonl(candidate_path, seed_rows)
    feedback_path = tmp_path / "accepted_feedback.json"
    _write_json(
        feedback_path,
        {
            "accepted_rows": [
                {
                    "canonical_hash": "accepted-r8",
                    "label": "24T25000",
                    "pair_key": "24T25000|r=8",
                    "r": 8,
                    "status": "accepted",
                    "exported_coefficients": seed_rows[0]["exported_coefficients"],
                    "construction_family": "r8_quartic_lift_perturbed",
                    "decomposition_pattern": "quartic_in_x6",
                    "perturbation_mode": "odd_single_off_core",
                    "support_gcd": 1,
                    "even_support": False,
                    "family_key": "accepted-r8-family",
                    "mod_p_pattern_signature": "p3:1-23",
                }
            ]
        },
    )

    summary = run_proposal_loop(
        version="AXG-1.1",
        registry=registry,
        run_id="seed_bank_only",
        candidate_paths=[candidate_path],
        feedback_paths=[feedback_path],
        sync_dir=None,
        output_dir=tmp_path / "proposal_runs",
        target_rs={8},
        collapsed_labels={"24T25000"},
        packet_limit=4,
        min_packet_rows=4,
        per_mode_cap=4,
        per_pattern_cap=4,
        crowded_team_threshold=20,
        dry_run=True,
    )

    assert summary["candidate_rows"] == 4
    assert summary["filtered_rows"] == 4
    assert summary["selected_rows"] == 0
    assert summary["decision"] == "hold_no_submission"
    assert summary["candidate_sample_export_source_counts"] == {"target_r_seed_bank": 4}
    assert summary["filtered_sample_export_source_counts"] == {"target_r_seed_bank": 4}
    assert summary["selected_sample_export_source_counts"] == {}
    assert summary["source_basin_summary"]["model_generated_target_r_survivor_rows"] == 0
    assert summary["source_basin_summary"]["seed_bank_target_r_survivor_rows"] == 4
    assert summary["recommendation"]["model_generated_selected_rows"] == 0
    assert "model_generate" not in summary["filtered_sample_export_source_counts"]


def test_source_basin_summary_separates_model_generate_risks():
    clean = _candidate(0)
    clean["sample_export_source"] = "model_generate"
    risky = _candidate(1)
    risky["sample_export_source"] = "model_generate"
    score_rows = [
        {
            "candidate": clean,
            "eligible_for_packet": True,
            "anti_basin_classification": "strong_packet_candidate",
            "risk_reasons": [],
        },
        {
            "candidate": risky,
            "eligible_for_packet": False,
            "anti_basin_classification": "reject_or_hold_known_basin_risk",
            "risk_reasons": ["accepted_hash_duplicate"],
        },
    ]

    summary = build_source_basin_summary(
        candidates=[clean, risky],
        filtered_rows=[clean, risky],
        scores=score_rows,
        selected=[score_rows[0]],
    )

    assert summary["model_generated_target_r_survivor_rows"] == 2
    assert summary["model_generated_eligible_rows"] == 1
    assert summary["model_generated_selected_rows"] == 1
    assert summary["risk_reason_counts_by_source"]["model_generate"] == {"accepted_hash_duplicate": 1}


def test_proposal_loop_can_recommend_clean_model_generated_packet(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1.3", "none", "diversity")
    candidate_path = tmp_path / "clean_model_generated.jsonl"
    rows = []
    for index in range(4):
        row = _candidate(index)
        row["sample_export_source"] = "model_generate"
        rows.append(row)
    _write_jsonl(candidate_path, rows)

    summary = run_proposal_loop(
        version="AXG-1.3",
        registry=registry,
        run_id="clean_model",
        candidate_paths=[candidate_path],
        feedback_paths=[],
        sync_dir=None,
        output_dir=tmp_path / "proposal_runs",
        target_rs={8},
        collapsed_labels=set(),
        packet_limit=4,
        min_packet_rows=4,
        min_model_generated_rows=4,
        per_mode_cap=4,
        per_pattern_cap=4,
        crowded_team_threshold=20,
        dry_run=True,
    )

    assert summary["selected_rows"] == 4
    assert summary["decision"] == "reviewed_packet_ready_for_dry_run"
    assert summary["recommendation"]["model_generated_selected_rows"] == 4
    assert summary["source_basin_summary"]["model_generated_target_r_survivor_rows"] == 4
    assert summary["source_basin_summary"]["selected_rows_by_source"] == {"model_generate": 4}


def test_proposal_loop_reports_axg14_provenance_diversity_gates(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1", "none", "baseline")
    create_version(registry, "AXG-1.1", "AXG-1", "seeded")
    create_version(registry, "AXG-1.2", "AXG-1.1", "conditioned")
    create_version(registry, "AXG-1.3", "AXG-1.2", "diversity")
    create_version(registry, "AXG-1.4", "AXG-1.3", "provenance")
    candidate_path = tmp_path / "model_generated_axg14.jsonl"
    rows = []
    for index in range(4):
        row = _candidate(index)
        row["sample_export_source"] = "model_generate"
        row["generation_metadata"].update(
            {
                "construction_family": "model_sample_export",
                "template_family_id": "model:mixed:r8:sparse_mixed_support_gcd1",
                "family_key": f"model:mixed:r8:sparse_mixed_support_gcd1:basin-{index}",
                "perturbation_mode": "sparse_mixed_support_gcd1" if index % 2 else "medium_mixed_support_gcd1",
                "support_pattern": "sparse_mixed_support_gcd1",
                "support_gcd": 1,
                "even_support_like": False,
                "basin_fingerprint": f"basin-{index}",
                "source_seed_hash": f"seed-{index}",
            }
        )
        rows.append(row)
    _write_jsonl(candidate_path, rows)

    summary = run_proposal_loop(
        version="AXG-1.4",
        registry=registry,
        run_id="axg14_provenance",
        candidate_paths=[candidate_path],
        feedback_paths=[],
        sync_dir=None,
        output_dir=tmp_path / "proposal_runs",
        target_rs={8},
        collapsed_labels=set(),
        packet_limit=4,
        min_packet_rows=4,
        min_model_generated_rows=4,
        min_template_family_count=2,
        min_basin_fingerprint_count=4,
        reject_unknown_provenance=True,
        per_mode_cap=4,
        per_pattern_cap=4,
        crowded_team_threshold=20,
        dry_run=True,
    )

    assert summary["decision"] == "hold_no_submission"
    assert "template_family" in summary["recommendation"]["reason"]
    assert summary["diversity_gates"]["min_template_family_count"] == 2
    assert summary["source_basin_summary"]["basin_fingerprint_counts_by_source"]["model_generate"] == {
        "basin-0": 1,
        "basin-1": 1,
        "basin-2": 1,
        "basin-3": 1,
    }
