# IGP24 Exact-Composed Route Experiment

- Created: `2026-07-10T07:11:23.589359+00:00`
- Source commit: `75bd6365c9bee88cd9b17880b96d726633b7988e`
- Safety: Offline exact-composed route experiment. It does not call SAIR/network APIs and does not make a live submission.
- Target route: `24T24134|r=8` via `tower_6x4`
- Executable generator: `tower_6x4_exact_quartic_inner_v1`
- Structure preservation: `exact h(q(x)) support with deg(h)=6 and quartic q(x)=x^4-s*x^2`
- Trials attempted: `5`
- Local-valid candidates stored: `5`
- Local-valid candidates evaluated: `5`
- Local-valid overflow not stored: `0`
- Adaptive target-compatible candidates: `0`
- Any valuable-target survivor candidates: `5`
- Known-submission rejections: `0`
- Live submission recommended now: `False`

## Candidate Rows

| rank | hash | height | usable primes | target label retained | target pair valuable | any valuable pairs | recommendation |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `d5aa43d6cb93` | 793585 | 5 | `False` | `False` | 1 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 2 | `aa10b2909f9f` | 793585 | 5 | `False` | `False` | 4 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 3 | `e84d801cab9f` | 793565 | 5 | `False` | `False` | 9 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 4 | `3e1b65cdb5a3` | 793585 | 5 | `False` | `False` | 39 | `false_target_label_ruled_out_by_adaptive_evidence` |
| 5 | `f6e11fda4e7f` | 793585 | 5 | `False` | `False` | 6 | `false_target_label_ruled_out_by_adaptive_evidence` |

Compatibility here is necessary target-exclusion evidence only; it is not exact 24T label verification.
