# r24 Deterministic SAIR Submission

Created: 2026-07-09

## Summary

The 11-row deterministic r24 high-real packet was submitted to SAIR after
explicit user approval.

- Submission: `sub_55fba0a7253d4a72b8ab7a6e80d5cede`
- Batch: `igp24_batch_ffd919c6ea844af8`
- Submitted rows: 11
- Accepted rows: 11
- Failed rows: 0
- Final post-submit sync pending rows: 0

All 11 rows were accepted as `24T25000|r=24`.

## Timing Note

The immediate status poll saw 5 scoreable rows and 6 rows still waiting on
discriminant work. The later full sync completed cleanly and showed all 11
submitted rows scoreable.

Post-submit sync state:

- 24/24 submission details recovered
- 24/24 submission downloads recovered
- 208 total recovered submission rows
- 208 scoreable rows
- 0 pending rows
- 0 failed rows
- 0 unmatched rows

For this submitted packet, the final discriminant-source split was 5
`exact_nfdisc` rows and 6 `mixed_disc` rows.

## Interpretation

This was a valid packet, but not a useful new discovery. The anti-basin gate
thought the row fingerprints were clean locally, yet SAIR verified every row as
the known crowded pair `24T25000|r=24`.

The feedback artifact is:

`data/igp24/r24_deterministic_high_real_expansion_20260709/submission/r24_deterministic_sair_accepted_feedback_20260709.json`

Planner action: load this feedback by default and treat the submitted
`r24_high_real:*` templates and basin fingerprints as durable negative memory
unless the construction changes materially.

## Replay Gate

After wiring this feedback into the default planner path, the original 24-row
r24 deterministic queue was replayed. The replay selected 0 rows and marked all
24 candidates ineligible, primarily via
`template_family_known_high_label_collapse=24T25000` plus exact or loose
fingerprint hits.
