# IGP24 Online MAGMA Manual Report

Online MAGMA calculator artifacts are offline scripts plus saved-output parsers. The helper does not submit requests, batch online work, call SAIR, or run inside training, GPU sampling, or CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_retry120_threshold20_pre_exact_review`
- Input kind: `review_batch`
- Records selected: 2
- Calculator URL: `https://magma.maths.usyd.edu.au/calc/`
- Observed calculator version: `2.29-8`
- Calculator caps: 60s, 50000 bytes
- Status counts: `{"verified": 2}`
- Already parsed exact labels: 2
- Ready for manual copy/paste: 0
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
| verified | 24T23883 | `8f32835b516d` | 24 | True | 1.929 | V2.29-8 | Permutation group G acting on a set of cardinality 24 |
| verified | 24T9993 | `425c30453d4a` | 24 | True | 0.740 | V2.29-8 | Permutation group G acting on a set of cardinality 24 |

## Ready For Manual Copy/Paste

| queue | hash | non-generic | score | r | strategy | flags | script |
| ---: | --- | ---: | ---: | ---: | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Proxy-Only Queue Candidates

| queue | hash | non-generic | score | r | height | flags | source ledger |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
|  |  |  |  |  |  |  |  |

## Local MAGMA Dry-Run Status

- Local MAGMA executed: `False`
- Local MAGMA status counts: `{"dry_run": 2}`

Artifacts:
- Copy/paste scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/online_magma_manual/copy_paste_scripts`
- Pasted-output template: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
- Parsed results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/online_magma_manual/online_magma_manual_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/online_magma_manual/online_magma_manual_summary.json`
