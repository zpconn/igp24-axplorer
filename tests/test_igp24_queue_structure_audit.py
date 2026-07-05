import json

from scripts.igp24_queue_structure_audit import (
    SAFETY_NOTE,
    audit_record,
    audit_records,
    build_summary,
    exact_block_bases,
    exported_coefficients,
    prioritize_records,
    write_outputs,
)


def _record(canonical_hash="a", coeffs=None, strategy="quartic_lift", flags=None, score=100.0, non_generic_score=1000.0):
    if coeffs is None:
        coeffs = [1] + [0] * 23
    if flags is None:
        flags = ["square_discriminant_excludes_s24", "exact_composed_support", "no_long_cycle_witness_in_sample"]
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": coeffs + [1],
        "score": score,
        "non_generic_score": non_generic_score,
        "real_root_count": 4,
        "coefficient_height": max(abs(value) for value in coeffs),
        "source_strategy": strategy,
        "non_generic_flags": flags,
        "non_generic_evidence": {
            "square_discriminant": "square_discriminant_excludes_s24" in flags,
            "block_structure": {"exact_block_divisors": [2] if "exact_composed_support" in flags else []},
        },
        "verified_group_label": None,
    }


def test_exported_coefficients_accepts_common_shapes():
    coeffs = [1] + [0] * 23

    assert exported_coefficients({"exported_coefficients": coeffs + [1]}) == coeffs + [1]
    assert exported_coefficients({"coefficients": coeffs}) == coeffs + [1]
    assert exported_coefficients({"decoded_coefficients": coeffs}) == coeffs + [1]


def test_exact_block_bases_extracts_lower_degree_polynomials():
    exported = [1] + [0] * 23 + [1]

    bases, summaries = exact_block_bases(exported)

    by_divisor = {base["divisor"]: base for base in bases}
    assert 12 in by_divisor
    assert by_divisor[12]["base_degree"] == 2
    assert by_divisor[12]["base_coefficients"] == [1, 0, 1]
    assert by_divisor[12]["base_polynomial"] == "(1)*1 + (1)*y^2"
    assert all(summary["exact_composed_support"] for summary in summaries)


def test_audit_record_confirms_square_discriminant_and_composed_support():
    record = _record("square")

    audited = audit_record(record, queue_index=1)

    assert audited["local_discriminant_is_square"] is True
    assert audited["square_discriminant_claim_status"] == "confirmed"
    assert audited["exact_composed_claim_status"] == "confirmed"
    assert audited["primary_exact_block_divisor"] == 12
    assert audited["primary_base_degree"] == 2
    assert audited["verified_group_label"] is None
    assert audited["exact_galois_label_claimed"] is False
    assert audited["local_algebra_caveat"] == SAFETY_NOTE


def test_audit_record_refutes_bad_square_claim():
    coeffs = [2] + [0] * 23
    record = _record("nonsquare", coeffs=coeffs, flags=["square_discriminant_excludes_s24", "exact_composed_support"])

    audited = audit_record(record, queue_index=1)

    assert audited["local_discriminant_is_square"] is False
    assert audited["square_discriminant_claim_status"] == "refuted"
    assert audited["exact_composed_claim_status"] == "confirmed"


def test_prioritize_records_covers_structural_buckets():
    square = audit_record(_record("square", strategy="quartic_lift", non_generic_score=1000.0), queue_index=1)
    nonsquare = audit_record(
        _record(
            "nonsquare",
            coeffs=[2] + [0] * 23,
            strategy="sparse",
            flags=["exact_composed_support", "no_long_cycle_witness_in_sample"],
            non_generic_score=900.0,
        ),
        queue_index=2,
    )
    d3_coeffs = [0] * 24
    d3_coeffs[0] = 1
    d3_coeffs[3] = 1
    d3 = audit_record(
        _record(
            "d3",
            coeffs=d3_coeffs,
            strategy="quartic_lift",
            flags=["exact_composed_support"],
            non_generic_score=800.0,
        ),
        queue_index=3,
    )

    priority = prioritize_records([square, nonsquare, d3], limit=3)

    assert [record["manual_priority_rank"] for record in priority] == [1, 2, 3]
    assert {record["canonical_hash"] for record in priority} == {"square", "nonsquare", "d3"}
    assert any("strategy:sparse" in record["manual_priority_new_coverage"] for record in priority)
    assert any("square:False" in record["manual_priority_new_coverage"] for record in priority)


def test_write_outputs_creates_local_algebra_only_artifacts(tmp_path):
    records = [_record("square")]
    audited, skipped = audit_records(records)
    priority = prioritize_records(audited, limit=1)
    summary = build_summary(
        input_path=tmp_path / "verification_batch.jsonl",
        records_loaded=1,
        audited=audited,
        skipped_counts=skipped,
        priority=priority,
        output_dir=tmp_path / "audit",
        command=["python3", "scripts/igp24_queue_structure_audit.py"],
        source_commit="abc123",
        block_divisors=[2, 3, 4, 6, 8, 12],
    )

    paths = write_outputs(audited=audited, priority=priority, summary=summary, output_dir=tmp_path / "audit")
    reloaded_summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    report = paths["report_md"].read_text(encoding="utf-8")
    priority_rows = [json.loads(line) for line in paths["priority_jsonl"].read_text(encoding="utf-8").splitlines()]

    assert reloaded_summary["safety"]["local_exact_algebra_only"] is True
    assert reloaded_summary["safety"]["exact_galois_labels_claimed"] is False
    assert reloaded_summary["records_with_local_square_discriminant"] == 1
    assert priority_rows[0]["canonical_hash"] == "square"
    assert "Queue Structure Audit" in report
    assert "not exact Galois labels" in report
