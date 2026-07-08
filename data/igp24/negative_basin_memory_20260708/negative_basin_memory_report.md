# IGP24 Negative-Basin Memory: 2026-07-08

## Summary

The r8 score-followup packet `sub_87b36ed9fbe84cd4aa3c6075c0ce3cd7`
was accepted by SAIR, but all four rows landed in the crowded
`24T25000|r=8` basin. That makes the lane useful as negative evidence:
the `24T9993`-sourced r8 quartic-in-`x^6` follow-up using e/f templates
and `odd_pair_off_core` perturbations should be stopped unless the
construction changes materially.

No live submission, dry-run, GPU training, or model training was performed
during this pass.

## Current SAIR State

- Sync source:
  `data/igp24/sair_sync_20260708_r8_followup_after_submit/`
- Sync status: complete, not partial.
- Labels: 25,000.
- Submissions / rows: 22 submissions, 193 rows.
- Scoreable rows: 185.
- Pending rows: 8.
- Unmatched rows: 0.
- Remaining signatures: 49,462.

Pending rows are exactly:

| pair | pending rows | submission |
| --- | ---: | --- |
| `24T25000|r=8` | 4 | `sub_87b36ed9fbe84cd4aa3c6075c0ce3cd7` |
| `24T25000|r=20` | 4 | `sub_be2f16728afa4ff2aa03fbec2898d997` |

Top remaining real-root buckets from the complete sync:

| r | remaining |
| ---: | ---: |
| 24 | 11,817 |
| 16 | 10,159 |
| 8 | 6,313 |
| 12 | 6,300 |
| 20 | 5,408 |

## New Hard Constraint

High-severity constraint:
`stop_r8_score_followup_quartic_x6_24T25000_lane`.

Observed failed-diversity features:

- Resulting pair: `24T25000|r=8`.
- Construction family: `r8_quartic_lift_score_followup`.
- Decomposition pattern: `quartic_in_x6`.
- Source templates: `four_positive_fibers_e`, `four_positive_fibers_f`.
- Perturbation mode: `odd_pair_off_core`.
- Support gcd: 1.
- Template family counts:
  `r8_score_followup:four_positive_fibers_e:odd_pair_off_core` = 3,
  `r8_score_followup:four_positive_fibers_f:odd_pair_off_core` = 1.
- Basin fingerprints:
  `2a6951bcf67e969d4c75ca90`,
  `21c013281e9b30402d91f1b5`,
  `2f549efd5a79b1ba5cf422ef`,
  `836c81d12ffe0df2b8d42188`.

Rule: reject or heavily penalize nearby r8 quartic-in-`x^6` odd off-core
rows unless the construction family, decomposition pattern, or label
discriminator changes materially.

## Pending r20 Constraint

The `24T25000|r=20` rows are not a new hard failure yet because their
discriminants are still pending. They are, however, a high-risk pending
basin. Do not widen the r20 AXG/high-real 24T25000 neighborhood until
those rows resolve and any follow-up queue clears explicit anti-24T25000
gates.

## Replay Gate

The old r8 score-followup candidate pool was replayed through the updated
anti-basin planner:

- Candidates: 32.
- Eligible candidates: 0.
- Selected rows: 0.
- Recommended for SAIR packet: `false`.
- Status: `hold_no_submission`.

This proves the same stale r8 neighborhood no longer produces a packet
under current gates.

## Lane Decision

The score-aware planner now marks `r8_quartic_lift_score_followup` as
stopped by `stop_r8_score_followup_quartic_x6_24T25000_lane`.

Recommended next lane:
`materially_different_high_real_lane_after_basin_stop`.

Target buckets: `r=24`, `r=16`, `r=20`.

Reason: r8 still has score signal from `24T9993|r=8`, but the specific
quartic-in-`x^6` odd off-core follow-up neighborhood collapsed. The next
productive work is to pivot to high-real buckets with larger remaining
coverage and explicit anti-24T25000 constraints, or use a genuinely
different r8 construction only if it passes the same anti-basin replay gate.

Submission decision: no submission now. Any future packet must pass local
exact checks, score-aware planning, anti-basin replay, pending-pair checks,
and SAIR dry-run before live submission.
