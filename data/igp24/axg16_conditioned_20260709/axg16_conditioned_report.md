# AXG-1.6 Anti-Collapse Cycle Report

Created: 2026-07-09

## Objective

Run the next standing-operating-rule cycle after AXG-1.5: fresh SAIR sync,
active-learning corpus rebuild, new model registry version, bounded CUDA
target-r training/exports, CPU proxy scoring, advisory-aware anti-basin
proposal gating, and local SAIR dry-run validation. No live SAIR submission was
authorized or made.

## SAIR Sync

- Sync directory: `data/igp24/axg16_conditioned_20260709/sair_sync/`
- Partial sync: `false`
- Labels: 25,000
- Remaining signatures: 47,811
- Submission details/downloads: 24/24 and 24/24
- Scoreable rows: 208
- Pending rows: 0
- Unmatched rows: 0

## Corpus

- Dataset: `data/igp24/active_learning/axg_training_dataset_20260709_axg16_conditioned.jsonl`
- Rows: 654
- Source roles: 171 accepted-feedback rows, 217 artifact rows, 58 candidate-queue rows, 208 SAIR submission rows
- Class counts:
  - accepted duplicate/collapsed basin: 435
  - accepted globally covered/high-team basin: 8
  - accepted useful score-positive: 8
  - exact local valid: 97
  - locally invalid: 30
  - wrong real-root count: 76

## CUDA Runs

AXG-1.6 used the AXG virtualenv with `PYTHONPATH=.` and PyTorch
2.12.0+cu130 on the RTX 5090. The export settings used open sampling,
support-gcd filtering, even-support avoidance, family cap 4 for r16/r20/r24,
family cap 3 for the initial r12 probe, and basin caps of 1 for r12 then 2
for r16/r20/r24.

| r | runtime s | max GPU % | avg GPU % | export rows | decoded | scored | valid | target survivors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | 192.000 | 89.000 | 77.479 | 369 | 6 | 6 | 5 | 5 |
| 16 | 194.571 | 89.000 | 77.400 | 276 | 10 | 10 | 10 | 8 |
| 20 | 192.771 | 89.000 | 78.021 | 310 | 8 | 8 | 8 | 8 |
| 24 | 192.646 | 89.000 | 78.128 | 245 | 8 | 8 | 8 | 7 |

Aggregate runtime was 771.988 seconds. Aggregate exports: 1,200. Aggregate
scored decoded rows: 32. Valid rows: 31. Target-r survivors: 28.

## Gate Result

- Proposal summary: `data/igp24/axg16_conditioned_20260709/proposal_loop/axg16_anti_collapse_multir_gate_20260709/proposal_loop_summary.json`
- Candidate rows: 32
- Filtered target-r rows: 29
- Eligible model-generated rows: 8
- Selected rows: 7
- Decision: `reviewed_packet_ready_for_dry_run`
- Fatal risk count: 0
- Advisory risk count: 7
- Selected r values: r12, r20, and r24
- Selected diversity: 7 basin fingerprints, 7 mod-p signatures, 4 template families, 2 perturbation modes
- Sync hold reasons: none
- Dry run: `ok=true`, 7 polynomials, 929 request bytes

The selected packet is locally ready under the advisory/fatal risk split and
fresh sync gate. Live SAIR submission still requires explicit user approval.

## Decision

AXG-1.6 is meaningful full-stack progress: it refreshed the corpus, exercised
the GPU stack across four target r values, reduced fatal basin risk to zero in
the selected packet, and produced a larger 7-row dry-run-ready packet than the
AXG-1.5 advisory replay. It is not yet significant verified score progress
because no live SAIR verification/scoring has occurred.

Best next step: request explicit approval before live-submitting either the
AXG-1.6 7-row packet or a deduplicated union/review of AXG-1.5 and AXG-1.6
ready packets. If not submitting, the next model iteration should improve
decoded yield while preserving the advisory/fatal gate split.
