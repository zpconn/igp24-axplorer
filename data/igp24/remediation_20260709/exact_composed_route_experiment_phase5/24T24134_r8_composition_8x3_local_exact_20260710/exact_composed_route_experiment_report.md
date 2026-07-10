# IGP24 Exact-Composed Route Experiment

- Created: `2026-07-10T06:37:12.113966+00:00`
- Source commit: `fed1e40ab44d74f3525d3fc801b998cfef36ca8b`
- Safety: Offline exact-composed route experiment. It does not call SAIR/network APIs and does not make a live submission.
- Target route: `24T24134|r=8` via `composition_8x3`
- Executable generator: `composition_8x3_exact_cubic_lift_v1`
- Structure preservation: `exact h(c(x)) support with deg(h)=8 and monic cubic c(x)`
- Trials attempted: `80`
- Local-valid candidates stored: `12`
- Local-valid candidates evaluated: `55`
- Local-valid overflow not stored: `43`
- Adaptive target-compatible candidates: `0`
- Any valuable-target survivor candidates: `0`
- Known-submission rejections: `0`
- Live submission recommended now: `False`

## Candidate Rows

| rank | hash | height | usable primes | target label retained | target pair valuable | any valuable pairs | recommendation |
| ---: | --- | ---: | ---: | --- | --- | ---: | --- |
| 1 | `a560edefd233` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 2 | `c761f68a0b28` | 3845349 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 3 | `d67b3eacbb7f` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 4 | `ac21bdfe4bbf` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 5 | `4ec581d227ec` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 6 | `27b9e678f4a6` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 7 | `4f31f591ffd1` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 8 | `f4fe7374fd97` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 9 | `81e7fcf1aae7` | 3845403 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 10 | `20e7ab87a545` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 11 | `2b7e8bc2cd84` | 3845376 | None | `None` | `None` | 0 | `false_missing_group_index` |
| 12 | `83a53da61b7e` | 3845385 | None | `None` | `None` | 0 | `false_missing_group_index` |

Compatibility here is necessary target-exclusion evidence only; it is not exact 24T label verification.
