# IGP24 Split Workflow Report

- Created UTC: `2026-07-09T15:19:02.986995+00:00`
- Source commit: `689baac40c4c313baa92f6dbc3e43ce6a8a32ee3`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_model_sample_export_target_r20_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_sample_export_target_r20_conditioned_dump/igp24_gpu_sample_export_target_r20_conditioned/axg15_target_r20_fullstack_20260709_cuda/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 123.22434200399584 | 88.0 | 662 | 16 | 1.213821408993681 | 662 | 16 | 16 | 0 | 16 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r20_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_sample_export_target_r20_conditioned_dump --exp_id axg15_target_r20_fullstack_20260709_cuda --seed 33020 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260709_axg15_fullstack.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 20 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 3600 --num_eval_steps 300 --num_samples_from_model 2048 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.18 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_model_sample_export_target_r20_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 384 --sample_export_max_attempts 2048 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_family_cap 8 --sample_export_basin_fingerprint_cap 2 --igp24_generation_strategy mixed --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_sample_export_target_r20_conditioned_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_model_sample_export_target_r20_conditioned.jsonl --output_dir data/igp24/axg15_fullstack_20260709/r20_cuda/cpu_scored_samples_bound1e15 --score_all true --gpu_probe_summary data/igp24/axg15_fullstack_20260709/r20_cuda/gpu_sampler_probe_summary.json --coeff_bound 1000000000000000 --target_r 20 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0 --exp_name axg15_r20_score_bound1e15_20260709`
