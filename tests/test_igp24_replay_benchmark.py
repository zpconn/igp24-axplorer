import json

from scripts.igp24_replay_benchmark import (
    aggregate_cases,
    evaluate_case,
    load_score_plan,
    write_outputs,
)


def _score_plan(tmp_path):
    path = tmp_path / "score_plan.json"
    path.write_text(
        json.dumps(
            {
                "record_type": "igp24_score_aware_target_plan",
                "ranked_targets": [
                    {
                        "pair_key": "24T1|r=24",
                        "label": "24T1",
                        "r": 24,
                        "category": "uncovered_signature",
                        "progress_state": "remaining",
                        "maximum_possible_points": 1.0,
                        "estimated_expected_points": 1.0,
                        "score_ceiling_class": "uncovered_first_team_one_point",
                    },
                    {
                        "pair_key": "24T25000|r=24",
                        "label": "24T25000",
                        "r": 24,
                        "category": "covered_or_crowded",
                        "progress_state": "discovered",
                        "maximum_possible_points": 0.0,
                        "estimated_expected_points": 0.0,
                        "score_ceiling_class": "crowded_near_zero_ceiling",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _coefficients(value):
    return [value, 1] + [0] * 22 + [1]


def _write_selected(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _selected_without_pair(hash_value):
    return {
        "canonical_hash": hash_value,
        "short_hash": hash_value[:12],
        "eligible_for_packet": True,
        "score": 150.0,
        "features": {
            "canonical_hash": hash_value,
            "short_hash": hash_value[:12],
            "r": 24,
            "construction_family": "old_family",
            "template_family_id": "old_family:mode",
            "perturbation_mode": "mode",
            "basin_fingerprint": hash_value,
            "mod_p_pattern_signature": f"p3:{hash_value[:4]}",
        },
        "exported_coefficients": _coefficients(3),
    }


def _selected_with_uncovered_pair(hash_value):
    row = _selected_without_pair(hash_value)
    row["group_compatibility"] = {
        "compatible_label_count": 1,
        "compatible_uncovered_pairs": ["24T1|r=24"],
        "compatible_low_team_pairs": [],
        "compatible_crowded_pairs": [],
        "crowded_only": False,
        "evidence": {"primes": list(range(101, 111))},
    }
    return row


def _feedback(path, selected_path, *, submission_id, label, pair, row_count=3):
    rows = []
    for index in range(row_count):
        rows.append(
            {
                "row_number": index + 1,
                "canonical_hash": f"h{index}",
                "short_hash": f"h{index}",
                "label": label,
                "r": int(pair.split("|r=", 1)[1]),
                "pair_key": pair,
                "status": "accepted",
                "scoreable": True,
                "scoring_status": "scoreable",
            }
        )
    path.write_text(
        json.dumps(
            {
                "record_type": "igp24_sair_accepted_label_feedback",
                "submission_id": submission_id,
                "submitted_at": "2026-07-09T00:00:00Z",
                "source_selected_jsonl": str(selected_path),
                "accepted_rows": rows,
            }
        ),
        encoding="utf-8",
    )


def _feedback_rows(path, selected_path, *, submission_id, rows):
    path.write_text(
        json.dumps(
            {
                "record_type": "igp24_sair_accepted_label_feedback",
                "submission_id": submission_id,
                "submitted_at": "2026-07-09T00:00:00Z",
                "source_selected_jsonl": str(selected_path),
                "accepted_rows": rows,
            }
        ),
        encoding="utf-8",
    )


def test_replay_benchmark_stops_historical_crowded_collapse(tmp_path):
    selected_path = tmp_path / "old_selected.jsonl"
    _write_selected(
        selected_path,
        [_selected_without_pair("a" * 64), _selected_without_pair("b" * 64), _selected_without_pair("c" * 64)],
    )
    feedback_path = tmp_path / "feedback.json"
    _feedback(
        feedback_path,
        selected_path,
        submission_id="sub_collapse",
        label="24T25000",
        pair="24T25000|r=24",
        row_count=3,
    )

    case = evaluate_case(
        feedback_path,
        score_plan=load_score_plan(_score_plan(tmp_path)),
        crowded_labels={"24T25000"},
        low_team_threshold=0.001,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    assert case["major_crowded_collapse_batch"] is True
    assert case["old_pipeline"]["crowded_collapse_rate"] == 1.0
    assert case["old_pipeline"]["duplicated_pair_rate"] == 0.666667
    assert case["remediated_replay"]["optimizer_rejected_all"] is True
    assert case["remediated_replay"]["source_candidate_metrics"]["unique_decode_rate"] == 1.0
    assert case["remediated_replay"]["source_candidate_metrics"]["compatibility_evidence_row_count"] == 0
    assert case["remediated_replay"]["optimizer_reject_reason_counts"] == {
        "missing_pair_or_compatibility_evidence": 3
    }
    assert case["remediated_stops_or_downranks"] is True


def test_replay_benchmark_keeps_rows_with_uncovered_pair_evidence(tmp_path):
    selected_path = tmp_path / "valuable_selected.jsonl"
    _write_selected(selected_path, [_selected_with_uncovered_pair("d" * 64)])
    feedback_path = tmp_path / "valuable_feedback.json"
    _feedback(
        feedback_path,
        selected_path,
        submission_id="sub_value",
        label="24T1",
        pair="24T1|r=24",
        row_count=1,
    )

    case = evaluate_case(
        feedback_path,
        score_plan=load_score_plan(_score_plan(tmp_path)),
        crowded_labels={"24T25000"},
        low_team_threshold=0.001,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    assert case["major_crowded_collapse_batch"] is False
    assert case["old_pipeline"]["low_team_pair_yield"] == 1
    assert case["remediated_replay"]["optimizer_selected_rows"] == 1
    assert case["remediated_replay"]["optimizer_selected_possible_uncovered_pair_count"] == 1
    assert case["remediated_replay"]["source_candidate_metrics"]["valuable_survival_row_count"] == 1


def test_replay_benchmark_reports_true_label_containment_when_hashes_join(tmp_path):
    selected_path = tmp_path / "contained_selected.jsonl"
    row = _selected_with_uncovered_pair("d" * 64)
    row["group_compatibility"]["indexed_target_labels_not_ruled_out"] = ["24T1", "24T7"]
    _write_selected(selected_path, [row])
    feedback_path = tmp_path / "contained_feedback.json"
    _feedback_rows(
        feedback_path,
        selected_path,
        submission_id="sub_contained",
        rows=[
            {
                "row_number": 1,
                "canonical_hash": "d" * 64,
                "short_hash": "d" * 12,
                "label": "24T1",
                "r": 24,
                "pair_key": "24T1|r=24",
                "status": "accepted",
                "scoreable": True,
                "scoring_status": "scoreable",
            }
        ],
    )

    case = evaluate_case(
        feedback_path,
        score_plan=load_score_plan(_score_plan(tmp_path)),
        crowded_labels={"24T25000"},
        low_team_threshold=0.001,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    metrics = case["remediated_replay"]["source_candidate_metrics"]
    assert metrics["true_label_containment_evaluated_count"] == 1
    assert metrics["true_label_containment_success_count"] == 1
    assert metrics["true_label_containment_rate"] == 1.0
    assert metrics["true_label_containment_missing_evidence_count"] == 0


def test_replay_benchmark_reports_containment_missing_when_no_compatibility_evidence(tmp_path):
    selected_path = tmp_path / "missing_evidence_selected.jsonl"
    _write_selected(selected_path, [_selected_without_pair("e" * 64)])
    feedback_path = tmp_path / "missing_evidence_feedback.json"
    _feedback_rows(
        feedback_path,
        selected_path,
        submission_id="sub_missing_evidence",
        rows=[
            {
                "row_number": 1,
                "canonical_hash": "e" * 64,
                "label": "24T25000",
                "r": 24,
                "pair_key": "24T25000|r=24",
                "status": "accepted",
                "scoreable": True,
            }
        ],
    )

    case = evaluate_case(
        feedback_path,
        score_plan=load_score_plan(_score_plan(tmp_path)),
        crowded_labels={"24T25000"},
        low_team_threshold=0.001,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    metrics = case["remediated_replay"]["source_candidate_metrics"]
    assert metrics["true_label_containment_evaluated_count"] == 0
    assert metrics["true_label_containment_rate"] is None
    assert metrics["true_label_containment_missing_evidence_count"] == 1


def test_replay_benchmark_writes_summary_report_and_cases(tmp_path):
    selected_path = tmp_path / "old_selected.jsonl"
    _write_selected(selected_path, [_selected_without_pair("a" * 64)] * 3)
    feedback_path = tmp_path / "feedback.json"
    _feedback(
        feedback_path,
        selected_path,
        submission_id="sub_collapse",
        label="24T25000",
        pair="24T25000|r=24",
        row_count=3,
    )
    case = evaluate_case(
        feedback_path,
        score_plan=load_score_plan(_score_plan(tmp_path)),
        crowded_labels={"24T25000"},
        low_team_threshold=0.001,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )
    summary = aggregate_cases(
        [case],
        caps={"construction_family": 10},
        feedback_paths=[feedback_path],
    )
    paths = write_outputs(tmp_path / "out", summary)

    saved = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    assert saved["phase7_minimum_gate_passed"] is True
    assert saved["remediated_totals"]["major_collapse_cases_stopped_or_downranked"] == 1
    assert "true_label_containment_missing_evidence_count" in saved["remediated_totals"]
    assert len(paths["cases_jsonl"].read_text(encoding="utf-8").splitlines()) == 1
    assert "Chronological Replay Benchmark" in paths["report_md"].read_text(encoding="utf-8")


def test_replay_benchmark_falls_back_to_sibling_selected_packet(tmp_path):
    selected_path = tmp_path / "selected_review_packet.jsonl"
    _write_selected(selected_path, [_selected_without_pair("a" * 64)])
    feedback_path = tmp_path / "feedback_without_source.json"
    feedback_path.write_text(
        json.dumps(
            {
                "record_type": "igp24_sair_accepted_label_feedback",
                "submission_id": "sub_missing_source",
                "submitted_at": "2026-07-09T00:00:00Z",
                "accepted_rows": [
                    {
                        "row_number": 1,
                        "label": "24T25000",
                        "r": 24,
                        "pair_key": "24T25000|r=24",
                        "status": "accepted",
                        "scoreable": True,
                    }
                ]
                * 3,
            }
        ),
        encoding="utf-8",
    )

    case = evaluate_case(
        feedback_path,
        score_plan=load_score_plan(_score_plan(tmp_path)),
        crowded_labels={"24T25000"},
        low_team_threshold=0.001,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    assert case["remediated_replay"]["source_available"] is True
    assert case["remediated_replay"]["source_candidate_count"] == 1
    assert case["remediated_replay"]["optimizer_rejected_all"] is True
