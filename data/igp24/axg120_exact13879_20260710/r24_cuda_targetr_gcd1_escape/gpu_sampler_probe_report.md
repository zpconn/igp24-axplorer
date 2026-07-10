# IGP24 GPU Probe Report

- Created UTC: `2026-07-10T09:41:12.481761+00:00`
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg120_exact13879_20260710/r24_cuda_targetr_gcd1_escape`
- Probe mode: `sample_export_target_r_conditioned`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `24`
- Target-r conditioning mode: `control_token`
- Target-r seed bank: `None`
- Target-r seed-bank limit: `None`
- Target-r training JSONL: `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_exact13879_axg120.jsonl`
- Target-r training target set: `8,12,16,20,24`
- Dedup unique target: `16`
- Dedup attempt budget: `8192`
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
| 0 | False | False | 111.217 | cuda | 4 | 0.022 | 2.900 | 34.000 | 92.000 | 25.729 | True | 591 | 0 | 0 | 0 | 0 | 0 | False |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| True | 8192 | 591 | 0 | 0 | 0 | attempt_budget_exhausted | /home/zpconn/code/igp24-axplorer/data/igp24/axg120_exact13879_20260710/r24_cuda_targetr_gcd1_escape/gpu_model_sample_export_target_r24_conditioned.jsonl.summary.json |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| False | 24 | 0 | 0 | 0 | 0 | 0 | None | `{"model_generate": 591}` |

## Recommendation

- Action: `run_another_short_gpu_probe_with_adjusted_settings`
- Reason: The sample-export probe ran, but did not produce decoded model-sample records.
