import json

from scripts.igp24_shortlist import (
    build_manifest,
    load_records,
    resolve_ledger_paths,
    select_records,
    write_outputs,
)


def _record(canonical_hash, score, real_root_count=4, strategy="four_real_seed", coeff0=1):
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
        "score": score,
        "real_root_count": real_root_count,
        "log_abs_discriminant": 12.5,
        "coefficient_height": abs(coeff0),
        "score_components": {"final_score": score, "target_r_distance": 0},
        "generation_metadata": {"strategy": strategy},
        "verification_status": "proxy_scored",
        "verified_group_label": None,
        "target_metadata": {"target_t": "24T1"},
    }


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_resolve_ledger_paths_accepts_benchmark_directories_and_files(tmp_path):
    run_dir = tmp_path / "bench" / "run_a"
    ledger_path = run_dir / "candidates.jsonl"
    _write_jsonl(ledger_path, [_record("a", 10.0)])
    summary_path = tmp_path / "bench" / "summary.json"
    summary_path.write_text(json.dumps([{"ledger_path": str(ledger_path)}]), encoding="utf-8")

    assert resolve_ledger_paths([tmp_path / "bench"]) == [ledger_path.resolve()]
    assert resolve_ledger_paths([summary_path]) == [ledger_path.resolve()]
    assert resolve_ledger_paths([ledger_path]) == [ledger_path.resolve()]


def test_select_records_filters_sorts_deduplicates_and_limits(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    _write_jsonl(
        first,
        [
            _record("dup", 10.0, strategy="four_real_seed", coeff0=1),
            _record("other_target", 99.0, real_root_count=2, strategy="four_real_seed", coeff0=2),
            _record("other_strategy", 98.0, strategy="sparse", coeff0=3),
        ],
    )
    _write_jsonl(
        second,
        [
            _record("dup", 15.0, strategy="quartic_lift", coeff0=4),
            _record("keep", 12.0, strategy="four_real_seed", coeff0=5),
            _record("third", 11.0, strategy="quartic_lift", coeff0=6),
        ],
    )

    records = load_records([first, second])
    selected = select_records(
        records,
        target_r=4,
        strategies={"four_real_seed", "quartic_lift"},
        limit=2,
    )

    assert [record["canonical_hash"] for record in selected] == ["dup", "keep"]
    assert selected[0]["score"] == 15.0
    assert selected[0]["exported_coefficients"][0] == 4
    assert selected[0]["source_ledger_path"] == str(second.resolve())


def test_write_outputs_creates_manifest_shortlist_and_coefficients(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    _write_jsonl(ledger_path, [_record("a", 10.0), _record("b", 12.0, strategy="quartic_lift", coeff0=2)])
    selected = select_records(load_records([ledger_path]), target_r=4, limit=2)
    output_dir = tmp_path / "shortlist"
    manifest = build_manifest(
        input_paths=[ledger_path.resolve()],
        ledger_paths=[ledger_path.resolve()],
        output_dir=output_dir,
        selected=selected,
        total_records_loaded=2,
        filters={"target_r": 4, "strategies": [], "deduplicate_by": "canonical_hash", "limit": 2},
        sort={"sort_by": "score", "ascending": False},
        command=["python3", "scripts/igp24_shortlist.py"],
        source_commit="abc123",
    )

    paths = write_outputs(selected, output_dir, manifest)
    shortlist = [json.loads(line) for line in paths["shortlist_jsonl"].read_text(encoding="utf-8").splitlines()]
    coefficients = json.loads(paths["coefficients_json"].read_text(encoding="utf-8"))
    text_lines = paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()
    reloaded_manifest = json.loads(paths["manifest_json"].read_text(encoding="utf-8"))

    assert [record["canonical_hash"] for record in shortlist] == ["b", "a"]
    assert "source_ledger_path" in shortlist[0]
    assert "verified_group_label" not in shortlist[0]
    assert coefficients[0]["exported_coefficients"][-1] == 1
    assert json.loads(text_lines[0])[-1] == 1
    assert reloaded_manifest["selected_records"] == 2
    assert reloaded_manifest["total_records_loaded"] == 2
    assert reloaded_manifest["strategy_counts"] == {"four_real_seed": 1, "quartic_lift": 1}
    assert reloaded_manifest["safety"]["proxy_only"]
    assert not reloaded_manifest["safety"]["verifier_executed"]
    assert not reloaded_manifest["safety"]["submission_executed"]
