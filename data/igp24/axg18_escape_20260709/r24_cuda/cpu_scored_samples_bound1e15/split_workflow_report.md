# IGP24 Split Workflow Report

- Created UTC: `2026-07-09T18:26:36.288811+00:00`
- Source commit: `c35cbf97ace324877fa5cb07ff525cebb2364ea5`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/gpu_model_sample_export_target_r24_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/gpu_sample_export_target_r24_conditioned_dump/igp24_gpu_sample_export_target_r24_conditioned/axg18_r24_high_real_escape_20260709/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 112.02654828000232 | 86.0 | 328 | 6 | 0.5548682320077205 | 328 | 6 | 6 | 0 | 6 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r24_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/gpu_sample_export_target_r24_conditioned_dump --exp_id axg18_r24_high_real_escape_20260709 --seed 33024 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260709_axg18_escape.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 24 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 3000 --num_eval_steps 300 --num_samples_from_model 3072 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.12 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/gpu_model_sample_export_target_r24_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 320 --sample_export_max_attempts 3072 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_family_cap 3 --sample_export_basin_fingerprint_cap 2 --igp24_generation_strategy fixed_sparse_template --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg18_escape_20260709/r24_cuda/gpu_sample_export_target_r24_conditioned_initial_candidates.jsonl`
- CPU score: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_score_sample_export.py data/igp24/axg18_escape_20260709/r24_cuda/gpu_model_sample_export_target_r24_conditioned.jsonl --output_dir data/igp24/axg18_escape_20260709/r24_cuda/cpu_scored_samples_bound1e15 --score_all true --coeff_bound 1000000000000000 --target_r 24 --exact_score_timeout 0 --local_search false`
