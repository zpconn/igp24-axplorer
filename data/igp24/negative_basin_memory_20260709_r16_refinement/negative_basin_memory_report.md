# IGP24 Negative-Basin Memory: r16 Refinement

Created: 2026-07-09

## Summary

The r16 high-real refinement packet `sub_997ed4ad0f75476b888b42bea2e3a3d0`
was accepted by SAIR, but all 4 rows landed in `24T25000|r=16`. The rows are
still pending discriminants, but the label feedback is enough to treat the
packet as a failed escape from a crowded/high-risk basin.

The planner now loads the r16 feedback artifact by default, alongside the
earlier r8 hard-stop feedback. Replaying the old r16 pool under this memory
produces 0 eligible rows, so the submitted model-mixed dense/medium support
packet shape is no longer recommended.

## New Hard Stop

- Pair: `24T25000|r=16`
- Source submission: `sub_997ed4ad0f75476b888b42bea2e3a3d0`
- Construction: `model_sample_export`
- Generation strategy: `mixed`
- Target conditioning: `r16`
- Template families:
  - `model:mixed:r16:medium_mixed_support_gcd1`
  - `model:mixed:r16:dense_mixed_support_gcd1`
- Basin fingerprints:
  - `4d91c3d0fe2fa1d3bebf04e0`
  - `6f8f07fe7a66bdc7c4d0be58`
  - `6034e5dd17ee25c1245534e5`
  - `25548a9429bf4bd396091d24`

Rule: do not widen this r16 model-mixed dense/medium support lane unless the
construction and label discriminator change materially.

## Sync Retry

The read-only SAIR sync retry completed in degraded mode:

- 23 submissions indexed
- 184 recovered rows
- 176 scoreable rows
- 8 pending rows
- 0 unmatched rows
- 20/23 submission details recovered
- 20/20 downloads recovered

The still-pending rows are 4 at `24T25000|r=16` and 4 at `24T25000|r=8`.
Three old submission-detail reads returned transient `IGP24_SERVICE_UNAVAILABLE`
responses, so live submission state remains partial.

## Gate Results

| Lane | Candidates | Eligible | Selected | Local packet | Submit now |
| --- | ---: | ---: | ---: | --- | --- |
| r16 model-mixed replay | 32 | 0 | 0 | no | no |
| r24 model-mixed replay | 44 | 3 | 3 | no | no |
| r24 tiny deterministic probe | 8 | 8 | 4 | yes | no |

The r24 model-mixed replay is cleaner than r16 but underfilled and still has
loose crowded-basin risk. The tiny deterministic r24 probe is the first lane in
this pass to clear the local 4-row anti-basin gate, but submission is held
because the current SAIR sync is partial and this goal forbids live submission.

## Decision

Best next lane: bounded r24 high-real deterministic probing from
`positive_quadratic_product_plus_low_odd_perturbation`, with odd-support and
root-set diversity, then review after a complete sync or explicit user approval.

Do not submit more of the r16 model-mixed dense/medium lane, and do not reopen
r20 until the pending `24T25000|r=20` history has stronger scored evidence.
