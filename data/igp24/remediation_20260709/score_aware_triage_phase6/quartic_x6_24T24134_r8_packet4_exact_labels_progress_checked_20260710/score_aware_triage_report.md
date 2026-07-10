# IGP24 Score-Aware Triage

Score-aware triage is local/file-only. It does not submit to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train models, sample on GPU, run CPU search loops, or run local search.

Most accepted rows have scored <0.0001 so far, while the visible positive outliers are low-team pairs such as 24T9993|r=8 and 24T22770|r=12. Acceptance alone is not enough. Prioritize genuinely new non-baseline non-generic pairs, low-team scored pockets, or accepted-pair duplicates only when the exact discriminant improvement is material.

- Queue: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710/verification_batch.jsonl`
- Exact artifact: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710`
- Reviewed rows: 4
- Verified labels: 4
- Pending exact labels: 0
- Known submission hash rows: 0
- Failed rows: 0
- Submission-grade rows: 0
- Classification counts: `{"sair_discovered_pair_not_improved": 4}`
- Labels found: `{"24T10010": 1, "24T12493": 1, "24T7635": 1, "24T9962": 1}`
- Label sources: `{"online_magma": 4}`
- Accepted-pair status counts: `{"not_previously_accepted": 4}`
- SAIR progress state counts: `{"allowed_discovered": 4}`
- SAIR score value status counts: `{"crowded_or_low_value": 2, "valuable_low_team": 2}`
- Known-submission status counts: `{"None": 4}`
- Exact r status counts: `{"ok": 4}`
- Exact nfdisc status counts: `{"ok": 4}`

## Row Triage

| rank | hash | label | r | nfdisc | progress | teams | known submission | class | submit | note |
| ---: | --- | --- | ---: | ---: | --- | ---: | --- | --- | --- | --- |
| 1 | `4b6fc1786722` | 24T7635 | 8 | 2589457471663020290830410681073952737028210688 | allowed_discovered | 13 |  | sair_discovered_pair_not_improved | no | SAIR progress shows this pair is already discovered, and this exact nfdisc is not a material current-best improvement. |
| 2 | `d4aed028ad97` | 24T10010 | 8 | 121820589364734876729591821613082841879342204583936 | allowed_discovered | 10 |  | sair_discovered_pair_not_improved | no | SAIR progress shows this pair is already discovered, and this exact nfdisc is not a material current-best improvement. |
| 3 | `caa861f3b409` | 24T12493 | 8 | 234873986312310215862112540341409720823302210977792 | allowed_discovered | 30 |  | sair_discovered_pair_not_improved | no | SAIR progress shows this pair is already discovered, and this exact nfdisc is not a material current-best improvement. |
| 4 | `5f06b5464de9` | 24T9962 | 8 | 40549925653208015572705075309591021536773230559232 | allowed_discovered | 24 |  | sair_discovered_pair_not_improved | no | SAIR progress shows this pair is already discovered, and this exact nfdisc is not a material current-best improvement. |

## Recommendation

Do not submit this queue as a new package yet. Exact labels are present, but the rows are not score-aware submission-grade after baseline, accepted-pair, generic, and discriminant-improvement checks.

Artifacts:
- Triage JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_exact_labels_progress_checked_20260710/score_aware_triage.jsonl`
- Submission-grade JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_exact_labels_progress_checked_20260710/submission_grade_rows.jsonl`
- Submission-grade coefficients: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_exact_labels_progress_checked_20260710/submission_grade_coefficients.txt`
- Manual checklist: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_aware_triage_phase6/quartic_x6_24T24134_r8_packet4_exact_labels_progress_checked_20260710/manual_magma_checklist.md`
