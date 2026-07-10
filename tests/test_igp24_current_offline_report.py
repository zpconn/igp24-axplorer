import json

from scripts.igp24_current_offline_report import build_summary, render_report


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_current_offline_report_blocks_missing_exact_labels(tmp_path):
    packet = tmp_path / "packet.json"
    triage = tmp_path / "triage.json"
    triage_rows = tmp_path / "triage.jsonl"
    adaptive = tmp_path / "adaptive.json"
    index = tmp_path / "index.json"
    historical = tmp_path / "historical.json"
    replay = tmp_path / "replay.json"
    gpu = tmp_path / "gpu.json"
    baseline = tmp_path / "baseline.json"

    _write_json(
        packet,
        {
            "selected_rows": 2,
            "candidate_count": 4,
            "best_case_packet_points": 2.0,
            "expected_points_status": "unavailable_uncalibrated",
            "expected_points_basis": "unavailable",
            "selected_possible_uncovered_pair_count": 3,
            "selected_possible_low_team_pair_count": 5,
            "selected_diversity": {"construction_family": {"quartic_in_x6": 2}},
            "live_submission_recommended_now": False,
        },
    )
    _write_json(
        triage,
        {
            "reviewed_rows": 2,
            "verified_rows": 0,
            "pending_exact_label_rows": 2,
            "known_submission_hash_rows": 0,
            "submission_grade_rows": 0,
            "exact_label_status_counts": {"missing": 2},
            "exact_r_status_counts": {"ok": 2},
            "exact_nfdisc_status_counts": {"ok": 1, "missing": 1},
        },
    )
    _write_jsonl(
        triage_rows,
        [
            {
                "canonical_hash": "a" * 64,
                "short_hash": "a" * 12,
                "computed_r": 8,
                "exact_label_status": "missing",
                "exact_nfdisc_status": "ok",
                "known_submission_hash_match": False,
                "score_aware_classification": "exact_result_missing",
                "submission_grade_candidate": False,
            },
            {
                "canonical_hash": "b" * 64,
                "short_hash": "b" * 12,
                "computed_r": 8,
                "exact_label_status": "missing",
                "exact_nfdisc_status": "missing",
                "known_submission_hash_match": False,
                "score_aware_classification": "exact_result_missing",
                "submission_grade_candidate": False,
            },
        ],
    )
    _write_json(
        adaptive,
        {
            "max_usable_primes": 80,
            "evaluated_row_count": 2,
            "failed_row_count": 0,
            "exact_label_missing_row_count": 2,
            "intended_target_survival_rows": 2,
            "intended_target_row_count": 2,
            "intended_target_failure_rows": 0,
            "final_valuable_target_survival_rows": 2,
            "budget_summary": {"80": {"median_indexed_target_survivor_count": 10}},
        },
    )
    _write_json(
        index,
        {
            "global_index_complete": True,
            "group_count": 25000,
            "expected_global_group_count": 25000,
            "integrity": {"integrity_ok": True},
        },
    )
    _write_json(historical, {"evaluated_row_count": 10, "indexed_true_label_containment_failures": 0})
    _write_json(replay, {"phase7_minimum_gate_passed": True})
    _write_json(gpu, {"run_id": "probe", "training_and_sampling": {"gpu_used": True}, "cpu_proxy_scoring": {"valid_records": 0}})
    _write_json(baseline, {"leaderboard": {"our_public_score": 0.1}})

    summary, rows = build_summary(
        packet_summary_path=packet,
        triage_summary_path=triage,
        triage_rows_path=triage_rows,
        adaptive_summary_path=adaptive,
        index_summary_path=index,
        historical_summary_path=historical,
        baseline_summary_path=baseline,
        replay_summary_path=replay,
        gpu_summary_path=gpu,
        output_dir=tmp_path / "out",
        command=["python3", "scripts/igp24_current_offline_report.py"],
    )

    assert len(rows) == 2
    assert summary["candidate_status"]["novel_candidate_count_against_synced_submission_history"] == 2
    assert summary["go_no_go"]["live_submission_recommended_now"] is False
    assert "exact_magma_labels_missing" in summary["go_no_go"]["blockers"]
    assert "exact_nfdisc_not_complete" in summary["go_no_go"]["blockers"]
    assert "score_aware_triage_has_no_submission_grade_rows" in summary["go_no_go"]["blockers"]
    assert "packet_uses_single_construction_family" in summary["go_no_go"]["warnings"]

    report = render_report(summary)
    assert "Live submission recommended now: `False`" in report
    assert "Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only" in report


