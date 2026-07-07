import math
import random
from collections import Counter
from pathlib import Path
import json

import pytest

pytest.importorskip("sympy")

from scripts.igp24_r12_structured_followup import (
    coefficient_line,
    coefficients_from_trial,
    exact_even_support,
    load_r12_feedback,
    structural_family_key,
    trial_variants,
)
from src.igp24.polynomial import (
    DEGREE,
    coefficient_height,
    export_coefficients,
    score_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
FEEDBACK_PATH = ROOT / "data/igp24/r12_structured_probe_sair_accepted_feedback_20260706.json"
PAIR_STATUS_PATH = ROOT / "data/igp24/pair_status_20260706.json"


def test_r12_followup_feedback_artifact_maps_labels():
    rows = load_r12_feedback(FEEDBACK_PATH)

    assert len(rows) == 10
    assert Counter(row.label for row in rows) == {
        "24T22770": 2,
        "24T24970": 1,
        "24T24979": 7,
    }
    assert rows[0].row_number == 1
    assert rows[0].pair_key == "24T22770|r=12"
    assert rows[2].pair_key == "24T24970|r=12"
    assert rows[4].pair_key == "24T22770|r=12"
    assert all(len(row.exported_coefficients) == DEGREE + 1 for row in rows)
    assert all(len(row.base_coefficients_y) == 13 for row in rows)
    assert all(row.structural_family_key for row in rows)


def test_r12_followup_pair_status_records_new_pairs_and_alternates():
    payload = json.loads(PAIR_STATUS_PATH.read_text(encoding="utf-8"))
    pairs = {row["pair_key"]: row for row in payload["pairs"]}

    assert pairs["24T22770|r=12"]["status"] == "accepted"
    assert pairs["24T22770|r=12"]["source_row_number"] == 1
    assert len(pairs["24T22770|r=12"]["accepted_alternates"]) == 1
    assert pairs["24T24970|r=12"]["status"] == "accepted"
    assert len(pairs["24T24970|r=12"]["accepted_alternates"]) == 2
    assert pairs["24T24979|r=12"]["status"] == "accepted"
    assert pairs["24T24979|r=12"]["source_row_number"] == 2
    assert len(pairs["24T24979|r=12"]["accepted_alternates"]) == 14
    followup_source = "data/igp24/r12_structured_followup_sair_accepted_feedback_20260706.json"
    assert sum(
        1 for alternate in pairs["24T24970|r=12"]["accepted_alternates"] if alternate["source"] == followup_source
    ) == 2
    assert sum(
        1 for alternate in pairs["24T24979|r=12"]["accepted_alternates"] if alternate["source"] == followup_source
    ) == 8
    assert all(pairs[key]["source"].endswith("r12_structured_probe_sair_accepted_feedback_20260706.json") for key in [
        "24T22770|r=12",
        "24T24970|r=12",
        "24T24979|r=12",
    ])


def test_r12_followup_trial_variants_are_deterministic_and_multi_perturbation():
    first = list(trial_variants(rng=random.Random(1213), max_trials=5))
    second = list(trial_variants(rng=random.Random(1213), max_trials=5))

    assert first == second
    assert len(first) == 5
    assert first[0]["mode"] == "two_base_wide_perturbation"
    for trial in first:
        perturbations = trial["base_perturbations"]
        assert len(perturbations) >= 2
        assert all(0 <= int(y_exponent) <= 11 for y_exponent, _ in perturbations)


def test_r12_followup_candidate_preserves_exact_even_support_and_sair_format():
    accepted = load_r12_feedback(FEEDBACK_PATH)
    trial = next(trial_variants(rng=random.Random(1213), max_trials=1))
    coeffs, metadata = coefficients_from_trial(trial, accepted=accepted)
    exported = export_coefficients(coeffs)

    assert len(coeffs) == DEGREE
    assert len(exported) == DEGREE + 1
    assert len(coefficient_line(exported).split(",")) == DEGREE + 1
    assert exported[-1] == 1
    assert coeffs[0] != 0
    assert math.gcd(*[abs(value) for value in exported]) == 1
    assert exact_even_support(coeffs)
    assert all(index % 2 == 0 for index, coeff in enumerate(exported) if coeff != 0)
    assert metadata["r12_followup_exact_composed_support_divisor"] == 2
    assert metadata["r12_followup_perturbation_terms"] >= 2
    assert metadata["r12_followup_min_l1_to_accepted_base_y"] is not None
    assert metadata["r12_followup_min_l1_to_accepted_exported"] is not None
    assert metadata["r12_followup_structural_family_key"] == structural_family_key(
        trial["positive_base_roots"],
        trial["negative_base_roots"],
        trial["base_perturbations"],
    )


def test_r12_followup_known_template_is_locally_valid():
    accepted = load_r12_feedback(FEEDBACK_PATH)
    trial = {
        "mode": "two_base_wide_perturbation",
        "positive_base_roots": (1, 2, 3, 5, 6, 8),
        "negative_base_roots": (1, 2, 4, 5, 7, 9),
        "base_coefficients_y": [
            3628800,
            -439200,
            -5107752,
            591668,
            1651254,
            -164439,
            -180235,
            12309,
            8085,
            -341,
            -153,
            3,
            1,
        ],
        "base_perturbations": [(4, 7), (9, -3)],
    }
    coeffs, metadata = coefficients_from_trial(trial, accepted=accepted)
    score, analysis = score_candidate(
        coeffs,
        coeff_bound=20_000_000,
        target_r=12,
        prime_limit=7,
        exact_score_timeout=5.0,
    )

    assert score >= 0
    assert coefficient_height(coeffs) == 5107752
    assert analysis.valid
    assert analysis.real_root_count == 12
    assert analysis.irreducible
    assert analysis.squarefree
    assert analysis.canonical_hash == "142adb90c2249b97a4aeba1690ac07494ee5f4eeddd1a355b6146475da05024d"
    assert metadata["r12_followup_nearest_accepted_base_label"] == "24T24979"
    assert metadata["r12_followup_min_l1_to_accepted_base_y"] == 5596251
    assert exact_even_support(coeffs)
