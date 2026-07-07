# IGP24 Alternate Composition Diagnostic

CPU-only local alternate-composition diagnostic. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 410
- Valid candidates: 80
- Selected rows: 16
- Queue status: `manual_review_ready_not_submitted`
- Selected pattern counts: `{"8x3": 16}`
- Valid pattern counts: `{"8x3": 80}`
- Trial pattern counts: `{"3x8": 169, "8x3": 241}`
- Selected r counts: `{"24": 16}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 161, "even_support_g_x_squared_like,support_gcd_not_one": 124, "real_root_count_not_target_bucket": 17, "reducible_over_q": 28}`
- Rejected counts by pattern: `{"3x8": {"coefficient_height_exceeds_bound": 56, "even_support_g_x_squared_like,support_gcd_not_one": 113}, "8x3": {"coefficient_height_exceeds_bound": 105, "even_support_g_x_squared_like,support_gcd_not_one": 11, "real_root_count_not_target_bucket": 17, "reducible_over_q": 28}}`

## Submission Readiness

- Status: `manual_review_ready_not_submitted`
- Worth submitting later: `True`
- Submitted by this tool: `False`
- Reason: Selected rows are locally valid, structurally outside the exhausted 6x4 tower neighborhood, and hit high-real-root target buckets; hold for human/next-goal review before SAIR.

## Selected Rows

| rank | hash | pattern | r | mode | family | height | log disc |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| 1 | `3207fcbad6f7` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:1` | 21465432 | 237.462 |
| 2 | `f6d01d13d4d0` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:1` | 21465432 | 237.462 |
| 3 | `88f1e7761002` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:10` | 21465432 | 237.513 |
| 4 | `2c8838b3f843` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-10` | 21465432 | 237.350 |
| 5 | `438b2f438a1e` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=-2,-1,1,2,3,4,5,6|outer_y=0:3` | 32548464 | 232.760 |
| 6 | `687873704268` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=-2,-1,1,2,3,4,5,6|outer_y=0:-2` | 32548464 | 232.784 |
| 7 | `ab9559414dc6` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=9|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-1` | 47192058 | 240.605 |
| 8 | `dacbce3e07e4` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=9|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-10` | 47192058 | 240.509 |
| 9 | `e141365c0590` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=9|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:10` | 47192058 | 240.672 |
| 10 | `e38eb848a607` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=9|mode=outer_constant_shift|levels=-6,-5,-4,-3,-2,-1,1,2|outer_y=0:-5` | 77782356 | 236.143 |
| 11 | `2257d3c8a5ba` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=10|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-3` | 96313230 | 243.315 |
| 12 | `dfb540ba6d0b` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=10|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-20` | 96313230 | 243.088 |
| 13 | `d2b8c728394a` | `8x3` | 24 | `outer_high_coefficient_shift` | `8x3|s=10|mode=outer_high_coefficient_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=0:10,5:-1` | 118163800 | 243.665 |
| 14 | `a228d1246463` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=1,2,3,4,5,6,7,8|outer_y=0:-10` | 135717120 | 209.759 |
| 15 | `ed3120c333fd` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=8|mode=outer_constant_shift|levels=1,2,3,4,5,6,7,8|outer_y=0:3` | 135717120 | 209.939 |
| 16 | `0f5a176f107c` | `8x3` | 24 | `outer_constant_shift` | `8x3|s=9|mode=outer_constant_shift|levels=-7,-6,-5,-4,-3,-2,-1,1|outer_y=0:-3` | 142220546 | 228.039 |

Caveat: these rows have local exact real-root, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
