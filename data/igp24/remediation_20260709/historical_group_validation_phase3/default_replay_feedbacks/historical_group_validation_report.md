# IGP24 Historical Group-Validation Rows

- Created: `2026-07-09T22:36:00.828499+00:00`
- Source commit: `c312dc9dd5bf0c5187f7567be7c07f15fc2c4cbe`
- Feedback files: `7`
- Accepted rows seen: `41`
- Validation rows: `35`
- Skipped rows: `6`
- Skip reasons: `{'missing_modular_factorization_evidence': 6}`
- Labels: `{'24T24979': 6, '24T25000': 29}`
- Safety: Read-only historical group-validation row extractor. It does not call SAIR/network APIs, run GAP/Magma/PARI, generate candidates, or submit anything.

Rows in `historical_group_validation_rows.jsonl` have SAIR-verified labels joined to local modular factorization evidence. They are containment-test inputs, not exact verifier outputs.

## Per Feedback

| feedback | accepted | selected | validation | skipped |
| --- | ---: | ---: | ---: | ---: |
| `data/igp24/r8_score_followup_20260708/anti_collapse_gate/r8_score_followup_sair_accepted_feedback_20260708.json` | 4 | 4 | 4 | 0 |
| `data/igp24/r24_deterministic_high_real_expansion_20260709/submission/r24_deterministic_sair_accepted_feedback_20260709.json` | 11 | 11 | 6 | 5 |
| `data/igp24/axg16_conditioned_20260709/proposal_loop/axg16_anti_collapse_multir_gate_20260709/axg16_sair_accepted_feedback_20260709.json` | 7 | 7 | 7 | 0 |
| `data/igp24/axg17_score_aware_20260709/proposal_loop/axg17_score_aware_gate_20260709/axg17_sair_accepted_feedback_20260709.json` | 6 | 6 | 6 | 0 |
| `data/igp24/axg18_escape_20260709/proposal_loop/axg18_high_real_escape_combined_gate_20260709/axg18_sair_accepted_feedback_20260709.json` | 3 | 3 | 2 | 1 |
| `data/igp24/axg110_hash_exclusion_20260709/proposal_loop/axg110_hash_exclusion_spillover_gate_sparse_submode_freshsync_20260709/axg110_sair_accepted_feedback_20260709.json` | 4 | 4 | 4 | 0 |
| `data/igp24/axg112_pivot_20260709/proposal_loop/axg112_r12_pivot_combined_gate_composed_advisory_20260709/axg112_sair_accepted_feedback_20260709.json` | 6 | 6 | 6 | 0 |
