# IGP24 Live TODO

This file is the working project log for the Axplorer-based IGP24 candidate
generator. Keep it current as implementation, tests, smoke runs, and benchmark
results change.

## Current Status

- Branch: `igp24-dev`
- Remote target: `zpconn/igp24-axplorer`
- Last pull: 2026-07-04, `git pull --ff-only` -> already up to date before
  GPU-readiness and training-smoke work.
- Active focus: add a small GPU-readiness milestone that verifies CUDA/PyTorch
  availability, runs a tiny IGP24 CPU data-generation baseline and a tiny GPU
  training smoke, and documents when GPU training should become the main path.
  This remains proxy-only: no exact `24Tt` labels, no MAGMA/PARI execution, no
  SAIR/network calls, and no auto-submission behavior.

## Stage 0: Scaffold

- [done] Register `igp24` Axplorer environment.
- [done] Represent monic degree-24 polynomials as `[a0, ..., a23]`.
- [done] Export candidates as `[a0, ..., a23, 1]`.
- [done] Add exact SymPy utilities for construction, validation, irreducibility,
  squarefreeness, discriminant, real-root count, translations, modular factor
  patterns, canonical hashes, and JSONL ledger records.
- [done] Add PARI, MAGMA, and SAIR verifier stubs that do not run in the
  training loop and do not auto-submit.
- [done] Add fast tests for stage-0 behavior.
- [done] Add a simple project README.

## Stage 1: Candidate Generation

- [done] Add generation strategies beyond uniform random coefficients.
  - [done] Sparse coefficient vectors.
  - [done] Low-height biased dense vectors.
  - [done] Lower-degree coefficient bias.
  - [done] Simple structured binomial/trinomial-like seeds.
- [done] Make generation strategy configurable from the CLI with
  `--igp24_generation_strategy`.
- [done] Record generation strategy in candidate metadata and ledger records.
- [done] Compare strategy yield and score quality across short benchmark
  runs.
- [done] Seed NumPy from `--seed` in the IGP24 environment so short
  process-pool-off benchmarks are reproducible.
- [done] Adjust default `mixed` weights conservatively toward the stronger
  small-sample strategies:
  `uniform:0.10,low_height:0.20,sparse:0.25,lower_degree:0.20,structured:0.25`.
- [done] Add an experimental `target_r=4`-friendlier generation
  strategy.
  - [done] Implement a bounded near-product `four_real_seed` strategy
    based on perturbed `(x^2-a)(x^2-b)(x^20+1)` seeds.
  - [done] Record strategy-specific metadata in ledger records.
  - [done] Add focused generation, metadata, and determinism tests.
  - [done] Benchmark against current `sparse` and `mixed` baselines on
    `target_r=4`.
- [done] Add opt-in target-specific generation presets.
  - [done] Add `--igp24_generation_preset` with `none`, `r0`, `r2`,
    and `r4` choices.
  - [done] Preserve default behavior when no preset is selected.
  - [done] Record preset name, target-r intent, resolved strategy, and
    resolved mixed weights in ledger metadata.
  - [done] Add focused preset tests and benchmark helper support.
  - [done] Benchmark the `r4` preset against baseline `mixed` and explicit
    `four_real_seed`.
- [done] Validate and tune the `target_r=4` preset tradeoff.
  - [done] Add benchmark-helper labels for r4 mixed-weight variants.
  - [done] Run a larger CPU-only `target_r=4` benchmark than the previous
    4-seed preset run.
  - [done] Compare baseline `mixed`, explicit `four_real_seed`,
    current `preset_r4`, and r4 mixed-weight variants.
  - [done] Interpret target-r yield versus peak proxy score before changing
    any preset or default.

## Stage 1: Scoring And Metadata

- [done] Preserve proxy-only scoring while making score components easier
  to inspect.
  - [done] Store score component breakdown in each ledger record.
  - [done] Keep `target_t` metadata-only unless exact external verification
    is actually performed.
  - [done] Keep invalid rejection reasons explicit and stable.
- [done] Add target real-root-count benchmark reporting.
  - [done] Extend benchmark helper with `--target_rs`.
  - [done] Summarize target-r match count, match rate, and best matching
    score.
  - [done] Run short untargeted vs `target_r=2` comparison.
- [done] Run larger per-strategy target real-root-count comparisons
  across `target_r=none,0,2,4`.
  - [done] Add aggregate strategy/target reporting to the benchmark
    helper so multi-seed runs are easier to audit.
  - [done] Run the larger CPU-only benchmark with at least `sparse`,
    `structured`, and `mixed`.
  - [done] Record commands, artifact paths, result tables, and
    interpretation before considering any default tuning.

## Stage 1: Local Search

- [done] Improve bounded local search observability.
  - [done] Track attempted, accepted, and rejected move counts.
  - [done] Track the accepted move type.
  - [done] Record whether accepted moves improved height, discriminant,
    root-count match, or modular diversity.
  - [done] Preserve determinism under a fixed seed.

## Stage 1: CLI And Smoke Runs

- [done] Add practical short CPU-only commands to documentation.
- [done] Run a small reproducible CPU-only generation smoke.
- [done] Record exact command, runtime, valid candidate count, best score, and
  ledger path below.
- [in_progress] Add a small GPU-readiness and training-smoke milestone.
  - [done] Inspect and document current `train.py` CUDA support.
    - Result: `--cpu true` forces CPU; otherwise `train.py` selects MPS when
      available and CUDA after that, moves the model and training/evaluation
      batches to `args.device`, and logs CUDA memory during epochs. It does
      not preflight `torch.cuda.is_available()`, so the smoke must probe
      PyTorch CUDA before running GPU training.
  - [pending] Confirm `nvidia-smi` GPU visibility and PyTorch CUDA
    availability.
  - [done] Add a lightweight GPU-smoke helper only if it improves
    reproducibility of command execution and artifact summaries.
    - Result: `scripts/igp24_gpu_smoke.py` writes
      `gpu_smoke_summary.json` and `gpu_smoke_report.md`, keep all runs
      proxy-only, and skip GPU training when PyTorch CUDA is unavailable.
  - [done] Add focused tests for pure parsing/reporting logic.
    - Result: `tests/test_igp24_gpu_smoke.py` covers probe parsing, command
      construction, train-log inspection, ledger summary, and recommendation
      logic without requiring GPU hardware.
  - [done] Update README and NOTES with when to use GPU training.
  - [pending] Run a tiny CPU data-generation baseline and a tiny GPU-enabled
    training smoke under `/tmp/igp24_gpu_smoke_20260704`.
  - [pending] Compare return codes, runtimes, valid candidates, ledger record
    counts, metadata completeness, and whether GPU was actually used.
  - [pending] Document whether to keep CPU proxy-search primary, switch to GPU
    training, or run both in parallel.
- [done] Add a reusable per-strategy benchmark helper.
  - [done] Add `scripts/igp24_benchmark.py` to run short CPU-only `train.py`
    jobs and summarize JSONL ledgers.
  - [done] Add fast tests for benchmark summary aggregation.
  - [done] Verify helper CLI with `--help`.
  - [done] Run the helper across all generation strategies.

## Tests And Checks

- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
  - Latest result: 35 passed in 0.74s after fixed-sparse-template work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
  - Latest result: passed after fixed-sparse-template work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`.
  - Latest result: passed after safe review-batch helper work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`.
  - Latest result: passed after adding the safe review-batch helper.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`.
  - Latest result: passed after adding the safe offline-verifier preparation
    helper.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`.
  - Latest result: passed after adding `fixed_sparse_template`.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --help`.
  - Latest result: passed after adding the GPU readiness helper.
- [done] Run an import check proving `square`, `isosceles`, `sphere`, and
  `igp24` remain discoverable.
  - Command: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- [blocked] Run literal `python -m pytest`, or record the blocker.
  - Latest result: blocked with `/bin/bash: line 1: python: command not found`.
- [done] If local dependency issues block the literal command, record the
  exact blocker and run the closest available equivalent.

## Command Log

- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before GPU-readiness and training-smoke work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_smoke.py`
  - Result: 6 passed in 0.02s after adding the GPU readiness helper.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --help`
  - Result: passed; helper exposes output directory, repo root, timeout,
    fixed run id, forced GPU train, and strict-mode options.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_smoke.py tests/test_igp24_gpu_smoke.py`
  - Result: passed after adding the GPU readiness helper and tests.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before fixed-support sparse template generation
    work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 24 passed in 1.16s after adding `fixed_sparse_template`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src/envs/igp24.py scripts/igp24_benchmark.py tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: passed after adding `fixed_sparse_template`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper documents `fixed_sparse_template` as a direct
    benchmark strategy alongside `quartic_lift`.
- 2026-07-04:
  `/usr/bin/time -f elapsed_seconds %e env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,fixed_sparse_template --seeds 1101,1102,1103,1104 --target_rs 2 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_fixed_sparse_template_bench_20260704`
  - Result: command-format blocker; `/usr/bin/time` received `%e` as the
    command because the format string was not quoted. Reran with portable
    `time -p`.
- 2026-07-04:
  `/usr/bin/time -p env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,fixed_sparse_template --seeds 1101,1102,1103,1104 --target_rs 2 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_fixed_sparse_template_bench_20260704`
  - Result: passed; 12 CPU-only `target_r=2` benchmark runs completed in
    `real 50.42` seconds.
