# IGP24 Axplorer

[Axplorer](https://github.com/AxiomMath/axplorer)-based research code for generating and triaging monic degree-24
integer polynomials for the
[SAIR IGP24 inverse Galois competition](https://competition.sair.foundation/competitions/igp24/overview). The underlying algorithm alternates between local search (Python) and transformer-based global pattern learning (custom-trained neural net).

This repository is a candidate generator, proxy scorer, and verification
handoff toolkit. It is not an automatic submission system.

## What This Searches

IGP24 candidates are monic degree-24 polynomials:

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

## Current State

The current verified result set includes a 25-row non-generic queue:

- 25/25 selected non-generic candidates were verified with Magma.
- All 25 are degree 24 and irreducible.
- Exact labels:
  - `24T24970`: 18 candidates
  - `24T24979`: 6 candidates
  - `24T24759`: 1 candidate
- None of these 25 were generic `24T25000`.

The raw Magma calculator XML outputs are preserved under
`data/igp24/online_magma_manual_output_*_20260705.xml`. See
[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) for the experiment summary and
artifact paths.

The verified-label feedback helper maps those exact labels back to local
structure-audit rows so future shortlist work can distinguish the
`24T24970`, `24T24979`, and `24T24759` families.

A fresh 2026-07-06 diversity queue has also been partially verified: 12/16
rows parsed as degree 24 and irreducible, adding exact labels `24T9683` and
`24T24648` alongside the previously seen families. Four rows are still pending
because the online calculator returned a temporarily-disabled response. See
[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) for details and caveats.

The bundled official baseline CSV (`data/igp24/lmfdb_baseline.csv`) lets the
manual planner compare verified `(24Tt, r)` pairs against the frozen LMFDB
baseline. The current five one-per-pair representatives are absent from that
baseline, but they still need exact Magma `r` and exact number-field
discriminant evidence before they should be treated as submission-grade.

## Capabilities

- Configurable coefficient generation strategies.
- Exact SymPy prefilters for basic polynomial validity.
- Proxy scoring with component metadata.
- Bounded deterministic local search with telemetry.
- JSONL ledgers with canonical-hash deduplication.
- CPU benchmark helpers for generation strategy comparisons.
- GPU training/sample-export probes with CPU scoring handoff.
- Shortlist, review, and offline verification handoff tools.
- PARI, Magma, official-baseline, and SAIR verifier/planning stubs that are
  explicit and opt-in.

## Safety Boundaries

The search pipeline keeps proxy evidence separate from exact labels.

- `train.py`, GPU sampling, CPU proxy scoring, local search, and shortlist
  helpers do not call Magma, PARI, SAIR, or online services.
- Local Magma execution requires explicit `--run_magma`.
- Online Magma calculator outputs in this repo are saved provenance from
  one-candidate verification requests, not an automated submission path.
- SAIR submission remains manual and out of scope for normal runs.

## Setup

Create the environment:

```bash
micromamba env create -f environment.yml
micromamba activate env_axplorer
```

If your machine needs a custom PyTorch or CUDA build, install that separately
for your hardware.

For local commands in this repo, use the repository root as the working
directory. Some historical runs used an extra local dependency path:

```bash
export PYTHONPATH=/tmp/igp24_pydeps
```

## Quick Smoke

Run a small CPU-only generation smoke:

```bash
python3 train.py \
  --env_name igp24 \
  --exp_name igp24_smoke \
  --dump_path /tmp/igp24_smoke \
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
  --igp24_ledger_path /tmp/igp24_smoke_candidates.jsonl
```

Candidate records are written as JSONL. Each record includes exported
coefficients, polynomial metadata, score components, generation metadata,
local-search metadata, and verification status.

## Common Workflows

Run tests:

```bash
python3 -m pytest -q
```

Compare generation strategies:

```bash
python3 scripts/igp24_benchmark.py \
  --strategies sparse,structured,mixed \
  --seeds 301,302 \
  --target_rs none,4 \
  --coeff_bound 4 \
  --gensize 18 \
  --pop_size 8 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 4 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_benchmark
```

Export a proxy shortlist:

```bash
python3 scripts/igp24_shortlist.py \
  /tmp/igp24_benchmark \
  --target_r 4 \
  --limit 25 \
  --output_dir /tmp/igp24_shortlist
```

Build a review batch:

```bash
python3 scripts/igp24_review_shortlist.py \
  /tmp/igp24_shortlist \
  --batch_size 8 \
  --min_strategies 2 \
  --per_strategy_cap 6 \
  --output_dir /tmp/igp24_review_batch
```

Prepare offline verification artifacts:

```bash
python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_review_batch \
  --output_dir /tmp/igp24_offline_verify \
  --max_records 3 \
  --timeout_seconds 5
```

The offline verifier helper is dry-run by default. It writes PARI/GP and Magma
input files, copied verification batches, reports, and result templates. It
does not execute Magma unless `--run_magma` is supplied.

Summarize verified exact-label feedback:

```bash
python3 scripts/igp24_verified_label_feedback.py \
  --structure_audit_jsonl /tmp/igp24_non_generic_structure_audit_20260705/structure_audit.jsonl \
  --magma_results_jsonl /tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual/online_magma_manual_results.jsonl \
  --diagnostic_jsonl /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl \
  --output_dir /tmp/igp24_verified_label_feedback_20260705
```

This helper is local/file-only: it reads saved artifacts and does not call
Magma, PARI, SAIR, training, GPU sampling, CPU search loops, or network APIs.

Build an exact-label-aware shortlist plan:

```bash
python3 scripts/igp24_exact_label_shortlist.py \
  --structure_audit_jsonl /tmp/igp24_non_generic_structure_audit_20260705/structure_audit.jsonl \
  --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl \
  --candidate_jsonl /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl \
  --output_dir /tmp/igp24_exact_label_shortlist_20260705 \
  --limit 12 \
  --min_per_label 0 \
  --label_quotas 24T24970:8,24T24979:2,24T24759:1
```

This uses saved feedback as family-planning evidence; it does not claim fresh
exact labels.
For fresh diversity queues, add `--include_unmatched`,
`--exclude_verified_hashes`, `--max_per_family_label`, and
`--prefer_unmatched` to avoid filling the queue with many variants from one
known feedback family.

Build a manual submission plan from saved verified rows:

```bash
python3 scripts/igp24_submission_plan.py \
  --verified_results /tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual \
  --candidate_jsonl /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl \
  --candidate_jsonl /tmp/igp24_exact_label_shortlist_20260705 \
  --baseline_csv data/igp24/lmfdb_baseline.csv \
  --output_dir /tmp/igp24_submission_plan_20260705
```

This helper is local/file-only. It selects one representative per expected
`(24Tt, r)` pair and writes manual review artifacts; it does not submit to
SAIR or claim scoreability without exact `r` and discriminant evidence.

## IGP24 Generation Strategies

`--igp24_generation_strategy` can be:

- `uniform`
- `low_height`
- `sparse`
- `lower_degree`
- `structured`
- `four_real_seed`
- `quartic_lift`
- `fixed_sparse_template`
- `mixed`

Target-specific presets are opt-in through `--igp24_generation_preset`:

- `none`
- `r0`
- `r2`
- `r4`

The experimental composed-support families, especially `quartic_lift`, are the
current focus because exact Magma verification confirmed non-generic labels in
that branch.

## Important Files

- `train.py`: Axplorer training/generation entry point.
- `src/envs/igp24.py`: IGP24 environment and coefficient tokenizer.
- `src/igp24/polynomial.py`: exact polynomial utilities and proxy scoring.
- `src/igp24/ledger.py`: JSONL candidate ledger helpers.
- `src/igp24/verifiers/`: PARI, Magma, and SAIR verifier interfaces.
- `scripts/igp24_benchmark.py`: short CPU benchmark runner.
- `scripts/igp24_non_generic_diagnostic.py`: proxy non-generic shortlist tool.
- `scripts/igp24_queue_structure_audit.py`: local exact-algebra structure audit.
- `scripts/igp24_offline_verify.py`: offline/local/manual verification handoff.
- `scripts/igp24_verified_label_feedback.py`: exact-label feedback summaries.
- `scripts/igp24_exact_label_shortlist.py`: feedback-family shortlist planner.
- `docs/EXPERIMENTS.md`: benchmark and verification result summary.
- `NOTES_IGP24.md`: design notes and research rationale.
- `TODO_IGP24.md`: live project log and task status.

## License

Apache-2.0. See [LICENSE](LICENSE).
