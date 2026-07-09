"""Stage-0 helpers for the IGP24 Axplorer environment."""

from src.igp24.polynomial import (
    DEGREE,
    CandidateAnalysis,
    analyze_candidate,
    canonicalize_under_translations,
    construct_polynomial,
    export_coefficients,
    score_candidate,
    stable_canonical_hash,
    translate_coefficients,
    validate_coefficients,
)
from src.igp24.group_compatibility import (
    GroupCycleIndex,
    GroupRecord,
    candidate_compatibility,
    cycle_type_key,
    validate_historical_containment,
)
from src.igp24.scoring import (
    discriminant_log_ratio,
    maximum_possible_points,
    official_score_economics,
    prospective_team_count,
    team_score_multiplier,
)
from src.igp24.constructions import (
    ConstructionFamily,
    ConstructionRegistry,
    default_registry,
    rank_families_for_target,
)

__all__ = [
    "DEGREE",
    "CandidateAnalysis",
    "ConstructionFamily",
    "ConstructionRegistry",
    "GroupCycleIndex",
    "GroupRecord",
    "analyze_candidate",
    "candidate_compatibility",
    "canonicalize_under_translations",
    "construct_polynomial",
    "cycle_type_key",
    "default_registry",
    "discriminant_log_ratio",
    "export_coefficients",
    "maximum_possible_points",
    "official_score_economics",
    "prospective_team_count",
    "rank_families_for_target",
    "score_candidate",
    "stable_canonical_hash",
    "team_score_multiplier",
    "translate_coefficients",
    "validate_coefficients",
    "validate_historical_containment",
]
