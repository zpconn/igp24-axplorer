# AXG Proposal Loop

- Model version: `AXG-1.8`
- Run id: `axg18_r16_high_real_escape_seed42116_gate_20260709`
- Candidate rows: 13
- Filtered rows: 6
- Rejected rows: 7
- Selected rows: 2
- Decision: `hold_no_submission`
- Recommendation reason: only_2_eligible_rows_below_min_3; only_2_model_generated_rows_below_min_3; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "26/26 details recovered; 26/26 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16], "submission_detail_complete": true}`
- Model-generated target-r survivors: `6`
- Model-generated eligible rows: `3`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"224d287c315d950419ca57cd": 1, "2a1f2f64702dcef315b5eeae": 2, "95e7003e8a82b2a736e86243": 1, "b6a7dc352ca6aeab7117cbc2": 1, "bd8fc1ac2ff20cc657e62cac": 1}}, "candidate_rows_by_source": {"model_generate": 13}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 3, "review_packet_candidate_loose_basin_match": 3}}, "eligible_rows_by_source": {"model_generate": 3}, "model_generated_eligible_rows": 3, "model_generated_selected_rows": 2, "model_generated_target_r_survivor_rows": 6, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 4, "medium_mixed_support_gcd1": 2}}, "rejected_basin_rows_by_source": {"model_generate": 3}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 3, "loose_crowded_basin_fingerprint_hits=4": 2, "loose_crowded_basin_fingerprint_hits=5": 4}}, "scored_rows_by_source": {"model_generate": 6}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 2}, "target_r_survivor_rows_by_source": {"model_generate": 6}, "template_family_counts_by_source": {"model_generate": {"model:fixed_sparse_template:r16:dense_mixed_support_gcd1": 4, "model:fixed_sparse_template:r16:medium_mixed_support_gcd1": 2}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
