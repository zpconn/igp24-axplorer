# IGP24 GPU Probe Report

- Created UTC: `2026-07-08T02:32:36.692971+00:00`
- Output directory: `/tmp/igp24_axg12_target_r_conditioned_20260707/r20`
- Probe mode: `sample_export_target_r_conditioned`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `20`
- Target-r conditioning mode: `control_token`
- Target-r seed bank: `None`
- Target-r seed-bank limit: `None`
- Target-r training JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl`
- Target-r training target set: `12,16,20,24`
- Dedup unique target: `0`
- Dedup attempt budget: `768`
- Dedup stop reason: `attempt_budget_exhausted`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Probes

- `nvidia-smi` return code: `0`
- GPUs: `[{"driver_version": "596.49", "memory_total_mib": 32607, "name": "NVIDIA GeForce RTX 5090"}]`
- PyTorch: `2.12.1+cu130`
- CUDA available: `True`
- CUDA device: `NVIDIA GeForce RTX 5090`

## GPU Probe Run

| returncode | timeout | interrupted | runtime_s | device | evals | final_train_loss | final_test_loss | max_reserved_mb | max_gpu_util | avg_gpu_util | post_train_cpu_sampling_scoring_avoided | sample_export_records | sample_export_decoded | sample_requested | sample_valid | model_sample_ledger | ledger_rows | metadata |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | False | False | 78.137 | cuda | 8 | 0.036 | 4.918 | 34.000 | 92.000 | 79.500 | True | 34 | 18 | 0 | 0 | 0 | 0 | False |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| True | 768 | 34 | 18 | 18 | 734 | attempt_budget_exhausted | /tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_model_sample_export_target_r20_conditioned.jsonl.summary.json |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| False | 20 | 0 | 0 | 0 | 0 | 0 | None | `{"model_generate": 34}` |

## Baseline Context

- Baseline summary: `/tmp/igp24_gpu_smoke_20260704/gpu_smoke_summary.json`
- Tiny CPU smoke valid/ledger/runtime: `7` / `12` / `2.388s`
- Tiny GPU smoke valid/ledger/runtime: `4` / `12` / `3.880s`

## Recommendation

- Action: `consume_exported_samples_with_cpu_proxy_helper`
- Reason: CUDA training/sampling produced unscored export records while avoiding CPU scoring/local search. The next check is to consume that export with the CPU proxy scorer before considering a medium run.
