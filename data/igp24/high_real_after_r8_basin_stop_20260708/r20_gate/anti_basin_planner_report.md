# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 35
- Eligible candidates: 7
- Selected rows: 4
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `True`
- Reason: safe_to_review_only_after_pending_rows_resolve:24T25000|r=20=4
- Sync gate: `{"degraded_mode_summary": "22/22 details recovered; 22/22 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": ["safe_to_review_only_after_pending_rows_resolve:24T25000|r=20=4"], "partial_sync": false, "pending_high_label_basin_collisions": {"24T25000|r=20": 4}, "pending_pair_counts": {"24T25000|r=20": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [20], "submission_detail_complete": true}`
- Mode counts: `{"dense_mixed_support_gcd1": 2, "medium_mixed_support_gcd1": 2}`
- Mod-p signature counts: `{"none": 3, "p2:1-2-3-18;p3:1-1-1-8-13;p5:1-2-10-11;p7:1-1-1-4-17": 1}`
- Template family counts: `{"model:mixed:r20:dense_mixed_support_gcd1": 2, "model:mixed:r20:medium_mixed_support_gcd1": 2}`
- Basin fingerprint counts: `{"33465526667f9ca21a77d799": 1, "64f19fed392372573952bfad": 1, "99b6cb3c4c0d9ae3b90a6dbd": 1, "f29ba57c997c51c793139aa4": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `2161d95361f0` | 155.71 | 20 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 144850083840000 | `p2:1-2-3-18;p3:1-1-1-8-13;p5:1-2-10-11;p7:1-1-1-4-17` |
| 2 | `3e8fad1c89ac` | 151.40 | 20 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 10813088 | `None` |
| 3 | `2291e2bce38a` | 151.34 | 20 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 11857252 | `None` |
| 4 | `6a30bae40b37` | 151.21 | 20 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 14683640 | `None` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `2161d95361f0` | 155.71 | True | `strong_packet_candidate` | `` |
| 2 | `f8e4f26aec24` | 155.00 | True | `strong_packet_candidate` | `` |
| 3 | `3e8fad1c89ac` | 151.40 | True | `strong_packet_candidate` | `` |
| 4 | `1567b241a5db` | 151.34 | True | `strong_packet_candidate` | `` |
| 5 | `2291e2bce38a` | 151.34 | True | `strong_packet_candidate` | `` |
| 6 | `59cf9d910d4c` | 151.21 | True | `strong_packet_candidate` | `` |
| 7 | `6a30bae40b37` | 151.21 | True | `strong_packet_candidate` | `` |
| 8 | `7df9eae0a310` | -20.01 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 9 | `47f1cf331e34` | -48.60 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 10 | `e7b078cbd8c6` | -48.66 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 11 | `5768787e4663` | -48.66 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 12 | `426f4be4aca5` | -48.80 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate` |
| 13 | `b8b9b30434b6` | -73.72 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 14 | `28a5db6ea30c` | -74.08 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 15 | `0673a8670cb2` | -74.59 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |

Next decision: Do not submit this packet; local packet is ready, but wait for complete SAIR state and pending rows to resolve.
