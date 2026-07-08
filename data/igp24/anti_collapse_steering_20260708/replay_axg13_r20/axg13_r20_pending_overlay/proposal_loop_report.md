# AXG Proposal Loop

- Model version: `AXG-1.3`
- Run id: `axg13_r20_pending_overlay`
- Candidate rows: 83
- Filtered rows: 38
- Rejected rows: 45
- Selected rows: 2
- Decision: `hold_no_submission`
- Recommendation reason: only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity; 2_selected_rows_have_unknown_perturbation_mode; 2_selected_rows_have_unknown_template_family; 2_selected_rows_have_unknown_basin_fingerprint; safe_to_review_only_after_pending_rows_resolve:24T25000|r=20=4
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": ["safe_to_review_only_after_pending_rows_resolve:24T25000|r=20=4"], "partial_sync": false, "pending_high_label_basin_collisions": {"24T25000|r=20": 4}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [20], "submission_detail_complete": true}`
- Model-generated target-r survivors: `38`
- Model-generated eligible rows: `27`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"unknown": 38}}, "candidate_rows_by_source": {"model_generate": 83}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 11, "strong_packet_candidate": 27}}, "eligible_rows_by_source": {"model_generate": 27}, "model_generated_eligible_rows": 27, "model_generated_selected_rows": 2, "model_generated_target_r_survivor_rows": 38, "perturbation_mode_counts_by_source": {"model_generate": {"unknown": 38}}, "rejected_basin_rows_by_source": {"model_generate": 11}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 11, "crowded_mod_p_signature_hits=1": 4}}, "scored_rows_by_source": {"model_generate": 38}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 2}, "target_r_survivor_rows_by_source": {"model_generate": 38}, "template_family_counts_by_source": {"model_generate": {"unknown": 38}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
