# AXG Known-Hash r24 Negative GPU Evidence

Created: 2026-07-09

## Purpose

After the fresh SAIR sync showed that the previous group-compatible r24 packet
contained already-submitted hashes, a bounded CUDA probe tested whether the
current high-real AXG training corpus could generate genuinely new r24 rows
while excluding known submission hashes.

This was a safety-only run: no SAIR calls, no exact verifier calls, no network
calls, and no live submission.

## Inputs

- Run id: `axg114_r24_knownhash_20260709T2323Z`
- Source commit: `200200dbc96d0cd47c96ae256e1743a8123b9935`
- Target r: `24`
- Training JSONL:
  `data/igp24/active_learning/axg_training_dataset_20260709_axg113_high_real.jsonl`
- Training target-r set: `8,12,16,20,24`
- Known-submission hash source:
  `data/igp24/remediation_20260709/submission_gate_phase6/fresh_sair_sync_20260709T231426Z/sair_submission_rows.jsonl`

## GPU Export Result

| metric | value |
| --- | ---: |
| runtime seconds | 106.853 |
| return code | 0 |
| timed out | false |
| GPU used | true |
| attempted samples | 2048 |
| export records written | 332 |
| decoded unique coefficient rows | 35 |
| invalid decode records | 297 |
| duplicate decoded records skipped | 1668 |
| known submitted hashes loaded | 265 |
| known submitted hashes skipped | 1 |
| stop reason | attempt_budget_exhausted |

The exporter intentionally avoided CPU scoring/local search during the CUDA
phase and wrote unscored sample records for a separate CPU proxy pass.

## CPU Proxy Scoring Result

| metric | value |
| --- | ---: |
| records read | 332 |
| decoded input records | 35 |
| scored records | 35 |
| valid records | 0 |
| rejected records | 35 |
| unique hashes | 35 |
| duplicate hash records | 0 |

All 35 decoded rows were rejected for `coefficient_height_exceeds_bound`. The
observed coefficient-height range among decoded rows was `725989` to
`12098014798404944990232070`, so none reached real-root, discriminant, group
compatibility, packet-optimizer, or submission-gate evaluation.

## Interpretation

This is useful negative evidence. Known-hash exclusion did its job, but the r24
mixed/high-temperature lane escaped submitted hashes by producing coefficient
vectors outside the configured scoring bound. The next remediation-aligned AXG
iteration should either lower temperature, constrain support/templates more
tightly, add coefficient-height-aware rejection/risk training, or prefer
group-directed structured construction search before another live packet is
considered.

No rows from this run should be submitted.
