# IGP24 Label Basin Analysis

- Observations: 110
- Feedback files: 12
- Queue files: 10
- Progress labels loaded: 11

## Label Summary

| label | rows | r counts | global fully covered | team count | dominant families |
| --- | ---: | --- | --- | ---: | --- |
| 24T25000 | 43 | {"16": 17, "20": 10, "24": 16} | True | 58 | {"mixed_even_odd_perturbed": 4, "odd_perturbed_r24_6x4_tower_escape": 8, "positive_quadratic_product_plus_low_odd_perturbation": 8, "r16_diversity_probe": 5, "ten_positive_two_negative_quadratic_product_plus_low_odd_perturbation": 10, "three_odd_perturbed_near_composed": 4, "two_odd_perturbed_near_composed": 4} |
| 24T24979 | 28 | {"12": 15, "16": 13} | True | 60 | {"degree12_base_six_positive_roots_lifted_by_x2": 15, "r16_diversity_probe": 5, "r16_quadratic_lift": 8} |
| 24T24651 | 17 | {"12": 8, "24": 9} | True | 56 | {"outer_degree6_all_four_real_preimage_composed_with_even_quartic_double_well": 9, "outer_degree6_composed_with_even_quartic_double_well": 8} |
| 24T24932 | 8 | {"24": 8} | True | 48 | {"alt_composition_8x3": 8} |
| 24T23883 | 3 | {"12": 2, "24": 1} | True | 59 | {"outer_degree6_all_four_real_preimage_composed_with_even_quartic_double_well": 1, "outer_degree6_composed_with_even_quartic_double_well": 2} |
| 24T24970 | 3 | {"12": 3} | True | 60 | {"degree12_base_six_positive_roots_lifted_by_x2": 3} |
| 24T1310 | 2 | {"8": 2} | True | 41 | {"r8_quartic_lift": 2} |
| 24T22770 | 2 | {"12": 2} | True | 36 | {"degree12_base_six_positive_roots_lifted_by_x2": 2} |
| 24T9993 | 2 | {"8": 2} | True | 53 | {"r8_quartic_lift": 2} |
| 24T657 | 1 | {"8": 1} | True | 41 | {"r8_quartic_lift": 1} |
| 24T661 | 1 | {"8": 1} | True | 22 | {"r8_quartic_lift": 1} |

## Pair Basins

| pair | rows | global discovered | fully covered label | families | modes |
| --- | ---: | --- | --- | --- | --- |
| 24T25000|r=16 | 17 | True | True | {"mixed_even_odd_perturbed": 4, "r16_diversity_probe": 5, "three_odd_perturbed_near_composed": 4, "two_odd_perturbed_near_composed": 4} | {"mixed_even_odd_perturbed": 4, "odd_perturbed_near_composed": 5, "three_odd_perturbed_near_composed": 4, "two_odd_perturbed_near_composed": 4} |
| 24T25000|r=24 | 16 | True | True | {"odd_perturbed_r24_6x4_tower_escape": 8, "positive_quadratic_product_plus_low_odd_perturbation": 8} | {"single_low_odd_break": 3, "three_low_odd_break": 2, "two_low_odd_break": 3} |
| 24T24979|r=12 | 15 | True | True | {"degree12_base_six_positive_roots_lifted_by_x2": 15} | {"four_base_balanced_perturbation": 3, "single_base_coefficient_perturbation": 4, "structured_base_coefficient_perturbation": 3, "three_base_balanced_perturbation": 2, "two_base_wide_perturbation": 3} |
| 24T24979|r=16 | 13 | True | True | {"r16_diversity_probe": 5, "r16_quadratic_lift": 8} | {"exact_composed_new_base": 5} |
| 24T25000|r=20 | 10 | True | True | {"ten_positive_two_negative_quadratic_product_plus_low_odd_perturbation": 10} | {"single_low_odd_break": 3, "three_low_odd_break": 4, "two_low_odd_break": 3} |
| 24T24651|r=24 | 9 | True | True | {"outer_degree6_all_four_real_preimage_composed_with_even_quartic_double_well": 9} | {"outer_constant_shift": 9} |
| 24T24651|r=12 | 8 | True | True | {"outer_degree6_composed_with_even_quartic_double_well": 8} | {"outer_constant_shift": 7, "outer_two_coefficient_shift": 1} |
| 24T24932|r=24 | 8 | True | True | {"alt_composition_8x3": 8} | {"outer_constant_shift": 8} |
| 24T24970|r=12 | 3 | True | True | {"degree12_base_six_positive_roots_lifted_by_x2": 3} | {"single_base_coefficient_perturbation": 1, "three_base_balanced_perturbation": 1, "two_base_wide_perturbation": 1} |
| 24T1310|r=8 | 2 | True | True | {"r8_quartic_lift": 2} | {} |
| 24T22770|r=12 | 2 | True | True | {"degree12_base_six_positive_roots_lifted_by_x2": 2} | {"single_base_coefficient_perturbation": 2} |
| 24T23883|r=12 | 2 | True | True | {"outer_degree6_composed_with_even_quartic_double_well": 2} | {"outer_constant_shift": 2} |
| 24T9993|r=8 | 2 | True | True | {"r8_quartic_lift": 2} | {} |
| 24T23883|r=24 | 1 | True | True | {"outer_degree6_all_four_real_preimage_composed_with_even_quartic_double_well": 1} | {"outer_constant_shift": 1} |
| 24T657|r=8 | 1 | True | True | {"r8_quartic_lift": 1} | {} |
| 24T661|r=8 | 1 | True | True | {"r8_quartic_lift": 1} | {} |

## Anti-Basin Constraints

- **avoid_common_labels_without_new_structure** (high): Do not spend more submissions on rows predicted to remain in these basins unless the structure differs in support divisor, composition pattern, perturbation mode, or mod-p signature.
- **stop_exact_even_6x4_constant_shift_towers** (high): Require non-even support, non-constant outer perturbations, or a different decomposition degree pattern before submitting more tower rows.
- **avoid_generic_24T25000_perturbation_lanes** (high): Do not widen product/composed seed plus low odd perturbation lanes that already collapsed to 24T25000.
- **stop_odd_escaped_r24_6x4_towers** (high): Odd x-perturbed r24 6x4 tower rows broke exact even support but collapsed to generic 24T25000; use a different composition pattern before submitting more r24 tower-derived rows.
- **require_divisor2_escape_feature** (medium): Exact divisor-2 support is now a known basin feature; require odd support or a different support divisor unless doing discriminant-only alternates.
- **mod_p_pattern_novelty** (medium): For future queues, compute mod-p signatures and prefer rows with signatures absent from accepted common-label observations.

## Next Lane Decision

Do not submit more nearby r24 6x4 tower variants: exact even towers hit 24T23883/24T24651, while odd-escaped 6x4 towers hit generic 24T25000. Next generated queue must use an alternate composition pattern or another measurable label-steering change before any SAIR submission.
