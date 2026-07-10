# Manual Magma Checklist

This queue is not submission-grade until exact Magma labels are parsed.

1. Open the one-candidate scripts in:
   `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/online_magma_manual/copy_paste_scripts`
2. Paste each script manually into the free online Magma calculator.
3. Paste each returned output into the matching `pasted_output` field in:
   `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
4. Re-run `scripts/igp24_offline_verify.py` with `--online_magma_pasted_output` pointing at that filled template.
5. Re-run `scripts/igp24_score_aware_triage.py` on the refreshed exact artifact.

Do not automate online calculator submission without explicit approval.

## Queue

| rank | hash | script | exact r | exact nfdisc | status |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `4b6fc1786722` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/online_magma_manual/copy_paste_scripts/0001_4b6fc17867226448a51aced431465fb37f29400ca35f3234aff13ab0ea4c6bb7.m` | 8 |  | exact_result_missing |
| 2 | `d4aed028ad97` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/online_magma_manual/copy_paste_scripts/0002_d4aed028ad972072f94586e017a8349bd142ea10f30e5e2062db78406c35b4fd.m` | 8 | 121820589364734876729591821613082841879342204583936 | exact_result_missing |
| 3 | `caa861f3b409` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/online_magma_manual/copy_paste_scripts/0003_caa861f3b409b480c883e1d4bb6ef797eca09f5d68dbff0472d86a7624071971.m` | 8 | 234873986312310215862112540341409720823302210977792 | exact_result_missing |
| 4 | `5f06b5464de9` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/online_magma_manual/copy_paste_scripts/0004_5f06b5464de967f57a92a0085561a48741483fb8c03c053965be0c497e7cecaf.m` | 8 | 40549925653208015572705075309591021536773230559232 | exact_result_missing |
