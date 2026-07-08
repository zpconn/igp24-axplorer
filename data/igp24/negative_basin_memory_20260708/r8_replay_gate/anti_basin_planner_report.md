# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 32
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_0_eligible_rows_below_min_4; only_0_model_generated_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_1; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Sync gate: `{"degraded_mode_summary": "22/22 details recovered; 22/22 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
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
| 1 | `cd27f9717863` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 2 | `1c4996d77f02` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 3 | `a19647074c42` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 4 | `e759bfefc8f9` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 5 | `9808f4cd5c1d` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 6 | `d5da92d3b266` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 7 | `124b074d5d0a` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 8 | `1075804323d7` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 9 | `ab973c891eab` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 10 | `b5d16068d82a` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 11 | `568f33801e1f` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 12 | `35f554f5eed0` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 13 | `a037cdd189f0` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 14 | `ecef338e1e29` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |
| 15 | `8b18616b36d7` | -179.84 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T25000;template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=8` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
