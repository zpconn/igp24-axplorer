# Anti-Collapse Steering Report

## Latest SAIR State
- Submission: `sub_be2f16728afa4ff2aa03fbec2898d997`
- Poll artifact: `data/igp24/axg14_provenance_20260708/r20/proposal_loop_resynced_gate/axg14_target_r20_provenance_20260708_resynced_gate/sair_status_poll4.json`
- Verified rows: `4`
- Pair counts: `{"24T25000|r=20": 4}`
- Scoring status counts: `{"pending": 4}`
- Scoring reason counts: `{"discriminant_pending": 4}`
- Local planning state: `24T25000|r=20` remains a fresh pending high-risk basin.

## Saturated Local Pairs
| pair | pre-latest sync rows | latest pending rows | local total | scoreable rows |
| --- | ---: | ---: | ---: | ---: |
| `24T25000|r=4` | 23 | 0 | 23 | 23 |
| `24T25000|r=20` | 18 | 4 | 22 | 18 |
| `24T25000|r=16` | 17 | 0 | 17 | 17 |
| `24T24932|r=24` | 16 | 0 | 16 | 16 |
| `24T25000|r=24` | 16 | 0 | 16 | 16 |
| `24T24979|r=12` | 15 | 0 | 15 | 15 |
| `24T24979|r=16` | 13 | 0 | 13 | 13 |
| `24T24984|r=12` | 12 | 0 | 12 | 12 |
| `24T24651|r=24` | 9 | 0 | 9 | 9 |
| `24T25000|r=8` | 9 | 0 | 9 | 9 |
| `24T24651|r=12` | 8 | 0 | 8 | 8 |
| `24T24932|r=12` | 4 | 0 | 4 | 4 |

## Score-Aware Buckets
| r | remaining | discovered % | top pair | priority |
| ---: | ---: | ---: | --- | ---: |
| 24 | 11820 | 52.72 | `24T19906|r=24` | 1275.093 |
| 16 | 10162 | 52.56 | `24T19906|r=16` | 1100.746 |
| 8 | 6313 | 73.2 | `24T19906|r=8` | 984.717 |
| 12 | 6300 | 68.4 | `24T19906|r=12` | 781.289 |
| 20 | 5409 | 50.16 | `24T19906|r=20` | 607.068 |
| 0 | 4103 | 83.48 | `24T19906|r=0` | 562.797 |
| 4 | 3593 | 82.09 | `24T19906|r=4` | 481.178 |
| 6 | 504 | 91.61 | `24T19906|r=6` | 111.336 |

## Replay Outcomes
| run | candidates | filtered | selected | decision | main reason |
| --- | ---: | ---: | ---: | --- | --- |
| `axg13_r12_pending_overlay` | 108 | 51 | 2 | `hold_no_submission` | only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selecte... |
| `axg13_r16_pending_overlay` | 89 | 44 | 2 | `hold_no_submission` | only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selecte... |
| `axg13_r20_pending_overlay` | 83 | 38 | 2 | `hold_no_submission` | only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selecte... |
| `axg13_r24_pending_overlay` | 91 | 39 | 1 | `hold_no_submission` | only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selecte... |
| `axg14_r12_pending_overlay` | 22 | 14 | 1 | `hold_no_submission` | only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; 1_selected_rows_have_risk_reasons; selected_rows_do_not_have_m... |
| `axg14_r16_pending_overlay` | 40 | 22 | 2 | `hold_no_submission` | only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; 2_selected_rows_have_risk_reasons; selected_rows_do_not_have_e... |
| `axg14_r20_pending_overlay` | 35 | 18 | 0 | `hold_no_submission` | only_0_eligible_rows_below_min_4; only_0_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selecte... |
| `axg14_r24_pending_overlay` | 39 | 28 | 1 | `hold_no_submission` | only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; 1_selected_rows_have_risk_reasons; selected_rows_do_not_have_m... |

## Decision
No saved AXG-1.3 or AXG-1.4 replay produced a 4-row, all-model, provenance-diverse packet under the pending-status overlay. Do not live-submit from these saved pools.

Next generator change: run a fresh score-aware r8 score-followup lane around the visible `24T9993|r=8` score signal, or regenerate AXG samples with explicit template/basin diversity and pre-exclusion of high-label `24T25000` basins.

This report is derived from local artifacts only and contains no SAIR API key material.
