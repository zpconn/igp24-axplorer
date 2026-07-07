# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 24
- Eligible candidates: 24
- Selected rows: 12
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Reason: anti-basin gates passed
- Mode counts: `{"outer_high_coefficient_shift": 4, "outer_mixed_high_shift": 4, "outer_two_coefficient_shift": 4}`
- Mod-p signature counts: `{"none": 3, "p2:1-2-7-14;p3:1-2-5-6-10;p7:1-1-1-3-4-6-8": 1, "p2:1-2-7-14;p3:1-2-5-6-10;p7:3-3-4-4-4-6": 1, "p2:3-21;p7:1-1-1-3-4-6-8": 1, "p2:3-7-7-7;p5:1-1-1-21;p7:2-3-4-6-9": 1, "p3:1-2-7-14;p5:3-3-3-5-10;p7:3-7-7-7": 1, "p3:3-3-18;p5:1-1-2-2-18;p7:3-3-18": 1, "p5:3-3-6-12": 1, "p5:3-3-6-12;p7:1-1-2-2-3-3-3-3-6": 1, "p5:3-3-6-12;p7:1-1-2-2-6-12": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `97f22796a8dd` | 206.00 | 24 | `outer_two_coefficient_shift` | `8x3` | 457072308 | `p5:3-3-6-12;p7:1-1-2-2-6-12` |
| 2 | `9c34d70d2fef` | 205.69 | 24 | `outer_two_coefficient_shift` | `8x3` | 729109836 | `p5:3-3-6-12;p7:1-1-2-2-3-3-3-3-6` |
| 3 | `4c1cd86533ba` | 205.69 | 24 | `outer_two_coefficient_shift` | `8x3` | 729109836 | `p5:3-3-6-12` |
| 4 | `d55ec0af1461` | 205.63 | 24 | `outer_two_coefficient_shift` | `8x3` | 797997200 | `p3:3-3-18;p5:1-1-2-2-18;p7:3-3-18` |
| 5 | `593dee11e4f9` | 205.19 | 24 | `outer_high_coefficient_shift` | `8x3` | 1572918424 | `p3:1-2-7-14;p5:3-3-3-5-10;p7:3-7-7-7` |
| 6 | `a1e622b46274` | 191.87 | 24 | `outer_high_coefficient_shift` | `8x3` | 118763800 | `None` |
| 7 | `8305b1f37dcc` | 191.40 | 24 | `outer_high_coefficient_shift` | `8x3` | 244512565 | `None` |
| 8 | `02fbed7470e2` | 190.19 | 24 | `outer_high_coefficient_shift` | `8x3` | 1576145368 | `None` |
| 9 | `e22a83dd688c` | 158.57 | 12 | `outer_mixed_high_shift` | `8x3` | 22780288 | `p2:1-2-7-14;p3:1-2-5-6-10;p7:1-1-1-3-4-6-8` |
| 10 | `69015829bf80` | 158.38 | 12 | `outer_mixed_high_shift` | `8x3` | 30451312 | `p2:1-2-7-14;p3:1-2-5-6-10;p7:3-3-4-4-4-6` |
| 11 | `9e344fee6c9e` | 158.16 | 12 | `outer_mixed_high_shift` | `8x3` | 42409089 | `p2:3-7-7-7;p5:1-1-1-21;p7:2-3-4-6-9` |
| 12 | `62413b1acc6f` | 158.01 | 12 | `outer_mixed_high_shift` | `8x3` | 53808219 | `p2:3-21;p7:1-1-1-3-4-6-8` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `97f22796a8dd` | 206.00 | True | `strong_packet_candidate` | `` |
| 2 | `9c34d70d2fef` | 205.69 | True | `strong_packet_candidate` | `` |
| 3 | `4c1cd86533ba` | 205.69 | True | `strong_packet_candidate` | `` |
| 4 | `0c192dbd5854` | 205.63 | True | `strong_packet_candidate` | `` |
| 5 | `d55ec0af1461` | 205.63 | True | `strong_packet_candidate` | `` |
| 6 | `f86dfbb47603` | 205.31 | True | `strong_packet_candidate` | `` |
| 7 | `bf404229a931` | 205.31 | True | `strong_packet_candidate` | `` |
| 8 | `593dee11e4f9` | 205.19 | True | `strong_packet_candidate` | `` |
| 9 | `a1e622b46274` | 191.87 | True | `strong_packet_candidate` | `` |
| 10 | `8305b1f37dcc` | 191.40 | True | `strong_packet_candidate` | `` |
| 11 | `02fbed7470e2` | 190.19 | True | `strong_packet_candidate` | `` |
| 12 | `e22a83dd688c` | 158.57 | True | `strong_packet_candidate` | `` |
| 13 | `69015829bf80` | 158.38 | True | `strong_packet_candidate` | `` |
| 14 | `9e344fee6c9e` | 158.16 | True | `strong_packet_candidate` | `` |
| 15 | `62413b1acc6f` | 158.01 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
