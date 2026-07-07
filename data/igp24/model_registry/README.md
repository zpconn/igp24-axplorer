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
