import json
import math
import random
from types import SimpleNamespace

import numpy as np
import pytest

sympy = pytest.importorskip("sympy")

from src.envs import ENVS, build_env
from src.datasets import load_initial_data
from src.envs.igp24 import (
    DEFAULT_MIXED_STRATEGY_WEIGHTS,
    IGP24DataPoint,
    IGP24_GENERATION_STRATEGIES,
    format_mixed_strategy_weights,
    parse_mixed_strategy_weights,
    resolve_generation_preset,
)
from src.igp24.ledger import CandidateLedger
from src.igp24.polynomial import (
    DEGREE,
    IGP24Error,
    analysis_to_record,
    analyze_candidate,
    canonicalize_under_translations,
    construct_polynomial,
    export_coefficients,
    is_irreducible_over_q,
    is_squarefree,
    mod_p_factorization_patterns,
    real_root_count,
    score_candidate,
    stable_canonical_hash,
    translate_coefficients,
    validate_coefficients,
)
from src.igp24.verifiers.magma import MagmaVerifier
from src.igp24.verifiers.pari import PARIVerifier
from src.igp24.verifiers.sair_api import SAIRAPIError, SAIRAPIVerifier
from scripts.igp24_r16_diversity_probe import (
    base_polynomial_from_layout,
    coefficient_line,
    coefficients_from_trial,
    lift_base_to_degree24,
    multiply_polynomials,
    off_block_exponents,
    trial_variants,
)


VALID = tuple([-2] + [0] * (DEGREE - 1))  # x^24 - 2, Eisenstein at 2.
REDUCIBLE = tuple([-1] + [0] * (DEGREE - 1))  # x^24 - 1.
NOT_SQUAREFREE = tuple([1] + [0] * 11 + [-2] + [0] * 11)  # (x^12 - 1)^2.


def test_construct_validate_and_export_format():
    assert validate_coefficients(VALID) == VALID
    poly = construct_polynomial(VALID)
    assert poly.degree() == DEGREE
    assert int(poly.LC()) == 1
    assert export_coefficients(VALID) == list(VALID) + [1]
    with pytest.raises(IGP24Error, match="wrong_length"):
        validate_coefficients([1, 2, 3])
    with pytest.raises(IGP24Error, match="coefficients_must_be_integers"):
        validate_coefficients([1.5] * DEGREE)


def test_exact_polynomial_utilities():
    assert is_squarefree(VALID)
    assert is_irreducible_over_q(VALID)
    assert not is_squarefree(NOT_SQUAREFREE)
    assert not is_irreducible_over_q(REDUCIBLE)
    assert real_root_count(REDUCIBLE) == 2
    analysis = analyze_candidate(VALID, coeff_bound=5, prime_limit=11)
    assert analysis.valid
    assert analysis.real_root_count == 2
    assert analysis.discriminant is not None
    assert analysis.log_abs_discriminant > 0
    assert analysis.coefficient_height == 2


def test_invalid_candidate_scoring_reasons():
    score, analysis = score_candidate([0] * DEGREE, coeff_bound=5)
    assert score == -1
    assert analysis.rejection_reason == "zero_constant_term"

    score, analysis = score_candidate(REDUCIBLE, coeff_bound=5)
    assert score == -1
    assert analysis.rejection_reason == "reducible_over_q"

    score, analysis = score_candidate(tuple([6] + [0] * (DEGREE - 1)), coeff_bound=5)
    assert score == -1
    assert analysis.rejection_reason == "coefficient_height_exceeds_bound"


def test_valid_synthetic_candidate_scoring_and_mod_p_patterns():
    score, analysis = score_candidate(VALID, coeff_bound=5, target_r=2, prime_limit=11)
    assert score >= 0
    assert analysis.valid
    assert analysis.score_components["target_r_distance"] == 0
    assert analysis.score_components["cycle_diversity_count"] >= 1
    assert analysis.score_components["final_score"] == score
    patterns = mod_p_factorization_patterns(VALID, analysis.discriminant, prime_limit=11)
    assert patterns
    for pattern in patterns:
        assert sum(pattern.degrees) == DEGREE


def test_canonical_hash_stability_and_translation():
    translated = translate_coefficients(VALID, 1)
    assert translated != VALID
    assert stable_canonical_hash(translated) == stable_canonical_hash(VALID)
    canonical, shift = canonicalize_under_translations(translated, radius=2)
    assert canonical == VALID
    assert shift == -1


def test_ledger_write_read_and_deduplication(tmp_path):
    score, analysis = score_candidate(VALID, coeff_bound=5, target_r=2, prime_limit=7)
    record = analysis_to_record(analysis, score, target_r=2, target_t="24T1", experiment_name="pytest")
    ledger_path = tmp_path / "candidates.jsonl"
    ledger = CandidateLedger(ledger_path)
    assert ledger.append(record)
    assert not ledger.append(record)
    reloaded = CandidateLedger(ledger_path)
    assert len(reloaded) == 1
    assert reloaded.records()[0]["canonical_hash"] == analysis.canonical_hash
    assert reloaded.records()[0]["exported_coefficients"][-1] == 1
    assert reloaded.records()[0]["score_components"]["final_score"] == score


