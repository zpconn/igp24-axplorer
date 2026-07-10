# IGP24 Offline MAGMA Verification Report

Offline MAGMA verification is explicit, local-only, timeout-bound, and separate from GPU training/sampling and CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/packet_verification_queue_1row`
- Input kind: `review_batch`
- Records loaded: 1
- Records selected for MAGMA: 1
- Timeout seconds: 60
- MAGMA available: `False`
- MAGMA executed: `False`
- Status counts: `{"dry_run": 1}`
- MAGMA discovery checked paths: 3
- MAGMA selected path: `None`
- Rerun guidance: MAGMA was not found on PATH or in the bounded common local search locations. Install MAGMA or pass --magma_executable /path/to/magma, then rerun the command below.
- Rerun command: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_offline_verify.py data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/packet_verification_queue_1row --output_dir /home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh_run_magma --run_sympy_nfdisc --run_sympy_signature --online_magma_manual --online_magma_pasted_output data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/online_magma_auto_probe_ee639_fresh_20260710/online_magma_pasted_outputs_automated_probe.jsonl --run_magma --magma_executable /path/to/magma`

| index | status | exact label | hash | score | r | cache | message |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | dry_run |  | `ee63944ba7bf` | 0.000000 | 24 | False | MAGMA execution was not requested; script generated only |

Artifacts:
- Results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_summary.json`
- Cache JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_cache.json`
- Candidate scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_candidate_scripts`
- Raw outputs: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_raw_outputs`
