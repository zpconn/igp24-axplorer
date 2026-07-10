# IGP24 Offline Verification Plan

Offline verifier artifact. No SAIR submission, network call, or auto-submission is performed; exact group labels are recorded only when an explicit local MAGMA run returns parseable provenance.

- Source review batch: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/packet_verification_queue_1row`
- Selected records: 1
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh`
- PARI/GP available: `False`
- MAGMA available: `False`
- PARI/GP executed: `False`
- MAGMA executed: `False`
- MAGMA discovery checked paths: 3
- MAGMA selected path: `None`
- MAGMA rerun command: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_offline_verify.py data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/packet_verification_queue_1row --output_dir /home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh_run_magma --run_sympy_nfdisc --run_sympy_signature --online_magma_manual --online_magma_pasted_output data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/online_magma_auto_probe_ee639_fresh_20260710/online_magma_pasted_outputs_automated_probe.jsonl --run_magma --magma_executable /path/to/magma`

Generated files:
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/pari_input.gp`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_input.m`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/offline_verification_manifest.json`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_results.jsonl`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_summary.json`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_report.md`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg119_tower24690_r24_20260710/r24_cuda_targetr_traininghash_excluded/offline_verification_1row_online_magma_fresh/magma_verification_cache.json`

Manual next steps:
1. Review the candidate table below, generated verifier scripts, and MAGMA result report.
2. Run local PARI/GP manually, or rerun this helper with an explicit `--run_magma` flag after confirming the local tool is available.
3. Promote an exact group label only from `magma_verification_results.jsonl` rows with status `verified` and recorded MAGMA provenance.
4. Keep any SAIR packaging or submission separate, explicit, and human-controlled.

| Rank | Score | Hash | r | Strategy | Height |
| ---: | ---: | --- | ---: | --- | ---: |
| 1 | 0.000000 | `ee63944ba7bf` | 24 | `None` | 567244 |
