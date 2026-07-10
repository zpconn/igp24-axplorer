# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/packet_verification_queue_1row/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh`
- Reviewed rows: 1
- Verified labels: 1
- Pending exact labels: 0
- Known submission hash rows: 0
- Failed rows: 0
- Submission-grade rows: 1
- Classification counts: `{"sair_discovered_pair_material_discriminant_improvement": 1}`
- Labels found: `{"24T13879": 1}`
- Label sources: `{"online_magma": 1}`
- Accepted-pair status counts: `{"not_previously_accepted": 1}`
- SAIR progress state counts: `{"allowed_discovered": 1}`
- SAIR score value status counts: `{"valuable_low_team": 1}`
- Known-submission status counts: `{"None": 1}`
- Exact r status counts: `{"ok": 1}`
- Exact nfdisc status counts: `{"ok": 1}`

## Row Triage

| rank | hash | label | r | nfdisc | progress | teams | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `ee63944ba7bf` | 24T13879 | 24 | 22825765914458084106356 | allowed_discovered | 7 |  | sair_discovered_pair_material_discriminant_improvement | yes | SAIR progress shows this pair is already discovered, but this exact nfdisc is a material improvement. |

## Recommendation

Build a manual submission package from `submission_grade_coefficients.txt` after human review.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_online_magma_fresh/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_online_magma_fresh/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_online_magma_fresh/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_online_magma_fresh/manual_magma_checklist.md`
