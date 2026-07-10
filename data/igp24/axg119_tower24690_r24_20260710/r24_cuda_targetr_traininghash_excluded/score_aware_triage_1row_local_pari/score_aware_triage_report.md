# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/packet_verification_queue_1row/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_local_pari`
- Reviewed rows: 1
- Verified labels: 0
- Pending exact labels: 1
- Known submission hash rows: 0
- Failed rows: 0
- Submission-grade rows: 0
- Classification counts: `{"exact_result_missing": 1}`
- Labels found: `{}`
- Label sources: `{}`
- Accepted-pair status counts: `{"not_previously_accepted": 1}`
- SAIR progress state counts: `{"exact_pair_missing": 1}`
- SAIR score value status counts: `{"no_score_value": 1}`
- Known-submission status counts: `{"None": 1}`
- Exact r status counts: `{"ok": 1}`
- Exact nfdisc status counts: `{"ok": 1}`

## Row Triage

| rank | hash | label | r | nfdisc | progress | teams | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `ee63944ba7bf` |  | 24 | 7748175911401154024403485283319595159976718226161664 | exact_pair_missing |  |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |

## Recommendation

Do not submit this queue yet. Exact labels are still missing; run the manual Magma scripts, paste outputs into the template, and rerun this triage.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_local_pari/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_local_pari/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_local_pari/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/score_aware_triage_1row_local_pari/manual_magma_checklist.md`
