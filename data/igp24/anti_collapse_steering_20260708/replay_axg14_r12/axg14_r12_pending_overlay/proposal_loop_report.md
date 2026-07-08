# AXG Proposal Loop

- Model version: `AXG-1.4`
- Run id: `axg14_r12_pending_overlay`
- Candidate rows: 22
- Filtered rows: 14
- Rejected rows: 8
- Selected rows: 1
- Decision: `hold_no_submission`
- Recommendation reason: only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; 1_selected_rows_have_risk_reasons; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [12], "submission_detail_complete": true}`
- Model-generated target-r survivors: `14`
- Model-generated eligible rows: `1`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"07e52322640a94691dc69079": 1, "16e91cf76e9f5a7b72e418e6": 2, "6f180c06a96c257823a0b443": 1, "79cf4512c28f5b6f978c1920": 8, "cc3475ac1f4d27ff6fb155e8": 1, "fddbe6f0ff38c8629060a918": 1}}, "candidate_rows_by_source": {"model_generate": 22}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 13, "review_packet_candidate_loose_basin_match": 1}}, "eligible_rows_by_source": {"model_generate": 1}, "model_generated_eligible_rows": 1, "model_generated_selected_rows": 1, "model_generated_target_r_survivor_rows": 14, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 11, "medium_mixed_support_gcd1": 3}}, "rejected_basin_rows_by_source": {"model_generate": 13}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 11, "crowded_mod_p_signature_hits=1": 10, "exact_crowded_basin_fingerprint_hits=1": 1, "exact_crowded_basin_fingerprint_hits=2": 2, "loose_crowded_basin_fingerprint_hits=2": 11}}, "scored_rows_by_source": {"model_generate": 14}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 1}, "target_r_survivor_rows_by_source": {"model_generate": 14}, "template_family_counts_by_source": {"model_generate": {"model:mixed:r12:dense_mixed_support_gcd1": 11, "model:mixed:r12:medium_mixed_support_gcd1": 3}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
