# AXG-1.5 Training Summary

Status: three bounded CUDA target-r exports completed under the full-stack
SAIR-synced operating rule; no live SAIR submission was made.

AXG-1.5 used the fresh 2026-07-09 SAIR sync and active-learning dataset
`data/igp24/active_learning/axg_training_dataset_20260709_axg15_fullstack.jsonl`.
The dataset had 605 rows, including 403 accepted duplicate/collapsed-basin
rows and 8 score-positive rows. The first two CUDA attempts diagnosed useful
environment issues: sandboxed GPU access blocked NVML, and
`PYTHONPATH=/tmp/igp24_pydeps` injected an incompatible NumPy into the AXG
Python 3.10 venv. The successful runs used the AXG venv with `PYTHONPATH=.`
so PyTorch 2.12.0+cu130 could access the RTX 5090.

## Results

| r | gpu s | max gpu % | avg gpu % | export rows | decoded | scored | valid | target survivors | selected | decision |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 16 | 135.900 | 89.000 | 77.076 | 214 | 17 | 17 | 17 | 16 | 0 | `hold_no_submission` |
| 20 | 123.224 | 88.000 | 77.900 | 662 | 16 | 16 | 16 | 12 | 3 | `hold_no_submission` |
| 24 | 123.486 | 87.000 | 76.500 | 207 | 16 | 16 | 16 | 14 | 2 | `hold_no_submission` |

Main GPU runtime: 382.610s (6.38m). Aggregate scored decoded rows: 49. Valid
rows: 49. Target-r survivors: 42. All selected rows were model-generated.

## Gate Result

The high-real AXG-1.5 proposal loop selected a 5-row advisory packet from r20
and r24 model-generated survivors, with five distinct basin fingerprints, five
mod-p signatures, three template families, and two perturbation modes. The
packet passed coefficient sanity and local SAIR dry-run validation
(`ok=true`, 5 polynomials, 741 bytes), but the strict planner held live
submission because all selected rows carried
`loose_crowded_basin_fingerprint_hits=2`. There were no pending sync holds and
no direct selected exact-pair pending collisions.

## Decision

Do not live-submit automatically. The packet is format-ready and potentially
interesting, but it is not a strict planner recommendation yet. The next AXG
iteration should either make the loose-crowded warning advisory instead of
fatal with explicit tests, or train/export with stronger anti-collapse
conditioning that avoids repeated dense/medium mixed-support basins before
selection.