- 2026-07-04: audited
  `/tmp/igp24_fixed_sparse_template_bench_20260704/summary.json`.
  - Result: 12 rows, all return codes 0, all metadata complete, strategies
    were `fixed_sparse_template`, `sparse`, and `structured`, target set was
    `[2]`, valid candidates totaled 216, ledger records totaled 391, and
    target-r matching records totaled 258.
- 2026-07-04: audited fixed-template benchmark ledger metadata.
  - Result: 130 `fixed_sparse_template` ledger rows checked; no missing
    template/support/bound metadata. Template counts were `low_high_bridge`: 48,
    `divisor_ladder_3`: 39, `r2_tail_bridge`: 23, and `r2_even_spine`: 20.
    Local search introduced 100 extra nonzero outside-template indices across
    those rows, recorded under `fixed_sparse_extra_nonzero_indices`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 35 passed in 0.74s after fixed-sparse-template work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before safe offline-verifier preparation
    workflow work.
- 2026-07-04: `python3 -c "import shutil; print('gp', shutil.which('gp')); print('magma', shutil.which('magma'))"`
  - Result: `gp None`; `magma None`. Local exact verifier binaries are not on
    PATH at setup time, so the first smoke should remain dry-run/preparation
    only and record the blocker.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
  - Result: 5 passed in 0.03s after adding the offline-verifier preparation
    helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_offline_verify.py tests/test_igp24_offline_verify.py`
  - Result: passed after adding the offline-verifier preparation helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
  - Result: passed; CLI documents review-batch input, output directory,
    explicit `--run_pari`/`--run_magma` opt-ins, executable names, timeout, and
    repo-root options.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_r4_offline_verify_20260704`
  - Result: passed in default preparation-only mode. Loaded 8 review records,
    wrote `offline_verification_manifest.json`, `pari_input.gp`,
    `magma_input.m`, and `verification_plan.md`. Local `gp` and `magma`
    availability were both false; no local verifier execution was requested or
    performed.
- 2026-07-04: audited `/tmp/igp24_r4_offline_verify_20260704`.
  - Result: selected record count is 8, selected hashes are unique, coefficient
    shape is recorded as length 25 with leading coefficient 1, PARI/GP and
    MAGMA are unavailable on PATH, `pari_executed=false`,
    `magma_executed=false`, `dry_run_preparation_only=true`, and safety flags
    record no network calls, no SAIR submission, no auto-submission, no exact
    group-label parsing, and no exact group claims. No `*raw_output*` files
    were created.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 33 passed in 0.95s after safe offline-verifier preparation helper
    work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before safe review-batch tooling work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_review_shortlist.py`
  - Result: 3 passed in 0.01s after adding the review-batch helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_review_shortlist.py tests/test_igp24_review_shortlist.py`
  - Result: passed after adding the review-batch helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`
  - Result: initially exposed a direct-execution import-path blocker
    (`ModuleNotFoundError: No module named 'scripts'`). Fixed the helper's
    repo-root path setup and reran successfully; CLI documents shortlist input,
    output directory, batch size, sort key, strategy cap/minimum, source-ledger
    following, and repo-root options.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py /tmp/igp24_r4_shortlist_20260704 --batch_size 8 --min_strategies 2 --per_strategy_cap 6 --output_dir /tmp/igp24_r4_review_batch_20260704`
  - Result: passed; loaded 25 shortlist records and selected 8 review records.
    Top score was 10214.147570701043. Strategy counts were `quartic_lift`: 6
    and `four_real_seed`: 2.
- 2026-07-04: audited `/tmp/igp24_r4_review_batch_20260704`.
  - Result: `review_report.md`, `verification_batch.jsonl`,
    `verification_coefficients.txt`, and `manifest.json` exist. The batch has
    8 rows, 8 unique canonical hashes, all exported coefficient vectors have
    length 25 and end in fixed leading coefficient 1, every row records source
    ledger and source shortlist paths, `verified_group_label` is null for every
    row, and manifest safety flags record proxy-only/review-export-only with no
    verifier execution, submission, network calls, or exact group claims.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 28 passed in 0.92s after safe review-batch helper work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before safe shortlist/export helper work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_shortlist.py`
  - Result: 3 passed in 0.01s after adding the shortlist/export helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_shortlist.py tests/test_igp24_shortlist.py`
  - Result: passed after adding the shortlist/export helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`
  - Result: passed; helper documents input paths, output directory,
    target-r filtering, strategy filtering, top-N limit, sort key, and
    ascending sort option.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py /tmp/igp24_r4_second_confirm_20260704 /tmp/igp24_r4_dual_quality_confirm_20260704 --target_r 4 --limit 25 --output_dir /tmp/igp24_r4_shortlist_20260704`
  - Result: passed; loaded 4,870 source records and selected 25 deduplicated
    `target_r=4` proxy candidates. Top score was 10214.147570701043.
    Strategy counts were `quartic_lift`: 23 and `four_real_seed`: 2.
- 2026-07-04: audited `/tmp/igp24_r4_shortlist_20260704`.
  - Result: `shortlist.jsonl`, `coefficients.json`, `coefficients.txt`, and
    `manifest.json` exist. The shortlist has 25 rows, 25 unique canonical
    hashes, all real-root counts are 4, all exported coefficient vectors have
    length 25 and end in fixed leading coefficient 1, all rows include source
    ledger paths, scores are sorted descending, and manifest safety flags show
    proxy-only/export-only with no verifier execution or submission.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 25 passed in 1.03s after safe shortlist/export helper work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before second r4 preset confirmation work.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies preset_r4,quartic_lift,mix_r4_dual_yield,mix_r4_dual_quality,four_real_seed,mix_r4_dual_balanced --seeds 1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_second_confirm_20260704`
  - Result: passed; 96 CPU-only `target_r=4` confirmation runs completed in
    397.34 seconds wall-clock.
- 2026-07-04: audited
  `/tmp/igp24_r4_second_confirm_20260704/summary.json`.
  - Result:
    `96 True True ['four_real_seed', 'mix_r4_dual_balanced', 'mix_r4_dual_quality', 'mix_r4_dual_yield', 'preset_r4', 'quartic_lift'] [4]`
    and `1715 2821 1887`.
- 2026-07-04: audited
  `/tmp/igp24_r4_second_confirm_20260704/aggregate_summary.json`.
  - Result: 6 aggregate rows; required aggregate fields for match rate,
    average best, average mean, best score, and local-search acceptance were
    present.
- 2026-07-04: inspected all second-confirmation dual-mix ledgers for mix
  metadata.
  - Result: 1,403 dual-label ledger records checked, no mixed-weight metadata
    mismatches. Observed strategy mix was `dual_yield`: 372
    `four_real_seed`, 104 `quartic_lift`; `dual_quality`: 325
    `quartic_lift`, 132 `four_real_seed`; `dual_balanced`: 228
    `four_real_seed`, 202 `quartic_lift`, 40 `sparse`.
- 2026-07-04: combined the prior 12-seed confirmation with the fresh 16-seed
  block for a 28-seed comparison.
  - Result: `four_real_seed` had the highest combined match rate at 0.702;
    `mix_r4_dual_quality` had the strongest combined average best score
    10204.712 and average mean score 10131.587; `quartic_lift` kept the best
    single proxy score at 10214.148; `mix_r4_dual_yield` remained a middle
    tradeoff at 0.694 match rate and 10129.761 average mean; `preset_r4`
    trailed at 0.585 match rate and 10108.354 average mean.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.68s after second r4 preset confirmation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before larger `mix_r4_dual_quality`
    confirmation work.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies preset_r4,four_real_seed,quartic_lift,mix_r4_dual_quality,mix_r4_dual_yield,mix_r4_dual_balanced --seeds 901,902,903,904,905,906,907,908,909,910,911,912 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_dual_quality_confirm_20260704`
  - Result: passed; 72 CPU-only `target_r=4` confirmation runs completed in
    289.85 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_dual_quality_confirm_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `72 True True ['four_real_seed', 'mix_r4_dual_balanced', 'mix_r4_dual_quality', 'mix_r4_dual_yield', 'preset_r4', 'quartic_lift'] [4]`
    and `1282 2049 1317`.
- 2026-07-04: inspected all confirmation dual-mix ledgers for mix metadata.
  - Result: 1,027 dual-label ledger records checked, no mixed-weight metadata
    mismatches. Observed strategy mix was `dual_yield`: 244
    `four_real_seed`, 91 `quartic_lift`; `dual_quality`: 244
    `quartic_lift`, 98 `four_real_seed`; `dual_balanced`: 162
    `quartic_lift`, 146 `four_real_seed`, 42 `sparse`.
