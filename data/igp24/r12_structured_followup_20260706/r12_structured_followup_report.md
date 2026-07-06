# IGP24 R12 Structured Follow-Up Queue

CPU-only local r12 exact-composed feedback-aware follow-up. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 240
- Valid r=12 candidates: 155
- Selected rows: 10
- Queue status: `manual_queue_ready`
- Accepted feedback rows loaded: 10
- Accepted label counts: `{"24T22770": 2, "24T24970": 1, "24T24979": 7}`
- Selected mode counts: `{"four_base_balanced_perturbation": 3, "three_base_balanced_perturbation": 3, "two_base_wide_perturbation": 4}`
- Selected nearest-label counts: `{"24T24979": 10}`
- Rows intentionally diversifying away from 24T24979: 10
- Rejected counts: `{"real_root_count_mismatch": 54, "reducible_over_q": 31}`

| rank | hash | mode | positive y-roots | negative y-roots | base perturbations | nearest label | base L1 | exported L1 | height |
| ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `4d7fcabc2a86` | `two_base_wide_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `1:5,6:-4` | `24T24979` | 11934000 | 11934000 | 8796916 |
| 2 | `5eee184fe28f` | `three_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,9` | `1:4,5:-5,9:3` | `24T24979` | 11933999 | 11933999 | 8796916 |
| 3 | `87fdb1807f05` | `four_base_balanced_perturbation` | `1,2,4,5,7,8` | `1,2,4,5,7,9` | `0:-3,3:4,6:-5,9:2` | `24T24979` | 10166005 | 10166005 | 7828192 |
| 4 | `cac0a5d4e36e` | `two_base_wide_perturbation` | `1,2,3,5,7,9` | `1,2,4,5,7,9` | `5:-6,10:2` | `24T24979` | 8736005 | 8736005 | 6696912 |
| 5 | `c06c11583c94` | `three_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,7,8` | `1:-4,5:5,9:-3` | `24T24979` | 9724003 | 9724003 | 7828192 |
| 6 | `90b3dec7d4e7` | `four_base_balanced_perturbation` | `1,2,3,5,7,9` | `1,2,4,5,7,9` | `0:-3,3:4,6:-5,9:2` | `24T24979` | 8736005 | 8736005 | 6696912 |
| 7 | `981ec514837a` | `two_base_wide_perturbation` | `1,2,4,5,7,9` | `1,2,4,5,6,8` | `5:6,10:-2` | `24T24979` | 7169237 | 7169237 | 6724736 |
| 8 | `02fd97dc6774` | `three_base_balanced_perturbation` | `1,2,4,5,7,9` | `1,2,3,5,7,9` | `1:-4,5:5,9:-3` | `24T24979` | 6604003 | 6604003 | 6696912 |
| 9 | `4a7c7e377901` | `four_base_balanced_perturbation` | `1,2,4,5,6,8` | `1,2,4,5,7,9` | `0:3,3:-4,6:5,9:-2` | `24T24979` | 8194677 | 8194677 | 6724736 |
| 10 | `7066d7a3cfee` | `two_base_wide_perturbation` | `1,2,4,5,7,9` | `1,2,3,5,7,9` | `3:-5,8:4` | `24T24979` | 6604000 | 6604000 | 6696912 |

Caveat: these rows have local exact `r=12`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.

Artifacts:
- Queue JSONL: `data/igp24/r12_structured_followup_20260706/r12_structured_followup_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r12_structured_followup_20260706/r12_structured_followup_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r12_structured_followup_20260706/r12_structured_followup_candidate_hashes.txt`
- Summary JSON: `data/igp24/r12_structured_followup_20260706/r12_structured_followup_summary.json`
