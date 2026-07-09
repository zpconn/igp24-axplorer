# AXG-1.9 Training Summary

Status: bounded CUDA sparse-support runs completed; no SAIR submission.

- r16 sparse CUDA: 8,192 attempts, 3 decoded records, 0 r16 target survivors after CPU scoring; r4 spillover gate held.
- r8 sparse CUDA: 8,192 attempts, 8 decoded records, 6 r8 target survivors, but all target-r survivors were accepted-hash duplicates and the gate selected 0 rows.
- Lesson: sparse support alone avoided the AXG-1.8 dense/medium hard stop but still rediscovered known rows; AXG-1.10 adds external hash-exclusion memory.
