import json

from scripts.igp24_non_generic_diagnostic import (
    SAFETY_NOTE,
    block_structure_evidence,
    build_summary,
    diagnose_record,
    diagnose_records,
    record_coefficients,
    write_outputs,
)


def _record(canonical_hash="a", coeffs=None, score=10.0, strategy="fixture", discriminant=144):
    if coeffs is None:
        coeffs = [1] + [0] * 23
    return {
        "canonical_hash": canonical_hash,
        "coefficients": coeffs,
        "exported_coefficients": coeffs + [1],
        "score": score,
        "real_root_count": 4,
        "coefficient_height": max(abs(value) for value in coeffs),
        "discriminant": discriminant,
        "log_abs_discriminant": 20.0,
        "mod_p_factorization_degree_patterns": [
            {"prime": 5, "degrees": [2, 2, 4, 4, 6, 6]},
            {"prime": 7, "degrees": [4, 4, 8, 8]},
        ],
        "generation_metadata": {"strategy": strategy},
        "verification_status": "proxy_scored",
        "verified_group_label": None,
    }


def test_record_coefficients_accepts_common_shapes():
    coeffs = [1] + [0] * 23

    assert record_coefficients({"coefficients": coeffs}) == coeffs
    assert record_coefficients({"decoded_coefficients": coeffs}) == coeffs
    assert record_coefficients({"exported_coefficients": coeffs + [1]}) == coeffs
    assert record_coefficients({"exported_coefficients": coeffs + [2]}) is None


def test_block_structure_evidence_finds_exact_and_near_composed_support():
    exact = [0] * 24
    exact[0] = 1
    exact[6] = -2
    exact[12] = 3
    near = list(exact)
    near[5] = 1

    exact_evidence = block_structure_evidence(exact)
    near_evidence = block_structure_evidence(near)

    assert 6 in exact_evidence["exact_block_divisors"]
    assert exact_evidence["best_near_block_off_terms"] == 0
    assert near_evidence["best_near_block_divisor"] == 6
    assert near_evidence["best_near_block_off_terms"] == 1
    assert near_evidence["best_near_block_off_exponents"] == [5]


def test_diagnose_record_scores_square_discriminant_and_proxy_flags():
    coeffs = [0] * 24
    coeffs[0] = 1
    coeffs[6] = -2
    coeffs[12] = 3
    record = _record("square", coeffs=coeffs, discriminant=144)

    diagnostic = diagnose_record(record)

    assert diagnostic["verified_group_label"] is None
    assert diagnostic["non_generic_evidence"]["square_discriminant"] is True
    assert "square_discriminant_excludes_s24" in diagnostic["non_generic_flags"]
    assert "exact_composed_support" in diagnostic["non_generic_flags"]
    assert "all_sampled_frobenius_even" in diagnostic["non_generic_flags"]
    assert diagnostic["non_generic_score"] > 1000
    assert diagnostic["proxy_only_caveat"] == SAFETY_NOTE


def test_diagnose_records_filters_deduplicates_and_sorts():
    exact = [0] * 24
    exact[0] = 1
    exact[6] = -2
    exact[12] = 3
    weak = [1] + [0] * 23
    records = [
        _record("weak", coeffs=weak, score=100.0, strategy="sparse", discriminant=145),
        _record("strong", coeffs=exact, score=1.0, strategy="quartic_lift", discriminant=144),
        _record("strong", coeffs=exact, score=2.0, strategy="quartic_lift", discriminant=144),
        _record("other_r", coeffs=exact, strategy="quartic_lift", discriminant=144) | {"real_root_count": 2},
        {"canonical_hash": "bad", "verification_status": "rejected"},
    ]

    diagnostics, skipped = diagnose_records(records, target_r=4)

    assert [record["canonical_hash"] for record in diagnostics] == ["strong", "weak"]
    assert skipped["duplicate_canonical_hash"] == 1
    assert skipped["target_r_mismatch"] == 1
    assert skipped["invalid_or_missing_coefficients"] == 1


def test_write_outputs_creates_proxy_only_artifacts(tmp_path):
    diagnostic = diagnose_record(_record("a"))
    output_dir = tmp_path / "diag"
    summary = build_summary(
        input_paths=[tmp_path / "input"],
        ledger_paths=[tmp_path / "ledger.jsonl"],
        diagnostics=[diagnostic],
        selected=[diagnostic],
        skipped_counts={},
        output_dir=output_dir,
        filters={"target_r": 4, "deduplicate_by": "canonical_hash"},
        command=["python3", "scripts/igp24_non_generic_diagnostic.py"],
        source_commit="abc123",
    )

    paths = write_outputs([diagnostic], [diagnostic], output_dir, summary)
    selected = [json.loads(line) for line in paths["shortlist_jsonl"].read_text(encoding="utf-8").splitlines()]
    reloaded_summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    report = paths["report_md"].read_text(encoding="utf-8")

    assert selected[0]["canonical_hash"] == "a"
    assert selected[0]["verified_group_label"] is None
    assert json.loads(paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()[0])[-1] == 1
    assert reloaded_summary["safety"]["proxy_only"] is True
    assert reloaded_summary["safety"]["exact_group_claims"] is False
    assert "Non-Generic Galois Proxy Diagnostic" in report
