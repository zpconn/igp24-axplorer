# IGP24 Split Workflow Report

- Created UTC: `2026-07-09T20:13:32.874387+00:00`
- Source commit: `29bd6815ca91d5b574b1a8fc9f18bf222a9be297`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_model_sample_export_target_r12_conditioned.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_sampler_probe_summary.json`
- GPU train log: `/home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_sample_export_target_r12_conditioned_dump/igp24_gpu_sample_export_target_r12_conditioned/axg112_r12_score_followup_20260709/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/cpu_scored_samples_bound1e15/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/cpu_scored_samples_bound1e15/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 229.91583214698767 | 84.0 | 1216 | 28 | 2.1560804010077845 | 1216 | 28 | 25 | 3 | 28 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r12_conditioned --dump_path /home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_sample_export_target_r12_conditioned_dump --exp_id axg112_r12_score_followup_20260709 --seed 33012 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260709_axg112_pivot.jsonl --igp24_training_jsonl_target_rs 8,12,16,20,24 --coeff_bound 1000000000000000 --target_r 12 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 2400 --num_eval_steps 300 --num_samples_from_model 8192 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.18 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_model_sample_export_target_r12_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 128 --sample_export_max_attempts 8192 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like false --sample_export_require_support_gcd_one false --sample_export_required_support_patterns '' --sample_export_excluded_support_patterns '' --sample_export_excluded_hashes_jsonl data/igp24/active_learning/axg20_hash_exclusions_20260709.jsonl --sample_export_family_cap 8 --sample_export_basin_fingerprint_cap 3 --igp24_generation_strategy mixed --igp24_ledger_path /home/zpconn/code/igp24-axplorer/data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_sample_export_target_r12_conditioned_initial_candidates.jsonl`
- CPU score: `/home/zpconn/code/axplorer/.venv/bin/python scripts/igp24_score_sample_export.py data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_model_sample_export_target_r12_conditioned.jsonl --output_dir data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/cpu_scored_samples_bound1e15 --gpu_probe_summary data/igp24/axg112_pivot_20260709/r12_score_followup_cuda/gpu_sampler_probe_summary.json --target_r 12 --coeff_bound 1000000000000000 --score_all true --local_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 2 --exp_name axg112_r12_score_followup_score_20260709`
