# IGP24 Split Workflow Report

- Created UTC: `2026-07-10T05:45:18.703703+00:00`
- Source commit: `7f14ff62d2eb52f004506945227a67aac5d5dd03`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_model_sample_export_target_r12_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_sample_export_target_r12_conditioned_dump/igp24_gpu_sample_export_target_r12_conditioned/axg114_r12_postremediation_mixed_loose_top20_20260710_gpu/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 59.562340759002836 | 90.0 | 162 | 9 | 0.3715375649917405 | 162 | 9 | 8 | 1 | 9 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r12_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_sample_export_target_r12_conditioned_dump --exp_id axg114_r12_postremediation_mixed_loose_top20_20260710_gpu --seed 33012 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260710_postremediation.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 12 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 1200 --num_eval_steps 300 --num_samples_from_model 8192 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.1 --top_k 20 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_model_sample_export_target_r12_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 64 --sample_export_max_attempts 8192 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like false --sample_export_require_support_gcd_one false --sample_export_required_support_patterns '' --sample_export_excluded_support_patterns '' --sample_export_excluded_hashes_jsonl data/igp24/active_learning/axg114_hash_exclusions_20260710.jsonl --sample_export_family_cap 8 --sample_export_basin_fingerprint_cap 2 --igp24_generation_strategy mixed --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_sample_export_target_r12_conditioned_initial_candidates.jsonl`
- CPU score: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_score_sample_export.py data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_model_sample_export_target_r12_conditioned.jsonl --output_dir data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/cpu_scored_samples --gpu_probe_summary data/igp24/axg114_postremediation_20260710/r12_cuda_mixed_loose_top20/gpu_sampler_probe_summary.json --score_all true --coeff_bound 1000000000000000 --target_r 12 --prime_limit 11 --exact_score_timeout 0 --local_search false --max_local_search_steps 0 --exp_name axg114_r12_postremediation_score_export`
