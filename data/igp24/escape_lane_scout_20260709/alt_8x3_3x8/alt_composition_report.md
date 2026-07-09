# IGP24 Alternate Composition Diagnostic

CPU-only local alternate-composition diagnostic. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 260
- Valid candidates: 3
- Selected rows: 3
- Queue status: `diagnostic_too_few_valid_rows`
- Selected pattern counts: `{"8x3": 3}`
- Selected mode counts: `{"outer_high_coefficient_shift": 1, "outer_two_coefficient_shift": 2}`
- Valid pattern counts: `{"8x3": 3}`
- Valid mode counts: `{"outer_high_coefficient_shift": 1, "outer_two_coefficient_shift": 2}`
- Trial pattern counts: `{"3x8": 105, "8x3": 155}`
- Selected r counts: `{"24": 3}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 27, "even_support_g_x_squared_like,support_gcd_not_one": 13, "excluded_perturbation_mode:outer_constant_shift": 171, "real_root_count_not_target_bucket": 14, "reducible_over_q": 32}`
- Rejected counts by pattern: `{"3x8": {"coefficient_height_exceeds_bound": 6, "even_support_g_x_squared_like,support_gcd_not_one": 12, "excluded_perturbation_mode:outer_constant_shift": 87}, "8x3": {"coefficient_height_exceeds_bound": 21, "even_support_g_x_squared_like,support_gcd_not_one": 1, "excluded_perturbation_mode:outer_constant_shift": 84, "real_root_count_not_target_bucket": 14, "reducible_over_q": 32}}`

## Submission Readiness

- Status: `diagnostic_only_not_ready`
- Worth submitting later: `False`
- Submitted by this tool: `False`
- Reason: Too few locally valid structurally novel rows were selected.

## Selected Rows

| rank | hash | pattern | r | mode | family | height | log disc |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| 1 | `886f7c30a5ad` | `8x3` | 24 | `outer_high_coefficient_shift` | `8x3|s=11|mode=outer_high_coefficient_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=0:10,5:-1` | 243546259 | 246.061 |
| 2 | `0c192dbd5854` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=10|mode=outer_two_coefficient_shift|levels=2,3,4,5,6,7,8,9|outer_y=0:1,2:-1` | 797997200 | 214.792 |
| 3 | `bf404229a931` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=11|mode=outer_two_coefficient_shift|levels=2,3,4,5,6,7,8,9|outer_y=0:1,2:-1` | 1310976436 | 217.810 |

Caveat: these rows have local exact real-root, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
