# Escape-Lane Scout

Created: 2026-07-09

## Summary

This pass pivoted away from the rejected deterministic r24 high-real quadratic
product lane and tested five bounded CPU-only construction/provenance lanes
against fresh SAIR state and accepted-feedback basin memory.

Fresh SAIR sync completed fully:

- 25,000 labels
- 47,834 remaining signatures
- 208 scoreable local submission rows
- 0 pending rows
- 0 unmatched rows
- 24/24 submission details and downloads recovered

Top remaining buckets are still r24, r16, r8, r12, and r20.

## Lane Results

| lane | trials | valid | raw selected | gate selected | decision |
| --- | ---: | ---: | ---: | ---: | --- |
| alt 4x6 | 220 | 0 | 0 | 0 | not enough valid rows |
| alt 8x3/3x8 | 260 | 3 | 3 | 0 | held by `24T24932` feedback |
| r20 linear-real | 160 | 88 | 10 | 0 | held by `24T25000` construction-family collapse |
| r24 tower odd-escape | 220 | 27 | 24 | 0 | held by `24T25000` construction-family collapse |
| r16 diversity | 220 | 48 | 24 | 10 | dry-run-ready |

The planner was updated so older accepted-feedback artifacts are loaded by
default and so r16/r20/r24 escape-lane provenance is visible as template
families and basin fingerprints.

## Ready Packet

Only the r16 diversity gate cleared:

- 24 candidates
- 24 eligible
- 10 selected
- 0 risk reasons
- 3 perturbation modes
- 3 template families
- 10 basin fingerprints
- 10 mod-p signatures
- no pending/sync collision hold

Dry-run passed:

- `ok=true`
- `polynomial_count=10`
- `body_bytes=1044`

Packet path:

`data/igp24/escape_lane_scout_20260709/gate_r16_diversity/anti_basin_candidate_coefficients.txt`

No live SAIR submission was made.

## Decision

The best next action is to ask for explicit approval to submit the 10-row r16
diversity packet. Do not submit the r20 linear-real, r24 tower odd-escape, or
alt-composition packets from this scout.
