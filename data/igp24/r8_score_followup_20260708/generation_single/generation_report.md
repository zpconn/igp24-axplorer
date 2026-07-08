# r8 Score-Followup Generation

- Source signal pair: `24T9993|r=8`
- Templates: `["four_positive_fibers_e", "four_positive_fibers_f"]`
- Trials run: `180`
- Accepted exact r8 rows: `0`
- Rejection counts: `{"reducible_over_q": 124, "support_profile_rejected": 56}`
- Accepted templates: `{}`
- Accepted perturbation modes: `{}`

## Outputs
- candidates_jsonl: `data/igp24/r8_score_followup_20260708/generation_single/generated_candidates.jsonl`
- rejected_jsonl: `data/igp24/r8_score_followup_20260708/generation_single/generated_rejected.jsonl`
- summary_json: `data/igp24/r8_score_followup_20260708/generation_single/generation_summary.json`
- report_md: `data/igp24/r8_score_followup_20260708/generation_single/generation_report.md`

This generator performs local exact checks only and does not call SAIR.
