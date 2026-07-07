# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 8
- Eligible candidates: 8
- Selected rows: 8
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Reason: anti-basin gates passed
- Mode counts: `{"single_low_coefficient_break": 4, "three_low_coefficient_break": 4}`
- Mod-p signature counts: `{"p2:1-11-12;p3:1-2-5-16;p5:1-5-5-13;p7:1-2-21": 1, "p2:1-2-3-18;p3:1-2-3-5-13;p5:1-2-10-11;p7:1-4-5-14": 1, "p2:1-2-3-18;p3:1-3-9-11;p5:1-3-20;p7:1-23": 1, "p2:1-2-3-18;p3:1-4-8-11;p5:1-9-14;p7:1-2-3-6-12": 1, "p2:1-3-10-10;p3:1-2-3-4-14;p5:1-8-15;p7:1-2-21": 1, "p2:1-4-9-10;p3:1-2-10-11;p5:1-2-3-7-11;p7:1-6-17": 1, "p2:1-4-9-10;p3:1-2-2-9-10;p5:1-2-3-7-11;p7:1-5-18": 1, "p2:1-6-7-10;p3:1-5-9-9;p5:1-6-17;p7:1-3-3-5-12": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `296916ec799e` | 158.79 | 20 | `single_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 33744739940928 | `p2:1-2-3-18;p3:1-4-8-11;p5:1-9-14;p7:1-2-3-6-12` |
| 2 | `1fc392ea555b` | 158.58 | 20 | `single_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 46641998908512 | `p2:1-6-7-10;p3:1-5-9-9;p5:1-6-17;p7:1-3-3-5-12` |
| 3 | `bc3044f2ac34` | 157.84 | 20 | `single_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 144850083840000 | `p2:1-2-3-18;p3:1-2-3-5-13;p5:1-2-10-11;p7:1-4-5-14` |
| 4 | `a43fce9992ec` | 157.84 | 20 | `single_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 144850083840000 | `p2:1-2-3-18;p3:1-3-9-11;p5:1-3-20;p7:1-23` |
| 5 | `3653b5643295` | 157.57 | 20 | `three_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 219616327325952 | `p2:1-3-10-10;p3:1-2-3-4-14;p5:1-8-15;p7:1-2-21` |
| 6 | `100b55bd5c96` | 157.34 | 20 | `three_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 309958436204928 | `p2:1-4-9-10;p3:1-2-10-11;p5:1-2-3-7-11;p7:1-6-17` |
| 7 | `ef671faed209` | 157.31 | 20 | `three_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 326289754344960 | `p2:1-11-12;p3:1-2-5-16;p5:1-5-5-13;p7:1-2-21` |
| 8 | `1e1c2b9b4460` | 157.12 | 20 | `three_low_coefficient_break` | `20x1_plus_2x2_noncomposed` | 434550251520000 | `p2:1-4-9-10;p3:1-2-2-9-10;p5:1-2-3-7-11;p7:1-5-18` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `296916ec799e` | 158.79 | True | `strong_packet_candidate` | `` |
| 2 | `1fc392ea555b` | 158.58 | True | `strong_packet_candidate` | `` |
| 3 | `a43fce9992ec` | 157.84 | True | `strong_packet_candidate` | `` |
| 4 | `bc3044f2ac34` | 157.84 | True | `strong_packet_candidate` | `` |
| 5 | `3653b5643295` | 157.57 | True | `strong_packet_candidate` | `` |
| 6 | `100b55bd5c96` | 157.34 | True | `strong_packet_candidate` | `` |
| 7 | `ef671faed209` | 157.31 | True | `strong_packet_candidate` | `` |
| 8 | `1e1c2b9b4460` | 157.12 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
