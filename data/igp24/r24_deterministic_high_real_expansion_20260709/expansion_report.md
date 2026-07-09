# R24 Deterministic High-Real Expansion

Created: 2026-07-09

## Summary

The deterministic r24 high-real lane improved materially over the tiny probe.
The expanded CPU-only run produced a review-ready 11-row packet with clean
anti-basin status. After explicit user approval, the packet was submitted to
SAIR as `sub_55fba0a7253d4a72b8ab7a6e80d5cede`. SAIR accepted all 11 rows, but
every row collapsed to the known `24T25000|r=24` basin.

## Sync

The read-only SAIR sync completed fully:

- 23/23 submission details recovered
- 23/23 downloads recovered
- 197 scoreable rows
- 0 pending rows
- 0 failed rows
- 0 unmatched rows

This clears the previous incomplete-state hold. The top remaining bucket is
still r24, with 11,535 remaining signatures.

## Probe

Command shape:

- script: `scripts/igp24_r24_high_real_probe.py`
- seed: `240710`
- max trials requested: 1000
- trials attempted: 252
- queue limit: 24
- per-family cap: 3
- construction: `positive_quadratic_product_plus_low_odd_perturbation`

Results:

- 217 valid local r24 candidates
- 24 queued rows
- mode balance: 8 single, 8 two-term, 8 three-term odd breaks
- rejects: 8 known/duplicate hashes, 27 reducible rows

## Gate

The anti-basin gate selected 11 rows:

- 24 candidates
- 24 eligible
- 11 selected
- 0 risk reasons
- 3 perturbation modes
- 3 template families
- 11 basin fingerprints
- 7 mod-p signatures
- complete sync, no pending collision hold

Status: `review_ready_not_submitted`.

The coefficient packet is:

`data/igp24/r24_deterministic_high_real_expansion_20260709/anti_basin_gate/anti_basin_candidate_coefficients.txt`

## Comparison To Tiny Probe

| Metric | Tiny | Expanded |
| --- | ---: | ---: |
| Candidate rows | 8 | 24 |
| Eligible rows | 8 | 24 |
| Selected rows | 4 | 11 |
| Perturbation modes | 3 | 3 |
| Basin fingerprints | 4 | 11 |
| Mod-p signatures | 4 | 7 |
| Risk count | 0 | 0 |
| Sync blocker | partial sync | none |

## Decision

This was the best current packet candidate before submission, but SAIR feedback
shows the local anti-basin signal was insufficient for this deterministic
construction. The next action is to use the accepted feedback as durable
negative memory and avoid widening this `r24_high_real:*` lane without a
material construction change.

Post-submit replay: after loading this feedback by default, the original
24-row queue replays with 0 eligible rows and 0 selected rows.
