# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 12
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Reason: only_0_eligible_rows_below_min_8; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity
- Mode counts: `{}`
- Mod-p signature counts: `{}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `778075741c82` | -296.13 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 2 | `85cefa437fa2` | -296.13 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 3 | `85cefa437fa2` | -296.13 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 4 | `778075741c82` | -296.13 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 5 | `86f62f433b3f` | -296.17 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 6 | `86f62f433b3f` | -296.17 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 7 | `de699993e8a9` | -296.22 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 8 | `eb604c239982` | -296.22 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 9 | `2fe4b5059101` | -296.22 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 10 | `de699993e8a9` | -296.22 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 11 | `eb604c239982` | -296.22 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |
| 12 | `2fe4b5059101` | -296.22 | False | `reject_or_hold_known_basin_risk` | `support_gcd_not_one;even_support_g_x_squared_like;accepted_hash_duplicate` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
