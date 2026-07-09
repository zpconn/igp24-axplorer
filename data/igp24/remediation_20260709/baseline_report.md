# IGP24 Remediation Phase 0 Baseline

Created: `2026-07-09T20:42:11.765235+00:00`
Git HEAD: `cebcc0680aea4dec66936a38089b2285265f3001`
Worktree dirty entries: `5`

## Test Baseline

- Command: `PYTHONPATH=. /home/zpconn/code/axplorer/.venv/bin/python -m pytest -q`
- Result: **failed**: 308 passed, 1 failed.
- Failure: stale r12 follow-up ledger assertion expects 14 `24T24979|r=12` alternates; current ledger has 20 after AXG-1.12 feedback.

## Training Data

- Latest dataset: `data/igp24/active_learning/axg_training_dataset_summary_20260709_axg113_high_real.json`
- Latest rows: 635
- Latest class counts: `{"accepted_duplicate_collapsed_basin": 454, "accepted_globally_covered_high_team_basin": 8, "accepted_useful_score_positive": 8, "exact_local_valid": 60, "wrong_real_root_count": 105}`
- Latest score-aware counts: `{"accepted_but_crowded_collapse": 462, "pending_or_unknown": 60, "score_positive": 8, "wrong_r": 105}`
- Committed AXG-1.12 reference rows: 2242
- Committed AXG-1.12 class counts: `{"accepted_duplicate_collapsed_basin": 876, "accepted_globally_covered_high_team_basin": 8, "accepted_useful_score_positive": 12, "exact_local_valid": 191, "locally_invalid": 144, "wrong_real_root_count": 1011}`

Diagnosis: score-aware reward/weight metadata is present, but current generator training still imitates coefficient-token rows uniformly. Crowded accepted rows are not excluded from generator demonstrations yet.

## Positive vs Collapse Mass

- Latest score-positive rows: 8
- Latest accepted/crowded-collapse rows: 454
- Raw collapse:positive ratio: 56.75:1
- AXG-1.12 reference score-positive rows: 12
- AXG-1.12 reference collapse rows: 876

## Verified Pair / Collapse State

- Current scoreable rows from fresh sync: 234
- Distinct verified scoreable pairs: 28
- Collapsed-label scoreable rows: 222 / 234 (94.9%)
- Top scoreable labels: `[["24T25000", 126], ["24T24979", 38], ["24T24932", 20], ["24T24651", 17], ["24T24984", 12], ["24T24970", 6], ["24T23883", 3], ["24T22770", 2], ["24T1310", 2], ["24T9993", 2]]`
- User-snapshot score-positive pair count: 2 (24T9993|r=8, 24T22770|r=12)

## AXG-1.10 Decode Baseline

- Total attempted samples: 32768
- Total unique decoded coefficients: 15
- Target-r survivors: 1
- Survivor yield per unique decoded: 6.7%
- Survivor yield per attempt: 0.003052%
- r8: attempted 16384, unique decoded 12, target-r survivors 1, train/test loss None / None
- r12: attempted 16384, unique decoded 3, target-r survivors 0, train/test loss None / None

## Recent Training Losses

- Latest completed model: AXG-1.12, train/test loss 0.044 / 2.246, no score improvement.
- Interrupted AXG-1.13 pre-remediation run: runtime 119.3755974079977s, train/test loss 0.045847349228958285 / 2.142430543899536, partial export 643 records / 12 decoded. Do not continue this run until Phase 1 is fixed.

## Leaderboard

- Our public rank/score: rank 77, score 0.000508, scoreable pairs 28.
- Current top-25 cutoff: rank 25 score 108.009839 with 5087 scoreable pairs.
- Recorded visible numeric points in local user snapshot: 0.0021 across 2 rows; many `<0.0001` rows are intentionally not treated as material progress.

## SAIR State

- Fresh sync: `data/igp24/axg113_high_real_20260709/sair_sync_full`
- Remaining signatures: 46998
- Top remaining r buckets: `[{"r": 24, "allowed": 25000, "discovered": 13632, "remaining": 11368, "discovered_pct": 54.53, "remaining_pct": 45.47, "average_signature_team_count": 1.8, "max_signature_team_count": 45}, {"r": 16, "allowed": 21421, "discovered": 11703, "remaining": 9718, "discovered_pct": 54.63, "remaining_pct": 45.37, "average_signature_team_count": 2.31, "max_signature_team_count": 42}, {"r": 8, "allowed": 23556, "discovered": 17570, "remaining": 5986, "discovered_pct": 74.59, "remaining_pct": 25.41, "average_signature_team_count": 3.66, "max_signature_team_count": 48}, {"r": 12, "allowed": 19934, "discovered": 14021, "remaining": 5913, "discovered_pct": 70.34, "remaining_pct": 29.66, "average_signature_team_count": 3.09, "max_signature_team_count": 46}, {"r": 20, "allowed": 10852, "discovered": 5678, "remaining": 5174, "discovered_pct": 52.32, "remaining_pct": 47.68, "average_signature_team_count": 2.24, "max_signature_team_count": 42}]`
- Partial sync: False; unmatched rows: 7

## Phase 0 Conclusion

No more routine GPU iterations should run until Phase 1 fixes generator-training semantics. The current model-training path has enough evidence of the core defect: score-aware labels exist, but collapse-heavy rows still dominate imitation training, while exact group targeting is absent.
