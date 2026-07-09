"""Declared construction-family metadata for IGP24 routing.

This module is intentionally conservative. A construction family can provide
structural routing evidence, but it must not claim an exact 24T label. Exact
labels still require SAIR/Magma-style verification, and cycle-type
compatibility remains necessary evidence only.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from src.igp24.group_compatibility import GroupRecord

SOUNDNESS_NOTE = "declared_structural_routing_only_not_exact_label_evidence"


def _ints(values: Iterable[int]) -> tuple[int, ...]:
    return tuple(sorted({int(value) for value in values}))


def _strings(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(str(value) for value in values if str(value))


@dataclass(frozen=True)
class ConstructionFamily:
    """A structural family used to generate or route degree-24 candidates."""

    name: str
    display_name: str
    aliases: tuple[str, ...] = ()
    degree_pattern: tuple[int, ...] = ()
    expected_block_sizes: tuple[int, ...] = ()
    imprimitive_expectation: str = "unknown"
    primitive_target_fit: str = "unknown"
    solvability_bias: str = "unknown"
    supported_r_values: tuple[int, ...] = ()
    parameterization: tuple[str, ...] = ()
    justified_group_constraints: tuple[str, ...] = ()
    mutation_parameters: tuple[str, ...] = ()
    known_collapse_labels: tuple[str, ...] = ()
    known_verified_pairs: tuple[str, ...] = ()
    known_score_positive_pairs: tuple[str, ...] = ()
    source_scripts: tuple[str, ...] = ()
    notes: str = ""
    exact_label_claimed: bool = False
    soundness: str = SOUNDNESS_NOTE

    def __post_init__(self) -> None:
        if self.exact_label_claimed:
            raise ValueError(f"{self.name} must not claim exact 24T labels")
        if self.supported_r_values and any(value < 0 or value > 24 for value in self.supported_r_values):
            raise ValueError(f"{self.name} has an invalid real-root count")
        if self.degree_pattern and sum(self.degree_pattern) != 24 and _product(self.degree_pattern) != 24:
            raise ValueError(f"{self.name} degree pattern does not describe degree 24")

    def supports_r(self, r_value: int | None) -> bool:
        return r_value is None or not self.supported_r_values or int(r_value) in self.supported_r_values

    def all_names(self) -> tuple[str, ...]:
        return (self.name,) + self.aliases

    def as_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "aliases": list(self.aliases),
            "degree_pattern": list(self.degree_pattern),
            "expected_block_sizes": list(self.expected_block_sizes),
            "imprimitive_expectation": self.imprimitive_expectation,
            "primitive_target_fit": self.primitive_target_fit,
            "solvability_bias": self.solvability_bias,
            "supported_r_values": list(self.supported_r_values),
            "parameterization": list(self.parameterization),
            "justified_group_constraints": list(self.justified_group_constraints),
            "mutation_parameters": list(self.mutation_parameters),
            "known_collapse_labels": list(self.known_collapse_labels),
            "known_verified_pairs": list(self.known_verified_pairs),
            "known_score_positive_pairs": list(self.known_score_positive_pairs),
            "source_scripts": list(self.source_scripts),
            "notes": self.notes,
            "exact_label_claimed": self.exact_label_claimed,
            "soundness": self.soundness,
        }


def _product(values: Sequence[int]) -> int:
    out = 1
    for value in values:
        out *= int(value)
    return out


class ConstructionRegistry:
    """Lookup and routing helpers for construction-family metadata."""

    def __init__(self, families: Iterable[ConstructionFamily]) -> None:
        self._families = tuple(families)
        self._by_alias: dict[str, ConstructionFamily] = {}
        for family in self._families:
            for name in family.all_names():
                key = normalize_family_name(name)
                if key in self._by_alias:
                    raise ValueError(f"duplicate construction family alias: {name}")
                self._by_alias[key] = family

    def families(self) -> tuple[ConstructionFamily, ...]:
        return self._families

    def resolve(self, value: str | None) -> ConstructionFamily | None:
        if not value:
            return None
        return self._by_alias.get(normalize_family_name(str(value)))

    def from_metadata(self, metadata: dict[str, Any]) -> ConstructionFamily | None:
        for key in (
            "construction_family",
            "source_family",
            "generation_strategy",
            "strategy",
            "resolved_generation_strategy",
            "template_family_id",
            "support_pattern",
        ):
            family = self.resolve(str(metadata.get(key) or ""))
            if family is not None:
                return family
        template = str(metadata.get("template_family_id") or "")
        if template.startswith("model:"):
            return self.resolve("model_sample_export")
        return None

    def families_supporting_r(self, r_value: int | None) -> list[ConstructionFamily]:
        return [family for family in self._families if family.supports_r(r_value)]

    def rank_for_target(
        self,
        *,
        r_value: int | None,
        group_record: GroupRecord | None = None,
        avoid_labels: Iterable[str] = (),
        top_limit: int | None = None,
    ) -> list[dict[str, Any]]:
        avoid = {str(label) for label in avoid_labels}
        rows = [
            rank_family_for_target(family, r_value=r_value, group_record=group_record, avoid_labels=avoid)
            for family in self._families
        ]
        rows.sort(key=lambda row: (row["routing_score"], row["family"]), reverse=True)
        if top_limit is not None:
            return rows[: int(top_limit)]
        return rows

    def as_json(self) -> dict[str, Any]:
        return {
            "record_type": "igp24_construction_family_registry",
            "schema_version": 1,
            "soundness": SOUNDNESS_NOTE,
            "family_count": len(self._families),
            "exact_label_claimed_count": sum(1 for family in self._families if family.exact_label_claimed),
            "families": [family.as_json() for family in self._families],
        }


def normalize_family_name(value: str) -> str:
    return str(value).strip().lower().replace("-", "_")


def rank_family_for_target(
    family: ConstructionFamily,
    *,
    r_value: int | None,
    group_record: GroupRecord | None = None,
    avoid_labels: Iterable[str] = (),
) -> dict[str, Any]:
    score = 0.0
    reasons: list[str] = []
    warnings: list[str] = []

    if family.supports_r(r_value):
        score += 90.0
        if r_value is not None:
            reasons.append(f"supports_r={int(r_value)}")
    else:
        score -= 140.0
        warnings.append(f"unsupported_r={int(r_value) if r_value is not None else 'unknown'}")

    if family.known_score_positive_pairs:
        score += min(35.0, 12.0 * len(family.known_score_positive_pairs))
        reasons.append("has_score_positive_history")
    elif family.known_verified_pairs:
        score += min(12.0, 2.0 * len(family.known_verified_pairs))
        reasons.append("has_verified_pair_history")

    blocked_labels = sorted(set(family.known_collapse_labels) & {str(label) for label in avoid_labels})
    if blocked_labels:
        score -= 35.0
        warnings.append(f"known_collapse_labels_in_avoid_set={','.join(blocked_labels)}")

    if group_record is not None:
        if group_record.primitive is True:
            if family.imprimitive_expectation == "forced":
                score -= 65.0
                warnings.append("forced_imprimitive_family_for_primitive_target")
            elif family.imprimitive_expectation in {"not_forced", "unknown"}:
                score += 18.0
                reasons.append("primitive_target_not_contradicted")
        elif group_record.primitive is False:
            if family.imprimitive_expectation in {"forced", "likely"}:
                score += 34.0
                reasons.append("imprimitive_target_matches_family")
            else:
                score -= 8.0
                warnings.append("imprimitive_target_without_declared_block_structure")

        group_blocks = set(int(value) for value in group_record.block_sizes)
        family_blocks = set(int(value) for value in family.expected_block_sizes)
        matching_blocks = sorted(group_blocks & family_blocks)
        if matching_blocks:
            score += 16.0 + min(24.0, 4.0 * len(matching_blocks))
            reasons.append(f"matching_block_sizes={','.join(str(value) for value in matching_blocks)}")
        elif group_blocks and family.imprimitive_expectation == "forced":
            score -= 12.0
            warnings.append("forced_block_structure_not_matched_to_target_record")

        if group_record.solvable is True:
            if family.solvability_bias in {"likely", "possible"}:
                score += 18.0
                reasons.append("solvable_target_family_bias")
        elif group_record.solvable is False and family.solvability_bias == "likely":
            score -= 14.0
            warnings.append("likely_solvable_family_for_nonsolvable_target")

    if family.name == "generic_sparse_random":
        score -= 10.0
        reasons.append("baseline_diversity_family_not_primary_targeting")

    return {
        "family": family.name,
        "display_name": family.display_name,
        "routing_score": round(score, 3),
        "supports_target_r": family.supports_r(r_value),
        "degree_pattern": list(family.degree_pattern),
        "expected_block_sizes": list(family.expected_block_sizes),
        "imprimitive_expectation": family.imprimitive_expectation,
        "primitive_target_fit": family.primitive_target_fit,
        "solvability_bias": family.solvability_bias,
        "known_collapse_labels": list(family.known_collapse_labels),
        "known_verified_pairs": list(family.known_verified_pairs),
        "known_score_positive_pairs": list(family.known_score_positive_pairs),
        "reasons": reasons,
        "warnings": warnings,
        "exact_label_claimed": family.exact_label_claimed,
        "soundness": family.soundness,
    }


def rank_families_for_target(
    *,
    r_value: int | None,
    group_record: GroupRecord | None = None,
    avoid_labels: Iterable[str] = (),
    registry: ConstructionRegistry | None = None,
    top_limit: int | None = None,
) -> list[dict[str, Any]]:
    return (registry or default_registry()).rank_for_target(
        r_value=r_value,
        group_record=group_record,
        avoid_labels=avoid_labels,
        top_limit=top_limit,
    )


def default_registry() -> ConstructionRegistry:
    return ConstructionRegistry(
        [
            ConstructionFamily(
                name="gx2_degree12_lift",
                display_name="g(x^2) degree-12 lift",
                aliases=(
                    "degree12_base_six_positive_roots_lifted_by_x2",
                    "r12_exact_composed_base_perturbation_probe",
                    "r16_diversified_root_layout_probe",
                    "r12_gx2_structured_score_followup",
                ),
                degree_pattern=(12, 2),
                expected_block_sizes=(2, 12),
                imprimitive_expectation="forced",
                primitive_target_fit="poor",
                solvability_bias="possible",
                supported_r_values=_ints(range(0, 25, 2)),
                parameterization=(
                    "degree-12 base polynomial g(y)",
                    "lift y=x^2",
                    "optional off-block perturbations only when explicitly declared",
                ),
                justified_group_constraints=(
                    "exact g(x^2) support forces a block system of size 2 before perturbation",
                    "near-composed variants need cycle-type compatibility before scoring",
                ),
                mutation_parameters=("base root layout", "off-block exponent set", "coefficient deltas"),
                known_collapse_labels=("24T24970", "24T24979", "24T25000"),
                known_verified_pairs=("24T22770|r=12", "24T24970|r=12", "24T24979|r=12", "24T24979|r=16"),
                known_score_positive_pairs=("24T22770|r=12",),
                source_scripts=(
                    "scripts/igp24_r12_structured_probe.py",
                    "scripts/igp24_r12_structured_followup.py",
                    "scripts/igp24_r16_diversity_probe.py",
                ),
                notes="Useful for even-r imprimitive scouting, but recent nearby lanes collapsed into crowded labels.",
            ),
            ConstructionFamily(
                name="quartic_in_x6",
                display_name="quartic in x^6",
                aliases=(
                    "quartic_lift",
                    "r8_quartic_lift_perturbed",
                    "r8_quartic_lift_score_followup",
                    "r8_score_followup_24T9993",
                ),
                degree_pattern=(4, 6),
                expected_block_sizes=(6, 12),
                imprimitive_expectation="forced",
                primitive_target_fit="poor",
                solvability_bias="possible",
                supported_r_values=(0, 4, 8, 12, 16, 20, 24),
                parameterization=("quartic base in y=x^6", "fiber sign pattern", "off-core odd perturbation mode"),
                justified_group_constraints=(
                    "unperturbed support is composed through x^6",
                    "off-core perturbations must be treated as structural escapes, not exact label evidence",
                ),
                mutation_parameters=("quartic coefficients", "off-core exponent pair", "coefficient deltas"),
                known_collapse_labels=("24T24979", "24T25000"),
                known_verified_pairs=("24T657|r=8", "24T661|r=8", "24T1310|r=8", "24T9993|r=8"),
                known_score_positive_pairs=("24T9993|r=8",),
                source_scripts=(
                    "scripts/igp24_r8_score_followup_generate.py",
                    "scripts/igp24_r8_score_followup_lane.py",
                ),
                notes="Historically found the best project score row, but nearby follow-up lanes became crowded.",
            ),
            ConstructionFamily(
                name="tower_6x4",
                display_name="6 by 4 tower/composition",
                aliases=("odd_perturbed_r24_6x4_tower_escape", "r24_tower_odd_escape_probe", "r12_tower_probe"),
                degree_pattern=(6, 4),
                expected_block_sizes=(4, 6, 12),
                imprimitive_expectation="forced",
                primitive_target_fit="poor",
                solvability_bias="possible",
                supported_r_values=(0, 4, 8, 12, 16, 20, 24),
                parameterization=("outer degree-6 polynomial", "inner quartic", "tower-level perturbation"),
                justified_group_constraints=("composition/tower form implies imprimitive block structure before escapes",),
                mutation_parameters=("outer coefficients", "inner quartic parameter", "odd escape perturbations"),
                known_collapse_labels=("24T23883", "24T24651", "24T25000"),
                known_verified_pairs=("24T23883|r=12", "24T24651|r=12", "24T24651|r=24"),
                source_scripts=("scripts/igp24_r12_tower_probe.py", "scripts/igp24_r24_tower_odd_escape_probe.py"),
                notes="Keep as a structured lane only when block compatibility is useful and old tower basins are avoided.",
            ),
            ConstructionFamily(
                name="composition_8x3",
                display_name="8 by 3 composition",
                aliases=("alt_composition_8x3", "alt_composition_r8_3x8", "first_reviewed_8x3_rows"),
                degree_pattern=(8, 3),
                expected_block_sizes=(3, 8, 12),
                imprimitive_expectation="forced",
                primitive_target_fit="poor",
                solvability_bias="possible",
                supported_r_values=(0, 4, 8, 12, 16, 20, 24),
                parameterization=("outer degree-8 polynomial", "inner cubic", "inner/outer perturbation mode"),
                justified_group_constraints=("composed form implies an imprimitive block system before perturbation",),
                mutation_parameters=("outer coefficient shift", "inner level shift", "fiber layout"),
                known_collapse_labels=("24T25000",),
                known_verified_pairs=("24T25000|r=4", "24T25000|r=12", "24T25000|r=16"),
                source_scripts=("scripts/igp24_alt_8x3_sair_probe.py",),
                notes="Prior submissions mostly collapsed; require materially different compatibility evidence before widening.",
            ),
            ConstructionFamily(
                name="composition_4x6",
                display_name="4 by 6 composition",
                aliases=("alt_composition_4x6", "new_4x6_inner_family_not_current_roots"),
                degree_pattern=(4, 6),
                expected_block_sizes=(4, 6, 12),
                imprimitive_expectation="forced",
                primitive_target_fit="poor",
                solvability_bias="possible",
                supported_r_values=(0, 4, 8, 12, 16, 20, 24),
                parameterization=("outer degree-4 polynomial", "inner sextic", "inner-root layout"),
                justified_group_constraints=("composed form gives block-structure evidence only",),
                mutation_parameters=("outer shift", "inner-root set", "mixed perturbation mode"),
                known_collapse_labels=("24T25000",),
                known_verified_pairs=("24T25000|r=16",),
                source_scripts=("scripts/igp24_alt_composition_4x6_probe.py",),
                notes="Use only with a new inner-root family and compatibility evidence.",
            ),
            ConstructionFamily(
                name="linear_real_product",
                display_name="linear-real-root product seed",
                aliases=(
                    "twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation",
                    "r20_linear_real_roots_probe",
                ),
                degree_pattern=(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2),
                expected_block_sizes=(),
                imprimitive_expectation="not_forced",
                primitive_target_fit="possible",
                solvability_bias="unknown",
                supported_r_values=(20,),
                parameterization=("20 integer real roots", "two no-real quadratic factors", "low coefficient perturbations"),
                justified_group_constraints=(
                    "base seed fixes real-root count locally but does not assert final Galois structure",
                ),
                mutation_parameters=("real-root layout", "no-real quadratic constants", "low coefficient breaks"),
                known_collapse_labels=("24T25000",),
                known_verified_pairs=("24T25000|r=20",),
                source_scripts=("scripts/igp24_r20_linear_real_probe.py",),
                notes="A non-composed high-real lane; promising only if cycle compatibility escapes crowded labels.",
            ),
            ConstructionFamily(
                name="positive_quadratic_product",
                display_name="positive quadratic product seed",
                aliases=(
                    "positive_quadratic_product_plus_low_odd_perturbation",
                    "r24_high_real_quadratic_product_probe",
                    "quadratic_product_construction",
                ),
                degree_pattern=(2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2),
                expected_block_sizes=(2, 12),
                imprimitive_expectation="likely",
                primitive_target_fit="weak",
                solvability_bias="possible",
                supported_r_values=(24,),
                parameterization=("twelve positive quadratic factors", "low odd perturbations"),
                justified_group_constraints=(
                    "base seed is a reducible all-real product; perturbations are heuristic escapes only",
                ),
                mutation_parameters=("positive quadratic roots", "odd exponent set", "coefficient deltas"),
                known_collapse_labels=("24T23883", "24T24651", "24T25000"),
                known_verified_pairs=("24T23883|r=24", "24T24651|r=24", "24T25000|r=24"),
                source_scripts=("scripts/igp24_r24_high_real_probe.py",),
                notes="Useful for r24 local validity pressure, but historical output collapsed heavily.",
            ),
            ConstructionFamily(
                name="generic_sparse_random",
                display_name="generic sparse/random model export",
                aliases=(
                    "generic sparse/random",
                    "model_sample_export",
                    "fixed_sparse_template",
                    "sparse",
                    "mixed",
                    "structured",
                    "sparse_mixed_support_gcd1",
                ),
                degree_pattern=(24,),
                expected_block_sizes=(),
                imprimitive_expectation="unknown",
                primitive_target_fit="possible",
                solvability_bias="unknown",
                supported_r_values=_ints(range(0, 25, 2)),
                parameterization=("AXG token model or random coefficient strategy", "support pattern", "coefficient bound"),
                justified_group_constraints=(
                    "no declared exact group structure; must rely on cycle-type compatibility",
                ),
                mutation_parameters=("support pattern", "target-r control token", "coefficient sampling temperature"),
                known_collapse_labels=("24T24970", "24T24979", "24T25000"),
                known_verified_pairs=("24T24979|r=16", "24T25000|r=16", "24T25000|r=20", "24T25000|r=24"),
                source_scripts=("scripts/igp24_score_sample_export.py", "scripts/igp24_gpu_sampler_probe.py"),
                notes="Keep as a baseline/source of raw diversity; never treat shape novelty as exact group targeting.",
            ),
        ]
    )


def registry_summary(registry: ConstructionRegistry) -> dict[str, Any]:
    r_counts: Counter[str] = Counter()
    imprimitive_counts: Counter[str] = Counter()
    for family in registry.families():
        for r_value in family.supported_r_values:
            r_counts[str(r_value)] += 1
        imprimitive_counts[family.imprimitive_expectation] += 1
    return {
        "record_type": "igp24_construction_registry_summary",
        "family_count": len(registry.families()),
        "soundness": SOUNDNESS_NOTE,
        "exact_label_claimed_count": sum(1 for family in registry.families() if family.exact_label_claimed),
        "supported_r_family_counts": dict(sorted(r_counts.items(), key=lambda item: int(item[0]))),
        "imprimitive_expectation_counts": dict(sorted(imprimitive_counts.items())),
    }
