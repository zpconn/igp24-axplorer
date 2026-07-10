# IGP24 Construction Target Router

- Created: `2026-07-10T03:26:11.424651+00:00`
- Source commit: `81fff4762aba34cd0096427ce6dab88f3a640fd9`
- Score plan: `data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `True`
- Require group invariants: `True`
- Target pairs: `5`
- Routes: `40`
- Target group records found: `5`
- Structurally eligible routes: `30`
- Executable-generator routes: `9`
- Generation-ready routes: `0`
- Blocking reasons: `{'unsupported_target_r': 10}`
- Generation-ready blockers: `{'adaptive_target_exclusion_not_run': 29, 'executable_generator_not_bound_to_target': 20, 'generated_outputs_not_validated': 29, 'generator_block_structure_not_matched_to_target': 1, 'generator_unsupported_target_r': 1, 'structure_preservation_not_verified': 20, 'target_parameters_not_instantiated': 20, 'unsupported_target_r': 10}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | structural | executable | generation-ready | blocks | gen blockers | warnings |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | `24T9993|r=8` | `quartic_in_x6` | 540.13007 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 2 | `24T9993|r=8` | `gx2_degree12_lift` | 540.13007 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 3 | `24T9993|r=8` | `tower_6x4` | 538.63007 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 4 | `24T9993|r=8` | `composition_8x3` | 538.63007 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 5 | `24T9993|r=8` | `composition_4x6` | 537.63007 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 6 | `24T9993|r=8` | `generic_sparse_random` | 516.63007 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 7 | `24T22770|r=12` | `gx2_degree12_lift` | 287.596259 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 8 | `24T22770|r=12` | `tower_6x4` | 286.096259 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 9 | `24T22770|r=12` | `composition_4x6` | 285.096259 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 10 | `24T22770|r=12` | `quartic_in_x6` | 279.596259 | `True` | `False` | `False` | - | generator_unsupported_target_r, generator_block_structure_not_matched_to_target | forced_block_structure_not_matched_to_target_record |
| 11 | `24T22770|r=12` | `composition_8x3` | 278.096259 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | forced_block_structure_not_matched_to_target_record |
| 12 | `24T22770|r=12` | `generic_sparse_random` | 268.596259 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 13 | `24T661|r=8` | `quartic_in_x6` | -32.795741 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 14 | `24T661|r=8` | `gx2_degree12_lift` | -32.795741 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 15 | `24T661|r=8` | `tower_6x4` | -33.295741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 16 | `24T661|r=8` | `composition_8x3` | -34.295741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 17 | `24T661|r=8` | `composition_4x6` | -34.295741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 18 | `24T661|r=8` | `generic_sparse_random` | -57.295741 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 19 | `24T1310|r=8` | `quartic_in_x6` | -66.931 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 20 | `24T1310|r=8` | `gx2_degree12_lift` | -66.931 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 21 | `24T1310|r=8` | `tower_6x4` | -68.431 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 22 | `24T1310|r=8` | `composition_8x3` | -68.431 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 23 | `24T1310|r=8` | `composition_4x6` | -69.431 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 24 | `24T1310|r=8` | `generic_sparse_random` | -91.431 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 25 | `24T657|r=8` | `quartic_in_x6` | -99.675881 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