def test_environment_registration_tokenizer_and_existing_env_imports(tmp_path):
    assert {"square", "isosceles", "sphere", "igp24"}.issubset(ENVS)
    params = SimpleNamespace(
        env_name="igp24",
        N=DEGREE,
        encoding_tokens="coefficients",
        coeff_bound=5,
        target_r=2,
        target_t="24T1",
        prime_limit=7,
        max_local_search_steps=3,
        discriminant_weight=1.0,
        height_weight=1.0,
        cycle_diversity_weight=5.0,
        exact_score_timeout=0.0,
        igp24_ledger_path=str(tmp_path / "ledger.jsonl"),
        igp24_write_ledger=False,
        igp24_translation_radius=2,
        igp24_generation_strategy="mixed",
        igp24_sparse_terms=4,
        igp24_low_height_bound=3,
        igp24_mixed_strategy_weights="uniform:0.1,low_height:0.2,sparse:0.25,lower_degree:0.2,structured:0.25",
        exp_name="pytest",
        seed=123,
    )
    env = build_env(params)
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=VALID)
    encoded = env.tokenizer.encode(datapoint)
    decoded = env.tokenizer.decode(encoded)
    assert decoded is not None
    assert decoded.coefficients == VALID


def _igp24_params(tmp_path, seed=123, strategy="mixed", encoding_tokens="coefficients", target_r_conditioning_mode="none"):
    return SimpleNamespace(
        env_name="igp24",
        N=DEGREE,
        encoding_tokens=encoding_tokens,
        coeff_bound=5,
        target_r=2,
        target_t="24T1",
        prime_limit=7,
        max_local_search_steps=3,
        discriminant_weight=1.0,
        height_weight=1.0,
        cycle_diversity_weight=5.0,
        exact_score_timeout=0.0,
        igp24_ledger_path=str(tmp_path / f"ledger_{seed}_{strategy}.jsonl"),
        igp24_write_ledger=False,
        igp24_translation_radius=2,
        igp24_generation_strategy=strategy,
        igp24_generation_preset="none",
        igp24_target_r_conditioning_mode=target_r_conditioning_mode,
        igp24_training_jsonl=[],
        igp24_training_jsonl_target_rs="",
        igp24_training_jsonl_max_rows=0,
        igp24_training_jsonl_max_abs_coeff=0,
        igp24_sparse_terms=4,
        igp24_low_height_bound=3,
        igp24_mixed_strategy_weights="uniform:0.1,low_height:0.2,sparse:0.25,lower_degree:0.2,structured:0.25",
        exp_name="pytest",
        seed=seed,
    )


def test_control_token_conditioning_roundtrips_fixed_coefficients(tmp_path):
    params = _igp24_params(tmp_path, target_r_conditioning_mode="control_token")
    env = build_env(params)
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=VALID, conditioning_target_r=16)

    encoded = env.tokenizer.encode(datapoint)
    decoded = env.tokenizer.decode(encoded)

    assert encoded[0] == env.tokenizer.stoi["BOS"]
    assert encoded[1] == env.tokenizer.stoi["R16"]
    assert decoded is not None
    assert decoded.coefficients == VALID
    assert env.tokenizer.block_size_for_max_len(24) == 27


def test_decimal_tokenizer_roundtrips_high_coefficients_with_target_r(tmp_path):
    params = _igp24_params(
        tmp_path,
        encoding_tokens="decimal_coefficients",
        target_r_conditioning_mode="control_token",
    )
    env = build_env(params)
    coeffs = tuple([434550251520000, -2258902656, 0, 17] + [0] * 20)
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=coeffs, conditioning_target_r=20)

    encoded = env.tokenizer.encode(datapoint)
    decoded = env.tokenizer.decode(encoded)

    assert encoded[0] == env.tokenizer.stoi["BOS"]
    assert encoded[1] == env.tokenizer.stoi["R20"]
    assert env.tokenizer.stoi["D9"] < len(env.tokenizer.itos)
    assert len(env.tokenizer.itos) < 40
    assert decoded is not None
    assert decoded.coefficients == coeffs


def test_load_initial_data_from_igp24_jsonl_carries_target_r_conditioning(tmp_path):
    dataset_path = tmp_path / "active.jsonl"
    rows = [
        {
            "coefficients": [1] + [0] * 23 + [1],
            "r": 12,
            "canonical_hash": "h12",
            "derived_class_label": "accepted_useful_score_positive",
            "score_aware_supervision": {"label": "score_positive", "reward": 3.0, "weight": 4.0},
            "train_eval_split": "train",
        },
        {
            "coefficients": [2] + [0] * 23 + [1],
            "r": 16,
            "canonical_hash": "h16",
            "derived_class_label": "accepted_duplicate_collapsed_basin",
            "train_eval_split": "eval",
        },
        {
            "coefficients": [3] + [0] * 23 + [1],
            "r": 4,
            "canonical_hash": "h4",
            "derived_class_label": "wrong_real_root_count",
            "train_eval_split": "train",
        },
    ]
    dataset_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    params = _igp24_params(tmp_path, encoding_tokens="decimal_coefficients", target_r_conditioning_mode="control_token")
    params.dump_path = str(tmp_path / "dump")
    params.ntest = 1
    params.igp24_training_jsonl = [str(dataset_path)]
    params.igp24_training_jsonl_target_rs = "12,16"

    train_set, test_set = load_initial_data(params, IGP24DataPoint)

    assert [row.conditioning_target_r for row in train_set] == [12]
    assert [row.conditioning_target_r for row in test_set] == [16]
    assert train_set[0].score == 12.0
    assert params.igp24_training_jsonl_loaded_rows == 2
    env = build_env(params)
    encoded = env.tokenizer.encode(train_set[0])
    assert encoded[1] == env.tokenizer.stoi["R12"]


