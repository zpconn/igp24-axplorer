"""Official scoring helpers for the SAIR IGP24 competition.

These helpers keep leaderboard economics separate from generator heuristics.
They intentionally do not decide whether a polynomial has a given Galois group;
they only estimate the point value of a pair once the pair/scoring
discriminants are known or bounded.
"""

from __future__ import annotations

import math
from typing import Any


def natural_log_positive_int(value: Any) -> float | None:
    """Return log(value) for a positive integer represented as int or digits."""
    if value in {None, ""}:
        return None
    text = str(value).strip()
    if text.startswith("-"):
        text = text[1:]
    if not text.isdigit():
        return None
    text = text.lstrip("0") or "0"
    if text in {"0", "1"}:
        return None
    if len(text) <= 15:
        return math.log(int(text))
    head_len = 15
    head = int(text[:head_len])
    return math.log(head) + (len(text) - head_len) * math.log(10)


def team_score_multiplier(team_count: int) -> float:
    """Official team-count factor, using k >= 1 credited teams."""
    k = max(1, int(team_count))
    return 2.0 ** (1 - k)


def prospective_team_count(current_team_count: int, *, uncovered: bool, baseline_pair: bool = False) -> int:
    """Return the team count relevant to a prospective submission.

    An uncovered non-baseline signature can become a first-team discovery, so
    its prospective k is 1. Covered pairs use the current credited team count.
    """
    if uncovered and not baseline_pair:
        return 1
    return max(1, int(current_team_count))


def maximum_possible_points(
    *,
    current_team_count: int,
    uncovered: bool,
    baseline_pair: bool = False,
) -> float:
    """Best possible contribution for a pair before candidate discrimination."""
    k = prospective_team_count(
        current_team_count,
        uncovered=uncovered,
        baseline_pair=baseline_pair,
    )
    return team_score_multiplier(k)


def discriminant_log_ratio(current_best_disc_abs: Any, candidate_disc_abs: Any) -> float | None:
    """Return log(D0) / log(D), capped by callers when used for scoring."""
    best_log = natural_log_positive_int(current_best_disc_abs)
    candidate_log = natural_log_positive_int(candidate_disc_abs)
    if best_log is None or candidate_log is None or candidate_log <= 0:
        return None
    return best_log / candidate_log


def score_ceiling_class(max_points: float, *, uncovered: bool, baseline_pair: bool = False) -> str:
    if uncovered and not baseline_pair:
        return "uncovered_first_team_one_point"
    if max_points >= 0.25:
        return "very_low_team_high_ceiling"
    if max_points >= 0.015625:
        return "low_team_meaningful_ceiling"
    if max_points >= 0.001:
        return "thin_but_visible_ceiling"
    if max_points >= 0.0001:
        return "crowded_low_ceiling"
    return "crowded_near_zero_ceiling"


def _round_points(value: float | None) -> float | None:
    if value is None:
        return None
    if value == 0:
        return 0.0
    return round(float(value), 12)


def official_score_economics(
    *,
    current_team_count: int,
    uncovered: bool,
    baseline_pair: bool = False,
    current_best_disc_abs: Any = None,
    candidate_disc_abs: Any = None,
    observed_points: float | None = None,
) -> dict[str, Any]:
    """Return official-score fields for a pair or candidate follow-up.

    Formula from the competition guidance:

        2^(1-k) * log(D0) / log(D)

    For an uncovered non-baseline signature, the first valid credited row has
    k=1 and D0=D, so the ceiling and expected first-discovery value are 1.
    """
    current_k = max(0, int(current_team_count))
    prospective_k = prospective_team_count(
        current_k,
        uncovered=uncovered,
        baseline_pair=baseline_pair,
    )
    max_points = maximum_possible_points(
        current_team_count=current_k,
        uncovered=uncovered,
        baseline_pair=baseline_pair,
    )
    ratio = discriminant_log_ratio(current_best_disc_abs, candidate_disc_abs)
    candidate_improves_best: bool | None = None
    if current_best_disc_abs not in {None, ""} and candidate_disc_abs not in {None, ""}:
        try:
            candidate_improves_best = int(str(candidate_disc_abs)) < int(str(current_best_disc_abs))
        except (TypeError, ValueError):
            candidate_improves_best = None

    if uncovered and not baseline_pair:
        estimated = max_points
        basis = "uncovered_non_baseline_first_valid"
    elif ratio is not None:
        estimated = max_points * max(0.0, min(1.0, ratio))
        basis = "candidate_vs_current_best_discriminant"
    elif observed_points is not None:
        estimated = float(observed_points)
        basis = "observed_score_snapshot_points"
    else:
        estimated = max_points
        basis = "score_ceiling_no_candidate_discriminant"

    return {
        "official_current_team_count": current_k,
        "official_prospective_team_count": prospective_k,
        "score_multiplier": _round_points(team_score_multiplier(prospective_k)),
        "maximum_possible_points": _round_points(max_points),
        "estimated_expected_points": _round_points(estimated),
        "estimated_points_basis": basis,
        "discriminant_log_ratio": round(ratio, 12) if ratio is not None else None,
        "candidate_improves_current_best": candidate_improves_best,
        "score_ceiling_class": score_ceiling_class(
            max_points,
            uncovered=uncovered,
            baseline_pair=baseline_pair,
        ),
    }
