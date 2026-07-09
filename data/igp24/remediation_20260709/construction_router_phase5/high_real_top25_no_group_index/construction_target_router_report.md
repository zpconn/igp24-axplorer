# IGP24 Construction Target Router

- Created: `2026-07-09T22:15:30.015065+00:00`
- Source commit: `1c435377bce8d5fb18843647b38f067df709558a`
- Score plan: `data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `False`
- Require group invariants: `True`
- Target pairs: `25`
- Routes: `125`
- Target group records found: `0`
- Generation-ready routes: `0`
- Blocking reasons: `{'missing_group_invariants': 125}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | ready | blocks | warnings |
| ---: | --- | --- | ---: | --- | --- | --- |
| 1 | `24T19906|r=24` | `quartic_in_x6` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 2 | `24T19906|r=24` | `gx2_degree12_lift` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 3 | `24T22306|r=24` | `quartic_in_x6` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 4 | `24T22306|r=24` | `gx2_degree12_lift` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 5 | `24T22631|r=24` | `quartic_in_x6` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 6 | `24T22631|r=24` | `gx2_degree12_lift` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 7 | `24T22667|r=24` | `quartic_in_x6` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 8 | `24T22667|r=24` | `gx2_degree12_lift` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 9 | `24T23413|r=24` | `quartic_in_x6` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 10 | `24T23413|r=24` | `gx2_degree12_lift` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 11 | `24T24093|r=24` | `quartic_in_x6` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 12 | `24T24093|r=24` | `gx2_degree12_lift` | 1448.491 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 13 | `24T19906|r=24` | `tower_6x4` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 14 | `24T19906|r=24` | `positive_quadratic_product` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 15 | `24T19906|r=24` | `composition_8x3` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T25000 |
| 16 | `24T22306|r=24` | `tower_6x4` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 17 | `24T22306|r=24` | `positive_quadratic_product` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 18 | `24T22306|r=24` | `composition_8x3` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T25000 |
| 19 | `24T22631|r=24` | `tower_6x4` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 20 | `24T22631|r=24` | `positive_quadratic_product` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 21 | `24T22631|r=24` | `composition_8x3` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T25000 |
| 22 | `24T22667|r=24` | `tower_6x4` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 23 | `24T22667|r=24` | `positive_quadratic_product` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 24 | `24T22667|r=24` | `composition_8x3` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T25000 |
| 25 | `24T23413|r=24` | `tower_6x4` | 1446.991 | `False` | missing_group_invariants | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |

## Interpretation

Routes blocked by `missing_group_invariants` are proxy routing rows only. They show which construction families would be plausible by real-root count and history, but they are not evidence that the family can hit the target 24T label.
