# IGP24 GPU Probe Report

- Created UTC: `2026-07-08T00:11:29.642769+00:00`
- Output directory: `/tmp/igp24_axg1_gpu_tiny_20260707`
- Probe mode: `sample_export_split`
- Diversity variant: `None`
- Diversity seed: `None`
- Dedup unique target: `None`
- Dedup attempt budget: `None`
- Dedup stop reason: `None`
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
| 0 | False | False | 29.816 | cuda | 2 | 0.951 | 0.722 | 88.000 | 95.000 | 10.964 | True | 1024 | 1021 | 0 | 0 | 0 | 462 | True |

## Sample Export Dedup

| dedup_enabled | attempted | written | decoded_written | unique_decoded | duplicate_skipped | stop_reason | summary |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| False | 1024 | 1024 | 1021 | None | 0 | None | None |

## Baseline Context

- Baseline summary: `/tmp/igp24_gpu_smoke_20260704/gpu_smoke_summary.json`
- Tiny CPU smoke valid/ledger/runtime: `7` / `12` / `2.388s`
- Tiny GPU smoke valid/ledger/runtime: `4` / `12` / `3.880s`

## Recommendation

- Action: `consume_exported_samples_with_cpu_proxy_helper`
- Reason: CUDA training/sampling produced unscored export records while avoiding CPU scoring/local search. The next check is to consume that export with the CPU proxy scorer before considering a medium run.
