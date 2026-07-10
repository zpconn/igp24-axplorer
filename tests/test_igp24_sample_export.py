import argparse
import json

import torch

from scripts.igp24_score_sample_export import (
    build_report,
    build_split_manifest,
    build_split_report,
    extract_decoded_coefficients,
    get_parser,
    score_export_records,
    summarize_scored_records,
)
from src.evaluator import build_sample_export_record, sample_and_export, sample_support_profile


def test_build_sample_export_record_marks_unscored_and_safe():
    args = argparse.Namespace(
        env_name="igp24",
        exp_name="exp",
        exp_id="run",
        device="cuda",
        max_len=24,
        coeff_bound=4,
        igp24_generation_strategy="fixed_sparse_template",
        igp24_generation_preset="none",
        target_r=16,
        sample_export_target_r_conditioning_mode="seed_bank_prefix",
    )

    record = build_sample_export_record(
        sample_index=3,
        batch_index=1,
        batch_row=2,
        token_ids=[1, 2, 3],
        decoded_coefficients=[0] * 24,
        args=args,
        temperature=0.9,
        top_k=9,
    )

    assert record["record_type"] == "igp24_model_sample_export"
    assert record["decoded"]
    assert record["exported_coefficients"] == [0] * 24 + [1]
    assert record["score"] is None
    assert record["scoring_status"] == "unscored"
    assert record["local_search_status"] == "not_run"
    assert record["sample_export_source"] == "model_generate"
    assert record["generation_metadata"]["target_r"] == 16
    assert record["generation_metadata"]["target_r_intent"] == 16
    assert record["generation_metadata"]["target_r_conditioning_mode"] == "seed_bank_prefix"
    assert record["template_family_id"] == "model:fixed_sparse_template:r16:zero_decoded"
    assert record["perturbation_mode"] == "sparse_mixed_support_gcd1"
    assert record["generation_metadata"]["template_family_id"] == record["template_family_id"]
    assert record["generation_metadata"]["basin_fingerprint"] == record["basin_fingerprint"]
    assert record["generation_metadata"]["source_seed_hash"] == record["source_seed_hash"]
    assert not record["safety"]["scored"]
    assert not record["safety"]["local_search_run"]
    assert not record["safety"]["runs_exact_verifiers"]
    assert not record["safety"]["calls_sair"]
    assert not record["safety"]["auto_submits"]


def test_build_sample_export_record_refines_sparse_support_submode():
    args = argparse.Namespace(
        env_name="igp24",
        exp_name="exp",
        exp_id="run",
        device="cuda",
        max_len=24,
        coeff_bound=4,
        igp24_generation_strategy="mixed",
        igp24_generation_preset="none",
        target_r=8,
        sample_export_target_r_conditioning_mode="control_token",
    )
    decoded = [0] * 24
    decoded[0] = 1
    decoded[9] = 1
    decoded[11] = -1
    decoded[18] = -8

    record = build_sample_export_record(
        sample_index=0,
        batch_index=0,
        batch_row=0,
        token_ids=[1, 2, 3],
        decoded_coefficients=decoded,
        args=args,
        temperature=0.8,
        top_k=12,
    )

    assert record["support_pattern"] == "sparse_mixed_support_gcd1"
    assert record["sparse_support_submode"] == "sparse_odd_pair_gap2_support_gcd1"
    assert record["perturbation_mode"] == "sparse_odd_pair_gap2_support_gcd1"
    assert record["generation_metadata"]["sparse_support_submode"] == "sparse_odd_pair_gap2_support_gcd1"


def test_sample_support_profile_identifies_axg14_basin_shapes():
    even = [0] * 24
    even[0] = 2
    even[2] = -1
    even[4] = 1
    mixed = [0] * 24
    mixed[0] = 2
    mixed[1] = 1
    mixed[6] = -3

    assert sample_support_profile(even)["support_pattern"] == "even_support_like"
    assert sample_support_profile(even)["even_support_like"] is True
    assert sample_support_profile(mixed)["support_pattern"] == "sparse_mixed_support_gcd1"
    assert sample_support_profile(mixed)["support_gcd"] == 1
    assert sample_support_profile(mixed)["sparse_support_submode"] == "sparse_odd_single_e1_support_gcd1"


