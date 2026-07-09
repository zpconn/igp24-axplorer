# IGP24 Split Workflow Report

- Created UTC: `2026-07-09T18:32:02.028887+00:00`
- Source commit: `c35cbf97ace324877fa5cb07ff525cebb2364ea5`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/gpu_sample_export_target_r16_conditioned_dump/igp24_gpu_sample_export_target_r16_conditioned/axg18_r16_high_real_escape_20260709/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 122.61002272700716 | 86.0 | 415 | 9 | 0.6408648829965387 | 415 | 9 | 9 | 0 | 9 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r16_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/gpu_sample_export_target_r16_conditioned_dump --exp_id axg18_r16_high_real_escape_20260709 --seed 33016 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260709_axg18_escape.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 16 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 3200 --num_eval_steps 300 --num_samples_from_model 4096 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.18 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 384 --sample_export_max_attempts 4096 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_family_cap 4 --sample_export_basin_fingerprint_cap 2 --igp24_generation_strategy fixed_sparse_template --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r16_cuda/gpu_sample_export_target_r16_conditioned_initial_candidates.jsonl`
- CPU score: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_score_sample_export.py data/igp24/axg18_escape_20260709/r16_cuda/gpu_model_sample_export_target_r16_conditioned.jsonl --output_dir data/igp24/axg18_escape_20260709/r16_cuda/cpu_scored_samples_bound1e15 --score_all true --coeff_bound 1000000000000000 --target_r 16 --exact_score_timeout 0 --local_search false`
