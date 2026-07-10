import json

from scripts.igp24_score_aware_triage import (
    build_summary,
    build_triage_rows,
    load_baseline_pairs,
    load_known_submission_rows,
    load_pair_status,
    load_sair_label_feedback,
    load_sair_progress_rows,
    write_outputs,
)


def _queue_row(candidate_hash="abc123", coeff0=1):
    return {
        "canonical_hash": candidate_hash,
        "short_hash": candidate_hash[:12],
        "source_strategy": "quartic_lift",
        "score": 10.0,
        "non_generic_score": 5.0,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
    }


def _empty_evidence():
    return {
        "sair_label_feedback": {},
        "online_magma": {},
        "local_magma": {},
        "pari_nfdisc": {},
        "sympy_nfdisc": {},
        "sympy_signature": {},
    }


def _evidence_for(candidate_hash, *, label=None, r=4, nfdisc=100, degree=24, irreducible=True):
    evidence = _empty_evidence()
    if label is not None:
        evidence["online_magma"][candidate_hash] = {
            "candidate_hash": candidate_hash,
            "status": "verified",
            "verified_group_label": label,
            "computed_r": r,
            "signature_r": r,
            "degree": degree,
            "is_irreducible": irreducible,
        }
    evidence["pari_nfdisc"][candidate_hash] = {
        "candidate_hash": candidate_hash,
        "status": "nfdisc_ok",
        "exact_nfdisc_abs": nfdisc,
        "nfdisc_source": "pari_gp_nfdisc",
        "pari_degree": degree,
        "pari_is_irreducible": irreducible,
        "pari_real_root_count": r,
    }
    evidence["sympy_signature"][candidate_hash] = {
        "candidate_hash": candidate_hash,
        "status": "signature_ok",
        "computed_r": r,
        "signature_r": r,
        "exact_r_source": "sympy_poly_count_roots",
    }
    return evidence