def test_environment_seed_resets_generation(tmp_path):
    build_env(_igp24_params(tmp_path, seed=777, strategy="lower_degree"))
    first = IGP24DataPoint._generate_coefficients()
    build_env(_igp24_params(tmp_path, seed=777, strategy="lower_degree"))
    second = IGP24DataPoint._generate_coefficients()

    assert first == second


def test_generation_strategies_are_bounded_and_metadata_is_set():
    IGP24DataPoint.COEFF_BOUND = 5
    IGP24DataPoint.SPARSE_TERMS = 4
    IGP24DataPoint.LOW_HEIGHT_BOUND = 2
    for strategy in [
        "uniform",
        "low_height",
        "sparse",
        "lower_degree",
        "structured",
        "four_real_seed",
        "quartic_lift",
        "fixed_sparse_template",
    ]:
        np_seed = {
            "uniform": 11,
            "low_height": 12,
            "sparse": 13,
            "lower_degree": 14,
            "structured": 15,
            "four_real_seed": 16,
            "quartic_lift": 17,
            "fixed_sparse_template": 18,
        }[strategy]
        np.random.seed(np_seed)
        IGP24DataPoint.GENERATION_STRATEGY = strategy
        coeffs, observed = IGP24DataPoint._generate_coefficients()
        assert observed == strategy
        assert len(coeffs) == DEGREE
        assert coeffs[0] != 0
        assert max(abs(c) for c in coeffs) <= IGP24DataPoint.COEFF_BOUND
        if strategy == "sparse":
            assert sum(1 for c in coeffs if c != 0) <= IGP24DataPoint.SPARSE_TERMS
        if strategy in {"low_height", "structured"}:
            non_constant = [abs(c) for c in coeffs[1:] if c != 0]
            assert all(c <= IGP24DataPoint.LOW_HEIGHT_BOUND for c in non_constant)
        if strategy == "four_real_seed":
            assert coeffs[0] > 0
            assert coeffs[2] < 0
            assert coeffs[4] == 1
            assert coeffs[20] == coeffs[0]
            assert coeffs[22] == coeffs[2]
            assert any(coeffs[index] != 0 for index in range(1, DEGREE, 2))
        if strategy == "quartic_lift":
            core_support = set(IGP24DataPoint._quartic_lift_core_support())
            assert coeffs[6] != 0
            assert coeffs[12] != 0
            assert coeffs[18] != 0
            assert any(coeffs[index] != 0 for index in range(DEGREE) if index not in core_support)
        if strategy == "fixed_sparse_template":
            details = IGP24DataPoint.LAST_GENERATION_DETAILS
            support = details["fixed_sparse_support"]
            assert details["fixed_sparse_template_name"]
            assert 0 in support
            assert sorted(index for index, coeff in enumerate(coeffs) if coeff != 0) == sorted(support)
            assert set(details["fixed_sparse_coefficients"]) == {str(index) for index in support}


def test_fixed_sparse_template_generation_is_deterministic_and_cli_selectable(tmp_path):
    params = _igp24_params(tmp_path, seed=4242, strategy="fixed_sparse_template")
    build_env(params)
    first_coeffs, first_strategy = IGP24DataPoint._generate_coefficients()
    first_details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)

    build_env(params)
    second_coeffs, second_strategy = IGP24DataPoint._generate_coefficients()
    second_details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)

    assert "fixed_sparse_template" in IGP24_GENERATION_STRATEGIES
    assert first_strategy == "fixed_sparse_template"
    assert second_strategy == "fixed_sparse_template"
    assert first_coeffs == second_coeffs
    assert first_details == second_details
    assert len(first_coeffs) == DEGREE
    assert max(abs(c) for c in first_coeffs) <= params.coeff_bound
    assert sorted(index for index, coeff in enumerate(first_coeffs) if coeff != 0) == sorted(first_details["fixed_sparse_support"])


def test_r8_quartic_lift_generation_emits_valid_composed_r8_template():
    IGP24DataPoint.COEFF_BOUND = 16
    IGP24DataPoint.SPARSE_TERMS = 4
    IGP24DataPoint.LOW_HEIGHT_BOUND = 2
    IGP24DataPoint.GENERATION_STRATEGY = "r8_quartic_lift"

    np.random.seed(824)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)

    assert "r8_quartic_lift" in IGP24_GENERATION_STRATEGIES
    assert observed == "r8_quartic_lift"
    assert len(coeffs) == DEGREE
    assert coeffs[0] != 0
    assert max(abs(c) for c in coeffs) <= IGP24DataPoint.COEFF_BOUND
    assert sorted(index for index, coeff in enumerate(coeffs) if coeff != 0) == [0, 6, 12, 18]
    assert details["r8_quartic_lift_template_name"]
    assert details["r8_quartic_lift_core_support"] == [0, 6, 12, 18]
    assert details["r8_quartic_lift_positive_quartic_roots"] == 4
    assert details["r8_quartic_lift_perturbation"] == "none_pure_composed_seed"
    assert details["target_r_heuristic"] == 8
    assert details["composed_support_divisor"] == 6

    score, analysis = IGP24DataPoint._score_coefficients(coeffs)
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 8


def _support_profile(coeffs):
    support = [index for index, coefficient in enumerate(coeffs) if coefficient != 0]
    support.append(DEGREE)
    support_gcd = 0
    for exponent in support:
        if exponent > 0:
            support_gcd = math.gcd(support_gcd, exponent)
    return support, support_gcd, all(exponent % 2 == 0 for exponent in support)


