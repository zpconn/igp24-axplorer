# IGP24 Online MAGMA Manual Report

Online MAGMA calculator artifacts are manual copy/paste aids only. The helper does not submit requests, batch online work, call SAIR, or run inside training, GPU sampling, or CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710`
- Input kind: `review_batch`
- Records selected: 4
- Calculator URL: `https://magma.maths.usyd.edu.au/calc/`
- Observed calculator version: `2.29-8`
- Calculator caps: 60s, 50000 bytes
- Status counts: `{}`
- Already parsed exact labels: 0
- Ready for manual copy/paste: 4
- Local MAGMA status counts: `{"dry_run": 4}`
- Diagnostic strategy counts: `{"missing": 4}`
- Diagnostic flag counts: `{}`
- Manual script chunking: `{"all_scripts_under_calculator_limit": true, "calculator_max_input_bytes": 50000, "max_script_bytes": 899, "mode": "one_candidate_per_script", "scripts_written": 4}`

Manual flow:
1. Open the calculator URL in a browser.
2. Paste one generated script from the copy-paste scripts directory.
3. Paste the returned output into the JSONL template's `pasted_output` field.
4. Rerun this helper with `--online_magma_pasted_output` pointing at that JSONL.

## Already Parsed Exact Labels

| status | exact label | hash | degree | irreducible | runtime | version | group |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
|  |  |  |  |  |  |  |  |

## Ready For Manual Copy/Paste

| queue | hash | non-generic | score | r | strategy | flags | script |
| ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | `4b6fc1786722` |  | 9963.627220 | 8 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/copy_paste_scripts/0001_4b6fc17867226448a51aced431465fb37f29400ca35f3234aff13ab0ea4c6bb7.m` |
| 2 | `d4aed028ad97` |  | 10091.673366 | 8 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/copy_paste_scripts/0002_d4aed028ad972072f94586e017a8349bd142ea10f30e5e2062db78406c35b4fd.m` |
| 3 | `caa861f3b409` |  | 10096.016866 | 8 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/copy_paste_scripts/0003_caa861f3b409b480c883e1d4bb6ef797eca09f5d68dbff0472d86a7624071971.m` |
| 4 | `5f06b5464de9` |  | 10092.773382 | 8 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/copy_paste_scripts/0004_5f06b5464de967f57a92a0085561a48741483fb8c03c053965be0c497e7cecaf.m` |

## Proxy-Only Queue Candidates

| queue | hash | non-generic | score | r | height | flags | source ledger |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `4b6fc1786722` |  | 9963.627220 | 8 | 176 |  | `` |
| 2 | `d4aed028ad97` |  | 10091.673366 | 8 | 78 |  | `` |
| 3 | `caa861f3b409` |  | 10096.016866 | 8 | 78 |  | `` |
| 4 | `5f06b5464de9` |  | 10092.773382 | 8 | 78 |  | `` |

## Local MAGMA Dry-Run Status

- Local MAGMA executed: `False`
- Local MAGMA status counts: `{"dry_run": 4}`

Artifacts:
- Copy/paste scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/copy_paste_scripts`
- Pasted-output template: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
- Parsed results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/online_magma_manual_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/online_magma_manual/online_magma_manual_summary.json`
