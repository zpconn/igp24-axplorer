# IGP24 GPU Probe Report

- Created UTC: `2026-07-08T01:56:24.323194+00:00`
- Output directory: `/tmp/igp24_axg11_target_r_seeded_20260707/r20`
- Probe mode: `sample_export_target_r_seeded`
- Diversity variant: `None`
- Diversity seed: `None`
- Target r: `20`
- Target-r conditioning mode: `seed_bank_prefix`
- Target-r seed bank: `data/igp24/axg_target_r_seed_bank_20260707/target_r_seed_bank.jsonl`
- Target-r seed-bank limit: `4`
- Dedup unique target: `0`
- Dedup attempt budget: `512`
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
| 0 | False | False | 27.403 | cuda | 2 | 0.798 | 0.706 | 14.000 | 84.000 | 7.154 | True | 516 | 511 | 0 | 0 | 0 | 459 | True |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| True | 512 | 516 | 511 | 511 | 0 | attempt_budget_exhausted | /tmp/igp24_axg11_target_r_seeded_20260707/r20/gpu_model_sample_export_target_r20_seeded.jsonl.summary.json |

## Target-r Seed Bank

| enabled | target_r | limit | written | matching_rows | duplicate_skipped | invalid_skipped | max_height | source_counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| True | 20 | 4 | 4 | 4 | 0 | 0 | 11857252 | `{"model_generate": 512, "target_r_seed_bank": 4}` |

## Baseline Context

- Baseline summary: `/tmp/igp24_gpu_smoke_20260704/gpu_smoke_summary.json`
- Tiny CPU smoke valid/ledger/runtime: `7` / `12` / `2.388s`
- Tiny GPU smoke valid/ledger/runtime: `4` / `12` / `3.880s`

## Recommendation

- Action: `consume_exported_samples_with_cpu_proxy_helper`
- Reason: CUDA training/sampling produced unscored export records while avoiding CPU scoring/local search. The next check is to consume that export with the CPU proxy scorer before considering a medium run.
