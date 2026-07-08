# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 32
- Eligible candidates: 5
- Selected rows: 4
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Local packet ready: `True`
- Reason: anti-basin gates passed
- Sync gate: `{"degraded_mode_summary": "22/22 details recovered; 22/22 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16], "submission_detail_complete": true}`
- Mode counts: `{"dense_mixed_support_gcd1": 2, "medium_mixed_support_gcd1": 2}`
- Mod-p signature counts: `{"p2:1-2-21;p3:1-2-4-8-9;p5:1-1-1-4-6-11;p7:1-1-2-3-6-11": 1, "p3:1-2-2-19;p5:1-1-2-20;p7:1-2-4-4-6-7": 1, "p5:8-16": 1, "p7:2-3-19": 1}`
- Template family counts: `{"model:mixed:r16:dense_mixed_support_gcd1": 2, "model:mixed:r16:medium_mixed_support_gcd1": 2}`
- Basin fingerprint counts: `{"25548a9429bf4bd396091d24": 1, "4d91c3d0fe2fa1d3bebf04e0": 1, "6034e5dd17ee25c1245534e5": 1, "6f8f07fe7a66bdc7c4d0be58": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `e6a03865c309` | 193.24 | 16 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 325430 | `p3:1-2-2-19;p5:1-1-2-20;p7:1-2-4-4-6-7` |
| 2 | `8fc8dbbbfc9b` | 193.11 | 16 | `medium_mixed_support_gcd1` | `medium_mixed_support_gcd1` | 399168 | `p5:8-16` |
| 3 | `a59933013ae1` | 191.61 | 16 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 3993600 | `p7:2-3-19` |
| 4 | `ad0ef274532e` | 191.34 | 16 | `dense_mixed_support_gcd1` | `dense_mixed_support_gcd1` | 5990400 | `p2:1-2-21;p3:1-2-4-8-9;p5:1-1-1-4-6-11;p7:1-1-2-3-6-11` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `e6a03865c309` | 193.24 | True | `strong_packet_candidate` | `` |
| 2 | `8fc8dbbbfc9b` | 193.11 | True | `strong_packet_candidate` | `` |
| 3 | `a59933013ae1` | 191.61 | True | `strong_packet_candidate` | `` |
| 4 | `ad0ef274532e` | 191.34 | True | `strong_packet_candidate` | `` |
| 5 | `d3a531fdfa1f` | 178.04 | True | `strong_packet_candidate` | `` |
| 6 | `7751ea339de9` | -42.30 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 7 | `13094bd39221` | -46.76 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 8 | `c9e9a9399712` | -46.95 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 9 | `e7657687d139` | -46.96 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 10 | `dbce4e2bc909` | -47.10 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 11 | `b2b4087281e1` | -47.16 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 12 | `f4ac64303241` | -47.42 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 13 | `338645796e79` | -48.66 | False | `reject_or_hold_known_basin_risk` | `accepted_hash_duplicate;crowded_mod_p_signature_hits=1` |
| 14 | `02c2e8db2cf7` | -82.11 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |
| 15 | `688dd64fec0d` | -82.95 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
