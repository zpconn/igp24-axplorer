import json

from scripts.igp24_historical_group_validation_rows import main as extract_main


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _candidate(hash_value="abc", *, patterns=True):
    row = {
        "candidate": {
            "canonical_hash": hash_value,
            "discriminant": 12345,
            "exported_coefficients": [2] + [0] * 23 + [1],
            "real_root_count": 16,
            "generation_metadata": {
                "construction_family": "model_sample_export",
                "template_family_id": "model:mixed:r16:sparse",
                "perturbation_mode": "gpu_decode",
                "basin_fingerprint": "basin-a",
            },
        }
    }
    if patterns:
        row["candidate"]["mod_p_factorization_degree_patterns"] = [
            {"prime": 5, "degrees": [1, 23]},
            {"prime": 7, "degrees": [3, 21]},
        ]
        row["candidate"]["mod_p_pattern_signature"] = "1.23|3.21"
    return row


def test_extracts_verified_rows_joined_to_selected_packet(tmp_path):
    selected_path = tmp_path / "selected_review_packet.jsonl"
    feedback_path = tmp_path / "accepted_feedback.json"
    output_dir = tmp_path / "out"
    _write_jsonl(selected_path, [_candidate("abc")])
    _write_json(
        feedback_path,
        {
            "source_selected_jsonl": str(selected_path),
            "accepted_rows": [
                {
                    "status": "accepted",
                    "label": "24T101",
                    "t": 101,
                    "r": 16,
                    "pair_key": "24T101|r=16",
                    "canonical_hash": "abc",
                    "polynomial_index": 0,
                    "row_number": 1,
                    "field_disc_abs": "12345",
                    "submission_id": "sub_test",
                    "submitted_at": "2026-07-09T00:00:00Z",
                }
            ],
        },
    )

    assert (
        extract_main(
            [
                "--accepted_feedback_json",
                str(feedback_path),
                "--output_dir",
                str(output_dir),
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "historical_group_validation_summary.json").read_text(encoding="utf-8"))
    assert summary["accepted_rows_seen"] == 1
    assert summary["validation_row_count"] == 1
    assert summary["skipped_row_count"] == 0
    row = json.loads((output_dir / "historical_group_validation_rows.jsonl").read_text(encoding="utf-8"))
    assert row["label"] == "24T101"
    assert row["verified_group_label"] == "24T101"
    assert row["t"] == 101
    assert row["r"] == 16
    assert row["canonical_hash"] == "abc"
    assert row["mod_p_factorization_degree_patterns"] == [
        {"degrees": [1, 23], "prime": 5},
        {"degrees": [3, 21], "prime": 7},
    ]
    assert row["construction_family"] == "model_sample_export"
    assert row["source"]["match_method"] == "canonical_hash"
    assert row["soundness"] == "sair_verified_label_plus_local_modular_factorization_evidence"


def test_skips_matched_rows_without_modular_factorization_evidence(tmp_path):
    selected_path = tmp_path / "selected_review_packet.jsonl"
    feedback_path = tmp_path / "accepted_feedback.json"
    output_dir = tmp_path / "out"
    _write_jsonl(selected_path, [_candidate("abc", patterns=False)])
    _write_json(
        feedback_path,
        {
            "source_selected_jsonl": str(selected_path),
            "accepted_rows": [
                {
                    "status": "accepted",
                    "label": "24T101",
                    "r": 16,
                    "canonical_hash": "abc",
                    "polynomial_index": 0,
                }
            ],
        },
    )

    assert (
        extract_main(
            [
                "--accepted_feedback_json",
                str(feedback_path),
                "--output_dir",
                str(output_dir),
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "historical_group_validation_summary.json").read_text(encoding="utf-8"))
    assert summary["validation_row_count"] == 0
    assert summary["skip_reason_counts"] == {"missing_modular_factorization_evidence": 1}
    skipped = json.loads((output_dir / "historical_group_validation_skipped.jsonl").read_text(encoding="utf-8"))
    assert skipped["reason"] == "missing_modular_factorization_evidence"


def test_falls_back_to_polynomial_index_when_hash_is_absent(tmp_path):
    selected_path = tmp_path / "selected_review_packet.jsonl"
    feedback_path = tmp_path / "accepted_feedback.json"
    output_dir = tmp_path / "out"
    _write_jsonl(selected_path, [_candidate("selected-hash")])
    _write_json(
        feedback_path,
        {
            "source_selected_jsonl": str(selected_path),
            "accepted_rows": [
                {
                    "status": "accepted",
                    "label": "24T102",
                    "r": 24,
                    "polynomial_index": 0,
                }
            ],
        },
    )

    assert (
        extract_main(
            [
                "--accepted_feedback_json",
                str(feedback_path),
                "--output_dir",
                str(output_dir),
            ]
        )
        == 0
    )

    row = json.loads((output_dir / "historical_group_validation_rows.jsonl").read_text(encoding="utf-8"))
    assert row["label"] == "24T102"
    assert row["pair_key"] == "24T102|r=24"
    assert row["canonical_hash"] == "selected-hash"
    assert row["source"]["match_method"] == "polynomial_index"
