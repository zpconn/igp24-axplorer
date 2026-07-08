# IGP24 Split Workflow Report

- Created UTC: `2026-07-08T02:35:53.839824+00:00`
- Source commit: `63ce57a2a43a9bdea2296acfbd149be7d998001f`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_model_sample_export_target_r20_conditioned.jsonl`
- GPU probe summary: `/tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_sampler_probe_summary.json`
- GPU train log: `/tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_sample_export_target_r20_conditioned_dump/igp24_gpu_sample_export_target_r20_conditioned/axg12_target_r20_conditioned_20260707_2136/train.log`
- CPU score summary: `/tmp/igp24_axg12_target_r_conditioned_20260707/r20/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/tmp/igp24_axg12_target_r_conditioned_20260707/r20/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 78.13692450698 | 92.0 | 34 | 18 | 1.7819681650144048 | 34 | 18 | 15 | 3 | 18 | 0 | False |

## Commands

- GPU probe: `/usr/bin/python3 train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r20_conditioned --dump_path /tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_sample_export_target_r20_conditioned_dump --exp_id axg12_target_r20_conditioned_20260707_2136 --seed 33020 --encoding_tokens decimal_coefficients --igp24_target_r_conditioning_mode control_token --igp24_training_jsonl /home/zpconn/code/igp24-axplorer/data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl --igp24_training_jsonl_target_rs 12,16,20,24 --coeff_bound 1000000000000000 --target_r 20 --gensize 0 --pop_size 512 --ntest 64 --gen_batch_size 64 --max_epochs 1 --max_steps 2400 --num_eval_steps 300 --num_samples_from_model 768 --batch_size 128 --n_layer 4 --n_head 4 --n_embd 256 --max_len 640 --temperature 0.9 --top_k 12 --always_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_model_sample_export_target_r20_conditioned.jsonl --sample_export_dedup true --sample_export_max_attempts 768 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode control_token --igp24_generation_strategy fixed_sparse_template --igp24_ledger_path /tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_sample_export_target_r20_conditioned_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py /tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_model_sample_export_target_r20_conditioned.jsonl --output_dir /tmp/igp24_axg12_target_r_conditioned_20260707/r20/cpu_scored_samples --score_all true --gpu_probe_summary /tmp/igp24_axg12_target_r_conditioned_20260707/r20/gpu_sampler_probe_summary.json --target_r 20 --coeff_bound 1000000000000000 --local_search false --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 0 --exp_name axg12_target_r20_conditioned_score_20260707`
