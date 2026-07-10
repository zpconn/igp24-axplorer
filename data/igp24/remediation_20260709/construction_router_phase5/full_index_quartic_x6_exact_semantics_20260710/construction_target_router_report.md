# IGP24 Construction Target Router

- Created: `2026-07-10T03:26:11.364365+00:00`
- Source commit: `81fff4762aba34cd0096427ce6dab88f3a640fd9`
- Score plan: `data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `True`
- Require group invariants: `True`
- Target pairs: `25`
- Routes: `200`
- Target group records found: `25`
- Structurally eligible routes: `175`
- Executable-generator routes: `25`
- Generation-ready routes: `0`
- Blocking reasons: `{'unsupported_target_r': 25}`
- Generation-ready blockers: `{'adaptive_target_exclusion_not_run': 150, 'executable_generator_not_bound_to_target': 125, 'generated_outputs_not_validated': 150, 'generator_block_structure_not_matched_to_target': 4, 'generator_unsupported_target_r': 25, 'structure_preservation_not_verified': 125, 'target_parameters_not_instantiated': 125, 'unsupported_target_r': 25}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | structural | executable | generation-ready | blocks | gen blockers | warnings |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | `24T22631|r=24` | `quartic_in_x6` | 1476.241 | `True` | `False` | `False` | - | generator_unsupported_target_r | - |
| 2 | `24T22631|r=24` | `gx2_degree12_lift` | 1476.241 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 3 | `24T22667|r=24` | `quartic_in_x6` | 1476.241 | `True` | `False` | `False` | - | generator_unsupported_target_r | - |
| 4 | `24T22667|r=24` | `gx2_degree12_lift` | 1476.241 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 5 | `24T19906|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 6 | `24T22306|r=24` | `quartic_in_x6` | 1475.241 | `True` | `False` | `False` | - | generator_unsupported_target_r | - |
| 7 | `24T22306|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 8 | `24T23413|r=24` | `quartic_in_x6` | 1475.241 | `True` | `False` | `False` | - | generator_unsupported_target_r | - |
| 9 | `24T23413|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 10 | `24T24093|r=24` | `quartic_in_x6` | 1475.241 | `True` | `False` | `False` | - | generator_unsupported_target_r | - |
| 11 | `24T24093|r=24` | `gx2_degree12_lift` | 1475.241 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 12 | `24T22306|r=24` | `tower_6x4` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 13 | `24T22306|r=24` | `composition_8x3` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 14 | `24T22631|r=24` | `tower_6x4` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 15 | `24T22631|r=24` | `positive_quadratic_product` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 16 | `24T22667|r=24` | `tower_6x4` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 17 | `24T22667|r=24` | `positive_quadratic_product` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 18 | `24T23413|r=24` | `tower_6x4` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 19 | `24T24093|r=24` | `tower_6x4` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 20 | `24T24093|r=24` | `composition_8x3` | 1474.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 21 | `24T19906|r=24` | `tower_6x4` | 1473.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 22 | `24T19906|r=24` | `positive_quadratic_product` | 1473.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 23 | `24T19906|r=24` | `composition_8x3` | 1473.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 24 | `24T22306|r=24` | `positive_quadratic_product` | 1473.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 25 | `24T22306|r=24` | `composition_4x6` | 1473.741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
