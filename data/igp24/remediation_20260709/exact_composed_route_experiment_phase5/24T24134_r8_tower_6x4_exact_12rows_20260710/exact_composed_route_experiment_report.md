# IGP24 Exact-Composed Route Experiment

- Created: `2026-07-10T07:12:43.403811+00:00`
- Source commit: `75bd6365c9bee88cd9b17880b96d726633b7988e`
- Safety: Offline exact-composed route experiment. It does not call SAIR/network APIs and does not make a live submission.
- Target route: `24T24134|r=8` via `tower_6x4`
- Executable generator: `tower_6x4_exact_quartic_inner_v1`
- Structure preservation: `exact h(q(x)) support with deg(h)=6 and quartic q(x)=x^4-s*x^2`
- Trials attempted: `12`
- Local-valid candidates stored: `8`
- Local-valid candidates evaluated: `8`
- Local-valid overflow not stored: `0`
- Adaptive target-compatible candidates: `0`
- Any valuable-target survivor candidates: `2`
- Known-submission rejections: `0`
- Live submission recommended now: `False`

## Candidate Rows

| rank | hash | height | usable primes | target label retained | target pair valuable | any valuable pairs | recommendation |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `d5aa43d6cb93` | 793585 | 9 | `False` | `False` | 1 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 2 | `aa10b2909f9f` | 793585 | 10 | `False` | `False` | 1 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 3 | `e84d801cab9f` | 793565 | 10 | `False` | `False` | 7 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 4 | `3e1b65cdb5a3` | 793585 | 10 | `False` | `False` | 0 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 5 | `f6e11fda4e7f` | 793585 | 10 | `False` | `False` | 0 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 6 | `35afe2487c9f` | 793585 | 10 | `False` | `False` | 0 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 7 | `c81935f005a8` | 793460 | 6 | `False` | `False` | 1 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 8 | `9eca1a243ae7` | 793575 | 10 | `False` | `False` | 0 | `false_target_label_ruled_out_by_adaptive_evidence` |

Compatibility here is necessary target-exclusion evidence only; it is not exact 24T label verification.
