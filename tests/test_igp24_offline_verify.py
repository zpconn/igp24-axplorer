import json

import pytest

from scripts.igp24_offline_verify import (
    MAGMA_INPUT_M,
    OFFLINE_MANIFEST_JSON,
    PARI_INPUT_GP,
    VERIFICATION_PLAN_MD,
    ReviewBatchError,
    build_magma_input,
    build_pari_input,
    load_review_batch,
    write_outputs,
)


def _record(canonical_hash="a", coeff0=1):
    return {
        "canonical_hash": canonical_hash,
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
        "score": 10200.0 + coeff0,
        "real_root_count": 4,
        "coefficient_height": abs(coeff0),
        "source_strategy": "quartic_lift",
        "source_ledger_path": "/tmp/source.jsonl",
        "source_shortlist_path": "/tmp/shortlist.jsonl",
        "verification_status": "proxy_scored",
        "verified_group_label": None,
    }


def _write_review_batch(path, records):
    path.mkdir(parents=True, exist_ok=True)
    (path / "verification_batch.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    (path / "verification_coefficients.txt").write_text(
        "".join(json.dumps(record["exported_coefficients"]) + "\n" for record in records),
        encoding="utf-8",
    )
    (path / "manifest.json").write_text(
        json.dumps({"selected_records": len(records), "safety": {"proxy_only": True}}),
        encoding="utf-8",
    )


def test_load_review_batch_validates_records_and_coefficients(tmp_path):
    review_dir = tmp_path / "review"
    _write_review_batch(review_dir, [_record("a", 1), _record("b", 2)])

    records, loaded_dir, manifest = load_review_batch(review_dir)

    assert loaded_dir == review_dir.resolve()
    assert manifest["selected_records"] == 2
    assert [record["canonical_hash"] for record in records] == ["a", "b"]
    assert all(record["verified_group_label"] is None for record in records)
    assert all(record["offline_verification_status"] == "prepared_unverified" for record in records)


def test_load_review_batch_rejects_bad_coefficient_shape(tmp_path):
    review_dir = tmp_path / "review"
    bad = _record("bad", 1)
    bad["exported_coefficients"] = [1, 2, 3]
    _write_review_batch(review_dir, [bad])

    with pytest.raises(ReviewBatchError, match="expected 25 coefficients"):
        load_review_batch(review_dir)


def test_load_review_batch_rejects_text_mismatch(tmp_path):
    review_dir = tmp_path / "review"
    record = _record("a", 1)
    _write_review_batch(review_dir, [record])
    (review_dir / "verification_coefficients.txt").write_text(json.dumps([2] + [0] * 23 + [1]) + "\n", encoding="utf-8")

    with pytest.raises(ReviewBatchError, match="does not match"):
        load_review_batch(review_dir)


def test_build_pari_and_magma_inputs_include_manual_exact_steps():
    records = [_record("abc", 1)]
    pari = build_pari_input(records)
    magma = build_magma_input(records)

    assert "abc" in pari
    assert "polisirreducible" in pari
    assert "polgalois" in pari
    assert "abc" in magma
    assert "IsIrreducible" in magma
    assert "GaloisGroup" in magma


def test_write_outputs_creates_manifest_scripts_plan_and_safety_flags(tmp_path):
    review_dir = tmp_path / "review"
    records = [_record("a", 1), _record("b", 2)]
    _write_review_batch(review_dir, records)
    loaded, loaded_dir, source_manifest = load_review_batch(review_dir)
    output_dir = tmp_path / "offline"

    paths = write_outputs(
        records=loaded,
        review_dir=loaded_dir,
        source_review_manifest=source_manifest,
        output_dir=output_dir,
        command=["python3", "scripts/igp24_offline_verify.py"],
        source_commit="abc123",
        pari_executable="definitely_missing_gp",
        magma_executable="definitely_missing_magma",
        run_pari=True,
        run_magma=True,
        timeout_seconds=5,
    )

    assert paths["offline_verification_manifest_json"] == output_dir / OFFLINE_MANIFEST_JSON
    assert (output_dir / PARI_INPUT_GP).exists()
    assert (output_dir / MAGMA_INPUT_M).exists()
    assert (output_dir / VERIFICATION_PLAN_MD).exists()
    manifest = json.loads((output_dir / OFFLINE_MANIFEST_JSON).read_text(encoding="utf-8"))

    assert manifest["selected_records"] == 2
    assert manifest["selected_hashes"] == ["a", "b"]
    assert not manifest["tool_availability"]["pari"]["available"]
    assert not manifest["tool_availability"]["magma"]["available"]
    assert manifest["execution"]["pari"]["status"] == "unavailable"
    assert manifest["execution"]["magma"]["status"] == "unavailable"
    assert not manifest["safety"]["network_calls"]
    assert not manifest["safety"]["sair_submission"]
    assert not manifest["safety"]["auto_submission"]
    assert not manifest["safety"]["pari_executed"]
    assert not manifest["safety"]["magma_executed"]
    assert not manifest["safety"]["exact_group_labels_parsed"]
    assert not manifest["safety"]["exact_group_claims"]