def test_r8_quartic_lift_perturbed_generation_emits_exact_r8_off_core_row():
    IGP24DataPoint.COEFF_BOUND = 16
    IGP24DataPoint.SPARSE_TERMS = 4
    IGP24DataPoint.LOW_HEIGHT_BOUND = 2
    IGP24DataPoint.TARGET_R = 8
    IGP24DataPoint.PRIME_LIMIT = 7
    IGP24DataPoint.EXACT_SCORE_TIMEOUT = 3.0
    IGP24DataPoint.TRANSLATION_RADIUS = 2
    IGP24DataPoint.KNOWN_HASHES = set()
    IGP24DataPoint.GENERATION_STRATEGY = "r8_quartic_lift_perturbed"

    np.random.seed(2811)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)
    support, support_gcd, even_support = _support_profile(coeffs)
    off_core = sorted(index for index, coeff in enumerate(coeffs) if coeff != 0 and index not in {0, 6, 12, 18})

    assert "r8_quartic_lift_perturbed" in IGP24_GENERATION_STRATEGIES
    assert observed == "r8_quartic_lift_perturbed"
    assert len(coeffs) == DEGREE
    assert coeffs[0] != 0
    assert max(abs(c) for c in coeffs) <= IGP24DataPoint.COEFF_BOUND
    assert sorted(index for index, coeff in enumerate(coeffs) if coeff != 0 and index in {0, 6, 12, 18}) == [
        0,
        6,
        12,
        18,
    ]
    assert off_core
    assert any(index % 2 == 1 for index in off_core)
    assert support_gcd == 1
    assert not even_support
    assert details["source_family"] == "r8_quartic_lift_perturbed"
    assert details["r8_quartic_lift_template_name"] == "four_positive_fibers_d"
    assert details["r8_quartic_lift_core_support"] == [0, 6, 12, 18]
    assert details["r8_quartic_lift_perturbation"] == "odd_off_core_support_gcd_1"
    assert details["r8_quartic_lift_family_key"]
    assert details["r8_quartic_lift_perturbation_mode"] in {
        "odd_single_off_core",
        "odd_pair_off_core",
        "odd_triple_off_core",
    }
    assert details["r8_quartic_lift_support_gcd"] == 1
    assert details["r8_quartic_lift_even_support"] is False
    assert details["target_r_heuristic"] == 8
    assert details["validated_real_root_count"] == 8
    assert set(details["r8_quartic_lift_perturbation_exponents"]) == set(off_core)

    score, analysis = IGP24DataPoint._score_coefficients(coeffs)
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 8
    assert analysis.irreducible
    assert analysis.squarefree


def test_r16_quadratic_lift_generation_emits_valid_composed_r16_template():
    IGP24DataPoint.COEFF_BOUND = 703
    IGP24DataPoint.SPARSE_TERMS = 4
    IGP24DataPoint.LOW_HEIGHT_BOUND = 2
    IGP24DataPoint.GENERATION_STRATEGY = "r16_quadratic_lift"
    IGP24DataPoint.EXACT_SCORE_TIMEOUT = 3.0

    np.random.seed(1601)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)

    assert "r16_quadratic_lift" in IGP24_GENERATION_STRATEGIES
    assert observed == "r16_quadratic_lift"
    assert len(coeffs) == DEGREE
    assert coeffs[0] != 0
    assert max(abs(c) for c in coeffs) <= IGP24DataPoint.COEFF_BOUND
    assert sorted(index for index, coeff in enumerate(coeffs) if coeff != 0) == list(range(0, DEGREE, 2))
    assert details["r16_quadratic_lift_template_name"]
    assert details["r16_quadratic_lift_core_support"] == list(range(0, DEGREE, 2))
    assert details["r16_quadratic_lift_positive_base_roots"] == 8
    assert details["r16_quadratic_lift_base_degree"] == 12
    assert details["r16_quadratic_lift_minimum_coeff_bound"] == 703
    assert details["target_r_heuristic"] == 16
    assert details["composed_support_divisor"] == 2

    score, analysis = IGP24DataPoint._score_coefficients(coeffs)
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 16


def test_r16_diversity_probe_helpers_build_degree24_lift():
    assert multiply_polynomials([1, 2], [3, 4]) == [3, 10, 8]
    base = base_polynomial_from_layout((1, 2, 3, 4, 6, 8, 10, 12), (((1, 1), (1, 2))))
    coeffs = lift_base_to_degree24(base)

    assert len(base) == 13
    assert base[-1] == 1
    assert len(coeffs) == DEGREE
    assert coeffs[0] == base[0]
    assert coeffs[1] == 0
    assert coeffs[22] == base[11]
    assert coefficient_line([*coeffs, 1]).endswith(",1")


def test_r16_diversity_probe_multi_odd_modes_escape_one_odd_support():
    base = base_polynomial_from_layout((1, 2, 3, 4, 6, 8, 10, 12), (((1, 1), (1, 2))))
    coeffs, metadata = coefficients_from_trial(
        {
            "mode": "two_odd_perturbed_near_composed",
            "positive_roots": (1, 2, 3, 4, 6, 8, 10, 12),
            "quadratics": (((1, 1), (1, 2))),
            "base_coefficients": base,
            "odd_perturbations": [(3, 2), (15, -1)],
        }
    )

    assert coeffs[3] == 2
    assert coeffs[15] == -1
    assert metadata["composed_support"] is False
    assert metadata["r16_diversity_off_block_perturbation_terms"] == 2
    assert off_block_exponents([*coeffs, 1], divisor=2) == [3, 15]

    variants = list(
        trial_variants(
            rng=random.Random(123),
            max_trials=4,
            include_exact=False,
            include_odd=False,
            include_two_odd=True,
            include_three_odd=True,
            include_mixed_even_odd=True,
            perturbations_per_family_mode=2,
        )
    )
    assert variants
    assert {variant["mode"] for variant in variants}.issubset(
        {
            "two_odd_perturbed_near_composed",
            "three_odd_perturbed_near_composed",
            "mixed_even_odd_perturbed",
        }
    )
    for variant in variants:
        assert len({index for index, _delta in variant["odd_perturbations"]}) >= 2


