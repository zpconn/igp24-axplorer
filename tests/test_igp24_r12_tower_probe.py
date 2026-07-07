import json
import math
import random
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("sympy")

from scripts.igp24_r12_tower_probe import (
    candidate_family_key,
    coefficient_line,
    coefficients_from_trial,
    compose_outer_inner,
    exact_tower_support,
    inner_quartic_coefficients,
    load_r12_followup_feedback,
    outer_from_roots,
    trial_variants,
)
from src.igp24.polynomial import DEGREE, coefficient_height, export_coefficients, score_candidate


ROOT = Path(__file__).resolve().parents[1]
FOLLOWUP_FEEDBACK_PATH = ROOT / "data/igp24/r12_structured_followup_sair_accepted_feedback_20260706.json"
TOWER_SUMMARY_PATH = ROOT / "data/igp24/r12_tower_probe_20260706/r12_tower_summary.json"
TOWER_QUEUE_PATH = ROOT / "data/igp24/r12_tower_probe_20260706/r12_tower_candidate_queue.jsonl"


def test_r12_tower_feedback_parser_maps_latest_sair_labels():
    rows = load_r12_followup_feedback(FOLLOWUP_FEEDBACK_PATH)

    assert len(rows) == 10
    assert Counter(row.label for row in rows) == {"24T24970": 2, "24T24979": 8}
    assert rows[0].pair_key == "24T24970|r=12"
    assert rows[1].pair_key == "24T24970|r=12"
    assert rows[2].pair_key == "24T24979|r=12"
    assert all(row.canonical_hash for row in rows)
    assert all(row.source_family_key for row in rows)


def test_r12_tower_trial_generation_is_deterministic():
    first = list(trial_variants(rng=random.Random(1246), max_trials=5))
    second = list(trial_variants(rng=random.Random(1246), max_trials=5))

    assert first == second
    assert len(first) == 5
    for trial in first:
        assert trial["mode"] in {
            "outer_constant_shift",
            "outer_two_coefficient_shift",
            "outer_three_coefficient_shift",
        }
        assert len(trial["inner_coefficients"]) == 5
        assert len(trial["outer_coefficients_before_perturbation"]) == 7
        assert len(trial["outer_roots"]) == 6
        assert trial["four_real_preimage_levels"]
        assert trial["no_real_preimage_levels"]


def test_r12_tower_composition_preserves_claimed_structure_and_export_format():
    trial = {
        "mode": "outer_constant_shift",
        "inner_parameter_s": 4,
        "inner_coefficients": inner_quartic_coefficients(4),
        "outer_roots": (-1, -2, -3, -5, -6, -8),
        "four_real_preimage_levels": [-1, -2, -3],
        "no_real_preimage_levels": [-5, -6, -8],
        "outer_coefficients_before_perturbation": outer_from_roots((-1, -2, -3, -5, -6, -8)),
        "outer_perturbations": [(0, -3)],
    }
    coeffs, metadata = coefficients_from_trial(trial)
    exported = export_coefficients(coeffs)

    assert compose_outer_inner(metadata["r12_tower_outer_coefficients"], inner_quartic_coefficients(4)) == coeffs
    assert len(coeffs) == DEGREE
    assert len(exported) == DEGREE + 1
    assert len(coefficient_line(exported).split(",")) == DEGREE + 1
    assert exported[-1] == 1
    assert exported[0] != 0
    assert math.gcd(*[abs(value) for value in exported]) == 1
    assert exact_tower_support(coeffs)
    assert metadata["decomposition_type"] == "exact_composition"
    assert metadata["decomposition_degree_pattern"] == "6x4"
    assert metadata["r12_tower_exact_composition"] is True
    assert metadata["r12_tower_inner_polynomial_coefficients"] == [0, 0, -4, 0, 1]
    assert metadata["r12_tower_expected_real_root_count"] == 12
    assert "degree-6 outer" in metadata["structural_difference_from_previous_r12_lane"]
    assert metadata["r12_tower_family_key"] == candidate_family_key({"generation_metadata": metadata})


def test_r12_tower_known_template_is_locally_valid():
    trial = {
        "mode": "outer_constant_shift",
        "inner_parameter_s": 4,
        "inner_coefficients": inner_quartic_coefficients(4),
        "outer_roots": (-1, -2, -3, -5, -6, -8),
        "four_real_preimage_levels": [-1, -2, -3],
        "no_real_preimage_levels": [-5, -6, -8],
        "outer_coefficients_before_perturbation": [1440, 3348, 2852, 1163, 243, 25, 1],
        "outer_perturbations": [(0, -3)],
    }
    coeffs, metadata = coefficients_from_trial(trial)
    score, analysis = score_candidate(
        coeffs,
        coeff_bound=20_000_000,
        target_r=12,
        prime_limit=7,
        exact_score_timeout=5.0,
    )

    assert score >= 0
    assert coefficient_height(coeffs) == 120884
    assert analysis.valid
    assert analysis.real_root_count == 12
    assert analysis.irreducible
    assert analysis.squarefree
    assert analysis.canonical_hash == "fceab6f1bb24887542978cc8ad4057f7538c27b92cfc553d24054103a094de7c"
    assert metadata["r12_tower_family_key"] == "s=4|mode=outer_constant_shift|real=-1,-2,-3|none=-5,-6,-8|outer_y=0"
    assert exact_tower_support(coeffs)


def test_r12_tower_tracked_artifact_shape():
    summary = json.loads(TOWER_SUMMARY_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in TOWER_QUEUE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert summary["queue_status"] == "manual_queue_ready"
    assert summary["decomposition_degree_pattern"] == "6x4"
    assert summary["selected_rows"] == 10
    assert len(rows) == 10
    assert summary["selected_inner_s_counts"] == {"4": 2, "5": 2, "6": 2, "7": 2, "8": 2}
    assert len({row["canonical_hash"] for row in rows}) == 10
    assert all(row["generation_metadata"]["r12_tower_exact_composition"] for row in rows)
