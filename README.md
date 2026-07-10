# IGP24 Axplorer

IGP24 Axplorer is a research toolkit for finding monic degree-24 integer
polynomials that may improve signatures in the
[SAIR IGP24 inverse Galois competition](https://competition.sair.foundation/competitions/igp24/overview).
It extends [Axplorer](https://github.com/AxiomMath/axplorer) with structured
algebraic generators, a feedback-conditioned transformer, exact local checks,
adaptive Frobenius evidence, historical backtesting, and score-aware candidate
review.

This repository is not an exact Galois-group oracle or an unattended
submission bot. Generated polynomials are proposals. Exact verification and
live submission remain explicit, separately gated steps.

## The Search Problem

Candidates have the form

```text
f(x) = x^24 + a23*x^23 + ... + a1*x + a0
```

The code represents a candidate internally by its 24 free coefficients:

```text
[a0, a1, ..., a23]
```

Competition exports append the fixed leading coefficient:

```text
[a0, a1, ..., a23, 1]
```

An IGP24 signature is a pair `(24Tt, r)`, where `24Tt` is the transitive
Galois-group label and `r` is the exact number of real roots. Producing a valid
polynomial is only the first hurdle. Useful candidates must reach an uncovered
or low-team signature, avoid known submissions, and have competitive exact
number-field discriminants.

One polynomial has exactly one true Galois label. Sets of labels that survive
local compatibility tests are therefore exploration targets, not additive
score and not a probability distribution.

## Research Loop

```text
fresh SAIR state + exact historical outcomes
                    |
          score-aware target planning
                    |
        +-----------+-----------+
        |                       |
 structured generators     AXG transformer
        |                       |
        +-----------+-----------+
                    |
       canonical deduplication and
          exact local validation
                    |
       adaptive Frobenius exclusion
                    |
       exact label and nfdisc checks
                    |
       offline score and safety gate
                    |
          explicit live submission
                    |
          feedback into both lanes
```

The current strategy has six parts:

1. **Target value, not volume.** Fresh SAIR progress and submission history
   identify uncovered signatures, low-team pairs, discriminant-improvement
   opportunities, and already exhausted basins.
2. **Use two complementary proposal lanes.** Executable construction families
   preserve intended composition or block structure; AXG trains and samples on
   the GPU from target-`r` and exact-feedback data. Generic local search remains
   a comparison baseline.
3. **Reject cheap failures early.** Known canonical hashes, duplicate or
   translation-equivalent rows, wrong real-root counts, reducible polynomials,
   repeated roots, and invalid coefficient vectors are removed before expensive
   group work.
4. **Escalate evidence adaptively.** Factorization patterns are collected only
   at unramified primes. Additional primes are sampled while they continue to
   eliminate valuable target groups.
5. **Require exact evidence for score claims.** Compatibility can rule groups
   out, but only exact label and discriminant evidence can make a candidate
   submission-grade or support official score economics.
6. **Learn from negative results.** Crowded labels, duplicates, wrong-`r` rows,
   invalid samples, and construction-family collapses remain explicit negative
   feedback. They are not silently turned into positive generator examples.

## Evidence Contract

| Layer | What it establishes | What it does not establish |
| --- | --- | --- |
| Local exact checks | Degree, coefficient validity, exact `r`, irreducibility, squarefreeness, and polynomial discriminant | Exact Galois label or official score |
| Canonical history gate | Matches against known submissions under the configured canonicalization rules | Mathematical equivalence under every possible transformation |
| Adaptive Frobenius filter | Necessary cycle-type compatibility from unramified primes | Exact label, posterior probability, or expected points |
| GAP group-cycle index | Cycle types and structural metadata for indexed transitive groups | Proof that a surviving group is the true group |
| Magma / PARI / exact fallbacks | Exact-label and field-discriminant evidence when the selected backend succeeds | Fresh competition coverage or team counts |
| SAIR sync | Current label progress, our submission history, and scoring state | Independent local verification of a candidate |

The repository can consume both partial and complete group indexes. Partial
indexes explicitly retain unknown unindexed label mass. A complete index spans
all 25,000 degree-24 transitive groups, but survival in that index is still only
necessary evidence. Numeric expected score is withheld unless an exact verified
pair supports official score economics.

## Current Research Direction

The pipeline has produced SAIR-accepted polynomials at several real-root
counts, but acceptance is not the main bottleneck. Structured families can
collapse into familiar transitive-group basins, while learned generators can
memorize training rows, reproduce narrow support patterns, or emit reducible
polynomials. The project therefore measures novelty, local validity, target
survival, nuisance-group survival, and known-hash reproduction instead of
promoting a model on training loss alone.

The default research cycle exercises the complete stack: refresh state, rebuild
the feedback corpus, train a bounded new AXG iteration, sample on the GPU,
compare against a structured construction lane, run exact local and adaptive
filters, and update the experiment ledger. A candidate advances only when the
measured evidence improves.

Fast-changing results and current candidate decisions intentionally live
outside this README. See [Experiment Notes](docs/EXPERIMENTS.md) and the
[live project log](TODO_IGP24.md).

## Setup

The base environment uses Python 3.12, PyTorch, SymPy, NumPy, Numba, and
pytest:

```bash
micromamba env create -f environment.yml
micromamba activate env_axplorer
python -m pytest -q
```

Run commands from the repository root. Install a CUDA-enabled PyTorch build
appropriate for your system if you want to train or sample AXG on a GPU.

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

Optional external systems unlock additional workflows:

- GAP with the transitive-groups library rebuilds the group-cycle index.
- PARI/GP supplies exact number-field discriminant checks.
- Magma supplies exact transitive-group verification.

The local generation and test paths do not require those optional systems.

## Quick Start

Run a small CPU-only candidate-generation smoke:

```bash
python train.py \
  --env_name igp24 \
  --exp_name igp24_cpu_smoke \
  --dump_path /tmp/igp24_cpu_smoke \
  --seed 123 \
  --cpu true \
  --data_generation_only true \
  --process_pool false \
  --num_workers 1 \
  --gensize 12 \
  --pop_size 6 \
  --ntest 2 \
  --gen_batch_size 2 \
  --always_search false \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --igp24_generation_strategy mixed \
  --igp24_ledger_path /tmp/igp24_cpu_smoke/candidates.jsonl
```

Candidate ledgers are JSONL. Records include coefficients, canonical hashes,
exact and proxy metadata, generation provenance, and rejection or verification
state.

Check GPU readiness with the real training path:

```bash
python scripts/igp24_gpu_smoke.py \
  --output_dir /tmp/igp24_gpu_smoke
```

## Common Workflows

### Refresh SAIR State

Credentials are read from the environment and are never written to artifacts:

```bash
export SAIR_API_KEY=...
python scripts/igp24_sair_sync.py \
  --fetch_live \
  --allow_partial \
  --output_dir /tmp/igp24_sair_sync
```

The sync is read-only. It retrieves competition metadata, participation state,
label progress, submission status, and downloadable rows. Partial mode retains
fresh progress if a submission endpoint is unavailable while marking submission
history incomplete.

### Compare CPU Generators

```bash
python scripts/igp24_benchmark.py \
  --strategies sparse,structured,mixed \
  --seeds 301 \
  --target_rs none,4 \
  --gensize 12 \
  --pop_size 6 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 2 \
  --output_dir /tmp/igp24_benchmark
```

### Prepare Exact Verification

```bash
python scripts/igp24_offline_verify.py \
  path/to/candidates.jsonl \
  --output_dir /tmp/igp24_verification \
  --max_records 4
```

This command is a dry run by default. It validates the input and prepares
PARI/GP and Magma artifacts without executing either system. Exact backends and
SymPy fallback calculations require their corresponding explicit flags.

Every research script provides `--help`. The most useful orchestration entry
points are:

| Purpose | Entry point |
| --- | --- |
| Core Axplorer generation and training | `train.py` |
| Feedback-aware AXG dataset | `scripts/igp24_active_learning_dataset.py` |
| Bounded GPU train/sample probes | `scripts/igp24_gpu_sampler_probe.py` |
| Structured construction registry and routing | `scripts/igp24_construction_target_router.py` |
| Candidate compatibility | `scripts/igp24_candidate_group_compatibility.py` |
| Adaptive prime benchmark | `scripts/igp24_adaptive_frobenius_benchmark.py` |
| Exact-verification handoff | `scripts/igp24_offline_verify.py` |
| Packet selection | `scripts/igp24_packet_optimizer.py` |
| Conservative final gate | `scripts/igp24_group_compatible_submission_gate.py` |
| Consolidated offline go/no-go report | `scripts/igp24_current_offline_report.py` |

## Repository Map

- `src/envs/igp24.py`: IGP24 environment, generation strategies, tokenizer,
  and local-search integration.
- `src/igp24/polynomial.py`: exact polynomial checks, canonicalization, and
  proxy metadata.
- `src/igp24/constructions/`: construction-family registry and executable
  structure-preserving generators.
- `src/igp24/group_compatibility.py`: partial/full index semantics and
  cycle-type compatibility.
- `src/igp24/adaptive_frobenius.py`: adaptive unramified-prime evidence.
- `src/igp24/verifiers/`: PARI, Magma, and SAIR interfaces.
- `scripts/`: reproducible planning, generation, training, backtest,
  verification, and packaging workflows.
- `data/igp24/lmfdb_baseline.csv`: bundled frozen baseline data.
- `data/igp24/model_registry/`: immutable AXG model and run manifests.
- `docs/EXPERIMENTS.md`: benchmark and verification summaries.
- `NOTES_IGP24.md`: design rationale and mathematical notes.
- `TODO_IGP24.md`: live status, command log, future stages, and next tasks.

## Safety and Reproducibility

- Never commit `SAIR_API_KEY` or pass it as a command-line value.
- SAIR submission validation is dry-run by default; a live POST requires an
  explicit execution flag and a separate human decision.
- GPU samples, proxy scores, and group compatibility are never presented as
  exact labels.
- Known submission hashes carry zero generator-training weight, can be blocked
  during model export, and are rejected again by packet optimization and the
  final gate.
- Random seeds, model manifests, source hashes, command metadata, and JSON/JSONL
  artifacts are retained so experiments can be replayed.
- Large checkpoint binaries are referenced by manifests rather than committed
  to the repository.

For disposable experiments, prefer an output directory under `/tmp`. Commit
only distilled reports, durable datasets, and provenance needed to reproduce a
result.

## License

Apache-2.0. See [LICENSE](LICENSE).
