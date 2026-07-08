# r8 Score-Followup Generation

- Source signal pair: `24T9993|r=8`
- Templates: `["four_positive_fibers_e", "four_positive_fibers_f"]`
- Trials run: `240`
- Accepted exact r8 rows: `16`
- Rejection counts: `{"duplicate": 2, "real_root_count_2": 8, "real_root_count_4": 38, "real_root_count_6": 16, "reducible_over_q": 114, "support_profile_rejected": 46}`
- Accepted templates: `{"four_positive_fibers_e": 7, "four_positive_fibers_f": 9}`
- Accepted perturbation modes: `{"odd_pair_off_core": 16}`

## Outputs
- candidates_jsonl: `data/igp24/r8_score_followup_20260708/generation/generated_candidates.jsonl`
- rejected_jsonl: `data/igp24/r8_score_followup_20260708/generation/generated_rejected.jsonl`
- summary_json: `data/igp24/r8_score_followup_20260708/generation/generation_summary.json`
- report_md: `data/igp24/r8_score_followup_20260708/generation/generation_report.md`

This generator performs local exact checks only and does not call SAIR.
