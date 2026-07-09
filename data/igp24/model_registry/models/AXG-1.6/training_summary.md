# AXG-1.6 Training Summary

Status: four bounded CUDA target-r exports completed under the full-stack
SAIR-synced operating rule; no live SAIR submission was made.

AXG-1.6 used fresh SAIR state from
`data/igp24/axg16_conditioned_20260709/sair_sync/` and the active-learning
dataset
`data/igp24/active_learning/axg_training_dataset_20260709_axg16_conditioned.jsonl`.
The dataset had 654 rows, including 435 accepted duplicate/collapsed-basin
rows and 8 score-positive rows. Successful runs used the AXG venv with
`PYTHONPATH=.` so PyTorch 2.12.0+cu130 could access the RTX 5090.

## Results

| r | gpu s | max gpu % | avg gpu % | export rows | decoded | scored | valid | target survivors | selected | decision |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 12 | 192.000 | 89.000 | 77.479 | 369 | 6 | 6 | 5 | 5 | 2 | `reviewed_packet_ready_for_dry_run` |
| 16 | 194.571 | 89.000 | 77.400 | 276 | 10 | 10 | 10 | 8 | 0 | `reviewed_packet_ready_for_dry_run` |
| 20 | 192.771 | 89.000 | 78.021 | 310 | 8 | 8 | 8 | 8 | 2 | `reviewed_packet_ready_for_dry_run` |
| 24 | 192.646 | 89.000 | 78.128 | 245 | 8 | 8 | 8 | 7 | 3 | `reviewed_packet_ready_for_dry_run` |

Main GPU runtime: 771.988s (12.87m). Aggregate exports: 1,200. Aggregate
scored decoded rows: 32. Valid rows: 31. Target-r survivors: 28. All selected
rows were model-generated.

## Gate Result

The AXG-1.6 multi-r proposal loop selected a 7-row packet from r12, r20, and
r24 model-generated survivors, with seven distinct basin fingerprints, seven
mod-p signatures, four template families, and two perturbation modes. Fatal
risk count was 0; advisory loose-basin warnings were present on all selected
rows. The packet passed local SAIR dry-run validation (`ok=true`,
7 polynomials, 929 bytes). There were no sync holds and no selected exact-pair
pending collisions.

## Decision

Do not live-submit automatically. The packet is locally ready under the
advisory/fatal gate split, but live SAIR submission still requires explicit
approval. The next model iteration should improve decoded yield while
preserving the stricter anti-collapse controls.
