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
- Mode counts: `{"outer_balanced_shift": 4, "outer_cubic_mixed_shift": 4, "outer_linear_quadratic_shift": 4}`
- Mod-p signature counts: `{"none": 1, "p3:12-12;p5:3-3-3-3-6-6;p7:4-20": 1, "p3:12-12;p5:8-16;p7:4-8-12": 1, "p3:3-6-6-9;p5:2-3-3-6-10;p7:1-2-3-3-15": 1, "p3:3-6-6-9;p5:3-3-3-6-9;p7:1-2-3-18": 1, "p3:3-6-6-9;p5:6-6-12;p7:1-2-3-3-15": 1, "p3:4-20;p5:2-10-12;p7:2-4-18": 1, "p3:4-20;p5:4-8-12;p7:8-16": 1, "p5:3-3-3-6-9": 1, "p5:3-3-3-6-9;p7:2-2-10-10": 1, "p7:4-20": 1, "p7:4-4-16": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `252045fc9d7e` | 158.48 | 12 | `outer_balanced_shift` | `4x6` | 25991674 | `p3:3-6-6-9;p5:3-3-3-6-9;p7:1-2-3-18` |
| 2 | `219ae1452d11` | 158.46 | 12 | `outer_balanced_shift` | `4x6` | 26857054 | `p3:3-6-6-9;p5:2-3-3-6-10;p7:1-2-3-3-15` |
| 3 | `9cde07708f31` | 158.42 | 12 | `outer_balanced_shift` | `4x6` | 28602466 | `p3:3-6-6-9;p5:6-6-12;p7:1-2-3-3-15` |
| 4 | `6b604d1a643d` | 158.42 | 12 | `outer_linear_quadratic_shift` | `4x6` | 28602466 | `p5:3-3-3-6-9` |
| 5 | `afe78a8e5b6d` | 158.38 | 12 | `outer_balanced_shift` | `4x6` | 30367414 | `p5:3-3-3-6-9;p7:2-2-10-10` |
| 6 | `27206c06aece` | 158.38 | 12 | `outer_linear_quadratic_shift` | `4x6` | 30367414 | `p7:4-4-16` |
| 7 | `72f1c312c340` | 158.28 | 12 | `outer_cubic_mixed_shift` | `4x6` | 35520801 | `p3:12-12;p5:3-3-3-3-6-6;p7:4-20` |
| 8 | `d0faeac3b9ab` | 158.28 | 12 | `outer_linear_quadratic_shift` | `4x6` | 35779474 | `p7:4-20` |
| 9 | `e29ea76b91d9` | 158.25 | 12 | `outer_cubic_mixed_shift` | `4x6` | 37363893 | `p3:4-20;p5:4-8-12;p7:8-16` |
| 10 | `8dfd4a8cabd1` | 158.22 | 12 | `outer_cubic_mixed_shift` | `4x6` | 39226521 | `p3:4-20;p5:2-10-12;p7:2-4-18` |
| 11 | `943852886c6f` | 158.18 | 12 | `outer_cubic_mixed_shift` | `4x6` | 41108685 | `p3:12-12;p5:8-16;p7:4-8-12` |
| 12 | `a5a6f3bd9305` | 143.48 | 12 | `outer_linear_quadratic_shift` | `4x6` | 25991674 | `None` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `252045fc9d7e` | 158.48 | True | `strong_packet_candidate` | `` |
| 2 | `219ae1452d11` | 158.46 | True | `strong_packet_candidate` | `` |
| 3 | `9cde07708f31` | 158.42 | True | `strong_packet_candidate` | `` |
| 4 | `6b604d1a643d` | 158.42 | True | `strong_packet_candidate` | `` |
| 5 | `afe78a8e5b6d` | 158.38 | True | `strong_packet_candidate` | `` |
| 6 | `27206c06aece` | 158.38 | True | `strong_packet_candidate` | `` |
| 7 | `02ef2d0b869a` | 158.31 | True | `strong_packet_candidate` | `` |
| 8 | `622dea1cd75a` | 158.29 | True | `strong_packet_candidate` | `` |
| 9 | `72f1c312c340` | 158.28 | True | `strong_packet_candidate` | `` |
| 10 | `d0faeac3b9ab` | 158.28 | True | `strong_packet_candidate` | `` |
| 11 | `f3f0392cfaed` | 158.28 | True | `strong_packet_candidate` | `` |
| 12 | `e29ea76b91d9` | 158.25 | True | `strong_packet_candidate` | `` |
| 13 | `275353f15c3d` | 158.24 | True | `strong_packet_candidate` | `` |
| 14 | `8dfd4a8cabd1` | 158.22 | True | `strong_packet_candidate` | `` |
| 15 | `943852886c6f` | 158.18 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
