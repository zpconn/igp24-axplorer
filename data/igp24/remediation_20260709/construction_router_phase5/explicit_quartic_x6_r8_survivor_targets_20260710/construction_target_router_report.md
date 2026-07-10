# IGP24 Construction Target Router

- Created: `2026-07-10T03:58:48.562515+00:00`
- Source commit: `75d34b753fb22df8f2e9dcebaa8c492c672f25a2`
- Score plan: `data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `True`
- Require group invariants: `True`
- Target pairs: `4`
- Routes: `32`
- Target group records found: `4`
- Structurally eligible routes: `24`
- Executable-generator routes: `4`
- Generation-ready routes: `0`
- Blocking reasons: `{'unsupported_target_r': 8}`
- Generation-ready blockers: `{'adaptive_target_exclusion_not_run': 20, 'executable_generator_not_bound_to_target': 16, 'generated_outputs_not_validated': 20, 'generator_block_structure_not_matched_to_target': 4, 'structure_preservation_not_verified': 16, 'target_parameters_not_instantiated': 16, 'unsupported_target_r': 8}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | structural | executable | generation-ready | blocks | gen blockers | warnings |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | `24T24134|r=8` | `quartic_in_x6` | 789.5 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 2 | `24T24134|r=8` | `tower_6x4` | 788.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 3 | `24T24134|r=8` | `composition_8x3` | 788.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 4 | `24T24134|r=8` | `composition_4x6` | 787.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 5 | `24T24134|r=8` | `gx2_degree12_lift` | 781.5 | `True` | `False` | `False` | - | generator_block_structure_not_matched_to_target | forced_block_structure_not_matched_to_target_record |
| 6 | `24T24134|r=8` | `generic_sparse_random` | 766.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 7 | `24T24135|r=8` | `quartic_in_x6` | 534.5 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 8 | `24T24135|r=8` | `tower_6x4` | 533.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 9 | `24T24135|r=8` | `composition_8x3` | 533.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 10 | `24T24135|r=8` | `composition_4x6` | 532.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 11 | `24T24908|r=8` | `quartic_in_x6` | 530.0 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 12 | `24T24908|r=8` | `tower_6x4` | 528.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 13 | `24T24908|r=8` | `composition_4x6` | 527.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 14 | `24T24135|r=8` | `gx2_degree12_lift` | 526.5 | `True` | `False` | `False` | - | generator_block_structure_not_matched_to_target | forced_block_structure_not_matched_to_target_record |
| 15 | `24T24908|r=8` | `gx2_degree12_lift` | 522.0 | `True` | `False` | `False` | - | generator_block_structure_not_matched_to_target | forced_block_structure_not_matched_to_target_record |
| 16 | `24T24908|r=8` | `composition_8x3` | 520.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | forced_block_structure_not_matched_to_target_record |
| 17 | `24T24135|r=8` | `generic_sparse_random` | 511.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 18 | `24T24908|r=8` | `generic_sparse_random` | 511.0 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 19 | `24T24529|r=8` | `quartic_in_x6` | 407.0 | `True` | `True` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 20 | `24T24529|r=8` | `tower_6x4` | 405.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 21 | `24T24529|r=8` | `composition_8x3` | 405.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 22 | `24T24529|r=8` | `composition_4x6` | 404.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - |
| 23 | `24T24529|r=8` | `gx2_degree12_lift` | 399.0 | `True` | `False` | `False` | - | generator_block_structure_not_matched_to_target | forced_block_structure_not_matched_to_target_record |
| 24 | `24T24529|r=8` | `generic_sparse_random` | 383.5 | `True` | `False` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | imprimitive_target_without_declared_block_structure |
| 25 | `24T24134|r=8` | `positive_quadratic_product` | 725.5 | `False` | `False` | `False` | unsupported_target_r | unsupported_target_r | unsupported_r=8 |
