import json

from scripts.igp24_active_learning_dataset import (
    DEFAULT_COLLAPSED_LABELS,
    build_dataset,
    derive_class_label,
    derive_score_aware_label,
)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_derive_class_label_prefers_score_positive_pair():
    assert (
        derive_class_label(
            label="24T9993",
            pair="24T9993|r=8",
            r_value=8,
            local_exact_valid=True,
            target_rs={8},
            known_status="accepted",
            scoreable=True,
            points_numeric=0.0019,
            progress_label={"fully_covered": False},
            signature_team_count=10,
            label_team_count=10,
            collapsed_labels=DEFAULT_COLLAPSED_LABELS,
            score_positive_pairs={"24T9993|r=8"},
            high_team_threshold=20,
        )
        == "accepted_useful_score_positive"
    )


def test_derive_class_label_marks_collapsed_label_even_when_pending():
    assert (
        derive_class_label(
            label="24T25000",
            pair="24T25000|r=20",
            r_value=20,
            local_exact_valid=True,
            target_rs={20},
            known_status="accepted",
            scoreable=False,
            points_numeric=None,
            progress_label={"fully_covered": False},
            signature_team_count=3,
            label_team_count=5,
            collapsed_labels=DEFAULT_COLLAPSED_LABELS,
            score_positive_pairs=set(),
            high_team_threshold=20,
        )
        == "accepted_duplicate_collapsed_basin"
    )


def test_derive_class_label_marks_wrong_target_r_before_exact_valid():
    assert (
        derive_class_label(
            label=None,
            pair=None,
            r_value=4,
            local_exact_valid=True,
            target_rs={8},
            known_status=None,
            scoreable=None,
            points_numeric=None,
            progress_label={},
            signature_team_count=0,
            label_team_count=0,
            collapsed_labels=set(),
            score_positive_pairs=set(),
            high_team_threshold=20,
        )
        == "wrong_real_root_count"
    )


def test_derive_score_aware_label_prefers_real_score_signal():
    assert (
        derive_score_aware_label(
            label="24T9993",
            pair="24T9993|r=8",
            r_value=8,
            local_exact_valid=True,
            target_rs={8},
            known_status="accepted",
            scoreable=True,
            points_numeric=0.0019,
            progress_label={"fully_covered": False},
            progress_pair={"discovered": True, "remaining": False},
            signature_team_count=10,
            label_team_count=10,
            collapsed_labels=DEFAULT_COLLAPSED_LABELS,
            score_positive_pairs={"24T9993|r=8"},
            high_team_threshold=20,
        )
        == "score_positive"
    )


def test_derive_score_aware_label_marks_crowded_collapse_before_duplicate():
    assert (
        derive_score_aware_label(
            label="24T25000",
            pair="24T25000|r=24",
            r_value=24,
            local_exact_valid=True,
            target_rs={24},
            known_status="accepted",
            scoreable=True,
            points_numeric=None,
            progress_label={"fully_covered": False},
            progress_pair={"discovered": True, "remaining": False},
            signature_team_count=2,
            label_team_count=2,
            collapsed_labels=DEFAULT_COLLAPSED_LABELS,
            score_positive_pairs=set(),
            high_team_threshold=20,
        )
        == "accepted_but_crowded_collapse"
    )


def test_derive_score_aware_label_separates_low_team_scoreable_from_duplicate():
    low_team = derive_score_aware_label(
        label="24T4242",
        pair="24T4242|r=16",
        r_value=16,
        local_exact_valid=True,
        target_rs={16},
        known_status="accepted",
        scoreable=True,
        points_numeric=None,
        progress_label={"fully_covered": False},
        progress_pair={"discovered": True, "remaining": False},
        signature_team_count=1,
        label_team_count=1,
        collapsed_labels=DEFAULT_COLLAPSED_LABELS,
        score_positive_pairs=set(),
        high_team_threshold=20,
    )
    crowded_duplicate = derive_score_aware_label(
        label="24T4242",
        pair="24T4242|r=16",
        r_value=16,
        local_exact_valid=True,
        target_rs={16},
        known_status="accepted",
        scoreable=True,
        points_numeric=None,
        progress_label={"fully_covered": False},
        progress_pair={"discovered": True, "remaining": False},
        signature_team_count=8,
        label_team_count=8,
        collapsed_labels=DEFAULT_COLLAPSED_LABELS,
        score_positive_pairs=set(),
        high_team_threshold=20,
    )

    assert low_team == "low_team_scoreable"
    assert crowded_duplicate == "accepted_duplicate"


