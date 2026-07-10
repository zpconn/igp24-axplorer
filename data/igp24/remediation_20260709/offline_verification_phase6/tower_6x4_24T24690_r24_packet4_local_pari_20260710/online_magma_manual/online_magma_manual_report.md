# IGP24 Online MAGMA Manual Report

Online MAGMA calculator artifacts are offline scripts plus saved-output parsers. The helper does not submit requests, batch online work, call SAIR, or run inside training, GPU sampling, or CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/tower_6x4_24T24690_r24_packet4_20260710`
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
- Manual script chunking: `{"all_scripts_under_calculator_limit": true, "calculator_max_input_bytes": 50000, "max_script_bytes": 946, "mode": "one_candidate_per_script", "scripts_written": 4}`

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
| 1 | `9da7a6f4dac4` |  | 0.000000 | 24 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0001_9da7a6f4dac4a3f9aec5b7a8a5fd7439c2ea3508da77689cc16cab0c7de6ca0e.m` |
| 2 | `16a66dd8583f` |  | 0.000000 | 24 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0002_16a66dd8583f7f612e350a3c5f921a7d74317946c077f21f27e7858a677f3e98.m` |
| 3 | `093d4ca1da4c` |  | 0.000000 | 24 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0003_093d4ca1da4c1f437c3313e3bf40eb0a5d0a1b0ed5805b3eca639ff6ed668220.m` |
| 4 | `b03eb2c2a86a` |  | 0.000000 | 24 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts/0004_b03eb2c2a86a9e2bef2de3683672347889e43bf31ee07cb8a8b45df74b8e05ce.m` |

## Proxy-Only Queue Candidates

| queue | hash | non-generic | score | r | height | flags | source ledger |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `9da7a6f4dac4` |  | 0.000000 | 24 | 567244 |  | `` |
| 2 | `16a66dd8583f` |  | 0.000000 | 24 | 327726 |  | `` |
| 3 | `093d4ca1da4c` |  | 0.000000 | 24 | 927454 |  | `` |
| 4 | `b03eb2c2a86a` |  | 0.000000 | 24 | 927454 |  | `` |

## Local MAGMA Dry-Run Status

- Local MAGMA executed: `False`
- Local MAGMA status counts: `{"dry_run": 4}`

Artifacts:
- Copy/paste scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/copy_paste_scripts`
- Pasted-output template: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
- Parsed results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/online_magma_manual_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/tower_6x4_24T24690_r24_packet4_local_pari_20260710/online_magma_manual/online_magma_manual_summary.json`
