# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 32
- Eligible candidates: 32
- Selected rows: 4
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Local packet ready: `True`
- Reason: anti-basin gates passed
- Sync gate: `{"degraded_mode_summary": "21/21 details recovered; 21/21 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [8], "submission_detail_complete": true}`
- Mode counts: `{"odd_pair_off_core": 4}`
- Mod-p signature counts: `{"p2:2-4-18;p3:3-4-17;p5:24;p7:3-5-16": 1, "p2:3-4-17;p3:11-13;p5:1-1-9-13;p7:1-2-7-14": 1, "p2:4-5-15;p3:10-14;p5:4-20;p7:1-2-8-13": 1, "p2:7-17;p3:11-13;p5:1-1-3-9-10;p7:1-2-5-8-8": 1}`
- Template family counts: `{"r8_score_followup:four_positive_fibers_e:odd_pair_off_core": 3, "r8_score_followup:four_positive_fibers_f:odd_pair_off_core": 1}`
- Basin fingerprint counts: `{"21c013281e9b30402d91f1b5": 1, "2a6951bcf67e969d4c75ca90": 1, "2f549efd5a79b1ba5cf422ef": 1, "836c81d12ffe0df2b8d42188": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `fab80a856ba7` | 160.16 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p2:2-4-18;p3:3-4-17;p5:24;p7:3-5-16` |
| 2 | `fa9b5c0d83b8` | 160.16 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p2:4-5-15;p3:10-14;p5:4-20;p7:1-2-8-13` |
| 3 | `ee2a23e49c9f` | 160.16 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p2:7-17;p3:11-13;p5:1-1-3-9-10;p7:1-2-5-8-8` |
| 4 | `ed07d10ea581` | 160.16 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p2:3-4-17;p3:11-13;p5:1-1-9-13;p7:1-2-7-14` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `cd27f9717863` | 160.16 | True | `strong_packet_candidate` | `` |
| 2 | `1c4996d77f02` | 160.16 | True | `strong_packet_candidate` | `` |
| 3 | `a19647074c42` | 160.16 | True | `strong_packet_candidate` | `` |
| 4 | `e759bfefc8f9` | 160.16 | True | `strong_packet_candidate` | `` |
| 5 | `9808f4cd5c1d` | 160.16 | True | `strong_packet_candidate` | `` |
| 6 | `d5da92d3b266` | 160.16 | True | `strong_packet_candidate` | `` |
| 7 | `fab80a856ba7` | 160.16 | True | `strong_packet_candidate` | `` |
| 8 | `124b074d5d0a` | 160.16 | True | `strong_packet_candidate` | `` |
| 9 | `1075804323d7` | 160.16 | True | `strong_packet_candidate` | `` |
| 10 | `ee2a23e49c9f` | 160.16 | True | `strong_packet_candidate` | `` |
| 11 | `ab973c891eab` | 160.16 | True | `strong_packet_candidate` | `` |
| 12 | `b5d16068d82a` | 160.16 | True | `strong_packet_candidate` | `` |
| 13 | `568f33801e1f` | 160.16 | True | `strong_packet_candidate` | `` |
| 14 | `35f554f5eed0` | 160.16 | True | `strong_packet_candidate` | `` |
| 15 | `a037cdd189f0` | 160.16 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
