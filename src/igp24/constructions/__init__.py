"""Construction-family registry for IGP24 search routing."""

from src.igp24.constructions.generators import (
    GX2_GENERATOR_NAME,
    GENERATOR_SOUNDNESS,
    QUARTIC_X6_GENERATOR_NAME,
    coefficients_from_gx2_trial,
    coefficients_from_quartic_x6_trial,
    coefficients_from_trial_for_family,
    executable_generator_for_family,
    generation_status_for_route,
    iter_gx2_trials,
    iter_quartic_x6_trials,
    iter_trials_for_family,
)
from src.igp24.constructions.registry import (
    ConstructionFamily,
    ConstructionRegistry,
    default_registry,
    rank_families_for_target,
)

__all__ = [
    "ConstructionFamily",
    "ConstructionRegistry",
    "GENERATOR_SOUNDNESS",
    "GX2_GENERATOR_NAME",
    "QUARTIC_X6_GENERATOR_NAME",
    "coefficients_from_gx2_trial",
    "coefficients_from_quartic_x6_trial",
    "coefficients_from_trial_for_family",
    "default_registry",
    "executable_generator_for_family",
    "generation_status_for_route",
    "iter_gx2_trials",
    "iter_quartic_x6_trials",
    "iter_trials_for_family",
    "rank_families_for_target",
]