- 2026-07-04: checked `resolve_generation_preset('r4', 'uniform', 'uniform:1')`.
  - Result: `preset_r4` still resolves to `mixed` with
    `four_real_seed:0.8,sparse:0.2`; no preset retune was applied.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.77s after larger r4 dual-quality confirmation
    work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before benchmark-only dual-family r4 mix work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_benchmark.py`
  - Result: 6 passed in 0.01s after adding benchmark-only dual r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts tests`
  - Result: passed after adding benchmark-only dual r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper mentions `mix_r4_dual_yield`,
    `mix_r4_dual_quality`, and `mix_r4_dual_balanced`.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies four_real_seed,quartic_lift,preset_r4,mix_r4_dual_yield,mix_r4_dual_quality,mix_r4_dual_balanced --seeds 801,802,803,804,805,806 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_dual_mix_bench_20260704`
  - Result: passed; 36 CPU-only `target_r=4` dual-mix benchmark runs
    completed in 150.98 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_dual_mix_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `36 True True ['four_real_seed', 'mix_r4_dual_balanced', 'mix_r4_dual_quality', 'mix_r4_dual_yield', 'preset_r4', 'quartic_lift'] [4]`
    and `640 1046 718`.
- 2026-07-04: inspected all dual-mix benchmark ledgers for mix metadata.
  - Result: 537 dual-label ledger records checked, no mixed-weight metadata
    mismatches. Observed strategy mix was `dual_yield`: 134 `four_real_seed`,
    37 `quartic_lift`; `dual_quality`: 120 `quartic_lift`, 60
    `four_real_seed`; `dual_balanced`: 84 `four_real_seed`, 86
    `quartic_lift`, 16 `sparse`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.68s after dual-family r4 mix work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after dual-family r4 mix work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper mentions the dual r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before Stage 2 `target_r=4`
    structured-family work.
- 2026-07-04: local scorer probe for quartic-lift templates
  `(y-a)(y-b)(y+c)(y+d)` with `y=x^6` and small off-support perturbations at
  `coeff_bound=4`.
  - Result: two bounded root templates were available. In 200-sample probes,
    odd perturbations produced 149 valid records with 77 at `r=4`,
    near-multiple perturbations produced 147 valid records with 73 at `r=4`,
    and all non-support perturbations produced 131 valid records with 79 at
    `r=4`. This justifies implementing a bounded `quartic_lift` strategy for
    comparison.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 22 passed in 0.85s after adding `quartic_lift`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src tests scripts`
  - Result: passed after adding `quartic_lift`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after adding `quartic_lift`.
- 2026-07-04: `quartic_lift` template probe through
  `IGP24DataPoint._quartic_lift_templates()` at `coeff_bound=4`.
  - Result: bounded templates are `(1,2,1,1)` with quartic coefficients
    `[2,1,-3,-1,1]` and `(1,3,1,1)` with `[3,2,-4,-2,1]`.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies mixed,four_real_seed,preset_r4,quartic_lift --seeds 701,702,703,704,705,706 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_quartic_lift_bench_20260704`
  - Result: passed; 24 CPU-only `target_r=4` comparison runs completed in
    104.35 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_quartic_lift_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `24 True True ['four_real_seed', 'mixed', 'preset_r4', 'quartic_lift'] [4]`
    and `430 708 391`.
- 2026-07-04: inspected `quartic_lift` benchmark ledgers for metadata.
  - Result: all six sampled `quartic_lift` run ledgers included
    `strategy='quartic_lift'`, the quartic-lift seed template, core support
    `[0,6,12,18]`, quartic coefficients, and perturbation coefficients.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.68s after `quartic_lift` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after `quartic_lift` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper mentions `quartic_lift`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before larger `target_r=4` preset validation.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_benchmark.py`
  - Result: 6 passed in 0.02s after adding benchmark-only r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts tests`
  - Result: passed after adding benchmark-only r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper documents `mix_r4_yield`,
    `mix_r4_balanced`, and `mix_r4_diverse` benchmark-only labels.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies mixed,four_real_seed,preset_r4,mix_r4_yield,mix_r4_balanced,mix_r4_diverse --seeds 601,602,603,604,605,606 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_mix_variant_bench_20260704`
  - Result: passed; 36 CPU-only `target_r=4` tradeoff runs completed in
    157.13 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_mix_variant_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `36 True True ['four_real_seed', 'mix_r4_balanced', 'mix_r4_diverse', 'mix_r4_yield', 'mixed', 'preset_r4'] [4]`
    and `646 1089 555`.
- 2026-07-04: inspected r4 mix-variant ledgers for metadata.
  - Result: `mix_r4_yield`, `mix_r4_balanced`, and `mix_r4_diverse` records
    included the intended resolved mixed strategy weights.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 21 passed in 0.62s after r4 mix validation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after r4 mix validation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after r4 mix validation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 21 passed in 1.00s after adding target-specific preset support.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src tests scripts`
  - Result: passed after adding target-specific preset support.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper documents `preset_r0`, `preset_r2`, and
    `preset_r4` benchmark labels.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies mixed,four_real_seed,preset_r4 --seeds 501,502,503,504 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_preset_bench_20260704`
  - Result: passed; 12 CPU-only `target_r=4` preset benchmark runs completed
    in 53.88 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_preset_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result: `12 True True ['four_real_seed', 'mixed', 'preset_r4'] [4]`
    and `215 379 180`.
- 2026-07-04: inspected `preset_r4` benchmark ledgers for metadata.
  - Result: 125 preset ledger records included `generation_preset='r4'`,
    `preset_target_r=4`, `resolved_generation_strategy='mixed'`, and resolved
    mixed weights `four_real_seed:0.8,sparse:0.2`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 21 passed in 0.66s after target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before `target_r=4` generation work.
- 2026-07-04: local scorer probe for odd-perturbed
  `(x^2-a)(x^2-b)(x^20+1)` seeds at `coeff_bound=4`.
  - Result: across three 200-sample probes, valid samples had high `r=4`
    representation; this justifies trying a small explicit generator strategy.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 18 passed in 0.70s after adding `four_real_seed`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src tests scripts`
  - Result: passed after adding `four_real_seed`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after adding `four_real_seed`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 train.py --env_name igp24 --help`
  - Result: passed; this code path prints global `train.py` options only.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,mixed,four_real_seed --seeds 401,402,403,404 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_four_real_seed_bench_20260704`
  - Result: passed; 12 CPU-only `target_r=4` benchmark runs completed in
    52.10 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_four_real_seed_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result: `12 True True ['four_real_seed', 'mixed', 'sparse'] [4]` and
    `216 380 144`.
- 2026-07-04: inspected `four_real_seed` benchmark ledgers for metadata.
  - Result: 123 `four_real_seed` ledger records included
    `target_r_heuristic=4`, the perturbed seed template, and perturbation
    metadata.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 18 passed in 0.65s after `four_real_seed` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after `four_real_seed` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after `four_real_seed` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before larger target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_benchmark.py`
  - Result: 5 passed in 0.02s after adding aggregate benchmark summaries.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts tests`
  - Result: passed after adding aggregate benchmark summaries.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after adding aggregate benchmark summaries.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,mixed --seeds 301,302,303,304 --target_rs none,0,2,4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_target_r_bench_larger_20260704`
  - Result: passed; 48 larger CPU-only target-r benchmark runs completed in
    193.26 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_target_r_bench_larger_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['target_r'] for r in data}, key=lambda x: -1 if x is None else x)); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data))"`
  - Result: `48 True True [None, 0, 2, 4]` and `864 1561`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 18 passed in 0.70s after larger target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after larger target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: fast-forwarded README update from `f60e285` to `9b00f3d`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 17 passed in 0.86s after adding target-r benchmark summary tests.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after adding target-r benchmark helper support.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; `--target_rs` is listed in the helper usage.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,mixed --seeds 201,202 --target_rs none,2 --coeff_bound 4 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 3 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_target_r_bench`
  - Result: passed; 12 short CPU-only target-r benchmark runs completed.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 17 passed in 0.64s on final target-r benchmark check.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed on final target-r benchmark check.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 13 passed in 1.04s for the initial benchmark helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; printed benchmark helper usage.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies uniform,low_height,sparse,lower_degree,structured,mixed --seeds 101,102 --coeff_bound 4 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 3 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_strategy_bench_final`
  - Result: passed; 12 short CPU-only runs completed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 16 passed in 0.64s after valid-count parser, mixed weights, and
    seed-reset fixes.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after valid-count parser, mixed weights, and seed-reset
    fixes.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 16 passed in 0.68s on final check.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed on final check.
- 2026-07-03: `git pull --ff-only`
  - Result: already up to date.
- 2026-07-03: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 11 passed in 0.66s after generation/scoring/local-search metadata
    changes.
- 2026-07-03: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests`
  - Result: passed.
- 2026-07-03: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-03: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-03:
  `/usr/bin/time -f 'elapsed_seconds %e' bash -lc 'PYTHONPATH=/tmp/igp24_pydeps python3 train.py --env_name igp24 --exp_name igp24_stage1_mixed_smoke --dump_path /tmp/igp24_stage1_smoke --seed 123 --coeff_bound 4 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --data_generation_only true --always_search true --max_local_search_steps 3 --prime_limit 11 --exact_score_timeout 3 --process_pool false --num_workers 1 --cpu true --igp24_generation_strategy mixed --igp24_sparse_terms 4 --igp24_low_height_bound 2 --igp24_ledger_path /tmp/igp24_stage1_mixed_candidates.jsonl'`
  - Result: passed, `elapsed_seconds 5.51`.

## Benchmark And Smoke Results

### 2026-07-03 Mixed Strategy CPU Smoke

- Command: see command log above.
- Runtime: 5.51 seconds wall-clock from `/usr/bin/time`.
- Generated valid examples reported by Axplorer stats: 12.
- Score summary:
  - Mean: 9928.237993556737.
  - Median: 9931.467170953914.
  - Max/best score: 9943.432289451468.
- Ledger path: `/tmp/igp24_stage1_mixed_candidates.jsonl`.
- Ledger records: 21 unique canonical hashes, 44K.
- Strategy mix in ledger:
  - `low_height`: 6.
  - `lower_degree`: 2.
  - `sparse`: 5.
  - `structured`: 2.
  - `uniform`: 6.
- Best strategy: `low_height`.
- Best canonical hash:
  `bb48609ade17fbf3a8e958ccaa87a5b39353bb4de00ccbbb8d617cd04c0cd484`.
- Metadata check: every ledger record included `score_components`,
  `generation_metadata`, and `local_search_metadata`.
- Local search telemetry: 12 ledger records included nonzero attempted move
  counts.

### 2026-07-04 Per-Strategy CPU Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_strategy_bench_final`.
- Summary files:
  - `/tmp/igp24_strategy_bench_final/summary.json`
  - `/tmp/igp24_strategy_bench_final/summary.jsonl`
