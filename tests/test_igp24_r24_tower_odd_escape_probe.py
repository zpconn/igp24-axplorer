import json
import math
import random
from pathlib import Path

import pytest

pytest.importorskip("sympy")

from scripts.igp24_r24_tower_odd_escape_probe import (
    candidate_family_key,
    coefficient_line,
    coefficients_from_trial,
    support_summary,
    trial_variants,
)
from scripts.igp24_r12_tower_probe import inner_quartic_coefficients, outer_from_roots
from scripts.igp24_r24_tower_probe import r24_outer_root_layouts
from src.igp24.polynomial import DEGREE, coefficient_height, export_coefficients, score_candidate


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data/igp24/r24_tower_odd_escape_probe_20260707/r24_tower_odd_escape_summary.json"
QUEUE_PATH = ROOT / "data/igp24/r24_tower_odd_escape_probe_20260707/r24_tower_odd_escape_candidate_queue.jsonl"


def test_r24_tower_odd_escape_known_template_is_locally_valid():
    trial = {
        "mode": "single_odd_tower_escape",
        "inner_parameter_s": 7,
        "inner_coefficients": inner_quartic_coefficients(7),
        "outer_roots": (-1, -2, -3, -7, -10, -11),
        "four_real_preimage_levels": [-1, -2, -3, -7, -10, -11],
        "outer_coefficients": outer_from_roots((-1, -2, -3, -7, -10, -11)),
        "odd_perturbations": [(1, -2)],
    }
    coeffs, metadata = coefficients_from_trial(trial)
    exported = export_coefficients(coeffs)
    support = support_summary(coeffs)
    score, analysis = score_candidate(
        coeffs,
        coeff_bound=2_000_000_000,
        target_r=24,
        prime_limit=7,
        exact_score_timeout=5.0,
    )

    assert len(coeffs) == DEGREE
    assert len(exported) == DEGREE + 1
    assert len(coefficient_line(exported).split(",")) == DEGREE + 1
    assert exported[-1] == 1
    assert exported[0] != 0
    assert math.gcd(*[abs(value) for value in exported]) == 1
    assert support["even_support"] is False
    assert support["support_gcd"] == 1
    assert metadata["r24_tower_odd_escape_exact_composition_after_perturbation"] is False
    assert metadata["r24_tower_odd_escape_even_support_after_perturbation"] is False
    assert metadata["r24_tower_odd_escape_support_gcd"] == 1
    assert "breaks_exact_even_support" in metadata["anti_basin_features"]
    assert metadata["r24_tower_odd_escape_family_key"] == candidate_family_key({"generation_metadata": metadata})
    assert coefficient_height(coeffs) == 1440473
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 24
    assert analysis.irreducible
    assert analysis.squarefree
    assert analysis.canonical_hash == "8fbad18048c9829c38c139437dd4aacbdd691e3ff2935e067a5ba7c80a0e5ff0"


def test_r24_tower_odd_escape_trials_are_deterministic():
    first = list(trial_variants(rng=random.Random(242405), max_trials=5))
    second = list(trial_variants(rng=random.Random(242405), max_trials=5))

    assert first == second
    assert len(first) == 5
    assert r24_outer_root_layouts(6)
    for trial in first:
        coeffs, metadata = coefficients_from_trial(trial)
        assert len(coeffs) == DEGREE
        assert coeffs[0] != 0
        assert metadata["r24_tower_odd_escape_mode"] in {
            "single_odd_tower_escape",
            "two_odd_tower_escape",
        }
        assert metadata["r24_tower_odd_escape_expected_real_root_count"] == 24
        assert metadata["r24_tower_odd_escape_perturbation_terms"] >= 1
        assert metadata["r24_tower_odd_escape_even_support_after_perturbation"] is False
        assert metadata["r24_tower_odd_escape_support_gcd"] == 1
        assert metadata["r24_tower_odd_escape_family_key"] == candidate_family_key({"generation_metadata": metadata})


def test_r24_tower_odd_escape_tracked_artifact_shape():
    if not SUMMARY_PATH.exists() or not QUEUE_PATH.exists():
        pytest.skip("tracked r24 tower odd-escape artifact has not been generated yet")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert summary["queue_status"] == "api_dry_run_ready"
    assert summary["target_r"] == 24
    assert summary["decomposition_degree_pattern"] == "6x4_seed_plus_odd_x_perturbation"
    assert summary["selected_rows"] == 8
    assert "non_even_support" in summary["anti_basin_constraints_satisfied"]
    assert len(rows) == 8
    assert len({row["canonical_hash"] for row in rows}) == 8
    assert all(row["real_root_count"] == 24 for row in rows)
    assert all(row["generation_metadata"]["r24_tower_odd_escape_even_support_after_perturbation"] is False for row in rows)
    assert all(row["generation_metadata"]["r24_tower_odd_escape_support_gcd"] == 1 for row in rows)
