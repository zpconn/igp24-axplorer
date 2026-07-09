# IGP24 Score-Aware Target Plan

## Snapshot

- Labels: 25000
- Pages: 5
- Published: True
- Generated: `2026-07-09T18:52:44Z` to `2026-07-09T18:52:52Z`
- Score snapshot rows: 20
- Sync submission rows: 0
- Partial sync: `False`
- Submission state complete: `True`
- Sync failing endpoint: `None`
- Basin constraints: 9

## Priority r Buckets

| rank | r | priority | remaining | category counts | top pair |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 24 | 1237.86 | 11390 | {"covered_or_crowded": 255, "lightly_solved_signature": 12774, "moderately_solved_signature": 581, "uncovered_signature": 11390} | 24T19906|r=24 |
| 2 | 16 | 1063.92 | 9735 | {"covered_or_crowded": 241, "lightly_solved_signature": 10755, "moderately_solved_signature": 690, "uncovered_signature": 9735} | 24T19906|r=16 |
| 3 | 8 | 956.82 | 5995 | {"covered_or_crowded": 489, "lightly_solved_signature": 15978, "moderately_solved_signature": 1093, "scored_pair_followup": 1, "uncovered_signature": 5995} | 24T19906|r=8 |
| 4 | 12 | 748.83 | 5925 | {"covered_or_crowded": 285, "lightly_solved_signature": 12959, "moderately_solved_signature": 764, "scored_pair_followup": 1, "uncovered_signature": 5925} | 24T19906|r=12 |
| 5 | 20 | 587.60 | 5182 | {"covered_or_crowded": 131, "lightly_solved_signature": 5145, "moderately_solved_signature": 394, "uncovered_signature": 5182} | 24T19906|r=20 |
| 6 | 0 | 539.14 | 3843 | {"covered_or_crowded": 1083, "lightly_solved_signature": 18347, "moderately_solved_signature": 1566, "uncovered_signature": 3843} | 24T19906|r=0 |
| 7 | 4 | 460.22 | 3355 | {"covered_or_crowded": 527, "lightly_solved_signature": 15223, "moderately_solved_signature": 952, "uncovered_signature": 3355} | 24T19906|r=4 |
| 8 | 6 | 108.33 | 471 | {"covered_or_crowded": 284, "lightly_solved_signature": 4860, "moderately_solved_signature": 389, "uncovered_signature": 471} | 24T19906|r=6 |
| 9 | 2 | 71.44 | 142 | {"covered_or_crowded": 374, "lightly_solved_signature": 4808, "moderately_solved_signature": 436, "uncovered_signature": 142} | 24T19906|r=2 |
| 10 | 10 | 64.11 | 355 | {"covered_or_crowded": 140, "lightly_solved_signature": 2464, "moderately_solved_signature": 329, "uncovered_signature": 355} | 24T19906|r=10 |

## Top Uncovered Targets

| rank | pair | score | label teams | signature teams | remaining on label |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 24T19906|r=24 | 922.00 | 0 | 0 | 12 |
| 2 | 24T22306|r=24 | 922.00 | 0 | 0 | 12 |
| 3 | 24T22631|r=24 | 922.00 | 0 | 0 | 12 |
| 4 | 24T22667|r=24 | 922.00 | 0 | 0 | 12 |
| 5 | 24T23413|r=24 | 922.00 | 0 | 0 | 12 |
| 6 | 24T24093|r=24 | 922.00 | 0 | 0 | 12 |
| 7 | 24T7872|r=24 | 919.00 | 0 | 0 | 11 |
| 8 | 24T12889|r=24 | 919.00 | 0 | 0 | 11 |
| 9 | 24T12891|r=24 | 919.00 | 0 | 0 | 11 |
| 10 | 24T15069|r=24 | 919.00 | 0 | 0 | 11 |
| 11 | 24T15083|r=24 | 919.00 | 0 | 0 | 11 |
| 12 | 24T15092|r=24 | 919.00 | 0 | 0 | 11 |
| 13 | 24T21404|r=24 | 919.00 | 0 | 0 | 11 |
| 14 | 24T21405|r=24 | 919.00 | 0 | 0 | 11 |
| 15 | 24T22567|r=24 | 919.00 | 0 | 0 | 11 |

## Score Follow-Up Targets

| rank | pair | points | solved teams | source score | category |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | 24T9993|r=8 | 0.0019 | 10 | 432.13 | scored_pair_followup |
| 2 | 24T22770|r=12 | 0.0002 | 12 | 213.71 | scored_pair_followup |

## API Scoreable Targets

| rank | pair | status | field disc | global min | log10 delta | submission |
| ---: | --- | --- | ---: | ---: | ---: | --- |

## API Pending Targets

| rank | pair | status | reason | submission |
| ---: | --- | --- | --- | --- |

## Lane Recommendations

| rank | lane | generation now | submission now | reason |
| ---: | --- | --- | --- | --- |
| 1 | r8_quartic_lift_score_followup | False | False | stopped by stop_r8_score_followup_quartic_x6_24T25000_lane: The 24T9993-sourced r8 quartic-in-x^6 score-followup lane using templates e/f and odd_pair_off_core perturbations collapsed to crowded 24T25000/r=8; reject nearby rows unless the construction family, decomposition pattern, or label discriminator changes materially. |
| 2 | r12_gx2_structured_score_followup | True | False | visible score outlier 24T22770/r=12 at 0.0002 with 12 solved teams |
| 3 | zero_team_high_real_target_conditioning | False | False | live progress still has many zero-team/uncovered signatures; current generators cannot directly condition exact labels |
| 4 | materially_different_high_real_lane_after_basin_stop | True | False | highest-score r8 follow-up lane is stopped; pivot to r24/r16/r20 or a genuinely different r8 construction with explicit anti-24T25000 gates |
| 5 | no_more_collapsed_composition_lanes | False | False | basin constraints show 6x4, ordinary 8x3, and current 4x6 inner-root family are exhausted |

## Decision

- Recommended next lane: `materially_different_high_real_lane_after_basin_stop`
- Clear bounded generation lane: `True`
- Submission recommended now: `False`
- GPU/model training now: `False` / `False`
- Submission reason: no candidate packet was generated by this planning helper; any future packet must pass score-aware and anti-basin gates plus SAIR dry-run