def test_sample_and_export_dedup_skips_duplicate_decoded_coefficients(tmp_path):
    class DummyDecoded:
        def __init__(self, coefficient):
            self.coefficients = [coefficient] + [0] * 23

    class DummyTokenizer:
        def decode(self, row):
            coefficient = int(row[0])
            if coefficient < 0:
                return None
            return DummyDecoded(coefficient)

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def __init__(self):
            self.values = [1, 1, 2, 3, 4, 5]
            self.offset = 0

        def generate(self, x_init, length, temperature, top_k, do_sample):
            batch_size = int(x_init.shape[0])
            values = self.values[self.offset : self.offset + batch_size]
            self.offset += batch_size
            return torch.tensor([[value] + [0] * (length - 1) for value in values], dtype=torch.long)

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="dedup_export_test",
        exp_id="run",
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=4,
        num_samples_from_model=6,
        sample_export_dedup=True,
        sample_export_unique_target=2,
        sample_export_max_attempts=6,
        sample_export_progress_interval=1,
        top_k=-1,
        igp24_generation_strategy="fixed_sparse_template",
        igp24_generation_preset="none",
        target_r=None,
        sample_export_target_r_conditioning_mode="none",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.1,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]
    sidecar = json.loads((tmp_path / "samples.jsonl.summary.json").read_text(encoding="utf-8"))

    assert summary["stop_reason"] == "unique_target_reached"
    assert summary["attempted_samples"] == 3
    assert summary["records_written"] == 2
    assert summary["unique_decoded_coefficients"] == 2
    assert summary["duplicate_decoded_records_skipped"] == 1
    assert sidecar["stop_reason"] == "unique_target_reached"
    assert [record["sample_index"] for record in records] == [0, 2]
    assert [record["export_index"] for record in records] == [0, 1]
    assert [record["deduplication"]["unique_decoded_index"] for record in records] == [0, 1]
    assert all(record["deduplication"]["enabled"] for record in records)
    assert all(not record["safety"]["scored"] for record in records)


