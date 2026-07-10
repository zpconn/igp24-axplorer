# IGP24 Construction Family Calibration

- Created: `2026-07-10T06:22:57.324140+00:00`
- Source commit: `fed1e40ab44d74f3525d3fc801b998cfef36ca8b`
- Families: `8`
- Recommended actions: `{"baseline_only_until_new_conditioning": 1, "block_repeat_exact_basin": 1, "candidate_for_generator_implementation": 2, "do_not_widen_without_material_structural_change": 1, "review_only_insufficient_evidence": 1, "review_only_until_reparameterized": 2}`
- Expected points: `unavailable_uncalibrated`
- Safety: Local-only construction-family calibration. It reads existing artifacts and writes advisory summaries; it does not submit to SAIR or claim exact Galois labels for compatibility-only rows.
- Live submission recommended now: `False`

## Family Actions

| family | action | structural | executable | adaptive rows | valuable adaptive | exact rows | target hits | false targets | packet selected | reasons |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `quartic_in_x6` | `block_repeat_exact_basin` | 31 | 5 | 16 | 16 | 4 | 0 | 4 | 0 | exact_label_route_outcome_blocked_repeat_basin |
| `composition_8x3` | `candidate_for_generator_implementation` | 31 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | structural_route_exists_but_no_executable_generator |
| `tower_6x4` | `candidate_for_generator_implementation` | 31 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | structural_route_exists_but_no_executable_generator |
| `generic_sparse_random` | `baseline_only_until_new_conditioning` | 31 | 0 | 3 | 2 | 0 | 0 | 0 | 1 | historical_replay_collapse_has_no_valuable_survivors |
| `composition_4x6` | `do_not_widen_without_material_structural_change` | 31 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | adaptive_review_found_no_valuable_survivors |
| `gx2_degree12_lift` | `review_only_until_reparameterized` | 31 | 30 | 0 | 0 | 0 | 0 | 0 | 0 | historical_replay_collapse_has_no_valuable_survivors |
| `positive_quadratic_product` | `review_only_until_reparameterized` | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | historical_replay_collapse_has_no_valuable_survivors |
| `linear_real_product` | `review_only_insufficient_evidence` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | insufficient_family_evidence |

## Interpretation

This report is an advisory calibration layer, not a verifier. It does not turn compatibility survivors into exact labels or expected official points.
Families marked for bounded experiments still need fresh candidate generation, known-hash exclusion, adaptive Frobenius review, exact-label verification, and the usual no-live-submission gate.
