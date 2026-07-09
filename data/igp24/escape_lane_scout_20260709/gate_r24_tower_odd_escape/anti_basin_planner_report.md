# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 24
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_0_eligible_rows_below_min_8; selected_rows_do_not_have_min_perturbation_mode_count_1; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Sync gate: `{"degraded_mode_summary": "24/24 details recovered; 24/24 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
- Mode counts: `{}`
- Mod-p signature counts: `{}`
- Template family counts: `{}`
- Basin fingerprint counts: `{}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `f48ecb66049a` | 57.30 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 2 | `d6da4886246d` | 57.10 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 3 | `a256a3c49815` | 57.08 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 4 | `48eccac8e215` | 56.90 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 5 | `ddbda553f944` | 56.83 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 6 | `217e51b89373` | 56.51 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 7 | `af0c4ce10dfc` | 56.24 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 8 | `87934ccf2357` | 56.18 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 9 | `bf1e4877b6f1` | 56.10 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 10 | `6a1878ef0a3d` | 56.08 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 11 | `62afb19a0df7` | 56.05 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 12 | `656c513ef280` | 56.00 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 13 | `e0d34ed6e496` | 55.75 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 14 | `ffc7dd1d7b25` | 55.75 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |
| 15 | `5f8964cecf2e` | 55.69 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
