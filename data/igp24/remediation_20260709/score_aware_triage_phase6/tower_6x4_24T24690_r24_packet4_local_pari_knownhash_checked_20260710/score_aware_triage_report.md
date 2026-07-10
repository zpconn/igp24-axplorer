# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/tower_6x4_24T24690_r24_packet4_20260710/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710`
- Reviewed rows: 4
- Verified labels: 0
- Pending exact labels: 4
- Known submission hash rows: 0
- Failed rows: 0
- Submission-grade rows: 0
- Classification counts: `{"exact_result_missing": 4}`
- Labels found: `{}`
- Label sources: `{}`
- Accepted-pair status counts: `{"not_previously_accepted": 4}`
- SAIR progress state counts: `{"exact_pair_missing": 4}`
- SAIR score value status counts: `{"no_score_value": 4}`
- Known-submission status counts: `{"None": 4}`
- Exact r status counts: `{"ok": 4}`
- Exact nfdisc status counts: `{"ok": 4}`

## Row Triage

| rank | hash | label | r | nfdisc | progress | teams | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `9da7a6f4dac4` |  | 24 | 13365495531490149029747688092026545642362720201473901836894208 | exact_pair_missing |  |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |
| 2 | `16a66dd8583f` |  | 24 | 84776163224614780474559042345342862121335731256164360388608 | exact_pair_missing |  |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |
| 3 | `093d4ca1da4c` |  | 24 | 24408050786200794374252897653120049130788211971745248182272 | exact_pair_missing |  |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |
| 4 | `b03eb2c2a86a` |  | 24 | 631092708921170101130806403434330302280044898156544 | exact_pair_missing |  |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |

## Recommendation

Do not submit this queue yet. Exact labels are still missing; run the manual Magma scripts, paste outputs into the template, and rerun this triage.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/tower_6x4_24T24690_r24_packet4_local_pari_knownhash_checked_20260710/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/tower_6x4_24T24690_r24_packet4_local_pari_knownhash_checked_20260710/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/tower_6x4_24T24690_r24_packet4_local_pari_knownhash_checked_20260710/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/tower_6x4_24T24690_r24_packet4_local_pari_knownhash_checked_20260710/manual_magma_checklist.md`
