# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710`
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
- Known-submission status counts: `{"None": 4}`
- Exact r status counts: `{"ok": 4}`
- Exact nfdisc status counts: `{"ok": 4}`

## Row Triage

| rank | hash | label | r | nfdisc | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 1 | `4b6fc1786722` |  | 8 | 2589457471663020290830410681073952737028210688 |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |
| 2 | `d4aed028ad97` |  | 8 | 121820589364734876729591821613082841879342204583936 |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |
| 3 | `caa861f3b409` |  | 8 | 234873986312310215862112540341409720823302210977792 |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |
| 4 | `5f06b5464de9` |  | 8 | 40549925653208015572705075309591021536773230559232 |  | exact_result_missing | no | Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade. |

## Recommendation

Do not submit this queue yet. Exact labels are still missing; run the manual Magma scripts, paste outputs into the template, and rerun this triage.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_local_pari_knownhash_checked_20260710/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_local_pari_knownhash_checked_20260710/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_local_pari_knownhash_checked_20260710/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_local_pari_knownhash_checked_20260710/manual_magma_checklist.md`