- Configuration:
  - Strategies: `uniform`, `low_height`, `sparse`, `lower_degree`,
    `structured`, `mixed`.
  - Seeds: `101`, `102`.
  - `coeff_bound=4`, `gensize=12`, `max_local_search_steps=3`,
    `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- All 12 runs returned code 0.
- All summary records included parsed valid-candidate counts and complete
  score/generation/local-search metadata.

| Strategy | Runs | Avg Runtime | Valid Total | Ledger Records | Avg Best | Avg Mean | Best | Local Acceptance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `uniform` | 2 | 5.08s | 24 | 44 | 9929.100 | 9909.405 | 9933.489 | 0.507 |
| `low_height` | 2 | 4.73s | 24 | 45 | 9950.229 | 9932.816 | 9950.780 | 0.507 |
| `sparse` | 2 | 2.74s | 24 | 40 | 9957.878 | 9933.097 | 9971.765 | 0.486 |
| `lower_degree` | 2 | 3.24s | 24 | 43 | 9945.981 | 9932.596 | 9947.996 | 0.478 |
| `structured` | 2 | 2.60s | 23 | 39 | 9963.893 | 9944.075 | 9966.440 | 0.530 |
| `mixed` | 2 | 3.58s | 24 | 45 | 9959.846 | 9925.957 | 9960.447 | 0.493 |

Interpretation:

- `structured` had the strongest average mean score and the fastest
  high-scoring runs in this tiny comparison.
- `sparse` found the best single candidate and was also fast.
- `uniform` was slowest and lowest-scoring here.
- `mixed` remained viable but diluted the strongest strategies; default mixed
  weights now lean toward `sparse` and `structured` while preserving all
  strategies for diversity.
- These are small proxy-scoring runs only; do not overfit without larger runs
  and later exact verification.

### 2026-07-04 Target-r CPU Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_target_r_bench`.
- Summary files:
  - `/tmp/igp24_target_r_bench/summary.json`
  - `/tmp/igp24_target_r_bench/summary.jsonl`
- Configuration:
  - Strategies: `sparse`, `structured`, `mixed`.
  - Targets: untargeted and `target_r=2`.
  - Seeds: `201`, `202`.
  - `coeff_bound=4`, `gensize=12`, `max_local_search_steps=3`,
    `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- All 12 runs returned code 0.
- All summary records included target-r fields and complete
  score/generation/local-search metadata.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sparse` | untargeted | 2 | 3.38s | 24 | 41 | NA | NA | 9958.046 | NA | 9930.899 | 9959.898 | 0.455 |
| `sparse` | `r=2` | 2 | 2.69s | 24 | 41 | 36 | 0.868 | 10207.559 | 10207.559 | 10158.324 | 10208.925 | 0.439 |
| `structured` | untargeted | 2 | 2.55s | 24 | 45 | NA | NA | 9964.574 | NA | 9941.921 | 9965.166 | 0.493 |
| `structured` | `r=2` | 2 | 2.65s | 24 | 44 | 25 | 0.564 | 10208.513 | 10208.513 | 10119.278 | 10215.166 | 0.515 |
| `mixed` | untargeted | 2 | 3.48s | 24 | 42 | NA | NA | 9952.847 | NA | 9931.606 | 9954.384 | 0.493 |
| `mixed` | `r=2` | 2 | 3.43s | 24 | 41 | 26 | 0.627 | 10202.847 | 10202.847 | 10119.258 | 10204.384 | 0.530 |

Interpretation:

- `target_r=2` produced high match rates for all three compared strategies in
  this tiny run.
- `sparse` had the strongest `r=2` match rate at 0.868 and the best sparse
  target-r average score.
- `structured` retained the strongest untargeted average mean score and found
  the best single target-r score, but its `r=2` match rate was lower than
  `sparse`.
- `mixed` remained useful but did not beat the best specialized strategy under
  this short run.
- No new generation default change is warranted from this small target-r run
  alone; use larger target-r benchmarks before tuning again.

