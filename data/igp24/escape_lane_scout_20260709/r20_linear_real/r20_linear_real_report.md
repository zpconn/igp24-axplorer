# IGP24 R20 Linear-Real-Root Candidate Queue

CPU-only local r20 non-composed linear-real-root probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 160
- Valid r=20 candidates: 88
- Selected rows: 10
- Queue status: `review_only_queue_ready`
- Mode counts: `{"single_low_coefficient_break": 5, "three_low_coefficient_break": 5}`
- Rejected counts: `{"known_or_duplicate_hash": 5, "reducible_over_q": 67}`

| rank | hash | mode | no-real quadratics | perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `cc006b8efc66` | `three_low_coefficient_break` | `1,3` | `1:1,3:-1,5:1` | 46641998908512 | 929.343 | 0.000 |
| 2 | `a82cc79e444f` | `single_low_coefficient_break` | `1,2` | `1:-1` | 219616327325952 | 958.981 | 0.000 |
| 3 | `d057941b79e3` | `single_low_coefficient_break` | `1,2` | `1:-1` | 289700167680000 | 953.112 | 0.000 |
| 4 | `0f1f3af9778a` | `single_low_coefficient_break` | `1,2` | `1:1` | 289700167680000 | 953.112 | 0.000 |
| 5 | `27546e009d25` | `three_low_coefficient_break` | `1,2` | `1:1,3:-1,5:1` | 289700167680000 | 953.112 | 0.000 |
| 6 | `8e5c728256e3` | `single_low_coefficient_break` | `1,3` | `1:1` | 309958436204928 | 964.663 | 0.000 |
| 7 | `1a7d4a12bdce` | `single_low_coefficient_break` | `1,3` | `1:-1` | 309958436204928 | 964.663 | 0.000 |
| 8 | `7788c1b86f9c` | `three_low_coefficient_break` | `5,6` | `1:1,3:-1,5:1` | 513721819468800 | 946.165 | 0.000 |
| 9 | `5c634392d4f7` | `three_low_coefficient_break` | `1,3` | `1:1,3:-1,5:1` | 521460301824000 | 971.602 | 0.000 |
| 10 | `ab1abe4e0947` | `three_low_coefficient_break` | `3,7` | `1:1,3:-1,5:1` | 2027901173760000 | 982.380 | 0.000 |

Caveat: these rows have local exact `r=20`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/escape_lane_scout_20260709/r20_linear_real/r20_linear_real_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/escape_lane_scout_20260709/r20_linear_real/r20_linear_real_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/escape_lane_scout_20260709/r20_linear_real/r20_linear_real_candidate_hashes.txt`
- Summary JSON: `data/igp24/escape_lane_scout_20260709/r20_linear_real/r20_linear_real_summary.json`
