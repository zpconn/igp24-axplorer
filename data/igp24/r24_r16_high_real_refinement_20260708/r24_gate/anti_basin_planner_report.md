# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 44
- Eligible candidates: 3
- Selected rows: 3
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_3_eligible_rows_below_min_4; only_3_model_generated_rows_below_min_4; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Sync gate: `{"degraded_mode_summary": "22/22 details recovered; 22/22 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [24], "submission_detail_complete": true}`
- Mode counts: `{"dense_mixed_support_gcd1": 2, "medium_mixed_support_gcd1": 1}`
- Mod-p signature counts: `{"none": 1, "p2:1-5-8-10;p3:1-1-1-21;p5:1-23;p7:1-3-20": 1, "p3:1-23;p5:1-7-16;p7:1-1-1-2-5-14": 1}`
- Template family counts: `{"model:mixed:r24:dense_mixed_support_gcd1": 2, "model:mixed:r24:medium_mixed_support_gcd1": 1}`
- Basin fingerprint counts: `{"3cae1f19e9eb8a2f4a412290": 1, "50faddcd74acf58a680ef6b5": 1, "89cbaf2808d63cd2757b0a39": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `b60ff30a7586` | 203.79 | 24 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 1931559552 | `p3:1-23;p5:1-7-16;p7:1-1-1-2-5-14` |
| 2 | `8c5ff74cd51d` | 203.79 | 24 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 1931559552 | `p2:1-5-8-10;p3:1-1-1-21;p5:1-23;p7:1-3-20` |
| 3 | `9d250eea5aa9` | 188.79 | 24 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 1931559552 | `None` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `8c5ff74cd51d` | 203.79 | True | `strong_packet_candidate` | `` |
| 2 | `b60ff30a7586` | 203.79 | True | `strong_packet_candidate` | `` |
| 3 | `9d250eea5aa9` | 188.79 | True | `strong_packet_candidate` | `` |
| 4 | `8305b1f37dcc` | -9.86 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 5 | `c05602fc0f8c` | -11.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 6 | `da0b4b43c0e0` | -11.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 7 | `796638a11606` | -11.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 8 | `2018298504d0` | -31.07 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 9 | `dacbce3e07e4` | -33.79 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 10 | `593dee11e4f9` | -36.08 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 11 | `c0df7a883c80` | -36.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 12 | `0d83f03eb475` | -36.21 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 13 | `4aed8c4ead77` | -36.26 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 14 | `17f65844117e` | -45.81 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 15 | `a38f4a3624fc` | -47.15 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
