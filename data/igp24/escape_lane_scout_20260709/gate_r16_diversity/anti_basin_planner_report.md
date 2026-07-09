# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 24
- Eligible candidates: 24
- Selected rows: 10
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `reviewed_packet_ready_for_dry_run`
- Recommended for packet: `True`
- Local packet ready: `True`
- Reason: anti-basin gates passed
- Sync gate: `{"degraded_mode_summary": "24/24 details recovered; 24/24 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16], "submission_detail_complete": true}`
- Mode counts: `{"four_odd_perturbed_near_composed": 3, "mixed_even_odd_perturbed": 3, "three_odd_perturbed_near_composed": 4}`
- Mod-p signature counts: `{"p3:1-2-10-11;p5:1-11-12;p7:1-1-2-3-8-9": 1, "p3:1-2-3-4-6-8;p5:1-4-19;p7:7-17": 1, "p3:1-2-4-4-13;p5:1-5-18;p7:1-8-15": 1, "p3:1-23;p5:1-2-3-3-4-11;p7:2-22": 1, "p3:1-23;p5:1-2-3-4-7-7;p7:2-4-4-14": 1, "p3:1-23;p5:1-9-14;p7:1-2-8-13": 1, "p3:1-3-4-16;p5:1-1-3-8-11;p7:1-5-7-11": 1, "p3:1-5-18;p5:1-2-21;p7:1-2-3-4-5-9": 1, "p3:1-5-9-9;p5:1-2-3-3-4-11;p7:1-2-4-8-9": 1, "p3:1-6-17;p5:1-3-6-7-7;p7:1-1-7-15": 1}`
- Template family counts: `{"r16_diversified_root_layout_probe::four_odd_perturbed_near_composed": 3, "r16_diversified_root_layout_probe::mixed_even_odd_perturbed": 3, "r16_diversified_root_layout_probe::three_odd_perturbed_near_composed": 4}`
- Basin fingerprint counts: `{"four_odd_perturbed_near_composed|roots=1,2,3,4,5,6,7,8|quads=2-2,2-3|odd=1,3,5,7|y=": 1, "four_odd_perturbed_near_composed|roots=1,2,3,4,6,8,10,12|quads=2-3,3-3|odd=1,3,5,7|y=": 1, "four_odd_perturbed_near_composed|roots=1,2,3,5,7,9,11,13|quads=2-3,3-3|odd=1,3,5,7|y=": 1, "mixed_even_odd_perturbed|roots=1,2,3,4,5,6,7,8|quads=2-5,4-5|odd=1,5|y=5": 1, "mixed_even_odd_perturbed|roots=1,2,3,4,5,7,8,10|quads=1-2,2-2|odd=1,7|y=2": 1, "mixed_even_odd_perturbed|roots=1,2,3,5,7,9,11,13|quads=1-1,1-2|odd=1,5|y=5": 1, "three_odd_perturbed_near_composed|roots=1,2,3,4,5,6,7,8|quads=2-2,2-3|odd=1,3,7|y=": 1, "three_odd_perturbed_near_composed|roots=1,2,3,4,5,6,8,9|quads=1-1,3-4|odd=1,3,7|y=": 1, "three_odd_perturbed_near_composed|roots=1,2,3,4,5,6,8,9|quads=2-3,3-3|odd=1,5,7|y=": 1, "three_odd_perturbed_near_composed|roots=1,2,3,4,5,7,8,10|quads=1-1,3-4|odd=1,5,7|y=": 1}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `52aceb854f0e` | 191.04 | 16 | `three_odd_perturbed_near_composed` | `` | 207360 | `p3:1-2-3-4-6-8;p5:1-4-19;p7:7-17` |
| 2 | `5d8e5c0048d9` | 190.91 | 16 | `four_odd_perturbed_near_composed` | `` | 254304 | `p3:1-23;p5:1-9-14;p7:1-2-8-13` |
| 3 | `0632ae3f417f` | 190.91 | 16 | `three_odd_perturbed_near_composed` | `` | 254304 | `p3:1-2-4-4-13;p5:1-5-18;p7:1-8-15` |
| 4 | `dda6de4dc0e1` | 190.88 | 16 | `three_odd_perturbed_near_composed` | `` | 268800 | `p3:1-5-18;p5:1-2-21;p7:1-2-3-4-5-9` |
| 5 | `ad05b6acc31f` | 190.78 | 16 | `mixed_even_odd_perturbed` | `` | 309440 | `p3:1-3-4-16;p5:1-1-3-8-11;p7:1-5-7-11` |
| 6 | `eae6516b0ef9` | 190.50 | 16 | `three_odd_perturbed_near_composed` | `` | 475632 | `p3:1-23;p5:1-2-3-4-7-7;p7:2-4-4-14` |
| 7 | `efb96272cc74` | 190.13 | 16 | `mixed_even_odd_perturbed` | `` | 841227 | `p3:1-6-17;p5:1-3-6-7-7;p7:1-1-7-15` |
| 8 | `e8d5eddcdfae` | 189.88 | 16 | `four_odd_perturbed_near_composed` | `` | 1244160 | `p3:1-23;p5:1-2-3-3-4-11;p7:2-22` |
| 9 | `6ee2d4e0ec36` | 189.74 | 16 | `mixed_even_odd_perturbed` | `` | 1530000 | `p3:1-2-10-11;p5:1-11-12;p7:1-1-2-3-8-9` |
| 10 | `1099b1a38538` | 189.44 | 16 | `four_odd_perturbed_near_composed` | `` | 2432430 | `p3:1-5-9-9;p5:1-2-3-3-4-11;p7:1-2-4-8-9` |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `52aceb854f0e` | 191.04 | True | `strong_packet_candidate` | `` |
| 2 | `0632ae3f417f` | 190.91 | True | `strong_packet_candidate` | `` |
| 3 | `5d8e5c0048d9` | 190.91 | True | `strong_packet_candidate` | `` |
| 4 | `dda6de4dc0e1` | 190.88 | True | `strong_packet_candidate` | `` |
| 5 | `ad05b6acc31f` | 190.78 | True | `strong_packet_candidate` | `` |
| 6 | `eae6516b0ef9` | 190.50 | True | `strong_packet_candidate` | `` |
| 7 | `15fde057e976` | 190.35 | True | `strong_packet_candidate` | `` |
| 8 | `efb96272cc74` | 190.13 | True | `strong_packet_candidate` | `` |
| 9 | `6b6bc6581bdf` | 190.09 | True | `strong_packet_candidate` | `` |
| 10 | `e8d5eddcdfae` | 189.88 | True | `strong_packet_candidate` | `` |
| 11 | `6ee2d4e0ec36` | 189.74 | True | `strong_packet_candidate` | `` |
| 12 | `ee95964ca035` | 189.57 | True | `strong_packet_candidate` | `` |
| 13 | `1099b1a38538` | 189.44 | True | `strong_packet_candidate` | `` |
| 14 | `f540e183055e` | 189.44 | True | `strong_packet_candidate` | `` |
| 15 | `d587da6ff2ab` | 189.17 | True | `strong_packet_candidate` | `` |

Next decision: Run SAIR dry-run on the coefficient file, then submit only if the operator accepts the packet.
