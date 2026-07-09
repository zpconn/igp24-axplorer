# AXG Proposal Loop

- Model version: `AXG-1.6`
- Run id: `axg16_anti_collapse_multir_gate_20260709`
- Candidate rows: 32
- Filtered rows: 29
- Rejected rows: 3
- Selected rows: 7
- Decision: `reviewed_packet_ready_for_dry_run`
- Recommendation reason: anti-basin gates passed
- Local packet ready: `True`
- Sync gate: `{"degraded_mode_summary": "24/24 details recovered; 24/24 downloads recovered", "download_complete": true, "full_submission_state_complete": true, "hold_reasons": [], "partial_sync": false, "pending_high_label_basin_collisions": {}, "pending_pair_counts": {}, "selected_exact_pair_pending_collisions": {}, "selected_pair_keys": [], "selected_r_values": [12, 20, 24], "submission_detail_complete": true}`
- Model-generated target-r survivors: `29`
- Model-generated eligible rows: `8`
- Source basin summary: `{"basin_fingerprint_counts_by_source": {"model_generate": {"0c64d09ca8a889c6cee1540d": 2, "16e91cf76e9f5a7b72e418e6": 1, "33465526667f9ca21a77d799": 1, "4f2ea644cc66bb89d89d0242": 1, "5488a4c10e30210d124495ff": 1, "5568f32b7eac61f4cca6045f": 1, "61f79676ed982c87d1ce4973": 2, "64f19fed392372573952bfad": 2, "6f180c06a96c257823a0b443": 1, "6f8f07fe7a66bdc7c4d0be58": 1, "74d091697e91e9e305a6e540": 1, "79cf4512c28f5b6f978c1920": 1, "898877151f3a305a2cca1864": 2, "93ccca84aa9fb2ba19ba9154": 2, "998602a5c3f403a4b2539f18": 1, "99b6cb3c4c0d9ae3b90a6dbd": 1, "ab7b0d06e137df0f017aa075": 1, "ba9cec390cf5da49ae63e373": 1, "c453631eee4dfc7ac0d55c84": 1, "c89fe9f39cae076364e172fe": 1, "cc3475ac1f4d27ff6fb155e8": 1, "d973d0eb231ca82cf8896650": 1, "f29ba57c997c51c793139aa4": 1, "fddbe6f0ff38c8629060a918": 1}}, "candidate_rows_by_source": {"model_generate": 32}, "classification_counts_by_source": {"model_generate": {"reject_or_hold_known_basin_risk": 21, "review_packet_candidate_loose_basin_match": 8}}, "eligible_rows_by_source": {"model_generate": 8}, "model_generated_eligible_rows": 8, "model_generated_selected_rows": 7, "model_generated_target_r_survivor_rows": 29, "perturbation_mode_counts_by_source": {"model_generate": {"dense_mixed_support_gcd1": 15, "medium_mixed_support_gcd1": 14}}, "rejected_basin_rows_by_source": {"model_generate": 21}, "risk_reason_counts_by_source": {"model_generate": {"accepted_hash_duplicate": 17, "basin_fingerprint_known_high_label_collapse=24T25000": 1, "loose_crowded_basin_fingerprint_hits=2": 29, "model_basin_fingerprint_known_high_label_collapse=24T25000": 1, "model_template_family_known_high_label_collapse=24T25000": 8, "template_family_known_high_label_collapse=24T25000": 8}}, "scored_rows_by_source": {"model_generate": 29}, "seed_bank_target_r_survivor_rows": 0, "selected_rows_by_source": {"model_generate": 7}, "target_r_survivor_rows_by_source": {"model_generate": 29}, "template_family_counts_by_source": {"model_generate": {"model:mixed:r12:dense_mixed_support_gcd1": 3, "model:mixed:r12:medium_mixed_support_gcd1": 2, "model:mixed:r16:dense_mixed_support_gcd1": 4, "model:mixed:r16:medium_mixed_support_gcd1": 4, "model:mixed:r20:dense_mixed_support_gcd1": 4, "model:mixed:r20:medium_mixed_support_gcd1": 4, "model:mixed:r24:dense_mixed_support_gcd1": 4, "model:mixed:r24:medium_mixed_support_gcd1": 4}}}`
- SAIR live submission: `false`

This run is a proposal-selection dry run. It does not submit raw GPU
samples or reviewed packets to SAIR.
