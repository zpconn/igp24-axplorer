# AXG-1 Training Summary

Status: tiny GPU smoke completed; no long training run started.

## axg1_gpu_tiny_20260707_1909

- Purpose: prove the bounded AXG-1 path on model-generated samples before any
  larger training run.
- GPU phase: CUDA on NVIDIA GeForce RTX 5090, runtime 29.816 seconds, max
  monitored GPU utilization 95%, max memory used 5,760 MiB.
- Export: 1,024 model sample rows, 1,021 decoded rows.
- CPU scoring: 256 scored rows, 230 proxy-valid rows, 26 rejected rows, 256
  unique canonical hashes, best proxy score 9950.58, mean proxy score 8912.44.
- Real-root distribution among scored rows: `r=0` x24, `r=2` x151, `r=4` x53,
  `r=6` x2, rejected/unknown x26.
- Proposal gate: 0 filtered rows, 0 selected rows, decision
  `hold_no_submission`.
- Safety: no SAIR submission, no automatic live submission, no API key
  serialization, no checkpoint binaries committed.

Conclusion: the GPU train/export machinery works, but the baseline tiny sampler
does not yet produce target `r=8,12,16,20,24` survivors. The next AXG model
step should add target-r conditioning or target-r-biased sampling before
scaling to a longer run.
