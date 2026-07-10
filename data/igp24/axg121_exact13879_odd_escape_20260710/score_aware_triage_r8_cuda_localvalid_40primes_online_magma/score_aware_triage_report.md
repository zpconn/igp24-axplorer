# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_40primes/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma`
- Reviewed rows: 1
- Verified labels: 1
- Pending exact labels: 0
- Known submission hash rows: 0
- Failed rows: 0
- Submission-grade rows: 0
- Classification counts: `{"sair_discovered_pair_not_improved": 1}`
- Labels found: `{"24T23883": 1}`
- Label sources: `{"online_magma": 1}`
- Accepted-pair status counts: `{"not_previously_accepted": 1}`
- SAIR progress state counts: `{"allowed_discovered": 1}`
- SAIR score value status counts: `{"crowded_or_low_value": 1}`
- Known-submission status counts: `{"None": 1}`
- Exact r status counts: `{"ok": 1}`
- Exact nfdisc status counts: `{"ok": 1}`

## Row Triage

| rank | hash | label | r | nfdisc | progress | teams | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `8f32835b516d` | 24T23883 | 8 | 737241846034013584158961827003874342424955999915225997334666057394099568420094367839673122816 | allowed_discovered | 47 |  | sair_discovered_pair_not_improved | no | SAIR progress shows this pair is already discovered, and this exact nfdisc is not a material current-best improvement. |

## Recommendation

Do not submit this queue as a new package yet. Exact labels are present, but the rows are not score-aware submission-grade after baseline, accepted-pair, generic, and discriminant-improvement checks.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_40primes_online_magma/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_40primes_online_magma/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_40primes_online_magma/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_40primes_online_magma/manual_magma_checklist.md`
