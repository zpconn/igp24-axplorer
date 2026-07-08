# IGP24 Split Workflow Report

- Created UTC: `2026-07-08T02:00:00.451731+00:00`
- Source commit: `fa9fc9c9bd9623e1372e490ec5cea2820be0c8e9`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg11_target_r_seeded_20260707/r16/gpu_probe/gpu_model_sample_export_target_r16_seeded.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg11_target_r_seeded_20260707/r16/gpu_probe/gpu_sampler_probe_summary.json`
- GPU train log: `/tmp/igp24_axg11_target_r_seeded_20260707/r16/gpu_sample_export_target_r16_seeded_dump/igp24_gpu_sample_export_target_r16_seeded/axg11_target_r16_seeded_20260707_2055/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg11_target_r_seeded_20260707/r16/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg11_target_r_seeded_20260707/r16/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 27.797531165007968 | 83.0 | 516 | 512 | 5.012495785020292 | 132 | 131 | 120 | 11 | 131 | 0 | False |

## Commands

- GPU probe: `/usr/bin/python3 train.py --env_name igp24 --exp_name igp24_gpu_sample_export_target_r16_seeded --dump_path /tmp/igp24_axg11_target_r_seeded_20260707/r16/gpu_sample_export_target_r16_seeded_dump --exp_id axg11_target_r16_seeded_20260707_2055 --seed 31016 --coeff_bound 4 --target_r 16 --gensize 512 --pop_size 384 --ntest 16 --gen_batch_size 64 --max_epochs 1 --max_steps 160 --num_eval_steps 60 --num_samples_from_model 512 --batch_size 256 --n_layer 4 --n_head 4 --n_embd 256 --max_len 24 --temperature 0.9 --top_k 9 --always_search false --max_local_search_steps 0 --prime_limit 11 --exact_score_timeout 2 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /tmp/igp24_axg11_target_r_seeded_20260707/r16/gpu_model_sample_export_target_r16_seeded.jsonl --sample_export_dedup true --sample_export_max_attempts 512 --sample_export_progress_interval 128 --sample_export_target_r_conditioning_mode seed_bank_prefix --sample_export_seed_bank_jsonl data/igp24/axg_target_r_seed_bank_20260707/target_r_seed_bank.jsonl --sample_export_seed_bank_target_r 16 --sample_export_seed_bank_limit 4 --igp24_generation_strategy fixed_sparse_template --igp24_ledger_path /tmp/igp24_axg11_target_r_seeded_20260707/r16/gpu_sample_export_target_r16_seeded_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py data/igp24/axg11_target_r_seeded_20260707/r16/gpu_probe/gpu_model_sample_export_target_r16_seeded.jsonl --output_dir data/igp24/axg11_target_r_seeded_20260707/r16/cpu_scored_samples --max_records 132 --gpu_probe_summary data/igp24/axg11_target_r_seeded_20260707/r16/gpu_probe/gpu_sampler_probe_summary.json --target_r 16 --coeff_bound 703 --local_search false --max_local_search_steps 0 --prime_limit 11 --exact_score_timeout 2 --exp_name axg11_target_r16_seeded_score_20260707`
