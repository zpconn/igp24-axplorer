# AXG Proposal Loop

- Model version: `AXG-1.3`
- Run id: `axg13_r24_pending_overlay`
- Candidate rows: 91
- Filtered rows: 39
- Rejected rows: 52
- Selected rows: 1
- Decision: `hold_no_submission`
- Recommendation reason: only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity; 1_selected_rows_have_unknown_perturbation_mode; 1_selected_rows_have_unknown_template_family; 1_selected_rows_have_unknown_basin_fingerprint
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [24], "submission_detail_complete": true}`
- Model-generated target-r survivors: `39`
- Model-generated eligible rows: `1`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"unknown": 39}}, "candidate_rows_by_source": {"model_generate": 91}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 38, "strong_packet_candidate": 1}}, "eligible_rows_by_source": {"model_generate": 1}, "model_generated_eligible_rows": 1, "model_generated_selected_rows": 1, "model_generated_target_r_survivor_rows": 39, "perturbation_mode_counts_by_source": {"model_generate": {"unknown": 39}}, "rejected_basin_rows_by_source": {"model_generate": 38}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 37, "crowded_mod_p_signature_hits=1": 5, "even_support_g_x_squared_like": 10, "support_gcd_not_one": 10}}, "scored_rows_by_source": {"model_generate": 39}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 1}, "target_r_survivor_rows_by_source": {"model_generate": 39}, "template_family_counts_by_source": {"model_generate": {"unknown": 39}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