def test_build_dataset_joins_candidate_to_sync_and_pair_status(tmp_path):
    candidate_path = tmp_path / "candidate_queue.jsonl"
    coeffs = [2, 1] + [0] * 22 + [1]
    _write_jsonl(
        candidate_path,
        [
            {
                "canonical_hash": "hash-positive",
                "exported_coefficients": coeffs,
                "real_root_count": 8,
                "valid": True,
                "irreducible": True,
                "squarefree": True,
                "generation_metadata": {"source_family": "unit_test_family"},
            }
        ],
    )
    pair_status_path = tmp_path / "pair_status.json"
    _write_json(
        pair_status_path,
        {
            "pairs": [
                {
                    "pair_key": "24T9993|r=8",
                    "label": "24T9993",
                    "r": 8,
                    "canonical_hash": "hash-positive",
                    "leaderboard_scoring": {"points_numeric": 0.0019},
                }
            ]
        },
    )
    sync_dir = tmp_path / "sync"
    _write_jsonl(
        sync_dir / "sair_submission_rows.jsonl",
        [
            {
                "canonical_hash": "hash-positive",
                "label": "24T9993",
                "pair_key": "24T9993|r=8",
                "r": 8,
                "status": "accepted",
                "scoreable": True,
            }
        ],
    )
    _write_jsonl(
        sync_dir / "sair_label_progress.jsonl",
        [
            {
                "label": "24T9993",
                "t": 9993,
                "teamCount": 10,
                "allowedR": [8],
                "discoveredSignatures": [8],
                "remainingSignatures": [],
                "signatures": [{"r": 8, "teamCount": 10, "discovered": True}],
            }
        ],
    )

    rows, summary = build_dataset(
        candidate_paths=[candidate_path],
        feedback_paths=[],
        pair_status_path=pair_status_path,
        sair_sync_dir=sync_dir,
        target_rs={8},
        collapsed_labels=DEFAULT_COLLAPSED_LABELS,
        score_positive_pairs={"24T9993|r=8"},
        high_team_threshold=20,
    )

    assert len(rows) == 2
    candidate = next(row for row in rows if row["source_role"] == "candidate_queue")
    assert candidate["derived_class_label"] == "accepted_useful_score_positive"
    assert candidate["score_aware_supervision"]["label"] == "score_positive"
    assert candidate["score_aware_supervision"]["reward"] > 0
    assert candidate["generator_training"]["eligible"] is True
    assert candidate["generator_training"]["role"] == "score_positive"
    assert candidate["generator_training"]["weight"] == 12.0
    assert candidate["sair_feedback"]["label"] == "24T9993"
    assert summary["class_counts"]["accepted_useful_score_positive"] == 2
    assert summary["score_aware_class_counts"]["score_positive"] == 2
    assert summary["generator_training"]["eligible_row_count"] == 2
    assert summary["generator_training"]["sampling_mass_by_role"]["score_positive"] == 24.0


def test_build_dataset_loads_feedback_rows_and_marks_collapsed(tmp_path):
    feedback_path = tmp_path / "accepted_feedback.json"
    _write_json(
        feedback_path,
        {
            "accepted_rows": [
                {
                    "canonical_hash": "hash-collapsed",
                    "exported_coefficients": [2, 1] + [0] * 22 + [1],
                    "label": "24T25000",
                    "pair_key": "24T25000|r=20",
                    "r": 20,
                    "status": "accepted",
                    "irreducible": True,
                    "squarefree": True,
                }
            ]
        },
    )

    rows, summary = build_dataset(
        candidate_paths=[],
        feedback_paths=[feedback_path],
        pair_status_path=None,
        sair_sync_dir=None,
        target_rs={20},
        collapsed_labels=DEFAULT_COLLAPSED_LABELS,
        score_positive_pairs=set(),
        high_team_threshold=20,
    )

    assert rows[0]["source_role"] == "accepted_feedback"
    assert rows[0]["derived_class_label"] == "accepted_duplicate_collapsed_basin"
    assert rows[0]["score_aware_supervision"]["label"] == "accepted_but_crowded_collapse"
    assert rows[0]["score_aware_supervision"]["avoid_for_generation"] is True
    assert rows[0]["generator_training"]["eligible"] is False
    assert rows[0]["generator_training"]["role"] == "crowded_collapse"
    assert rows[0]["generator_training"]["weight"] == 0.0
    assert summary["class_counts"] == {"accepted_duplicate_collapsed_basin": 1}
    assert summary["generator_training"]["eligible_row_count"] == 0
