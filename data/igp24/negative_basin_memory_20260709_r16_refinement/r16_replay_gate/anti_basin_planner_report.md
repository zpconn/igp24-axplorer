# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 32
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_0_eligible_rows_below_min_4; only_0_model_generated_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity; locally_ready_but_blocked_by_incomplete_sair_state
- Sync gate: `{"degraded_mode_summary": "20/23 details recovered; 20/20 downloads recovered", "download_complete": false, "full_submission_state_complete": false, "hold_reasons": ["locally_ready_but_blocked_by_incomplete_sair_state"], "partial_sync": true, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=16": 4, "24T25000|r=8": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": false}`
- Mode counts: `{}`
- Mod-p signature counts: `{}`
- Template family counts: `{}`
- Basin fingerprint counts: `{}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `7751ea339de9` | -122.46 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 2 | `02c2e8db2cf7` | -162.26 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 3 | `688dd64fec0d` | -163.10 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 4 | `dda9b283ed86` | -165.23 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 5 | `b30939a8dbf3` | -168.40 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 6 | `bb765a645aa4` | -170.56 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 7 | `d1097cefc222` | -173.55 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 8 | `1ebe899c0356` | -177.73 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 9 | `dfdd6bc4ef8f` | -181.43 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 10 | `d3a531fdfa1f` | -182.05 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T25000;model_template_family_known_high_label_collapse=24T25000;loose_crowded_basin_fingerprint_hits=2` |
| 11 | `ab765dd84f46` | -182.11 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 12 | `ae0368792320` | -182.87 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 13 | `6e9a197afc73` | -183.44 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 14 | `c761aea0d514` | -187.19 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |
| 15 | `26dfbbc24d5c` | -190.77 | False | `reject_or_hold_known_basin_risk` | `real_root_count_not_target;loose_crowded_basin_fingerprint_hits=2` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
