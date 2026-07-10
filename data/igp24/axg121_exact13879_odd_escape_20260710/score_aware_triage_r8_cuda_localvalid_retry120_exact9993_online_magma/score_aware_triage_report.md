# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_retry120_post_exact_feedback/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_post_exact_feedback_online_magma`
- Reviewed rows: 1
- Verified labels: 1
- Pending exact labels: 0
- Known submission hash rows: 0
- Failed rows: 0
- Submission-grade rows: 0
- Classification counts: `{"accepted_pair_duplicate": 1}`
- Labels found: `{"24T9993": 1}`
- Label sources: `{"online_magma": 1}`
- Accepted-pair status counts: `{"accepted_pair_needs_exact_nfdisc": 1}`
- SAIR progress state counts: `{"allowed_discovered": 1}`
- SAIR score value status counts: `{"valuable_low_team": 1}`
- Known-submission status counts: `{"None": 1}`
- Exact r status counts: `{"ok": 1}`
- Exact nfdisc status counts: `{"ok": 1}`

## Row Triage

| rank | hash | label | r | nfdisc | progress | teams | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `425c30453d4a` | 24T9993 | 8 | 10723488292100241361294296648700284370944 | allowed_discovered | 12 |  | accepted_pair_duplicate | no | Pair is already accepted locally; most accepted pairs have tiny scores unless the pair is low-team or the discriminant improves materially. |

## Recommendation

Do not submit this queue as a new package yet. Exact labels are present, but the rows are not score-aware submission-grade after baseline, accepted-pair, generic, and discriminant-improvement checks.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_retry120_exact9993_online_magma/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_retry120_exact9993_online_magma/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_retry120_exact9993_online_magma/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/score_aware_triage_r8_cuda_localvalid_retry120_exact9993_online_magma/manual_magma_checklist.md`
