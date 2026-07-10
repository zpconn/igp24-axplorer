# IGP24 Construction Target Router

- Created: `2026-07-10T08:41:27.839734+00:00`
- Source commit: `a0060d0545344c2d70e191014ef9216aa0d33d04`
- Score plan: `data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `True`
- Require group invariants: `True`
- Target pairs: `30`
- Routes: `240`
- Target group records found: `30`
- Structurally eligible routes: `210`
- Executable-generator routes: `74`
- Generation-ready routes: `0`
- Blocking reasons: `{'unsupported_target_r': 30}`
- Generation-ready blockers: `{'adaptive_target_exclusion_not_run': 164, 'executable_generator_not_bound_to_target': 90, 'generated_outputs_not_validated': 164, 'generator_block_structure_not_matched_to_target': 21, 'generator_unsupported_target_r': 30, 'structure_preservation_not_verified': 90, 'target_parameters_not_instantiated': 90, 'unsupported_target_r': 30}`
- Construction outcome blockers: `{}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | structural | executable | stage | generation-ready | blocks | gen blockers | outcome blockers | warnings |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `24T22631|r=24` | `quartic_in_x6` | 1476.241 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 2 | `24T22631|r=24` | `gx2_degree12_lift` | 1476.241 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 3 | `24T22667|r=24` | `quartic_in_x6` | 1476.241 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 4 | `24T22667|r=24` | `gx2_degree12_lift` | 1476.241 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 5 | `24T19906|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 6 | `24T22306|r=24` | `quartic_in_x6` | 1475.241 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 7 | `24T22306|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 8 | `24T23413|r=24` | `quartic_in_x6` | 1475.241 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 9 | `24T23413|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 10 | `24T24093|r=24` | `quartic_in_x6` | 1475.241 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 11 | `24T24093|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 12 | `24T22306|r=24` | `tower_6x4` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 13 | `24T22306|r=24` | `composition_8x3` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 14 | `24T22631|r=24` | `tower_6x4` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 15 | `24T22631|r=24` | `positive_quadratic_product` | 1474.741 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 16 | `24T22667|r=24` | `tower_6x4` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 17 | `24T22667|r=24` | `positive_quadratic_product` | 1474.741 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 18 | `24T23413|r=24` | `tower_6x4` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 19 | `24T24093|r=24` | `tower_6x4` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 20 | `24T24093|r=24` | `composition_8x3` | 1474.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 21 | `24T19906|r=24` | `tower_6x4` | 1473.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 22 | `24T19906|r=24` | `positive_quadratic_product` | 1473.741 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 23 | `24T19906|r=24` | `composition_8x3` | 1473.741 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 24 | `24T22306|r=24` | `positive_quadratic_product` | 1473.741 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 25 | `24T22306|r=24` | `composition_4x6` | 1473.741 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
