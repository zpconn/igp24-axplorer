# AXG-1.12 Training Summary

Status: completed, no score improvement.

- Training data: `data/igp24/active_learning/axg_training_dataset_20260709_axg112_pivot.jsonl`
- GPU run: r12 mixed target-r conditioned, 2400 steps, 8192 attempts.
- GPU: NVIDIA GeForce RTX 5090, max/avg utilization 84.0% / 31.723%, runtime 229.916s.
- Export/scoring: 1216 records, 28 decoded, 25 valid, 9 r12 survivors.
- Structured scout: 12 r12 feedback-aware `g(x^2)` rows selected for gate review.
- Submission: `sub_51983ad56663418187e9adc3142c1162`, 6/6 accepted and scoreable.
- Result: all rows collapsed to `24T24979|r=12`; no team-count or discriminant improvement observed.

The active score-improvement goal remains incomplete.
