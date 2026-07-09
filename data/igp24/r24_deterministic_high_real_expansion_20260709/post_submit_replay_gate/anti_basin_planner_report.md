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
- Reason: only_0_eligible_rows_below_min_8; selected_rows_do_not_have_min_perturbation_mode_count_3; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
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
| 1 | `47388e854930` | 1.70 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 2 | `edaa7062f581` | 1.70 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 3 | `cbf1b76f204b` | 1.70 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 4 | `25f15d313de0` | 1.64 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 5 | `28116793e051` | -38.36 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=4;crowded_mod_p_signature_hits=1` |
| 6 | `e3cc168c8fdf` | -63.36 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=2` |
| 7 | `4808b3e10a00` | -63.42 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=2` |
| 8 | `b74324d92baa` | -63.49 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=2` |
| 9 | `ae35388af803` | -203.20 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=3` |
| 10 | `36843df231d8` | -203.20 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=3` |
| 11 | `44c1c658d534` | -203.20 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=3` |
| 12 | `6754548c688a` | -203.20 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=3` |
| 13 | `c5f728e584aa` | -203.20 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=3` |
| 14 | `b4d8d742bb83` | -403.20 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=2` |
| 15 | `f8a1432c8316` | -403.20 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;template_family_known_high_label_collapse=24T25000;basin_fingerprint_known_high_label_collapse=24T25000;exact_crowded_basin_fingerprint_hits=3` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
