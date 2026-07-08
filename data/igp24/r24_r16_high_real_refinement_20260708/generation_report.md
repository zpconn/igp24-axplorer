# r24/r16 High-Real Refinement Generation

Created: 2026-07-08

This pass ran short bounded AXG target-r CUDA sample exports for r24 and r16
after stopping the r8 quartic-in-x^6 lane. r8 stayed stopped and r20 stayed
held because the latest complete local sync still has pending `24T25000|r=20`
rows.

`SAIR_API_KEY` was not present in the environment, so no live sync or live
submission was attempted. The run used
`data/igp24/sair_sync_20260708_r8_followup_after_submit/`.

## Knobs

- Training corpus: `data/igp24/active_learning/axg_training_dataset_20260707_axg11_target_r_seeded.jsonl`
- Training target-r set: `12,16,20,24`
- Per-lane max steps: 2400
- Per-lane sample attempts: 2048
- Temperature: 1.25
- Top-k: open (`-1`)
- Unique target: 256
- Generation strategy: `mixed`
- Filters: non-even support, support gcd 1
- Caps: family cap 24, basin fingerprint cap 1

## Results

| lane | runtime s | avg GPU % | exported | decoded | scored | valid | target-r survivors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| r24 | 89.150 | 73.372 | 568 | 44 | 44 | 36 | 13 |
| r16 | 85.883 | 75.310 | 422 | 32 | 32 | 30 | 12 |

The one-per-basin export pressure produced fewer decoded rows than broader
AXG-1.4 exports, but it materially improved provenance diversity. The r16 lane
had enough target-r survivors to clear the anti-basin packet gate; r24 improved
to three strong rows but remained one row/basin short.
