# IGP24 Construction Family Calibration

- Created: `2026-07-10T07:16:40.110487+00:00`
- Source commit: `75bd6365c9bee88cd9b17880b96d726633b7988e`
- Families: `8`
- Recommended actions: `{"block_repeat_exact_basin": 1, "do_not_widen_without_material_structural_change": 2, "review_only_insufficient_evidence": 1, "review_only_until_reparameterized": 4}`
- Expected points: `unavailable_uncalibrated`
- Safety: Local-only construction-family calibration. It reads existing artifacts and writes advisory summaries; it does not submit to SAIR or claim exact Galois labels for compatibility-only rows.
- Live submission recommended now: `False`

## Family Actions

| family | action | structural | executable | adaptive rows | valuable adaptive | exact rows | target hits | false targets | packet selected | reasons |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `quartic_in_x6` | `block_repeat_exact_basin` | 33 | 7 | 16 | 16 | 4 | 0 | 4 | 0 | exact_label_route_outcome_blocked_repeat_basin |
| `generic_sparse_random` | `review_only_until_reparameterized` | 33 | 0 | 3 | 2 | 0 | 0 | 0 | 0 | adaptive_review_found_no_target_compatible_survivors, valuable_survivors_are_non_target_review_only |
| `composition_8x3` | `review_only_until_reparameterized` | 33 | 2 | 7 | 1 | 0 | 0 | 0 | 1 | adaptive_review_found_no_target_compatible_survivors, valuable_survivors_are_non_target_review_only |
| `composition_4x6` | `do_not_widen_without_material_structural_change` | 33 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | adaptive_review_found_no_valuable_survivors |
| `gx2_degree12_lift` | `review_only_until_reparameterized` | 33 | 30 | 0 | 0 | 0 | 0 | 0 | 0 | historical_replay_collapse_has_no_valuable_survivors |
| `tower_6x4` | `do_not_widen_without_material_structural_change` | 33 | 1 | 8 | 0 | 0 | 0 | 0 | 0 | adaptive_review_found_no_valuable_survivors |
| `positive_quadratic_product` | `review_only_until_reparameterized` | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | historical_replay_collapse_has_no_valuable_survivors |
| `linear_real_product` | `review_only_insufficient_evidence` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | insufficient_family_evidence |

## Interpretation

This report is an advisory calibration layer, not a verifier. It does not turn compatibility survivors into exact labels or expected official points.
Families marked for bounded experiments still need fresh candidate generation, known-hash exclusion, adaptive Frobenius review, exact-label verification, and the usual no-live-submission gate.
