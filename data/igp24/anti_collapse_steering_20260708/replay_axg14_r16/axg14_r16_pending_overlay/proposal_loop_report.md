# AXG Proposal Loop

- Model version: `AXG-1.4`
- Run id: `axg14_r16_pending_overlay`
- Candidate rows: 40
- Filtered rows: 22
- Rejected rows: 18
- Selected rows: 2
- Decision: `hold_no_submission`
- Recommendation reason: only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; 2_selected_rows_have_risk_reasons; selected_rows_do_not_have_enough_basin_fingerprint_diversity
- Local packet ready: `False`
- Sync gate: `{"degraded_mode_summary": "20/20 details recovered; 20/20 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {"24T25000|r=20": 4}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16], "submission_detail_complete": true}`
- Model-generated target-r survivors: `22`
- Model-generated eligible rows: `4`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"0c64d09ca8a889c6cee1540d": 6, "210d2d77a1c941582da80776": 1, "2f422da111c7a8834d653c53": 5, "61f79676ed982c87d1ce4973": 6, "79c6dfeed8fdbb34d3cce557": 1, "7ad797632b96042402547322": 1, "8c83f5b2d7a9079da4f55404": 1, "f1baba7af5e7a2cfad301e62": 1}}, "candidate_rows_by_source": {"model_generate": 40}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 18, "review_packet_candidate_loose_basin_match": 4}}, "eligible_rows_by_source": {"model_generate": 4}, "model_generated_eligible_rows": 4, "model_generated_selected_rows": 2, "model_generated_target_r_survivor_rows": 22, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 6, "medium_mixed_support_gcd1": 16}}, "rejected_basin_rows_by_source": {"model_generate": 18}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 17, "exact_crowded_basin_fingerprint_hits=2": 2, "loose_crowded_basin_fingerprint_hits=2": 20}}, "scored_rows_by_source": {"model_generate": 22}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 2}, "target_r_survivor_rows_by_source": {"model_generate": 22}, "template_family_counts_by_source": {"model_generate": {"model:mixed:r16:dense_mixed_support_gcd1": 6, "model:mixed:r16:medium_mixed_support_gcd1": 16}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