### 2026-07-04 Larger Target-r CPU Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_target_r_bench_larger_20260704`.
- Summary files:
  - `/tmp/igp24_target_r_bench_larger_20260704/summary.json`
  - `/tmp/igp24_target_r_bench_larger_20260704/summary.jsonl`
  - `/tmp/igp24_target_r_bench_larger_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: `sparse`, `structured`, `mixed`.
  - Targets: untargeted, `target_r=0`, `target_r=2`, and `target_r=4`.
  - Seeds: `301`, `302`, `303`, `304`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 193.26 seconds.
- All 48 runs returned code 0.
- Artifact audit:
  - Summary rows: 48.
  - Valid candidates: 864.
  - Ledger records: 1,561.
  - All summary records included complete score/generation/local-search
    metadata.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `mixed` | `r=0` | 4 | 4.95s | 72 | 135 | 41 | 0.303 | 10210.117 | 10210.117 | 10061.147 | 10222.117 | 0.424 |
| `mixed` | `r=2` | 4 | 4.97s | 72 | 135 | 92 | 0.680 | 10208.197 | 10208.197 | 10127.371 | 10213.260 | 0.417 |
| `mixed` | `r=4` | 4 | 4.88s | 72 | 135 | 28 | 0.209 | 10201.770 | 10201.770 | 10042.195 | 10205.289 | 0.431 |
| `mixed` | untargeted | 4 | 4.96s | 72 | 135 | NA | NA | 9963.787 | NA | 9931.598 | 9972.117 | 0.417 |
| `sparse` | `r=0` | 4 | 3.63s | 72 | 135 | 33 | 0.246 | 10196.939 | 10196.939 | 10053.043 | 10204.853 | 0.417 |
| `sparse` | `r=2` | 4 | 3.70s | 72 | 134 | 100 | 0.745 | 10202.643 | 10202.643 | 10139.115 | 10208.544 | 0.430 |
| `sparse` | `r=4` | 4 | 3.78s | 72 | 137 | 26 | 0.191 | 10192.821 | 10192.821 | 10041.827 | 10207.005 | 0.426 |
| `sparse` | untargeted | 4 | 4.03s | 72 | 137 | NA | NA | 9955.183 | NA | 9932.331 | 9958.544 | 0.419 |
| `structured` | `r=0` | 4 | 3.26s | 72 | 120 | 60 | 0.501 | 10215.071 | 10215.071 | 10108.438 | 10216.978 | 0.364 |
| `structured` | `r=2` | 4 | 3.16s | 72 | 119 | 75 | 0.629 | 10213.416 | 10213.416 | 10128.951 | 10216.622 | 0.413 |
| `structured` | `r=4` | 4 | 3.25s | 72 | 119 | 4 | 0.034 | 10126.258 | 10204.226 | 10017.312 | 10209.825 | 0.424 |
| `structured` | untargeted | 4 | 3.28s | 72 | 120 | NA | NA | 9965.160 | NA | 9942.122 | 9966.978 | 0.389 |

Interpretation:

- `structured` looks best for `target_r=0` in this run: strongest average
  best score, strongest average mean score, and the highest `r=0` match rate.
- `sparse` still looks best for reliably hitting `target_r=2`: highest match
  rate at 0.745 and the strongest `r=2` average mean score.
- `structured` found the strongest `r=2` peak and average best scores, so a
  larger `r=2` run should probably compare `sparse` reliability against
  `structured` peak quality rather than picking only one.
- `target_r=4` remains weak for the current families. `mixed` and `sparse`
  found some matching records, but match rates stayed low; `structured` nearly
  missed this target entirely.
- Untargeted results still favor `structured` on average score, while `mixed`
  found the best single untargeted candidate in this batch.
- No global generation default change is justified from this proxy-only run.
  A practical next tuning step would be target-specific run presets, especially
  `structured` for `r=0`, `sparse` plus `structured` for `r=2`, and new
  `r=4`-friendly families before retuning `mixed`.

### 2026-07-04 Four-real Seed Target-r Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_four_real_seed_bench_20260704`.
- Summary files:
  - `/tmp/igp24_four_real_seed_bench_20260704/summary.json`
  - `/tmp/igp24_four_real_seed_bench_20260704/summary.jsonl`
  - `/tmp/igp24_four_real_seed_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: `sparse`, `mixed`, `four_real_seed`.
  - Target: `target_r=4`.
  - Seeds: `401`, `402`, `403`, `404`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 52.10 seconds.
- All 12 runs returned code 0.
- Artifact audit:
  - Summary rows: 12.
  - Valid candidates: 216.
  - Ledger records: 380.
  - Target-r matching records: 144.
  - All summary records included complete score/generation/local-search
    metadata.
  - `four_real_seed` ledger records included `target_r_heuristic=4`,
    `seed_template`, and perturbation metadata.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 4 | 4.18s | 72 | 123 | 97 | 0.792 | 10193.136 | 10193.136 | 10145.343 | 10195.370 | 0.346 |
| `mixed` | `r=4` | 4 | 5.04s | 72 | 130 | 26 | 0.200 | 10191.476 | 10191.476 | 10043.085 | 10197.883 | 0.438 |
| `sparse` | `r=4` | 4 | 3.67s | 72 | 127 | 21 | 0.164 | 10194.103 | 10194.103 | 10037.574 | 10207.604 | 0.423 |

Interpretation:

- `four_real_seed` materially improved `target_r=4` match rate in this short
  proxy-scored run: 0.792 average match rate versus 0.200 for `mixed` and
  0.164 for `sparse`.
- `four_real_seed` also had the strongest average mean score, which is expected
  because target-r bonus dominates once many generated candidates match
  `r=4`.
- `sparse` still found the best single candidate score in this batch, so the
  new strategy should be treated as a high-yield target-r generator rather than
  a universal quality winner.
- Local-search acceptance was lower for `four_real_seed`; this may indicate the
  current mutation moves often disturb the `r=4` shape.
- No global `mixed` default was changed. A later target-specific preset could
  include `four_real_seed` for `target_r=4`, but it needs a larger run and
  eventually exact external verification before promotion.

### 2026-07-04 R4 Preset Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_preset_bench_20260704`.
- Summary files:
  - `/tmp/igp24_r4_preset_bench_20260704/summary.json`
  - `/tmp/igp24_r4_preset_bench_20260704/summary.jsonl`
  - `/tmp/igp24_r4_preset_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: baseline `mixed`, explicit `four_real_seed`, and
    `preset_r4`.
  - Preset resolution: `preset_r4` runs as `--igp24_generation_strategy mixed`
    and `--igp24_generation_preset r4`, resolving to
    `four_real_seed:0.8,sparse:0.2`.
  - Target: `target_r=4`.
  - Seeds: `501`, `502`, `503`, `504`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 53.88 seconds.
- All 12 runs returned code 0.
- Artifact audit:
  - Summary rows: 12.
  - Valid candidates: 215.
  - Ledger records: 379.
  - Target-r matching records: 180.
  - All summary records included complete score/generation/local-search
    metadata.
  - `preset_r4` ledger records included preset name, target-r intent, resolved
    strategy, and resolved mixed weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 4 | 4.27s | 71 | 123 | 89 | 0.728 | 10193.071 | 10193.071 | 10132.778 | 10195.370 | 0.364 |
| `mixed` | `r=4` | 4 | 5.05s | 72 | 131 | 28 | 0.213 | 10195.711 | 10195.711 | 10047.644 | 10201.811 | 0.442 |
| `preset_r4` | `r=4` | 4 | 4.00s | 72 | 125 | 63 | 0.503 | 10198.249 | 10198.249 | 10096.563 | 10203.117 | 0.406 |

Interpretation:

- `preset_r4` improved over baseline `mixed` on `r=4` match rate and average
  mean score, while preserving some sparse diversity.
- Explicit `four_real_seed` still had the strongest `r=4` match rate in this
  bounded run: 0.728 versus 0.503 for `preset_r4`.
- `preset_r4` found the best single score and strongest average best score in
  this batch, so the sparse-diversity blend may help peak quality even though
  it dilutes target-r yield.
- The preset did not beat explicit `four_real_seed` on target-r match rate; do
  not promote it as strictly better. Treat it as a named convenience preset
  with a yield/quality tradeoff that needs larger validation.
- Default generation remains unchanged because presets are opt-in.

### 2026-07-04 R4 Mix Variant Validation

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_mix_variant_bench_20260704`.
- Summary files:
  - `/tmp/igp24_r4_mix_variant_bench_20260704/summary.json`
  - `/tmp/igp24_r4_mix_variant_bench_20260704/summary.jsonl`
  - `/tmp/igp24_r4_mix_variant_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: baseline `mixed`, explicit `four_real_seed`, current
    `preset_r4`, and benchmark-only mix labels `mix_r4_yield`,
    `mix_r4_balanced`, and `mix_r4_diverse`.
  - Mix labels:
    - `mix_r4_yield`: `four_real_seed:1.0`.
    - `mix_r4_balanced`: `four_real_seed:0.8,sparse:0.2`.
    - `mix_r4_diverse`: `four_real_seed:0.6,sparse:0.4`.
  - Target: `target_r=4`.
  - Seeds: `601`, `602`, `603`, `604`, `605`, `606`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 157.13 seconds.
- All 36 runs returned code 0.
- Artifact audit:
  - Summary rows: 36.
  - Valid candidates: 646.
  - Ledger records: 1,089.
  - Target-r matching records: 555.
  - All summary records included complete score/generation/local-search
    metadata.
  - Mix-variant ledger records included the intended resolved mixed weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 6 | 4.29s | 107 | 174 | 133 | 0.765 | 10193.551 | 10193.551 | 10140.093 | 10195.370 | 0.347 |
| `mix_r4_balanced` | `r=4` | 6 | 4.12s | 108 | 182 | 101 | 0.555 | 10195.700 | 10195.700 | 10106.215 | 10198.632 | 0.372 |
| `mix_r4_diverse` | `r=4` | 6 | 3.88s | 108 | 185 | 71 | 0.393 | 10195.487 | 10195.487 | 10076.236 | 10201.230 | 0.404 |
| `mix_r4_yield` | `r=4` | 6 | 4.20s | 107 | 173 | 112 | 0.652 | 10192.954 | 10192.954 | 10120.969 | 10198.193 | 0.349 |
| `mixed` | `r=4` | 6 | 5.32s | 108 | 193 | 37 | 0.192 | 10194.609 | 10194.609 | 10044.129 | 10204.040 | 0.406 |
| `preset_r4` | `r=4` | 6 | 4.06s | 108 | 182 | 101 | 0.555 | 10195.700 | 10195.700 | 10106.215 | 10198.632 | 0.372 |

Interpretation:

- Explicit `four_real_seed` remains the best high-yield `target_r=4` option:
  it had the highest average match rate at 0.765 and the highest average mean
  score.
- Current `preset_r4` exactly matches the benchmark-only balanced label,
  `mix_r4_balanced`, as expected. It improved over baseline `mixed` on match
  rate, average best score, and average mean score.
- The diversity-heavy `mix_r4_diverse` found the best single proxy score in
  this batch, but its match rate fell to 0.393. Extra sparse diversity appears
  to help peak exploration at the cost of target-r yield.
- The pure `mix_r4_yield` label used mixed dispatch with 100%
  `four_real_seed`; because it consumed random choices differently than the
  explicit strategy, it was not identical to explicit `four_real_seed` and had
  a lower 0.652 match rate in this run.
- Do not change `preset_r4` from `four_real_seed:0.8,sparse:0.2` yet. It is a
  reasonable balanced preset, while explicit `four_real_seed` should remain
  the documented recommendation when `r=4` yield is the only priority.
- No default generation change is justified; this is still proxy-only and has
  no exact `24Tt` verification.

### 2026-07-04 Quartic-lift Target-r Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_quartic_lift_bench_20260704`.
- Summary files:
  - `/tmp/igp24_quartic_lift_bench_20260704/summary.json`
  - `/tmp/igp24_quartic_lift_bench_20260704/summary.jsonl`
  - `/tmp/igp24_quartic_lift_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: baseline `mixed`, explicit `four_real_seed`, current
    `preset_r4`, and new `quartic_lift`.
  - Target: `target_r=4`.
  - Seeds: `701`, `702`, `703`, `704`, `705`, `706`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 104.35 seconds.
- All 24 runs returned code 0.
- Artifact audit:
  - Summary rows: 24.
  - Valid candidates: 430.
  - Ledger records: 708.
  - Target-r matching records: 391.
  - All summary records included complete score/generation/local-search
    metadata.
  - `quartic_lift` ledger records included the seed template, core support,
    quartic coefficients, and perturbation coefficients.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 6 | 4.18s | 107 | 166 | 126 | 0.757 | 10196.049 | 10196.049 | 10137.886 | 10203.007 | 0.381 |
| `mixed` | `r=4` | 6 | 5.22s | 108 | 196 | 39 | 0.197 | 10191.736 | 10191.736 | 10041.856 | 10194.638 | 0.424 |
| `preset_r4` | `r=4` | 6 | 4.06s | 107 | 180 | 109 | 0.608 | 10195.473 | 10195.473 | 10112.317 | 10201.396 | 0.390 |
| `quartic_lift` | `r=4` | 6 | 3.78s | 108 | 166 | 117 | 0.705 | 10206.896 | 10206.896 | 10139.839 | 10210.196 | 0.352 |

Interpretation:

- `quartic_lift` is a promising quality-oriented r4 family. It had the
  strongest average best score, strongest average matching score, strongest
  average mean score, and best single proxy score in this batch.
- Explicit `four_real_seed` still had the strongest r4 yield: 0.757 average
  match rate versus 0.705 for `quartic_lift` and 0.608 for `preset_r4`.
- `quartic_lift` beat the current balanced `preset_r4` on match rate and proxy
  score in this run, but one bounded proxy-only benchmark is not enough to
  retune the preset.
- Local-search acceptance was lowest for `quartic_lift`; future work should
  inspect whether generic mutations disrupt the quartic-lift shape.
- Keep default mixed weights and `preset_r4` unchanged. The next useful step is
  a larger r4 comparison that includes both `four_real_seed` and
  `quartic_lift`, or a benchmark-only mixed variant combining them.

### 2026-07-04 R4 Dual-family Mix Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_dual_mix_bench_20260704`.
- Summary files:
  - `/tmp/igp24_r4_dual_mix_bench_20260704/summary.json`
  - `/tmp/igp24_r4_dual_mix_bench_20260704/summary.jsonl`
  - `/tmp/igp24_r4_dual_mix_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: explicit `four_real_seed`, explicit `quartic_lift`, current
    `preset_r4`, and benchmark-only dual labels `mix_r4_dual_yield`,
    `mix_r4_dual_quality`, and `mix_r4_dual_balanced`.
  - Mix labels:
    - `mix_r4_dual_yield`: `four_real_seed:0.75,quartic_lift:0.25`.
    - `mix_r4_dual_quality`: `four_real_seed:0.25,quartic_lift:0.75`.
    - `mix_r4_dual_balanced`:
      `four_real_seed:0.45,quartic_lift:0.45,sparse:0.10`.
  - Target: `target_r=4`.
  - Seeds: `801`, `802`, `803`, `804`, `805`, `806`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 150.98 seconds.
- All 36 runs returned code 0.
- Artifact audit:
  - Summary rows: 36.
  - Valid candidates: 640.
  - Ledger records: 1,046.
  - Target-r matching records: 718.
  - All summary records included complete score/generation/local-search
    metadata.
  - All 537 dual-label ledger records checked had the expected mixed weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 6 | 4.41s | 106 | 171 | 121 | 0.709 | 10192.989 | 10192.989 | 10129.971 | 10195.878 | 0.358 |
| `mix_r4_dual_balanced` | `r=4` | 6 | 4.07s | 108 | 186 | 120 | 0.649 | 10206.061 | 10206.061 | 10123.920 | 10212.713 | 0.355 |
| `mix_r4_dual_quality` | `r=4` | 6 | 4.04s | 108 | 180 | 139 | 0.774 | 10201.181 | 10201.181 | 10147.115 | 10207.040 | 0.359 |
| `mix_r4_dual_yield` | `r=4` | 6 | 4.30s | 106 | 171 | 126 | 0.734 | 10196.517 | 10196.517 | 10136.035 | 10205.056 | 0.387 |
| `preset_r4` | `r=4` | 6 | 4.38s | 108 | 190 | 115 | 0.604 | 10195.842 | 10195.842 | 10112.710 | 10205.003 | 0.376 |
| `quartic_lift` | `r=4` | 6 | 3.95s | 104 | 148 | 97 | 0.657 | 10201.844 | 10201.844 | 10130.628 | 10207.040 | 0.362 |

Interpretation:

- `mix_r4_dual_quality` was the best overall tradeoff in this bounded run:
  highest average match rate at 0.774, strongest average mean score, and a
  strong average best score.
- `mix_r4_dual_yield` also improved over explicit `four_real_seed` on match
  rate and score metrics, though less dramatically than the quality-leaning
  mix.
- `mix_r4_dual_balanced` found the best single proxy score at 10212.713, but
  its match rate was below the other two dual mixes.
- Current `preset_r4` trailed all three dual labels on match rate and average
  best score in this run.
- Despite that, do not change `preset_r4` yet. This was a bounded proxy-only
  benchmark with one seed block. The evidence justifies a larger confirmation
  run, likely centered on `mix_r4_dual_quality`, before retuning any preset.

### 2026-07-04 R4 Dual-quality Confirmation

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_dual_quality_confirm_20260704`.
- Summary files:
  - `/tmp/igp24_r4_dual_quality_confirm_20260704/summary.json`
  - `/tmp/igp24_r4_dual_quality_confirm_20260704/summary.jsonl`
  - `/tmp/igp24_r4_dual_quality_confirm_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: current `preset_r4`, explicit `four_real_seed`, explicit
    `quartic_lift`, `mix_r4_dual_quality`, `mix_r4_dual_yield`, and
    `mix_r4_dual_balanced`.
  - Target: `target_r=4`.
  - Seeds: `901`, `902`, `903`, `904`, `905`, `906`, `907`, `908`, `909`,
    `910`, `911`, `912`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 289.85 seconds.
- All 72 runs returned code 0.
- Artifact audit:
  - Summary rows: 72.
  - Valid candidates: 1,282.
  - Ledger records: 2,049.
  - Target-r matching records: 1,317.
  - All summary records included complete score/generation/local-search
    metadata.
  - All 1,027 dual-label ledger records checked had the expected mixed
    weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 12 | 4.19s | 216 | 352 | 241 | 0.688 | 10195.219 | 10195.219 | 10126.379 | 10201.043 | 0.361 |
| `mix_r4_dual_balanced` | `r=4` | 12 | 4.03s | 215 | 350 | 212 | 0.609 | 10198.942 | 10198.942 | 10117.771 | 10207.509 | 0.407 |
| `mix_r4_dual_quality` | `r=4` | 12 | 3.95s | 214 | 342 | 218 | 0.639 | 10203.367 | 10203.367 | 10125.458 | 10207.509 | 0.377 |
| `mix_r4_dual_yield` | `r=4` | 12 | 4.09s | 214 | 335 | 229 | 0.683 | 10199.688 | 10199.688 | 10128.913 | 10206.711 | 0.385 |
| `preset_r4` | `r=4` | 12 | 4.19s | 213 | 348 | 206 | 0.590 | 10193.351 | 10193.351 | 10109.302 | 10202.793 | 0.384 |
| `quartic_lift` | `r=4` | 12 | 3.71s | 210 | 322 | 211 | 0.650 | 10204.553 | 10204.553 | 10129.814 | 10214.148 | 0.366 |

Interpretation:

- `mix_r4_dual_quality` again beat current `preset_r4` on average match rate
  and score metrics, but it was not the strongest confirmed option overall.
- Explicit `quartic_lift` beat `mix_r4_dual_quality` on match rate, average
  best score, average mean score, and best single proxy score in this seed
  block.
- `mix_r4_dual_yield` nearly matched explicit `four_real_seed` on match rate
  and beat `mix_r4_dual_quality` on average mean score.
- This is mixed evidence for retuning specifically to
  `four_real_seed:0.25,quartic_lift:0.75`. The larger run confirms that the
  current `preset_r4` is probably stale, but it does not cleanly confirm the
  dual-quality mix as the new preset.
- Decision: keep `preset_r4` unchanged for now. The next retuning step should
  directly compare `quartic_lift`, `mix_r4_dual_yield`, and current `preset_r4`
  on a second 12-seed block or add a quartic-heavy preset candidate before
  changing the user-facing preset.

### 2026-07-04 Second R4 Preset Confirmation

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_second_confirm_20260704`.
- Summary files:
  - `/tmp/igp24_r4_second_confirm_20260704/summary.json`
  - `/tmp/igp24_r4_second_confirm_20260704/summary.jsonl`
  - `/tmp/igp24_r4_second_confirm_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: current `preset_r4`, explicit `quartic_lift`,
    `mix_r4_dual_yield`, `mix_r4_dual_quality`, explicit
    `four_real_seed`, and `mix_r4_dual_balanced`.
  - Target: `target_r=4`.
  - Fresh disjoint seeds: `1001`, `1002`, `1003`, `1004`, `1005`,
    `1006`, `1007`, `1008`, `1009`, `1010`, `1011`, `1012`, `1013`,
    `1014`, `1015`, `1016`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 397.34 seconds.
- All 96 runs returned code 0.
- Artifact audit:
  - Summary rows: 96.
  - Valid candidates: 1,715.
  - Ledger records: 2,821.
  - Target-r matching records: 1,887.
  - All summary records included complete score/generation/local-search
    metadata.
  - Aggregate rows included match rate, average best, average mean, best
    score, and local-search acceptance fields.
  - All 1,403 dual-label ledger records checked had the expected mixed
    weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 16 | 4.29s | 281 | 479 | 341 | 0.712 | 10196.345 | 10196.345 | 10129.904 | 10205.378 | 0.375 |
| `mix_r4_dual_balanced` | `r=4` | 16 | 4.09s | 288 | 470 | 311 | 0.665 | 10203.000 | 10203.000 | 10126.958 | 10206.711 | 0.365 |
| `mix_r4_dual_quality` | `r=4` | 16 | 3.96s | 285 | 457 | 321 | 0.703 | 10205.721 | 10205.721 | 10136.184 | 10213.786 | 0.363 |
| `mix_r4_dual_yield` | `r=4` | 16 | 4.12s | 287 | 476 | 334 | 0.702 | 10200.852 | 10200.852 | 10130.398 | 10212.926 | 0.356 |
| `preset_r4` | `r=4` | 16 | 4.44s | 287 | 494 | 288 | 0.582 | 10193.953 | 10193.953 | 10107.642 | 10203.816 | 0.372 |
| `quartic_lift` | `r=4` | 16 | 3.94s | 287 | 445 | 292 | 0.657 | 10204.829 | 10204.829 | 10131.884 | 10213.786 | 0.352 |

Combined with the prior 12-seed confirmation:

| Strategy | Runs | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Mean | Best | Local Acceptance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | 28 | 497 | 831 | 582 | 0.702 | 10195.863 | 10128.393 | 10205.378 | 0.369 |
| `mix_r4_dual_balanced` | 28 | 503 | 820 | 523 | 0.641 | 10201.261 | 10123.021 | 10207.509 | 0.383 |
| `mix_r4_dual_quality` | 28 | 499 | 799 | 539 | 0.676 | 10204.712 | 10131.587 | 10213.786 | 0.369 |
| `mix_r4_dual_yield` | 28 | 501 | 811 | 563 | 0.694 | 10200.353 | 10129.761 | 10212.926 | 0.368 |
| `preset_r4` | 28 | 500 | 842 | 494 | 0.585 | 10193.695 | 10108.354 | 10203.816 | 0.377 |
| `quartic_lift` | 28 | 497 | 767 | 503 | 0.654 | 10204.711 | 10130.997 | 10214.148 | 0.358 |

Interpretation:

- Current `preset_r4` again trailed the stronger r4 families and mixes on
  both match rate and score metrics. It is useful as historical context but no
  longer looks competitive in these proxy runs.
- The fresh 16-seed block favored `mix_r4_dual_quality` on average best score,
  average mean score, and best single score, while `four_real_seed` retained a
  slightly higher match rate.
- `mix_r4_dual_yield` did not clearly win the yield/quality tradeoff: its
  match rate was close to `mix_r4_dual_quality`, but its average best and
  average mean scores were lower.
- `quartic_lift` did not clearly beat the mix labels overall. It had strong
  quality metrics and ties the fresh-block best single proxy score, but its
  match rate was lower than both dual-yield and dual-quality.
- Across both confirmation blocks, evidence still splits by objective:
  `four_real_seed` for match rate, `mix_r4_dual_quality` for average proxy
  quality, and `quartic_lift` for the best single proxy score.
- Decision: keep `preset_r4` unchanged again. The current preset is likely
  stale, but neither requested retune target is clearly dominant enough to
  change the user-facing preset on proxy-only evidence. A better next step is
  to add safe batch export/shortlist tooling for top r4 proxy candidates so the
  strongest families can feed later offline exact verification.

### 2026-07-04 R4 Shortlist Export Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_shortlist_20260704`.
- Inputs:
  - `/tmp/igp24_r4_second_confirm_20260704`
  - `/tmp/igp24_r4_dual_quality_confirm_20260704`
