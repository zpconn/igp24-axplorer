# IGP24 Split Workflow Report

- Created UTC: `2026-07-10T10:17:39.085175+00:00`
- Source commit: `af8061a5cc018c58d85da4de076c230e0c4ddb4b`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_model_sample_export_target_r8_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_sample_export_target_r8_conditioned_dump/igp24_gpu_sample_export_target_r8_conditioned/20260710T101409Z/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 190.30134727800032 | 91.0 | 204 | 2 | 0.036507938988506794 | 204 | 2 | 2 | 0 | 2 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r8_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_sample_export_target_r8_conditioned_dump --exp_id 20260710T101409Z --seed 34121 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260710_postremediation_exact13879_crossr_axg121.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 8 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 1200 --num_eval_steps 300 --num_samples_from_model 8192 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.1 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_model_sample_export_target_r8_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 12 --sample_export_max_attempts 8192 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like false --sample_export_require_support_gcd_one false --sample_export_require_nonzero_constant true --sample_export_require_target_r true --sample_export_require_local_valid true --sample_export_required_support_patterns '' --sample_export_excluded_support_patterns '' --sample_export_excluded_hashes_jsonl data/igp24/active_learning/axg_training_dataset_20260710_postremediation_exact13879_crossr_axg121.jsonl --sample_export_family_cap 12 --sample_export_basin_fingerprint_cap 3 --igp24_generation_strategy mixed --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_sample_export_target_r8_conditioned_initial_candidates.jsonl`
- CPU score: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_score_sample_export.py data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_model_sample_export_target_r8_conditioned.jsonl --output_dir data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/cpu_scored_samples_bound1e15 --score_all true --gpu_probe_summary data/igp24/axg121_exact13879_odd_escape_20260710/r8_cuda_localvalid_export/gpu_sampler_probe_summary.json --coeff_bound 1000000000000000 --target_r 8 --prime_limit 7 --exact_score_timeout 3 --translation_radius 0 --local_search false --max_local_search_steps 0 --seed 34121 --exp_name axg121_r8_localvalid_score`
