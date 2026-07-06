# IGP24 R24 High-Real-Root Candidate Queue

CPU-only local r24 high-real-root probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 120
- Valid r=24 candidates: 113
- Selected rows: 8
- Queue status: `manual_queue_ready`
- Mode counts: `{"single_low_odd_break": 3, "three_low_odd_break": 2, "two_low_odd_break": 3}`
- Rejected counts: `{"reducible_over_q": 7}`

| rank | hash | mode | roots | odd perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `796638a11606` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `9:-2` | 1931559552 | 361.783 | 0.000 |
| 2 | `c0df7a883c80` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `1:1,5:1` | 1931559552 | 362.895 | 0.000 |
| 3 | `0d83f03eb475` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `1:1,3:-1,5:1` | 1931559552 | 362.895 | 0.000 |
| 4 | `da0b4b43c0e0` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `7:1` | 1931559552 | 362.891 | 0.000 |
| 5 | `b8258363b2f7` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,12,13` | `3:1,7:1` | 2258902656 | 379.819 | 0.000 |
| 6 | `4aed8c4ead77` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,13` | `1:-1,3:1,7:1` | 2082477528 | 372.912 | 0.000 |
| 7 | `c05602fc0f8c` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `5:-2` | 1931559552 | 362.895 | 0.000 |
| 8 | `f5c5a7728207` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,12,13` | `1:1,5:1` | 2258902656 | 379.820 | 0.000 |

Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r24_high_real_probe_20260706/r24_high_real_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r24_high_real_probe_20260706/r24_high_real_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r24_high_real_probe_20260706/r24_high_real_candidate_hashes.txt`
- Summary JSON: `data/igp24/r24_high_real_probe_20260706/r24_high_real_summary.json`