- Filters: `target_r=4`, top 25 by descending proxy score, deduplicated by
  canonical hash.
- Output files:
  - `/tmp/igp24_r4_shortlist_20260704/shortlist.jsonl`
  - `/tmp/igp24_r4_shortlist_20260704/coefficients.json`
  - `/tmp/igp24_r4_shortlist_20260704/coefficients.txt`
  - `/tmp/igp24_r4_shortlist_20260704/manifest.json`
- Loaded source records: 4,870.
- Selected records: 25.
- Unique canonical hashes: 25.
- Top score: 10214.147570701043.
- Last selected score: 10205.676526314839.
- Strategy counts:
  - `quartic_lift`: 23.
  - `four_real_seed`: 2.
- Audit:
  - All selected rows have `real_root_count=4`.
  - All exported coefficient vectors have length 25 and end in the fixed
    leading coefficient 1.
  - All selected rows include `source_ledger_path`.
  - Scores are sorted descending.
  - Manifest safety flags record `proxy_only=true`,
    `verifier_executed=false`, `submission_executed=false`, and
    `exact_group_claims=false`.
- Caveat: this is still proxy-scored export data only. It prepares candidates
  for later human-reviewed offline exact verification and does not certify any
  exact group label.

### 2026-07-04 R4 Review Batch Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_review_batch_20260704`.
- Input shortlist: `/tmp/igp24_r4_shortlist_20260704`.
- Selection criteria: top proxy score, batch size 8, at least 2 strategies
  where available, and a per-strategy cap of 6.
