# AXG-1.2 Training Summary

Status: four short CUDA target-r-conditioned runs completed; no SAIR submission.

- Encoding: `decimal_coefficients`.
- Conditioning: model-side `R12/R16/R20/R24` control token after `BOS`.
- Training data: `data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl`.
- GPU runtime total: `308.0s`.
- Model-generated target-r survivors: `128` across `212` scored decoded rows.
- Proposal dry-runs: `7` selected rows total, all targets held below packet gate; submitted_to_sair=false.

| r | decoded | scored | valid | target survivors | selected |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | 85 | 85 | 80 | 47 | 2 |
| 16 | 35 | 35 | 34 | 31 | 1 |
| 20 | 18 | 18 | 15 | 12 | 1 |
| 24 | 74 | 74 | 70 | 38 | 3 |
