# AXG-1.3 Diversity-Aware Target-r Summary

AXG-1.3 increased total target-r survivors from 128 to 172 and total selected rows from 7 to 13, but did not improve submission readiness because source rows still lack meaningful perturbation-mode metadata and r24 eligible rows dropped.

| r | gpu_s | max_util | decoded | scored | valid | target_survivors | eligible | selected | decision | hold reason |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 12 | 164.3 | 91.0 | 108 | 108 | 108 | 51 | 4 | 4 | `hold_no_submission` | selected_rows_do_not_have_multiple_perturbation_modes |
| 16 | 152.0 | 92.0 | 89 | 89 | 85 | 44 | 7 | 4 | `hold_no_submission` | selected_rows_do_not_have_multiple_perturbation_modes |
| 20 | 172.5 | 87.0 | 83 | 83 | 73 | 38 | 27 | 4 | `hold_no_submission` | selected_rows_do_not_have_multiple_perturbation_modes |
| 24 | 157.0 | 91.0 | 91 | 91 | 87 | 39 | 1 | 1 | `hold_no_submission` | only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity |

## Aggregate

`{"max_gpu_utilization_percent": 92.0, "model_generate_target_r_survivor_count": 172, "model_generated_eligible_rows": 39, "proposal_selected_rows": 13, "rejected_records": 18, "runtime_seconds": 645.7669243339333, "sample_export_decoded_records": 371, "sample_export_records": 814, "sample_export_unique_decoded_coefficients": 371, "scored_records": 371, "target_r_survivor_count": 172, "valid_records": 353}`

## SAIR Sync

`{"endpoint_count": null, "label_count": null, "partial_sync": null, "pending_rows": null, "remaining_signature_count": null, "scoreable_rows": null, "submission_count": null, "submission_state_complete": null, "summary_path": "data/igp24/axg13_diversity_20260708/sair_sync/sair_sync_summary.json"}`

No SAIR submission was made. The next useful change is to preserve or infer perturbation-mode/family metadata for model-generated rows before relaxing packet gates.
