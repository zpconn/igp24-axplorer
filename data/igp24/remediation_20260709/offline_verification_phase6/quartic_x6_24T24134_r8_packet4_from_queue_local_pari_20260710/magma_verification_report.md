# IGP24 Offline MAGMA Verification Report

Offline MAGMA verification is explicit, local-only, timeout-bound, and separate from GPU training/sampling and CPU proxy scoring.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710`
- Input kind: `review_batch`
- Records loaded: 4
- Records selected for MAGMA: 4
- Timeout seconds: 300
- MAGMA available: `False`
- MAGMA executed: `False`
- Status counts: `{"dry_run": 4}`
- MAGMA discovery checked paths: 3
- MAGMA selected path: `None`
- Rerun guidance: MAGMA was not found on PATH or in the bounded common local search locations. Install MAGMA or pass --magma_executable /path/to/magma, then rerun the command below.
- Rerun command: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_offline_verify.py data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710 --output_dir /home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710_run_magma --pari_executable /tmp/igp24_pari_gp_local/root/usr/bin/gp --run_pari --run_sympy_signature --run_sympy_nfdisc --online_magma_manual --timeout_seconds 300 --run_magma --magma_executable /path/to/magma`

| index | status | exact label | hash | score | r | cache | message |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | dry_run |  | `4b6fc1786722` | 9963.627220 | 8 | False | MAGMA execution was not requested; script generated only |
| 2 | dry_run |  | `d4aed028ad97` | 10091.673366 | 8 | False | MAGMA execution was not requested; script generated only |
| 3 | dry_run |  | `caa861f3b409` | 10096.016866 | 8 | False | MAGMA execution was not requested; script generated only |
| 4 | dry_run |  | `5f06b5464de9` | 10092.773382 | 8 | False | MAGMA execution was not requested; script generated only |

Artifacts:
- Results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/magma_verification_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/magma_verification_summary.json`
- Cache JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/magma_verification_cache.json`
- Candidate scripts: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/magma_candidate_scripts`
- Raw outputs: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_local_pari_20260710/magma_raw_outputs`
