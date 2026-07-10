# IGP24 Offline Verification Plan

Offline verifier artifact. No SAIR submission, network call, or auto-submission is performed; exact group labels are recorded only when an explicit local MAGMA run returns parseable provenance.

- Source review batch: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710`
- Selected records: 4
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710`
- PARI/GP available: `True`
- MAGMA available: `False`
- PARI/GP executed: `True`
- MAGMA executed: `False`
- MAGMA discovery checked paths: 3
- MAGMA selected path: `None`
- MAGMA rerun command: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_offline_verify.py data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710 --output_dir /home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710_run_magma --pari_executable /tmp/igp24_pari_gp_local/root/usr/bin/gp --run_pari --run_sympy_signature --run_sympy_nfdisc --online_magma_manual --online_magma_pasted_output data/igp24/remediation_20260709/online_magma_auto_probe_phase6/quartic_x6_24T24134_r8_packet4_20260710/online_magma_pasted_outputs_automated_probe.jsonl --run_magma --magma_executable /path/to/magma`

Generated files:
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/pari_input.gp`
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/magma_input.m`
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/offline_verification_manifest.json`
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/magma_verification_results.jsonl`
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/magma_verification_summary.json`
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/magma_verification_report.md`
- `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_online_magma_pari_20260710/magma_verification_cache.json`

Manual next steps:
1. Review the candidate table below, generated verifier scripts, and MAGMA result report.
2. Run local PARI/GP manually, or rerun this helper with an explicit `--run_magma` flag after confirming the local tool is available.
3. Promote an exact group label only from `magma_verification_results.jsonl` rows with status `verified` and recorded MAGMA provenance.
4. Keep any SAIR packaging or submission separate, explicit, and human-controlled.

| Rank | Score | Hash | r | Strategy | Height |
| ---: | ---: | --- | ---: | --- | ---: |
| 1 | 9963.627220 | `4b6fc1786722` | 8 | `None` | 176 |
| 2 | 10091.673366 | `d4aed028ad97` | 8 | `None` | 78 |
| 3 | 10096.016866 | `caa861f3b409` | 8 | `None` | 78 |
| 4 | 10092.773382 | `5f06b5464de9` | 8 | `None` | 78 |
