# IGP24 R20 High-Real-Root Candidate Queue

CPU-only local r20 high-real-root probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 160
- Valid r=20 candidates: 95
- Selected rows: 10
- Queue status: `manual_queue_ready`
- Mode counts: `{"single_low_odd_break": 3, "three_low_odd_break": 4, "two_low_odd_break": 3}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 50, "reducible_over_q": 15}`

| rank | hash | mode | positive roots | negative roots | odd perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `47f1cf331e34` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10` | `1,2` | `3:1,7:-1,11:1` | 10813088 | 374.969 | 0.000 |
| 2 | `73c1fa372bc1` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10` | `1,2` | `9:2` | 10813088 | 375.420 | 0.000 |
| 3 | `426f4be4aca5` | `two_low_odd_break` | `1,2,3,4,5,6,7,9,10,11` | `1,2` | `3:1,7:1` | 14683640 | 397.132 | 0.000 |
| 4 | `e9ca5d4d1887` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,11` | `1,2` | `3:1,7:-1,11:1` | 11857252 | 385.171 | 0.000 |
| 5 | `5768787e4663` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,11` | `1,2` | `5:2` | 11857252 | 385.438 | 0.000 |
| 6 | `6b00bef14865` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,11` | `1,5` | `3:1,7:1` | 34326000 | 407.108 | 0.000 |
| 7 | `b8b9b30434b6` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,10,11` | `1,2` | `1:-1,3:1,7:1` | 13121856 | 392.289 | 0.000 |
| 8 | `e7b078cbd8c6` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,11` | `1,2` | `3:1` | 11857252 | 385.438 | 0.000 |
| 9 | `0673a8670cb2` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,11` | `2,3` | `1:1,5:1` | 49972896 | 399.517 | 0.000 |
| 10 | `28a5db6ea30c` | `three_low_odd_break` | `1,2,3,4,6,7,8,9,10,11` | `1,2` | `1:-1,3:1,7:1` | 22700672 | 402.889 | 0.000 |

Caveat: these rows have local exact `r=20`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r20_high_real_probe_20260706/r20_high_real_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r20_high_real_probe_20260706/r20_high_real_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r20_high_real_probe_20260706/r20_high_real_candidate_hashes.txt`
- Summary JSON: `data/igp24/r20_high_real_probe_20260706/r20_high_real_summary.json`
