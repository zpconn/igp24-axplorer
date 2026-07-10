# IGP24 Construction Target Router

- Created: `2026-07-10T08:41:27.894108+00:00`
- Source commit: `a0060d0545344c2d70e191014ef9216aa0d33d04`
- Score plan: `data/igp24/remediation_20260709/score_economics_phase4/score_aware_target_plan.json`
- Group index provided: `True`
- Require group invariants: `True`
- Target pairs: `25`
- Routes: `200`
- Target group records found: `25`
- Structurally eligible routes: `175`
- Executable-generator routes: `72`
- Generation-ready routes: `0`
- Blocking reasons: `{'unsupported_target_r': 25}`
- Generation-ready blockers: `{'adaptive_target_exclusion_not_run': 147, 'executable_generator_not_bound_to_target': 75, 'generated_outputs_not_validated': 147, 'generator_block_structure_not_matched_to_target': 15, 'generator_unsupported_target_r': 25, 'structure_preservation_not_verified': 75, 'target_parameters_not_instantiated': 75, 'unsupported_target_r': 25}`
- Construction outcome blockers: `{}`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only target-to-construction router. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Live submission recommended now: `False`

## Top Routes

| rank | pair | family | combined score | structural | executable | stage | generation-ready | blocks | gen blockers | outcome blockers | warnings |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `24T24690|r=24` | `tower_6x4` | 942.441 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 2 | `24T24690|r=24` | `composition_8x3` | 942.441 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 3 | `24T24690|r=24` | `composition_4x6` | 941.441 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 4 | `24T12017|r=24` | `gx2_degree12_lift` | 940.941 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 5 | `24T12017|r=24` | `tower_6x4` | 939.441 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 6 | `24T12017|r=24` | `positive_quadratic_product` | 939.441 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 7 | `24T12017|r=24` | `composition_8x3` | 939.441 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 8 | `24T12017|r=24` | `composition_4x6` | 938.441 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 9 | `24T24690|r=24` | `positive_quadratic_product` | 937.441 | `True` | `False` | `structurally_eligible` | `False` | - | executable_generator_not_bound_to_target, structure_preservation_not_verified, target_parameters_not_instantiated, generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 10 | `24T6187|r=24` | `gx2_degree12_lift` | 937.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 11 | `24T7893|r=24` | `gx2_degree12_lift` | 937.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 12 | `24T8006|r=24` | `gx2_degree12_lift` | 937.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 13 | `24T10896|r=24` | `gx2_degree12_lift` | 937.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 14 | `24T13117|r=24` | `gx2_degree12_lift` | 937.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 15 | `24T10356|r=24` | `gx2_degree12_lift` | 936.641 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 16 | `24T5481|r=24` | `gx2_degree12_lift` | 936.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 17 | `24T6187|r=24` | `quartic_in_x6` | 936.091 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 18 | `24T7893|r=24` | `quartic_in_x6` | 936.091 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 19 | `24T8006|r=24` | `quartic_in_x6` | 936.091 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 20 | `24T10896|r=24` | `quartic_in_x6` | 936.091 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 21 | `24T11840|r=24` | `gx2_degree12_lift` | 936.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 22 | `24T13117|r=24` | `quartic_in_x6` | 936.091 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
| 23 | `24T13167|r=24` | `gx2_degree12_lift` | 936.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 24 | `24T13169|r=24` | `gx2_degree12_lift` | 936.091 | `True` | `True` | `executable_generator_available` | `False` | - | generated_outputs_not_validated, adaptive_target_exclusion_not_run | - | - |
| 25 | `24T20420|r=24` | `quartic_in_x6` | 936.091 | `True` | `False` | `structurally_eligible` | `False` | - | generator_unsupported_target_r | - | - |
