import json

import pytest

import scripts.igp24_build_group_cycle_index as build_group_cycle_index
from scripts.igp24_build_group_cycle_index import (
    gap_program,
    import_rows_into_index,
    load_import_rows,
    main as build_index_main,
    write_dependency_report,
    write_gap_export_programs,
)
from scripts.igp24_candidate_group_compatibility import main as compatibility_main
from src.igp24.group_compatibility import (
    DEGREE,
    GroupCycleIndex,
    GroupRecord,
    candidate_compatibility,
    cycle_type_key,
    progress_states_for_pairs,
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
    assert result["index_scope"] == "target_subset"
    assert result["global_index_complete"] is False
    assert result["unindexed_label_mass_unknown"] is True
    assert result["indexed_target_survivor_count"] == 2
    assert result["indexed_target_labels_not_ruled_out"] == ["24T2", "24T3"]
    assert result["compatible_label_count_deprecated"] is True
    assert result["compatible_labels"] == ["24T2", "24T3"]
    assert result["compatible_uncovered_pairs"] == ["24T2|r=8"]
    assert result["compatible_crowded_pairs"] == ["24T3|r=8"]
    assert result["crowded_only"] is False
    assert result["evidence"]["cycle_types"] == ["1.23", "3.21"]


def test_candidate_compatibility_missing_progress_is_not_uncovered(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")

    result = candidate_compatibility(_candidate_row(), index, progress_rows=[])

    assert result["status"] == "ok"
    assert result["compatible_uncovered_pairs"] == []
    assert result["compatible_low_team_pairs"] == []
    assert result["valuable_targets_not_ruled_out"] == []
    assert set(result["compatible_unknown_or_no_score_pairs"]) == {"24T2|r=8", "24T3|r=8"}
    assert all(
        item["progress_state"] == "progress_data_missing_unknown"
        for item in result["progress_states"].values()
    )


def test_candidate_compatibility_signature_not_allowed_has_no_score_value(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    progress = [{"label": "24T2", "allowedR": [4], "signatures": [{"r": 4, "discovered": False, "teamCount": 0}]}]

    result = candidate_compatibility(_candidate_row(), index, progress_rows=progress)

    assert "24T2|r=8" in result["compatible_unknown_or_no_score_pairs"]
    assert result["progress_states"]["24T2|r=8"]["progress_state"] == "signature_not_allowed"
    assert "24T2|r=8" not in result["compatible_uncovered_pairs"]


def test_progress_states_for_pairs_public_helper_keeps_unknown_and_not_allowed_distinct():
    progress = [{"label": "24T2", "allowedR": [4], "signatures": [{"r": 4, "discovered": False, "teamCount": 0}]}]

    states = progress_states_for_pairs(["24T2|r=8", "24T999|r=8"], progress)

    assert states["24T2|r=8"]["progress_state"] == "signature_not_allowed"
    assert states["24T2|r=8"]["score_value_status"] == "no_score_value"
    assert states["24T999|r=8"]["progress_state"] == "progress_data_missing_unknown"
    assert states["24T999|r=8"]["score_value_status"] == "unknown_no_score_value"


def test_discriminant_square_applies_sound_even_group_filter(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    row = _candidate_row()
    row["discriminant"] = 49

    result = candidate_compatibility(row, index)

    assert result["compatible_labels"] == ["24T3"]
    assert result["evidence"]["parity_filter_applied"] is True


def test_square_field_discriminant_does_not_apply_parity_filter(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    row = _candidate_row()
    row.pop("discriminant", None)
    row["field_disc_abs"] = 49

    result = candidate_compatibility(row, index)

    assert result["compatible_labels"] == ["24T2", "24T3"]
    assert result["evidence"]["parity_filter_applied"] is False
    assert result["evidence"]["parity_filter_status"] == "polynomial_discriminant_missing"
    assert result["evidence"]["polynomial_discriminant_source"] is None


def test_historical_containment_reports_failures(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    rows = [_candidate_row("24T2"), _candidate_row("24T1")]

    result = validate_historical_containment(rows, index)

    assert result["checked_count"] == 2
    assert result["failure_count"] == 1
    assert result["failures"][0]["label"] == "24T1"


def test_historical_containment_marks_true_label_outside_partial_index_as_unknown_mass(tmp_path):
    index = _build_fixture_index(tmp_path / "groups.sqlite")
    rows = [_candidate_row("24T24932")]

    result = validate_historical_containment(rows, index)

    assert result["checked_count"] == 1
    assert result["indexed_true_label_checked_count"] == 0
    assert result["true_label_outside_index_count"] == 1
    assert result["failure_count"] == 0
    assert result["true_label_containment"] is None
    assert result["checked_rows"][0]["true_label_indexed"] is False
    assert result["checked_rows"][0]["unindexed_label_mass_unknown"] is True


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
        group_compatibility={"indexed_target_labels_not_ruled_out": ["24T2"], "indexed_target_survivor_count": 1},
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
    compatibility = json.loads(rows[0])["group_compatibility"]
    assert compatibility["indexed_target_survivor_count"] == 2
    assert compatibility["compatible_label_count_deprecated"] is True


def test_gap_dependency_report_never_claims_approximation(tmp_path):
    report = write_dependency_report(tmp_path, gap_path=None, note="missing in test")
    assert report["status"] == "blocked_missing_gap"
    assert report["no_approximation_written"] is True
    assert (tmp_path / "gap_dependency_report.md").exists()


def test_gap_program_exports_block_sizes_and_cycle_types():
    program = gap_program(["24T1", "24T2"])

    assert "AllBlocks(g)" in program
    assert "AllBlocks(g, " not in program
    assert "IsPrimitive(g)" in program
    assert "CycleLengths(rep," in program
    assert "CycleLengthsPerm" not in program
    assert "SizeScreen([1000000, 1000000]);" in program
    assert '\\"block_sizes\\":[' in program
    assert '\\"cycle_types\\":[' in program
    assert "TransitiveGroup(24, t)" in program


def test_write_gap_export_programs_is_chunked_and_read_only(tmp_path):
    manifest = write_gap_export_programs(
        tmp_path,
        ["24T1", "24T2", "24T3"],
        chunk_size=2,
        source_commit="test-commit",
    )

    assert manifest["record_type"] == "igp24_gap_group_cycle_export_manifest"
    assert manifest["program_count"] == 2
    assert manifest["complete_degree24_universe_requested"] is False
    assert manifest["safety"]["calls_sair"] is False
    assert manifest["safety"]["writes_repo_index"] is False
    assert (tmp_path / "degree24_group_cycle_export_0001_1_2.g").exists()
    assert (tmp_path / "degree24_group_cycle_export_0002_3_3.g").exists()
    saved = json.loads((tmp_path / "gap_export_manifest.json").read_text(encoding="utf-8"))
    assert saved["labels"] == ["24T1", "24T2", "24T3"]
    assert saved["programs"][0]["labels"] == ["24T1", "24T2"]
    assert saved["programs"][0]["completion_status"] == "not_started"


def test_load_import_rows_accepts_json_array_jsonl_and_wrapped_rows(tmp_path):
    row = {
        "label": "24T1",
        "t": 1,
        "group_order": "24",
        "primitive": False,
        "solvable": True,
        "parity": "mixed",
        "block_sizes": [2, 12],
        "cycle_types": ["1.23", "24"],
    }
    array_path = tmp_path / "rows.json"
    array_path.write_text(json.dumps([row]), encoding="utf-8")
    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    wrapped_path = tmp_path / "wrapped.json"
    wrapped_path.write_text(json.dumps({"groups": [row]}), encoding="utf-8")

    assert load_import_rows(array_path) == [row]
    assert load_import_rows(jsonl_path) == [row]
    assert load_import_rows(wrapped_path) == [row]


def test_group_cycle_index_builder_imports_gap_rows_without_running_gap(tmp_path):
    rows_path = tmp_path / "gap_rows.jsonl"
    rows_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "label": "24T1",
                        "t": 1,
                        "group_order": "24",
                        "primitive": False,
                        "solvable": True,
                        "parity": "mixed",
                        "block_sizes": [2, 12],
                        "cycle_types": ["1.23", "24"],
                    }
                ),
                json.dumps(
                    {
                        "label": "24T2",
                        "t": 2,
                        "group_order": "48",
                        "primitive": True,
                        "solvable": False,
                        "parity": "mixed",
                        "block_sizes": [],
                        "cycle_types": ["1.23", "3.21"],
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    index_path = tmp_path / "degree24.sqlite"
    output_dir = tmp_path / "out"

    assert (
        build_index_main(
            [
                "--import_rows",
                str(rows_path),
                "--index",
                str(index_path),
                "--output_dir",
                str(output_dir),
            ]
        )
        == 0
    )

    index = GroupCycleIndex(index_path)
    records = index.records_for_labels(["24T1", "24T2"])
    assert records["24T1"].block_sizes == (2, 12)
    assert records["24T2"].primitive is True
    assert index.labels_for_cycle_type("1.23") == {"24T1", "24T2"}
    summary = json.loads((output_dir / "group_cycle_index_import_summary.json").read_text(encoding="utf-8"))
    assert summary["rows_imported"] == 2
    assert summary["group_count"] == 2
    assert summary["integrity"]["integrity_ok"] is True


def test_group_cycle_index_import_rejects_duplicate_labels(tmp_path):
    row = {
        "label": "24T1",
        "t": 1,
        "group_order": "24",
        "primitive": False,
        "solvable": True,
        "parity": "mixed",
        "block_sizes": [2, 12],
        "cycle_types": ["1.23"],
    }

    with pytest.raises(ValueError, match="integrity check failed"):
        import_rows_into_index(
            [row, dict(row)],
            GroupCycleIndex(tmp_path / "degree24.sqlite"),
            import_source=None,
        )


def test_group_cycle_index_import_rejects_missing_expected_labels(tmp_path):
    row = {
        "label": "24T1",
        "t": 1,
        "group_order": "24",
        "primitive": False,
        "solvable": True,
        "parity": "mixed",
        "block_sizes": [2, 12],
        "cycle_types": ["1.23"],
    }

    with pytest.raises(ValueError, match="missing_expected_labels"):
        import_rows_into_index(
            [row],
            GroupCycleIndex(tmp_path / "degree24.sqlite"),
            import_source=None,
            expected_labels=["24T1", "24T2"],
        )


def test_group_cycle_index_import_marks_complete_universe_when_expected_labels_match(tmp_path, monkeypatch):
    monkeypatch.setattr(build_group_cycle_index, "EXPECTED_GLOBAL_GROUP_COUNT", 3)
    rows = [
        {
            "label": f"24T{number}",
            "t": number,
            "group_order": "24",
            "primitive": False,
            "solvable": True,
            "parity": "mixed",
            "block_sizes": [2, 12],
            "cycle_types": ["1.23"],
        }
        for number in range(1, 4)
    ]
    index = GroupCycleIndex(tmp_path / "degree24.sqlite")

    summary = build_group_cycle_index.import_rows_into_index(
        rows,
        index,
        import_source=None,
        expected_labels=["24T1", "24T2", "24T3"],
    )

    metadata = index.metadata()
    assert summary["index_scope"] == "complete_degree24_universe"
    assert summary["global_index_complete"] is True
    assert metadata["index_scope"] == "complete_degree24_universe"
    assert metadata["global_index_complete"] is True
    assert metadata["expected_global_group_count"] == 3
    assert index.scope_metadata()["unindexed_label_mass_unknown"] is False


def test_group_cycle_index_builder_strict_import_rejects_missing_labels(tmp_path):
    rows_path = tmp_path / "gap_rows.jsonl"
    rows_path.write_text(
        json.dumps(
            {
                "label": "24T1",
                "t": 1,
                "group_order": "24",
                "primitive": False,
                "solvable": True,
                "parity": "mixed",
                "block_sizes": [2, 12],
                "cycle_types": ["1.23"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing_expected_labels"):
        build_index_main(
            [
                "--import_rows",
                str(rows_path),
                "--labels",
                "1-2",
                "--strict_expected_labels",
                "--index",
                str(tmp_path / "degree24.sqlite"),
                "--output_dir",
                str(tmp_path / "out"),
            ]
        )
