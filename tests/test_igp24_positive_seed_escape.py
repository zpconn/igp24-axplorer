import json

import pytest

pytest.importorskip("sympy")

from scripts.igp24_positive_seed_escape import (
    generate_candidates,
    load_known_hashes,
    selected_seed_rows,
)
from scripts.igp24_r24_high_real_probe import quadratic_product_coefficients
from src.igp24.polynomial import stable_canonical_hash


def _active_row(coeffs, *, r=24, role="score_positive", eligible=True, weight=12.0, hash_value=None):
    hash_value = hash_value or stable_canonical_hash(coeffs)
    return {
        "canonical_hash": hash_value,
        "coefficients": coeffs + [1],
        "r": r,
        "generator_training": {
            "eligible": eligible,
            "weight": weight,
            "role": role,
            "pair_key": f"24Tseed|r={r}",
            "label": "24Tseed",
        },
        "sair_feedback": {"pair_key": f"24Tseed|r={r}", "label": "24Tseed"},
    }


def test_selected_seed_rows_deduplicates_and_filters_roles():
    coeffs = quadratic_product_coefficients(range(1, 13))
    rows = [
        _active_row(coeffs, r=24, hash_value="seed"),
        _active_row(coeffs, r=24, hash_value="seed"),
        _active_row(coeffs, r=24, role="crowded_collapse", eligible=False, hash_value="bad"),
        _active_row(coeffs, r=12, hash_value="wrong-r"),
    ]

    selected = selected_seed_rows(rows, target_rs={24}, roles={"score_positive"})

    assert len(selected) == 1
    assert selected[0]["canonical_hash"] == "seed"
    assert selected[0]["r"] == 24


def test_load_known_hashes_accepts_hashes_and_coefficients(tmp_path):
    coeffs = quadratic_product_coefficients(range(1, 13))
    known = tmp_path / "known.jsonl"
    known.write_text(
        "\n".join(
            [
                json.dumps({"canonical_hash": "abc"}),
                json.dumps({"exported_coefficients": coeffs + [1]}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    hashes = load_known_hashes([known])

    assert "abc" in hashes
    assert stable_canonical_hash(coeffs) in hashes


def test_generate_candidates_keeps_exact_target_r_odd_escape():
    seed_coeffs = quadratic_product_coefficients(range(1, 13))
    seed = _active_row(seed_coeffs, r=24)

    candidates, rejected, summary = generate_candidates(
        seeds=[seed],
        known_hashes={stable_canonical_hash(seed_coeffs)},
        odd_exponents=[1],
        deltas=[1],
        max_trials_per_seed=1,
        max_candidates=4,
        coeff_bound=5_000_000_000,
        prime_limit=7,
        exact_score_timeout=5.0,
        require_support_gcd_one=True,
        include_pair_mutations=False,
    )

    assert rejected == []
    assert summary["candidate_count"] == 1
    assert summary["exact_r_counts"] == {"r=24": 1}
    candidate = candidates[0]
    assert candidate["valid"] is True
    assert candidate["real_root_count"] == 24
    assert candidate["irreducible"] is True
    assert candidate["squarefree"] is True
    assert candidate["known_submission_hash_match"] is False
    assert candidate["sample_export_source"] == "positive_seed_escape"
    assert candidate["generation_metadata"]["odd_escape_mutations"] == [{"x_exponent": 1, "delta": 1}]
    assert candidate["generation_metadata"]["support_gcd"] == 1
