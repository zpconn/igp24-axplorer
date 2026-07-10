import json

import pytest

from scripts.igp24_packet_verification_queue import (
    VerificationQueueError,
    index_source_rows,
    main as queue_main,
    materialize_queue,
)


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _source_row(candidate_hash, coeff0):
    return {
        "canonical_hash": candidate_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
        "real_root_count": 8,
        "group_compatibility": {"valuable_targets_not_ruled_out": ["24T1|r=8"]},
    }


def _selected_row(candidate_hash, rank):
    return {
        "canonical_hash": candidate_hash,
        "short_hash": candidate_hash[:12],
        "optimizer_rank": rank,
        "best_case_points": 1.0,
        "marginal_best_case_points": 1.0,
        "expected_points_status": "unavailable_uncalibrated",
        "valuable_targets_not_ruled_out": ["24T1|r=8"],
    }


def test_materialize_queue_preserves_selected_order_and_coefficients(tmp_path):
    hash_a = "a" * 64
    hash_b = "b" * 64
    source_path = tmp_path / "source.jsonl"
    _write_jsonl(source_path, [_source_row(hash_b, 3), _source_row(hash_a, 2)])
    by_hash, summaries = index_source_rows([source_path])

    records = materialize_queue(
        selected_rows=[_selected_row(hash_a, 1), _selected_row(hash_b, 2)],
        source_rows_by_hash=by_hash,
    )

    assert summaries == [{"path": str(source_path), "rows": 2, "coefficient_rows_indexed": 2}]
    assert [row["canonical_hash"] for row in records] == [hash_a, hash_b]
    assert [row["exported_coefficients"][0] for row in records] == [2, 3]
    assert [row["optimizer_rank"] for row in records] == [1, 2]
    assert records[0]["packet_optimizer_selected_row"]["short_hash"] == hash_a[:12]
    assert records[0]["offline_verification_status"] == "prepared_unverified"
    assert records[0]["verified_group_label"] is None


def test_materialize_queue_rejects_missing_source_coefficients(tmp_path):
    with pytest.raises(VerificationQueueError, match="missing from coefficient sources"):
        materialize_queue(
            selected_rows=[_selected_row("c" * 64, 1)],
            source_rows_by_hash={},
        )


def test_cli_writes_offline_verify_review_batch(tmp_path):
    hash_a = "a" * 64
    hash_b = "b" * 64
    selected = tmp_path / "selected.jsonl"
    source = tmp_path / "source.jsonl"
    output_dir = tmp_path / "queue"
    _write_jsonl(selected, [_selected_row(hash_a, 1), _selected_row(hash_b, 2)])
    _write_jsonl(source, [_source_row(hash_a, 2), _source_row(hash_b, 3)])

    assert queue_main(
        [
            "--selected_jsonl",
            str(selected),
            "--source_candidate_jsonl",
            str(source),
            "--output_dir",
            str(output_dir),
        ]
    ) == 0

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    batch_rows = [json.loads(line) for line in (output_dir / "verification_batch.jsonl").read_text(encoding="utf-8").splitlines()]
    coefficient_lines = (output_dir / "verification_coefficients.txt").read_text(encoding="utf-8").splitlines()

    assert manifest["record_type"] == "igp24_packet_verification_queue"
    assert manifest["selected_hashes"] == [hash_a, hash_b]
    assert manifest["safety"]["sair_submission"] is False
    assert [row["canonical_hash"] for row in batch_rows] == [hash_a, hash_b]
    assert coefficient_lines == [
        json.dumps([2] + [0] * 23 + [1], separators=(",", ":")),
        json.dumps([3] + [0] * 23 + [1], separators=(",", ":")),
    ]
