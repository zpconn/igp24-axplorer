# IGP24 R12 Structured Follow-Up Queue

CPU-only local r12 exact-composed feedback-aware follow-up. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 600
- Valid r=12 candidates: 394
- Selected rows: 12
- Queue status: `manual_queue_ready`
- Accepted feedback rows loaded: 10
- Accepted label counts: `{"24T22770": 2, "24T24970": 1, "24T24979": 7}`
- Selected mode counts: `{"four_base_balanced_perturbation": 4, "three_base_balanced_perturbation": 4, "two_base_wide_perturbation": 4}`
- Selected nearest-label counts: `{"24T24979": 12}`
- Rows intentionally diversifying away from 24T24979: 12
- Rejected counts: `{"known_or_duplicate_hash": 3, "real_root_count_mismatch": 108, "reducible_over_q": 95}`

| rank | hash | mode | positive y-roots | negative y-roots | base perturbations | nearest label | base L1 | exported L1 | height |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `a429ed348266` | `two_base_wide_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `2:-7,7:5` | `24T24979` | 11934013 | 11934013 | 8796923 |
| 2 | `87efd4d3d5b1` | `three_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `0:5,4:-4,8:3` | `24T24979` | 11934005 | 11934005 | 8796916 |
| 3 | `4f495a65e7df` | `four_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `0:3,3:-4,6:5,9:-2` | `24T24979` | 11933997 | 11933997 | 8796916 |
| 4 | `a47fbc9f4746` | `two_base_wide_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `3:5,8:-4` | `24T24979` | 11934002 | 11934002 | 8796916 |
| 5 | `7b06316130fa` | `three_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `1:-4,5:5,9:-3` | `24T24979` | 11934003 | 11934003 | 8796916 |
| 6 | `8f6c60774634` | `four_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,8` | `0:3,3:-4,6:5,9:-2` | `24T24979` | 9723997 | 9723997 | 7828192 |
| 7 | `75db800d94db` | `two_base_wide_perturbation` | `1,2,4,5,7,8` | `1,2,4,5,7,9` | `0:7,5:-3` | `24T24979` | 10166011 | 10166011 | 7828192 |
| 8 | `9ffdb88ccdba` | `three_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,8` | `0:5,4:-4,8:3` | `24T24979` | 9724005 | 9724005 | 7828192 |
| 9 | `b3e1e9a8b42c` | `four_base_balanced_perturbation` | `1,2,3,5,7,9` | `1,2,4,5,7,9` | `0:3,3:-4,6:5,9:-2` | `24T24979` | 8735997 | 8735997 | 6696912 |
| 10 | `4342b94fd43e` | `two_base_wide_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,8` | `2:-7,7:5` | `24T24979` | 9724013 | 9724013 | 7828199 |
| 11 | `395f2427b6b8` | `three_base_balanced_perturbation` | `1,2,3,5,7,9` | `1,2,4,5,7,9` | `0:5,4:-4,8:3` | `24T24979` | 8736005 | 8736005 | 6696912 |
| 12 | `4c74f492540d` | `four_base_balanced_perturbation` | `1,2,4,5,6,8` | `1,2,4,5,7,9` | `0:-3,3:4,6:-5,9:2` | `24T24979` | 8194685 | 8194685 | 6724736 |

Caveat: these rows have local exact `r=12`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/axg112_pivot_20260709/r12_structured_followup/r12_structured_followup_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/axg112_pivot_20260709/r12_structured_followup/r12_structured_followup_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/axg112_pivot_20260709/r12_structured_followup/r12_structured_followup_candidate_hashes.txt`
- Summary JSON: `data/igp24/axg112_pivot_20260709/r12_structured_followup/r12_structured_followup_summary.json`
