import json

from scripts.igp24_next_verification_queue import (
    annotate_filter_status,
    build_summary,
    load_pair_status,
    select_queue,
    write_outputs,
)


def _record(candidate_hash, *, family="a", score=100.0, coeff0=1, label_hint=None):
    square = family.startswith("square")
    divisor = 2 if family.endswith("2") else 3
    return {
        "canonical_hash": candidate_hash,
        "short_hash": candidate_hash[:12],
        "queue_index": int(score),
        "feedback_family_match_status": "matched" if label_hint else "unmatched",
        "feedback_family_label": label_hint,
        "local_discriminant_is_square": square,
        "primary_exact_block_divisor": divisor,
        "primary_base_degree": 24 // divisor,
        "sparse_bucket": "sparse",
        "source_strategy": family,
        "non_generic_score": score,
        "score": score,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
    }


def test_load_pair_status_indexes_pairs(tmp_path):
    path = tmp_path / "pairs.json"
    path.write_text(
        json.dumps(
            {
                "pairs": [
                    {"label": "24T1", "r": 4, "status": "accepted"},
                    {"pair_key": "24T2|r=4", "status": "pending"},
                ]
            }
        ),
        encoding="utf-8",
    )

    pairs, info = load_pair_status(path)

    assert pairs["24T1|r=4"]["status"] == "accepted"
    assert pairs["24T2|r=4"]["status"] == "pending"
    assert info["status_counts"] == {"accepted": 1, "pending": 1}


def test_filter_status_respects_accepted_pending_baseline_and_generic():
    rows = [
        _record("accepted_hash", family="square2"),
        _record("pending_hash", family="square3"),
        _record("generic_hash", family="plain2", label_hint="24T25000"),
        _record("baseline_hash", family="plain3"),
        _record("eligible_hash", family="fresh2"),
    ]
    pair_status = {
        "24T9683|r=4": {"status": "accepted"},
        "24T25000|r=4": {"status": "pending"},
    }
    known_by_hash = {
        "accepted_hash": {"known_exact_label": "24T9683", "known_exact_r": 4, "known_exact_pair_key": "24T9683|r=4"},
        "pending_hash": {"known_exact_label": "24T25000", "known_exact_r": 4, "known_exact_pair_key": "24T25000|r=4"},
        "baseline_hash": {"known_exact_label": "24T1", "known_exact_r": 0, "known_exact_pair_key": "24T1|r=0"},
    }

    annotated = annotate_filter_status(
        rows,
        pair_status=pair_status,
        baseline_pairs={"24T1|r=0"},
        known_by_hash=known_by_hash,
        target_r=4,
        allow_generic_s24=False,
    )
    by_hash = {row["canonical_hash"]: row for row in annotated}

    assert by_hash["accepted_hash"]["queue_filter_reason"] == "known_exact_accepted_pair"
    assert by_hash["pending_hash"]["queue_filter_reason"] == "known_exact_pending_pair"
    assert by_hash["generic_hash"]["queue_filter_reason"] == "generic_s24_hint"
    assert by_hash["baseline_hash"]["queue_filter_reason"] == "known_exact_baseline_pair"
    assert by_hash["eligible_hash"]["queue_filter_status"] == "eligible"
    assert "not_generic_s24" in by_hash["eligible_hash"]["survived_filters"]


def test_select_queue_uses_family_cap_before_relaxing():
    rows = [
        _record("a1", family="square2", score=100, coeff0=1),
        _record("a2", family="square2", score=99, coeff0=2),
        _record("b1", family="plain3", score=98, coeff0=3),
    ]
    annotated = annotate_filter_status(
        rows,
        pair_status={},
        baseline_pairs=set(),
        known_by_hash={},
        target_r=4,
        allow_generic_s24=False,
    )

    selected = select_queue(annotated, limit=3, max_per_structural_family=1)

    assert [row["canonical_hash"] for row in selected] == ["a1", "b1", "a2"]
    assert [row["next_queue_selection_phase"] for row in selected] == [
        "primary_family_cap",
        "primary_family_cap",
        "relaxed_family_cap",
    ]


def test_write_outputs_creates_queue_and_coefficients(tmp_path):
    selected = [
        _record("a1", family="square2", score=100, coeff0=7)
        | {
            "next_queue_rank": 1,
            "next_queue_selection_phase": "primary_family_cap",
            "next_queue_selection_reason": "test",
            "queue_filter_status": "eligible",
            "structural_family_key": "family",
        }
    ]
    summary = build_summary(
        structure_path=tmp_path / "structure.jsonl",
        feedback_paths=[],
        known_paths=[],
        candidate_paths=[],
        pair_status_info={"path": "pairs.json", "records": 0},
        baseline_info={"baseline_loaded": True, "pairs": 0},
        family_rules={},
        annotated=selected,
        selected=selected,
        output_dir=tmp_path / "out",
        command=["python3", "scripts/igp24_next_verification_queue.py"],
        source_commit="abc123",
        options={"limit": 1},
    )

    paths = write_outputs(selected=selected, summary=summary, output_dir=tmp_path / "out")

    assert json.loads(paths["queue_jsonl"].read_text(encoding="utf-8").splitlines()[0])["canonical_hash"] == "a1"
    assert paths["coefficients_txt"].read_text(encoding="utf-8").strip() == "[7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]"
    assert "IGP24 Next Verification Queue" in paths["report_md"].read_text(encoding="utf-8")