def test_sample_and_export_skips_external_excluded_hashes(tmp_path):
    class DummyDecoded:
        def __init__(self, coefficient):
            self.coefficients = [coefficient] + [0] * 23

    class DummyTokenizer:
        def decode(self, row):
            return DummyDecoded(int(row[0]))

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def __init__(self):
            self.values = [1, 2, 3]
            self.offset = 0

        def generate(self, x_init, length, temperature, top_k, do_sample):
            batch_size = int(x_init.shape[0])
            values = self.values[self.offset : self.offset + batch_size]
            self.offset += batch_size
            return torch.tensor([[value] + [0] * (length - 1) for value in values], dtype=torch.long)

    excluded = tmp_path / "excluded_hashes.jsonl"
    excluded.write_text(json.dumps({"decoded_coefficients": [1] + [0] * 23}) + "\n", encoding="utf-8")
    args = argparse.Namespace(
        env_name="igp24",
        exp_name="excluded_hash_export_test",
        exp_id="run",
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=3,
        num_samples_from_model=3,
        sample_export_dedup=True,
        sample_export_unique_target=2,
        sample_export_max_attempts=3,
        sample_export_progress_interval=1,
        sample_export_excluded_hashes_jsonl=str(excluded),
        top_k=-1,
        igp24_generation_strategy="fixed_sparse_template",
        igp24_generation_preset="none",
        target_r=None,
        sample_export_target_r_conditioning_mode="none",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.1,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["stop_reason"] == "unique_target_reached"
    assert summary["attempted_samples"] == 3
    assert summary["records_written"] == 2
    assert summary["excluded_hashes_loaded"] >= 1
    assert summary["excluded_hash_records_skipped"] == 1
    assert summary["provenance_skip_counts"] == {"excluded_hash": 1}
    assert [record["decoded_coefficients"][0] for record in records] == [2, 3]


def test_sample_and_export_axg14_provenance_controls_skip_bad_basins(tmp_path):
    class DummyDecoded:
        def __init__(self, a0, a1):
            self.coefficients = [a0, a1] + [0] * 22

    class DummyTokenizer:
        def decode(self, row):
            return DummyDecoded(int(row[0]), int(row[1]))

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def __init__(self):
            self.values = [(2, 0), (2, 1), (3, 0), (3, 1)]
            self.offset = 0

        def generate(self, x_init, length, temperature, top_k, do_sample):
            batch_size = int(x_init.shape[0])
            values = self.values[self.offset : self.offset + batch_size]
            self.offset += batch_size
            return torch.tensor([[a0, a1] + [0] * (length - 2) for a0, a1 in values], dtype=torch.long)

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="axg14_export_test",
        exp_id="run",
        seed=44,
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=4,
        num_samples_from_model=4,
        sample_export_dedup=True,
        sample_export_unique_target=0,
        sample_export_max_attempts=4,
        sample_export_progress_interval=1,
        sample_export_avoid_even_support_like=True,
        sample_export_require_support_gcd_one=True,
        sample_export_family_cap=1,
        sample_export_basin_fingerprint_cap=0,
        top_k=-1,
        igp24_generation_strategy="mixed",
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode="control_token",
        target_r=20,
        sample_export_target_r_conditioning_mode="control_token",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "axg14_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.15,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["records_written"] == 1
    assert summary["provenance_controls_enabled"]
    assert summary["provenance_skip_counts"] == {
        "even_support_like": 2,
        "support_gcd_not_one": 2,
        "template_family_cap": 1,
    }
    assert records[0]["generation_metadata"]["generation_strategy"] == "mixed"
    assert records[0]["generation_metadata"]["support_gcd"] == 1
    assert records[0]["generation_metadata"]["support_pattern"] == "sparse_mixed_support_gcd1"
    assert records[0]["generation_metadata"]["perturbation_mode"] == "sparse_odd_single_e1_support_gcd1"
    assert records[0]["generation_metadata"]["sparse_support_submode"] == "sparse_odd_single_e1_support_gcd1"


def test_sample_and_export_can_require_nonzero_constant(tmp_path):
    class DummyDecoded:
        def __init__(self, coeffs):
            self.coefficients = coeffs

    class DummyTokenizer:
        def decode(self, row):
            value = int(row[0])
            return DummyDecoded([value, 1] + [0] * 22)

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def __init__(self):
            self.values = [0, 5]
            self.offset = 0

        def generate(self, x_init, length, temperature, top_k, do_sample):
            batch_size = int(x_init.shape[0])
            values = self.values[self.offset : self.offset + batch_size]
            self.offset += batch_size
            return torch.tensor([[value] + [0] * (length - 1) for value in values], dtype=torch.long)

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="nonzero_constant_export_test",
        exp_id="run",
        seed=46,
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=2,
        num_samples_from_model=2,
        sample_export_dedup=True,
        sample_export_unique_target=0,
        sample_export_max_attempts=2,
        sample_export_progress_interval=1,
        sample_export_avoid_even_support_like=False,
        sample_export_require_support_gcd_one=False,
        sample_export_require_nonzero_constant=True,
        sample_export_required_support_patterns="",
        sample_export_excluded_support_patterns="",
        sample_export_family_cap=0,
        sample_export_basin_fingerprint_cap=0,
        top_k=-1,
        igp24_generation_strategy="mixed",
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode="control_token",
        target_r=16,
        sample_export_target_r_conditioning_mode="control_token",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "nonzero_constant_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.15,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["records_written"] == 1
    assert summary["require_nonzero_constant"] is True
    assert summary["provenance_skip_counts"] == {"zero_constant_term": 1}
    assert records[0]["decoded_coefficients"][0] == 5


def test_sample_and_export_can_require_exact_target_r(tmp_path):
    def multiply(lhs, rhs):
        out = [0] * (len(lhs) + len(rhs) - 1)
        for i, left in enumerate(lhs):
            for j, right in enumerate(rhs):
                out[i + j] += int(left) * int(right)
        return out

    def quadratic_product_coefficients(roots):
        coeffs = [1]
        for root in roots:
            coeffs = multiply(coeffs, [-int(root), 0, 1])
        assert len(coeffs) == 25
        return coeffs[:-1]

    wrong_r = [1] + [0] * 23
    target_r = quadratic_product_coefficients(range(1, 13))

    class DummyDecoded:
        def __init__(self, coeffs):
            self.coefficients = coeffs

    class DummyTokenizer:
        def decode(self, row):
            return DummyDecoded(target_r if int(row[0]) else wrong_r)

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def generate(self, x_init, length, temperature, top_k, do_sample):
            return torch.tensor([[0] + [0] * (length - 1), [1] + [0] * (length - 1)], dtype=torch.long)

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="target_r_export_test",
        exp_id="run",
        seed=47,
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=2,
        num_samples_from_model=2,
        sample_export_dedup=True,
        sample_export_unique_target=0,
        sample_export_max_attempts=2,
        sample_export_progress_interval=1,
        sample_export_avoid_even_support_like=False,
        sample_export_require_support_gcd_one=False,
        sample_export_require_nonzero_constant=False,
        sample_export_require_target_r=True,
        sample_export_required_support_patterns="",
        sample_export_excluded_support_patterns="",
        sample_export_family_cap=0,
        sample_export_basin_fingerprint_cap=0,
        top_k=-1,
        igp24_generation_strategy="mixed",
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode="control_token",
        target_r=24,
        sample_export_target_r_conditioning_mode="control_token",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "target_r_filtered_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.15,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["records_written"] == 1
    assert summary["require_target_r"] is True
    assert summary["exact_target_r_filter_target"] == 24
    assert summary["exact_target_r_filter_counts"] == {"observed_r:0": 1, "observed_r:24": 1}
    assert summary["provenance_skip_counts"] == {"target_r_mismatch": 1}
    assert records[0]["decoded_coefficients"] == target_r
    assert records[0]["sample_provenance"]["exact_real_root_count"] == 24
    assert records[0]["safety"]["runs_exact_local_filters"] is True
    assert records[0]["safety"]["runs_exact_verifiers"] is False


def test_sample_and_export_can_require_local_validity(tmp_path):
    reducible = [720, 0, -10584, 0, 60228, 0, -178248, 0, 307804, 0, -327726, 0, 221271, 0, -96216, 0, 27175, 0, -4950, 0, 561, 0, -36, 0]
    valid = [
        5039,
        0,
        -48168,
        0,
        191772,
        0,
        -420888,
        0,
        567244,
        0,
        -494802,
        0,
        287001,
        0,
        -112056,
        0,
        29455,
        0,
        -5130,
        0,
        567,
        0,
        -36,
        0,
    ]

    class DummyDecoded:
        def __init__(self, coeffs):
            self.coefficients = coeffs

    class DummyTokenizer:
        def decode(self, row):
            return DummyDecoded(valid if int(row[0]) else reducible)

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def generate(self, x_init, length, temperature, top_k, do_sample):
            return torch.tensor([[0] + [0] * (length - 1), [1] + [0] * (length - 1)], dtype=torch.long)

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="local_valid_export_test",
        exp_id="run",
        seed=48,
        device="cpu",
        max_len=24,
        coeff_bound=10**15,
        prime_limit=3,
        exact_score_timeout=2,
        translation_radius=0,
        gen_batch_size=2,
        num_samples_from_model=2,
        sample_export_dedup=True,
        sample_export_unique_target=0,
        sample_export_max_attempts=2,
        sample_export_progress_interval=1,
        sample_export_avoid_even_support_like=False,
        sample_export_require_support_gcd_one=False,
        sample_export_require_nonzero_constant=False,
        sample_export_require_target_r=False,
        sample_export_require_local_valid=True,
        sample_export_required_support_patterns="",
        sample_export_excluded_support_patterns="",
        sample_export_family_cap=0,
        sample_export_basin_fingerprint_cap=0,
        top_k=-1,
        igp24_generation_strategy="mixed",
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode="control_token",
        target_r=24,
        sample_export_target_r_conditioning_mode="control_token",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "local_valid_filtered_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.15,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["records_written"] == 1
    assert summary["require_local_valid"] is True
    assert summary["provenance_skip_counts"] == {"local_invalid:reducible_over_q": 1}
    assert records[0]["decoded_coefficients"] == valid
    assert records[0]["sample_provenance"]["local_valid_filter"]["valid"] is True
    assert records[0]["sample_provenance"]["local_valid_filter"]["irreducible"] is True
    assert records[0]["safety"]["runs_exact_local_filters"] is True
    assert records[0]["safety"]["runs_exact_verifiers"] is False


def test_sample_and_export_can_require_sparse_support_pattern(tmp_path):
    class DummyDecoded:
        def __init__(self, coeffs):
            self.coefficients = coeffs

    class DummyTokenizer:
        def __init__(self):
            self.coefficients_by_index = [
                [2, 1] + [0] * 22,
                [2, 1, 1, 1, 1, 1, 1] + [0] * 17,
                [2] + [1] * 15 + [0] * 8,
            ]

        def decode(self, row):
            return DummyDecoded(self.coefficients_by_index[int(row[0])])

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def __init__(self):
            self.offset = 0

        def generate(self, x_init, length, temperature, top_k, do_sample):
            batch_size = int(x_init.shape[0])
            values = list(range(self.offset, self.offset + batch_size))
            self.offset += batch_size
            return torch.tensor([[value] + [0] * (length - 1) for value in values], dtype=torch.long)

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="support_filter_export_test",
        exp_id="run",
        seed=45,
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=3,
        num_samples_from_model=3,
        sample_export_dedup=True,
        sample_export_unique_target=0,
        sample_export_max_attempts=3,
        sample_export_progress_interval=1,
        sample_export_avoid_even_support_like=False,
        sample_export_require_support_gcd_one=False,
        sample_export_required_support_patterns="sparse_mixed_support_gcd1",
        sample_export_excluded_support_patterns="",
        sample_export_family_cap=0,
        sample_export_basin_fingerprint_cap=0,
        top_k=-1,
        igp24_generation_strategy="sparse",
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode="control_token",
        target_r=16,
        sample_export_target_r_conditioning_mode="control_token",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "support_filtered_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=1.15,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["records_written"] == 1
    assert summary["provenance_controls_enabled"]
    assert summary["required_support_patterns"] == ["sparse_mixed_support_gcd1"]
    assert summary["provenance_skip_counts"] == {"required_support_pattern_mismatch": 2}
    assert records[0]["generation_metadata"]["generation_strategy"] == "sparse"
    assert records[0]["generation_metadata"]["support_pattern"] == "sparse_mixed_support_gcd1"


def test_sample_and_export_prefixes_target_r_seed_bank(tmp_path):
    class DummyDecoded:
        def __init__(self, coefficient):
            self.coefficients = [coefficient] + [0] * 23

    class DummyTokenizer:
        def decode(self, row):
            return DummyDecoded(int(row[0]))

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def __init__(self):
            self.offset = 0

        def generate(self, x_init, length, temperature, top_k, do_sample):
            batch_size = int(x_init.shape[0])
            rows = []
            for index in range(batch_size):
                rows.append([9 + self.offset + index] + [0] * (length - 1))
            self.offset += batch_size
            return torch.tensor(rows, dtype=torch.long)

    seed_bank = tmp_path / "seed_bank.jsonl"
    seed_bank.write_text(
        "\n".join(
            [
                json.dumps({"r": 12, "label": "24Tseed", "exported_coefficients": [5] + [0] * 23 + [1]}),
                json.dumps({"r": 16, "label": "24Tother", "exported_coefficients": [7] + [0] * 23 + [1]}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    args = argparse.Namespace(
        env_name="igp24",
        exp_name="seeded_export_test",
        exp_id="run",
        device="cpu",
        max_len=24,
        coeff_bound=4,
        gen_batch_size=2,
        num_samples_from_model=2,
        sample_export_dedup=True,
        sample_export_unique_target=0,
        sample_export_max_attempts=2,
        sample_export_progress_interval=1,
        top_k=-1,
        igp24_generation_strategy="fixed_sparse_template",
        igp24_generation_preset="none",
        target_r=12,
        sample_export_target_r_conditioning_mode="seed_bank_prefix",
        sample_export_seed_bank_jsonl=str(seed_bank),
        sample_export_seed_bank_target_r=12,
        sample_export_seed_bank_limit=1,
    )
    export_path = tmp_path / "seeded_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0},
        {},
        DummyEnv(),
        temp=0.9,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]
    sidecar = json.loads((tmp_path / "seeded_samples.jsonl.summary.json").read_text(encoding="utf-8"))

    assert summary["seed_bank_records_written"] == 1
    assert summary["records_written"] == 3
    assert sidecar["seed_bank_target_r"] == 12
    assert records[0]["sample_export_source"] == "target_r_seed_bank"
    assert records[0]["generation_metadata"]["strategy"] == "target_r_seed_bank_export"
    assert records[0]["generation_metadata"]["target_r_conditioning_mode"] == "seed_bank_prefix"
    assert records[0]["seed_bank"]["label"] == "24Tseed"
    assert records[1]["sample_export_source"] == "model_generate"
    assert records[1]["generation_metadata"]["target_r_intent"] == 12


def test_sample_and_export_uses_model_side_target_r_and_structure_control_prefix(tmp_path):
    class DummyDecoded:
        def __init__(self, coefficient):
            self.coefficients = [coefficient] + [0] * 23

    class DummyTokenizer:
        def target_r_control_token_ids(self, target_r):
            return [9] if int(target_r) == 16 else []

        def inner_power_control_token_ids(self, inner_power):
            return [10] if int(inner_power) == 2 else []

        def decode(self, row):
            values = [int(value) for value in row.tolist()]
            assert values[:3] == [0, 9, 10]
            return DummyDecoded(values[3])

    class DummyEnv:
        tokenizer = DummyTokenizer()

    class DummyModel:
        def generate(self, x_init, length, temperature, top_k, do_sample):
            assert x_init.shape == (2, 3)
            assert x_init[:, 0].tolist() == [0, 0]
            assert x_init[:, 1].tolist() == [9, 9]
            assert x_init[:, 2].tolist() == [10, 10]
            return torch.tensor(
                [[0, 9, 10, 5] + [0] * (length - 1), [0, 9, 10, 6] + [0] * (length - 1)],
                dtype=torch.long,
            )

    args = argparse.Namespace(
        env_name="igp24",
        exp_name="control_export_test",
        exp_id="run",
        device="cpu",
        max_len=24,
        block_size=27,
        coeff_bound=100,
        gen_batch_size=2,
        num_samples_from_model=2,
        sample_export_dedup=False,
        sample_export_unique_target=0,
        sample_export_max_attempts=2,
        sample_export_progress_interval=1,
        top_k=-1,
        encoding_tokens="decimal_coefficients",
        igp24_generation_strategy="fixed_sparse_template",
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode="control_token",
        igp24_structure_conditioning_mode="control_token",
        target_r=16,
        target_inner_power=2,
        sample_export_target_r_conditioning_mode="none",
        sample_export_seed_bank_jsonl="",
        sample_export_seed_bank_target_r=None,
        sample_export_seed_bank_limit=0,
    )
    export_path = tmp_path / "control_samples.jsonl"

    summary = sample_and_export(
        DummyModel(),
        args,
        {"BOS": 0, "R16": 9, "M2": 10},
        {},
        DummyEnv(),
        temp=0.9,
        export_path=export_path,
    )
    records = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert summary["model_target_r_conditioning_mode"] == "control_token"
    assert summary["model_structure_conditioning_mode"] == "control_token"
    assert summary["target_inner_power"] == 2
    assert records[0]["token_ids"][:3] == [0, 9, 10]
    assert records[0]["generation_metadata"]["target_r_conditioning_mode"] == "control_token"
    assert records[0]["generation_metadata"]["model_target_r_conditioning_mode"] == "control_token"
    assert records[0]["generation_metadata"]["model_structure_conditioning_mode"] == "control_token"
    assert records[0]["generation_metadata"]["target_inner_power"] == 2


def test_extract_decoded_coefficients_accepts_decoded_or_exported():
    decoded = {"decoded_coefficients": list(range(24))}
    exported = {"exported_coefficients": list(range(24)) + [1]}

    assert extract_decoded_coefficients(decoded) == list(range(24))
    assert extract_decoded_coefficients(exported) == list(range(24))
    assert extract_decoded_coefficients({"decoded_coefficients": [1, 2]}) is None
    assert extract_decoded_coefficients({"exported_coefficients": list(range(25))}) is None


def test_score_export_records_consumes_decoded_samples_without_local_search():
    args = argparse.Namespace(
        coeff_bound=4,
        target_r=None,
        target_t=None,
        prime_limit=5,
        max_local_search_steps=0,
        discriminant_weight=1.0,
        height_weight=1.0,
        cycle_diversity_weight=5.0,
        exact_score_timeout=1.0,
        exp_name="test_score_export",
        seed=123,
        translation_radius=1,
        max_records=2,
        score_all=False,
        local_search=False,
    )
    records = [
        {
            "sample_index": 0,
            "decoded_coefficients": [1] + [0] * 23,
            "temperature": 0.9,
            "top_k": 9,
            "device": "cuda",
            "sample_export_source": "target_r_seed_bank",
            "generation_metadata": {
                "strategy": "target_r_seed_bank_export",
                "target_r_conditioning_mode": "seed_bank_prefix",
                "template_family_id": "model:mixed:r20:sparse_mixed_support_gcd1",
                "family_key": "model:mixed:r20:sparse_mixed_support_gcd1:fingerprint",
                "perturbation_mode": "sparse_mixed_support_gcd1",
                "support_pattern": "sparse_mixed_support_gcd1",
                "support_gcd": 1,
                "even_support_like": False,
                "basin_fingerprint": "fingerprint",
                "source_seed_hash": "seedhash",
            },
        },
        {"sample_index": 1, "decoded_coefficients": None},
    ]

    scored, summary = score_export_records(records, args=args, source_path="samples.jsonl")

    assert summary["records_read"] == 2
    assert summary["records_selected"] == 2
    assert summary["skipped_decode_records"] == 1
    assert summary["scored_records"] == len(scored)
    assert summary["selection_mode"] == "capped"
    assert summary["local_search_enabled"] is False
    assert summary["safety"]["proxy_only"]
    assert not summary["safety"]["runs_exact_verifiers"]
    assert not summary["safety"]["calls_sair"]
    assert not summary["safety"]["auto_submits"]
    assert all(record["generation_metadata"]["strategy"] == "model_sample_export" for record in scored)
    assert scored[0]["source_sample_export"]["sample_export_source"] == "target_r_seed_bank"
    assert scored[0]["generation_metadata"]["template_family_id"] == "model:mixed:r20:sparse_mixed_support_gcd1"
    assert scored[0]["generation_metadata"]["perturbation_mode"] == "sparse_mixed_support_gcd1"
    assert scored[0]["template_family_id"] == "model:mixed:r20:sparse_mixed_support_gcd1"
    assert scored[0]["basin_fingerprint"] == "fingerprint"
    assert summary["sample_export_source_counts"] == {"target_r_seed_bank": 1}


def test_score_all_mode_selects_every_exported_record_and_manifest_records_mode():
    args = argparse.Namespace(
        coeff_bound=4,
        target_r=None,
        target_t=None,
        prime_limit=5,
        max_local_search_steps=0,
        discriminant_weight=1.0,
        height_weight=1.0,
        cycle_diversity_weight=5.0,
        exact_score_timeout=1.0,
        exp_name="test_score_export_all",
        seed=123,
        translation_radius=1,
        max_records=None,
        score_all=True,
        local_search=False,
    )
    records = [
        {"sample_index": 0, "decoded_coefficients": [1] + [0] * 23, "temperature": 0.9, "top_k": 9, "device": "cuda"},
        {"sample_index": 1, "decoded_coefficients": [0, 1] + [0] * 22, "temperature": 0.9, "top_k": 9, "device": "cuda"},
        {"sample_index": 2, "decoded_coefficients": None, "temperature": 0.9, "top_k": 9, "device": "cuda"},
    ]

    scored, summary = score_export_records(records, args=args, source_path="samples.jsonl")
    manifest = build_split_manifest(
        score_summary=summary,
        gpu_summary=None,
        gpu_summary_path=None,
        source_commit="abc123",
        score_command="python3 scripts/igp24_score_sample_export.py --score_all true",
    )

    assert summary["records_read"] == 3
    assert summary["records_selected"] == 3
    assert summary["selection_mode"] == "all_explicit"
    assert summary["score_all"] is True
    assert summary["max_records"] is None
    assert summary["skipped_decode_records"] == 1
    assert summary["scored_records"] == len(scored)
    assert manifest["cpu_phase"]["selection_mode"] == "all_explicit"
    assert manifest["cpu_phase"]["max_records"] is None
    assert manifest["cpu_phase"]["records_selected"] == 3
    assert "--score_all true" in manifest["commands"]["cpu_score"]


def test_summarize_scored_records_counts_duplicate_hashes():
    records = [
        {"canonical_hash": "a", "score": 10.0, "verification_status": "proxy_scored"},
        {"canonical_hash": "a", "score": 12.0, "verification_status": "proxy_scored"},
        {"canonical_hash": "b", "score": -1.0, "verification_status": "rejected"},
    ]

    summary = summarize_scored_records(records)

    assert summary["scored_records"] == 3
    assert summary["proxy_scored_records"] == 2
    assert summary["rejected_records"] == 1
    assert summary["unique_canonical_hashes"] == 2
    assert summary["duplicate_canonical_hash_records"] == 1
    assert summary["duplicate_canonical_hashes"] == 1
    assert summary["best_score"] == 12.0


def test_build_split_manifest_links_gpu_and_cpu_artifacts(tmp_path):
    gpu_summary_path = tmp_path / "gpu_sampler_probe_summary.json"
    score_summary = {
        "source_path": str(tmp_path / "samples.jsonl"),
        "summary_path": str(tmp_path / "score_summary.json"),
        "report_path": str(tmp_path / "score_report.md"),
        "scored_jsonl_path": str(tmp_path / "scored_samples.jsonl"),
        "runtime_seconds": 2.5,
        "records_read": 1024,
        "records_selected": 512,
        "selection_mode": "capped",
        "max_records": 512,
        "decoded_input_records": 512,
        "scored_records": 512,
        "valid_records": 400,
        "rejected_records": 112,
        "local_search_enabled": False,
        "scored_record_summary": {"unique_canonical_hashes": 390, "duplicate_canonical_hash_records": 10},
    }
    gpu_summary = {
        "runs": {
            "gpu_sampler_probe": {
                "command_text": "python3 scripts/igp24_gpu_sampler_probe.py",
                "train_log_path": str(tmp_path / "train.log"),
                "returncode": 0,
                "timed_out": False,
                "interrupted": False,
                "runtime_seconds": 20.0,
                "sample_export_records": 1024,
                "sample_export_decoded_records": 1024,
                "post_train_cpu_sampling_scoring_avoided": True,
                "train_log": {"logged_device": "cuda", "eval_losses": [{}, {}], "max_cuda_reserved_mb": 100.0},
                "gpu_monitor": {
                    "max_gpu_utilization_percent": 90.0,
                    "avg_gpu_utilization_percent": 20.0,
                    "max_memory_used_mib": 5000.0,
                },
            }
        }
    }

    manifest = build_split_manifest(
        score_summary=score_summary,
        gpu_summary=gpu_summary,
        gpu_summary_path=gpu_summary_path,
        source_commit="abc123",
        score_command="python3 scripts/igp24_score_sample_export.py",
    )

    assert manifest["record_type"] == "igp24_split_workflow_manifest"
    assert manifest["source_commit"] == "abc123"
    assert manifest["artifacts"]["sample_export_path"].endswith("samples.jsonl")
    assert manifest["artifacts"]["train_log_path"].endswith("train.log")
    assert manifest["gpu_phase"]["sample_export_records"] == 1024
    assert manifest["gpu_phase"]["scoring_local_search_avoided"]
    assert manifest["cpu_phase"]["records_selected"] == 512
    assert manifest["cpu_phase"]["local_search_enabled"] is False
    assert manifest["dedup"]["unique_canonical_hashes"] == 390
    assert not manifest["safety"]["runs_exact_verifiers"]


def test_build_split_report_includes_manifest_counts():
    manifest = {
        "created_at_utc": "2026-07-04T00:00:00+00:00",
        "source_commit": "abc123",
        "commands": {"gpu_probe": "gpu cmd", "cpu_score": "cpu cmd"},
        "artifacts": {
            "sample_export_path": "samples.jsonl",
            "gpu_probe_summary_path": "gpu_summary.json",
            "train_log_path": "train.log",
            "cpu_score_summary_path": "score_summary.json",
            "scored_jsonl_path": "scored.jsonl",
        },
        "gpu_phase": {"runtime_seconds": 20.0, "max_gpu_utilization_percent": 90.0, "sample_export_records": 1024, "sample_export_decoded_records": 1024},
        "cpu_phase": {"runtime_seconds": 2.5, "records_selected": 512, "scored_records": 512, "valid_records": 400, "rejected_records": 112, "local_search_enabled": False},
        "dedup": {"unique_canonical_hashes": 390, "duplicate_canonical_hash_records": 10},
    }

    report = build_split_report(manifest)

    assert "IGP24 Split Workflow Report" in report
    assert "samples.jsonl" in report
    assert "scored.jsonl" in report
    assert "gpu cmd" in report
    assert "cpu cmd" in report


def test_build_score_report_includes_counts():
    summary = {
        "created_at_utc": "2026-07-04T00:00:00+00:00",
        "source_path": "samples.jsonl",
        "scored_jsonl_path": "scored.jsonl",
        "records_read": 2,
        "records_selected": 2,
        "decoded_input_records": 1,
        "skipped_decode_records": 1,
        "invalid_input_records": 0,
        "scored_records": 1,
        "valid_records": 1,
        "rejected_records": 0,
        "split_manifest_path": "manifest.json",
        "scored_record_summary": {"unique_canonical_hashes": 1, "duplicate_canonical_hash_records": 0},
        "local_search_enabled": False,
    }

    report = build_report(summary)

    assert "IGP24 Sample Export Scoring Report" in report
    assert "samples.jsonl" in report
    assert "scored.jsonl" in report
    assert "manifest.json" in report
    assert "no exact verifier execution" in report


def test_parser_false_boolean_defaults_are_not_truthy():
    parser = get_parser()

    args = parser.parse_args(["samples.jsonl", "--max_records", "2"])

    assert args.score_all is False
    assert args.local_search is False
