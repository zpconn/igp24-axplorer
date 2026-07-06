import json

from scripts.igp24_verified_label_feedback import (
    GENERIC_S24_LABEL,
    SAFETY_NOTE,
    build_summary,
    join_feedback_rows,
    representative_rows,
    write_outputs,
)


def _audit_record(
    canonical_hash,
    *,
    queue_index=1,
    square=True,
    divisor=2,
    base_degree=12,
    strategy="quartic_lift",
    flags=None,
    score=100.0,
    non_generic_score=900.0,
):
    if flags is None:
        flags = ["exact_composed_support"]
    return {
        "canonical_hash": canonical_hash,
        "queue_index": queue_index,
        "local_discriminant_is_square": square,
        "primary_exact_block_divisor": divisor,
        "primary_base_degree": base_degree,
        "sparse_bucket": "medium",
        "source_strategy": strategy,
        "non_generic_flags": flags,
        "score": score,
        "non_generic_score": non_generic_score,
        "coefficient_height": 5,
        "nonzero_exponents": [0, divisor, 24],
        "nonzero_term_count": 3,
        "primary_base_polynomial": "(1)*1 + (1)*y^12",
    }


def _verification_record(canonical_hash, *, label, degree=24, irreducible=True, status="verified"):
    return {
        "candidate_hash": canonical_hash,
        "status": status,
        "verified_group_label": label,
        "transitive_group_id": int(label.split("T", 1)[1]) if label else None,
        "degree": degree,
        "is_irreducible": irreducible,
        "magma_runtime_seconds": 0.42,
        "magma_version": "V2.29-8",
        "raw_output_source_path": f"data/igp24/online_magma_manual_output_{canonical_hash[:12]}_20260705.xml",
    }


def _diagnostic_record(canonical_hash):
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [1] + [0] * 23 + [1],
    }


def test_join_feedback_rows_summarizes_verified_labels_by_structure(tmp_path):
    audits = [
        _audit_record("square_hash", queue_index=1, square=True, divisor=2, base_degree=12),
        _audit_record("tail_hash", queue_index=2, square=False, divisor=2, base_degree=12, strategy="sparse"),
        _audit_record("d3_hash", queue_index=3, square=False, divisor=3, base_degree=8),
    ]
    verification = [
        _verification_record("square_hash", label="24T24970"),
        _verification_record("tail_hash", label="24T24979"),
        _verification_record("d3_hash", label="24T24759"),
    ]

    joined, diagnostics = join_feedback_rows(
        structure_records=audits,
        verification_records=verification,
        diagnostic_records=[_diagnostic_record("square_hash")],
    )
    representatives = representative_rows(joined, per_label=1)
    summary = build_summary(
        joined=joined,
        representatives=representatives,
        diagnostics_info=diagnostics,
        output_dir=tmp_path,
        command=["python3", "scripts/igp24_verified_label_feedback.py"],
        source_commit="abc123",
        structure_path=tmp_path / "structure.jsonl",
        verification_path=tmp_path / "magma.jsonl",
        diagnostic_path=tmp_path / "diagnostic.jsonl",
    )

    assert diagnostics["joined_records"] == 3
    assert summary["exact_label_counts"] == {"24T24759": 1, "24T24970": 1, "24T24979": 1}
    assert summary["label_by_square_discriminant"] == {
        "False": {"24T24759": 1, "24T24979": 1},
        "True": {"24T24970": 1},
    }
    assert summary["label_by_primary_block"] == {
        "d=2|base=12": {"24T24970": 1, "24T24979": 1},
        "d=3|base=8": {"24T24759": 1},
    }
    assert summary["generic_24T25000_records"] == 0
    assert summary["safety"]["magma_executed"] is False
    assert GENERIC_S24_LABEL == "24T25000"
    square_rep = next(record for record in representatives if record["verified_group_label"] == "24T24970")
    assert square_rep["coefficient_summary"]["exported_coefficients"] == [1] + [0] * 23 + [1]
    assert any("divisor-3/base-degree-8" in item for item in summary["recommendations"])


def test_join_feedback_rows_records_missing_and_nonverified_inputs():
    audits = [_audit_record("present_hash")]
    verification = [
        _verification_record("present_hash", label="24T24970"),
        _verification_record("missing_hash", label="24T24979"),
        _verification_record("failed_hash", label=None, status="failed"),
    ]

    joined, diagnostics = join_feedback_rows(structure_records=audits, verification_records=verification)

    assert [row["canonical_hash"] for row in joined] == ["present_hash"]
    assert diagnostics["missing_structure_hashes"] == ["missing_hash", "failed_hash"]
    assert diagnostics["non_verified_hashes"] == []


def test_write_outputs_creates_feedback_report_and_machine_outputs(tmp_path):
    audits = [_audit_record("square_hash", square=True)]
    verification = [_verification_record("square_hash", label="24T24970")]
    joined, diagnostics = join_feedback_rows(structure_records=audits, verification_records=verification)
    representatives = representative_rows(joined, per_label=1)
    summary = build_summary(
        joined=joined,
        representatives=representatives,
        diagnostics_info=diagnostics,
        output_dir=tmp_path / "feedback",
        command=["python3", "scripts/igp24_verified_label_feedback.py"],
        source_commit="abc123",
        structure_path=tmp_path / "structure.jsonl",
        verification_path=tmp_path / "magma.jsonl",
        diagnostic_path=None,
    )

    paths = write_outputs(joined=joined, representatives=representatives, summary=summary, output_dir=tmp_path / "feedback")

    reloaded_summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    report = paths["report_md"].read_text(encoding="utf-8")
    joined_rows = [json.loads(line) for line in paths["joined_jsonl"].read_text(encoding="utf-8").splitlines()]

    assert reloaded_summary["exact_label_counts"] == {"24T24970": 1}
    assert joined_rows[0]["feedback_caveat"] == SAFETY_NOTE
    assert "IGP24 Verified Label Feedback" in report
    assert "24T24970" in report
    assert "does not call PARI" in report
