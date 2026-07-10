# IGP24 Online MAGMA Manual Report

Online MAGMA calculator artifacts are offline scripts plus saved-output parsers. The helper does not submit requests, batch online work, call SAIR, or run inside training, GPU sampling, or CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710`
- Input kind: `review_batch`
- Records selected: 4
- Calculator URL: `https://magma.maths.usyd.edu.au/calc/`
- Observed calculator version: `2.29-8`
- Calculator caps: 60s, 50000 bytes
- Status counts: `{"verified": 4}`
- Already parsed exact labels: 4
- Ready for manual copy/paste: 0
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
| verified | 24T7635 | `4b6fc1786722` | 24 | True | 1.000 | V2.29-8 | Permutation group G acting on a set of cardinality 24 |
| verified | 24T10010 | `d4aed028ad97` | 24 | True | 0.880 | V2.29-8 | Permutation group G acting on a set of cardinality 24 |
| verified | 24T12493 | `caa861f3b409` | 24 | True | 1.389 | V2.29-8 | Permutation group G acting on a set of cardinality 24 |
| verified | 24T9962 | `5f06b5464de9` | 24 | True | 0.870 | V2.29-8 | Permutation group G acting on a set of cardinality 24 |

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
- Local MAGMA status counts: `{"dry_run": 4}`

Artifacts:
- Copy/paste scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/online_magma_manual/copy_paste_scripts`
- Pasted-output template: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/online_magma_manual/online_magma_pasted_outputs_template.jsonl`
- Parsed results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/online_magma_manual/online_magma_manual_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/online_magma_manual/online_magma_manual_summary.json`