def test_mixed_strategy_weights_are_normalized_and_selectable():
    weights = parse_mixed_strategy_weights("uniform:1,structured:3")
    assert weights["uniform"] == 0.25
    assert weights["structured"] == 0.75
    assert weights["sparse"] == 0.0
    assert weights["four_real_seed"] == 0.0
    assert weights["quartic_lift"] == 0.0
    assert weights["r8_quartic_lift"] == 0.0
    assert weights["r8_quartic_lift_perturbed"] == 0.0
    assert weights["r16_quadratic_lift"] == 0.0
    assert weights["fixed_sparse_template"] == 0.0
    assert "structured:0.7500" in format_mixed_strategy_weights(weights)

    IGP24DataPoint.GENERATION_STRATEGY = "mixed"
    IGP24DataPoint.COEFF_BOUND = 5
    IGP24DataPoint.MIXED_STRATEGY_WEIGHTS = parse_mixed_strategy_weights("quartic_lift:1")
    np.random.seed(100)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    assert observed == "quartic_lift"
    assert len(coeffs) == DEGREE

    IGP24DataPoint.MIXED_STRATEGY_WEIGHTS = parse_mixed_strategy_weights("fixed_sparse_template:1")
    np.random.seed(101)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    assert observed == "fixed_sparse_template"
    assert len(coeffs) == DEGREE

    IGP24DataPoint.COEFF_BOUND = 16
    IGP24DataPoint.MIXED_STRATEGY_WEIGHTS = parse_mixed_strategy_weights("r8_quartic_lift:1")
    np.random.seed(102)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    assert observed == "r8_quartic_lift"
    assert len(coeffs) == DEGREE

    IGP24DataPoint.COEFF_BOUND = 16
    IGP24DataPoint.TARGET_R = 8
    IGP24DataPoint.PRIME_LIMIT = 7
    IGP24DataPoint.EXACT_SCORE_TIMEOUT = 3.0
    IGP24DataPoint.MIXED_STRATEGY_WEIGHTS = parse_mixed_strategy_weights("r8_quartic_lift_perturbed:1")
    np.random.seed(104)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    assert observed == "r8_quartic_lift_perturbed"
    assert len(coeffs) == DEGREE

    IGP24DataPoint.COEFF_BOUND = 703
    IGP24DataPoint.MIXED_STRATEGY_WEIGHTS = parse_mixed_strategy_weights("r16_quadratic_lift:1")
    np.random.seed(103)
    coeffs, observed = IGP24DataPoint._generate_coefficients()
    assert observed == "r16_quadratic_lift"
    assert len(coeffs) == DEGREE


def test_generation_presets_resolve_explicitly_without_changing_default():
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["uniform"] == 0.10
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["low_height"] == 0.20
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["sparse"] == 0.25
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["lower_degree"] == 0.20
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["structured"] == 0.25
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["four_real_seed"] == 0.0
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["quartic_lift"] == 0.0
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["r8_quartic_lift"] == 0.0
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["r8_quartic_lift_perturbed"] == 0.0
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["r16_quadratic_lift"] == 0.0
    assert DEFAULT_MIXED_STRATEGY_WEIGHTS["fixed_sparse_template"] == 0.0

    no_preset = resolve_generation_preset(
        "none",
        "sparse",
        "uniform:0.1,low_height:0.2,sparse:0.25,lower_degree:0.2,structured:0.25",
    )
    assert no_preset["preset_name"] == "none"
    assert no_preset["target_r_intent"] is None
    assert no_preset["resolved_strategy"] == "sparse"
    assert no_preset["resolved_mixed_strategy_weights"]["four_real_seed"] == 0.0

    r0 = resolve_generation_preset("r0", "mixed", "uniform:1")
    assert r0["resolved_strategy"] == "structured"
    assert r0["target_r_intent"] == 0

    r2 = resolve_generation_preset("r2", "uniform", "uniform:1")
    assert r2["resolved_strategy"] == "mixed"
    assert r2["target_r_intent"] == 2
    assert r2["resolved_mixed_strategy_weights"]["sparse"] == 0.55
    assert r2["resolved_mixed_strategy_weights"]["structured"] == 0.45

    r4 = resolve_generation_preset("r4", "uniform", "uniform:1")
    assert r4["resolved_strategy"] == "mixed"
    assert r4["target_r_intent"] == 4
    assert r4["resolved_mixed_strategy_weights"]["four_real_seed"] == 0.8
    assert r4["resolved_mixed_strategy_weights"]["sparse"] == 0.2
    assert r4["resolved_mixed_strategy_weights"]["fixed_sparse_template"] == 0.0


