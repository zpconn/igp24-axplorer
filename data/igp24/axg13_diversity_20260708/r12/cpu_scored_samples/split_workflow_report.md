# IGP24 Split Workflow Report

- Created UTC: `2026-07-08T03:10:04.393248+00:00`
- Source commit: `797f42693d437ef1af27ac557f4c27dc1b565a59`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/tmp/igp24_axg13_diversity_20260708/r12/gpu_model_sample_export_target_r12_conditioned.jsonl`
- GPU probe summary: `/tmp/igp24_axg13_diversity_20260708/r12/gpu_sampler_probe_summary.json`
- GPU train log: `/tmp/igp24_axg13_diversity_20260708/r12/gpu_sample_export_target_r12_conditioned_dump/igp24_gpu_sample_export_target_r12_conditioned/axg13_target_r12_diversity_20260708_2207/train.log`
- CPU score summary: `/tmp/igp24_axg13_diversity_20260708/r12/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/tmp/igp24_axg13_diversity_20260708/r12/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 164.2850768439821 | 91.0 | 232 | 108 | 9.38529612601269 | 232 | 108 | 108 | 0 | 108 | 0 | False |

## Commands

- GPU probe: `/usr/bin/python3 train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r12_conditioned --dump_path /tmp/igp24_axg13_diversity_20260708/r12/gpu_sample_export_target_r12_conditioned_dump --exp_id axg13_target_r12_diversity_20260708_2207 --seed 33012 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl /home/zpconn/code/igp24-axplorer/data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl --igp24_training_jsonl_target_rs 12,16,20,24 --coeff_bound 1000000000000000 --target_r 12 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 4800 --num_eval_steps 300 --num_samples_from_model 2048 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.15 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /tmp/igp24_axg13_diversity_20260708/r12/gpu_model_sample_export_target_r12_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 512 --sample_export_max_attempts 2048 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --igp24_generation_strategy mixed --igp24_ledger_path /tmp/igp24_axg13_diversity_20260708/r12/gpu_sample_export_target_r12_conditioned_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py /tmp/igp24_axg13_diversity_20260708/r12/gpu_model_sample_export_target_r12_conditioned.jsonl --output_dir /tmp/igp24_axg13_diversity_20260708/r12/cpu_scored_samples --score_all true --coeff_bound 1000000000000000 --target_r 12 --prime_limit 7 --exact_score_timeout 0 --local_search false --max_local_search_steps 0`
