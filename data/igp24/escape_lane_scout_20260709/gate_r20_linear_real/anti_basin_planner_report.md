# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 10
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_0_eligible_rows_below_min_8; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
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
| 1 | `cc006b8efc66` | -195.53 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 2 | `a82cc79e444f` | -196.54 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 3 | `d057941b79e3` | -196.72 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 4 | `0f1f3af9778a` | -196.72 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 5 | `27546e009d25` | -196.72 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 6 | `8e5c728256e3` | -196.77 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 7 | `1a7d4a12bdce` | -196.77 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 8 | `7788c1b86f9c` | -197.10 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 9 | `5c634392d4f7` | -197.11 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 10 | `ab1abe4e0947` | -197.99 | False | `reject_or_hold_known_basin_risk` | `construction_family_known_high_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
