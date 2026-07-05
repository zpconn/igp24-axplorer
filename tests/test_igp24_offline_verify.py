import json

import pytest

from scripts.igp24_offline_verify import (
    MAGMA_CACHE_JSON,
    MAGMA_INPUT_M,
    MAGMA_REPORT_MD,
    MAGMA_RESULTS_JSONL,
    MAGMA_SUMMARY_JSON,
    OFFLINE_MANIFEST_JSON,
    ONLINE_MAGMA_MANUAL_DIR,
    ONLINE_MAGMA_RESULTS_JSONL,
    ONLINE_MAGMA_SUMMARY_JSON,
    PARI_INPUT_GP,
    VERIFICATION_PLAN_MD,
    ReviewBatchError,
    build_online_magma_manual_input,
    build_magma_command,
    build_magma_guidance,
    build_magma_input,
    build_magma_verification_input,
    build_pari_input,
    cache_key_for_record,
    discover_magma_executable,
    load_review_batch,
    load_verification_input,
    parse_magma_output,
    parse_online_magma_pasted_output,
    run_magma_verification,
    select_records_by_candidate_hash,
    write_cache,
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
    assert "Signature(f)" not in magma


def test_build_magma_verification_input_command_and_parser(tmp_path):
    record = _record("abc", 1)
    script = build_magma_verification_input(record, timeout_seconds=7)
    online_script = build_online_magma_manual_input(record)
    command = build_magma_command("/usr/bin/magma", tmp_path / "candidate.m")
    parsed = parse_magma_output(
        "\n".join(
            [
                "IGP24_BEGIN abc",
                "IGP24_DEGREE 24",
                "IGP24_IS_IRREDUCIBLE true",
                "IGP24_SIGNATURE 4 10",
                "IGP24_GALOIS_GROUP Symmetric group G acting on a set of cardinality 24",
                "IGP24_TRANSITIVE_GROUP_ID 12",
            ]
        )
    )

    assert "GaloisGroup(f)" in script
    assert "TransitiveGroupIdentification(G)" in script
    assert "IGP24_TRANSITIVE_GROUP_ID" in script
    assert "Signature(f)" not in script
    assert "Signature(f)" not in online_script
    assert "do not batch-submit" in online_script
    assert command == ["/usr/bin/magma", str(tmp_path / "candidate.m")]
    assert parsed["parse_status"] == "verified"
    assert parsed["verified_group_label"] == "24T12"
    assert parsed["signature_r"] == 4
    assert parsed["candidate_hash"] == "abc"
    assert parsed["galois_group_text"] == "Symmetric group G acting on a set of cardinality 24"
    assert parsed["degree"] == 24
    assert parsed["is_irreducible"] is True


def test_parse_online_magma_pasted_output_records_exact_label_and_headers():
    pasted_xml = """<?xml version=\"1.0\"?>
<calculator><headers><max_time>60</max_time><max_input>50000</max_input><seed>52682226</seed><version>2.29-8</version><time>0.420</time><memory>32.09MB</memory></headers><results><line>IGP24_BEGIN 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb</line><line>IGP24_DEGREE 24</line><line>IGP24_IS_IRREDUCIBLE true</line><line>IGP24_GALOIS_GROUP Symmetric group G acting on a set of cardinality 24</line><line>Order = 2^22 * 3^10 * 5^4 * 7^3 * 11^2 * 13 * 17 * 19 * 23</line><line>IGP24_TRANSITIVE_GROUP_ID 25000</line><line>IGP24_END 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb</line></results></calculator>"""

    parsed = parse_online_magma_pasted_output(
        pasted_xml,
        expected_candidate_hash="70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb",
    )

    assert parsed["status"] == "verified"
    assert parsed["verified_group_label"] == "24T25000"
    assert parsed["degree"] == 24
    assert parsed["is_irreducible"] is True
    assert parsed["galois_group_text"] == "Symmetric group G acting on a set of cardinality 24"
    assert parsed["transitive_group_id"] == 25000
    assert parsed["magma_version"] == "V2.29-8"
    assert parsed["magma_runtime_seconds"] == 0.420
    assert parsed["provenance"]["manual_probe"] is True
    assert parsed["safety"]["automated_online_submission"] is False


def test_discover_magma_executable_checks_path_common_and_extra_patterns(tmp_path):
    fake_magma = tmp_path / "MagmaFake" / "magma"
    fake_magma.parent.mkdir()
    fake_magma.write_text("#!/bin/sh\necho fake magma\n", encoding="utf-8")
    fake_magma.chmod(0o755)
    missing_path = tmp_path / "missing" / "magma"

    discovery = discover_magma_executable(
        "definitely_missing_magma",
        common_search_patterns=[str(missing_path), str(fake_magma)],
        extra_search_patterns=[str(tmp_path / "extra_missing")],
    )

    assert discovery["available"] is True
    assert discovery["path"] == str(fake_magma)
    assert discovery["selected_source"] == "search_pattern"
    assert discovery["selected_query"] == str(fake_magma)
    assert discovery["common_search_patterns"] == [str(missing_path), str(fake_magma)]
    assert discovery["extra_search_patterns"] == [str(tmp_path / "extra_missing")]
    checked_by_path = {candidate["path"]: candidate for candidate in discovery["candidates_checked"]}
    assert checked_by_path[str(missing_path)]["exists"] is False
    assert checked_by_path[str(fake_magma)]["is_executable"] is True


def test_magma_unavailable_guidance_builds_exact_rerun_command(tmp_path):
    command = [
        "/usr/bin/python3",
        "scripts/igp24_offline_verify.py",
        "/tmp/review",
        "--output_dir",
        str(tmp_path / "dry"),
        "--max_records",
        "3",
        "--timeout_seconds",
        "5",
    ]
    guidance = build_magma_guidance(
        availability={"available": False, "path": None, "executable": "magma"},
        command=command,
        run_magma=False,
        output_dir=tmp_path / "dry",
    )

    assert guidance["status"] == "unavailable"
    assert "--run_magma" in guidance["rerun_command"]
    assert "--magma_executable" in guidance["rerun_command"]
    assert "/path/to/magma" in guidance["rerun_command"]
    assert str(tmp_path / "dry_run_magma") in guidance["rerun_command"]
    assert "--run_magma" in guidance["rerun_command_text"]


def test_load_verification_input_accepts_jsonl_and_coefficients_file(tmp_path):
    jsonl_path = tmp_path / "candidates.jsonl"
    jsonl_path.write_text(json.dumps({"decoded_coefficients": [0] * 24, "score": 1.0}) + "\n", encoding="utf-8")
    coeffs_path = tmp_path / "coefficients.txt"
    coeffs_path.write_text(json.dumps([1] + [0] * 23 + [1]) + "\n", encoding="utf-8")

    jsonl_records, _, jsonl_manifest, jsonl_kind = load_verification_input(jsonl_path)
    coeff_records, _, coeff_manifest, coeff_kind = load_verification_input(coeffs_path)

    assert jsonl_kind == "candidate_jsonl"
    assert jsonl_manifest["records_loaded"] == 1
    assert jsonl_records[0]["exported_coefficients"] == [0] * 24 + [1]
    assert jsonl_records[0]["canonical_hash"].startswith("coeff_")
    assert coeff_kind == "coefficients_file"
    assert coeff_manifest["records_loaded"] == 1
    assert coeff_records[0]["exported_coefficients"] == [1] + [0] * 23 + [1]


def test_select_records_by_candidate_hash_preserves_requested_order():
    records = [_record("a", 1), _record("b", 2), _record("c", 3)]

    selected = select_records_by_candidate_hash(records, ["c", "a"])

    assert [record["canonical_hash"] for record in selected] == ["c", "a"]
    with pytest.raises(ReviewBatchError, match="not found"):
        select_records_by_candidate_hash(records, ["missing"])
    with pytest.raises(ReviewBatchError, match="duplicate --candidate_hash"):
        select_records_by_candidate_hash(records, ["a", "a"])


def test_run_magma_verification_statuses_cache_and_timeout(tmp_path):
    records = [_record("a", 1), _record("b", 2)]
    for index, record in enumerate(records, start=1):
        record["source_input_kind"] = "fixture"
        record["input_index"] = index
    cache_path = tmp_path / MAGMA_CACHE_JSON
    key = cache_key_for_record(records[0])
    write_cache(
        cache_path,
        {
            "schema_version": 1,
            "entries": {
                key: {
                    "status": "verified",
                    "exact_verification_status": "verified",
                    "verified_group_label": "24T12",
                    "transitive_group_id": 12,
                }
            },
        },
    )

    cached_results, cached_execution = run_magma_verification(
        records=[records[0]],
        output_dir=tmp_path / "cached",
        availability={"available": True, "path": "/definitely/not/executed", "executable": "magma"},
        run_magma=True,
        timeout_seconds=1,
        cache_path=cache_path,
        refresh_cache=False,
        max_records=None,
    )
    unavailable_results, unavailable_execution = run_magma_verification(
        records=[records[1]],
        output_dir=tmp_path / "unavailable",
        availability={"available": False, "path": None, "executable": "missing_magma"},
        run_magma=True,
        timeout_seconds=1,
        cache_path=tmp_path / "unavailable_cache.json",
        refresh_cache=False,
        max_records=None,
    )
    dry_results, _ = run_magma_verification(
        records=[records[1]],
        output_dir=tmp_path / "dry",
        availability={"available": False, "path": None, "executable": "missing_magma"},
        run_magma=False,
        timeout_seconds=1,
        cache_path=tmp_path / "dry_cache.json",
        refresh_cache=False,
        max_records=None,
    )

    fake_magma = tmp_path / "fake_magma"
    fake_magma.write_text("#!/bin/sh\nsleep 2\n", encoding="utf-8")
    fake_magma.chmod(0o755)
    timeout_results, _ = run_magma_verification(
        records=[records[1]],
        output_dir=tmp_path / "timeout",
        availability={"available": True, "path": str(fake_magma), "executable": str(fake_magma)},
        run_magma=True,
        timeout_seconds=1,
        cache_path=tmp_path / "timeout_cache.json",
        refresh_cache=False,
        max_records=None,
    )

    assert cached_results[0]["status"] == "verified"
    assert cached_results[0]["cache_hit"] is True
    assert cached_results[0]["verified_group_label"] == "24T12"
    assert cached_execution["results"] == {"verified": 1}
    assert unavailable_results[0]["status"] == "unavailable"
    assert unavailable_execution["status"] == "unavailable"
    assert dry_results[0]["status"] == "dry_run"
    assert (tmp_path / "dry" / "magma_candidate_scripts").is_dir()
    assert timeout_results[0]["status"] == "timeout"
    assert timeout_results[0]["timed_out"] is True


def test_write_outputs_creates_manifest_scripts_plan_and_safety_flags(tmp_path):
    review_dir = tmp_path / "review"
    records = [_record("a", 1), _record("b", 2)]
    _write_review_batch(review_dir, records)
    loaded, loaded_dir, source_manifest = load_review_batch(review_dir)
    output_dir = tmp_path / "offline"

    paths = write_outputs(
        records=loaded,
        input_path=loaded_dir,
        input_kind="review_batch",
        source_review_manifest=source_manifest,
        output_dir=output_dir,
        command=["python3", "scripts/igp24_offline_verify.py"],
        source_commit="abc123",
        pari_executable="definitely_missing_gp",
        magma_executable="definitely_missing_magma",
        run_pari=True,
        run_magma=True,
        timeout_seconds=5,
        magma_common_search_patterns=[],
    )

    assert paths["offline_verification_manifest_json"] == output_dir / OFFLINE_MANIFEST_JSON
    assert (output_dir / PARI_INPUT_GP).exists()
    assert (output_dir / MAGMA_INPUT_M).exists()
    assert (output_dir / VERIFICATION_PLAN_MD).exists()
    assert (output_dir / MAGMA_RESULTS_JSONL).exists()
    assert (output_dir / MAGMA_SUMMARY_JSON).exists()
    assert (output_dir / MAGMA_REPORT_MD).exists()
    assert (output_dir / MAGMA_CACHE_JSON).exists()
    manifest = json.loads((output_dir / OFFLINE_MANIFEST_JSON).read_text(encoding="utf-8"))
    magma_summary = json.loads((output_dir / MAGMA_SUMMARY_JSON).read_text(encoding="utf-8"))
    magma_results = [json.loads(line) for line in (output_dir / MAGMA_RESULTS_JSONL).read_text(encoding="utf-8").splitlines()]

    assert manifest["selected_records"] == 2
    assert manifest["selected_hashes"] == ["a", "b"]
    assert manifest["source_input_kind"] == "review_batch"
    assert not manifest["tool_availability"]["pari"]["available"]
    assert not manifest["tool_availability"]["magma"]["available"]
    assert manifest["execution"]["pari"]["status"] == "unavailable"
    assert manifest["execution"]["magma"]["status"] == "unavailable"
    assert manifest["magma_discovery"]["available"] is False
    assert manifest["magma_rerun_guidance"]["status"] == "unavailable"
    assert "--run_magma" in manifest["magma_rerun_guidance"]["rerun_command_text"]
    assert "--magma_executable /path/to/magma" in manifest["magma_rerun_guidance"]["rerun_command_text"]
    assert magma_summary["status_counts"] == {"unavailable": 2}
    assert magma_summary["magma_discovery"]["available"] is False
    assert magma_summary["magma_rerun_guidance"]["status"] == "unavailable"
    assert [record["status"] for record in magma_results] == ["unavailable", "unavailable"]
    report = (output_dir / MAGMA_REPORT_MD).read_text(encoding="utf-8")
    assert "MAGMA discovery checked paths" in report
    assert "Rerun command" in report
    assert not manifest["safety"]["network_calls"]
    assert not manifest["safety"]["sair_submission"]
    assert not manifest["safety"]["auto_submission"]
    assert not manifest["safety"]["pari_executed"]
    assert not manifest["safety"]["magma_executed"]
    assert not manifest["safety"]["exact_group_labels_parsed"]
    assert not manifest["safety"]["exact_group_claims"]


def test_write_outputs_creates_online_magma_manual_artifacts_and_parses_paste(tmp_path):
    candidate_hash = "70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb"
    review_dir = tmp_path / "review"
    records = [_record(candidate_hash, 1)]
    _write_review_batch(review_dir, records)
    loaded, loaded_dir, source_manifest = load_review_batch(review_dir)
    pasted_xml = """<?xml version=\"1.0\"?>
<calculator><headers><max_time>60</max_time><max_input>50000</max_input><seed>52682226</seed><version>2.29-8</version><time>0.420</time><memory>32.09MB</memory></headers><results><line>IGP24_BEGIN 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb</line><line>IGP24_DEGREE 24</line><line>IGP24_IS_IRREDUCIBLE true</line><line>IGP24_GALOIS_GROUP Symmetric group G acting on a set of cardinality 24</line><line>IGP24_TRANSITIVE_GROUP_ID 25000</line><line>IGP24_END 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb</line></results></calculator>"""
    pasted_path = tmp_path / "online_pasted_outputs.jsonl"
    pasted_path.write_text(
        json.dumps({"candidate_hash": candidate_hash, "pasted_output": pasted_xml}) + "\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "offline"

    paths = write_outputs(
        records=loaded,
        input_path=loaded_dir,
        input_kind="review_batch",
        source_review_manifest=source_manifest,
        output_dir=output_dir,
        command=["python3", "scripts/igp24_offline_verify.py"],
        source_commit="abc123",
        pari_executable="definitely_missing_gp",
        magma_executable="definitely_missing_magma",
        run_pari=False,
        run_magma=False,
        timeout_seconds=5,
        max_records=1,
        magma_common_search_patterns=[],
        online_magma_manual=True,
        online_magma_pasted_outputs=[pasted_path],
    )

    manual_dir = output_dir / ONLINE_MAGMA_MANUAL_DIR
    results = [json.loads(line) for line in (manual_dir / ONLINE_MAGMA_RESULTS_JSONL).read_text(encoding="utf-8").splitlines()]
    summary = json.loads((manual_dir / ONLINE_MAGMA_SUMMARY_JSON).read_text(encoding="utf-8"))
    manifest = json.loads((output_dir / OFFLINE_MANIFEST_JSON).read_text(encoding="utf-8"))
    generated_script = next((manual_dir / "copy_paste_scripts").glob("*.m")).read_text(encoding="utf-8")
    report = (manual_dir / "online_magma_manual_report.md").read_text(encoding="utf-8")

    assert paths["online_magma_results_jsonl"] == manual_dir / ONLINE_MAGMA_RESULTS_JSONL
    assert "Signature(f)" not in generated_script
    assert results[0]["status"] == "verified"
    assert results[0]["verified_group_label"] == "24T25000"
    assert results[0]["magma_version"] == "V2.29-8"
    assert results[0]["magma_runtime_seconds"] == 0.420
    assert summary["verified_group_labels"] == ["24T25000"]
    assert summary["queue_status"]["already_parsed_exact_label_hashes"] == [candidate_hash]
    assert summary["queue_status"]["ready_for_manual_copy_paste_hashes"] == []
    assert summary["queue_status"]["proxy_only_candidate_hashes"] == []
    assert summary["queue_status"]["local_magma_status_counts"] == {"dry_run": 1}
    assert summary["safety"]["network_calls_by_helper"] is False
    assert summary["safety"]["automated_online_submission"] is False
    assert "## Already Parsed Exact Labels" in report
    assert "## Ready For Manual Copy/Paste" in report
    assert "## Proxy-Only Queue Candidates" in report
    assert "## Local MAGMA Dry-Run Status" in report
    assert "24T25000" in report
    assert manifest["online_magma_manual"]["verified_group_labels"] == ["24T25000"]
    assert manifest["safety"]["online_magma_automated_submission"] is False
    assert manifest["safety"]["online_magma_exact_group_labels_parsed"] is True
    assert manifest["safety"]["exact_group_labels_parsed"] is True
    assert manifest["safety"]["exact_group_claims"] is True
    assert manifest["safety"]["dry_run_preparation_only"] is False
    assert manifest["safety"]["magma_executed"] is False
