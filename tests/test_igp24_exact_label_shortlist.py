import json

from scripts.igp24_exact_label_shortlist import (
    SAFETY_NOTE,
    annotate_records,
    build_family_rules,
    build_summary,
    parse_label_quotas,
    select_shortlist,
    write_outputs,
)


def _feedback(canonical_hash, label, *, square, divisor, base_degree, sparse="sparse", strategy="quartic_lift"):
    return {
        "canonical_hash": canonical_hash,
        "verified_group_label": label,
        "raw_output_source_path": f"data/igp24/online_magma_manual_output_{canonical_hash[:12]}_20260705.xml",
        "local_discriminant_is_square": square,
        "primary_exact_block_divisor": divisor,
        "primary_base_degree": base_degree,
        "sparse_bucket": sparse,
        "source_strategy": strategy,
    }


def _audit(canonical_hash, *, queue, square, divisor, base_degree, non_generic=100.0, score=1000.0, sparse="sparse"):
    return {
        "canonical_hash": canonical_hash,
        "queue_index": queue,
        "local_discriminant_is_square": square,
        "primary_exact_block_divisor": divisor,
        "primary_base_degree": base_degree,
        "sparse_bucket": sparse,
        "source_strategy": "quartic_lift",
        "non_generic_flags": ["exact_composed_support"],
        "score": score,
        "non_generic_score": non_generic,
        "real_root_count": 4,
        "coefficient_height": 3,
    }


def _candidate(canonical_hash, coeff0):
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
    }


def _feedback_rows():
    return [
        _feedback("known_square", "24T24970", square=True, divisor=2, base_degree=12, sparse="very_sparse"),
        _feedback("known_square_2", "24T24970", square=True, divisor=2, base_degree=12, sparse="sparse"),
        _feedback("known_tail", "24T24979", square=False, divisor=2, base_degree=12, sparse="very_sparse"),
        _feedback("known_d3", "24T24759", square=False, divisor=3, base_degree=8),
    ]


def test_build_family_rules_uses_coarse_structural_labels():
    rules = build_family_rules(_feedback_rows(), mode="coarse")

    assert rules["square=True|divisor=2|base_degree=12"]["label_counts"] == {"24T24970": 2}
    assert rules["square=False|divisor=2|base_degree=12"]["dominant_feedback_family_label"] == "24T24979"
    assert rules["square=False|divisor=3|base_degree=8"]["confidence"] == 1.0


def test_annotate_and_select_shortlist_preserves_label_coverage():
    feedback_rows = _feedback_rows()
    audit_rows = [
        _audit("new_square", queue=1, square=True, divisor=2, base_degree=12, non_generic=900.0),
        _audit("known_square", queue=2, square=True, divisor=2, base_degree=12, non_generic=800.0),
        _audit("new_tail", queue=3, square=False, divisor=2, base_degree=12, non_generic=700.0),
        _audit("new_d3", queue=4, square=False, divisor=3, base_degree=8, non_generic=600.0),
        _audit("new_unmatched", queue=5, square=False, divisor=4, base_degree=6, non_generic=500.0),
    ]
    rules = build_family_rules(feedback_rows, mode="coarse")
    annotated = annotate_records(
        audit_rows,
        family_rules=rules,
        feedback_rows=feedback_rows,
        candidate_rows=[_candidate("new_square", 1), _candidate("new_tail", 2), _candidate("new_d3", 3)],
        mode="coarse",
    )

    selected = select_shortlist(
        annotated,
        family_rules=rules,
        limit=3,
        min_per_label=0,
        label_quotas=parse_label_quotas("24T24970:1,24T24979:1,24T24759:1"),
        exclude_verified_hashes=True,
    )

    assert {record["feedback_family_label"] for record in selected} == {"24T24970", "24T24979", "24T24759"}
    assert all(record["exact_group_claimed_by_helper"] is False for record in selected)
    assert selected[0]["known_verified_group_label"] is None
    assert selected[0]["exported_coefficients"] == [1] + [0] * 23 + [1]
    assert all(record["feedback_family_match_status"] == "matched" for record in selected)