- Output files:
  - `/tmp/igp24_r4_review_batch_20260704/review_report.md`
  - `/tmp/igp24_r4_review_batch_20260704/verification_batch.jsonl`
  - `/tmp/igp24_r4_review_batch_20260704/verification_coefficients.txt`
  - `/tmp/igp24_r4_review_batch_20260704/manifest.json`
- Loaded shortlist records: 25.
- Selected records: 8.
- Unique canonical hashes: 8.
- Top score: 10214.147570701043.
- Strategy counts:
  - `quartic_lift`: 6.
  - `four_real_seed`: 2.
- Audit:
  - All exported coefficient vectors have length 25 and end in the fixed
    leading coefficient 1.
  - Every row records both `source_ledger_path` and `source_shortlist_path`.
  - Every review record keeps `verified_group_label=null` and an explicit
    proxy-only caveat.
  - Manifest safety flags record `proxy_only=true`,
    `review_export_only=true`, `verifier_executed=false`,
    `submission_executed=false`, `network_calls=false`, and
    `exact_group_claims=false`.
- Caveat: this is a human-review batch for later offline exact-verifier
  experiments. It did not run PARI, MAGMA, SAIR, network calls, exact group
  verification, or any submission path.

### 2026-07-04 R4 Offline Verification Prep Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_offline_verify_20260704`.
- Input review batch: `/tmp/igp24_r4_review_batch_20260704`.
- Mode: default preparation-only dry run; no `--run_pari` or `--run_magma`
  flags were used.
- Output files:
  - `/tmp/igp24_r4_offline_verify_20260704/offline_verification_manifest.json`
  - `/tmp/igp24_r4_offline_verify_20260704/pari_input.gp`
  - `/tmp/igp24_r4_offline_verify_20260704/magma_input.m`
  - `/tmp/igp24_r4_offline_verify_20260704/verification_plan.md`
- Loaded review records: 8.
- Unique selected hashes: 8.
- Tool availability:
  - PARI/GP `gp`: unavailable on PATH.
  - MAGMA `magma`: unavailable on PATH.
- Execution:
  - PARI/GP requested: false; executed: false.
  - MAGMA requested: false; executed: false.
  - No raw verifier output files were created.
- Audit:
  - Manifest records coefficient shape as length 25 with fixed leading
    coefficient 1.
  - Generated PARI/GP and MAGMA scripts include the candidate hashes and
    commented exact Galois-group steps for deliberate manual use.
  - Manifest safety flags record `network_calls=false`,
    `sair_submission=false`, `auto_submission=false`,
    `pari_executed=false`, `magma_executed=false`,
    `exact_group_labels_parsed=false`, `exact_group_claims=false`, and
    `dry_run_preparation_only=true`.
- Caveat: this smoke only prepares local verifier inputs. It does not verify
  candidates, parse exact group labels, contact SAIR, make network calls, or
  submit anything.

### 2026-07-04 Fixed Sparse Template r2 Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_fixed_sparse_template_bench_20260704`.
- Configuration:
  - Strategies: `sparse`, `structured`, `fixed_sparse_template`.
  - Target: `target_r=2`.
  - Seeds: `1101`, `1102`, `1103`, `1104`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 50.42 seconds from `/usr/bin/time -p`.