def test_missing_exact_label_is_not_submission_grade():
    rows = build_triage_rows(
        [_queue_row("missing_label")],
        evidence=_evidence_for("missing_label", label=None, nfdisc=123),
        baseline_pairs={},
        pair_status={},
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert rows[0]["exact_r_status"] == "ok"
    assert rows[0]["exact_nfdisc_status"] == "ok"
    assert rows[0]["exact_label_status"] == "missing"
    assert rows[0]["score_aware_classification"] == "exact_result_missing"
    assert rows[0]["submission_grade_candidate"] is False


def test_new_non_baseline_pair_is_submission_grade():
    rows = build_triage_rows(
        [_queue_row("new_pair")],
        evidence=_evidence_for("new_pair", label="24T123", nfdisc=99),
        baseline_pairs={},
        pair_status={},
        sair_progress_rows=[
            {"label": "24T123", "allowedR": [4], "signatures": [{"r": 4, "discovered": False, "teamCount": 0}]}
        ],
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert rows[0]["pair_key"] == "24T123|r=4"
    assert rows[0]["sair_progress_state"] == "allowed_remaining"
    assert rows[0]["score_aware_classification"] == "new_uncovered_pair"
    assert rows[0]["submission_grade_candidate"] is True


def test_exact_pair_without_progress_is_unknown_not_uncovered():
    rows = build_triage_rows(
        [_queue_row("unknown_progress")],
        evidence=_evidence_for("unknown_progress", label="24T123", nfdisc=99),
        baseline_pairs={},
        pair_status={},
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert rows[0]["pair_key"] == "24T123|r=4"
    assert rows[0]["sair_progress_state"] == "progress_data_missing_unknown"
    assert rows[0]["score_aware_classification"] == "progress_data_missing_unknown"
    assert rows[0]["submission_grade_candidate"] is False


def test_discovered_progress_pair_without_improvement_is_not_submission_grade():
    rows = build_triage_rows(
        [_queue_row("discovered")],
        evidence=_evidence_for("discovered", label="24T123", nfdisc=500),
        baseline_pairs={},
        pair_status={},
        sair_progress_rows=[
            {
                "label": "24T123",
                "allowedR": [4],
                "signatures": [{"r": 4, "discovered": True, "teamCount": 9, "minimumDiscAbs": "100"}],
            }
        ],
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert rows[0]["sair_progress_state"] == "allowed_discovered"
    assert rows[0]["sair_progress_team_count"] == 9
    assert rows[0]["sair_progress_minimum_disc_abs"] == 100
    assert rows[0]["sair_progress_discriminant_status"] == "sair_progress_not_improved"
    assert rows[0]["score_aware_classification"] == "sair_discovered_pair_not_improved"
    assert rows[0]["submission_grade_candidate"] is False


def test_baseline_and_generic_pairs_are_not_auto_submission_grade():
    baseline_rows = build_triage_rows(
        [_queue_row("baseline")],
        evidence=_evidence_for("baseline", label="24T1", nfdisc=99),
        baseline_pairs={"24T1|r=4": {"baseline_nfdisc_abs": 100, "baseline_scoring_disc": "nfdisc"}},
        pair_status={},
        material_ratio=0.5,
        allow_generic_submission=False,
    )
    generic_rows = build_triage_rows(
        [_queue_row("generic")],
        evidence=_evidence_for("generic", label="24T25000", nfdisc=99),
        baseline_pairs={},
        pair_status={},
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert baseline_rows[0]["score_aware_classification"] == "baseline_pair"
    assert baseline_rows[0]["submission_grade_candidate"] is False
    assert generic_rows[0]["score_aware_classification"] == "generic_24T25000"
    assert generic_rows[0]["submission_grade_candidate"] is False


def test_accepted_pair_requires_material_improvement():
    duplicate_rows = build_triage_rows(
        [_queue_row("accepted_dup")],
        evidence=_evidence_for("accepted_dup", label="24T123", nfdisc=90),
        baseline_pairs={},
        pair_status={"24T123|r=4": {"status": "accepted", "exact_nfdisc_abs": 100, "short_hash": "old"}},
        material_ratio=0.5,
        allow_generic_submission=False,
    )
    improvement_rows = build_triage_rows(
        [_queue_row("accepted_better")],
        evidence=_evidence_for("accepted_better", label="24T123", nfdisc=49),
        baseline_pairs={},
        pair_status={"24T123|r=4": {"status": "accepted", "exact_nfdisc_abs": 100, "short_hash": "old"}},
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert duplicate_rows[0]["accepted_pair_status"] == "accepted_pair_minor_discriminant_improvement"
    assert duplicate_rows[0]["score_aware_classification"] == "accepted_pair_duplicate"
    assert duplicate_rows[0]["submission_grade_candidate"] is False
    assert improvement_rows[0]["accepted_pair_status"] == "accepted_pair_material_discriminant_improvement"
    assert improvement_rows[0]["score_aware_classification"] == "accepted_pair_material_discriminant_improvement"
    assert improvement_rows[0]["submission_grade_candidate"] is True


def test_user_reported_sair_feedback_supplies_exact_label(tmp_path):
    feedback_path = tmp_path / "sair_feedback.json"
    feedback_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "canonical_hash": "sair_row",
                        "status": "accepted",
                        "label": "24T24979",
                        "r": 4,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    sair_feedback, inputs = load_sair_label_feedback([feedback_path])
    evidence = _evidence_for("sair_row", label=None, nfdisc=90)
    evidence["sair_label_feedback"] = sair_feedback

    rows = build_triage_rows(
        [_queue_row("sair_row")],
        evidence=evidence,
        baseline_pairs={},
        pair_status={"24T24979|r=4": {"status": "accepted", "exact_nfdisc_abs": 100, "short_hash": "old"}},
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert inputs[0]["accepted_label_rows"] == 1
    assert rows[0]["verified_group_label"] == "24T24979"
    assert rows[0]["exact_label_source"] == "sair_accepted_label_feedback"
    assert rows[0]["pair_key"] == "24T24979|r=4"
    assert rows[0]["accepted_pair_status"] == "accepted_pair_minor_discriminant_improvement"
    assert rows[0]["submission_grade_candidate"] is False


def test_known_submission_hash_blocks_submission_grade_and_records_metadata(tmp_path):
    known_path = tmp_path / "sair_submission_rows.jsonl"
    candidate_hash = "known_hash"
    known_path.write_text(
        json.dumps(
            {
                "canonical_hash": candidate_hash,
                "submission_id": "sub_known",
                "status": "accepted",
                "label": "24T123",
                "r": 4,
                "pair_key": "24T123|r=4",
                "scoreable": True,
                "scoring_status": "scoreable",
                "disc_source": "exact_nfdisc",
                "field_disc_abs": "12345",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    known_submissions, inputs = load_known_submission_rows([known_path])

    rows = build_triage_rows(
        [_queue_row(candidate_hash)],
        evidence=_evidence_for(candidate_hash, label="24T123", nfdisc=99),
        baseline_pairs={},
        pair_status={},
        known_submissions=known_submissions,
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    assert inputs[0]["canonical_hashes_indexed"] == 1
    assert rows[0]["known_submission_hash_match"] is True
    assert rows[0]["known_submission_id"] == "sub_known"
    assert rows[0]["known_submission_label"] == "24T123"
    assert rows[0]["known_submission_pair_key"] == "24T123|r=4"
    assert rows[0]["known_submission_scoreable"] is True
    assert rows[0]["known_submission_disc_source"] == "exact_nfdisc"
    assert rows[0]["known_submission_field_disc_abs"] == 12345
    assert rows[0]["score_aware_classification"] == "known_submission_hash"
    assert rows[0]["submission_grade_candidate"] is False


def test_loaders_and_write_outputs(tmp_path):
    baseline_path = tmp_path / "baseline.csv"
    baseline_path.write_text("label,r,poly_disc_abs,nfdisc_abs,scoring_disc,coeffs\n24T1,4,9,8,nfdisc,\"1,1\"\n", encoding="utf-8")
    pair_status_path = tmp_path / "pairs.json"
    pair_status_path.write_text(
        json.dumps({"pairs": [{"pair_key": "24T2|r=4", "status": "accepted", "exact_nfdisc_abs": 7}]}),
        encoding="utf-8",
    )
    progress_path = tmp_path / "progress.jsonl"
    progress_path.write_text(
        json.dumps({"label": "24T123", "allowedR": [4], "signatures": [{"r": 4, "discovered": False}]}) + "\n",
        encoding="utf-8",
    )
    baseline, baseline_info = load_baseline_pairs(baseline_path)
    pairs, pair_info = load_pair_status(pair_status_path)
    progress_rows, progress_inputs = load_sair_progress_rows([progress_path])
    rows = build_triage_rows(
        [_queue_row("new_pair", coeff0=5)],
        evidence=_evidence_for("new_pair", label="24T123", nfdisc=99),
        baseline_pairs=baseline,
        pair_status=pairs,
        sair_progress_rows=progress_rows,
        material_ratio=0.5,
        allow_generic_submission=False,
    )
    submission_rows = [row for row in rows if row["submission_grade_candidate"]]
    summary = build_summary(
        queue_path=tmp_path / "queue.jsonl",
        offline_dir=tmp_path / "offline",
        sair_label_feedback_inputs=[],
        known_submission_inputs=[],
        sair_progress_inputs=progress_inputs,
        baseline_info=baseline_info,
        pair_status_info=pair_info,
        triage_rows=rows,
        submission_rows=submission_rows,
        output_dir=tmp_path / "out",
        command=["python3", "scripts/igp24_score_aware_triage.py"],
        source_commit="abc123",
        material_ratio=0.5,
        allow_generic_submission=False,
    )

    paths = write_outputs(output_dir=tmp_path / "out", summary=summary, triage_rows=rows, submission_rows=submission_rows)

    assert summary["submission_grade_rows"] == 1
    assert summary["sair_progress_inputs"][0]["rows_loaded"] == 1
    assert summary["sair_progress_state_counts"] == {"allowed_remaining": 1}
    assert json.loads(paths["triage_jsonl"].read_text(encoding="utf-8").splitlines()[0])["pair_key"] == "24T123|r=4"
    assert paths["submission_coefficients_txt"].read_text(encoding="utf-8").strip().startswith("5,0,0")
    assert "Manual Verification Follow-Up" in paths["manual_checklist_md"].read_text(encoding="utf-8")
