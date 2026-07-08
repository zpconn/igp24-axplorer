# AXG Proposal Loop

- Model version: `AXG-1.4`
- Run id: `axg14_r20_pending_overlay`
- Candidate rows: 35
- Filtered rows: 18
- Rejected rows: 17
- Selected rows: 0
- Decision: `hold_no_submission`
- Recommendation reason: only_0_eligible_rows_below_min_4; only_0_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [], "submission_detail_complete": true}`
- Model-generated target-r survivors: `18`
- Model-generated eligible rows: `0`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"33465526667f9ca21a77d799": 3, "4f2ea644cc66bb89d89d0242": 2, "64f19fed392372573952bfad": 6, "99b6cb3c4c0d9ae3b90a6dbd": 2, "a8d377ad551d84fbd33d11d8": 1, "ab7b0d06e137df0f017aa075": 1, "ba9cec390cf5da49ae63e373": 1, "f29ba57c997c51c793139aa4": 2}}, "candidate_rows_by_source": {"model_generate": 35}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 18}}, "eligible_rows_by_source": {}, "model_generated_eligible_rows": 0, "model_generated_selected_rows": 0, "model_generated_target_r_survivor_rows": 18, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 10, "medium_mixed_support_gcd1": 8}}, "rejected_basin_rows_by_source": {"model_generate": 18}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 15, "crowded_mod_p_signature_hits=1": 5, "exact_crowded_basin_fingerprint_hits=1": 3, "exact_crowded_basin_fingerprint_hits=2": 7, "loose_crowded_basin_fingerprint_hits=2": 8, "model_basin_fingerprint_known_high_label_collapse=24T25000": 13, "model_template_family_known_high_label_collapse=24T25000": 18}}, "scored_rows_by_source": {"model_generate": 18}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {}, "target_r_survivor_rows_by_source": {"model_generate": 18}, "template_family_counts_by_source": {"model_generate": {"model:mixed:r20:dense_mixed_support_gcd1": 10, "model:mixed:r20:medium_mixed_support_gcd1": 8}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
