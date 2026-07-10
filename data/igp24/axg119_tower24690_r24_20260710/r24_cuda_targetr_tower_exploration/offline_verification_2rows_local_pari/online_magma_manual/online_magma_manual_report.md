# IGP24 Online MAGMA Manual Report

Online MAGMA calculator artifacts are offline scripts plus saved-output parsers. The helper does not submit requests, batch online work, call SAIR, or run inside training, GPU sampling, or CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/packet_verification_queue_2rows`
- Input kind: `review_batch`
- Records selected: 2
- Calculator URL: `https://magma.maths.usyd.edu.au/calc/`
- Observed calculator version: `2.29-8`
- Calculator caps: 60s, 50000 bytes
- Status counts: `{}`
- Already parsed exact labels: 0
- Ready for manual copy/paste: 2
- Local MAGMA status counts: `{"dry_run": 2}`
- Diagnostic strategy counts: `{"model_sample_export": 2}`
- Diagnostic flag counts: `{}`
- Manual script chunking: `{"all_scripts_under_calculator_limit": true, "calculator_max_input_bytes": 50000, "max_script_bytes": 941, "mode": "one_candidate_per_script", "scripts_written": 2}`

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
| 1 | `16a66dd8583f` |  | 0.000000 | 24 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/offline_verification_2rows_local_pari/online_magma_manual/copy_paste_scripts/0001_16a66dd8583f7f612e350a3c5f921a7d74317946c077f21f27e7858a677f3e98.m` |
| 2 | `9a6203690a28` |  | 0.000000 | 24 | `` |  | `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/offline_verification_2rows_local_pari/online_magma_manual/copy_paste_scripts/0002_9a6203690a2842ad02462d00b009912ef02606c2c5df914710a96e03825258e2.m` |

## Proxy-Only Queue Candidates

| queue | hash | non-generic | score | r | height | flags | source ledger |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `16a66dd8583f` |  | 0.000000 | 24 | 327726 |  | `` |
| 2 | `9a6203690a28` |  | 0.000000 | 24 | 327726 |  | `` |

## Local MAGMA Dry-Run Status

- Local MAGMA executed: `False`
- Local MAGMA status counts: `{"dry_run": 2}`

Artifacts:
- Copy/paste scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/offline_verification_2rows_local_pari/online_magma_manual/copy_paste_scripts`
- Pasted-output template: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/offline_verification_2rows_local_pari/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
- Parsed results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/offline_verification_2rows_local_pari/online_magma_manual/online_magma_manual_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_tower_exploration/offline_verification_2rows_local_pari/online_magma_manual/online_magma_manual_summary.json`
