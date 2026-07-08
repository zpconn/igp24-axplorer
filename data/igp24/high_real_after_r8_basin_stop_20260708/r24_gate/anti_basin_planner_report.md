# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 39
- Eligible candidates: 2
- Selected rows: 2
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Sync gate: `{"degraded_mode_summary": "22/22 details recovered; 22/22 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [24], "submission_detail_complete": true}`
- Mode counts: `{"medium_mixed_support_gcd1": 2}`
- Mod-p signature counts: `{"none": 1, "p2:1-23;p3:1-7-16;p5:1-3-20;p7:1-1-2-7-13": 1}`
- Template family counts: `{"model:mixed:r24:medium_mixed_support_gcd1": 2}`
- Basin fingerprint counts: `{"1d5261d1c012fd41aae493d6": 1, "5568f32b7eac61f4cca6045f": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `79d50771cbb4` | 208.93 | 24 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 725998 | `p2:1-23;p3:1-7-16;p5:1-3-20;p7:1-1-2-7-13` |
| 2 | `e408737b742b` | 188.79 | 24 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 1931559552 | `None` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `79d50771cbb4` | 208.93 | True | `strong_packet_candidate` | `` |
| 2 | `e408737b742b` | 188.79 | True | `strong_packet_candidate` | `` |
| 3 | `48024349b2e3` | -8.27 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 4 | `a1e622b46274` | -9.39 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 5 | `8305b1f37dcc` | -9.86 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 6 | `02fbed7470e2` | -11.08 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 7 | `da0b4b43c0e0` | -11.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 8 | `c05602fc0f8c` | -11.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 9 | `796638a11606` | -11.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 10 | `b8258363b2f7` | -11.31 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 11 | `d1e6f4ff199c` | -30.75 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 12 | `49c02cb24668` | -30.89 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 13 | `efb95ccde1e1` | -30.89 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 14 | `aee83a43fc3e` | -30.94 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 15 | `2018298504d0` | -31.07 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
