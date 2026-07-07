# IGP24 R12 Tower Candidate Queue

CPU-only local r12 degree-6-by-degree-4 exact-composed tower probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 240
- Valid r=12 candidates: 118
- Selected rows: 10
- Queue status: `manual_queue_ready`
- Selected mode counts: `{"outer_constant_shift": 9, "outer_two_coefficient_shift": 1}`
- Selected inner-s counts: `{"4": 2, "5": 2, "6": 2, "7": 2, "8": 2}`
- Rejected counts: `{"real_root_count_mismatch": 62, "reducible_over_q": 60}`

| rank | hash | mode | s | four-real levels | no-real levels | outer perturbations | height | log disc |
| ---: | --- | --- | ---: | --- | --- | --- | ---: | ---: |
| 1 | `fceab6f1bb24` | `outer_constant_shift` | 4 | `-1,-2,-3` | `-5,-6,-8` | `0:-3` | 120884 | 168.558 |
| 2 | `4386edc001eb` | `outer_constant_shift` | 5 | `-1,-2,-3` | `-7,-8,-9` | `0:-2` | 365519 | 191.030 |
| 3 | `55312e7f3ef8` | `outer_constant_shift` | 6 | `-1,-2,-3` | `-10,-11,-13` | `0:-5` | 1231669 | 237.833 |
| 4 | `ec129a4a3309` | `outer_constant_shift` | 7 | `-1,-2,-4` | `-13,-14,-15` | `0:-1` | 3269504 | 255.700 |
| 5 | `73ad1314f2a1` | `outer_constant_shift` | 8 | `-1,-2,-3` | `-17,-18,-19` | `0:-1` | 7745345 | 273.666 |
| 6 | `f390d55c6ec1` | `outer_constant_shift` | 4 | `-1,-2,-3` | `-5,-6,-9` | `0:3` | 130679 | 179.274 |
| 7 | `3a74dd44b9ab` | `outer_two_coefficient_shift` | 5 | `-1,-2,-3` | `-7,-8,-10` | `0:2,4:-1` | 390301 | 229.532 |
| 8 | `a80b6e64f3c0` | `outer_constant_shift` | 6 | `-1,-2,-3` | `-10,-11,-14` | `0:-2` | 1294234 | 246.041 |
| 9 | `099239e97867` | `outer_constant_shift` | 7 | `-1,-2,-3` | `-13,-14,-17` | `0:-2` | 3317405 | 268.144 |
| 10 | `7b778019941c` | `outer_constant_shift` | 8 | `-1,-2,-3` | `-17,-18,-22` | `0:-5` | 8559386 | 297.522 |

Caveat: these rows have local exact `r=12`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r12_tower_probe_20260706/r12_tower_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r12_tower_probe_20260706/r12_tower_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r12_tower_probe_20260706/r12_tower_candidate_hashes.txt`
- Summary JSON: `data/igp24/r12_tower_probe_20260706/r12_tower_summary.json`
