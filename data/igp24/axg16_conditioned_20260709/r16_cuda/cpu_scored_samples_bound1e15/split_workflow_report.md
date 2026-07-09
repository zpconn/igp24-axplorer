# IGP24 Split Workflow Report

- Created UTC: `2026-07-09T15:46:58.155919+00:00`
- Source commit: `b6f832e7addbd679feb5a1f37de8eecbfad546ac`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_sample_export_target_r16_conditioned_dump/igp24_gpu_sample_export_target_r16_conditioned/axg16_target_r16_anti_collapse_20260709_cuda/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 194.5707834509958 | 89.0 | 276 | 10 | 0.5918667180085322 | 276 | 10 | 10 | 0 | 10 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r16_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_sample_export_target_r16_conditioned_dump --exp_id axg16_target_r16_anti_collapse_20260709_cuda --seed 33016 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260709_axg16_conditioned.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 16 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 5400 --num_eval_steps 300 --num_samples_from_model 4096 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.25 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 512 --sample_export_max_attempts 4096 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_family_cap 4 --sample_export_basin_fingerprint_cap 2 --igp24_generation_strategy mixed --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_sample_export_target_r16_conditioned_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py data/igp24/axg16_conditioned_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl --output_dir data/igp24/axg16_conditioned_20260709/r16_cuda/cpu_scored_samples_bound1e15 --target_r 16 --coeff_bound 1000000000000000`
