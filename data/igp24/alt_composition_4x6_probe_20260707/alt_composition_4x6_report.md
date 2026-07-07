# IGP24 4x6 Alternate Composition Diagnostic

CPU-only local 4x6 alternate-composition diagnostic. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 1600
- Valid candidates: 110
- Selected rows: 24
- Queue status: `planner_review_ready_not_submitted`
- Selected r counts: `{"12": 24}`
- Selected mode counts: `{"outer_balanced_shift": 8, "outer_cubic_mixed_shift": 8, "outer_linear_quadratic_shift": 8}`
- Valid mode counts: `{"outer_balanced_shift": 34, "outer_cubic_mixed_shift": 40, "outer_linear_quadratic_shift": 36}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 1120, "even_support_g_x_squared_like,support_gcd_not_one": 158, "not_squarefree": 3, "real_root_count_not_target_bucket": 160, "reducible_over_q": 49}`

## Submission Readiness

- Status: `planner_review_ready_not_submitted`
- Planner scoring recommended: `True`
- Submitted by this tool: `False`
- Reason: Selected rows are locally valid 4x6 candidates with multiple perturbation modes; score with the anti-basin planner before any SAIR dry-run.

## Selected Rows

| rank | hash | r | mode | family | height | log disc |
| ---: | --- | ---: | --- | --- | ---: | ---: |
| 1 | `252045fc9d7e` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-37,-36,-35,-34|outer_y=0:-1,1:2,2:-1` | 25991674 | 275.990 |
| 2 | `a5a6f3bd9305` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-37,-36,-35,-34|outer_y=1:1,2:-1` | 25991674 | 275.659 |
| 3 | `219ae1452d11` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-36,-35,-34,-33|outer_y=0:-1,1:2,2:-1` | 26857054 | 277.229 |
| 4 | `9d5c96b6d8c9` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-36,-35,-34,-33|outer_y=1:1,2:-1` | 26857054 | 276.739 |
| 5 | `9cde07708f31` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-34,-33,-32,-31|outer_y=0:-1,1:2,2:-1` | 28602466 | 276.868 |
| 6 | `6b604d1a643d` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-34,-33,-32,-31|outer_y=1:1,2:-1` | 28602466 | 276.329 |
| 7 | `afe78a8e5b6d` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-32,-31,-30,-29|outer_y=0:-1,1:2,2:-1` | 30367414 | 275.750 |
| 8 | `27206c06aece` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-32,-31,-30,-29|outer_y=1:1,2:-1` | 30367414 | 275.172 |
| 9 | `0fb1b4429fbf` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-30,-29,-28,-27|outer_y=1:1,2:-1` | 32151898 | 273.599 |
| 10 | `02ef2d0b869a` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-28,-27,-26,-25|outer_y=0:-1,1:2,2:-1` | 33955918 | 272.350 |
| 11 | `8dd1a454cfaf` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-28,-27,-26,-25|outer_y=1:1,2:-1` | 33955918 | 271.684 |
| 12 | `622dea1cd75a` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-27,-26,-25,-24|outer_y=0:-1,1:2,2:-1` | 34865254 | 271.296 |
| 13 | `85a8c33ebd27` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-27,-26,-25,-24|outer_y=1:1,2:-1` | 34865254 | 270.604 |
| 14 | `72f1c312c340` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-26,-25,-24,-23|outer_y=0:2,1:-1,3:1` | 35520801 | 324.447 |
| 15 | `d0faeac3b9ab` | 12 | `outer_linear_quadratic_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_linear_quadratic_shift|levels=-26,-25,-24,-23|outer_y=1:1,2:-1` | 35779474 | 269.443 |
| 16 | `f3f0392cfaed` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-26,-25,-24,-23|outer_y=0:-1,1:2,2:-1` | 35779474 | 270.163 |
| 17 | `e29ea76b91d9` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-24,-23,-22,-21|outer_y=0:2,1:-1,3:1` | 37363893 | 321.120 |
| 18 | `275353f15c3d` | 12 | `outer_balanced_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_balanced_shift|levels=-24,-23,-22,-21|outer_y=0:-1,1:2,2:-1` | 37622566 | 267.651 |
| 19 | `8dfd4a8cabd1` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-22,-21,-20,-19|outer_y=0:2,1:-1,3:1` | 39226521 | 316.772 |
| 20 | `943852886c6f` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-20,-19,-18,-17|outer_y=0:2,1:-1,3:1` | 41108685 | 311.666 |
| 21 | `bb957b5a1cd6` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-18,-17,-16,-15|outer_y=0:2,1:-1,3:1` | 43876420 | 305.774 |
| 22 | `08135e8b78ae` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-17,-16,-15,-14|outer_y=0:2,1:-1,3:1` | 45726208 | 302.495 |
| 23 | `779b8d0b1af8` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-16,-15,-14,-13|outer_y=0:2,1:-1,3:1` | 47602492 | 298.962 |
| 24 | `f5a05127fa9c` | 12 | `outer_cubic_mixed_shift` | `4x6|inner_roots=-3,-2,-1,1,2,4|mode=outer_cubic_mixed_shift|levels=-14,-13,-12,-11|outer_y=0:2,1:-1,3:1` | 51434644 | 290.999 |

Caveat: these rows have local exact real-root, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