def test_select_shortlist_can_include_unmatched_fill_rows():
    feedback_rows = _feedback_rows()
    rules = build_family_rules(feedback_rows, mode="coarse")
    annotated = annotate_records(
        [
            _audit("new_square", queue=1, square=True, divisor=2, base_degree=12, non_generic=10.0),
            _audit("new_unmatched", queue=2, square=False, divisor=4, base_degree=6, non_generic=999.0),
        ],
        family_rules=rules,
        feedback_rows=feedback_rows,
        mode="coarse",
    )

    selected = select_shortlist(annotated, family_rules=rules, limit=2, min_per_label=0, include_unmatched=True)

    assert [record["canonical_hash"] for record in selected] == ["new_square", "new_unmatched"]
    assert selected[1]["feedback_family_match_status"] == "unmatched"


def test_select_shortlist_can_cap_known_family_and_prefer_unmatched_fill():
    feedback_rows = _feedback_rows()
    rules = build_family_rules(feedback_rows, mode="coarse")
    annotated = annotate_records(
        [
            _audit("knownish_a", queue=1, square=False, divisor=2, base_degree=12, non_generic=800.0),
            _audit("knownish_b", queue=2, square=False, divisor=2, base_degree=12, non_generic=790.0),
            _audit("novel_high", queue=3, square=False, divisor=6, base_degree=4, non_generic=700.0),
            _audit("novel_low", queue=4, square=False, divisor=4, base_degree=6, non_generic=600.0),
        ],
        family_rules=rules,
        feedback_rows=feedback_rows,
        mode="coarse",
    )

    selected = select_shortlist(
        annotated,
        family_rules=rules,
        limit=3,
        min_per_label=0,
        label_quotas=parse_label_quotas("24T24979:1"),
        include_unmatched=True,
        max_per_family_label=1,
        prefer_unmatched=True,
    )

    assert [record["canonical_hash"] for record in selected] == ["knownish_a", "novel_high", "novel_low"]
    assert [record["feedback_family_match_status"] for record in selected] == ["matched", "unmatched", "unmatched"]
    assert selected[0]["exact_label_shortlist_reason"] == "quota:24T24979"


def test_write_outputs_creates_local_file_only_artifacts(tmp_path):
    feedback_rows = _feedback_rows()
    audit_rows = [_audit("new_square", queue=1, square=True, divisor=2, base_degree=12, non_generic=900.0)]
    rules = build_family_rules(feedback_rows, mode="coarse")
    annotated = annotate_records(
        audit_rows,
        family_rules=rules,
        feedback_rows=feedback_rows,
        candidate_rows=[_candidate("new_square", 7)],
        mode="coarse",
    )
    selected = select_shortlist(annotated, family_rules=rules, limit=1, min_per_label=1)
    summary = build_summary(
        structure_path=tmp_path / "structure.jsonl",
        feedback_path=tmp_path / "feedback.jsonl",
        candidate_paths=[tmp_path / "candidates.jsonl"],
        output_dir=tmp_path / "out",
        family_rules=rules,
        annotated=annotated,
        selected=selected,
        command=["python3", "scripts/igp24_exact_label_shortlist.py"],
        source_commit="abc123",
        options={"limit": 1},
    )

    paths = write_outputs(selected=selected, summary=summary, output_dir=tmp_path / "out")

    reloaded = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    report = paths["report_md"].read_text(encoding="utf-8")
    shortlist = [json.loads(line) for line in paths["shortlist_jsonl"].read_text(encoding="utf-8").splitlines()]
    coeffs = [json.loads(line) for line in paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()]

    assert reloaded["safety"]["local_file_only"] is True
    assert reloaded["safety"]["exact_group_claims"] is False
    assert shortlist[0]["planning_caveat"] == SAFETY_NOTE
    assert coeffs == [[7] + [0] * 23 + [1]]
    assert "Exact-Label-Aware Shortlist" in report
    assert "Feedback family labels are planning labels" in report
