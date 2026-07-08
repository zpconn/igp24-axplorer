# IGP24 Split Workflow Report

- Created UTC: `2026-07-08T00:13:03.507247+00:00`
- Source commit: `dd41dd3857841ae851d89d55de95847433689e19`
- Safety: proxy-only; no exact verifier execution, SAIR calls, network calls, or submission.

## Artifacts

- Sample export JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg_gpu_tiny_20260707/gpu_probe/gpu_model_sample_export.jsonl`
- GPU probe summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg_gpu_tiny_20260707/gpu_probe/gpu_sampler_probe_summary.json`
- GPU train log: `/tmp/igp24_axg1_gpu_tiny_20260707/gpu_sample_export_dump/igp24_gpu_sample_export_probe/axg1_gpu_tiny_20260707_1909/train.log`
- CPU score summary: `/home/zpconn/code/igp24-axplorer/data/igp24/axg_gpu_tiny_20260707/cpu_scored_samples/score_summary.json`
- CPU scored JSONL: `/home/zpconn/code/igp24-axplorer/data/igp24/axg_gpu_tiny_20260707/cpu_scored_samples/scored_samples.jsonl`

## Counts

| gpu_runtime_s | max_gpu_util | exported | decoded | cpu_runtime_s | selected | scored | valid | rejected | unique_hashes | duplicate_hash_records | local_search |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 29.81646273698425 | 95.0 | 1024 | 1021 | 9.067305851029232 | 256 | 256 | 230 | 26 | 256 | 0 | False |

## Commands

- GPU probe: `/usr/bin/python3 train.py --env_name igp24 --exp_name igp24_gpu_sample_export_probe --dump_path /tmp/igp24_axg1_gpu_tiny_20260707/gpu_sample_export_dump --exp_id axg1_gpu_tiny_20260707_1909 --seed 2001 --coeff_bound 4 --gensize 512 --pop_size 384 --ntest 16 --gen_batch_size 64 --max_epochs 1 --max_steps 160 --num_eval_steps 60 --num_samples_from_model 1024 --batch_size 256 --n_layer 6 --n_head 8 --n_embd 512 --max_len 24 --temperature 0.9 --top_k 9 --always_search false --max_local_search_steps 0 --prime_limit 11 --exact_score_timeout 2 --process_pool false --num_workers 1 --cpu false --sample_export_only true --sample_export_path /tmp/igp24_axg1_gpu_tiny_20260707/gpu_model_sample_export.jsonl --igp24_generation_strategy fixed_sparse_template --igp24_ledger_path /tmp/igp24_axg1_gpu_tiny_20260707/gpu_sample_export_initial_candidates.jsonl`
- CPU score: `/usr/bin/python3 scripts/igp24_score_sample_export.py data/igp24/axg_gpu_tiny_20260707/gpu_probe/gpu_model_sample_export.jsonl --output_dir data/igp24/axg_gpu_tiny_20260707/cpu_scored_samples --max_records 256 --gpu_probe_summary data/igp24/axg_gpu_tiny_20260707/gpu_probe/gpu_sampler_probe_summary.json --local_search false --max_local_search_steps 0 --prime_limit 11 --exact_score_timeout 2 --exp_name axg1_gpu_tiny_score_20260707`
