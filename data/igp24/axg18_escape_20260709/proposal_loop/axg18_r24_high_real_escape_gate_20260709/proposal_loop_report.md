# AXG Proposal Loop

- Model version: `AXG-1.8`
- Run id: `axg18_r24_high_real_escape_gate_20260709`
- Candidate rows: 6
- Filtered rows: 6
- Rejected rows: 0
- Selected rows: 0
- Decision: `hold_no_submission`
- Recommendation reason: only_0_eligible_rows_below_min_3; only_0_model_generated_rows_below_min_3; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "26/26 details recovered; 26/26 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
- Model-generated target-r survivors: `6`
- Model-generated eligible rows: `0`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"04d19bd97839513f0f23cd28": 1, "2f727619c2b7d722e9d9de06": 1, "65178bfdb9772813a579933f": 1, "774213898a5b360f86bc6ee2": 2, "c24cd13ac8ec01407dd0b6b4": 1}}, "candidate_rows_by_source": {"model_generate": 6}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 6}}, "eligible_rows_by_source": {}, "model_generated_eligible_rows": 0, "model_generated_selected_rows": 0, "model_generated_target_r_survivor_rows": 6, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 3, "medium_mixed_support_gcd1": 3}}, "rejected_basin_rows_by_source": {"model_generate": 6}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 6, "loose_crowded_basin_fingerprint_hits=4": 3, "loose_crowded_basin_fingerprint_hits=5": 3}}, "scored_rows_by_source": {"model_generate": 6}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {}, "target_r_survivor_rows_by_source": {"model_generate": 6}, "template_family_counts_by_source": {"model_generate": {"model:fixed_sparse_template:r24:dense_mixed_support_gcd1": 3, "model:fixed_sparse_template:r24:medium_mixed_support_gcd1": 3}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
