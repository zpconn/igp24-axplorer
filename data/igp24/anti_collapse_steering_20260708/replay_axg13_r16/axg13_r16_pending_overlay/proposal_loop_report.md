# AXG Proposal Loop

- Model version: `AXG-1.3`
- Run id: `axg13_r16_pending_overlay`
- Candidate rows: 89
- Filtered rows: 44
- Rejected rows: 45
- Selected rows: 2
- Decision: `hold_no_submission`
- Recommendation reason: only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity; 2_selected_rows_have_unknown_perturbation_mode; 2_selected_rows_have_unknown_template_family; 2_selected_rows_have_unknown_basin_fingerprint
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16], "submission_detail_complete": true}`
- Model-generated target-r survivors: `44`
- Model-generated eligible rows: `7`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"unknown": 44}}, "candidate_rows_by_source": {"model_generate": 89}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 37, "strong_packet_candidate": 7}}, "eligible_rows_by_source": {"model_generate": 7}, "model_generated_eligible_rows": 7, "model_generated_selected_rows": 2, "model_generated_target_r_survivor_rows": 44, "perturbation_mode_counts_by_source": {"model_generate": {"unknown": 44}}, "rejected_basin_rows_by_source": {"model_generate": 37}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 29, "even_support_g_x_squared_like": 20, "support_gcd_not_one": 20}}, "scored_rows_by_source": {"model_generate": 44}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 2}, "target_r_survivor_rows_by_source": {"model_generate": 44}, "template_family_counts_by_source": {"model_generate": {"unknown": 44}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
