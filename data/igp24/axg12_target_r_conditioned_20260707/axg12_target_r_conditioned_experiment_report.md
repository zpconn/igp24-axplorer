# AXG-1.2 Target-r Conditioned Summary

Control-token decimal training produced model_generate target-r survivors in every requested bucket; unlike AXG-1.1, target-r survivors did not come from seed-bank prefix rows.

| r | gpu_s | max_util | decoded | scored | valid | target_survivors | real_root_counts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 12 | 80.9 | 92.0 | 85 | 85 | 80 | 47 | `{"0": 1, "10": 6, "12": 47, "2": 1, "4": 9, "6": 10, "8": 6}` |
| 16 | 74.0 | 92.0 | 35 | 35 | 34 | 31 | `{"12": 2, "16": 31, "8": 1}` |
| 20 | 78.1 | 92.0 | 18 | 18 | 15 | 12 | `{"16": 1, "2": 1, "20": 12, "4": 1}` |
| 24 | 75.0 | 94.0 | 74 | 74 | 70 | 38 | `{"0": 2, "10": 4, "12": 5, "16": 1, "2": 4, "20": 1, "24": 38, "4": 9, "6": 2, "8": 4}` |

## Aggregate

`{"max_gpu_utilization_percent": 94.0, "model_generate_target_r_survivor_count": 128, "rejected_records": 13, "runtime_seconds": 308.0497058460023, "sample_export_decoded_records": 212, "sample_export_records": 366, "sample_export_unique_decoded_coefficients": 212, "scored_records": 212, "target_r_survivor_count": 128, "valid_records": 199}`

No SAIR submission was made. Checkpoints and pickle files remain only under `/tmp`.

## Proposal Dry-runs

| r | filtered | selected | decision | risk_reasons |
| ---: | ---: | ---: | --- | --- |
| 12 | 47 | 2 | hold_no_submission | `{"accepted_hash_duplicate": 38, "crowded_mod_p_signature_hits=1": 14, "even_support_g_x_squared_like": 31, "support_gcd_not_one": 31}` |
| 16 | 31 | 1 | hold_no_submission | `{"accepted_hash_duplicate": 29, "even_support_g_x_squared_like": 13, "support_gcd_not_one": 13}` |
| 20 | 12 | 1 | hold_no_submission | `{"accepted_hash_duplicate": 11, "crowded_mod_p_signature_hits=1": 4}` |
| 24 | 38 | 3 | hold_no_submission | `{"accepted_hash_duplicate": 35, "crowded_mod_p_signature_hits=1": 5, "even_support_g_x_squared_like": 9, "support_gcd_not_one": 9}` |

All proposal loops used dry-run mode and made no SAIR submission.
