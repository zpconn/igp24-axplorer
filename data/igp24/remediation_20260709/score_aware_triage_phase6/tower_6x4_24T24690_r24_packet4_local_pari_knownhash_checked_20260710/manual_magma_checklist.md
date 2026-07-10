# Manual Magma Checklist

This queue is not submission-grade until exact Magma labels are parsed.

1. Open the one-candidate scripts in:
   `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts`
2. Paste each script manually into the free online Magma calculator.
3. Paste each returned output into the matching `pasted_output` field in:
   `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
4. Re-run `scripts/igp24_offline_verify.py` with `--online_magma_pasted_output` pointing at that filled template.
5. Re-run `scripts/igp24_score_aware_triage.py` on the refreshed exact artifact.

Do not automate online calculator submission without explicit approval.

## Queue

| rank | hash | script | exact r | exact nfdisc | status |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `9da7a6f4dac4` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0001_9da7a6f4dac4a3f9aec5b7a8a5fd7439c2ea3508da77689cc16cab0c7de6ca0e.m` | 24 | 13365495531490149029747688092026545642362720201473901836894208 | exact_result_missing |
| 2 | `16a66dd8583f` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0002_16a66dd8583f7f612e350a3c5f921a7d74317946c077f21f27e7858a677f3e98.m` | 24 | 84776163224614780474559042345342862121335731256164360388608 | exact_result_missing |
| 3 | `093d4ca1da4c` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0003_093d4ca1da4c1f437c3313e3bf40eb0a5d0a1b0ed5805b3eca639ff6ed668220.m` | 24 | 24408050786200794374252897653120049130788211971745248182272 | exact_result_missing |
| 4 | `b03eb2c2a86a` | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0004_b03eb2c2a86a9e2bef2de3683672347889e43bf31ee07cb8a8b45df74b8e05ce.m` | 24 | 631092708921170101130806403434330302280044898156544 | exact_result_missing |
