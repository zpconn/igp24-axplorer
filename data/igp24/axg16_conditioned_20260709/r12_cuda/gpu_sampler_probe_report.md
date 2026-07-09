# IGP24 GPU Probe Report

- Created UTC: `2026-07-09T15:39:34.440607+00:00`
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r12_cuda`
- Probe mode: `sample_export_target_r_conditioned`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `12`
- Target-r conditioning mode: `control_token`
- Target-r seed bank: `None`
- Target-r seed-bank limit: `None`
- Target-r training JSONL: `data/igp24/active_learning/axg_training_dataset_20260709_axg16_conditioned.jsonl`
- Target-r training target set: `8,12,16,20,24`
- Dedup unique target: `512`
- Dedup attempt budget: `4096`
- Dedup stop reason: `attempt_budget_exhausted`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Probes

- `nvidia-smi` return code: `0`
- GPUs: `[{"driver_version": "596.49", "memory_total_mib": 32607, "name": "NVIDIA GeForce RTX 5090"}]`
- PyTorch: `2.12.0+cu130`
- CUDA available: `True`
- CUDA device: `NVIDIA GeForce RTX 5090`

## GPU Probe Run

| returncode | timeout | interrupted | runtime_s | device | evals | final_train_loss | final_test_loss | max_reserved_mb | max_gpu_util | avg_gpu_util | post_train_cpu_sampling_scoring_avoided | sample_export_records | sample_export_decoded | sample_requested | sample_valid | model_sample_ledger | ledger_rows | metadata |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | False | False | 192.000 | cuda | 18 | 0.040 | 2.576 | 34.000 | 89.000 | 77.479 | True | 369 | 6 | 0 | 0 | 0 | 0 | False |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| True | 4096 | 369 | 6 | 6 | 379 | attempt_budget_exhausted | /home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r12_cuda/gpu_model_sample_export_target_r12_conditioned.jsonl.summary.json |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| False | 12 | 0 | 0 | 0 | 0 | 0 | None | `{"model_generate": 369}` |

## Recommendation

- Action: `consume_exported_samples_with_cpu_proxy_helper`
- Reason: CUDA training/sampling produced unscored export records while avoiding CPU scoring/local search. The next check is to consume that export with the CPU proxy scorer before considering a medium run.
