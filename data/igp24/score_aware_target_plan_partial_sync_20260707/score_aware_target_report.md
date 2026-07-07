# IGP24 Score-Aware Target Plan

## Snapshot

- Labels: 25000
- Pages: 5
- Published: True
- Generated: `2026-07-07T18:08:49Z` to `2026-07-07T18:08:49Z`
- Score snapshot rows: 20
- Sync submission rows: 0
- Partial sync: `True`
- Submission state complete: `False`
- Sync failing endpoint: `submissions/me`
- Basin constraints: 8

## Priority r Buckets

| rank | r | priority | remaining | category counts | top pair |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 24 | 1290.41 | 11998 | {"covered_or_crowded": 181, "lightly_solved_signature": 12284, "moderately_solved_signature": 537, "uncovered_signature": 11998} | 24T18897|r=24 |
| 2 | 16 | 1144.93 | 10676 | {"covered_or_crowded": 180, "lightly_solved_signature": 9966, "moderately_solved_signature": 599, "uncovered_signature": 10676} | 24T18897|r=16 |
| 3 | 8 | 1028.55 | 6822 | {"covered_or_crowded": 360, "lightly_solved_signature": 15344, "moderately_solved_signature": 1029, "scored_pair_followup": 1, "uncovered_signature": 6822} | 24T18897|r=8 |
| 4 | 12 | 819.18 | 6740 | {"covered_or_crowded": 199, "lightly_solved_signature": 12291, "moderately_solved_signature": 703, "scored_pair_followup": 1, "uncovered_signature": 6740} | 24T18897|r=12 |
| 5 | 20 | 626.02 | 5629 | {"covered_or_crowded": 105, "lightly_solved_signature": 4757, "moderately_solved_signature": 361, "uncovered_signature": 5629} | 24T18897|r=20 |
| 6 | 0 | 583.59 | 4336 | {"covered_or_crowded": 864, "lightly_solved_signature": 18250, "moderately_solved_signature": 1389, "uncovered_signature": 4336} | 24T18897|r=0 |
| 7 | 4 | 503.32 | 3848 | {"covered_or_crowded": 401, "lightly_solved_signature": 14880, "moderately_solved_signature": 928, "uncovered_signature": 3848} | 24T18897|r=4 |
| 8 | 6 | 115.88 | 555 | {"covered_or_crowded": 238, "lightly_solved_signature": 4830, "moderately_solved_signature": 381, "uncovered_signature": 555} | 24T18897|r=6 |
| 9 | 2 | 73.93 | 165 | {"covered_or_crowded": 315, "lightly_solved_signature": 4859, "moderately_solved_signature": 421, "uncovered_signature": 165} | 24T18897|r=2 |
| 10 | 10 | 69.54 | 416 | {"covered_or_crowded": 122, "lightly_solved_signature": 2443, "moderately_solved_signature": 307, "uncovered_signature": 416} | 24T18897|r=10 |

## Top Uncovered Targets

| rank | pair | score | label teams | signature teams | remaining on label |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 24T18897|r=24 | 923.00 | 0 | 0 | 12 |
| 2 | 24T19906|r=24 | 923.00 | 0 | 0 | 12 |
| 3 | 24T22306|r=24 | 923.00 | 0 | 0 | 12 |
| 4 | 24T22631|r=24 | 923.00 | 0 | 0 | 12 |
| 5 | 24T22667|r=24 | 923.00 | 0 | 0 | 12 |
| 6 | 24T23413|r=24 | 923.00 | 0 | 0 | 12 |
| 7 | 24T24093|r=24 | 923.00 | 0 | 0 | 12 |
| 8 | 24T24768|r=24 | 923.00 | 0 | 0 | 12 |
| 9 | 24T7872|r=24 | 920.00 | 0 | 0 | 11 |
| 10 | 24T12889|r=24 | 920.00 | 0 | 0 | 11 |
| 11 | 24T12891|r=24 | 920.00 | 0 | 0 | 11 |
| 12 | 24T15037|r=24 | 920.00 | 0 | 0 | 11 |
| 13 | 24T15069|r=24 | 920.00 | 0 | 0 | 11 |
| 14 | 24T15083|r=24 | 920.00 | 0 | 0 | 11 |
| 15 | 24T15092|r=24 | 920.00 | 0 | 0 | 11 |

## Score Follow-Up Targets

| rank | pair | points | solved teams | source score | category |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | 24T9993|r=8 | 0.0019 | 10 | 445.31 | scored_pair_followup |
| 2 | 24T22770|r=12 | 0.0002 | 12 | 287.89 | scored_pair_followup |

## API Scoreable Targets

| rank | pair | status | field disc | global min | log10 delta | submission |
| ---: | --- | --- | ---: | ---: | ---: | --- |

## API Pending Targets

| rank | pair | status | reason | submission |
| ---: | --- | --- | --- | --- |

## Lane Recommendations

| rank | lane | generation now | submission now | reason |
| ---: | --- | --- | --- | --- |
| 1 | r8_quartic_lift_score_followup | True | False | visible score outlier 24T9993/r=8 at 0.0019 with 10 solved teams |
| 2 | r12_gx2_structured_score_followup | True | False | visible score outlier 24T22770/r=12 at 0.0002 with 12 solved teams |
| 3 | zero_team_high_real_target_conditioning | False | False | live progress still has many zero-team/uncovered signatures; current generators cannot directly condition exact labels |
| 4 | no_more_collapsed_composition_lanes | False | False | basin constraints show 6x4, ordinary 8x3, and current 4x6 inner-root family are exhausted |

## Decision

- Recommended next lane: `r8_quartic_lift_score_followup`
- Clear bounded generation lane: `True`
- Submission recommended now: `False`
- GPU/model training now: `False` / `False`
- Submission reason: partial SAIR sync: submission/scoring state is incomplete, so no submission packet can be recommended
