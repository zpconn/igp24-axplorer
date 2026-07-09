# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 8
- Eligible candidates: 8
- Selected rows: 4
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `True`
- Reason: locally_ready_but_blocked_by_incomplete_sair_state
- Sync gate: `{"degraded_mode_summary": "20/23 details recovered; 20/20 downloads recovered", "download_complete": false, "full_submission_state_complete": false, "hold_reasons": ["locally_ready_but_blocked_by_incomplete_sair_state"], "partial_sync": true, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=16": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [24], "submission_detail_complete": false}`
- Mode counts: `{"single_low_odd_break": 1, "three_low_odd_break": 2, "two_low_odd_break": 1}`
- Mod-p signature counts: `{"p2:1-2-4-17;p3:1-2-5-8-8;p5:1-2-4-17;p7:1-2-3-8-10": 1, "p2:1-4-9-10;p5:1-3-20;p7:1-2-2-4-4-5-6": 1, "p3:1-4-19;p5:1-2-2-19;p7:1-2-5-16": 1, "p3:1-4-4-7-8;p5:1-2-2-2-4-5-8;p7:1-5-6-12": 1}`
- Template family counts: `{"r24_high_real:single_low_odd_break": 1, "r24_high_real:three_low_odd_break": 2, "r24_high_real:two_low_odd_break": 1}`
- Basin fingerprint counts: `{"single_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=1": 1, "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,12|odd=1,3,7": 1, "three_low_odd_break|roots=1,2,3,4,5,6,7,8,9,11,12,13|odd=1,3,5": 1, "two_low_odd_break|roots=1,2,3,4,5,6,7,8,9,10,11,13|odd=1,5": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `c5dc17f68854` | 203.77 | 24 | `single_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `p3:1-4-19;p5:1-2-2-19;p7:1-2-5-16` |
| 2 | `63b9f340d15f` | 203.77 | 24 | `three_low_odd_break` | `near_composed_quadratic_product_d2` | 1931559552 | `p2:1-2-4-17;p3:1-2-5-8-8;p5:1-2-4-17;p7:1-2-3-8-10` |
| 3 | `b51dc9fc89b4` | 203.72 | 24 | `two_low_odd_break` | `near_composed_quadratic_product_d2` | 2082477528 | `p3:1-4-4-7-8;p5:1-2-2-2-4-5-8;p7:1-5-6-12` |
| 4 | `8727263019b9` | 203.61 | 24 | `three_low_odd_break` | `near_composed_quadratic_product_d2` | 2467871136 | `p2:1-4-9-10;p5:1-3-20;p7:1-2-2-4-4-5-6` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `63b9f340d15f` | 203.77 | True | `strong_packet_candidate` | `` |
| 2 | `c5dc17f68854` | 203.77 | True | `strong_packet_candidate` | `` |
| 3 | `b51dc9fc89b4` | 203.72 | True | `strong_packet_candidate` | `` |
| 4 | `8727263019b9` | 203.61 | True | `strong_packet_candidate` | `` |
| 5 | `36843df231d8` | 188.77 | True | `strong_packet_candidate` | `` |
| 6 | `b4d8d742bb83` | 188.77 | True | `strong_packet_candidate` | `` |
| 7 | `81536275b446` | 188.77 | True | `strong_packet_candidate` | `` |
| 8 | `b74324d92baa` | 188.48 | True | `strong_packet_candidate` | `` |

Next decision: Do not submit this packet; local packet is ready, but wait for complete SAIR state and pending rows to resolve.
