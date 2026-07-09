# AXG-1.11 Training Summary

Status: bounded CUDA run completed; no submit-ready packet.

- Parent: `AXG-1.10`.
- Training data: `data/igp24/active_learning/axg_training_dataset_20260709_axg19_sparse_escape.jsonl` plus hash exclusions.
- r8 CUDA run `axg111_r8_sparse_submode_20260709`: runtime 278.957s, max/avg GPU 87.0% / 35.17%, final train/test loss 0.040 / 2.971.
- Export: 12,288 attempts, 6,013 records written, 12 decoded unique rows, 2,840 excluded-hash skips; raw export/checkpoints removed after summaries.
- CPU scoring: 12 decoded rows, 5 valid, 7 rejected.
- Gate `axg111_r8_sparse_submode_gate_refresh_20260709`: 12 candidates, 4 filtered, 1 selected, `hold_no_submission`.
- Reason: new AXG-1.10 feedback correctly blocked sparse-template rows as known `24T25000` collapse; only one loose-basin r6 row survived.
