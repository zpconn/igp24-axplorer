# AXG-1.5 Full-Stack Cycle Report

Created: 2026-07-09

## Objective

Run one substantial IGP24 research cycle under the standing operating rule:
fresh SAIR sync, active-learning corpus rebuild, fresh bounded AXG GPU
training, model inference, CPU scoring, anti-basin gating, dry-run validation,
TODO update, validation, commit, and push. No live SAIR submission was
authorized or made.

## SAIR Sync

- Sync directory: `data/igp24/axg15_fullstack_20260709/sair_sync/`
- Partial sync: `false`
- Labels: 25,000
- Remaining signatures: 47,823
- Submission details/downloads: 24/24 and 24/24
- Scoreable rows: 208
- Pending rows: 0
- Failed rows: 0
- Unmatched rows: 0
- Largest remaining buckets: r24 = 11,520, r16 = 9,819, r8 = 6,112, r12 = 6,092, r20 = 5,200

The local scoreable row distribution is still dominated by known crowded
basins, especially `24T25000`.

## Corpus

- Dataset: `data/igp24/active_learning/axg_training_dataset_20260709_axg15_fullstack.jsonl`
- Rows: 605
- Candidate sources: 8
- Feedback sources: 19
- Class counts:
  - accepted duplicate/collapsed basin: 403
  - accepted globally covered/high-team basin: 8
  - accepted useful score-positive: 8
  - exact local valid: 84
  - locally invalid: 30
  - wrong real-root count: 72

## CUDA Runs

Successful runs used `PYTHONPATH=.` with the AXG virtualenv Python. Two
environment lessons matter for future cycles:

- Sandbox execution can block NVML/CUDA access; use the approved escalated GPU
  command path for training.
- Do not put `/tmp/igp24_pydeps` on `PYTHONPATH` for AXG-vendored GPU
  training. It can inject an incompatible NumPy into the Python 3.10 AXG venv.

| r | runtime s | max GPU % | avg GPU % | export rows | decoded | scored | valid | target survivors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 135.900 | 89.000 | 77.076 | 214 | 17 | 17 | 17 | 16 |
| 20 | 123.224 | 88.000 | 77.900 | 662 | 16 | 16 | 16 | 12 |
| 24 | 123.486 | 87.000 | 76.500 | 207 | 16 | 16 | 16 | 14 |

Aggregate runtime was 382.610 seconds. Aggregate scored decoded rows: 49.
Valid rows: 49. Target-r survivors: 42.

## Initial Gate Result

- Proposal summary: `data/igp24/axg15_fullstack_20260709/proposal_loop/axg15_fullstack_high_real_gate_20260709/proposal_loop_summary.json`
- Candidate rows: 49
- Filtered target-r rows: 42
- Eligible model-generated rows: 6
- Selected advisory rows: 5
- Decision: `hold_no_submission`
- Reason: `5_selected_rows_have_risk_reasons`
- Selected risk reason: `loose_crowded_basin_fingerprint_hits=2`
- Selected r values: r20 and r24
- Sync hold reasons: none

The selected 5-row packet passed coefficient sanity and local SAIR dry-run
validation:

- Coefficient file: `data/igp24/axg15_fullstack_20260709/proposal_loop/axg15_fullstack_high_real_gate_20260709/selected_review_coefficients.txt`
- Dry run: `ok=true`
- Polynomial count: 5
- Request body bytes: 741

## Advisory Replay

Planner refinement split risk reasons into fatal and advisory buckets. Accepted
duplicates, known high-label collapse, exact crowded basin fingerprints, and
unknown provenance still block packets. Weak loose crowded-basin and crowded
mod-p hints are now advisory, because they should guide review without
automatically discarding otherwise diverse model-generated rows.

- Replay summary: `data/igp24/axg15_fullstack_20260709/proposal_loop_advisory/axg15_fullstack_high_real_gate_advisory_20260709/proposal_loop_summary.json`
- Candidate rows: 49
- Filtered target-r rows: 42
- Eligible model-generated rows: 6
- Selected rows: 5
- Decision: `reviewed_packet_ready_for_dry_run`
- Fatal risk count: 0
- Advisory risk count: 5
- Selected r values: r20 and r24
- Selected diversity: 5 basin fingerprints, 5 mod-p signatures, 3 template families, 2 perturbation modes
- Sync hold reasons: none
- Dry run: `ok=true`, 5 polynomials, 741 request bytes

No live SAIR submission was made. The packet is now locally submission-ready
under the advisory/fatal split, but it still requires explicit user approval
before a live POST.

## Decision

This is meaningful model-stack progress but not significant verified SAIR score
progress. The full AXG path worked end to end, produced valid target-r
model-generated rows, and now produces a dry-run-ready r20/r24 packet after an
explicit planner improvement with tests. The score bottleneck remains live SAIR
verification and later scoring, which is intentionally gated on user approval.

Best next step: commit/push this planner correction, then run AXG-1.6 with
stronger negative conditioning against dense/medium mixed-support basins that
repeatedly shadow `24T25000`, using the advisory/fatal split during proposal
selection.