def test_known_submission_hash_is_not_novel(tmp_path):
    packet = tmp_path / "packet.json"
    triage = tmp_path / "triage.json"
    triage_rows = tmp_path / "triage.jsonl"
    adaptive = tmp_path / "adaptive.json"
    index = tmp_path / "index.json"
    historical = tmp_path / "historical.json"

    _write_json(packet, {"selected_rows": 1, "candidate_count": 1, "expected_points_status": "unavailable_uncalibrated"})
    _write_json(
        triage,
        {
            "reviewed_rows": 1,
            "verified_rows": 1,
            "known_submission_hash_rows": 1,
            "submission_grade_rows": 0,
            "exact_r_status_counts": {"ok": 1},
            "exact_nfdisc_status_counts": {"ok": 1},
        },
    )
    _write_jsonl(
        triage_rows,
        [
            {
                "canonical_hash": "c" * 64,
                "known_submission_hash_match": True,
                "submission_grade_candidate": False,
            }
        ],
    )
    _write_json(
        adaptive,
        {
            "evaluated_row_count": 1,
            "failed_row_count": 0,
            "exact_label_missing_row_count": 0,
            "intended_target_failure_rows": 0,
            "final_valuable_target_survival_rows": 1,
        },
    )
    _write_json(
        index,
        {
            "global_index_complete": True,
            "group_count": 25000,
            "expected_global_group_count": 25000,
            "integrity": {"integrity_ok": True},
        },
    )
    _write_json(historical, {"evaluated_row_count": 1, "indexed_true_label_containment_failures": 0})

    summary, _rows = build_summary(
        packet_summary_path=packet,
        triage_summary_path=triage,
        triage_rows_path=triage_rows,
        adaptive_summary_path=adaptive,
        index_summary_path=index,
        historical_summary_path=historical,
        baseline_summary_path=None,
        replay_summary_path=None,
        gpu_summary_path=None,
        output_dir=tmp_path / "out",
        command=[],
    )

    assert summary["candidate_status"]["novel_candidate_count_against_synced_submission_history"] == 0
    assert "known_submission_hash_present" in summary["go_no_go"]["blockers"]


def test_current_offline_report_supersedes_adaptive_missing_label_when_triage_verified(tmp_path):
    packet = tmp_path / "packet.json"
    triage = tmp_path / "triage.json"
    triage_rows = tmp_path / "triage.jsonl"
    adaptive = tmp_path / "adaptive.json"
    index = tmp_path / "index.json"
    historical = tmp_path / "historical.json"

    _write_json(packet, {"selected_rows": 1, "candidate_count": 1, "expected_points_status": "unavailable_uncalibrated"})
    _write_json(
        triage,
        {
            "reviewed_rows": 1,
            "verified_rows": 1,
            "known_submission_hash_rows": 0,
            "submission_grade_rows": 0,
            "exact_r_status_counts": {"ok": 1},
            "exact_nfdisc_status_counts": {"ok": 1},
        },
    )
    _write_jsonl(
        triage_rows,
        [
            {
                "canonical_hash": "d" * 64,
                "verified_group_label": "24T7635",
                "computed_r": 8,
                "exact_label_status": "ok",
                "exact_nfdisc_status": "ok",
                "known_submission_hash_match": False,
                "sair_progress_state": "allowed_discovered",
                "sair_progress_team_count": 13,
                "score_aware_classification": "sair_discovered_pair_not_improved",
                "submission_grade_candidate": False,
            }
        ],
    )
    _write_json(
        adaptive,
        {
            "evaluated_row_count": 1,
            "failed_row_count": 0,
            "exact_label_missing_row_count": 1,
            "intended_target_failure_rows": 0,
            "final_valuable_target_survival_rows": 1,
        },
    )
    _write_json(
        index,
        {
            "global_index_complete": True,
            "group_count": 25000,
            "expected_global_group_count": 25000,
            "integrity": {"integrity_ok": True},
        },
    )
    _write_json(historical, {"evaluated_row_count": 1, "indexed_true_label_containment_failures": 0})

    summary, _rows = build_summary(
        packet_summary_path=packet,
        triage_summary_path=triage,
        triage_rows_path=triage_rows,
        adaptive_summary_path=adaptive,
        index_summary_path=index,
        historical_summary_path=historical,
        baseline_summary_path=None,
        replay_summary_path=None,
        gpu_summary_path=None,
        output_dir=tmp_path / "out",
        command=[],
    )

    assert "adaptive_rows_still_missing_exact_labels" not in summary["go_no_go"]["blockers"]
    assert "exact_magma_labels_missing" not in summary["go_no_go"]["blockers"]
    assert "adaptive_exact_label_missing_field_superseded_by_score_aware_triage" in summary["go_no_go"]["warnings"]
