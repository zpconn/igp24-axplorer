import json
from pathlib import Path

from scripts.igp24_alt_8x3_sair_probe import (
    ACCEPTED_FEEDBACK_JSON,
    COEFFICIENTS_TXT,
    PACKET_JSONL,
    build_feedback,
    build_packet,
    record_submit_response,
    update_pair_status,
)


def _queue_row(rank, candidate_hash, *, height=100):
    return {
        "alt_composition_queue_rank": rank,
        "canonical_hash": candidate_hash,
        "exported_coefficients": [2, 1] + [0] * 22 + [1],
        "coefficient_height": height,
        "real_root_count": 24,
        "irreducible": True,
        "squarefree": True,
        "generation_metadata": {
            "strategy": "alt_composition_probe",
            "construction_family": "alt_composition_8x3",
            "decomposition_degree_pattern": "8x3",
            "alt_composition_family_key": f"8x3:test:{rank}",
            "alt_support_gcd": 1,
            "alt_even_support": False,
            "alt_odd_support_exponents": [1],
            "alt_perturbation_mode": "outer_constant_shift",
            "alt_outer_three_real_levels": [-3, -2, -1, 1, 2, 3, 4, 5],
            "alt_outer_perturbations": [{"outer_y_exponent": 0, "delta": 1}],
            "anti_basin_features": ["degree_pattern_not_6x4"],
        },
    }


def test_build_packet_writes_reviewed_eight_row_subset(tmp_path):
    queue_path = tmp_path / "queue.jsonl"
    summary_path = tmp_path / "summary.json"
    output_dir = tmp_path / "packet"
    rows = [_queue_row(index, f"hash-{index}") for index in range(1, 10)]
    queue_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps({"trials_attempted": 9, "valid_candidate_count": 9, "selected_rows": 9}), encoding="utf-8")

    summary = build_packet(
        source_queue_path=queue_path,
        source_summary_path=summary_path,
        output_dir=output_dir,
        limit=8,
    )

    packet_rows = [json.loads(line) for line in (output_dir / PACKET_JSONL).read_text(encoding="utf-8").splitlines()]
    coeff_lines = (output_dir / COEFFICIENTS_TXT).read_text(encoding="utf-8").splitlines()
    assert summary["selection"]["selected_rows"] == 8
    assert summary["selection"]["source_queue_ranks"] == list(range(1, 9))
    assert len(packet_rows) == 8
    assert len(coeff_lines) == 8
    assert all(len(line.split(",")) == 25 for line in coeff_lines)
    assert packet_rows[0]["structural_gates_satisfied"] == [
        "decomposition_degree_pattern_8x3",
        "not_6x4",
        "not_g_x_squared_even_support",
        "not_odd_escaped_6x4",
        "support_gcd_one",
        "exact_local_r24",
        "irreducible_squarefree_local_check",
    ]


def test_record_submit_response_updates_packet_summary(tmp_path):
    queue_path = tmp_path / "queue.jsonl"
    summary_path = tmp_path / "summary.json"
    output_dir = tmp_path / "packet"
    rows = [_queue_row(index, f"hash-{index}") for index in range(1, 9)]
    queue_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps({"trials_attempted": 8}), encoding="utf-8")
    build_packet(source_queue_path=queue_path, source_summary_path=summary_path, output_dir=output_dir, limit=8)
    submit_response = tmp_path / "submit.json"
    dry_run = tmp_path / "dry.json"
    submit_response.write_text(json.dumps({"data": {"submissionId": "sub_test", "createdAt": "now"}}), encoding="utf-8")
    dry_run.write_text(json.dumps({"dry_run": True}), encoding="utf-8")

    summary = record_submit_response(output_dir=output_dir, submit_response_path=submit_response, dry_run_response_path=dry_run)

    assert summary["submission"]["submission_id"] == "sub_test"
    assert summary["submission"]["status"] == "submitted"
    assert "sub_test" in (output_dir / "alt_composition_8x3_sair_probe_report.md").read_text(encoding="utf-8")


def test_build_feedback_joins_verified_rows_and_pair_status_updates(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_path = packet_dir / PACKET_JSONL
    packet_rows = [
        {
            **_queue_row(1, "hash-a"),
            "probe_row_number": 1,
            "source_queue_rank": 1,
            "short_hash": "hash-a",
            "submission_line": "2,1," + ",".join(["0"] * 22) + ",1",
        },
        {
            **_queue_row(2, "hash-b"),
            "probe_row_number": 2,
            "source_queue_rank": 2,
            "short_hash": "hash-b",
            "submission_line": "2,1," + ",".join(["0"] * 22) + ",1",
        },
    ]
    packet_path.write_text("\n".join(json.dumps(row) for row in packet_rows) + "\n", encoding="utf-8")
    response_path = tmp_path / "status.json"
    response_path.write_text(
        json.dumps(
            {
                "data": {
                    "submissionId": "sub_test",
                    "competitionId": "igp24",
                    "verifiedPolynomials": [
                        {
                            "polynomialIndex": 0,
                            "status": "accepted",
                            "label": "24T123",
                            "t": 123,
                            "r": 24,
                            "scoreable": True,
                            "scoringStatus": "scoreable",
                            "discSource": "exact_nfdisc",
                            "fieldDiscAbs": "99",
                            "inBaseline": False,
                            "baselineUnlocked": False,
                        },
                        {
                            "polynomialIndex": 1,
                            "status": "accepted",
                            "label": "24T25000",
                            "t": 25000,
                            "r": 24,
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
    output_json = tmp_path / ACCEPTED_FEEDBACK_JSON

    feedback = build_feedback(status_response_path=response_path, packet_jsonl_path=packet_path, output_json_path=output_json)
    pair_status, update = update_pair_status(
        {"record_type": "igp24_pair_status_ledger", "pairs": [{"pair_key": "24T25000|r=24", "canonical_hash": "old"}]},
        feedback,
        feedback_path=output_json,
    )

    assert feedback["summary"]["accepted_rows"] == 2
    assert feedback["summary"]["label_counts"] == {"24T123": 1, "24T25000": 1}
    assert feedback["summary"]["escaped_known_basins"] is True
    assert feedback["summary"]["escaped_known_basin_labels"] == ["24T123"]
    assert update["new_pairs_added"] == 1
    assert update["alternates_added"] == 1
    pairs = {pair["pair_key"]: pair for pair in pair_status["pairs"]}
    assert pairs["24T123|r=24"]["exact_nfdisc_abs"] == 99
    assert pairs["24T25000|r=24"]["accepted_alternates"][0]["canonical_hash"] == "hash-b"
