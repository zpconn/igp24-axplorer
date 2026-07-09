# AXG Proposal Loop

- Model version: `AXG-1.10`
- Run id: `axg110_r8_sparse_hash_exclusion_gate_20260709`
- Candidate rows: 12
- Filtered rows: 1
- Rejected rows: 11
- Selected rows: 1
- Decision: `hold_no_submission`
- Recommendation reason: only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "27/27 details recovered; 27/27 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [8], "submission_detail_complete": true}`
- Model-generated target-r survivors: `1`
- Model-generated eligible rows: `1`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"b10cb08dc87f31df5df4c0b7": 1}}, "candidate_rows_by_source": {"model_generate": 12}, "classification_counts_by_source": {"model_generate": {"review_packet_candidate_loose_basin_match": 1}}, "eligible_rows_by_source": {"model_generate": 1}, "model_generated_eligible_rows": 1, "model_generated_selected_rows": 1, "model_generated_target_r_survivor_rows": 1, "perturbation_mode_counts_by_source": {"model_generate": {"sparse_mixed_support_gcd1": 1}}, "rejected_basin_rows_by_source": {}, "risk_reason_counts_by_source": {"model_generate": {"crowded_mod_p_signature_hits=1": 1, "loose_crowded_basin_fingerprint_hits=1": 1}}, "scored_rows_by_source": {"model_generate": 1}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 1}, "target_r_survivor_rows_by_source": {"model_generate": 1}, "template_family_counts_by_source": {"model_generate": {"model:sparse:r8:sparse_mixed_support_gcd1": 1}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
