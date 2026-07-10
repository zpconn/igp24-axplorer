# IGP24 Construction Family Calibration

- Created: `2026-07-10T08:40:09.964530+00:00`
- Source commit: `a0060d0545344c2d70e191014ef9216aa0d33d04`
- Families: `8`
- Recommended actions: `{"block_repeat_exact_basin": 1, "candidate_for_generator_implementation": 2, "do_not_widen_without_material_structural_change": 2, "review_only_insufficient_evidence": 2, "review_only_until_reparameterized": 1}`
- Expected points: `unavailable_uncalibrated`
- Safety: Local-only construction-family calibration. It reads existing artifacts and writes advisory summaries; it does not submit to SAIR or claim exact Galois labels for compatibility-only rows.
- Live submission recommended now: `False`

## Family Actions

| family | action | structural | executable | adaptive rows | valuable adaptive | exact rows | target hits | false targets | packet selected | reasons |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `quartic_in_x6` | `block_repeat_exact_basin` | 3 | 3 | 16 | 16 | 4 | 0 | 4 | 0 | exact_label_route_outcome_blocked_repeat_basin |
| `generic_sparse_random` | `candidate_for_generator_implementation` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | structural_route_exists_but_no_executable_generator |
| `gx2_degree12_lift` | `candidate_for_generator_implementation` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | structural_route_exists_but_no_executable_generator |
| `composition_8x3` | `review_only_until_reparameterized` | 3 | 2 | 7 | 1 | 0 | 0 | 0 | 1 | adaptive_review_found_no_target_compatible_survivors, valuable_survivors_are_non_target_review_only |
| `composition_4x6` | `do_not_widen_without_material_structural_change` | 3 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | adaptive_review_found_no_valuable_survivors |
| `tower_6x4` | `do_not_widen_without_material_structural_change` | 3 | 1 | 8 | 0 | 0 | 0 | 0 | 0 | adaptive_review_found_no_valuable_survivors |
| `linear_real_product` | `review_only_insufficient_evidence` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | insufficient_family_evidence |
| `positive_quadratic_product` | `review_only_insufficient_evidence` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | insufficient_family_evidence |

## Interpretation

This report is an advisory calibration layer, not a verifier. It does not turn compatibility survivors into exact labels or expected official points.
Families marked for bounded experiments still need fresh candidate generation, known-hash exclusion, adaptive Frobenius review, exact-label verification, and the usual no-live-submission gate.
