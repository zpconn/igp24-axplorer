# IGP24 Offline MAGMA Verification Report

Offline MAGMA verification is explicit, local-only, timeout-bound, and separate from GPU training/sampling and CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_retry120_threshold20_pre_exact_review`
- Input kind: `review_batch`
- Records loaded: 2
- Records selected for MAGMA: 2
- Timeout seconds: 240
- MAGMA available: `False`
- MAGMA executed: `False`
- Status counts: `{"dry_run": 2}`
- MAGMA discovery checked paths: 3
- MAGMA selected path: `None`
- Rerun guidance: MAGMA was not found on PATH or in the bounded common local search locations. Install MAGMA or pass --magma_executable /path/to/magma, then rerun the command below.
- Rerun command: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_offline_verify.py data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_retry120_threshold20_pre_exact_review --output_dir /home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma_run_magma --run_sympy_signature --run_sympy_nfdisc --online_magma_manual --online_magma_pasted_output data/igp24/axg121_exact13879_odd_escape_20260710/online_magma_auto_probe_r8_cuda_localvalid_20260710/raw_xml/0001_8f32835b516d.xml --online_magma_pasted_output data/igp24/axg121_exact13879_odd_escape_20260710/online_magma_auto_probe_r8_cuda_localvalid_20260710/raw_xml/0002_425c30453d4a.xml --timeout_seconds 240 --run_magma --magma_executable /path/to/magma`

| index | status | exact label | hash | score | r | cache | message |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | dry_run |  | `425c30453d4a` | 10171.432296 | 8 | False | MAGMA execution was not requested; script generated only |
| 2 | dry_run |  | `8f32835b516d` | 0.000000 | 8 | False | MAGMA execution was not requested; script generated only |

Artifacts:
- Results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/magma_verification_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/magma_verification_summary.json`
- Cache JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/magma_verification_cache.json`
- Candidate scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/magma_candidate_scripts`
- Raw outputs: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_retry120_threshold20_both_exact_online_magma/magma_raw_outputs`
