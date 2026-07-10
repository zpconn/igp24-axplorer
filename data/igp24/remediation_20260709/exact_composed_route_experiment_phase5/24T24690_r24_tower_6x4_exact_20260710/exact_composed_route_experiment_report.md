# IGP24 Exact-Composed Route Experiment

- Created: `2026-07-10T08:46:04.991611+00:00`
- Source commit: `a0060d0545344c2d70e191014ef9216aa0d33d04`
- Safety: Offline exact-composed route experiment. It does not call SAIR/network APIs and does not make a live submission.
- Target route: `24T24690|r=24` via `tower_6x4`
- Executable generator: `tower_6x4_exact_quartic_inner_v1`
- Structure preservation: `exact h(q(x)) support with deg(h)=6 and quartic q(x)=x^4-s*x^2`
- Trials attempted: `120`
- Local-valid candidates stored: `16`
- Local-valid candidates evaluated: `16`
- Local-valid overflow not stored: `0`
- Adaptive target-compatible candidates: `0`
- Any valuable-target survivor candidates: `16`
- Known-submission rejections: `1`
- Live submission recommended now: `False`

## Candidate Rows

| rank | hash | height | usable primes | target label retained | target pair valuable | any valuable pairs | recommendation |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `d549e1349f9c` | 927454 | 20 | `False` | `False` | 10 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 2 | `14066a706f48` | 927454 | 20 | `False` | `False` | 90 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 3 | `69c6d32d48b8` | 927454 | 20 | `False` | `False` | 5 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 4 | `fe3e3a14916b` | 927454 | 20 | `False` | `False` | 52 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 5 | `093d4ca1da4c` | 927454 | 20 | `False` | `False` | 23 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 6 | `b03eb2c2a86a` | 927454 | 20 | `False` | `False` | 12 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 7 | `b500c6872333` | 327726 | 20 | `False` | `False` | 4 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 8 | `16a66dd8583f` | 327726 | 20 | `False` | `False` | 80 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 9 | `298d2a2235fa` | 327726 | 20 | `False` | `False` | 3 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 10 | `4bcffb45d4ff` | 327726 | 20 | `False` | `False` | 8 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 11 | `07de9bfad59f` | 327726 | 20 | `False` | `False` | 2 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 12 | `551de7fd33fd` | 327726 | 20 | `False` | `False` | 5 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 13 | `9a6203690a28` | 327726 | 20 | `False` | `False` | 10 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 14 | `5c52c2f98542` | 567244 | 20 | `False` | `False` | 30 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 15 | `9da7a6f4dac4` | 567244 | 20 | `False` | `False` | 31 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 16 | `0d3df46a2436` | 567244 | 20 | `False` | `False` | 32 | `false_target_label_ruled_out_by_adaptive_evidence` |

Compatibility here is necessary target-exclusion evidence only; it is not exact 24T label verification.
