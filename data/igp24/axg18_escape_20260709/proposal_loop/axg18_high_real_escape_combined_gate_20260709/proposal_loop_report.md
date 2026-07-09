# AXG Proposal Loop

- Model version: `AXG-1.8`
- Run id: `axg18_high_real_escape_combined_gate_20260709`
- Candidate rows: 36
- Filtered rows: 27
- Rejected rows: 9
- Selected rows: 3
- Decision: `reviewed_packet_ready_for_dry_run`
- Recommendation reason: anti-basin gates passed
- Local packet ready: `True`
- Sync gate: `{"degraded_mode_summary": "26/26 details recovered; 26/26 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [16, 20], "submission_detail_complete": true}`
- Model-generated target-r survivors: `27`
- Model-generated eligible rows: `7`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"04d19bd97839513f0f23cd28": 1, "06629a343fa918b0637084c0": 1, "1802fb18c64142738dc6cbcc": 2, "224d287c315d950419ca57cd": 2, "2a1f2f64702dcef315b5eeae": 4, "2f727619c2b7d722e9d9de06": 1, "6126234301726ebd10f5bca5": 2, "65178bfdb9772813a579933f": 1, "774213898a5b360f86bc6ee2": 2, "95e7003e8a82b2a736e86243": 2, "a7eaec28942819c713a49f57": 1, "b6a7dc352ca6aeab7117cbc2": 2, "bd8fc1ac2ff20cc657e62cac": 3, "c24cd13ac8ec01407dd0b6b4": 1, "ea79641e7f170d623817f823": 2}}, "candidate_rows_by_source": {"model_generate": 36}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 20, "review_packet_candidate_loose_basin_match": 7}}, "eligible_rows_by_source": {"model_generate": 7}, "model_generated_eligible_rows": 7, "model_generated_selected_rows": 3, "model_generated_target_r_survivor_rows": 27, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 15, "medium_mixed_support_gcd1": 12}}, "rejected_basin_rows_by_source": {"model_generate": 20}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 20, "loose_crowded_basin_fingerprint_hits=4": 12, "loose_crowded_basin_fingerprint_hits=5": 15}}, "scored_rows_by_source": {"model_generate": 27}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 3}, "target_r_survivor_rows_by_source": {"model_generate": 27}, "template_family_counts_by_source": {"model_generate": {"model:fixed_sparse_template:r16:dense_mixed_support_gcd1": 8, "model:fixed_sparse_template:r16:medium_mixed_support_gcd1": 5, "model:fixed_sparse_template:r20:dense_mixed_support_gcd1": 4, "model:fixed_sparse_template:r20:medium_mixed_support_gcd1": 4, "model:fixed_sparse_template:r24:dense_mixed_support_gcd1": 3, "model:fixed_sparse_template:r24:medium_mixed_support_gcd1": 3}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
