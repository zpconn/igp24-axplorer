import math

from src.igp24.scoring import (
    discriminant_log_ratio,
    maximum_possible_points,
    official_score_economics,
    prospective_team_count,
    team_score_multiplier,
)


def test_uncovered_non_baseline_first_valid_is_one_point_ceiling():
    economics = official_score_economics(current_team_count=0, uncovered=True)

    assert prospective_team_count(0, uncovered=True) == 1
    assert economics["official_prospective_team_count"] == 1
    assert economics["maximum_possible_points"] == 1.0
    assert economics["estimated_expected_points"] == 1.0
    assert economics["estimated_points_basis"] == "uncovered_non_baseline_first_valid"
    assert economics["score_ceiling_class"] == "uncovered_first_team_one_point"


def test_team_multiplier_matches_visible_low_team_scores():
    assert team_score_multiplier(1) == 1.0
    assert team_score_multiplier(2) == 0.5
    assert math.isclose(team_score_multiplier(10), 0.001953125)
    assert maximum_possible_points(current_team_count=10, uncovered=False) == 0.001953125


def test_discriminant_ratio_caps_score_at_pair_ceiling_for_improvements():
    worse = official_score_economics(
        current_team_count=10,
        uncovered=False,
        current_best_disc_abs=10**30,
        candidate_disc_abs=10**60,
    )
    better = official_score_economics(
        current_team_count=10,
        uncovered=False,
        current_best_disc_abs=10**60,
        candidate_disc_abs=10**30,
    )

    assert math.isclose(discriminant_log_ratio(10**30, 10**60), 0.5)
    assert worse["estimated_expected_points"] == round(0.001953125 * 0.5, 12)
    assert better["candidate_improves_current_best"] is True
    assert better["estimated_expected_points"] == better["maximum_possible_points"]


def test_crowded_pair_has_near_zero_ceiling():
    economics = official_score_economics(current_team_count=54, uncovered=False)

    assert economics["maximum_possible_points"] < 0.000000000001
    assert economics["score_ceiling_class"] == "crowded_near_zero_ceiling"
    assert economics["estimated_points_basis"] == "score_ceiling_no_candidate_discriminant"
