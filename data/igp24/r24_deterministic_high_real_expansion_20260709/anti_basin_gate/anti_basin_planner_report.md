# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 24
- Eligible candidates: 24
- Selected rows: 11
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Local packet ready: `True`
- Reason: anti-basin gates passed
- Sync gate: `{"degraded_mode_summary": "23/23 details recovered; 23/23 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [24], "submission_detail_complete": true}`
- Mode counts: `{"single_low_odd_break": 3, "three_low_odd_break": 4, "two_low_odd_break": 4}`
- Mod-p signature counts: `{"none": 5, "p2:1-2-4-17;p3:1-2-5-8-8;p5:1-2-4-17;p7:1-2-3-8-10": 1, "p2:1-23;p3:1-23;p5:1-3-3-4-6-7;p7:1-23": 1, "p2:1-3-5-15;p3:1-4-19;p5:1-3-20;p7:1-3-20": 1, "p2:1-4-9-10;p5:1-23": 1, "p3:1-4-4-7-8;p5:1-2-2-2-4-5-8;p7:1-5-6-12": 1, "p3:1-4-4-7-8;p5:1-2-2-3-3-4-9;p7:1-4-5-14": 1}`
- Template family counts: `{"r24_high_real:single_low_odd_break": 3, "r24_high_real:three_low_odd_break": 4, "r24_high_real:two_low_odd_break": 4}`
- Basin fingerprint counts: `{"single_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=5": 1, "single_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=7": 1, "single_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=9": 1, "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=1,3,7": 1, "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=1,5,9": 1, "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,13|odd=1,3,5": 1, "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,13|odd=1,5,9": 1, "two_low_odd_break|roots=1,2,3,4,5,6,7,8,10,11,12,13|odd=1,5": 1, "two_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=3,7": 1, "two_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,13|odd=1,5": 1, "two_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,13|odd=3,7": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `e2a187758d37` | 201.82 | 24 | `three_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `p2:1-23;p3:1-23;p5:1-3-3-4-6-7;p7:1-23` |
| 2 | `63b9f340d15f` | 201.82 | 24 | `three_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `p2:1-2-4-17;p3:1-2-5-8-8;p5:1-2-4-17;p7:1-2-3-8-10` |
| 3 | `b51dc9fc89b4` | 201.77 | 24 | `two_low_odd_break` | `near_composed_quadratic_product_d2` | 2082477528 | `p3:1-4-4-7-8;p5:1-2-2-2-4-5-8;p7:1-5-6-12` |
| 4 | `25bd60ebd9dd` | 201.77 | 24 | `three_low_odd_break` | `near_composed_quadratic_product_d2` | 2082477528 | `p2:1-3-5-15;p3:1-4-19;p5:1-3-20;p7:1-3-20` |
| 5 | `09a8f62da068` | 201.77 | 24 | `three_low_odd_break` | `near_composed_quadratic_product_d2` | 2082477528 | `p2:1-4-9-10;p5:1-23` |
| 6 | `cea3bd6380d3` | 201.59 | 24 | `two_low_odd_break` | `near_composed_quadratic_product_d2` | 2719254144 | `p3:1-4-4-7-8;p5:1-2-2-3-3-4-9;p7:1-4-5-14` |
| 7 | `f8a1432c8316` | 186.82 | 24 | `single_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `None` |
| 8 | `f58cb6f78afb` | 186.82 | 24 | `single_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `None` |
| 9 | `f2d99f5e2de5` | 186.82 | 24 | `single_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `None` |
| 10 | `b4d8d742bb83` | 186.82 | 24 | `two_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `None` |
| 11 | `160f5c3f63b7` | 186.77 | 24 | `two_low_odd_break` | `near_composed_quadratic_product_d2` | 2082477528 | `None` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `e2a187758d37` | 201.82 | True | `strong_packet_candidate` | `` |
| 2 | `63b9f340d15f` | 201.82 | True | `strong_packet_candidate` | `` |
| 3 | `25bd60ebd9dd` | 201.77 | True | `strong_packet_candidate` | `` |
| 4 | `b51dc9fc89b4` | 201.77 | True | `strong_packet_candidate` | `` |
| 5 | `09a8f62da068` | 201.77 | True | `strong_packet_candidate` | `` |
| 6 | `47388e854930` | 201.71 | True | `strong_packet_candidate` | `` |
| 7 | `edaa7062f581` | 201.71 | True | `strong_packet_candidate` | `` |
| 8 | `cbf1b76f204b` | 201.71 | True | `strong_packet_candidate` | `` |
| 9 | `25f15d313de0` | 201.66 | True | `strong_packet_candidate` | `` |
| 10 | `cea3bd6380d3` | 201.59 | True | `strong_packet_candidate` | `` |
| 11 | `ae35388af803` | 186.82 | True | `strong_packet_candidate` | `` |
| 12 | `b4d8d742bb83` | 186.82 | True | `strong_packet_candidate` | `` |
| 13 | `36843df231d8` | 186.82 | True | `strong_packet_candidate` | `` |
| 14 | `f8a1432c8316` | 186.82 | True | `strong_packet_candidate` | `` |
| 15 | `44c1c658d534` | 186.82 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
