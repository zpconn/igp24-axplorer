import json
import math
import random
from pathlib import Path

import pytest

pytest.importorskip("sympy")

from scripts.igp24_alt_composition_probe import (
    alt_composition_family_key,
    apply_outer_perturbations,
    build_submission_readiness,
    centered_level_layouts,
    coefficients_from_trial,
    compose_outer_inner,
    cubic_inner_coefficients,
    cubic_three_real_levels,
    octic_inner_root_layouts,
    outer_from_roots,
    passes_structural_gates,
    support_summary,
    trial_variants,
)
from scripts.igp24_r16_diversity_probe import coefficient_line
from src.igp24.polynomial import DEGREE, coefficient_height, export_coefficients, score_candidate


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data/igp24/alt_composition_probe_20260707/alt_composition_summary.json"
QUEUE_PATH = ROOT / "data/igp24/alt_composition_probe_20260707/alt_composition_candidate_queue.jsonl"


def test_alt_8x3_known_template_is_locally_valid():
    roots = (-4, -3, -2, -1, 1, 2, 3, 4)
    trial = {
        "decomposition_degree_pattern": "8x3",
        "mode": "outer_high_coefficient_shift",
        "inner_parameter_s": 8,
        "inner_coefficients": cubic_inner_coefficients(8),
        "three_real_band_radius": 2.0,
        "outer_roots": list(roots),
        "outer_coefficients_before_perturbation": outer_from_roots(roots),
        "outer_perturbations": [(0, 10), (5, -1)],
        "expected_real_root_count": 24,
    }

    coeffs, metadata = coefficients_from_trial(trial)
    exported = export_coefficients(coeffs)
    gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)
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
    assert metadata["decomposition_degree_pattern"] == "8x3"
    assert metadata["alt_support_gcd"] == 1
    assert metadata["alt_even_support"] is False
    assert gate_ok is True
    assert gate_failures == []
    assert metadata["alt_composition_family_key"] == alt_composition_family_key({"generation_metadata": metadata})
    assert coefficient_height(coeffs) == 22780288
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 24
    assert analysis.irreducible
    assert analysis.squarefree


def test_alt_3x8_symmetric_template_is_rejected_as_even_support():
    inner_roots = (-4, -3, -2, -1, 1, 2, 3, 4)
    outer_roots = (-1, 0, 2)
    trial = {
        "decomposition_degree_pattern": "3x8",
        "mode": "outer_constant_shift",
        "inner_roots": list(inner_roots),
        "inner_coefficients": outer_from_roots(inner_roots),
        "outer_roots": list(outer_roots),
        "outer_coefficients_before_perturbation": outer_from_roots(outer_roots),
        "outer_perturbations": [(0, 1)],
        "expected_real_root_count": 24,
    }

    coeffs, metadata = coefficients_from_trial(trial)
    gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)

    assert metadata["decomposition_degree_pattern"] == "3x8"
    assert metadata["alt_support_gcd"] == 2
    assert metadata["alt_even_support"] is True
    assert gate_ok is False
    assert "even_support_g_x_squared_like" in gate_failures
    assert "support_gcd_not_one" in gate_failures
    assert coefficient_height(coeffs) == 1432644302


def test_alt_composition_trials_are_deterministic_and_structurally_gated():
    first = list(trial_variants(rng=random.Random(243083), max_trials=8, lanes=["8x3", "3x8"]))
    second = list(trial_variants(rng=random.Random(243083), max_trials=8, lanes=["8x3", "3x8"]))

    assert first == second
    assert len(first) == 8
    assert cubic_three_real_levels(8)
    assert octic_inner_root_layouts()
    for trial in first:
        coeffs, metadata = coefficients_from_trial(trial)
        gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)
        assert len(coeffs) == DEGREE
        assert metadata["decomposition_degree_pattern"] in {"8x3", "3x8"}
        assert metadata["alt_composition_family_key"] == alt_composition_family_key({"generation_metadata": metadata})
        assert "degree_pattern_not_6x4" in metadata["anti_basin_features"]
        if metadata["alt_support_gcd"] == 1 and metadata["alt_even_support"] is False:
            assert gate_ok is True
            assert gate_failures == []


def test_alt_composition_helpers_reject_even_g_x_squared_like_support():
    coeffs = [0] * DEGREE
    coeffs[0] = 1
    coeffs[2] = -3
    coeffs[4] = 2
    metadata = {
        "decomposition_degree_pattern": "8x3",
        "construction_family": "alt_composition_8x3",
        "alt_even_support": support_summary(coeffs)["even_support"],
        "alt_support_gcd": support_summary(coeffs)["support_gcd"],
    }

    gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)

    assert gate_ok is False
    assert "even_support_g_x_squared_like" in gate_failures
    assert "support_gcd_not_one" in gate_failures
    assert centered_level_layouts([-3, -2, -1, 1, 2, 3, 4, 5], 8, max_layouts=3)
    assert apply_outer_perturbations([1, 2, 1], [(0, 3)]) == [4, 2, 1]
    assert len(compose_outer_inner([1, 0, 0, 0, 0, 0, 0, 0, 1], [0, -1, 0, 1])) == DEGREE


def test_alt_submission_readiness_requires_selected_rows():
    readiness = build_submission_readiness(
        [
            {
                "alt_composition_queue_rank": index + 1,
                "canonical_hash": f"hash-{index}",
                "real_root_count": 24,
                "coefficient_height": 100 + index,
                "generation_metadata": {"decomposition_degree_pattern": "8x3"},
            }
            for index in range(8)
        ],
        [24, 20, 16, 12, 8],
    )

    assert readiness["status"] == "manual_review_ready_not_submitted"
    assert readiness["worth_submitting_later"] is True
    assert readiness["submitted_by_this_tool"] is False


def test_alt_composition_tracked_artifact_shape():
    if not SUMMARY_PATH.exists() or not QUEUE_PATH.exists():
        pytest.skip("tracked alternate-composition artifact has not been generated yet")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert summary["queue_status"] == "manual_review_ready_not_submitted"
    assert summary["submission_readiness"]["submitted_by_this_tool"] is False
    assert summary["selected_rows"] >= 8
    assert "degree_pattern_not_6x4" in summary["anti_basin_constraints_satisfied"]
    assert len(rows) == summary["selected_rows"]
    assert len({row["canonical_hash"] for row in rows}) == len(rows)
    assert all(row["real_root_count"] in {24, 20, 16, 12, 8} for row in rows)
    assert all(row["generation_metadata"]["decomposition_degree_pattern"] in {"8x3", "3x8"} for row in rows)
    assert all(row["generation_metadata"]["alt_support_gcd"] == 1 for row in rows)
    assert all(row["generation_metadata"]["alt_even_support"] is False for row in rows)
