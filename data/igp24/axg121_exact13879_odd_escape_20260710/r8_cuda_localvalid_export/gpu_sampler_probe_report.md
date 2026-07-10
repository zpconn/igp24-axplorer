# IGP24 GPU Probe Report

- Created UTC: `2026-07-10T10:14:09.451657+00:00`
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export`
- Probe mode: `sample_export_target_r_conditioned`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `8`
- Target-r conditioning mode: `control_token`
- Target-r seed bank: `None`
- Target-r seed-bank limit: `None`
- Target-r training JSONL: `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_exact13879_crossr_axg121.jsonl`
- Target-r training target set: `8,12,16,20,24`
- Dedup unique target: `12`
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
| 0 | False | False | 190.301 | cuda | 4 | 0.022 | 2.848 | 34.000 | 91.000 | 25.114 | True | 204 | 2 | 0 | 0 | 0 | 0 | False |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| True | 8192 | 204 | 2 | 2 | 0 | attempt_budget_exhausted | /home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_model_sample_export_target_r8_conditioned.jsonl.summary.json |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| False | 8 | 0 | 0 | 0 | 0 | 0 | None | `{"model_generate": 204}` |

## Recommendation

- Action: `consume_exported_samples_with_cpu_proxy_helper`
- Reason: CUDA training/sampling produced unscored export records while avoiding CPU scoring/local search. The next check is to consume that export with the CPU proxy scorer before considering a medium run.
