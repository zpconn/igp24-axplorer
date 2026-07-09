# AXG Proposal Loop

- Model version: `AXG-1.12`
- Run id: `axg112_r12_pivot_combined_gate_20260709`
- Candidate rows: 40
- Filtered rows: 21
- Rejected rows: 19
- Selected rows: 0
- Decision: `hold_no_submission`
- Recommendation reason: only_0_eligible_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "28/28 details recovered; 28/28 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
- Model-generated target-r survivors: `9`
- Model-generated eligible rows: `0`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"44fb30adf0cde4349f192384": 1, "4740d0179cd141508d41d6f1": 1, "4ba1d20465192461dc3a7380": 1, "4e9c1c354ccb7b59df5cf7e9": 1, "cf60e8782569461cdebebd1d": 2, "e28f0e56856d746182eabafa": 2, "f72dd60091e6003c43527d51": 1}, "unknown": {"unknown": 12}}, "candidate_rows_by_source": {"model_generate": 28, "unknown": 12}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 9}, "unknown": {"reject_or_hold_known_basin_risk": 12}}, "eligible_rows_by_source": {}, "model_generated_eligible_rows": 0, "model_generated_selected_rows": 0, "model_generated_target_r_survivor_rows": 9, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 3, "even_support_g_x2_like": 5, "medium_mixed_support_gcd1": 1}, "unknown": {"unknown": 12}}, "rejected_basin_rows_by_source": {"model_generate": 9, "unknown": 12}, "risk_reason_counts_by_source": {"model_generate": {"even_support_g_x_squared_like": 5, "loose_crowded_basin_fingerprint_hits=4": 1, "loose_crowded_basin_fingerprint_hits=5": 3, "model_mixed_high_real_24T25000_collapse_pattern:r12:dense_mixed_support_gcd1": 3, "model_mixed_high_real_24T25000_collapse_pattern:r12:medium_mixed_support_gcd1": 1, "support_gcd_not_one": 5}, "unknown": {"even_support_g_x_squared_like": 12, "support_gcd_not_one": 12}}, "scored_rows_by_source": {"model_generate": 9, "unknown": 12}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {}, "target_r_survivor_rows_by_source": {"model_generate": 9, "unknown": 12}, "template_family_counts_by_source": {"model_generate": {"model:mixed:r12:dense_mixed_support_gcd1": 3, "model:mixed:r12:even_support_like": 5, "model:mixed:r12:medium_mixed_support_gcd1": 1}, "unknown": {"unknown": 12}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
