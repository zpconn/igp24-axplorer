# IGP24 R24 High-Real-Root Candidate Queue

CPU-only local r24 high-real-root probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 80
- Valid r=24 candidates: 67
- Selected rows: 8
- Queue status: `manual_queue_ready`
- Mode counts: `{"single_low_odd_break": 3, "three_low_odd_break": 2, "two_low_odd_break": 3}`
- Rejected counts: `{"known_or_duplicate_hash": 3, "reducible_over_q": 10}`

| rank | hash | mode | roots | odd perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `36843df231d8` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `9:1` | 1931559552 | 362.648 | 0.000 |
| 2 | `b4d8d742bb83` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `3:1,7:1` | 1931559552 | 362.891 | 0.000 |
| 3 | `63b9f340d15f` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `1:-1,3:1,7:1` | 1931559552 | 362.891 | 0.000 |
| 4 | `81536275b446` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `5:1` | 1931559552 | 362.895 | 0.000 |
| 5 | `b51dc9fc89b4` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,13` | `1:1,5:1` | 2082477528 | 372.914 | 0.000 |
| 6 | `8727263019b9` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,11,12,13` | `1:1,3:-1,5:1` | 2467871136 | 384.732 | 0.000 |
| 7 | `c5dc17f68854` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `1:2` | 1931559552 | 362.895 | 0.000 |
| 8 | `b74324d92baa` | `two_low_odd_break` | `1,2,3,4,5,6,7,9,10,11,12,13` | `3:1,7:1` | 3027333672 | 390.078 | 0.000 |

Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/negative_basin_memory_20260709_r16_refinement/r24_tiny_local_probe/r24_high_real_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/negative_basin_memory_20260709_r16_refinement/r24_tiny_local_probe/r24_high_real_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/negative_basin_memory_20260709_r16_refinement/r24_tiny_local_probe/r24_high_real_candidate_hashes.txt`
- Summary JSON: `data/igp24/negative_basin_memory_20260709_r16_refinement/r24_tiny_local_probe/r24_high_real_summary.json`
