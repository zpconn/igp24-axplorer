# IGP24 R24 Tower Odd-Escape Candidate Queue

CPU-only local r24 odd-perturbed tower escape probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 900
- Valid r=24 candidates: 91
- Selected rows: 8
- Queue status: `api_dry_run_ready`
- Selected mode counts: `{"single_odd_tower_escape": 8}`
- Selected inner-s counts: `{"6": 5, "7": 3}`
- Rejected counts: `{"real_root_count_mismatch": 786, "reducible_over_q": 23}`

Anti-basin rationale: every selected row has odd support, support gcd 1, and is not an exact even outer-constant-shift tower.

| rank | hash | mode | s | levels | odd perturbations | height | log disc |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| 1 | `d1e6f4ff199c` | `single_odd_tower_escape` | 6 | `-1,-2,-3,-5,-6,-8` | `1:-1` | 443384 | 177.949 |
| 2 | `49c02cb24668` | `single_odd_tower_escape` | 6 | `-1,-3,-4,-5,-6,-8` | `1:-1` | 547090 | 168.980 |
| 3 | `efb95ccde1e1` | `single_odd_tower_escape` | 6 | `-1,-3,-4,-5,-6,-8` | `1:-2` | 547090 | 168.144 |
| 4 | `aee83a43fc3e` | `single_odd_tower_escape` | 6 | `-1,-3,-4,-5,-7,-8` | `1:-3` | 592489 | 174.792 |
| 5 | `2018298504d0` | `single_odd_tower_escape` | 7 | `-1,-2,-3,-4,-5,-9` | `1:1` | 725998 | 180.302 |
| 6 | `6d33e127c7ef` | `single_odd_tower_escape` | 7 | `-1,-2,-3,-4,-5,-9` | `1:-3` | 725998 | 175.505 |
| 7 | `44fa8ceeb02d` | `single_odd_tower_escape` | 7 | `-1,-2,-3,-4,-6,-8` | `1:-2` | 730744 | 182.063 |
| 8 | `b6afdf761b8a` | `single_odd_tower_escape` | 6 | `-2,-3,-5,-6,-7,-8` | `1:-2` | 777584 | 160.803 |

Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
