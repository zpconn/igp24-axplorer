import json

from scripts.igp24_score1_target_analysis import (
    annotate_targets,
    label_band,
    load_score1_snapshot,
    select_saved_candidates,
    write_outputs,
)


def _diagnostic(hash_value, *, r=0, square=True, exact=True, score=100.0):
    flags = ["near_composed_support"]
    if square:
        flags.append("square_discriminant_excludes_s24")
    block = {"exact_block_divisors": [2] if exact else [], "nonzero_term_count": 5}
    return {
        "canonical_hash": hash_value,
        "exported_coefficients": [1] + [0] * 23 + [1],
        "real_root_count": r,
        "source_strategy": "structured",
        "score": score,
        "non_generic_score": score,
        "non_generic_flags": flags,
        "non_generic_evidence": {
            "square_discriminant": square,
            "block_structure": block,
        },
    }


def test_label_band_for_low_score1_labels():
    assert label_band("24T105") == "00001-00499"
    assert label_band("24T21844") == "20000-25000"
    assert label_band(None) == "unknown"


def test_load_score1_snapshot_normalizes_pairs(tmp_path):
    path = tmp_path / "score1.json"
    path.write_text(
        json.dumps({"rows": [{"label": "24T105", "r": 12}, {"label": "106", "r": "8"}, {"label": "24T290", "r": 0}]}),
        encoding="utf-8",
    )

    rows, info = load_score1_snapshot(path)

    assert info["targets_loaded"] == 3
    assert [row["pair_key"] for row in rows] == ["24T105|r=12", "24T106|r=8", "24T290|r=0"]


def test_annotate_targets_marks_underexplored_and_baseline_status():
    targets = [
        {"label": "24T105", "r": 12, "pair_key": "24T105|r=12", "snapshot_rank": 1},
        {"label": "24T290", "r": 0, "pair_key": "24T290|r=0", "snapshot_rank": 2},
    ]

    rows = annotate_targets(
        targets,
        baseline_pairs={"24T105|r=12": {"baseline_scoring_disc": "nfdisc"}},
        pair_status={"24T290|r=0": {"status": "accepted"}},
        feedback_pair_counts={},
        saved_r_counts={0: 5},
    )
    by_pair = {row["pair_key"]: row for row in rows}

    assert by_pair["24T105|r=12"]["in_baseline"] is True
    assert by_pair["24T105|r=12"]["signature_underexplored"] is True
    assert by_pair["24T105|r=12"]["generator_plausibility"] == "needs_targeted_generation"
    assert by_pair["24T290|r=0"]["local_pair_status"] == "accepted"
    assert by_pair["24T290|r=0"]["generator_plausibility"] == "saved_candidates_present"


def test_select_saved_candidates_requires_target_signature_and_strong_proxy():
    selected, skipped = select_saved_candidates(
        [
            _diagnostic("good", r=0, square=True, score=10),
            _diagnostic("known", r=0, square=True, score=9),
            _diagnostic("wrong_r", r=4, square=True, score=8),
            _diagnostic("weak", r=0, square=False, exact=False, score=7),
        ],
        target_rs={0, 8, 12},
        known_hashes={"known"},
        feedback_hashes=set(),
        limit=10,
    )

    assert [row["canonical_hash"] for row in selected] == ["good"]
    assert skipped["known_feedback_or_accepted_hash"] == 1
    assert skipped["target_r_mismatch"] == 1
    assert skipped["weak_proxy_evidence"] == 1
    assert selected[0]["exact_label_claimed_by_helper"] is False


def test_write_outputs_creates_target_and_candidate_artifacts(tmp_path):
    targets = [{"target_rank": 1, "pair_key": "24T105|r=12", "r": 12}]
    candidates = [_diagnostic("good", r=0)]
    candidates[0]["score1_candidate_rank"] = 1
    candidates[0]["short_hash"] = "good"
    summary = {
        "target_rows": 1,
        "target_r_counts": {"12": 1},
        "target_label_band_counts": {},
        "target_baseline_presence_counts": {},
        "target_local_pair_status_counts": {},
        "target_generator_plausibility_counts": {},
        "candidate_skipped_counts": {},
        "selected_candidate_records": 1,
        "selected_candidate_r_counts": {"0": 1},
        "queue_status": "tiny_not_padded",
        "recommendation": "test",
        "output_files": {
            "target_rankings_jsonl": str(tmp_path / "score1_target_rankings.jsonl"),
            "candidate_queue_jsonl": str(tmp_path / "score1_saved_candidate_queue.jsonl"),
            "candidate_coefficients_txt": str(tmp_path / "score1_saved_candidate_coefficients.txt"),
            "summary_json": str(tmp_path / "score1_target_analysis_summary.json"),
        },
    }

    paths = write_outputs(target_rows=targets, selected_candidates=candidates, summary=summary, output_dir=tmp_path)

    assert json.loads(paths["target_rankings_jsonl"].read_text(encoding="utf-8").splitlines()[0])["pair_key"] == "24T105|r=12"
    assert json.loads(paths["candidate_queue_jsonl"].read_text(encoding="utf-8").splitlines()[0])["canonical_hash"] == "good"
    assert paths["candidate_coefficients_txt"].read_text(encoding="utf-8").strip().endswith(",1")
