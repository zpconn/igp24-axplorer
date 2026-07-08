# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 40
- Eligible candidates: 5
- Selected rows: 3
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_3_eligible_rows_below_min_4; only_3_model_generated_rows_below_min_4; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Sync gate: `{"degraded_mode_summary": "22/22 details recovered; 22/22 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16], "submission_detail_complete": true}`
- Mode counts: `{"dense_mixed_support_gcd1": 1, "medium_mixed_support_gcd1": 2}`
- Mod-p signature counts: `{"none": 1, "p2:7-8-9;p5:2-2-5-7-8;p7:4-6-14": 1, "p7:2-22": 1}`
- Template family counts: `{"model:mixed:r16:dense_mixed_support_gcd1": 1, "model:mixed:r16:medium_mixed_support_gcd1": 2}`
- Basin fingerprint counts: `{"0c64d09ca8a889c6cee1540d": 1, "2f422da111c7a8834d653c53": 1, "61f79676ed982c87d1ce4973": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `e5a78c6bb1ba` | 192.63 | 16 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 829440 | `p7:2-22` |
| 2 | `f749dfde7a2e` | 191.61 | 16 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 3993603 | `p2:7-8-9;p5:2-2-5-7-8;p7:4-6-14` |
| 3 | `7d6bd67c4b29` | 178.68 | 16 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 165784 | `None` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `e5a78c6bb1ba` | 192.63 | True | `strong_packet_candidate` | `` |
| 2 | `36d719fde8c0` | 192.08 | True | `strong_packet_candidate` | `` |
| 3 | `c63a754a19e4` | 191.61 | True | `strong_packet_candidate` | `` |
| 4 | `f749dfde7a2e` | 191.61 | True | `strong_packet_candidate` | `` |
| 5 | `7d6bd67c4b29` | 178.68 | True | `strong_packet_candidate` | `` |
| 6 | `1c3b415990a7` | -21.32 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 7 | `d0e0031b7cbb` | -42.30 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 8 | `624066636c9c` | -46.35 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 9 | `70b58279f77a` | -46.35 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 10 | `2259d4517994` | -46.58 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 11 | `9a2847991d70` | -46.70 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 12 | `13094bd39221` | -46.76 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 13 | `7bcf04f2e733` | -46.89 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 14 | `b3e1bf9ee555` | -46.91 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 15 | `c9e9a9399712` | -46.95 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
