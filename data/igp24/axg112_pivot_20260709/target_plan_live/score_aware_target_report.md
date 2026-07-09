# IGP24 Score-Aware Target Plan

## Snapshot

- Labels: 25000
- Pages: 5
- Published: True
- Generated: `2026-07-09T20:02:44Z` to `2026-07-09T20:02:51Z`
- Score snapshot rows: 20
- Sync submission rows: 0
- Partial sync: `False`
- Submission state complete: `True`
- Sync failing endpoint: `None`
- Basin constraints: 9

## Priority r Buckets

| rank | r | priority | remaining | category counts | top pair |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 24 | 1236.30 | 11372 | {"covered_or_crowded": 255, "lightly_solved_signature": 12786, "moderately_solved_signature": 587, "uncovered_signature": 11372} | 24T19906|r=24 |
| 2 | 16 | 1062.71 | 9721 | {"covered_or_crowded": 241, "lightly_solved_signature": 10763, "moderately_solved_signature": 696, "uncovered_signature": 9721} | 24T19906|r=16 |
| 3 | 8 | 956.12 | 5987 | {"covered_or_crowded": 491, "lightly_solved_signature": 15982, "moderately_solved_signature": 1095, "scored_pair_followup": 1, "uncovered_signature": 5987} | 24T19906|r=8 |
| 4 | 12 | 748.13 | 5917 | {"covered_or_crowded": 286, "lightly_solved_signature": 12963, "moderately_solved_signature": 767, "scored_pair_followup": 1, "uncovered_signature": 5917} | 24T19906|r=12 |
| 5 | 20 | 587.18 | 5177 | {"covered_or_crowded": 131, "lightly_solved_signature": 5150, "moderately_solved_signature": 394, "uncovered_signature": 5177} | 24T19906|r=20 |
| 6 | 0 | 539.12 | 3843 | {"covered_or_crowded": 1085, "lightly_solved_signature": 18345, "moderately_solved_signature": 1566, "uncovered_signature": 3843} | 24T19906|r=0 |
| 7 | 4 | 459.86 | 3351 | {"covered_or_crowded": 528, "lightly_solved_signature": 15224, "moderately_solved_signature": 954, "uncovered_signature": 3351} | 24T19906|r=4 |
| 8 | 6 | 108.23 | 470 | {"covered_or_crowded": 284, "lightly_solved_signature": 4860, "moderately_solved_signature": 390, "uncovered_signature": 470} | 24T19906|r=6 |
| 9 | 2 | 71.44 | 142 | {"covered_or_crowded": 374, "lightly_solved_signature": 4808, "moderately_solved_signature": 436, "uncovered_signature": 142} | 24T19906|r=2 |
| 10 | 10 | 64.02 | 354 | {"covered_or_crowded": 140, "lightly_solved_signature": 2465, "moderately_solved_signature": 329, "uncovered_signature": 354} | 24T19906|r=10 |

## Top Uncovered Targets

| rank | pair | score | label teams | signature teams | remaining on label |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 24T19906|r=24 | 921.79 | 0 | 0 | 12 |
| 2 | 24T22306|r=24 | 921.79 | 0 | 0 | 12 |
| 3 | 24T22631|r=24 | 921.79 | 0 | 0 | 12 |
| 4 | 24T22667|r=24 | 921.79 | 0 | 0 | 12 |
| 5 | 24T23413|r=24 | 921.79 | 0 | 0 | 12 |
| 6 | 24T24093|r=24 | 921.79 | 0 | 0 | 12 |
| 7 | 24T7872|r=24 | 918.79 | 0 | 0 | 11 |
| 8 | 24T12889|r=24 | 918.79 | 0 | 0 | 11 |
| 9 | 24T12891|r=24 | 918.79 | 0 | 0 | 11 |
| 10 | 24T15069|r=24 | 918.79 | 0 | 0 | 11 |
| 11 | 24T15083|r=24 | 918.79 | 0 | 0 | 11 |
| 12 | 24T15092|r=24 | 918.79 | 0 | 0 | 11 |
| 13 | 24T21404|r=24 | 918.79 | 0 | 0 | 11 |
| 14 | 24T21405|r=24 | 918.79 | 0 | 0 | 11 |
| 15 | 24T22567|r=24 | 918.79 | 0 | 0 | 11 |

## Score Follow-Up Targets

| rank | pair | points | solved teams | source score | category |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | 24T9993|r=8 | 0.0019 | 10 | 432.04 | scored_pair_followup |
| 2 | 24T22770|r=12 | 0.0002 | 12 | 213.61 | scored_pair_followup |

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
