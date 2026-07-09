# IGP24 Remediation Phase 1: Generator Training Contract

Created: 2026-07-09

## Purpose

Phase 0 identified a training-semantics defect: active-learning rows contained score-aware labels and weights, but the language-model training path still imitated the loaded rows uniformly. That allowed accepted-but-crowded collapse examples to act like positive demonstrations.

Phase 1 makes generator eligibility explicit and moves the filtering/weighting decision into the dataset and sampler path used by `train.py`.

## Implemented Contract

Each active-learning JSONL row now carries a `generator_training` object with:

- `eligible`
- `weight`
- `role`
- `reason`
- `pair_key`
- `label`
- `construction_family`
- `basin_fingerprint`
- `split_group_key`

Generator roles are policy-defined in `scripts/igp24_active_learning_dataset.py`. Score-positive rows are high-weight positives, exact local exploration rows are low-weight exploration positives, and crowded-collapse, duplicate, wrong-r, and invalid rows are ineligible for generator imitation.

## Training Path Changes

`src/datasets.py` now enforces the contract when loading IGP24 JSONL training data:

- skips rows with `generator_training.eligible=false`
- skips rows with non-positive generator weights
- deduplicates by canonical coefficient hash
- caps eligible rows by pair, label, construction family, and basin fingerprint
- stores generator role, weight, and grouped split key on each datapoint
- uses grouped train/eval splitting and fails if a group appears in both splits
- keeps a single-family corpus entirely in train rather than creating a leaky
  random eval split; empty eval loss is reported as `nan`

`train.py` now passes those weights and metadata into `CharDataset`, and `InfiniteDataLoader` uses a weighted replacement sampler with role/label/family sampling telemetry.

## Probe Result

Sampler probe: `data/igp24/remediation_20260709/generator_sampler_probe_summary.json`

- Train rows: 44
- Eval rows: 3
- Train/eval group overlap: none
- Generator-ineligible rows skipped: 390
- Target-r-filtered rows skipped: 122
- Duplicate canonical hashes skipped: 2
- Draws: 4096
- Sampled score-positive draws: 887
- Sampled exact-local exploration draws: 3209
- Zero-weight negative roles sampled: none

The refreshed AXG-1.13 dataset has 635 physical rows but only 68 generator-eligible rows: 8 score-positive rows with sampling mass 96.0 and 60 exact-local exploration rows with sampling mass 60.0. All 462 crowded-collapse rows are ineligible.

## Validation

Full test suite after remediation:

`PYTHONPATH=. /home/zpconn/code/axplorer/.venv/bin/python -m pytest -q`

Result: 312 passed.

Focused hardening rerun after the single-family split fix:

`PYTHONPATH=. /home/zpconn/code/axplorer/.venv/bin/python -m pytest -q tests/test_igp24.py tests/test_igp24_active_learning_dataset.py`

Result: 42 passed.

## Remaining Gate

This phase fixes the training-contract defect, but the active research goal is not complete. The next completed AXG iteration must train under this contract, submit only explicitly approved and gated rows, and remain open until SAIR verifies actual score improvement.
