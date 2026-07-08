# AXG Model Registry

AXG means Axplorer Generator. This registry tracks trained or planned IGP24
generator versions used for active learning.

Version rules:

- Integer versions such as `AXG-1` are full training generations.
- Decimal versions such as `AXG-1.5` are intermediate tuned/checkpoint
  generations with the same broad architecture and a meaningful data, sampler,
  or discriminator update.
- Model versions are never overwritten. New training attempt, new run id; new
  model generation, new AXG version.

Safety rules:

- Checkpoint files are referenced by path in manifests; large weight binaries
  are not stored here.
- SAIR API keys must never be written here.
- SAIR submission remains explicit and gated. GPU samples are proposals only.

Current status:

- `AXG-1` exists as the baseline proposal-generator generation.
- No long GPU training run has started for `AXG-1`.
- The first registered run is `axg1_dry_run_20260707`, a local dry-run using a
  known-collapsed r8 packet. It selected 0 rows and returned
  `hold_no_submission`.
- The second registered run is `axg1_gpu_tiny_20260707_1909`, a tiny CUDA
  train/export smoke. It exported 1,024 model samples, CPU-scored 256 rows,
  found 0 valid survivors in target `r=8,12,16,20,24`, selected 0 rows, and
  returned `hold_no_submission`.
- `AXG-1.1` exists as a target-r seeded export probe. Four tiny CUDA probes
  for `r=12,16,20,24` exported 2,064 rows and CPU-scored 524 rows. The
  seed-bank prefix produced 16 target-r control survivors, but raw
  `model_generate` rows produced 0 target-r survivors, and every proposal loop
  returned `hold_no_submission`.

Useful commands:

```bash
python3 scripts/igp24_model_registry.py --registry data/igp24/model_registry validate
python3 scripts/igp24_model_registry.py --registry data/igp24/model_registry summarize
python3 scripts/igp24_active_learning_dataset.py --help
python3 scripts/igp24_axg_proposal_loop.py --help
```
