# IGP24 GPU Probe Report

- Created UTC: `2026-07-09T17:52:09.209657+00:00`
- Output directory: `/home/zpconn/code/igp24-axplorer/data/igp24/axg17_score_aware_20260709/r16_cuda`
- Probe mode: `sample_export_target_r_conditioned`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `16`
- Target-r conditioning mode: `control_token`
- Target-r seed bank: `None`
- Target-r seed-bank limit: `None`
- Target-r training JSONL: `data/igp24/active_learning/axg_training_dataset_20260709_axg17_score_aware.jsonl`
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
| 0 | False | False | 142.858 | cuda | 12 | 0.040 | 3.352 | 34.000 | 88.000 | 73.971 | True | 868 | 8 | 0 | 0 | 0 | 0 | False |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| True | 4096 | 868 | 8 | 8 | 909 | attempt_budget_exhausted | /home/zpconn/code/igp24-axplorer/data/igp24/axg17_score_aware_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl.summary.json |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| False | 16 | 0 | 0 | 0 | 0 | 0 | None | `{"model_generate": 868}` |

## Recommendation

- Action: `consume_exported_samples_with_cpu_proxy_helper`
- Reason: CUDA training/sampling produced unscored export records while avoiding CPU scoring/local search. The next check is to consume that export with the CPU proxy scorer before considering a medium run.
