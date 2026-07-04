# IGP24 Axplorer

Research scaffold for using Axplorer as a candidate generator for the
[SAIR IGP24 inverse Galois competition](https://competition.sair.foundation/competitions/igp24/overview).

This project generates, scores, locally improves, deduplicates, and exports
monic degree-24 integer polynomials:

```text
f(x) = x^24 + a23*x^23 + ... + a1*x + a0
```

Internally, candidates are represented by the 24 free coefficients:

```text
[a0, a1, ..., a23]
```

Exported candidates append the fixed leading coefficient:

```text
[a0, a1, ..., a23, 1]
```

## Status

This is a candidate generator and proxy scorer. It is not an exact Galois group
verifier.

Exact `24Tt` labels require later verification with external tooling such as
PARI, MAGMA, or SAIR infrastructure. The current modular factorization data is
only proxy evidence.

Current features:

- configurable coefficient generation strategies,
- exact SymPy prefilters for basic polynomial validity,
- proxy score component metadata,
- bounded deterministic local search with telemetry,
- JSONL candidate ledger with canonical hash deduplication,
- dry-run verifier stubs for future PARI, MAGMA, and SAIR integration.

## Setup

Create the environment from `environment.yml`:

```bash
micromamba env create -f environment.yml
micromamba activate env_axplorer
```

If your machine needs a custom PyTorch or CUDA setup, install that separately
for your hardware.

## Run A Small Smoke Job

```bash
python train.py \
  --env_name igp24 \
  --exp_name igp24_smoke \
  --coeff_bound 10 \
  --gensize 100 \
  --pop_size 20 \
  --data_generation_only true \
  --always_search true \
  --max_local_search_steps 20 \
  --igp24_generation_strategy mixed \
  --igp24_sparse_terms 4 \
  --igp24_low_height_bound 3 \
  --cpu true
```

Useful IGP24-specific generation flags:

```text
--igp24_generation_strategy mixed
--igp24_generation_preset none
--igp24_sparse_terms 4
--igp24_low_height_bound 3
--igp24_mixed_strategy_weights uniform:0.10,low_height:0.20,sparse:0.25,lower_degree:0.20,structured:0.25,four_real_seed:0.00,quartic_lift:0.00
```

`--igp24_generation_strategy` can be `mixed`, `uniform`, `low_height`,
`sparse`, `lower_degree`, `structured`, `four_real_seed`, or
`quartic_lift`.

The strategies are:

- `uniform`: dense coefficients sampled from the full search box.
- `low_height`: dense coefficients sampled from a smaller inner box.
- `sparse`: a configurable number of nonzero free coefficients.
- `lower_degree`: coefficients biased toward low-degree terms.
- `structured`: simple sparse binomial/trinomial-like seeds.
- `four_real_seed`: an experimental `target_r=4`-oriented near-product seed
  with small odd perturbations.
- `quartic_lift`: an experimental `target_r=4`-oriented quartic-in-`x^6`
  seed with small off-support perturbations.
- `mixed`: a weighted mix of the above.

The default `mixed` weights keep `four_real_seed` and `quartic_lift` at zero
weight. Use them explicitly when running `target_r=4` experiments.

Target-specific presets are opt-in with `--igp24_generation_preset`. The
default `none` preserves the explicit strategy and weight settings. Available
presets are:

- `r0`: use `structured` generation.
- `r2`: use a sparse/structured mixed strategy.
- `r4`: use a `four_real_seed`/sparse mixed strategy.

Ledger records include the preset name, target-r intent, resolved strategy, and
resolved mixed weights.

Candidate records are written as JSONL by default:

```text
data/igp24/candidates.jsonl
```

Each ledger record includes exported coefficients, polynomial metadata, score
components, generation metadata, local-search metadata, and verification status.
Records remain proxy-scored unless an external verifier is used later.

## Compare Generation Strategies

Use the benchmark helper for short, reproducible CPU-only comparisons:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies uniform,low_height,sparse,lower_degree,structured,mixed \
  --seeds 101,102 \
  --target_rs none \
  --coeff_bound 4 \
  --gensize 12 \
  --pop_size 6 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 3 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_strategy_bench
```

The helper runs `train.py`, writes per-run ledgers under the output directory,
and produces `summary.json`, `summary.jsonl`, and `aggregate_summary.json`.
These include valid-candidate counts, ledger counts, scores, runtimes, strategy
mix, target-r match rates, and local-search acceptance statistics.

To compare target real-root counts, pass one or more targets with `--target_rs`.
Use `none` for untargeted runs:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies sparse,structured,mixed \
  --seeds 301,302,303,304 \
  --target_rs none,0,2,4 \
  --coeff_bound 4 \
  --gensize 18 \
  --pop_size 8 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 4 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_target_r_bench_larger
```

Target-r summaries include match counts, match rates, and best matching scores
when a target is supplied. The aggregate summary groups repeated seeds by
strategy and target.

For a focused `target_r=4` comparison, include the experimental strategy
or the `r4` preset explicitly:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies mixed,four_real_seed,preset_r4,quartic_lift \
  --seeds 501,502,503,504 \
  --target_rs 4 \
  --coeff_bound 4 \
  --gensize 18 \
  --pop_size 8 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 4 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_r4_preset_bench
```

The benchmark helper also accepts r4 mix labels for tuning experiments:

- `mix_r4_yield`: `four_real_seed:1.0`
- `mix_r4_balanced`: `four_real_seed:0.8,sparse:0.2`
- `mix_r4_diverse`: `four_real_seed:0.6,sparse:0.4`
- `mix_r4_dual_yield`: `four_real_seed:0.75,quartic_lift:0.25`
- `mix_r4_dual_quality`: `four_real_seed:0.25,quartic_lift:0.75`
- `mix_r4_dual_balanced`: `four_real_seed:0.45,quartic_lift:0.45,sparse:0.10`

These labels are benchmark-only conveniences. Use `preset_r4` for the actual
opt-in generation preset, `four_real_seed` directly when r4 yield is the main
priority, or the dual labels to compare `four_real_seed` yield with
`quartic_lift` peak proxy quality.

## Export Proxy Shortlists

Use the shortlist helper to collect top proxy-scored candidates from existing
benchmark directories or ledger JSONL files:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py \
  /tmp/igp24_r4_second_confirm_20260704 \
  /tmp/igp24_r4_dual_quality_confirm_20260704 \
  --target_r 4 \
  --limit 25 \
  --output_dir /tmp/igp24_r4_shortlist
```

The helper writes `shortlist.jsonl`, `coefficients.json`,
`coefficients.txt`, and `manifest.json`. It is export-only: it does not run
PARI, MAGMA, SAIR, network calls, exact group verification, or submission.
Treat every exported candidate as proxy-scored until a human-reviewed offline
exact verifier confirms it.

## Review A Shortlist

Use the review helper to turn a proxy shortlist into a small manual review
batch for later offline verifier experiments:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py \
  /tmp/igp24_r4_shortlist_20260704 \
  --batch_size 8 \
  --min_strategies 2 \
  --per_strategy_cap 6 \
  --output_dir /tmp/igp24_r4_review_batch
```

The helper writes `review_report.md`, `verification_batch.jsonl`,
`verification_coefficients.txt`, and `manifest.json`. It may follow recorded
`source_ledger_path` values to enrich records, but it still only reads and
writes local files. It does not run exact verifiers or submit anything.

## Prepare Offline Verification

Use the offline verification helper to validate a review batch and write manual
PARI/GP and MAGMA input files:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_r4_review_batch_20260704 \
  --output_dir /tmp/igp24_r4_offline_verify
```

By default this is preparation-only. It writes
`offline_verification_manifest.json`, `pari_input.gp`, `magma_input.m`, and
`verification_plan.md`, records whether `gp` or `magma` are available locally,
and does not run exact verification. Local verifier execution requires explicit
`--run_pari` or `--run_magma` flags. SAIR submission and network calls are out
of scope.

## Recent Smoke Result

The current smoke run used CPU-only mixed generation:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 train.py \
  --env_name igp24 \
  --exp_name igp24_stage1_mixed_smoke \
  --dump_path /tmp/igp24_stage1_smoke \
  --seed 123 \
  --coeff_bound 4 \
  --gensize 12 \
  --pop_size 6 \
  --ntest 2 \
  --gen_batch_size 2 \
  --data_generation_only true \
  --always_search true \
  --max_local_search_steps 3 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --process_pool false \
  --num_workers 1 \
  --cpu true \
  --igp24_generation_strategy mixed \
  --igp24_sparse_terms 4 \
  --igp24_low_height_bound 2 \
  --igp24_ledger_path /tmp/igp24_stage1_mixed_candidates.jsonl
```

Result: 12 valid generated examples, best score `9943.432289451468`, and
metadata present on all ledger records. See `TODO_IGP24.md` for the live command
log and benchmark notes.

## Run Tests

```bash
python -m pytest
```

The tests cover polynomial construction, export format, exact utility checks,
generation strategies, proxy scoring, local-search determinism and telemetry,
ledger deduplication, verifier stubs, and environment registration.

## Main Files

- `src/envs/igp24.py`: Axplorer environment and coefficient tokenizer.
- `src/igp24/polynomial.py`: exact polynomial utilities and proxy scoring.
- `src/igp24/ledger.py`: JSONL candidate ledger.
- `src/igp24/verifiers/`: PARI, MAGMA, and SAIR stubs.
- `NOTES_IGP24.md`: architecture notes and scoring/generation rationale.
- `TODO_IGP24.md`: live project log, task status, commands, and benchmark notes.

## License

This fork follows the upstream Axplorer license. See `LICENSE`.
