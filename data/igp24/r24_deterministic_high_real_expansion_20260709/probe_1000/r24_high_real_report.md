# IGP24 R24 High-Real-Root Candidate Queue

CPU-only local r24 high-real-root probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 252
- Valid r=24 candidates: 217
- Selected rows: 24
- Queue status: `manual_queue_ready`
- Mode counts: `{"single_low_odd_break": 8, "three_low_odd_break": 8, "two_low_odd_break": 8}`
- Rejected counts: `{"known_or_duplicate_hash": 8, "reducible_over_q": 27}`

| rank | hash | mode | roots | odd perturbations | height | log disc | score |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `ae35388af803` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `9:2` | 1931559552 | 361.783 | 0.000 |
| 2 | `e2a187758d37` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `1:1,5:-1,9:1` | 1931559552 | 362.656 | 0.000 |
| 3 | `b4d8d742bb83` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `3:1,7:1` | 1931559552 | 362.891 | 0.000 |
| 4 | `36843df231d8` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `9:1` | 1931559552 | 362.648 | 0.000 |
| 5 | `63b9f340d15f` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `1:-1,3:1,7:1` | 1931559552 | 362.891 | 0.000 |
| 6 | `160f5c3f63b7` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,13` | `3:1,7:1` | 2082477528 | 372.912 | 0.000 |
| 7 | `f8a1432c8316` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `9:-1` | 1931559552 | 362.648 | 0.000 |
| 8 | `25bd60ebd9dd` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,13` | `1:1,5:-1,9:1` | 2082477528 | 372.769 | 0.000 |
| 9 | `b51dc9fc89b4` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,13` | `1:1,5:1` | 2082477528 | 372.914 | 0.000 |
| 10 | `44c1c658d534` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `7:-2` | 1931559552 | 362.879 | 0.000 |
| 11 | `09a8f62da068` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,13` | `1:1,3:-1,5:1` | 2082477528 | 372.914 | 0.000 |
| 12 | `e3cc168c8fdf` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,11,12,13` | `3:1,7:1` | 2467871136 | 384.731 | 0.000 |
| 13 | `6754548c688a` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `7:2` | 1931559552 | 362.879 | 0.000 |
| 14 | `47388e854930` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,12,13` | `1:1,5:-1,9:1` | 2258902656 | 379.742 | 0.000 |
| 15 | `28116793e051` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,9,11,12,13` | `1:1,5:1` | 2467871136 | 384.732 | 0.000 |
| 16 | `f58cb6f78afb` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `7:-1` | 1931559552 | 362.891 | 0.000 |
| 17 | `edaa7062f581` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,12,13` | `1:-1,3:1,7:1` | 2258902656 | 379.819 | 0.000 |
| 18 | `4808b3e10a00` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,10,11,12,13` | `3:1,7:1` | 2719254144 | 388.080 | 0.000 |
| 19 | `f2d99f5e2de5` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `5:2` | 1931559552 | 362.895 | 0.000 |
| 20 | `cbf1b76f204b` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,12,13` | `1:1,3:-1,5:1` | 2258902656 | 379.820 | 0.000 |
| 21 | `cea3bd6380d3` | `two_low_odd_break` | `1,2,3,4,5,6,7,8,10,11,12,13` | `1:1,5:1` | 2719254144 | 388.081 | 0.000 |
| 22 | `c5f728e584aa` | `single_low_odd_break` | `1,2,3,4,5,6,7,8,9,10,11,12` | `5:-1` | 1931559552 | 362.895 | 0.000 |
| 23 | `25f15d313de0` | `three_low_odd_break` | `1,2,3,4,5,6,7,8,9,11,12,13` | `1:1,5:-1,9:1` | 2467871136 | 384.697 | 0.000 |
| 24 | `b74324d92baa` | `two_low_odd_break` | `1,2,3,4,5,6,7,9,10,11,12,13` | `3:1,7:1` | 3027333672 | 390.078 | 0.000 |

Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r24_deterministic_high_real_expansion_20260709/probe_1000/r24_high_real_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r24_deterministic_high_real_expansion_20260709/probe_1000/r24_high_real_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r24_deterministic_high_real_expansion_20260709/probe_1000/r24_high_real_candidate_hashes.txt`
- Summary JSON: `data/igp24/r24_deterministic_high_real_expansion_20260709/probe_1000/r24_high_real_summary.json`