def test_environment_applies_generation_preset_and_keeps_seed_determinism(tmp_path):
    params = _igp24_params(tmp_path, seed=888, strategy="uniform")
    params.target_r = 4
    params.igp24_generation_preset = "r4"
    build_env(params)
    assert IGP24DataPoint.GENERATION_PRESET == "r4"
    assert IGP24DataPoint.GENERATION_PRESET_TARGET_R == 4
    assert IGP24DataPoint.GENERATION_STRATEGY == "mixed"
    assert IGP24DataPoint.MIXED_STRATEGY_WEIGHTS["four_real_seed"] == 0.8
    first = IGP24DataPoint._generate_coefficients()

    build_env(params)
    second = IGP24DataPoint._generate_coefficients()
    assert first == second


def test_local_search_determinism_under_fixed_seed(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 5,
            "TARGET_R": 2,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 5,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 0.0,
            "LEDGER_PATH": str(tmp_path / "ledger.jsonl"),
            "WRITE_LEDGER": False,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 999,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "mixed",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 3,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("uniform:0.1,low_height:0.2,sparse:0.25,lower_degree:0.2,structured:0.25"),
            "GENERATION_PRESET": "none",
            "GENERATION_PRESET_TARGET_R": None,
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    first = IGP24DataPoint(N=DEGREE, coeffs=VALID)
    second = IGP24DataPoint(N=DEGREE, coeffs=VALID)
    first.calc_score()
    second.calc_score()
    first.local_search(improve_with_local_search=True)
    second.local_search(improve_with_local_search=True)
    assert first.coefficients == second.coefficients
    assert first.score == second.score
    assert first.score >= 0 or first.analysis.rejection_reason is not None
    assert first.local_search_stats == second.local_search_stats
    assert first.local_search_stats["attempted"] <= 5
    assert "accepted_moves" in first.local_search_stats


def test_ledger_records_generation_and_local_search_metadata(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 5,
            "TARGET_R": 2,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 2,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 0.0,
            "LEDGER_PATH": str(tmp_path / "ledger.jsonl"),
            "WRITE_LEDGER": True,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 321,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "mixed",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("four_real_seed:0.8,sparse:0.2"),
            "GENERATION_PRESET": "r4",
            "GENERATION_PRESET_TARGET_R": 4,
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=VALID, generation_strategy="four_real_seed")
    datapoint.calc_score()
    datapoint.local_search(improve_with_local_search=True)
    records = CandidateLedger(tmp_path / "ledger.jsonl").records()
    assert records
    latest = records[-1]
    assert latest["generation_metadata"]["strategy"] == "four_real_seed"
    assert latest["generation_metadata"]["generation_preset"] == "r4"
    assert latest["generation_metadata"]["preset_target_r"] == 4
    assert latest["generation_metadata"]["resolved_generation_strategy"] == "mixed"
    assert "resolved_mixed_strategy_weights" in latest["generation_metadata"]
    assert latest["generation_metadata"]["target_r_heuristic"] == 4
    assert "perturbed_(x^2-a)(x^2-b)" in latest["generation_metadata"]["seed_template"]
    assert "mixed_strategy_weights" in latest["generation_metadata"]
    assert latest["local_search_metadata"]["max_steps"] == 2
    assert "score_components" in latest


def test_quartic_lift_ledger_metadata_identifies_template_and_perturbations(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 5,
            "TARGET_R": 4,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 0,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 0.0,
            "LEDGER_PATH": str(tmp_path / "quartic_lift_ledger.jsonl"),
            "WRITE_LEDGER": True,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 701,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "quartic_lift",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("quartic_lift:1"),
            "GENERATION_PRESET": "none",
            "GENERATION_PRESET_TARGET_R": None,
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    coeffs = [0] * DEGREE
    coeffs[0] = 2
    coeffs[1] = 1
    coeffs[6] = 1
    coeffs[12] = -3
    coeffs[18] = -1
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=tuple(coeffs), generation_strategy="quartic_lift")
    datapoint.calc_score()
    records = CandidateLedger(tmp_path / "quartic_lift_ledger.jsonl").records()

    assert records
    latest = records[-1]
    assert latest["real_root_count"] == 4
    assert latest["generation_metadata"]["strategy"] == "quartic_lift"
    assert latest["generation_metadata"]["target_r_heuristic"] == 4
    assert latest["generation_metadata"]["quartic_lift_core_support"] == [0, 6, 12, 18]
    assert latest["generation_metadata"]["quartic_lift_coefficients_y"] == [2, 1, -3, -1, 1]
    assert latest["generation_metadata"]["perturbation_coefficients"] == {"1": 1}
    assert "y=x^6" in latest["generation_metadata"]["seed_template"]


def test_r8_quartic_lift_ledger_metadata_identifies_composed_template(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 16,
            "TARGET_R": 8,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 0,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 0.0,
            "LEDGER_PATH": str(tmp_path / "r8_quartic_lift_ledger.jsonl"),
            "WRITE_LEDGER": True,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 824,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "r8_quartic_lift",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("r8_quartic_lift:1"),
            "GENERATION_PRESET": "none",
            "GENERATION_PRESET_TARGET_R": None,
            "LAST_GENERATION_DETAILS": {
                "r8_quartic_lift_template_name": "four_positive_fibers_a",
                "r8_quartic_lift_core_support": [0, 6, 12, 18],
                "r8_quartic_lift_coefficients_y": [1, -7, 14, -8, 1],
                "r8_quartic_lift_positive_quartic_roots": 4,
                "r8_quartic_lift_minimum_coeff_bound": 14,
                "r8_quartic_lift_perturbation": "none_pure_composed_seed",
            },
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    coeffs = [0] * DEGREE
    coeffs[0] = 1
    coeffs[6] = -7
    coeffs[12] = 14
    coeffs[18] = -8
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=tuple(coeffs), generation_strategy="r8_quartic_lift")
    datapoint.generation_details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)
    datapoint.calc_score()
    records = CandidateLedger(tmp_path / "r8_quartic_lift_ledger.jsonl").records()

    assert records
    latest = records[-1]
    metadata = latest["generation_metadata"]
    assert latest["real_root_count"] == 8
    assert metadata["strategy"] == "r8_quartic_lift"
    assert metadata["target_r_heuristic"] == 8
    assert metadata["seed_template"] == "pure_g(y)_with_four_positive_roots_and_y=x^6"
    assert metadata["r8_quartic_lift_template_name"] == "four_positive_fibers_a"
    assert metadata["r8_quartic_lift_core_support"] == [0, 6, 12, 18]
    assert metadata["r8_quartic_lift_coefficients_y"] == [1, -7, 14, -8, 1]
    assert metadata["r8_quartic_lift_positive_quartic_roots"] == 4
    assert metadata["r8_quartic_lift_minimum_coeff_bound"] == 14
    assert metadata["r8_quartic_lift_perturbation"] == "none_pure_composed_seed"
    assert metadata["exact_composed_support_divisor"] == 6
    assert metadata["composed_support"]


