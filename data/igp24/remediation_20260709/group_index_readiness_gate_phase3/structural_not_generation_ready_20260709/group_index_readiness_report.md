# IGP24 Group Index Readiness Gate

- Created: `2026-07-10T00:41:05.461331+00:00`
- Source commit: `f4dafe65271f1a72ef5e4fc3cd58f43cf81d6866`
- Group index: `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_plus_historical_local_gap_v2/degree24_group_cycle_index.sqlite`
- Group index exists: `True`
- Target pairs: `25`
- Covered target labels: `25` / `25`
- Historical rows: `35`
- Structurally eligible routes: `125`
- Generation-ready routes: `0`
- Blocking reasons: `['no_executable_generation_ready_routes']`
- Ready for structural route review: `True`
- Ready for group-directed generation: `False`
- Live submission recommended now: `False`
- Safety: Read-only group-index readiness gate. It does not build groups, generate candidates, call external algebra systems or SAIR, or recommend live submission.

## Historical Containment

- Checked rows: `35`
- Failure count: `0`
- True-label containment: `1.0`

## Top Routes

| rank | pair | family | structural | generation-ready | blocks |
| ---: | --- | --- | --- | --- | --- |
| 1 | `24T22631|r=24` | `quartic_in_x6` | `True` | `False` | - |
| 2 | `24T22631|r=24` | `gx2_degree12_lift` | `True` | `False` | - |
| 3 | `24T22667|r=24` | `quartic_in_x6` | `True` | `False` | - |
| 4 | `24T22667|r=24` | `gx2_degree12_lift` | `True` | `False` | - |
| 5 | `24T19906|r=24` | `gx2_degree12_lift` | `True` | `False` | - |
| 6 | `24T22306|r=24` | `quartic_in_x6` | `True` | `False` | - |
| 7 | `24T22306|r=24` | `gx2_degree12_lift` | `True` | `False` | - |
| 8 | `24T23413|r=24` | `quartic_in_x6` | `True` | `False` | - |
| 9 | `24T23413|r=24` | `gx2_degree12_lift` | `True` | `False` | - |
| 10 | `24T24093|r=24` | `quartic_in_x6` | `True` | `False` | - |
| 11 | `24T24093|r=24` | `gx2_degree12_lift` | `True` | `False` | - |
| 12 | `24T22306|r=24` | `tower_6x4` | `True` | `False` | - |
| 13 | `24T22306|r=24` | `composition_8x3` | `True` | `False` | - |
| 14 | `24T22631|r=24` | `tower_6x4` | `True` | `False` | - |
| 15 | `24T22631|r=24` | `positive_quadratic_product` | `True` | `False` | - |
| 16 | `24T22667|r=24` | `tower_6x4` | `True` | `False` | - |
| 17 | `24T22667|r=24` | `positive_quadratic_product` | `True` | `False` | - |
| 18 | `24T23413|r=24` | `tower_6x4` | `True` | `False` | - |
| 19 | `24T24093|r=24` | `tower_6x4` | `True` | `False` | - |
| 20 | `24T24093|r=24` | `composition_8x3` | `True` | `False` | - |
| 21 | `24T19906|r=24` | `tower_6x4` | `True` | `False` | - |
| 22 | `24T19906|r=24` | `positive_quadratic_product` | `True` | `False` | - |
| 23 | `24T19906|r=24` | `composition_8x3` | `True` | `False` | - |
| 24 | `24T22306|r=24` | `positive_quadratic_product` | `True` | `False` | - |
| 25 | `24T22631|r=24` | `composition_8x3` | `True` | `False` | - |

Structural eligibility only means a route is not ruled out by the current group invariants.
Generation readiness additionally requires an executable target-bound generator, structure-preservation checks, instantiated parameters, and adaptive Frobenius review on generated outputs.
