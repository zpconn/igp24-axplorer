# IGP24 R12 Structured Candidate Queue

CPU-only local r12 exact-composed structured probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 180
- Valid r=12 candidates: 111
- Selected rows: 10
- Queue status: `manual_queue_ready`
- Mode counts: `{"single_base_coefficient_perturbation": 7, "structured_base_coefficient_perturbation": 3}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 39, "real_root_count_mismatch": 21, "reducible_over_q": 9}`

| rank | hash | mode | positive y-roots | negative y-roots | base perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `23ab54762bd5` | `single_base_coefficient_perturbation` | `1,2,3,4,5,6` | `1,2,3,4,5,6` | `8:5` | 773136 | 380.907 | 0.000 |
| 2 | `ce09a0129584` | `structured_base_coefficient_perturbation` | `1,2,3,4,5,6` | `1,2,3,4,5,7` | `1:1,4:-1,7:1` | 899592 | 393.160 | 0.000 |
| 3 | `694d5370d953` | `single_base_coefficient_perturbation` | `1,2,3,4,5,6` | `1,2,3,4,5,6` | `5:5` | 773136 | 383.381 | 0.000 |
| 4 | `c1ce7abab479` | `structured_base_coefficient_perturbation` | `1,2,3,4,5,7` | `1,2,3,4,5,6` | `1:2,5:-1` | 899592 | 393.178 | 0.000 |
| 5 | `9eff4260b12d` | `single_base_coefficient_perturbation` | `1,2,3,4,5,6` | `1,2,3,4,5,6` | `2:-3` | 773139 | 383.381 | 0.000 |
| 6 | `002c52e1c2c2` | `structured_base_coefficient_perturbation` | `1,3,4,5,7,8` | `1,2,3,4,6,7` | `1:1,4:-1,7:1` | 4410912 | 439.739 | 0.000 |
| 7 | `5927a1af8dd6` | `single_base_coefficient_perturbation` | `1,2,3,4,5,6` | `1,2,3,4,5,7` | `4:-5` | 899592 | 393.178 | 0.000 |
| 8 | `e8f187d5e7f2` | `single_base_coefficient_perturbation` | `1,2,3,4,5,7` | `1,2,3,4,5,6` | `3:-2` | 899592 | 393.178 | 0.000 |
| 9 | `7bf15e9a1190` | `single_base_coefficient_perturbation` | `1,2,3,4,5,7` | `1,2,3,4,5,6` | `0:3` | 899592 | 393.178 | 0.000 |
| 10 | `4ba559ad7f24` | `single_base_coefficient_perturbation` | `1,2,3,4,5,6` | `1,2,3,4,5,7` | `1:-2` | 899592 | 393.178 | 0.000 |

Caveat: these rows have local exact `r=12`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r12_structured_probe_20260706/r12_structured_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r12_structured_probe_20260706/r12_structured_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r12_structured_probe_20260706/r12_structured_candidate_hashes.txt`
- Summary JSON: `data/igp24/r12_structured_probe_20260706/r12_structured_summary.json`
