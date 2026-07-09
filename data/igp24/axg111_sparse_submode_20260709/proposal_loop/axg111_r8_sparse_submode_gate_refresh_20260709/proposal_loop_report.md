# AXG Proposal Loop

- Model version: `AXG-1.11`
- Run id: `axg111_r8_sparse_submode_gate_refresh_20260709`
- Candidate rows: 12
- Filtered rows: 4
- Rejected rows: 8
- Selected rows: 1
- Decision: `hold_no_submission`
- Recommendation reason: only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "27/27 details recovered; 27/27 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [6], "submission_detail_complete": true}`
- Model-generated target-r survivors: `4`
- Model-generated eligible rows: `1`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"5982ec2d4d72617aa3624cb5": 2, "9ef607f0f883c102333f1b9a": 1, "f354addebc98b7484454ad1c": 1}}, "candidate_rows_by_source": {"model_generate": 12}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 3, "review_packet_candidate_loose_basin_match": 1}}, "eligible_rows_by_source": {"model_generate": 1}, "model_generated_eligible_rows": 1, "model_generated_selected_rows": 1, "model_generated_target_r_survivor_rows": 4, "perturbation_mode_counts_by_source": {"model_generate": {"sparse_odd_pair_gap2_support_gcd1": 2, "sparse_odd_pair_gap4_support_gcd1": 1, "sparse_odd_single_e11_support_gcd1": 1}}, "rejected_basin_rows_by_source": {"model_generate": 3}, "risk_reason_counts_by_source": {"model_generate": {"crowded_mod_p_signature_hits=2": 2, "exact_crowded_basin_fingerprint_hits=1": 2, "loose_crowded_basin_fingerprint_hits=1": 1, "loose_crowded_basin_fingerprint_hits=2": 1, "model_template_family_known_high_label_collapse=24T25000": 3, "template_family_known_high_label_collapse=24T25000": 3}}, "scored_rows_by_source": {"model_generate": 4}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 1}, "target_r_survivor_rows_by_source": {"model_generate": 4}, "template_family_counts_by_source": {"model_generate": {"model:sparse:r8:sparse_mixed_support_gcd1": 4}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