def test_r8_quartic_lift_perturbed_ledger_metadata_identifies_escape_support(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 16,
            "TARGET_R": 8,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 0,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 3.0,
            "LEDGER_PATH": str(tmp_path / "r8_quartic_lift_perturbed_ledger.jsonl"),
            "WRITE_LEDGER": True,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 2811,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "r8_quartic_lift_perturbed",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("r8_quartic_lift_perturbed:1"),
            "GENERATION_PRESET": "none",
            "GENERATION_PRESET_TARGET_R": None,
            "LAST_GENERATION_DETAILS": {
                "source_family": "r8_quartic_lift_perturbed",
                "r8_quartic_lift_family_key": "four_positive_fibers_d:odd_single_off_core:11:-1",
                "r8_quartic_lift_template_name": "four_positive_fibers_d",
                "r8_quartic_lift_core_support": [0, 6, 12, 18],
                "r8_quartic_lift_coefficients_y": [1, -8, 16, -8, 1],
                "r8_quartic_lift_positive_quartic_roots": 4,
                "r8_quartic_lift_minimum_coeff_bound": 16,
                "r8_quartic_lift_perturbation": "odd_off_core_support_gcd_1",
                "r8_quartic_lift_perturbation_mode": "odd_single_off_core",
                "r8_quartic_lift_perturbation_exponents": [11],
                "r8_quartic_lift_perturbation_coefficients": {"11": -1},
                "r8_quartic_lift_support_gcd": 1,
                "r8_quartic_lift_even_support": False,
                "validated_real_root_count": 8,
                "generation_attempts": 1,
            },
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    coeffs = [0] * DEGREE
    coeffs[0] = 1
    coeffs[6] = -8
    coeffs[11] = -1
    coeffs[12] = 16
    coeffs[18] = -8
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=tuple(coeffs), generation_strategy="r8_quartic_lift_perturbed")
    datapoint.generation_details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)
    datapoint.calc_score()
    records = CandidateLedger(tmp_path / "r8_quartic_lift_perturbed_ledger.jsonl").records()

    assert records
    latest = records[-1]
    metadata = latest["generation_metadata"]
    assert latest["real_root_count"] == 8
    assert metadata["strategy"] == "r8_quartic_lift_perturbed"
    assert metadata["target_r_heuristic"] == 8
    assert metadata["source_family"] == "r8_quartic_lift_perturbed"
    assert metadata["seed_template"] == "perturbed_g(y)_with_four_positive_roots_and_y=x^6"
    assert metadata["r8_quartic_lift_family_key"] == "four_positive_fibers_d:odd_single_off_core:11:-1"
    assert metadata["r8_quartic_lift_template_name"] == "four_positive_fibers_d"
    assert metadata["r8_quartic_lift_core_support"] == [0, 6, 12, 18]
    assert metadata["r8_quartic_lift_coefficients_y"] == [1, -8, 16, -8, 1]
    assert metadata["r8_quartic_lift_perturbation"] == "odd_off_core_support_gcd_1"
    assert metadata["r8_quartic_lift_perturbation_mode"] == "odd_single_off_core"
    assert metadata["r8_quartic_lift_perturbation_exponents"] == [11]
    assert metadata["r8_quartic_lift_perturbation_coefficients"] == {"11": -1}
    assert metadata["r8_quartic_lift_support_gcd"] == 1
    assert metadata["r8_quartic_lift_even_support"] is False
    assert metadata["exact_composed_support_divisor"] == 1
    assert metadata["composed_support"] is False
    assert metadata["validated_real_root_count"] == 8
    assert metadata["generation_attempts"] == 1


