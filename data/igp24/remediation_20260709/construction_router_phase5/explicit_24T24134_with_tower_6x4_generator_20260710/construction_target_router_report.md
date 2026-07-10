# IGP24 Construction Target Router

- Created: `2026-07-10T07:05:24.651706+00:00`
- Source commit: `75bd6365c9bee88cd9b17880b96d726633b7988e`
- Score plan: `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `True`
- Require group invariants: `True`
- Target pairs: `1`
- Routes: `8`
- Target group records found: `1`
- Structurally eligible routes: `6`
- Executable-generator routes: `3`
- Generation-ready routes: `0`
- Blocking reasons: `{'unsupported_target_r': 2}`
- Generation-ready blockers: `{'adaptive_target_exclusion_not_run': 5, 'exact_route_false_target_outcome': 1, 'executable_generator_not_bound_to_target': 2, 'generated_outputs_not_validated': 5, 'generator_block_structure_not_matched_to_target': 1, 'structure_preservation_not_verified': 2, 'target_parameters_not_instantiated': 2, 'unsupported_target_r': 2}`
- Construction outcome blockers: `{'exact_route_false_target_outcome': 1}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | structural | executable | stage | generation-ready | blocks | gen blockers | outcome blockers | warnings |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `24T24134|r=8` | `tower_6x4` | 788.0 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 2 | `24T24134|r=8` | `composition_8x3` | 788.0 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 3 | `24T24134|r=8` | `composition_4x6` | 787.0 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 4 | `24T24134|r=8` | `gx2_degree12_lift` | 781.5 | `True` | `False` | `structurally_eligible` | `False` | - | generator_block_structure_not_matched_to_target | - | forced_block_structure_not_matched_to_target_record |
| 5 | `24T24134|r=8` | `generic_sparse_random` | 766.0 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | imprimitive_target_without_declared_block_structure |
| 6 | `24T24134|r=8` | `quartic_in_x6` | 289.5 | `True` | `True` | `outcome_blocked` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run, exact_route_false_target_outcome | exact_route_false_target_outcome | - |
| 7 | `24T24134|r=8` | `positive_quadratic_product` | 725.5 | `False` | `False` | `blocked` | `False` | unsupported_target_r | unsupported_target_r | - | unsupported_r=8 |
| 8 | `24T24134|r=8` | `linear_real_product` | 709.5 | `False` | `False` | `blocked` | `False` | unsupported_target_r | unsupported_target_r | - | unsupported_r=8, imprimitive_target_without_declared_block_structure |
