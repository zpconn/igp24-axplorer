import json

from scripts.igp24_axg_proposal_loop import exact_filter_row, run_proposal_loop
from scripts.igp24_model_registry import create_version


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _candidate(index):
    return {
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
