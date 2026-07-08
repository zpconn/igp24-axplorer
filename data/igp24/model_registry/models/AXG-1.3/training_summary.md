# AXG-1.3 Training Summary

Status: four short CUDA diversity-aware target-r-conditioned runs completed; no SAIR submission.

- Parent: `AXG-1.2`.
- Encoding: `decimal_coefficients`.
- Conditioning: model-side `R12/R16/R20/R24` control token after `BOS`.
- Diversity sampling: temperature `1.15`, open top-k `-1`, unique decoded target `512`, attempt budget `2048`, generation strategy metadata `mixed`.
- GPU runtime total: `645.8s`.
- Model-generated target-r survivors: `172` across `371` scored rows.
- Model-generated eligible rows: `39`; proposal selected rows: `13`.
- Decision: `hold_no_submission`. Fresh SAIR sync succeeded, but proposal dry-runs held every target. r12/r16/r20 selected four model-generated rows each, yet all selected rows had perturbation_mode=unknown and failed mode-diversity gates; r24 had only one eligible model-generated row.

| r | decoded | scored | valid | target survivors | eligible | selected | decision |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 12 | 108 | 108 | 108 | 51 | 4 | 4 | `hold_no_submission` |
| 16 | 89 | 89 | 85 | 44 | 7 | 4 | `hold_no_submission` |
| 20 | 83 | 83 | 73 | 38 | 27 | 4 | `hold_no_submission` |
| 24 | 91 | 91 | 87 | 39 | 1 | 1 | `hold_no_submission` |