def test_r16_quadratic_lift_ledger_metadata_identifies_composed_template(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 703,
            "TARGET_R": 16,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 0,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 3.0,
            "LEDGER_PATH": str(tmp_path / "r16_quadratic_lift_ledger.jsonl"),
            "WRITE_LEDGER": True,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 1601,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "r16_quadratic_lift",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("r16_quadratic_lift:1"),
            "GENERATION_PRESET": "none",
            "GENERATION_PRESET_TARGET_R": None,
            "LAST_GENERATION_DETAILS": {
                "r16_quadratic_lift_template_name": "eight_positive_fibers_c2_minus1",
                "r16_quadratic_lift_core_support": list(range(0, DEGREE, 2)),
                "r16_quadratic_lift_coefficients_y": [8, -48, 9, 364, -543, -216, 703, -176, -186, 84, 7, -8, 1],
                "r16_quadratic_lift_positive_base_roots": 8,
                "r16_quadratic_lift_base_degree": 12,
                "r16_quadratic_lift_minimum_coeff_bound": 703,
                "r16_quadratic_lift_perturbation": "near_product_quadratic_factors_c2_minus1",
            },
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    y_coefficients = [8, -48, 9, 364, -543, -216, 703, -176, -186, 84, 7, -8, 1]
    coeffs = [0] * DEGREE
    for exponent, coefficient in zip(range(0, DEGREE, 2), y_coefficients[:12]):
        coeffs[exponent] = coefficient
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=tuple(coeffs), generation_strategy="r16_quadratic_lift")
    datapoint.generation_details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)
    datapoint.calc_score()
    records = CandidateLedger(tmp_path / "r16_quadratic_lift_ledger.jsonl").records()

    assert records
    latest = records[-1]
    metadata = latest["generation_metadata"]
    assert latest["real_root_count"] == 16
    assert metadata["strategy"] == "r16_quadratic_lift"
    assert metadata["target_r_heuristic"] == 16
    assert metadata["seed_template"] == "pure_g(y)_with_eight_positive_roots_and_y=x^2"
    assert metadata["r16_quadratic_lift_template_name"] == "eight_positive_fibers_c2_minus1"
    assert metadata["r16_quadratic_lift_core_support"] == list(range(0, DEGREE, 2))
    assert metadata["r16_quadratic_lift_coefficients_y"] == y_coefficients
    assert metadata["r16_quadratic_lift_positive_base_roots"] == 8
    assert metadata["r16_quadratic_lift_base_degree"] == 12
    assert metadata["r16_quadratic_lift_minimum_coeff_bound"] == 703
    assert metadata["r16_quadratic_lift_perturbation"] == "near_product_quadratic_factors_c2_minus1"
    assert metadata["exact_composed_support_divisor"] == 2
    assert metadata["composed_support"]


def test_fixed_sparse_template_ledger_metadata_identifies_support(tmp_path):
    IGP24DataPoint._update_class_params(
        {
            "COEFF_BOUND": 5,
            "TARGET_R": 2,
            "TARGET_T": None,
            "PRIME_LIMIT": 7,
            "MAX_LOCAL_SEARCH_STEPS": 0,
            "DISCRIMINANT_WEIGHT": 1.0,
            "HEIGHT_WEIGHT": 1.0,
            "CYCLE_DIVERSITY_WEIGHT": 5.0,
            "EXACT_SCORE_TIMEOUT": 0.0,
            "LEDGER_PATH": str(tmp_path / "fixed_sparse_template_ledger.jsonl"),
            "WRITE_LEDGER": True,
            "EXPERIMENT_NAME": "pytest",
            "SEED": 4242,
            "TRANSLATION_RADIUS": 2,
            "KNOWN_HASHES": set(),
            "GENERATION_STRATEGY": "fixed_sparse_template",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "MIXED_STRATEGY_WEIGHTS": parse_mixed_strategy_weights("fixed_sparse_template:1"),
            "GENERATION_PRESET": "none",
            "GENERATION_PRESET_TARGET_R": None,
            "LAST_GENERATION_DETAILS": {
                "fixed_sparse_template_name": "r2_even_spine",
                "fixed_sparse_support": [0, 2, 4, 6, 12, 18, 22],
                "fixed_sparse_coefficients": {"0": -2},
                "target_r_heuristic": 2,
            },
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=VALID, generation_strategy="fixed_sparse_template")
    datapoint.generation_details = dict(IGP24DataPoint.LAST_GENERATION_DETAILS)
    datapoint.calc_score()
    records = CandidateLedger(tmp_path / "fixed_sparse_template_ledger.jsonl").records()

    assert records
    latest = records[-1]
    metadata = latest["generation_metadata"]
    assert metadata["strategy"] == "fixed_sparse_template"
    assert metadata["fixed_sparse_template_name"] == "r2_even_spine"
    assert metadata["fixed_sparse_support"] == [0, 2, 4, 6, 12, 18, 22]
    assert metadata["fixed_sparse_coefficients"] == {"0": -2}
    assert metadata["fixed_sparse_coefficient_bound"] == 5
    assert metadata["target_r_heuristic"] == 2
    assert metadata["fixed_sparse_extra_nonzero_indices"] == []
    assert metadata["seed_template"] == "fixed_support_sparse_integer_coefficients"


def test_verifier_stubs_fail_gracefully_and_sair_is_dry_run(tmp_path, monkeypatch):
    pari_result = PARIVerifier(executable="definitely_missing_gp").verify(VALID)
    magma_result = MagmaVerifier(executable="definitely_missing_magma").verify(VALID)
    assert pari_result.status == "unverified"
    assert "not found" in pari_result.message
    assert magma_result.status == "unverified"
    assert "not found" in magma_result.message

    sair = SAIRAPIVerifier(dry_run=True)
    dry_run = sair.submit([{"canonical_hash": "abc"}], submit=False)
    assert dry_run.status == "unverified"
    export_path = sair.export_batch_without_submission([{"canonical_hash": "abc"}], tmp_path / "batch.jsonl")
    assert export_path.exists()
    monkeypatch.delenv("SAIR_API_KEY", raising=False)
    with pytest.raises(SAIRAPIError, match="missing SAIR_API_KEY"):
        SAIRAPIVerifier(dry_run=False).submit([{"exported_coefficients": list(VALID) + [1]}], submit=True)
