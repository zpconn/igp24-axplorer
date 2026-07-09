# AXG-1.6 SAIR Submission Report

Created: 2026-07-09

## Submission

- Submission id: `sub_11fc452b521044619796f738cc4b22c3`
- Batch id: `igp24_batch_8efa96c1afd6465a`
- Description: `AXG-1.6 anti-collapse multi-r packet 20260709`
- Source coefficients: `data/igp24/axg16_conditioned_20260709/proposal_loop/axg16_anti_collapse_multir_gate_20260709/selected_review_coefficients.txt`
- Queued rows: 7
- Rejected rows: 0

## Final SAIR Status

Post-submit polling completed with `partial_sync=false`, 25/25 submission
details recovered, 25/25 downloads recovered, 215/215 rows scoreable, 0
pending rows, 0 failed rows, and 0 unmatched rows.

All seven AXG-1.6 rows were accepted and became scoreable, but all seven
collapsed to the already crowded label `24T25000`.

| line | pair | status | disc source |
| ---: | --- | --- | --- |
| 1 | `24T25000|r=24` | scoreable | `exact_nfdisc` |
| 2 | `24T25000|r=24` | scoreable | `exact_nfdisc` |
| 3 | `24T25000|r=20` | scoreable | `exact_nfdisc` |
| 4 | `24T25000|r=12` | scoreable | `mixed_disc` |
| 5 | `24T25000|r=12` | scoreable | `exact_nfdisc` |
| 6 | `24T25000|r=20` | scoreable | `mixed_disc` |
| 7 | `24T25000|r=12` | scoreable | `mixed_disc` |

## Score Interpretation

The public submission-detail API exposes `scoreable`, `scoringStatus`,
`discSource`, and discriminant fields, but it does not expose row-level points
in the fetched response. The current label-progress API shows the relevant
`24T25000` signatures were already discovered and crowded:

- `24T25000|r=12`: team count changed from 27 before this submit to 28 after
  scoring.
- `24T25000|r=20`: team count stayed 25.
- `24T25000|r=24`: team count stayed 24.

Therefore this submission did not produce meaningful score improvement. It is
useful negative feedback: AXG-1.6's advisory-ready packet still collapsed to
the `24T25000` basin.

## Artifacts

- Live submit response: `sair_live_submit_response.json`
- Raw final submission detail: `sair_submission_detail_poll2.json`
- Final sync: `data/igp24/axg16_conditioned_20260709/sair_sync_after_submit_poll2/`
- Feedback artifact: `axg16_sair_accepted_feedback_20260709.json`
