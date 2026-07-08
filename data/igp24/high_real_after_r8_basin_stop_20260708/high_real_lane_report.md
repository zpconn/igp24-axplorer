# High-Real Lane After R8 Basin Stop

## Decision

No submission and no SAIR dry-run now.

The r8 stopped lane remains stopped. The best next refinement is to stay with
a materially different high-real model-sample lane, primarily r24, and generate
more provenance-diverse rows before any packet is considered.

## Refresh State

- `git pull --ff-only`: already up to date.
- Initial worktree: clean.
- `SAIR_API_KEY`: not present in the environment.
- Sync source used:
  `data/igp24/sair_sync_20260708_r8_followup_after_submit/`.
- Sync status: complete, not partial.
- Pending rows:
  - `24T25000|r=8`: 4.
  - `24T25000|r=20`: 4.

## Lane Comparison

| lane | candidates | eligible | selected | local ready | final status |
| --- | ---: | ---: | ---: | --- | --- |
| r24 model sample export | 39 | 2 | 2 | false | held: underfilled and not diverse enough |
| r16 model sample export | 40 | 5 | 3 | false | held: one row short and only 3 basin fingerprints |
| r20 model sample export | 35 | 7 | 4 | true | held: pending `24T25000|r=20` collision risk |

## What Passed

- The evaluated lanes are materially different from the stopped r8 lane:
  `model_sample_export` rows with mixed support, not quartic-in-`x^6` r8
  follow-up rows.
- The stopped `r8_quartic_lift_score_followup` lane was not re-enabled.
- Candidate rows included useful provenance: construction family, target r,
  template family, perturbation mode, support pattern/gcd, basin fingerprint,
  mod-p signature when sampled, and source lineage.
- Local exact filters passed for all 9 selected rows across r24/r16/r20:
  25 integer coefficients, monic degree 24, nonzero constant, coefficient gcd
  1, target real-root count, squarefree, irreducible, and local-valid status.
- The sync gate saw the current pending rows and correctly blocked r20.

## What Failed

r24 is the preferred strategic bucket, but the current AXG-1.4 pool only gives
2 selected rows. Both selected rows are `medium_mixed_support_gcd1`, so the
packet fails the minimum four-row, four-model-row, two-mode, two-template, and
four-basin gates.

r16 is closer: it has 5 eligible rows and 3 selected rows across two modes and
two templates, but still misses the four-row/four-basin gate.

r20 locally passes the packet shape with 4 selected model-generated rows across
two modes, two template families, and four basin fingerprints. It is held only
because the sync has 4 pending rows at `24T25000|r=20`, and this objective
explicitly avoids widening that basin before those rows resolve.

## Next Refinement

Use a short bounded generation/evaluation pass focused on r24 first, r16 second.
The generation target is not more of the same r24 medium-support rows; it needs
more support-pattern and template-family diversity:

- at least 4 model-generated selected rows,
- at least 2 perturbation modes,
- at least 2 template families,
- at least 4 basin fingerprints,
- no accepted-hash duplicates,
- no pending `24T25000|r=8` or `24T25000|r=20` collision,
- no r8 quartic-in-`x^6` follow-up provenance.

r20 should be revisited only after the pending `24T25000|r=20` rows resolve.
