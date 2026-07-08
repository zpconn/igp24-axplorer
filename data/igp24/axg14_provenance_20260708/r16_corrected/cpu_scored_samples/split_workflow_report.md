# IGP24 Split Workflow Report

- Created UTC: `2026-07-08T04:06:59.024633+00:00`
- Source commit: `2a35f72fedb2ba938b30aa5cf60e5664a2d42759`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_model_sample_export_target_r16_conditioned.jsonl`
- GPU probe summary: `/tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_sampler_probe_summary.json`
- GPU train log: `/tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_sample_export_target_r16_conditioned_dump/igp24_gpu_sample_export_target_r16_conditioned/axg14_target_r16_provenance_20260708_0350/train.log`
- CPU score summary: `/tmp/igp24_axg14_provenance_20260708/r16_corrected/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/tmp/igp24_axg14_provenance_20260708/r16_corrected/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 235.93067599396454 | 87.0 | 124 | 40 | 2.7441251249983907 | 124 | 40 | 40 | 0 | 40 | 0 | False |

## Commands

- GPU probe: `/usr/bin/python3 train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r16_conditioned --dump_path /tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_sample_export_target_r16_conditioned_dump --exp_id axg14_target_r16_provenance_20260708_0350 --seed 33016 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl /home/zpconn/code/igp24-axplorer/data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl --igp24_training_jsonl_target_rs 12,16,20,24 --coeff_bound 1000000000000000 --target_r 16 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 7200 --num_eval_steps 300 --num_samples_from_model 3072 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 1.15 --top_k -1 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_model_sample_export_target_r16_conditioned.jsonl --sample_export_dedup true --sample_export_unique_target 384 --sample_export_max_attempts 3072 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --sample_export_avoid_even_support_like true --sample_export_require_support_gcd_one true --sample_export_family_cap 0 --sample_export_basin_fingerprint_cap 8 --igp24_generation_strategy mixed --igp24_ledger_path /tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_sample_export_target_r16_conditioned_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py /tmp/igp24_axg14_provenance_20260708/r16_corrected/gpu_model_sample_export_target_r16_conditioned.jsonl --output_dir /tmp/igp24_axg14_provenance_20260708/r16_corrected/cpu_scored_samples --score_all true --coeff_bound 1000000000000000 --target_r 16 --prime_limit 7 --exact_score_timeout 0 --local_search false --max_local_search_steps 0`
