import json
import math
import random
from pathlib import Path

import pytest

pytest.importorskip("sympy")

from scripts.igp24_r24_tower_probe import (
    candidate_family_key,
    coefficient_line,
    coefficients_from_trial,
    r24_outer_root_layouts,
    trial_variants,
)
from scripts.igp24_r12_tower_probe import exact_tower_support, inner_quartic_coefficients, outer_from_roots
from src.igp24.polynomial import DEGREE, coefficient_height, export_coefficients, score_candidate


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data/igp24/r24_tower_probe_20260707/r24_tower_summary.json"
QUEUE_PATH = ROOT / "data/igp24/r24_tower_probe_20260707/r24_tower_candidate_queue.jsonl"
ACCEPTED_FEEDBACK_PATH = ROOT / "data/igp24/r24_tower_probe_sair_accepted_feedback_20260707.json"


def test_r24_tower_layouts_keep_all_levels_in_four_real_band():
    assert r24_outer_root_layouts(4) == []
    layouts = r24_outer_root_layouts(6)

    assert layouts
    for layout in layouts:
        assert len(layout["outer_roots"]) == 6
        assert layout["outer_roots"] == layout["four_real_preimage_levels"]
        assert all(0 < abs(level) < 6 * 6 / 4 for level in layout["outer_roots"])


def test_r24_tower_trial_generation_is_deterministic():
    first = list(trial_variants(rng=random.Random(2407), max_trials=5))
    second = list(trial_variants(rng=random.Random(2407), max_trials=5))

    assert first == second
    assert len(first) == 5
    assert all(len(trial["outer_roots"]) == 6 for trial in first)
    assert all(trial["four_real_preimage_levels"] == list(trial["outer_roots"]) for trial in first)


def test_r24_tower_known_template_is_locally_valid():
    trial = {
        "mode": "outer_constant_shift",
        "inner_parameter_s": 6,
        "inner_coefficients": inner_quartic_coefficients(6),
        "outer_roots": (-1, -2, -3, -5, -6, -8),
        "four_real_preimage_levels": [-1, -2, -3, -5, -6, -8],
        "outer_coefficients_before_perturbation": outer_from_roots((-1, -2, -3, -5, -6, -8)),
        "outer_perturbations": [(0, 2)],
    }
    coeffs, metadata = coefficients_from_trial(trial)
    exported = export_coefficients(coeffs)
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
    assert exact_tower_support(coeffs)
    assert metadata["r24_tower_expected_real_root_count"] == 24
    assert metadata["r24_tower_all_outer_levels_have_four_real_preimages"] is True
    assert "not a product-of-quadratics" in metadata["structural_difference_from_previous_r24_lane"]
    assert metadata["r24_tower_family_key"] == candidate_family_key({"generation_metadata": metadata})
    assert coefficient_height(coeffs) == 443384
    assert score >= 0
    assert analysis.valid
    assert analysis.real_root_count == 24
    assert analysis.irreducible
    assert analysis.squarefree
    assert analysis.canonical_hash == "b906cada2cadc8556ca63a38e07d6021e1c49f2823e93a148843951ee6c5d2d6"


def test_r24_tower_tracked_artifact_shape():
    if not SUMMARY_PATH.exists() or not QUEUE_PATH.exists():
        pytest.skip("tracked r24 tower artifact has not been generated yet")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert summary["queue_status"] == "api_dry_run_ready"
    assert summary["target_r"] == 24
    assert summary["decomposition_degree_pattern"] == "6x4"
    assert summary["selected_rows"] == 10
    assert len(rows) == 10
    assert len({row["canonical_hash"] for row in rows}) == 10
    assert all(row["generation_metadata"]["r24_tower_exact_composition"] for row in rows)
    assert all(row["real_root_count"] == 24 for row in rows)


def test_r24_tower_sair_feedback_records_accepted_labels():
    if not ACCEPTED_FEEDBACK_PATH.exists():
        pytest.skip("tracked r24 tower SAIR accepted feedback has not been generated yet")
    payload = json.loads(ACCEPTED_FEEDBACK_PATH.read_text(encoding="utf-8"))

    assert payload["record_type"] == "igp24_sair_accepted_label_feedback"
    assert payload["submission_id"].startswith("sub_")
    assert payload["safety"]["api_key_recorded"] is False
    assert payload["summary"]["accepted_rows"] == 10
    assert payload["summary"]["failed_rows"] == 0
    assert payload["summary"]["queued_rows"] == 0
    assert payload["summary"]["labels_found_counts"] == {"24T23883": 1, "24T24651": 9}
    assert payload["summary"]["accepted_pair_keys"] == ["24T23883|r=24", "24T24651|r=24"]
    assert payload["summary"]["scoreable_false_pending_discriminant_rows"] == 10
    assert len(payload["accepted_rows"]) == 10
    assert {row["status"] for row in payload["accepted_rows"]} == {"accepted"}
