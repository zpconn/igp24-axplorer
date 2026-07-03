# IGP24 Axplorer

Stage-0 research scaffold for using Axplorer as a candidate generator for the
SAIR IGP24 inverse Galois competition.

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
  --cpu true
```

Useful IGP24-specific generation flags:

```text
--igp24_generation_strategy mixed
--igp24_sparse_terms 4
--igp24_low_height_bound 3
```

`--igp24_generation_strategy` can be `mixed`, `uniform`, `low_height`,
`sparse`, `lower_degree`, or `structured`.

Candidate records are written as JSONL by default:

```text
data/igp24/candidates.jsonl
```

## Run Tests

```bash
python -m pytest
```

The tests cover polynomial construction, export format, exact utility checks,
proxy scoring, local search determinism, ledger deduplication, verifier stubs,
and environment registration.

## Main Files

- `src/envs/igp24.py`: Axplorer environment and coefficient tokenizer.
- `src/igp24/polynomial.py`: exact polynomial utilities and proxy scoring.
- `src/igp24/ledger.py`: JSONL candidate ledger.
- `src/igp24/verifiers/`: PARI, MAGMA, and SAIR stubs.
- `NOTES_IGP24.md`: architecture notes and stage-0 rationale.
- `TODO_IGP24.md`: staged roadmap.

## License

This fork follows the upstream Axplorer license. See `LICENSE`.
