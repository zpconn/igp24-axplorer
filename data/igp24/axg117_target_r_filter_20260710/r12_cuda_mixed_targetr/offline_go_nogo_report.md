# AXG-1.17 Target-r Filter Offline Report

- Created UTC: 2026-07-10T08:00Z
- Run implementation commit: `6157e2bec9b581adf1dcb609f3759552c020634b`
- Output directory: `data/igp24/axg117_target_r_filter_20260710/r12_cuda_mixed_targetr/`
- Live SAIR submission: not run

## Purpose

Exercise the full AXG stack after adding an exact target-r sample-export gate.
The run trained a fresh bounded model, sampled on GPU, rejected known hashes and
structural basins upstream, then applied CPU exact scoring and full-index
adaptive Frobenius review.

## GPU / Export

- Target: r=12.
- Training rows: `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_tower6x4.jsonl`.
- Training target-r set: `8,12,16,20,24`.
- Attempts: 2048.
- CUDA device: NVIDIA GeForce RTX 5090.
- Max GPU utilization: 91%.
- Average GPU utilization: 29.353%.
- Runtime: 34.772s.
- Final train/test loss: 0.023 / 0.250.
- Export filters enabled:
  - known-submission hash exclusion;
  - avoid even-support `g(x^2)` basin;
  - require positive-support gcd one;
  - require nonzero constant coefficient;
  - require exact real-root count equal to target r.
- Exact target-r observations among decoded attempts:
  - r=12: 1880;
  - r=8: 6;
  - r=6: 2;
  - r=4: 6.
- Export skip counts:
  - known/excluded hash: 1865;
  - even-support-like: 1890;
  - support-gcd-not-one: 1890;
  - target-r mismatch: 14.
- Decoded rows exported after all filters: 1.

## CPU Exact Scoring

- Source export rows read: 155.
- Decoded input rows: 1.
- Skipped invalid-decode rows: 154.
- Locally valid rows: 1.
- Irreducible/squarefree rows: 1.
- Target-r survivors: 1.
- Candidate hash: `d8b7f708da52`.
- Polynomial:
  `x^24 - 91*x^20 + 3003*x^16 + 9*x^13 - 44473*x^12 + 296296*x^8 - 773139*x^4 + 518400`.

## Adaptive Frobenius Gate

- Index: complete degree-24 universe.
- Indexed groups: 25000.
- Evidence budgets: 5, 10, 20, 40, 80 usable primes.
- Evaluated rows: 1.
- Failed rows: 0.
- Valuable target survival rows: 0 at every budget.
- Final indexed target survivor count: 1.
- Exact label: missing.

## Decision

Recommendation: `do_not_submit`.

The one novel-looking local r12 row is not packet-eligible because full-index
adaptive Frobenius evidence leaves no currently valuable target pair. The
target-r filter is useful stack hygiene and prevents wrong-r rows from reaching
adaptive review, but the model is still mostly reproducing known/crowded
support basins.

## Next Implication

The next AXG iteration should keep the exact target-r export gate, but change
the training/export objective away from the repeated even/support-gcd basin.
The most direct next experiment is to add stronger negative pressure for
known-hash basin reproduction and add scarce positive examples from
non-even, support-gcd-one, nonzero-constant rows that survive at least shallow
valuable-target filters.
