# IGP24 SymPy nfdisc Report

SymPy nfdisc artifacts are explicit local fallback evidence. PARI/GP remains the official workflow when available.

- Input: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/packet_verification_queue_phase6/quartic_x6_24T24134_r8_packet4_20260710`
- Input kind: `review_batch`
- Records loaded: 4
- Requested: `True`
- Exact nfdisc records: 3
- Status counts: `{"nfdisc_error": 1, "nfdisc_ok": 3}`

| status | hash | degree | nfdisc | poly_disc | quotient_square |
| --- | --- | ---: | ---: | ---: | --- |
| nfdisc_error | `4b6fc1786722` |  |  |  |  |
| nfdisc_ok | `d4aed028ad97` | 24 | 121820589364734876729591821613082841879342204583936 | 121820589364734876729591821613082841879342204583936 | True |
| nfdisc_ok | `caa861f3b409` | 24 | 234873986312310215862112540341409720823302210977792 | 234873986312310215862112540341409720823302210977792 | True |
| nfdisc_ok | `5f06b5464de9` | 24 | 40549925653208015572705075309591021536773230559232 | 40549925653208015572705075309591021536773230559232 | True |

Artifacts:
- Results JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/sympy_nfdisc_results.jsonl`
- Summary JSON: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/offline_verification_phase6/quartic_x6_24T24134_r8_packet4_from_queue_20260710/sympy_nfdisc_summary.json`
