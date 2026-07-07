# IGP24 R24 Tower Candidate Queue

CPU-only local r24 degree-6-by-degree-4 exact-composed tower probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 600
- Valid r=24 candidates: 329
- Selected rows: 10
- Queue status: `api_dry_run_ready`
- Selected mode counts: `{"outer_constant_shift": 10}`
- Selected inner-s counts: `{"10": 1, "11": 1, "12": 1, "6": 2, "7": 2, "8": 2, "9": 1}`
- Rejected counts: `{"real_root_count_mismatch": 117, "reducible_over_q": 154}`

| rank | hash | mode | s | four-real levels | outer perturbations | height | log disc |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| 1 | `3d68a81f60f3` | `outer_constant_shift` | 6 | `-1,-2,-3,-4,-5,-6` | `0:-3` | 327726 | 139.833 |
| 2 | `279813797174` | `outer_constant_shift` | 7 | `-1,-2,-3,-4,-6,-9` | `0:2` | 771498 | 190.753 |
| 3 | `505417204dd5` | `outer_constant_shift` | 8 | `-1,-2,-3,-4,-6,-7` | `0:-5` | 1199800 | 174.502 |
| 4 | `c5c54fd906c5` | `outer_constant_shift` | 9 | `-1,-2,-3,-4,-5,-10` | `0:-1` | 2190510 | 195.690 |
| 5 | `9bd8d4ef409a` | `outer_constant_shift` | 10 | `-1,-2,-3,-4,-5,-9` | `0:-3` | 3309700 | 191.820 |
| 6 | `f7e44459f1cf` | `outer_constant_shift` | 11 | `-1,-2,-3,-4,-6,-8` | `0:-5` | 5086136 | 196.560 |
| 7 | `eb3d7bcc205a` | `outer_constant_shift` | 12 | `-1,-2,-3,-4,-7,-10` | `0:-5` | 8667684 | 221.873 |
| 8 | `afa03adae24b` | `outer_constant_shift` | 6 | `-1,-2,-3,-4,-6,-7` | `0:-7` | 374346 | 161.114 |
| 9 | `8bc15d06f438` | `outer_constant_shift` | 7 | `-1,-2,-3,-4,-6,-11` | `0:7` | 853006 | 201.051 |
| 10 | `3ef87f855f08` | `outer_constant_shift` | 8 | `-1,-2,-3,-4,-7,-8` | `0:2` | 1340008 | 190.378 |

Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
