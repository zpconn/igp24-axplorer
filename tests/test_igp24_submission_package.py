import json

import pytest

from scripts.igp24_submission_package import PackageError, build_package


def _row(candidate_hash, label, *, rank=1, coeff0=1):
    return {
        "schema_version": 1,
        "record_type": "igp24_submission_plan_candidate",
        "submission_plan_rank": rank,
        "canonical_hash": candidate_hash,
        "short_hash": candidate_hash[:12],
        "pair_key": f"{label}|r=4",
        "verified_group_label": label,
        "expected_r": 4,
        "expected_r_source": "verified.sympy_real_root_count",
        "exact_r_status": "ok",
        "exact_nfdisc_status": "ok",
        "exact_nfdisc_source": "sympy_algebraic_field_discriminant",
        "exact_nfdisc_abs": 1000 + rank,
        "baseline_status": "non_baseline_candidate",
        "scoreability_status": "new_pair_candidate",
        "discriminant_rank_category": "exact_nfdisc",
        "exported_coefficients": [coeff0] + [0] * 23 + [1],
    }


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_fixture(tmp_path):
    hash_a = "a" * 64
    hash_b = "b" * 64
    rows = [_row(hash_a, "24T1", rank=1, coeff0=2), _row(hash_b, "24T2", rank=2, coeff0=3)]
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    _write_jsonl(plan_dir / "submission_plan.jsonl", rows)
    _write_json(
        plan_dir / "submission_plan_summary.json",
        {
            "source_commit": "abc123",
            "baseline_status_counts": {"non_baseline_candidate": 2},
            "scoreability_status_counts": {"new_pair_candidate": 2},
            "exact_r_status_counts": {"ok": 2},
            "exact_nfdisc_status_counts": {"ok": 2},
            "discriminant_rank_category_counts": {"exact_nfdisc": 2},
        },
    )
    (plan_dir / "submission_plan_report.md").write_text("# report\n", encoding="utf-8")
    (plan_dir / "submission_candidates.txt").write_text("2," + ",".join(["0"] * 23) + ",1 # comment\n", encoding="utf-8")

    evidence_dir = tmp_path / "evidence"
    (evidence_dir / "online_magma_manual" / "copy_paste_scripts").mkdir(parents=True)
    (evidence_dir / "magma_candidate_scripts").mkdir()
    for name in (
        "offline_verification_manifest.json",
        "verification_batch.jsonl",
        "verification_coefficients.txt",
        "pari_input.gp",
        "sympy_signature_results.jsonl",
        "sympy_signature_summary.json",
        "sympy_nfdisc_results.jsonl",
        "sympy_nfdisc_summary.json",
    ):
        (evidence_dir / name).write_text("{}\n", encoding="utf-8")
    for name in (
        "online_magma_manual_results.jsonl",
        "online_magma_manual_summary.json",
        "online_magma_manual_report.md",
    ):
        (evidence_dir / "online_magma_manual" / name).write_text("{}\n", encoding="utf-8")
    (evidence_dir / "online_magma_manual" / "copy_paste_scripts" / "0001_a.m").write_text("print \"IGP24_SIGNATURE\";\n", encoding="utf-8")
    (evidence_dir / "magma_candidate_scripts" / "0001_a.m").write_text("print \"IGP24_SIGNATURE\";\n", encoding="utf-8")

    baseline_csv = tmp_path / "baseline.csv"
    baseline_csv.write_text("label,r,nfdisc_abs\n24T999,4,10\n", encoding="utf-8")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / f"online_magma_manual_output_{hash_a[:12]}_20260706.xml").write_text("<xml>a</xml>\n", encoding="utf-8")
    (raw_dir / f"online_magma_manual_output_{hash_b[:12]}_20260706.xml").write_text("<xml>b</xml>\n", encoding="utf-8")
    return rows, plan_dir, evidence_dir, baseline_csv, raw_dir


def test_build_package_writes_manifest_checklist_and_clean_coefficients(tmp_path):
    rows, plan_dir, evidence_dir, baseline_csv, raw_dir = _write_fixture(tmp_path)
    output_dir = tmp_path / "package"

    paths = build_package(
        plan_dir=plan_dir,
        evidence_dir=evidence_dir,
        baseline_csv=baseline_csv,
        raw_magma_dir=raw_dir,
        output_dir=output_dir,
        expected_hashes=[row["canonical_hash"] for row in rows],
        command=["python3", "scripts/igp24_submission_package.py"],
        source_commit="abc123",
        local_tool_availability={"magma": {"available": False}, "pari_gp": {"available": False}},
    )

    manifest = json.loads(paths["package_manifest_json"].read_text(encoding="utf-8"))
    coefficient_lines = paths["submission_coefficients_txt"].read_text(encoding="utf-8").splitlines()
    checklist = paths["submission_checklist_md"].read_text(encoding="utf-8")

    assert manifest["selected_records"] == 2
    assert manifest["plan_summary"]["scoreability_status_counts"] == {"new_pair_candidate": 2}
    assert manifest["safety"]["sair_submission"] is False
    assert all("#" not in line for line in coefficient_lines)
    assert coefficient_lines == [
        "2," + ",".join(["0"] * 23) + ",1",
        "3," + ",".join(["0"] * 23) + ",1",
    ]
    assert "Exactly five rows" in checklist
    assert (output_dir / "raw_magma_xml" / f"online_magma_manual_output_{rows[0]['short_hash']}_20260706.xml").exists()


def test_build_package_rejects_wrong_expected_hashes(tmp_path):
    _rows, plan_dir, evidence_dir, baseline_csv, raw_dir = _write_fixture(tmp_path)

    with pytest.raises(PackageError, match="hash set mismatch"):
        build_package(
            plan_dir=plan_dir,
            evidence_dir=evidence_dir,
            baseline_csv=baseline_csv,
            raw_magma_dir=raw_dir,
            output_dir=tmp_path / "package",
            expected_hashes=["c" * 64, "d" * 64],
            command=["python3", "scripts/igp24_submission_package.py"],
            source_commit="abc123",
            local_tool_availability={"magma": {"available": False}, "pari_gp": {"available": False}},
        )
