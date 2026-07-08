# AXG-1.1 Training Summary

Status: four tiny target-r seeded GPU probes completed; no long training run
started.

## 2026-07-07 Target-r Seeded Probe

AXG-1.1 is a target-r-biased export probe, not full control-token
conditioning. The coefficient tokenizer remains raw coefficient based, so high
real-root rows such as `r=20` cannot be used as ordinary small-vocabulary model
training examples without making the vocabulary/logits impractical. Instead,
the probe prefixes target-r-labelled seed-bank rows into the unscored export
stream and records source metadata so seed-bank rows and raw `model_generate`
rows are measured separately.

Targets: `r=12,16,20,24`.

Aggregate:

- GPU runs: 4
- Exported rows: 2,064
- CPU-scored rows: 524
- Proxy-valid rows: 477
- Target-r survivors: 16
- Raw `model_generate` target-r survivors: 0
- Seed-bank target-r survivors: 16
- Proposal-loop selected rows: 0
- Proposal-loop decision: `hold_no_submission` for every target

Conclusion: the seeded export control path works, but the model itself is not
yet steering into the target buckets. Do not start a larger AXG GPU training
run until model-side target-r conditioning improves beyond the seed-bank
control rows.
