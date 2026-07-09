# AXG-1.13 Training Summary

Status: interrupted before remediation; do not continue this run or submit rows from it.

AXG-1.13 was registered as a high-real r24/r16/r20 pivot after AXG-1.12 collapsed to crowded r12 labels. A short r24 CUDA mixed sample-export run started on 2026-07-09 with seed 33024, but the run was interrupted after the remediation objective made clear that the generator-training semantics had to be fixed before another routine AXG iteration.

Observed run evidence:

- Summary: `data/igp24/axg113_high_real_20260709/r24_cuda_mixed/gpu_sampler_probe_summary.json`
- Runtime: 119.376 seconds
- Return code: 130
- Logged train device: `cuda`
- GPU monitor: max 88.0% utilization, average 56.259% utilization on RTX 5090
- Final recorded train/test loss: 0.045847 / 2.142431
- Sample export: 643 records, 12 decoded records

No AXG-1.13 samples were exact-gated, submitted to SAIR, or scored. The next completed AXG model must use the remediation Phase 1 `generator_training` contract and must not be marked complete until SAIR score improves.
