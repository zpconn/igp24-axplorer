import json

from scripts.igp24_submission_plan import (
    build_joined_rows,
    build_summary,
    load_baseline_csv,
    merge_verified_evidence_rows,
    select_best_per_pair,
    write_outputs,
)


def _verified(canonical_hash, label="24T24970"):
    return {
        "candidate_hash": canonical_hash,
        "status": "verified",
        "verified_group_label": label,
        "degree": 24,
        "is_irreducible": True,
        "raw_output_source_path": f"data/igp24/online_magma_manual_output_{canonical_hash[:12]}_20260705.xml",
    }


def _candidate(canonical_hash, *, coeff0=1, r=4, score=100.0, log_disc=80.0, extra=None):
    row = {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
        "real_root_count": r,
        "score": score,
        "log_abs_discriminant": log_disc,
        "source_jsonl_path": "/tmp/candidates.jsonl",
    }
    if extra:
        row.update(extra)
    return row


def test_select_best_per_pair_suppresses_duplicate_expected_pairs():
    verified = [
        _verified("hash_a", "24T24970"),
        _verified("hash_b", "24T24970"),
        _verified("hash_c", "24T24979"),
    ]
    candidates = [
        _candidate("hash_a", coeff0=1, score=10.0, log_disc=90.0),
        _candidate("hash_b", coeff0=2, score=9.0, log_disc=70.0),
        _candidate("hash_c", coeff0=3, score=8.0, log_disc=95.0),
    ]

    joined, diagnostics = build_joined_rows(verified_rows=verified, candidate_rows=candidates, baseline={}, baseline_loaded=False)
    selected, suppressed = select_best_per_pair(joined)

    by_pair = {row["pair_key"]: row for row in selected}
    assert diagnostics["joined_rows"] == 3
    assert len(selected) == 2
    assert by_pair["24T24970|r=4"]["canonical_hash"] == "hash_b"
    assert by_pair["24T24970|r=4"]["duplicate_pair_candidates_suppressed"] == 1
    assert suppressed == [
        {
            "canonical_hash": "hash_a",
            "discriminant_rank_category": "log_polynomial_disc_proxy",
            "discriminant_value": 90.0,
            "pair_key": "24T24970|r=4",
            "reason": "duplicate_expected_pair_lower_ranked",
            "selected_canonical_hash": "hash_b",
        }
    ]


def test_exact_nfdisc_preferred_over_proxy_discriminant():
    verified = [_verified("exact_row", "24T24970"), _verified("proxy_row", "24T24970")]
    candidates = [
        _candidate("exact_row", coeff0=1, log_disc=200.0, extra={"nfdisc_abs": 10_000}),
        _candidate("proxy_row", coeff0=2, log_disc=1.0),
    ]

    joined, _diagnostics = build_joined_rows(verified_rows=verified, candidate_rows=candidates, baseline={}, baseline_loaded=False)
    selected, _suppressed = select_best_per_pair(joined)

    assert selected[0]["canonical_hash"] == "exact_row"
    assert selected[0]["discriminant_rank_category"] == "exact_nfdisc"
    assert selected[0]["exact_nfdisc_abs"] == 10_000


def test_verified_label_and_pari_nfdisc_rows_merge_by_hash():
    verified = [
        _verified("hash_a", "24T24970") | {"signature_r": 4, "status": "verified"},
        {
            "candidate_hash": "hash_a",
            "record_type": "igp24_pari_nfdisc_result",
            "status": "nfdisc_ok",
            "nfdisc_abs": 321,
            "nfdisc_source": "pari_gp_nfdisc",
            "poly_disc_abs": 999,
            "pari_real_root_count": 4,
        },
    ]
    candidates = [_candidate("hash_a", coeff0=1, r=2, log_disc=200.0)]

    merged = merge_verified_evidence_rows(verified)
    joined, diagnostics = build_joined_rows(
        verified_rows=verified,
        candidate_rows=candidates,
        baseline={},
        baseline_loaded=False,
    )

    assert len(merged) == 1
    assert diagnostics["verified_rows_loaded"] == 2
    assert diagnostics["verified_evidence_rows_after_merge"] == 1
    assert joined[0]["verified_group_label"] == "24T24970"
    assert joined[0]["expected_r"] == 4
    assert joined[0]["expected_r_source"] == "verified.signature_r"
    assert joined[0]["exact_r_status"] == "ok"
    assert joined[0]["exact_nfdisc_abs"] == 321
    assert joined[0]["exact_nfdisc_status"] == "ok"
    assert joined[0]["exact_nfdisc_source"] == "pari_gp_nfdisc"
    assert joined[0]["discriminant_source"] == "pari_gp_nfdisc"
    assert joined[0]["discriminant_rank_category"] == "exact_nfdisc"


