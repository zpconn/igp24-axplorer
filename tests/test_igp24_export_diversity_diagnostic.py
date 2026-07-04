import json

import pytest

from scripts.igp24_export_diversity_diagnostic import build_summary, get_parser, write_outputs


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _export_record(sample_index, batch_index, coeffs, token_ids=None):
    return {
        "sample_index": sample_index,
        "batch_index": batch_index,
        "batch_row": sample_index % 64,
        "decoded_coefficients": coeffs,
        "exported_coefficients": coeffs + [1] if coeffs is not None else None,
        "token_ids": token_ids if token_ids is not None else [12, sample_index, 10],
        "temperature": 0.9,
        "top_k": 9,
        "device": "cuda",
        "exp_name": "exp",
        "exp_id": "run",
        "generation_metadata": {
            "sample_export_only": True,
            "resolved_generation_strategy": "fixed_sparse_template",
        },
    }


def test_build_summary_counts_raw_export_duplicates_and_checkpoints(tmp_path):
    coeff_a = [1] + [0] * 23
    coeff_b = [2] + [0] * 23
    source_a = tmp_path / "seed_a.jsonl"
    source_b = tmp_path / "seed_b.jsonl"
    _write_jsonl(
        source_a,
        [
            _export_record(0, 0, coeff_a, [12, 1, 10]),
            _export_record(1, 0, coeff_a, [12, 1, 10]),
            _export_record(2, 0, coeff_b, [12, 2, 10]),
            _export_record(3, 0, None, [12, 10]),
        ],
    )
    _write_jsonl(
        source_b,
        [
            _export_record(0, 0, coeff_a, [12, 1, 10]),
            _export_record(1, 0, [3] + [0] * 23, [12, 3, 10]),
        ],
    )

    summary, duplicate_records = build_summary(
        [source_a, source_b],
        labels=["seed_a", "seed_b"],
        translation_radius=1,
        coeff_bound=4,
        checkpoint_interval=2,
        top_n=5,
    )

    seed_a = summary["sources"][0]
    assert summary["safety"]["proxy_only"]
    assert not summary["safety"]["scores_candidates"]
    assert seed_a["records_read"] == 4
    assert seed_a["decoded_records"] == 3
    assert seed_a["invalid_decode_records"] == 1
    assert seed_a["exact_unique_coefficients"] == 2
    assert seed_a["exact_duplicate_records"] == 1
    assert seed_a["canonical_unique_hashes"] == 2
    assert seed_a["canonical_duplicate_records"] == 1
    assert seed_a["token_unique_sequences"] == 2
    assert seed_a["token_duplicate_records"] == 1
    assert seed_a["top_canonical_duplicate_groups"][0]["count"] == 2
    assert seed_a["checkpoints"][0]["decoded_records"] == 2
    assert seed_a["checkpoints"][0]["canonical_duplicate_records"] == 1
    assert summary["overlap"]["pairwise"][0]["shared_canonical_hashes"] == 1
    assert any(record["source_label"] == "seed_a" for record in duplicate_records)


def test_write_outputs_creates_report_and_duplicate_jsonl(tmp_path):
    source = tmp_path / "seed.jsonl"
    _write_jsonl(
        source,
        [
            _export_record(0, 0, [1] + [0] * 23),
            _export_record(1, 0, [1] + [0] * 23),
        ],
    )
    summary, duplicate_records = build_summary(
        [source],
        labels=None,
        translation_radius=1,
        coeff_bound=4,
        checkpoint_interval=1,
        top_n=5,
    )
    output_dir = tmp_path / "diagnostic"

    write_outputs(summary, duplicate_records, output_dir)

    written = json.loads((output_dir / "export_diversity_summary.json").read_text(encoding="utf-8"))
    report = (output_dir / "export_diversity_report.md").read_text(encoding="utf-8")
    duplicate_lines = (output_dir / "top_duplicate_groups.jsonl").read_text(encoding="utf-8").splitlines()
    assert written["artifacts"]["report_path"].endswith("export_diversity_report.md")
    assert "proxy-only diagnostic" in report
    assert duplicate_lines


def test_build_summary_rejects_label_count_mismatch(tmp_path):
    source = tmp_path / "seed.jsonl"
    _write_jsonl(source, [_export_record(0, 0, [1] + [0] * 23)])

    with pytest.raises(ValueError):
        build_summary(
            [source],
            labels=["seed", "extra"],
            translation_radius=1,
            coeff_bound=4,
            checkpoint_interval=1,
            top_n=5,
        )


def test_parser_defaults_are_bounded_for_diagnostics():
    parser = get_parser()
    args = parser.parse_args(["samples.jsonl"])

    assert args.translation_radius == 2
    assert args.coeff_bound == 4
    assert args.checkpoint_interval == 256
    assert args.top_n == 20
