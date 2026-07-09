import json

from scripts.igp24_build_group_cycle_index import write_dependency_report
from scripts.igp24_candidate_group_compatibility import main as compatibility_main
from src.igp24.group_compatibility import (
    DEGREE,
    GroupCycleIndex,
    GroupRecord,
    candidate_compatibility,
    cycle_type_key,
    validate_historical_containment,
)
from src.igp24.polynomial import score_candidate

VALID = tuple([-2] + [0] * (DEGREE - 1))


def _build_fixture_index(path):
    index = GroupCycleIndex(path)
    index.initialize(provenance={"test": True})
    index.upsert_group(
        GroupRecord(
            label="24T1",
            t=1,
            order=24,
            parity="mixed",
            cycle_types=("1.23", "24"),
        )
    )
    index.upsert_group(
        GroupRecord(
            label="24T2",
            t=2,
            order=48,
            parity="mixed",
            cycle_types=("1.23", "3.21", "4.20"),
        )
    )
    index.upsert_group(
        GroupRecord(
            label="24T3",
            t=3,
            order=96,
            parity="even",
            cycle_types=("1.23", "3.21", "2.22"),
        )
    )
    return index


def _candidate_row(label=None):
    row = {
        "canonical_hash": "candidate-hash",
        "r": 8,
        "discriminant": 12345,
        "mod_p_factorization_degree_patterns": [
            {"prime": 5, "degrees": [1, 23]},
            {"prime": 7, "degrees": [3, 21]},
        ],
    }
    if label:
        row["label"] = label
    return row


def test_cycle_type_key_normalizes_and_rejects_wrong_degree():
    assert cycle_type_key([23, 1]) == "1.23"
    try:
        cycle_type_key([1, 22])
    except ValueError as exc:
        assert "invalid degree-24" in str(exc)
    else:
        raise AssertionError("wrong-degree cycle type was accepted")


def test_candidate_compatibility_intersects_cycle_types_and_pairs(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    progress = [
        {
            "label": "24T2",
            "signatures": [{"r": 8, "discovered": False, "teamCount": 0}],
        },
        {
            "label": "24T3",
            "signatures": [{"r": 8, "discovered": True, "teamCount": 30}],
        },
    ]

    result = candidate_compatibility(_candidate_row(), index, progress_rows=progress)

    assert result["status"] == "ok"
    assert result["compatible_labels"] == ["24T2", "24T3"]
    assert result["compatible_uncovered_pairs"] == ["24T2|r=8"]
    assert result["compatible_crowded_pairs"] == ["24T3|r=8"]
    assert result["crowded_only"] is False
    assert result["evidence"]["cycle_types"] == ["1.23", "3.21"]


def test_discriminant_square_applies_sound_even_group_filter(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    row = _candidate_row()
    row["discriminant"] = 49

    result = candidate_compatibility(row, index)

    assert result["compatible_labels"] == ["24T3"]
    assert result["evidence"]["parity_filter_applied"] is True


def test_historical_containment_reports_failures(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    rows = [_candidate_row("24T2"), _candidate_row("24T1")]

    result = validate_historical_containment(rows, index)

    assert result["checked_count"] == 2
    assert result["failure_count"] == 1
    assert result["failures"][0]["label"] == "24T1"


def test_score_candidate_target_label_requires_or_uses_compatibility():
    score, analysis = score_candidate(VALID, coeff_bound=5, target_t="24T2", prime_limit=7)
    assert score >= 0
    assert "target_label_not_applied_missing_group_compatibility_index" in analysis.warnings
    assert analysis.score_components["target_label_requested"] is True
    assert analysis.score_components["target_label_applied"] is False

    rejected_score, rejected = score_candidate(
        VALID,
        coeff_bound=5,
        target_label="24T1",
        group_compatibility={"compatible_labels": ["24T2"], "compatible_label_count": 1},
        prime_limit=7,
    )
    assert rejected_score == -1.0
    assert rejected.score_components["target_label_rejected"] is True
    assert "target_label_incompatible_with_group_cycle_evidence" in rejected.warnings


def test_candidate_group_compatibility_cli_outputs_summary(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    assert index.group_count() == 3
    input_path = tmp_path / "candidates.jsonl"
    input_path.write_text(json.dumps(_candidate_row("24T2")) + "\n", encoding="utf-8")
    output_dir = tmp_path / "out"

    assert (
        compatibility_main(
            [
                "--index",
                str(tmp_path / "groups.sqlite"),
                "--input_jsonl",
                str(input_path),
                "--output_dir",
                str(output_dir),
                "--historical_validation",
            ]
        )
        == 0
    )
    summary = json.loads((output_dir / "candidate_group_compatibility_summary.json").read_text(encoding="utf-8"))
    assert summary["historical_containment"]["failure_count"] == 0
    rows = (output_dir / "candidate_group_compatibility_rows.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(rows[0])["group_compatibility"]["compatible_label_count"] == 2


def test_gap_dependency_report_never_claims_approximation(tmp_path):
    report = write_dependency_report(tmp_path, gap_path=None, note="missing in test")
    assert report["status"] == "blocked_missing_gap"
    assert report["no_approximation_written"] is True
    assert (tmp_path / "gap_dependency_report.md").exists()
