import json

from scripts.igp24_audit_structural_pretraining_corpus import main
from scripts.igp24_build_structural_pretraining_corpus import main as build_main


def test_structural_corpus_independent_audit_passes_smoke_manifest(tmp_path):
    corpus = tmp_path / "corpus"
    audit = tmp_path / "audit"
    assert build_main(["--output_dir", str(corpus), "--train_rows", "10", "--eval_rows", "5"]) == 0

    assert main(
        [
            "--manifest",
            str(corpus / "corpus_manifest.json"),
            "--output_dir",
            str(audit),
            "--samples_per_file",
            "1",
        ]
    ) == 0
    summary = json.loads((audit / "structural_corpus_audit_summary.json").read_text(encoding="utf-8"))

    assert summary["status"] == "passed"
    assert summary["manifest_row_count"] == 15
    assert summary["file_integrity_failure_count"] == 0
    assert summary["sampled_row_failure_count"] == 0
