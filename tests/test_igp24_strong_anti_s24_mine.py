import json

from scripts.igp24_strong_anti_s24_mine import (
    build_negative_family_rules,
    build_summary,
    diagnostic_family_key,
    mine_records,
    write_outputs,
)


def _diagnostic_row(
    canonical_hash,
    *,
    square=True,
    strategy="quartic_lift",
    exact_divisors=None,
    term_count=5,
    score=100.0,
):
    if exact_divisors is None:
        exact_divisors = [2]
    flags = ["near_composed_support"]
    if square:
        flags.append("square_discriminant_excludes_s24")
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [1] + [0] * 23 + [1],
        "real_root_count": 4,
        "source_strategy": strategy,
        "score": score,
        "non_generic_score": score,
        "non_generic_flags": flags,
        "non_generic_evidence": {
            "square_discriminant": square,
            "block_structure": {
                "exact_block_divisors": exact_divisors,
                "nonzero_term_count": term_count,
            },
        },
    }


def test_diagnostic_family_key_matches_square_and_structure():
    row = _diagnostic_row("h", square=True, exact_divisors=[2, 6], term_count=5, strategy="four_real_seed")

    assert diagnostic_family_key(row) == "square=True|divisor=6|base_degree=4|sparse=very_sparse|strategy=four_real_seed"


def test_negative_family_rules_mark_generic_feedback_family():
    generic = _diagnostic_row("generic", square=False, exact_divisors=[], term_count=8, strategy="four_real_seed")
    fresh_same_family = _diagnostic_row("fresh", square=False, exact_divisors=[], term_count=8, strategy="four_real_seed")
    feedback_rows = [{"canonical_hash": "generic", "verified_group_label": "24T25000", "r": 4, "status": "accepted"}]

    rules, by_hash = build_negative_family_rules(
        [generic, fresh_same_family],
        feedback_rows,
        pair_status={"24T25000|r=4": {"status": "accepted"}},
        target_r=4,
    )

    assert by_hash["generic"]["sair_feedback_outcome"] == "generic_s24"
    rule = rules[diagnostic_family_key(fresh_same_family)]
    assert rule["family_status"] == "generic_prone"
    assert rule["avoid_reason"] == "sair_generic_prone_family"


def test_mine_records_requires_fresh_square_non_negative_rows():
    exhausted = _diagnostic_row("exhausted", square=True, score=100)
    weak = _diagnostic_row("weak", square=False, score=99)
    generic_family_seen = _diagnostic_row("generic_seen", square=True, exact_divisors=[], term_count=8, score=98)
    generic_family_fresh = _diagnostic_row("generic_fresh", square=True, exact_divisors=[], term_count=8, score=97)
    accepted = _diagnostic_row("accepted", square=True, score=96)
    fresh = _diagnostic_row("fresh", square=True, score=95)
    feedback_rows = [{"canonical_hash": "generic_seen", "verified_group_label": "24T25000", "r": 4, "status": "accepted"}]
    rules, by_hash = build_negative_family_rules(
        [exhausted, weak, generic_family_seen, generic_family_fresh, accepted, fresh],
        feedback_rows,
        pair_status={"24T25000|r=4": {"status": "accepted"}},
        target_r=4,
    )

    annotated, selected, skipped = mine_records(
        [exhausted, weak, generic_family_seen, generic_family_fresh, accepted, fresh],
        excluded_hashes={"exhausted"},
        known_by_hash={"accepted": {"known_exact_label": "24T9683", "known_exact_pair_key": "24T9683|r=4"}},
        pair_status={"24T9683|r=4": {"status": "accepted"}, "24T25000|r=4": {"status": "accepted"}},
        baseline_pairs=set(),
        negative_family_rules=rules,
        sair_feedback_by_hash=by_hash,
        target_r=4,
        limit=10,
    )
    by_hash = {row["canonical_hash"]: row for row in annotated}

    assert by_hash["exhausted"]["mine_filter_reason"] == "exhausted_pool_hash"
    assert by_hash["weak"]["mine_filter_reason"] == "missing_strong_anti_s24_evidence"
    assert by_hash["generic_seen"]["mine_filter_reason"] == "sair_feedback_generic_hash"
    assert by_hash["generic_fresh"]["mine_filter_reason"] == "sair_generic_prone_family"
    assert by_hash["accepted"]["mine_filter_reason"] == "known_exact_accepted_pair"
    assert [row["canonical_hash"] for row in selected] == ["fresh"]
    assert skipped["sair_generic_prone_family"] == 1


def test_write_outputs_creates_mining_artifacts(tmp_path):
    selected = [_diagnostic_row("fresh")]
    selected[0]["fresh_mining_family_key"] = diagnostic_family_key(selected[0])
    selected[0]["strong_anti_s24_evidence"] = True
    selected[0]["strong_anti_s24_mining_rank"] = 1
    summary = build_summary(
        diagnostic_paths=["diagnostic.jsonl"],
        excluded_hash_paths=[],
        feedback_paths=[],
        known_paths=[],
        sair_feedback_inputs=[],
        pair_status_info={"records": 0},
        baseline_info={"pairs": 0},
        negative_family_rules={},
        annotated=selected,
        selected=selected,
        skipped_counts={},
        output_dir=tmp_path / "mine",
        command=["python3", "scripts/igp24_strong_anti_s24_mine.py"],
        source_commit="abc123",
        options={"target_r": 4, "limit": 1},
    )

    paths = write_outputs(selected=selected, summary=summary, output_dir=tmp_path / "mine")

    assert json.loads(paths["mined_jsonl"].read_text(encoding="utf-8").splitlines()[0])["canonical_hash"] == "fresh"
    assert json.loads(paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()[0])[-1] == 1
    assert "Strong Anti-S24 Saved Mining" in paths["report_md"].read_text(encoding="utf-8")
