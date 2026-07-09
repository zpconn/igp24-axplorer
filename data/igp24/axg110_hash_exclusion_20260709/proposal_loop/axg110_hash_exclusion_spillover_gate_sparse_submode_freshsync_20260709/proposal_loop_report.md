# AXG Proposal Loop

- Model version: `AXG-1.10`
- Run id: `axg110_hash_exclusion_spillover_gate_sparse_submode_freshsync_20260709`
- Candidate rows: 15
- Filtered rows: 8
- Rejected rows: 7
- Selected rows: 4
- Decision: `reviewed_packet_ready_for_dry_run`
- Recommendation reason: anti-basin gates passed
- Local packet ready: `True`
- Sync gate: `{"degraded_mode_summary": "27/27 details recovered; 27/27 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [4, 8], "submission_detail_complete": true}`
- Model-generated target-r survivors: `8`
- Model-generated eligible rows: `6`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"30339275e4ef10237355407c": 1, "308ea5d9d8285254af71724c": 1, "5c5866cec8d715a2015a936a": 1, "620edad428a0fb09b5e104be": 2, "6bd567da12943cddf7168273": 1, "b10cb08dc87f31df5df4c0b7": 1, "b7b2aac9b4c44c1b2b049769": 1}}, "candidate_rows_by_source": {"model_generate": 15}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 2, "strong_packet_candidate": 6}}, "eligible_rows_by_source": {"model_generate": 6}, "model_generated_eligible_rows": 6, "model_generated_selected_rows": 4, "model_generated_target_r_survivor_rows": 8, "perturbation_mode_counts_by_source": {"model_generate": {"sparse_odd_pair_gap2_support_gcd1": 1, "sparse_odd_pair_gap4_support_gcd1": 1, "sparse_odd_pair_gap6_support_gcd1": 1, "sparse_odd_single_e11_support_gcd1": 4, "sparse_odd_single_e13_support_gcd1": 1}}, "rejected_basin_rows_by_source": {"model_generate": 2}, "risk_reason_counts_by_source": {"model_generate": {"crowded_mod_p_signature_hits=1": 1, "real_root_count_not_target": 2}}, "scored_rows_by_source": {"model_generate": 8}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 4}, "target_r_survivor_rows_by_source": {"model_generate": 8}, "template_family_counts_by_source": {"model_generate": {"model:sparse:r12:sparse_mixed_support_gcd1": 3, "model:sparse:r8:sparse_mixed_support_gcd1": 5}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
