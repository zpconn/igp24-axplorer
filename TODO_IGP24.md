# IGP24 Live TODO

This file is the working project log for the Axplorer-based IGP24 candidate
generator. Keep it current as implementation, tests, smoke runs, and benchmark
results change.

## Current Status

- Branch: `igp24-dev`
- Remote target: `zpconn/igp24-axplorer`
- Last pull: 2026-07-03, `git pull --ff-only` -> already up to date.
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

- [in progress] Add generation strategies beyond uniform random coefficients.
  - [pending] Sparse coefficient vectors.
  - [pending] Low-height biased dense vectors.
  - [pending] Lower-degree coefficient bias.
  - [pending] Simple structured families such as binomial/trinomial seeds.
- [pending] Make generation strategy configurable from the CLI.
- [pending] Record generation strategy in candidate metadata and ledger records.

## Stage 1: Scoring And Metadata

- [in progress] Preserve proxy-only scoring while making score components easier
  to inspect.
  - [pending] Store score component breakdown in each ledger record.
  - [pending] Keep `target_t` metadata-only unless exact external verification
    is actually performed.
  - [pending] Keep invalid rejection reasons explicit and stable.

## Stage 1: Local Search

- [in progress] Improve bounded local search observability.
  - [pending] Track attempted, accepted, and rejected move counts.
  - [pending] Track the accepted move type.
  - [pending] Record whether accepted moves improved height, discriminant,
    root-count match, or modular diversity.
  - [pending] Preserve determinism under a fixed seed.

## Stage 1: CLI And Smoke Runs

- [pending] Add practical short CPU-only commands to documentation.
- [pending] Run a small reproducible CPU-only generation smoke.
- [pending] Record exact command, runtime, valid candidate count, best score, and
  ledger path below.

## Tests And Checks

- [pending] Run `python -m pytest`.
- [pending] Run an import check proving `square`, `isosceles`, `sphere`, and
  `igp24` remain discoverable.
- [pending] If local dependency issues block the literal command, record the
  exact blocker and run the closest available equivalent.

## Benchmark And Smoke Results

No current stage-1 benchmark results yet.

## Blockers / Environment Notes

- The previous stage-0 run used a temporary dependency target at
  `/tmp/igp24_pydeps` because the base shell did not have `python`, `numpy`,
  `sympy`, `pytest`, or `torch` available directly.
- Re-check local dependency state before running stage-1 tests and smoke jobs.

## Recommended Next Tasks

- [pending] Implement configurable generation strategies and tests.
- [pending] Add score component metadata to ledger records.
- [pending] Add local-search stats metadata and tests.
- [pending] Run and document a short CPU-only generation benchmark.
