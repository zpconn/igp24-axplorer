# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 51
- Eligible candidates: 51
- Selected rows: 10
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Reason: anti-basin gates passed
- Mode counts: `{"odd_pair_off_core": 4, "odd_single_off_core": 4, "odd_triple_off_core": 2}`
- Mod-p signature counts: `{"p2:10-14;p3:1-6-7-10;p5:9-15;p7:1-8-15": 4, "p2:7-17;p3:1-2-3-18;p5:24;p7:1-2-21": 2, "p3:2-3-3-6-10;p7:1-1-4-4-14": 1, "p3:3-21;p5:5-19;p7:7-8-9": 2, "p3:4-20;p5:1-2-3-18;p7:4-4-5-11": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `edc417a0902e` | 163.78 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p3:3-21;p5:5-19;p7:7-8-9` |
| 2 | `ed23e7fa2284` | 163.78 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p3:4-20;p5:1-2-3-18;p7:4-4-5-11` |
| 3 | `e690ee562bf8` | 163.78 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p3:2-3-3-6-10;p7:1-1-4-4-14` |
| 4 | `d4579b20d0b4` | 163.78 | 8 | `odd_pair_off_core` | `quartic_in_x6` | 16 | `p3:3-21;p5:5-19;p7:7-8-9` |
| 5 | `7976852a75db` | 163.78 | 8 | `odd_triple_off_core` | `quartic_in_x6` | 16 | `p2:7-17;p3:1-2-3-18;p5:24;p7:1-2-21` |
| 6 | `691f389c1687` | 163.78 | 8 | `odd_single_off_core` | `quartic_in_x6` | 16 | `p2:10-14;p3:1-6-7-10;p5:9-15;p7:1-8-15` |
| 7 | `66aa96ecaf0b` | 163.78 | 8 | `odd_single_off_core` | `quartic_in_x6` | 16 | `p2:10-14;p3:1-6-7-10;p5:9-15;p7:1-8-15` |
| 8 | `1979ec29b95b` | 163.78 | 8 | `odd_single_off_core` | `quartic_in_x6` | 16 | `p2:10-14;p3:1-6-7-10;p5:9-15;p7:1-8-15` |
| 9 | `194f4cf0780c` | 163.78 | 8 | `odd_triple_off_core` | `quartic_in_x6` | 16 | `p2:7-17;p3:1-2-3-18;p5:24;p7:1-2-21` |
| 10 | `1018c4047258` | 163.78 | 8 | `odd_single_off_core` | `quartic_in_x6` | 16 | `p2:10-14;p3:1-6-7-10;p5:9-15;p7:1-8-15` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `590490ef8f26` | 163.78 | True | `strong_packet_candidate` | `` |
| 2 | `d01174705ffc` | 163.78 | True | `strong_packet_candidate` | `` |
| 3 | `31afd8c19b58` | 163.78 | True | `strong_packet_candidate` | `` |
| 4 | `66aa96ecaf0b` | 163.78 | True | `strong_packet_candidate` | `` |
| 5 | `229d930de156` | 163.78 | True | `strong_packet_candidate` | `` |
| 6 | `691f389c1687` | 163.78 | True | `strong_packet_candidate` | `` |
| 7 | `1018c4047258` | 163.78 | True | `strong_packet_candidate` | `` |
| 8 | `e690ee562bf8` | 163.78 | True | `strong_packet_candidate` | `` |
| 9 | `02c74285df40` | 163.78 | True | `strong_packet_candidate` | `` |
| 10 | `1979ec29b95b` | 163.78 | True | `strong_packet_candidate` | `` |
| 11 | `57287a606711` | 163.78 | True | `strong_packet_candidate` | `` |
| 12 | `7f9f4cecfad5` | 163.78 | True | `strong_packet_candidate` | `` |
| 13 | `08468c499fed` | 163.78 | True | `strong_packet_candidate` | `` |
| 14 | `0ebfe6fbce5c` | 163.78 | True | `strong_packet_candidate` | `` |
| 15 | `66aa96ecaf0b` | 163.78 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
