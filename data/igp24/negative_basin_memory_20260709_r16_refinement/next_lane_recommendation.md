# Next Lane Recommendation

Created: 2026-07-09

## Recommendation

Pursue bounded r24 high-real deterministic probing with
`positive_quadratic_product_plus_low_odd_perturbation`.

Do not submit during this goal. The tiny local probe produced a locally ready
4-row packet, but the latest SAIR sync is still partial, so the conservative
state is review-only.

## Evidence

- r16 model-mixed replay: 32 candidates, 0 eligible, 0 selected.
- r24 model-mixed replay: 44 candidates, 3 eligible, 3 selected, below the
  4-row packet gate and still carrying loose crowded-basin risk.
- r24 deterministic tiny probe: 8 candidates, 8 eligible, 4 selected, 0 risk
  reasons, 4 basin fingerprints, and 3 perturbation modes.
- Latest progress snapshot still has r24 as the largest remaining bucket:
  11,814 remaining signatures.

## Current Holds

- Hard stop: r16 `model:mixed:r16:{medium,dense}_mixed_support_gcd1` after
  the accepted `24T25000|r=16` collapse.
- Hard stop: r8 quartic-in-`x^6` odd off-core neighborhood after the accepted
  `24T25000|r=8` collapse.
- Hold: r20 high-real/AXG `24T25000` neighborhood until pending/scored evidence
  resolves.
- Refine: r24 model-mixed dense/medium support, because it is underfilled and
  still near crowded basins.

## Practical Next Step

After a complete sync, either review the tiny 4-row deterministic r24 packet
or run a slightly larger bounded deterministic r24 probe to build an 8-12 row
candidate pool with:

- per-mode caps,
- per-family caps,
- at least 4 distinct family-key fingerprints,
- exact local r24 validation,
- anti-basin replay against the default feedback memory,
- no live submission unless explicitly requested.
