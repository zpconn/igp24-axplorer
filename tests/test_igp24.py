from types import SimpleNamespace

import numpy as np
import pytest

sympy = pytest.importorskip("sympy")

from src.envs import ENVS, build_env
from src.envs.igp24 import IGP24DataPoint
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
from src.igp24.verifiers.sair_api import SAIRAPIVerifier


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
        exp_name="pytest",
        seed=123,
    )
    env = build_env(params)
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=VALID)
    encoded = env.tokenizer.encode(datapoint)
    decoded = env.tokenizer.decode(encoded)
    assert decoded is not None
    assert decoded.coefficients == VALID


def test_generation_strategies_are_bounded_and_metadata_is_set():
    IGP24DataPoint.COEFF_BOUND = 5
    IGP24DataPoint.SPARSE_TERMS = 4
    IGP24DataPoint.LOW_HEIGHT_BOUND = 2
    for strategy in ["uniform", "low_height", "sparse", "lower_degree", "structured"]:
        np_seed = {"uniform": 11, "low_height": 12, "sparse": 13, "lower_degree": 14, "structured": 15}[strategy]
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
            "GENERATION_STRATEGY": "structured",
            "SPARSE_TERMS": 4,
            "LOW_HEIGHT_BOUND": 2,
            "ALWAYS_SEARCH": False,
            "REDEEM_ONLY": False,
        }
    )
    datapoint = IGP24DataPoint(N=DEGREE, coeffs=VALID, generation_strategy="structured")
    datapoint.calc_score()
    datapoint.local_search(improve_with_local_search=True)
    records = CandidateLedger(tmp_path / "ledger.jsonl").records()
    assert records
    latest = records[-1]
    assert latest["generation_metadata"]["strategy"] == "structured"
    assert latest["local_search_metadata"]["max_steps"] == 2
    assert "score_components" in latest


def test_verifier_stubs_fail_gracefully_and_sair_is_dry_run(tmp_path):
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
    with pytest.raises(NotImplementedError):
        SAIRAPIVerifier(dry_run=False).submit([], submit=True)
