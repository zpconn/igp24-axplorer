# IGP24 Split Workflow Report

- Created UTC: `2026-07-08T23:12:41.415469+00:00`
- Source commit: `72a3aa7fd187c96e224201b77fff140a79d8b3c4`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_model_sample_export_target_r24_conditioned.jsonl`
- GPU probe summary: `/tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_sampler_probe_summary.json`
- GPU train log: `/tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_sample_export_target_r24_conditioned_dump/igp24_gpu_sample_export_target_r24_conditioned/r24_high_real_refinement_20260708_03/train.log`
- CPU score summary: `/tmp/igp24_r24_r16_high_real_refinement_20260708/r24/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/tmp/igp24_r24_r16_high_real_refinement_20260708/r24/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 89.14977109500069 | 87.0 | 568 | 44 | 3.2398677509991103 | 568 | 44 | 36 | 8 | 44 | 0 | False |

## Commands

- GPU probe: `/home/zpconn/code/axplorer/.venv/bin/python train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r24_conditioned --dump_path /tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_sample_export_target_r24_conditioned_dump --exp_id r24_high_real_refinement_20260708_03 --seed 33024 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl --igp24_training_jsonl_target_rs 12,16,20,24 --coeff_bound 1000000000000000 --target_r 24 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 2400 --num_eval_steps 300 --num_samples_from_model 2048 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.25 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_model_sample_export_target_r24_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 256 --sample_export_max_attempts 2048 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_family_cap 24 --sample_export_basin_fingerprint_cap 1 --igp24_generation_strategy mixed --igp24_ledger_path /tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_sample_export_target_r24_conditioned_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py /tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_model_sample_export_target_r24_conditioned.jsonl --output_dir /tmp/igp24_r24_r16_high_real_refinement_20260708/r24/cpu_scored_samples --score_all true --gpu_probe_summary /tmp/igp24_r24_r16_high_real_refinement_20260708/r24/gpu_sampler_probe_summary.json --coeff_bound 1000000000000000 --target_r 24 --prime_limit 7 --exact_score_timeout 0 --local_search false --max_local_search_steps 0 --exp_name r24_high_real_refinement_score_20260708`
