# AXG-1.18 Positive-Seed Escape Offline Report

- Created UTC: 2026-07-10T08:18Z
- Implementation commit: `fdc012ed2fbd6923d71cda3c33f555676e9d4eed`
- Live SAIR submission: not run

## Purpose

AXG-1.17 showed that exact target-r export filtering works, but the model still
spends nearly all sampling mass reproducing known/crowded score-positive
basins. This pass added an offline positive-seed escape lane that mutates the
scarce score-positive seeds into non-even, support-gcd-one, exact-local rows,
then uses adaptive Frobenius evidence to decide whether they should become
generator examples or negative/risk evidence.

## Positive-Seed Escape Lane

- Source dataset:
  `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_tower6x4.jsonl`.
- Selected generator-positive seeds: 4 unique rows.
- Seed pairs:
  - `24T22770|r=12`: 2 seeds.
  - `24T9993|r=8`: 2 seeds.
- Local mutation search:
  `data/igp24/axg118_positive_seed_escape_20260710/r8_r12_local_exact/`.
- Trials: 47.
- Local exact candidates: 40.
- Rejected trials: 7 reducible rows.
- All 40 candidates were exact r12 from the `24T22770|r=12` seed family.
- Adaptive 20-prime full-index review:
  `data/igp24/axg118_positive_seed_escape_20260710/r8_r12_local_exact/adaptive_frobenius_40rows_20primes/`.
- Adaptive result: 40/40 evaluated, 0 failures, 0 valuable target survivors.
- Materialized review:
  `data/igp24/axg118_positive_seed_escape_20260710/r8_r12_local_exact/adaptive_reviewed_candidates_20primes/`.
- Packet-eligible rows: 0.

## Dataset / Reward Feedback

- Refreshed dataset:
  `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_axg118_escape.jsonl`.
- Row count: 507.
- Generator-eligible rows: still 8, all `score_positive`.
- Escape rows in dataset: 40, all `no_valuable_target_survival`, 0 generator-eligible.
- Refreshed reward model:
  `data/igp24/remediation_20260709/reward_model_phase2/postremediation_axg118_escape_20260710/`.
- Reward model status: `advisory_insufficient_positive_data`.
- Group overlap: none.
- Scoring the refreshed dataset produced:
  - `crowded_accepted_collapse`: 388 rows;
  - `no_valuable_target_survival`: 72 rows;
  - `score_positive`: 8 rows;
  - `wrong_r`: 39 rows.
- The 40 positive-seed escape rows score as
  `advisory_conflicted_sparse_positive` with collapse risk 0.671 and reward
  probability 0.329.

## Bounded AXG Run

- Output:
  `data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/`.
- Training dataset:
  `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_axg118_escape.jsonl`.
- Target: r=12.
- CUDA device: NVIDIA GeForce RTX 5090.
- Max GPU utilization: 90%.
- Average GPU utilization: 28.688%.
- Runtime: 32.583s.
- Final train/test loss: 0.013 / 0.290.
- Attempts: 1024.
- Decoded attempts: 977.
- Exported decoded rows after known-hash, support, nonzero, and exact-target-r filters: 1.
- Export skip counts:
  - known/excluded hash: 962;
  - even-support-like: 973;
  - support-gcd-not-one: 973;
  - target-r mismatch: 8.
- The one exported row was locally valid, irreducible, squarefree, and exact r12:
  `581c10d5e536`.
- Adaptive 40-prime review found 0 valuable target survivors at budgets 5, 10,
  20, and 40.

## Decision

Recommendation: `do_not_submit`.

The positive-seed escape lane is useful negative feedback: simple odd-support
escapes from the scarce score-positive seed family produce exact-local r12
polynomials, but they do not preserve valuable target compatibility. The next
work should stop widening this lane unless the construction changes
materially, and should instead seek new positive generator mass from a
different structural family with adaptive valuable-target survival.
