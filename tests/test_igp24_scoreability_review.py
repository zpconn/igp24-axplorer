import json

from scripts.igp24_scoreability_review import classify_rows, load_accepted_pairs, write_outputs, build_summary
from scripts.igp24_submission_plan import build_joined_rows, load_baseline_csv, select_best_per_pair


def _verified(candidate_hash, label, *, nfdisc, r=4, text=None):
    return [
        {
            "candidate_hash": candidate_hash,
            "status": "verified",
            "verified_group_label": label,
            "computed_r": r,
            "degree": 24,
            "is_irreducible": True,
            "galois_group_text": text or "Permutation group G acting on a set of cardinality 24",
            "raw_output_source_path": f"/tmp/{candidate_hash[:12]}.xml",
        },
        {
            "candidate_hash": candidate_hash,
            "status": "nfdisc_ok",
            "record_type": "igp24_pari_nfdisc_result",
            "nfdisc_abs": nfdisc,
            "nfdisc_source": "pari_gp_nfdisc",
            "pari_real_root_count": r,
        },
    ]


def _candidate(candidate_hash, *, coeff0=1, score=100.0):
    return {
        "canonical_hash": candidate_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
        "score": score,
        "real_root_count": 4,
        "source_jsonl_path": "/tmp/candidates.jsonl",
    }


def _write_manifest(path):
    manifest = {
        "selected_record_summaries": [
            {
                "pair_key": "24T24648|r=4",
                "canonical_hash": "accepted_a",
                "short_hash": "accepted_a",
                "exact_nfdisc_abs": 1000,
                "verified_group_label": "24T24648",
                "expected_r": 4,
            },
            {
                "pair_key": "24T24759|r=4",
                "canonical_hash": "accepted_b",
                "short_hash": "accepted_b",
                "exact_nfdisc_abs": 2000,
                "verified_group_label": "24T24759",
                "expected_r": 4,
            },
        ]
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_classifies_new_generic_pair_and_accepted_pair_improvement(tmp_path):
    baseline_path = tmp_path / "baseline.csv"
    baseline_path.write_text("label,r,nfdisc_abs\n24T1,0,10\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path)
    accepted, _accepted_info = load_accepted_pairs(manifest_path)
    baseline, baseline_info = load_baseline_csv(baseline_path)

    generic_best = "g" * 64
    generic_worse = "h" * 64
    improvement = "i" * 64
    duplicate = "j" * 64
    verified = []
    verified += _verified(
        generic_best,
        "24T25000",
        nfdisc=500,
        text="Symmetric group G acting on a set of cardinality 24",
    )
    verified += _verified(
        generic_worse,
        "24T25000",
        nfdisc=700,
        text="Symmetric group G acting on a set of cardinality 24",
    )
    verified += _verified(improvement, "24T24648", nfdisc=900)
    verified += _verified(duplicate, "24T24759", nfdisc=3000)
    candidates = [
        _candidate(generic_best, coeff0=1),
        _candidate(generic_worse, coeff0=2),
        _candidate(improvement, coeff0=3),
        _candidate(duplicate, coeff0=4),
    ]

    joined, _diagnostics = build_joined_rows(
        verified_rows=verified,
        candidate_rows=candidates,
        baseline=baseline,
        baseline_loaded=baseline_info["baseline_loaded"],
    )
    selected, _suppressed = select_best_per_pair(joined)
    reviewed = classify_rows(joined, selected, accepted)
    by_hash = {row["canonical_hash"]: row for row in reviewed}

    assert by_hash[generic_best]["scoreability_review_classification"] == "scoreable_new_pair_generic_s24"
    assert by_hash[generic_best]["actionable_for_manual_submission"] is True
    assert by_hash[generic_worse]["scoreability_review_classification"] == "duplicate_pending_pair_not_best"
    assert by_hash[generic_worse]["actionable_for_manual_submission"] is False
    assert by_hash[improvement]["scoreability_review_classification"] == "accepted_pair_discriminant_improvement_candidate"
    assert by_hash[improvement]["accepted_nfdisc_delta"] == -100
    assert by_hash[improvement]["actionable_for_manual_submission"] is True
    assert by_hash[duplicate]["scoreability_review_classification"] == "accepted_pair_duplicate_not_improved"
    assert by_hash[duplicate]["actionable_for_manual_submission"] is False


def test_write_outputs_creates_clean_and_annotated_actionable_files(tmp_path):
    row = {
        "canonical_hash": "a" * 64,
        "short_hash": "a" * 12,
        "pair_key": "24T25000|r=4",
        "scoreability_review_classification": "scoreable_new_pair_generic_s24",
        "exact_nfdisc_abs": 500,
        "exact_r_status": "ok",
        "exact_nfdisc_status": "ok",
        "exported_coefficients": [5] + [0] * 23 + [1],
    }
    summary = build_summary(
        reviewed_rows=[row],
        actionable_rows=[row],
        verified_paths=[tmp_path / "verified.jsonl"],
        candidate_paths=[tmp_path / "candidates.jsonl"],
        baseline_info={"baseline_loaded": True, "pairs": 1},
        accepted_info={"accepted_manifest_loaded": True, "accepted_pairs": 0},
        diagnostics={"joined_rows": 1},
        output_dir=tmp_path / "review",
        command=["python3", "scripts/igp24_scoreability_review.py"],
        source_commit="abc123",
        copied_files=[],
    )

    paths = write_outputs(
        reviewed_rows=[row],
        actionable_rows=[row],
        summary=summary,
        output_dir=tmp_path / "review",
    )

    assert paths["submission_coefficients_txt"].read_text(encoding="utf-8").strip() == "5," + ",".join(["0"] * 23) + ",1"
    annotated = paths["submission_annotated_txt"].read_text(encoding="utf-8")
    assert "expected_pair=24T25000|r=4" in annotated
    assert "scoreable_new_pair_generic_s24" in annotated
    report = paths["report_md"].read_text(encoding="utf-8")
    assert "IGP24 Scoreability Review" in report
