import json
import math
import random
from pathlib import Path

import pytest

pytest.importorskip("sympy")

from scripts.igp24_alt_composition_4x6_probe import (
    alt_4x6_family_key,
    build_submission_readiness,
    coefficients_from_trial,
    level_layouts,
    outer_from_roots,
    passes_structural_gates,
    sextic_inner_root_layouts,
    sextic_six_real_levels,
    trial_variants,
    write_outputs,
)
from scripts.igp24_alt_composition_probe import apply_outer_perturbations, compose_outer_inner, support_summary
from scripts.igp24_r16_diversity_probe import coefficient_line
from src.igp24.polynomial import DEGREE, coefficient_height, export_coefficients, score_candidate


def test_4x6_known_template_is_locally_valid():
    inner_roots = (-4, -2, -1, 1, 3, 4)
    outer_roots = (-30, -29, -28, -27)
    trial = {
        "decomposition_degree_pattern": "4x6",
        "mode": "outer_linear_quadratic_shift",
        "inner_roots": list(inner_roots),
        "inner_coefficients": outer_from_roots(inner_roots),
        "outer_roots": list(outer_roots),
        "outer_coefficients_before_perturbation": outer_from_roots(outer_roots),
        "outer_perturbations": [(1, 1), (2, -1)],
        "available_six_real_level_count": 10,
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
    assert metadata["construction_family"] == "alt_composition_4x6"
    assert metadata["decomposition_degree_pattern"] == "4x6"
    assert metadata["alt_support_gcd"] == 1
    assert metadata["alt_even_support"] is False
    assert metadata["alt_composition_family_key"] == alt_4x6_family_key({"generation_metadata": metadata})
    assert gate_ok is True
    assert gate_failures == []
    assert coefficient_height(coeffs) == 506569499
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 12
    assert analysis.irreducible
    assert analysis.squarefree


def test_4x6_trials_are_deterministic_and_have_six_real_levels():
    first = list(
        trial_variants(
            rng=random.Random(244601),
            max_trials=12,
            level_bound=80,
            max_levels_per_inner=20,
            max_layouts_per_inner=8,
            excluded_modes={"outer_constant_shift"},
        )
    )
    second = list(
        trial_variants(
            rng=random.Random(244601),
            max_trials=12,
            level_bound=80,
            max_levels_per_inner=20,
            max_layouts_per_inner=8,
            excluded_modes={"outer_constant_shift"},
        )
    )

    assert first == second
    assert len(first) == 12
    assert sextic_inner_root_layouts()
    inner = outer_from_roots((-4, -2, -1, 1, 3, 4))
    levels = sextic_six_real_levels(inner, level_bound=80, max_levels=20)
    assert len(levels) >= 4
    assert level_layouts(levels, width=4, max_layouts=4)
    assert all(trial["decomposition_degree_pattern"] == "4x6" for trial in first)
    assert all(trial["mode"] != "outer_constant_shift" for trial in first)


def test_4x6_structural_gates_reject_even_support():
    coeffs = [0] * DEGREE
    coeffs[0] = 1
    coeffs[2] = -3
    coeffs[4] = 2
    metadata = {
        "decomposition_degree_pattern": "4x6",
        "construction_family": "alt_composition_4x6",
        "alt_even_support": support_summary(coeffs)["even_support"],
        "alt_support_gcd": support_summary(coeffs)["support_gcd"],
    }

    gate_ok, gate_failures = passes_structural_gates(coeffs, metadata)

    assert gate_ok is False
    assert "even_support_g_x_squared_like" in gate_failures
    assert "support_gcd_not_one" in gate_failures
    assert len(compose_outer_inner([1, 0, 0, 0, 1], [1, 1, 0, -1, 0, 0, 1])) == DEGREE
    assert apply_outer_perturbations([1, 2, 3, 4, 1], [(3, -1)]) == [1, 2, 3, 3, 1]


def test_4x6_submission_readiness_and_outputs(tmp_path):
    selected = []
    for index in range(8):
        selected.append(
            {
                "alt_composition_4x6_queue_rank": index + 1,
                "canonical_hash": f"hash-{index}",
                "exported_coefficients": [2, 1] + [0] * 22 + [1],
                "real_root_count": 12 if index % 2 else 24,
                "coefficient_height": 100 + index,
                "log_abs_discriminant": 10.0 + index,
                "generation_metadata": {
                    "decomposition_degree_pattern": "4x6",
                    "alt_perturbation_mode": "outer_linear_quadratic_shift" if index % 2 else "outer_cubic_mixed_shift",
                    "alt_composition_family_key": f"family-{index}",
                },
            }
        )

    readiness = build_submission_readiness(selected, [24, 20, 16, 12, 8])
    assert readiness["status"] == "planner_review_ready_not_submitted"
    assert readiness["worth_scoring_with_anti_basin_planner"] is True

    paths = write_outputs(
        output_dir=tmp_path,
        selected=selected,
        rejected=[{"rejection_reason": "test"}],
        summary={"selected_rows": 8, "submission_readiness": readiness},
    )
    assert len(paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()) == 8
    assert len(paths["queue_jsonl"].read_text(encoding="utf-8").splitlines()) == 8
    assert json.loads(paths["queue_jsonl"].read_text(encoding="utf-8").splitlines()[0])["canonical_hash"] == "hash-0"
    assert "4x6 Alternate Composition" in paths["report_md"].read_text(encoding="utf-8")
