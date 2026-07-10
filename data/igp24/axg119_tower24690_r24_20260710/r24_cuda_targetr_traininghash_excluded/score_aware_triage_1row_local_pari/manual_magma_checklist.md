# Manual Magma Checklist

This queue is not submission-grade until exact Magma labels are parsed.

1. Open the one-candidate scripts in:
   `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_local_pari/online_magma_manual/copy_paste_scripts`
2. Paste each script manually into the free online Magma calculator.
3. Paste each returned output into the matching `pasted_output` field in:
   `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_local_pari/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
4. Re-run `scripts/igp24_offline_verify.py` with `--online_magma_pasted_output` pointing at that filled template.
5. Re-run `scripts/igp24_score_aware_triage.py` on the refreshed exact artifact.

Do not automate online calculator submission without explicit approval.

## Queue

| rank | hash | script | exact r | exact nfdisc | status |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `ee63944ba7bf` | `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_local_pari/online_magma_manual/copy_paste_scripts/0001_ee63944ba7bf61dde03b31907636e85b3cea05f648ae1f0a2918d629fd29c825.m` | 24 | 7748175911401154024403485283319595159976718226161664 | exact_result_missing |