def test_baseline_csv_classifies_unknown_new_and_improvement_states(tmp_path):
    baseline_path = tmp_path / "baseline.csv"
    baseline_path.write_text(
        "label,r,nfdisc_abs\n24T24970,4,500\n24T24979,4,1000\n",
        encoding="utf-8",
    )
    baseline, baseline_info = load_baseline_csv(baseline_path)
    verified = [
        _verified("improved", "24T24970"),
        _verified("requires_nfdisc", "24T24979"),
        _verified("new_pair", "24T24759"),
    ]
    candidates = [
        _candidate("improved", coeff0=1, extra={"nfdisc_abs": 400}),
        _candidate("requires_nfdisc", coeff0=2),
        _candidate("new_pair", coeff0=3),
    ]

    joined, _diagnostics = build_joined_rows(
        verified_rows=verified,
        candidate_rows=candidates,
        baseline=baseline,
        baseline_loaded=baseline_info["baseline_loaded"],
    )

    status_by_hash = {row["canonical_hash"]: row["baseline_status"] for row in joined}
    assert status_by_hash == {
        "improved": "baseline_improvement_candidate",
        "new_pair": "non_baseline_candidate",
        "requires_nfdisc": "baseline_requires_exact_nfdisc",
    }
    scoreability_by_hash = {row["canonical_hash"]: row["scoreability_status"] for row in joined}
    assert scoreability_by_hash == {
        "improved": "baseline_improvement_needs_exact_evidence",
        "new_pair": "new_pair_needs_exact_r",
        "requires_nfdisc": "baseline_pair_needs_exact_nfdisc",
    }
    assert all(row["exact_r_status"] == "candidate_proxy" for row in joined)
    assert all(row["scoreable_claimed"] is False for row in joined)


def test_no_baseline_marks_pairs_unknown_and_outputs_manual_candidate_file(tmp_path):
    verified = [_verified("hash_a", "24T24970"), _verified("hash_b", "24T24979")]
    candidates = [_candidate("hash_a", coeff0=4), _candidate("hash_b", coeff0=5)]
    joined, diagnostics = build_joined_rows(verified_rows=verified, candidate_rows=candidates, baseline={}, baseline_loaded=False)
    selected, suppressed = select_best_per_pair(joined)
    summary = build_summary(
        verified_paths=[tmp_path / "results.jsonl"],
        candidate_paths=[tmp_path / "candidates.jsonl"],
        baseline_info={"baseline_loaded": False, "baseline_path": None, "pairs": 0},
        diagnostics=diagnostics,
        selected=selected,
        suppressed=suppressed,
        output_dir=tmp_path / "plan",
        command=["python3", "scripts/igp24_submission_plan.py"],
        source_commit="abc123",
    )

    paths = write_outputs(selected=selected, suppressed=suppressed, summary=summary, output_dir=tmp_path / "plan")

    reloaded_summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    text_lines = paths["submission_candidates_txt"].read_text(encoding="utf-8").splitlines()
    plan_rows = [json.loads(line) for line in paths["submission_plan_jsonl"].read_text(encoding="utf-8").splitlines()]

    assert reloaded_summary["baseline_status_counts"] == {"baseline_unknown": 2}
    assert reloaded_summary["exact_r_status_counts"] == {"candidate_proxy": 2}
    assert reloaded_summary["exact_nfdisc_status_counts"] == {"missing": 2}
    assert reloaded_summary["safety"]["sair_submission"] is False
    assert reloaded_summary["safety"]["scoreable_claims"] is False
    assert len([line for line in text_lines if not line.startswith("#")]) == 2
    assert all("# NOT_SUBMITTED expected_pair=24T" in line for line in text_lines if not line.startswith("#"))
    assert [row["submission_plan_rank"] for row in plan_rows] == [1, 2]
