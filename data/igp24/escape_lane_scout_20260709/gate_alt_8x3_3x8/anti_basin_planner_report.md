# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 3
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Local packet ready: `False`
- Reason: only_0_eligible_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Sync gate: `{"degraded_mode_summary": "24/24 details recovered; 24/24 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
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
| 1 | `886f7c30a5ad` | 3.08 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T24932;loose_crowded_basin_fingerprint_hits=8` |
| 2 | `bf404229a931` | 1.98 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T24932;loose_crowded_basin_fingerprint_hits=8` |
| 3 | `0c192dbd5854` | -87.69 | False | `reject_or_hold_known_basin_risk` | `template_family_known_high_label_collapse=24T24932;exact_crowded_basin_fingerprint_hits=2;crowded_mod_p_signature_hits=2` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
