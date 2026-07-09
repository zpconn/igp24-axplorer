# AXG Proposal Loop

- Model version: `AXG-1.9`
- Run id: `axg19_r8_sparse_escape_gate_20260709`
- Candidate rows: 8
- Filtered rows: 6
- Rejected rows: 2
- Selected rows: 0
- Decision: `hold_no_submission`
- Recommendation reason: only_0_eligible_rows_below_min_4; only_0_model_generated_rows_below_min_4; selected_rows_do_not_have_min_perturbation_mode_count_2; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "27/27 details recovered; 27/27 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
- Model-generated target-r survivors: `6`
- Model-generated eligible rows: `0`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"30339275e4ef10237355407c": 2, "32f4cdb4e4b8f532eaca81ea": 1, "5216e5713960bf2b7b9d9e7c": 1, "6b6e9df34420768b37ef5b9c": 1, "bbbf85148f934725cfd759cd": 1}}, "candidate_rows_by_source": {"model_generate": 8}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 6}}, "eligible_rows_by_source": {}, "model_generated_eligible_rows": 0, "model_generated_selected_rows": 0, "model_generated_target_r_survivor_rows": 6, "perturbation_mode_counts_by_source": {"model_generate": {"sparse_mixed_support_gcd1": 6}}, "rejected_basin_rows_by_source": {"model_generate": 6}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 6, "crowded_mod_p_signature_hits=1": 1, "loose_crowded_basin_fingerprint_hits=1": 6}}, "scored_rows_by_source": {"model_generate": 6}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {}, "target_r_survivor_rows_by_source": {"model_generate": 6}, "template_family_counts_by_source": {"model_generate": {"model:sparse:r8:sparse_mixed_support_gcd1": 6}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
