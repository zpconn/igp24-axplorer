# AXG-1.14 Post-Remediation Offline Report

- Created: 2026-07-10
- Model version: `AXG-1.14`
- Source commit for generated artifacts: `7f14ff62d2eb52f004506945227a67aac5d5dd03`
- Live SAIR submission: `false`

## Inputs

- Training data: `data/igp24/active_learning/axg_training_dataset_20260710_postremediation.jsonl`
- Hash exclusions: `data/igp24/active_learning/axg114_hash_exclusions_20260710.jsonl`
- Full group index: `data/igp24/remediation_20260709/group_index_workflow_phase3/full_degree24_universe_local_gap_20260709/degree24_group_cycle_index.sqlite`
- Progress snapshot: `data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_label_progress.jsonl`

## GPU Runs

### r8 strict export

- Artifact: `data/igp24/axg114_postremediation_20260710/r8_cuda_mixed/`
- Runtime: 27.795s
- Device: CUDA, RTX 5090
- Max GPU utilization observed: 90%
- Final train/test loss: 0.017 / 0.300
- Export attempts: 4,096
- Excluded-hash skips: 4,037
- Exported records: 45
- Unique decoded rows: 1
- CPU scoring: 1 decoded, 0 valid, 0 target-r survivors

### r12 loose top-k-20 export

- Artifact: `data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/`
- Runtime: 59.562s
- Device: CUDA, RTX 5090
- Max GPU utilization observed: 90%
- Final train/test loss: 0.013 / 0.286
- Export attempts: 8,192
- Excluded-hash skips: 8,002
- Exported records: 162
- Unique decoded rows: 9
- CPU scoring: 9 decoded, 8 valid, 3 target-r survivors

## Adaptive Review

- Artifact: `data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/adaptive_frobenius_3rows_40primes/`
- Evaluated rows: 3/3
- Failed rows: 0
- Max usable primes: 40
- Complete-index metadata: `global_index_complete=true`, `indexed_group_count=25000`
- Exact labels: missing for all 3 rows
- Valuable target survival at 40 primes: 2 rows
- Median indexed survivor count at 40 primes: 2

## Packet Gate

- Artifact: `data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/packet_optimizer_40prime_reviewed/`
- Candidates considered: 3
- Eligible candidates: 2
- Selected offline-review rows: 1
- Selected hash: `4b4d9399b761`
- Possible low-team pair: `24T24999|r=12`
- Possible uncovered pairs: 0
- Best-case packet points: 0.015625
- Expected points status: `unavailable_uncalibrated`
- Live submission recommended now: `false`

## Conclusion

AXG-1.14 successfully exercised the corrected generator-training contract and the full offline inference stack, including CUDA training, hash exclusion, CPU scoring, 40-prime complete-index adaptive review, and corrected packet optimization.

It did not produce a submission-grade row. The only optimized survivor is novel and has sufficient adaptive Frobenius evidence for compatibility with one low-team target, but exact Galois label verification is still missing and compatibility remains necessary target-exclusion evidence only.

Recommendation: do not submit. Use this run as evidence that the tiny post-remediation positive corpus is too memorization-prone, then improve the next AXG iteration by adding more exact positive diversity or by training against construction-family negatives without allowing no-value rows to become demonstrations.
