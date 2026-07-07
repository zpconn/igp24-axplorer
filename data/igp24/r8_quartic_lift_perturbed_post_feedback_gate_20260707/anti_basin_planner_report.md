# IGP24 Anti-Basin Planner

This report ranks local candidates before any live submission. It uses local metadata, accepted SAIR feedback, and live/loaded SAIR progress, but it claims no exact `24Tt` labels.

## Inputs

- Candidates scored: 51
- Eligible candidates: 0
- Selected rows: 0
- Progress labels: 25000
- Avoid labels: `["24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T25000"]`
- Crowded labels: `["24T1310", "24T22770", "24T23883", "24T24651", "24T24932", "24T24970", "24T24979", "24T24984", "24T25000", "24T657", "24T661", "24T9993"]`

## Recommendation

- Status: `hold_no_submission`
- Recommended for packet: `False`
- Reason: only_0_eligible_rows_below_min_8; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity
- Mode counts: `{}`
- Mod-p signature counts: `{}`

## Selected Rows

| rank | hash | score | r | mode | pattern | height | mod-p |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |

## Top Scored Rows

| rank | hash | score | eligible | classification | risks |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `d01174705ffc` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 2 | `31afd8c19b58` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 3 | `0ebfe6fbce5c` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 4 | `0ebfe6fbce5c` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 5 | `a7b02ae4c651` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 6 | `31afd8c19b58` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 7 | `d01174705ffc` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 8 | `31afd8c19b58` | -56.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;loose_crowded_basin_fingerprint_hits=4` |
| 9 | `590490ef8f26` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=2;crowded_mod_p_signature_hits=2` |
| 10 | `229d930de156` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=1;crowded_mod_p_signature_hits=1` |
| 11 | `02c74285df40` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=1;crowded_mod_p_signature_hits=1` |
| 12 | `57287a606711` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=1;crowded_mod_p_signature_hits=1` |
| 13 | `7f9f4cecfad5` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=1;crowded_mod_p_signature_hits=1` |
| 14 | `08468c499fed` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=2;crowded_mod_p_signature_hits=2` |
| 15 | `08468c499fed` | -146.22 | False | `reject_or_hold_known_basin_risk` | `r8_quartic_in_x6_known_label_collapse=24T24979,24T25000;exact_crowded_basin_fingerprint_hits=2;crowded_mod_p_signature_hits=2` |

Next decision: Do not submit this packet; refine generation toward more perturbation-mode and mod-p diversity.
