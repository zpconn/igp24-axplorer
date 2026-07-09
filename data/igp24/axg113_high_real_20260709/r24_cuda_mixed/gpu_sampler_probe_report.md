# IGP24 GPU Probe Report

- Created UTC: `2026-07-09T20:34:53.618713+00:00`
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg113_high_real_20260709/r24_cuda_mixed`
- Probe mode: `sample_export_target_r_conditioned`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `24`
- Target-r conditioning mode: `control_token`
- Target-r seed bank: `None`
- Target-r seed-bank limit: `None`
- Target-r training JSONL: `data/igp24/active_learning/axg_training_dataset_20260709_axg113_high_real.jsonl`
- Target-r training target set: `8,12,16,20,24`
- Dedup unique target: `None`
- Dedup attempt budget: `None`
- Dedup stop reason: `None`
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
| 130 | False | True | 119.376 | cuda | 8 | 0.046 | 2.142 | 34.000 | 88.000 | 56.259 | True | 643 | 12 | 0 | 0 | 0 | 0 | False |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| False | 643 | 643 | 12 | None | 0 | None | None |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| False | None | None | 0 | 0 | 0 | 0 | None | `{"model_generate": 643}` |

## Recommendation

- Action: `run_another_short_gpu_probe_with_adjusted_settings`
- Reason: The monitored probe was interrupted before a complete utilization report was written.
