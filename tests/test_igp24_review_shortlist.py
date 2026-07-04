import json

from scripts.igp24_review_shortlist import (
    PROXY_CAVEAT,
    build_manifest,
    hydrate_from_source_ledgers,
    load_shortlist,
    select_review_batch,
    write_review_outputs,
)


def _record(canonical_hash, score, real_root_count=4, strategy="quartic_lift", coeff0=1):
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
        "score": score,
        "real_root_count": real_root_count,
        "log_abs_discriminant": 20.0 + coeff0,
        "coefficient_height": abs(coeff0),
        "score_components": {"final_score": score, "target_r_distance": 0},
        "generation_metadata": {"strategy": strategy, "seed_template": "fixture"},
        "target_metadata": {"target_r": real_root_count, "target_t": "24T1"},
        "verification_status": "proxy_scored",
        "verified_group_label": None,
    }


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_load_shortlist_and_hydrate_from_source_ledger(tmp_path):
    ledger_path = tmp_path / "source" / "candidates.jsonl"
    full_record = _record("a", 11.0, strategy="four_real_seed", coeff0=2)
    full_record["polynomial_string"] = "x**24 + 2"
    _write_jsonl(ledger_path, [full_record])

    shortlist_dir = tmp_path / "shortlist"
    shortlist_record = _record("a", 10.0, strategy="quartic_lift", coeff0=1)
    shortlist_record["source_ledger_path"] = str(ledger_path)
    _write_jsonl(shortlist_dir / "shortlist.jsonl", [shortlist_record])
    (shortlist_dir / "manifest.json").write_text(json.dumps({"selected_records": 1}), encoding="utf-8")

    records, shortlist_path, manifest = load_shortlist(shortlist_dir)
    hydrated = hydrate_from_source_ledgers(records)

    assert shortlist_path == (shortlist_dir / "shortlist.jsonl").resolve()
    assert manifest["selected_records"] == 1
    assert hydrated[0]["score"] == 11.0
    assert hydrated[0]["shortlist_score"] == 10.0
    assert hydrated[0]["generation_metadata"]["strategy"] == "four_real_seed"
    assert hydrated[0]["source_ledger_path"] == str(ledger_path.resolve())
    assert hydrated[0]["source_shortlist_path"] == str(shortlist_path)
    assert hydrated[0]["polynomial_string"] == "x**24 + 2"


def test_select_review_batch_balances_strategy_when_possible():
    records = [
        _record("q1", 20.0, strategy="quartic_lift", coeff0=1),
        _record("q2", 19.0, strategy="quartic_lift", coeff0=2),
        _record("q3", 18.0, strategy="quartic_lift", coeff0=3),
        _record("q4", 17.0, strategy="quartic_lift", coeff0=4),
        _record("f1", 12.0, strategy="four_real_seed", coeff0=5),
        _record("q1", 10.0, strategy="four_real_seed", coeff0=6),
    ]

    selected = select_review_batch(records, batch_size=4, per_strategy_cap=3, min_strategies=2)
    counts = {}
    for record in selected:
        strategy = record["generation_metadata"]["strategy"]
        counts[strategy] = counts.get(strategy, 0) + 1

    assert [record["canonical_hash"] for record in selected] == ["q1", "q2", "q3", "f1"]
    assert counts == {"quartic_lift": 3, "four_real_seed": 1}
    assert len({record["canonical_hash"] for record in selected}) == 4


def test_write_review_outputs_creates_report_batch_coefficients_and_manifest(tmp_path):
    selected = [
        _record("a", 20.0, strategy="quartic_lift", coeff0=1),
        _record("b", 18.0, strategy="four_real_seed", coeff0=2),
    ]
    for record in selected:
        record["source_ledger_path"] = str(tmp_path / "source.jsonl")
        record["source_shortlist_path"] = str(tmp_path / "shortlist.jsonl")
    output_dir = tmp_path / "review"
    manifest = build_manifest(
        source_shortlist_path=tmp_path / "shortlist.jsonl",
        source_shortlist_manifest={"selected_records": 2},
        selected=selected,
        total_shortlist_records=2,
        output_dir=output_dir,
        command=["python3", "scripts/igp24_review_shortlist.py"],
        criteria={"batch_size": 2, "deduplicate_by": "canonical_hash"},
        source_commit="abc123",
    )

    paths = write_review_outputs(selected, output_dir, manifest)
    batch = [json.loads(line) for line in paths["verification_batch_jsonl"].read_text(encoding="utf-8").splitlines()]
    coeff_lines = paths["verification_coefficients_txt"].read_text(encoding="utf-8").splitlines()
    report = paths["review_report_md"].read_text(encoding="utf-8")
    reloaded_manifest = json.loads(paths["manifest_json"].read_text(encoding="utf-8"))

    assert [record["canonical_hash"] for record in batch] == ["a", "b"]
    assert batch[0]["proxy_only_caveat"] == PROXY_CAVEAT
    assert batch[0]["verified_group_label"] is None
    assert json.loads(coeff_lines[0])[-1] == 1
    assert len(json.loads(coeff_lines[0])) == 25
    assert "Proxy Review Batch" in report
    assert "No PARI, MAGMA, SAIR" in report
    assert reloaded_manifest["selected_records"] == 2
    assert reloaded_manifest["strategy_counts"] == {"four_real_seed": 1, "quartic_lift": 1}
    assert reloaded_manifest["safety"]["proxy_only"]
    assert reloaded_manifest["safety"]["review_export_only"]
    assert not reloaded_manifest["safety"]["verifier_executed"]
    assert not reloaded_manifest["safety"]["submission_executed"]
    assert not reloaded_manifest["safety"]["network_calls"]
    assert not reloaded_manifest["safety"]["exact_group_claims"]