- All 12 runs returned code 0.
- Artifact audit:
  - Summary rows: 12.
  - Valid candidates: 216.
  - Ledger records: 391.
  - Target-r matching records: 258.
  - All summary rows had complete score/generation/local-search metadata.
  - 130 `fixed_sparse_template` ledger rows included template name, support
    indices, coefficient bound, and extra nonzero indices introduced by local
    search where applicable.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_sparse_template` | `r=2` | 4 | 4.66s | 72 | 130 | 90 | 0.692 | 10192.027 | 10118.108 | 10193.846 | 0.420 |
| `sparse` | `r=2` | 4 | 4.40s | 72 | 133 | 88 | 0.658 | 10199.870 | 10124.774 | 10205.840 | 0.472 |
| `structured` | `r=2` | 4 | 3.54s | 72 | 128 | 80 | 0.626 | 10214.248 | 10128.146 | 10219.375 | 0.408 |

Interpretation:

- `fixed_sparse_template` had the highest average `r=2` match rate in this
  small block, 0.692 versus 0.658 for `sparse` and 0.626 for `structured`.
- The new family lagged the baselines on proxy quality: `structured` had the
  strongest average best, average mean, and best single proxy score; `sparse`
  was second on those score metrics.
- Treat `fixed_sparse_template` as a useful r2-yield/diversity probe, not as a
  default or preset candidate from this one bounded proxy benchmark.
- No generation default, default mixed weight, or `preset_r4` change is
  justified here. Exact verification remains unrun because local PARI/GP and
  MAGMA are unavailable.

## Blockers / Environment Notes

- The previous stage-0 run used a temporary dependency target at
  `/tmp/igp24_pydeps` because the base shell did not have `python`, `numpy`,
  `sympy`, `pytest`, or `torch` available directly.
- Current shell still lacks a `python` executable; use `python3` with
  `PYTHONPATH=/tmp/igp24_pydeps` for local checks unless a proper environment is
  activated.
- Benchmark helper initially parsed valid candidates from stdout only, but
  Axplorer logging writes the count to stderr. Fixed by parsing combined
  stdout/stderr.
- Initial benchmark attempts showed that fixed `--seed` did not control NumPy
  generation. Fixed by seeding NumPy in `IGP24Environment`.

## Future Stages

Keep these future-stage items visible while the live log changes. Break them
down further as they become active.

### Stage 2: Structured Families And Exact-Tool Prep

- [done] Add an opt-in fixed-support sparse template generation family.
  - [done] Add a `fixed_sparse_template` strategy distinct from random
    `sparse`, using a small hand-auditable set of support templates.
  - [done] Keep the strategy opt-in only; do not change default mixed
    weights, default generation behavior, or `preset_r4`.
  - [done] Record ledger metadata for template name, support indices,
    coefficient bound, and any target-r intent.
  - [done] Add focused tests for coefficient shape, template metadata,
    deterministic generation, CLI strategy validity, and unchanged defaults.
  - [done] Document the strategy in README/NOTES/TODO.
  - [done] Run a bounded CPU-only benchmark against `sparse` and
    `structured`, including at least `target_r=2`, and interpret proxy-only
    results without retuning defaults.
- [done] Add safe offline exact-verifier preparation workflow.
  - [done] Add a preparation-only CLI that reads review-batch directories,
    validates `verification_batch.jsonl`, `verification_coefficients.txt`, and
    `manifest.json`, and refuses malformed coefficient exports.
  - [done] Emit `offline_verification_manifest.json`, `pari_input.gp`,
    `magma_input.m`, and `verification_plan.md` for manual local verifier runs.
  - [done] Probe local PARI/GP and MAGMA availability without installing or
    downloading anything, and record unavailable-tool blockers.
  - [done] Gate any local verifier execution behind explicit opt-in flags,
    keep dry-run/preparation as the default, and never add SAIR/network or
    auto-submission behavior.
  - [done] Add fast fixture-based tests for batch loading, coefficient
    validation, script generation, manifest safety flags, and unavailable
    verifier handling.
  - [done] Document the workflow in README/NOTES/TODO.
  - [done] Smoke it against
    `/tmp/igp24_r4_review_batch_20260704`.
- [done] Add safe human-review tooling for exported shortlists.
  - [done] Add a review/export-only CLI that reads shortlist export
    directories and optionally follows `source_ledger_path` to richer ledger
    records.
  - [done] Support batch size, canonical-hash deduplication, score sorting,
    and source-strategy diversity constraints where possible.
  - [done] Emit `review_report.md`, `verification_batch.jsonl`,
    `verification_coefficients.txt`, and `manifest.json` with source
    shortlist, source ledgers, command, criteria, timestamp, and safety flags.
  - [done] Add fast fixture-based tests covering shortlist loading,
    source-ledger rehydration, diverse top-N selection, output files, and
    proxy-only safety flags.
  - [done] Document the review-batch command and safety boundary in
    README/NOTES/TODO.
  - [done] Run and audit an r4 review-batch smoke export from the existing
    `/tmp/igp24_r4_shortlist_20260704` shortlist.
- [done] Add safe batch export/shortlist helpers for verifier input
  files.
  - [done] Add an export-only CLI that reads benchmark directories and/or
    ledger JSONL files without running MAGMA/PARI/SAIR or network calls.
  - [done] Support target-r filtering, generation-strategy filtering,
    top-N limits, canonical-hash deduplication, and score sorting.
  - [done] Emit an audit manifest, JSONL shortlist, and coefficient export
    suitable for later human-reviewed offline verifier input.
  - [done] Add fast fixture-based tests for filtering, deduplication,
    sorting, manifest creation, and coefficient export shape.
  - [done] Document usage and the safety boundary in README/NOTES/TODO.
  - [done] Run and audit a small r4 shortlist smoke export from existing
    benchmark artifacts.
- [done] Run second direct r4 preset confirmation.
  - [done] Run a fresh disjoint-seed CPU-only `target_r=4` comparison
    across `preset_r4`, `quartic_lift`, `mix_r4_dual_yield`,
    `mix_r4_dual_quality`, `four_real_seed`, and
    `mix_r4_dual_balanced`.
  - [done] Audit return codes, expected summary row count, metadata
    completeness, aggregate fields, and dual-mix ledger metadata.
  - [done] Decide whether `preset_r4` should remain unchanged, retune
    toward `quartic_lift`, or retune to the dual-yield mix.
  - [done] If retuning, update focused tests plus README/NOTES/TODO; if
    not retuning, document the tradeoff and next task.
- [done] Confirm whether `preset_r4` should retune to
  `mix_r4_dual_quality`.
  - [done] Run a larger 12-seed CPU-only `target_r=4` confirmation across
    `preset_r4`, `four_real_seed`, `quartic_lift`, and dual r4 mix labels.
  - [done] Audit return codes, metadata completeness, expected row count,
    and mix metadata in ledgers.
  - [done] Decide whether `mix_r4_dual_quality` clearly beats current
    `preset_r4` on match rate and average score metrics.
  - [done] If evidence is strong, retune `preset_r4`; otherwise document why
    it remains unchanged.
- [done] Test benchmark-only r4 dual-family mixes.
  - [done] Add helper-only labels combining `four_real_seed`,
    `quartic_lift`, and optional sparse diversity.
  - [done] Add focused benchmark-helper tests for dual-mix label
    resolution.
  - [done] Run a bounded CPU-only `target_r=4` comparison against
    `four_real_seed`, `quartic_lift`, `preset_r4`, and the dual labels.
  - [done] Interpret whether any dual mix improves the current r4
    yield/quality tradeoff before changing any preset/default.
- [done] Add a `target_r=4` quartic-lift structured family.
  - [done] Probe bounded quartic-in-`x^6` templates with small perturbations.
  - [done] Implement a distinct `quartic_lift` generation strategy with
    ledger metadata.
  - [done] Add deterministic generation and metadata tests.
  - [done] Benchmark `quartic_lift` against `mixed`, `four_real_seed`, and
    `preset_r4`.
  - [done] Document whether it improves target-r yield, peak proxy score,
    or diversity before changing any preset/default.
- [in_progress] Add more structured polynomial families:
  - [pending] sparse families with fixed support templates,
  - [done] first compositional/tower-style construction:
    `quartic_lift`, a quartic-in-`x^6` family for `target_r=4`,
  - [pending] compositional and tower constructions with degrees multiplying to
    24,
  - [pending] resolvent-inspired families,
  - [pending] solvable or imprimitive group families.
- [pending] Add group metadata and target-family tags without claiming exact
  `24Tt` labels.
- [pending] Add better group-specific modular cycle-type filters.
- [pending] Build PARI and MAGMA wrappers for offline/batched exact checks,
  still outside the training loop.
- [pending] Add safe batch export helpers for verifier input files.

### Stage 3: Verification And Long Runs

- [pending] Consider an optional Rust/PyO3 or multiprocessing verifier bridge.
- [pending] Add batched exact verification workflows for candidates exported
  from the ledger.
- [pending] Add leaderboard-aware target selection after exact verification is
  available.
- [pending] Run longer generation/training jobs only after short benchmark
  comparisons justify them.
- [pending] Keep SAIR submission explicit and manual; never auto-submit.

### Stage 4: Competition Packaging And Reproducibility

- [pending] Curate a final set of externally verified candidates with exact
  group/signature metadata and verifier provenance.
- [pending] Produce reproducible run manifests for any candidates promoted to
  submission consideration:
  - [pending] source commit,
  - [pending] command line,
  - [pending] random seeds,
  - [pending] environment details,
  - [pending] ledger record hashes,
  - [pending] verifier outputs.
- [pending] Add leaderboard-aware reporting once exact verification exists:
  - [pending] best candidates by target,
  - [pending] discriminant comparisons,
  - [pending] duplicate/canonical-equivalence checks,
  - [pending] rejected-candidate audit trail.
- [pending] Build safe manual submission packaging for SAIR:
  - [pending] export-only by default,
  - [pending] explicit human review checklist,
  - [pending] no automatic submission path,
  - [pending] no API keys in logs or artifacts.
- [pending] Archive benchmark, training, and verification artifacts needed for
  post-competition reproducibility.

## Recommended Next Tasks

- [done] Implement configurable generation strategies and tests.
- [done] Add score component metadata to ledger records.
- [done] Add local-search stats metadata and tests.
- [done] Run and document a short CPU-only generation benchmark.
- [done] Run per-strategy comparisons with equal `gensize` and fixed seeds.
- [done] Run short per-strategy comparisons including target real-root counts.
- [done] Run larger per-strategy target-r comparisons before further tuning
  defaults.
- [done] Add an experimental `target_r=4`-friendlier `four_real_seed`
  generation family.
- [done] Add target-specific benchmark presets or docs for promising
  strategy/target pairs.
- [done] Run a larger `target_r=4` validation with `four_real_seed`,
  `preset_r4`, and tuned target-specific mixes before promoting presets.
- [done] Run a longer focused `target_r=2` comparison between `sparse`,
  `structured`, and the new fixed-support sparse template family.
- [pending] Use fixed-support sparse templates as an opt-in diversity/yield
  probe only; do not promote to defaults or presets without larger proxy runs
  and later exact verifier evidence.
- [pending] Run a small GPU training smoke before treating model training as a
  main path; keep CPU proxy-search primary unless CUDA/PyTorch and tiny
  training both work cleanly.
- [done] Add one more `target_r=4` structured family before retuning the
  balanced `preset_r4` weights again.
- [done] Run a larger r4 comparison or benchmark-only mix that combines
  `four_real_seed` yield with `quartic_lift` peak proxy quality before changing
  `preset_r4`.
- [done] Run a larger confirmation benchmark centered on
  `mix_r4_dual_quality` before retuning `preset_r4`.
- [done] Run a second confirmation that directly compares `quartic_lift`,
  `mix_r4_dual_yield`, and current `preset_r4` before changing the r4 preset.
- [done] Add safe batch export/shortlist helpers for top proxy candidates
  from the strongest r4 strategies so later offline exact verification can
  inspect them without adding any automatic SAIR submission path.
- [done] Manually review the exported r4 shortlist and choose a small batch
  for offline exact-verifier experiments, keeping any SAIR submission explicit
  and human-controlled.
- [done] Prepare manual offline exact-verifier inputs for
  `/tmp/igp24_r4_review_batch_20260704`, record local tool availability, and
  keep any SAIR submission explicit and human-controlled.
- [pending] Run manual offline exact-verifier experiments only after local
  PARI/MAGMA tooling is available, record verifier provenance and outputs, and
  keep any SAIR submission explicit and human-controlled.
