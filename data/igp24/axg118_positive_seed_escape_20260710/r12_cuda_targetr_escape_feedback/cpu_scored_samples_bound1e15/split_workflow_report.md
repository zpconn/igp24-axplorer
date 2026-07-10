# IGP24 Split Workflow Report

- Created UTC: `2026-07-10T08:17:20.704322+00:00`
- Source commit: `fdc012ed2fbd6923d71cda3c33f555676e9d4eed`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_model_sample_export_target_r12_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_sample_export_target_r12_conditioned_dump/igp24_gpu_sample_export_target_r12_conditioned/20260710T081638Z/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 32.582925084992894 | 90.0 | 48 | 1 | 0.025668929010862485 | 48 | 1 | 1 | 0 | 1 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r12_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_sample_export_target_r12_conditioned_dump --exp_id 20260710T081638Z --seed 33012 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260710_postremediation_axg118_escape.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 12 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 700 --num_eval_steps 233 --num_samples_from_model 1024 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.1 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_model_sample_export_target_r12_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 8 --sample_export_max_attempts 1024 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_require_nonzero_constant true --sample_export_require_target_r true --sample_export_required_support_patterns '' --sample_export_excluded_support_patterns '' --sample_export_excluded_hashes_jsonl data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_submission_rows.jsonl --sample_export_family_cap 6 --sample_export_basin_fingerprint_cap 3 --igp24_generation_strategy mixed --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_sample_export_target_r12_conditioned_initial_candidates.jsonl`
- CPU score: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_score_sample_export.py data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_model_sample_export_target_r12_conditioned.jsonl --output_dir data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/cpu_scored_samples_bound1e15 --score_all true --gpu_probe_summary data/igp24/axg118_positive_seed_escape_20260710/r12_cuda_targetr_escape_feedback/gpu_sampler_probe_summary.json --coeff_bound 1000000000000000 --target_r 12 --prime_limit 7 --exact_score_timeout 2 --translation_radius 0 --local_search false --max_local_search_steps 0 --seed 34118 --exp_name axg118_r12_escape_feedback_score`
