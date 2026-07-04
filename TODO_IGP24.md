# IGP24 Live TODO

This file is the working project log for the Axplorer-based IGP24 candidate
generator. Keep it current as implementation, tests, smoke runs, and benchmark
results change.

## Current Status

- Branch: `igp24-dev`
- Remote target: `zpconn/igp24-axplorer`
- Last pull: 2026-07-04, `git pull --ff-only` -> fast-forwarded README update
  from `f60e285` to `9b00f3d`.
- Active focus: move from stage-0 scaffold toward a practical stage-1 candidate
  generation workflow.

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
- [done] Add a reusable per-strategy benchmark helper.
  - [done] Add `scripts/igp24_benchmark.py` to run short CPU-only `train.py`
    jobs and summarize JSONL ledgers.
  - [done] Add fast tests for benchmark summary aggregation.
  - [done] Verify helper CLI with `--help`.
  - [done] Run the helper across all generation strategies.

## Tests And Checks

- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
  - Latest result: 17 passed in 0.64s on final target-r benchmark check.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
  - Latest result: passed with `scripts` included.
- [done] Run an import check proving `square`, `isosceles`, `sphere`, and
  `igp24` remain discoverable.
  - Command: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- [blocked] Run literal `python -m pytest`, or record the blocker.
  - Latest result: blocked because `python` is not on PATH in this shell.
- [done] If local dependency issues block the literal command, record the
  exact blocker and run the closest available equivalent.

## Command Log

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

- [pending] Add more structured polynomial families:
  - [pending] sparse families with fixed support templates,
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
- [pending] Run larger per-strategy target-r comparisons before further tuning
  defaults.
