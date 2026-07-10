import json

from scripts.igp24_run_gap_group_index_workflow import main as workflow_main


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _manifest(tmp_path, labels):
    program = tmp_path / "degree24_group_cycle_export_0001.g"
    program.write_text("QUIT;\n", encoding="utf-8")
    manifest = tmp_path / "gap_export_manifest.json"
    _write_json(
        manifest,
        {
            "record_type": "igp24_gap_group_cycle_export_manifest",
            "label_count": len(labels),
            "labels": labels,
            "program_count": 1,
            "programs": [
                {
                    "path": str(program),
                    "chunk_index": 1,
                    "label_count": len(labels),
                    "first_label": labels[0],
                    "last_label": labels[-1],
                }
            ],
        },
    )
    return manifest, program


def _gap_rows():
    return [
        {
            "label": "24T101",
            "t": 101,
            "degree": 24,
            "group_order": "24",
            "primitive": False,
            "solvable": True,
            "parity": "mixed",
            "block_sizes": [2, 12],
            "status": "complete",
            "cycle_types": ["1.23", "2.22"],
        },
        {
            "label": "24T102",
            "t": 102,
            "degree": 24,
            "group_order": "48",
            "primitive": True,
            "solvable": False,
            "parity": "mixed",
            "block_sizes": [],
            "status": "complete",
            "cycle_types": ["24"],
        },
    ]


def _score_plan(path):
    _write_json(
        path,
        {
            "record_type": "igp24_score_aware_target_plan",
            "created_at": "2026-07-09T00:00:00+00:00",
            "ranked_targets": [
                {
                    "pair_key": "24T101|r=16",
                    "label": "24T101",
                    "t": 101,
                    "r": 16,
                    "category": "uncovered_signature",
                    "progress_state": "remaining",
                    "target_score": 500.0,
                    "maximum_possible_points": 1.0,
                    "estimated_expected_points": 1.0,
                    "score_ceiling_class": "uncovered_first_team_one_point",
                    "signature_team_count": 0,
                },
                {
                    "pair_key": "24T102|r=24",
                    "label": "24T102",
                    "t": 102,
                    "r": 24,
                    "category": "uncovered_signature",
                    "progress_state": "remaining",
                    "target_score": 450.0,
                    "maximum_possible_points": 1.0,
                    "estimated_expected_points": 1.0,
                    "score_ceiling_class": "uncovered_first_team_one_point",
                    "signature_team_count": 0,
                },
            ],
        },
    )
    return path


def _historical_rows(path):
    _write_jsonl(
        path,
        [
            {
                "canonical_hash": "hist-a",
                "label": "24T101",
                "r": 16,
                "discriminant": 12345,
                "mod_p_factorization_degree_patterns": [{"prime": 5, "degrees": [1, 23]}],
            }
        ],
    )
    return path


def test_gap_workflow_reports_blocked_without_gap_or_captured_outputs(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "")
    manifest, _program = _manifest(tmp_path, ["24T101"])
    output_dir = tmp_path / "workflow"
    index_path = tmp_path / "groups.sqlite"

    assert (
        workflow_main(
            [
                "--manifest",
                str(manifest),
                "--output_dir",
                str(output_dir),
                "--index",
                str(index_path),
                "--skip_readiness",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "gap_group_index_workflow_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "blocked_missing_gap_outputs"
    assert summary["blocking_reasons"] == ["missing_gap_and_missing_captured_outputs"]
    assert summary["no_approximation_written"] is True
    assert summary["program_status_counts"] == {"blocked_missing_gap_output": 1}
    assert not index_path.exists()


def test_gap_workflow_imports_captured_outputs_and_runs_readiness(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "")
    manifest, program = _manifest(tmp_path, ["24T101", "24T102"])
    output_dir = tmp_path / "workflow"
    captured_output = output_dir / "gap_outputs" / f"{program.stem}.json"
    _write_json(captured_output, _gap_rows())
    score_plan = _score_plan(tmp_path / "score_plan.json")
    historical = _historical_rows(tmp_path / "historical.jsonl")
    index_path = tmp_path / "groups.sqlite"

    assert (
        workflow_main(
            [
                "--manifest",
                str(manifest),
                "--output_dir",
                str(output_dir),
                "--index",
                str(index_path),
                "--score_plan",
                str(score_plan),
                "--historical_jsonl",
                str(historical),
                "--top_targets",
                "2",
                "--families_per_target",
                "8",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "gap_group_index_workflow_summary.json").read_text(encoding="utf-8"))
    assert summary["program_status_counts"] == {"loaded_existing_output": 1}
    assert summary["rows_imported"] == 2
    assert summary["group_count"] == 2
    assert summary["structurally_eligible_route_count"] > 0
    assert summary["generation_ready_route_count"] == 0
    assert summary["ready_for_structural_route_review"] is True
    assert summary["ready_for_group_directed_generation"] is False
    assert summary["readiness_blocking_reasons"] == ["no_executable_generation_ready_routes"]
    readiness = json.loads((output_dir / "readiness/group_index_readiness_summary.json").read_text(encoding="utf-8"))
    assert readiness["historical_containment"]["failure_count"] == 0
    assert readiness["ready_for_structural_route_review"] is True
    assert readiness["ready_for_group_directed_generation"] is False


def test_gap_workflow_passes_library_path_to_gap_runner(tmp_path):
    manifest, _program = _manifest(tmp_path, ["24T101"])
    output_dir = tmp_path / "workflow"
    index_path = tmp_path / "groups.sqlite"
    args_path = tmp_path / "gap_args.txt"
    fake_gap = tmp_path / "fake_gap.sh"
    fake_gap.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$@\" > {args_path}\n"
        "cat <<'JSON'\n"
        "[{\"label\":\"24T101\",\"t\":101,\"degree\":24,\"group_order\":\"24\","
        "\"primitive\":false,\"solvable\":true,\"parity\":\"mixed\","
        "\"block_sizes\":[2,12],\"status\":\"complete\",\"cycle_types\":[\"1.23\"]}]\n"
        "JSON\n",
        encoding="utf-8",
    )
    fake_gap.chmod(0o755)
    library_path = tmp_path / "gaplib"
    library_path.mkdir()

    assert (
        workflow_main(
            [
                "--manifest",
                str(manifest),
                "--output_dir",
                str(output_dir),
                "--index",
                str(index_path),
                "--gap_path",
                str(fake_gap),
                "--gap_library_path",
                str(library_path),
                "--skip_readiness",
            ]
        )
        == 0
    )

    summary = json.loads((output_dir / "gap_group_index_workflow_summary.json").read_text(encoding="utf-8"))
    assert summary["program_status_counts"] == {"ran_gap": 1}
    assert summary["rows_imported"] == 1
    assert summary["gap_library_path"] == str(library_path)
    args = args_path.read_text(encoding="utf-8").splitlines()
    assert args[:2] == ["-l", str(library_path)]
    assert "-q" in args
