# r24/r16 High-Real Refinement Decision

Created: 2026-07-08

## Decision

Status: dry-run packet ready, awaiting explicit live-submit approval.

The r16 lane cleared all local gates and passed dry-run validation. No live
SAIR submission was made.

## What Ran

- Refreshed git state: already up to date.
- Used latest complete local sync:
  `data/igp24/sair_sync_20260708_r8_followup_after_submit/`.
- `SAIR_API_KEY` was missing, so no live sync or live submit was attempted.
- Held r20 because `24T25000|r=20` still has 4 pending rows.
- Kept the stopped r8 quartic-in-x^6 lane stopped.
- Ran two bounded CUDA sample-export passes:
  - r24: 2400 steps, 2048 attempts, 89.150 s, avg GPU 73.372%.
  - r16: 2400 steps, 2048 attempts, 85.883 s, avg GPU 75.310%.

## Gate Results

| lane | candidates | eligible | selected | local packet? | reason |
| --- | ---: | ---: | ---: | --- | --- |
| r24 | 44 | 3 | 3 | no | below 4 selected/model rows and 4 basin fingerprints |
| r16 | 32 | 5 | 4 | yes | anti-basin gates passed |

The r16 selected packet has:

- 4 model-generated rows.
- 2 perturbation modes: `medium_mixed_support_gcd1`,
  `dense_mixed_support_gcd1`.
- 2 template families.
- 4 basin fingerprints.
- 4 mod-p signatures.
- 0 anti-basin risk reasons.
- No exact pending-pair collision in the complete local sync.
- All selected rows passed local exact filters.

## Dry Run

Dry-run validation output:
`data/igp24/r24_r16_high_real_refinement_20260708/r16_gate/r16_high_real_refinement_sair_dry_run.json`

Result: `ok=true`, `dry_run=true`, `polynomial_count=4`.

Packet coefficient file:
`data/igp24/r24_r16_high_real_refinement_20260708/r16_gate/anti_basin_candidate_coefficients.txt`

## Next

If the user approves live submission, submit only the r16 dry-runed coefficient
file, then poll and ingest feedback before any further generation. If that
packet collapses into crowded labels, keep r24 as the next high-real target and
slightly loosen the basin cap while adding lower-height high-real rows.
