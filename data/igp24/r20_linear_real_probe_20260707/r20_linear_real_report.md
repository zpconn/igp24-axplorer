# IGP24 R20 Linear-Real-Root Candidate Queue

CPU-only local r20 non-composed linear-real-root probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 160
- Valid r=20 candidates: 102
- Selected rows: 8
- Queue status: `review_only_queue_ready`
- Mode counts: `{"single_low_coefficient_break": 4, "three_low_coefficient_break": 4}`
- Rejected counts: `{"reducible_over_q": 58}`

| rank | hash | mode | no-real quadratics | perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `296916ec799e` | `single_low_coefficient_break` | `1,2` | `1:1` | 33744739940928 | 923.362 | 0.000 |
| 2 | `1fc392ea555b` | `single_low_coefficient_break` | `1,3` | `1:1` | 46641998908512 | 929.343 | 0.000 |
| 3 | `a43fce9992ec` | `single_low_coefficient_break` | `2,5` | `1:1` | 144850083840000 | 940.165 | 0.000 |
| 4 | `bc3044f2ac34` | `single_low_coefficient_break` | `2,5` | `1:-1` | 144850083840000 | 940.165 | 0.000 |
| 5 | `3653b5643295` | `three_low_coefficient_break` | `1,2` | `1:1,3:-1,5:1` | 219616327325952 | 958.981 | 0.000 |
| 6 | `100b55bd5c96` | `three_low_coefficient_break` | `1,3` | `1:1,3:-1,5:1` | 309958436204928 | 964.663 | 0.000 |
| 7 | `ef671faed209` | `three_low_coefficient_break` | `3,7` | `1:1,3:-1,5:1` | 326289754344960 | 948.582 | 0.000 |
| 8 | `1e1c2b9b4460` | `three_low_coefficient_break` | `1,3` | `1:1,3:-1,5:1` | 434550251520000 | 958.536 | 0.000 |

Caveat: these rows have local exact `r=20`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r20_linear_real_probe_20260707/r20_linear_real_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r20_linear_real_probe_20260707/r20_linear_real_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r20_linear_real_probe_20260707/r20_linear_real_candidate_hashes.txt`
- Summary JSON: `data/igp24/r20_linear_real_probe_20260707/r20_linear_real_summary.json`
