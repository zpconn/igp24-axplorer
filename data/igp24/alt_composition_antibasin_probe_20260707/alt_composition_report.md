# IGP24 Alternate Composition Diagnostic

CPU-only local alternate-composition diagnostic. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 1400
- Valid candidates: 38
- Selected rows: 24
- Queue status: `manual_review_ready_not_submitted`
- Selected pattern counts: `{"8x3": 24}`
- Selected mode counts: `{"outer_high_coefficient_shift": 10, "outer_mixed_high_shift": 7, "outer_two_coefficient_shift": 7}`
- Valid pattern counts: `{"8x3": 38}`
- Valid mode counts: `{"outer_high_coefficient_shift": 17, "outer_mixed_high_shift": 10, "outer_three_coefficient_shift": 1, "outer_two_coefficient_shift": 10}`
- Trial pattern counts: `{"3x8": 620, "8x3": 780}`
- Selected r counts: `{"12": 13, "24": 11}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 160, "even_support_g_x_squared_like,support_gcd_not_one": 73, "excluded_perturbation_mode:outer_constant_shift": 982, "real_root_count_not_target_bucket": 58, "reducible_over_q": 89}`
- Rejected counts by pattern: `{"3x8": {"coefficient_height_exceeds_bound": 31, "even_support_g_x_squared_like,support_gcd_not_one": 61, "excluded_perturbation_mode:outer_constant_shift": 528}, "8x3": {"coefficient_height_exceeds_bound": 129, "even_support_g_x_squared_like,support_gcd_not_one": 12, "excluded_perturbation_mode:outer_constant_shift": 454, "real_root_count_not_target_bucket": 58, "reducible_over_q": 89}}`

## Submission Readiness

- Status: `manual_review_ready_not_submitted`
- Worth submitting later: `True`
- Submitted by this tool: `False`
- Reason: Selected rows are locally valid, structurally outside the exhausted 6x4 tower neighborhood, and hit high-real-root target buckets; hold for human/next-goal review before SAIR.

## Selected Rows

| rank | hash | pattern | r | mode | family | height | log disc |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| 1 | `a1e622b46274` | `8x3` | 24 | `outer_high_coefficient_shift` | `8x3|s=10|mode=outer_high_coefficient_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=1:3,6:-1` | 118763800 | 244.085 |
| 2 | `8305b1f37dcc` | `8x3` | 24 | `outer_high_coefficient_shift` | `8x3|s=11|mode=outer_high_coefficient_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=1:3,6:-1` | 244512565 | 246.486 |
| 3 | `97f22796a8dd` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=9|mode=outer_two_coefficient_shift|levels=-9,-8,-7,-6,-5,-4,-3,-2|outer_y=0:-1,2:1` | 457072308 | 210.499 |
| 4 | `9c34d70d2fef` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=9|mode=outer_two_coefficient_shift|levels=-10,-9,-8,-7,-6,-5,-4,-3|outer_y=0:-1,2:1` | 729109836 | 196.078 |
| 5 | `4c1cd86533ba` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=9|mode=outer_two_coefficient_shift|levels=-10,-9,-8,-7,-6,-5,-4,-3|outer_y=0:1,2:-1` | 729109836 | 202.390 |
| 6 | `0c192dbd5854` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=10|mode=outer_two_coefficient_shift|levels=2,3,4,5,6,7,8,9|outer_y=0:1,2:-1` | 797997200 | 214.792 |
| 7 | `d55ec0af1461` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=10|mode=outer_two_coefficient_shift|levels=-9,-8,-7,-6,-5,-4,-3,-2|outer_y=0:1,2:-1` | 797997200 | 214.792 |
| 8 | `f86dfbb47603` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=11|mode=outer_two_coefficient_shift|levels=-9,-8,-7,-6,-5,-4,-3,-2|outer_y=0:-1,2:1` | 1310976436 | 217.461 |
| 9 | `bf404229a931` | `8x3` | 24 | `outer_two_coefficient_shift` | `8x3|s=11|mode=outer_two_coefficient_shift|levels=2,3,4,5,6,7,8,9|outer_y=0:1,2:-1` | 1310976436 | 217.810 |
| 10 | `593dee11e4f9` | `8x3` | 24 | `outer_high_coefficient_shift` | `8x3|s=14|mode=outer_high_coefficient_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=0:10,5:-1` | 1572918424 | 252.013 |
| 11 | `02fbed7470e2` | `8x3` | 24 | `outer_high_coefficient_shift` | `8x3|s=14|mode=outer_high_coefficient_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=1:3,6:-1` | 1576145368 | 252.445 |
| 12 | `e22a83dd688c` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=8|mode=outer_mixed_high_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=0:5,1:-2,7:1` | 22780288 | 249.834 |
| 13 | `69015829bf80` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=8|mode=outer_mixed_high_shift|levels=-2,-1,1,2,3,4,5,6|outer_y=0:5,1:-2,7:1` | 30451312 | 283.600 |
| 14 | `9e344fee6c9e` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=9|mode=outer_mixed_high_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:5,1:-2,7:1` | 42409089 | 265.550 |
| 15 | `62413b1acc6f` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=9|mode=outer_mixed_high_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=0:5,1:-2,7:1` | 53808219 | 252.949 |
| 16 | `8a972b27fc45` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=10|mode=outer_mixed_high_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:5,1:-2,7:1` | 96261400 | 268.193 |
| 17 | `929f1d335989` | `8x3` | 12 | `outer_high_coefficient_shift` | `8x3|s=9|mode=outer_high_coefficient_shift|levels=-1,1,2,3,4,5,6,7|outer_y=1:3,6:-1` | 141689105 | 285.062 |
| 18 | `69c3a58a33a0` | `8x3` | 12 | `outer_high_coefficient_shift` | `8x3|s=9|mode=outer_high_coefficient_shift|levels=-7,-6,-5,-4,-3,-2,-1,1|outer_y=1:3,6:-1` | 141689105 | 285.198 |
| 19 | `618e88d3ba76` | `8x3` | 12 | `outer_high_coefficient_shift` | `8x3|s=10|mode=outer_high_coefficient_shift|levels=-2,-1,1,2,3,4,5,6|outer_y=1:3,6:-1` | 167350860 | 270.567 |
| 20 | `8d34125fadc4` | `8x3` | 12 | `outer_high_coefficient_shift` | `8x3|s=10|mode=outer_high_coefficient_shift|levels=-6,-5,-4,-3,-2,-1,1,2|outer_y=0:10,5:-1` | 167400860 | 258.148 |
| 21 | `0f3abbf6e840` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=11|mode=outer_mixed_high_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:5,1:-2,7:1` | 208393339 | 270.561 |
| 22 | `5681703f37c0` | `8x3` | 12 | `outer_mixed_high_shift` | `8x3|s=11|mode=outer_mixed_high_shift|levels=-4,-3,-2,-1,1,2,3,4|outer_y=0:5,1:-2,7:1` | 243546259 | 258.050 |
| 23 | `c2e1da0884ba` | `8x3` | 12 | `outer_high_coefficient_shift` | `8x3|s=10|mode=outer_high_coefficient_shift|levels=-1,1,2,3,4,5,6,7|outer_y=1:3,6:-1` | 273763936 | 288.411 |
| 24 | `54b3c8359b28` | `8x3` | 12 | `outer_high_coefficient_shift` | `8x3|s=10|mode=outer_high_coefficient_shift|levels=-7,-6,-5,-4,-3,-2,-1,1|outer_y=1:3,6:-1` | 273763936 | 288.547 |

Caveat: these rows have local exact real-root, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
