# r8 Score-Followup Generation

- Source signal pair: `24T9993|r=8`
- Templates: `["four_positive_fibers_e", "four_positive_fibers_f"]`
- Trials run: `220`
- Accepted exact r8 rows: `18`
- Rejection counts: `{"duplicate": 1, "real_root_count_2": 9, "real_root_count_4": 28, "real_root_count_6": 16, "reducible_over_q": 111, "support_profile_rejected": 37}`
- Accepted templates: `{"four_positive_fibers_e": 11, "four_positive_fibers_f": 7}`
- Accepted perturbation modes: `{"odd_pair_off_core": 18}`

## Outputs
- candidates_jsonl: `data/igp24/r8_score_followup_20260708/generation_triple/generated_candidates.jsonl`
- rejected_jsonl: `data/igp24/r8_score_followup_20260708/generation_triple/generated_rejected.jsonl`
- summary_json: `data/igp24/r8_score_followup_20260708/generation_triple/generation_summary.json`
- report_md: `data/igp24/r8_score_followup_20260708/generation_triple/generation_report.md`

This generator performs local exact checks only and does not call SAIR.
