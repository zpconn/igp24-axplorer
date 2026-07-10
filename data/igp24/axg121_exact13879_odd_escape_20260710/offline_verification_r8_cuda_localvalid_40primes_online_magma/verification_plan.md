# IGP24 Offline Verification Plan

Offline verifier artifact. No SAIR submission, network call, or auto-submission is performed; exact group labels are recorded only when an explicit local MAGMA run returns parseable provenance.

- Source review batch: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_40primes`
- Selected records: 1
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma`
- PARI/GP available: `False`
- MAGMA available: `False`
- PARI/GP executed: `False`
- MAGMA executed: `False`
- MAGMA discovery checked paths: 3
- MAGMA selected path: `None`
- MAGMA rerun command: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_offline_verify.py data/igp24/axg121_exact13879_odd_escape_20260710/packet_verification_queue_r8_cuda_localvalid_40primes --output_dir /home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma_run_magma --run_sympy_signature --run_sympy_nfdisc --online_magma_manual --online_magma_pasted_output data/igp24/axg121_exact13879_odd_escape_20260710/online_magma_auto_probe_r8_cuda_localvalid_20260710/raw_xml/0001_8f32835b516d.xml --timeout_seconds 180 --run_magma --magma_executable /path/to/magma`

Generated files:
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/pari_input.gp`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/magma_input.m`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/offline_verification_manifest.json`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/magma_verification_results.jsonl`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/magma_verification_summary.json`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/magma_verification_report.md`
- `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/offline_verification_r8_cuda_localvalid_40primes_online_magma/magma_verification_cache.json`

Manual next steps:
1. Review the candidate table below, generated verifier scripts, and MAGMA result report.
2. Run local PARI/GP manually, or rerun this helper with an explicit `--run_magma` flag after confirming the local tool is available.
3. Promote an exact group label only from `magma_verification_results.jsonl` rows with status `verified` and recorded MAGMA provenance.
4. Keep any SAIR packaging or submission separate, explicit, and human-controlled.

| Rank | Score | Hash | r | Strategy | Height |
| ---: | ---: | --- | ---: | --- | ---: |
| 1 | 0.000000 | `8f32835b516d` | 8 | `None` | 327726 |
