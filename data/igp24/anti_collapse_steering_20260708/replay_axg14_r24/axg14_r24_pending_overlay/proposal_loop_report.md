# AXG Proposal Loop

- Model version: `AXG-1.4`
- Run id: `axg14_r24_pending_overlay`
- Candidate rows: 39
- Filtered rows: 28
- Rejected rows: 11
- Selected rows: 1
- Decision: `hold_no_submission`
- Recommendation reason: only_1_eligible_rows_below_min_4; only_1_model_generated_rows_below_min_4; 1_selected_rows_have_risk_reasons; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_mod_p_diversity; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [24], "submission_detail_complete": true}`
- Model-generated target-r survivors: `28`
- Model-generated eligible rows: `1`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"1d5261d1c012fd41aae493d6": 1, "1ef89bf9556019f197c060ad": 3, "5568f32b7eac61f4cca6045f": 8, "74d091697e91e9e305a6e540": 1, "886c747b4c88d216df1263c8": 1, "898877151f3a305a2cca1864": 7, "8c465ce1e11c4b961f7e3ada": 1, "9fb151d86cb8e93ac1badc54": 1, "b83111c9e1d3ca3b02f91145": 1, "b9888af191af9c42a1f76f50": 1, "d973d0eb231ca82cf8896650": 2, "ff9a8c3b2c85bd7cf2a8b7b4": 1}}, "candidate_rows_by_source": {"model_generate": 39}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 27, "review_packet_candidate_loose_basin_match": 1}}, "eligible_rows_by_source": {"model_generate": 1}, "model_generated_eligible_rows": 1, "model_generated_selected_rows": 1, "model_generated_target_r_survivor_rows": 28, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 10, "medium_mixed_support_gcd1": 18}}, "rejected_basin_rows_by_source": {"model_generate": 27}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 26, "crowded_mod_p_signature_hits=1": 5, "exact_crowded_basin_fingerprint_hits=2": 8, "loose_crowded_basin_fingerprint_hits=2": 20}}, "scored_rows_by_source": {"model_generate": 28}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 1}, "target_r_survivor_rows_by_source": {"model_generate": 28}, "template_family_counts_by_source": {"model_generate": {"model:mixed:r24:dense_mixed_support_gcd1": 10, "model:mixed:r24:medium_mixed_support_gcd1": 18}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
