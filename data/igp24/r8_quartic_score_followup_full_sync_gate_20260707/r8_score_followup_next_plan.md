# r8 Quartic-Lift Score Follow-Up Plan

Generated from the recovered full SAIR sync on 2026-07-07. This is an
offline planning artifact only; no SAIR submission or dry-run was performed by
this pass.

## Source Of Truth

- Full sync: `data/igp24/sair_sync_20260707/`
- Score-aware plan:
  `data/igp24/score_aware_target_plan_from_sync_20260707/`
- Current r8 candidate source:
  `data/igp24/r8_quartic_score_followup_probe_20260707/`
- Full-sync anti-basin gate:
  `data/igp24/r8_quartic_score_followup_full_sync_gate_20260707/`

Full sync state:

- `partial_sync=false`
- `submission_state_complete=true`
- 18 submissions
- 167 accepted rows
- 135 scoreable rows
- 32 pending rows
- 0 failed rows
- 0 unmatched rows
- pending pairs: `24T24932|r=24`, `24T24984|r=12`, `24T24932|r=12`

Planner decision:

- recommended lane: `r8_quartic_lift_score_followup`
- source pair: `24T9993|r=8`
- visible points: `0.0019`
- solved teams: 10
- submission recommended now: `false`
- GPU/model training recommended now: `false`

## Gate Result

The current pure `r8_quartic_lift` generator was already rerun as a bounded
CPU-only probe with seeds `2801,2802`. It produced 12 local `r=8` candidate
rows, but only 6 unique hashes, all overlapping already accepted/submitted
pure-template rows.

Full-sync anti-basin command:

```bash
python3 scripts/igp24_anti_basin_planner.py \
  --candidate_jsonl data/igp24/r8_quartic_score_followup_probe_20260707/r8_quartic_lift_r8_seed_2801/candidates.jsonl \
  --candidate_jsonl data/igp24/r8_quartic_score_followup_probe_20260707/r8_quartic_lift_r8_seed_2802/candidates.jsonl \
  --progress_snapshot_json /tmp/igp24_full_sync_progress_snapshot_20260707.json \
  --output_dir data/igp24/r8_quartic_score_followup_full_sync_gate_20260707 \
  --target_rs 8 \
  --packet_limit 12 \
  --min_packet_rows 8
```

Result:

- candidates scored: 12
- eligible candidates: 0
- selected rows: 0
- `recommended_for_sair_packet=false`
- status: `hold_no_submission`
- rejection/hold reasons: `support_gcd_not_one`,
  `even_support_g_x_squared_like`, `accepted_hash_duplicate`

## Decision

Do not submit from the current pure `g(x^6)` r8 family. The useful signal is
the score-positive pair `24T9993|r=8`, but the finite pure-template generator is
exhausted. Repeating it or scaling seeds will mostly recycle the same six
hashes and known even-support basin.

## Next Work

The next useful goal should add r8 perturbation diversity before generating a
new packet:

1. Add an opt-in perturbed r8 quartic-lift mode or sibling strategy.
   - Start from the six positive-fiber `g(x^6)` templates.
   - Add 1-3 small off-core coefficients outside exponents `0,6,12,18,24`.
   - Prefer at least one odd exponent or support gcd 1.
   - Preserve exact local `r=8` as a hard gate.
   - Record metadata for perturbation mode, perturbed exponents,
     support gcd, even-support status, template name, and source seed.
2. Add focused tests proving:
   - pure `r8_quartic_lift` behavior remains unchanged,
   - perturbed mode can emit non-even/support-gcd-1 rows,
   - metadata is written to ledger records,
   - invalid or non-`r=8` perturbations are rejected before queue export.
3. Run a bounded CPU-only probe, for example:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies r8_quartic_lift \
  --seeds 2811,2812,2813,2814 \
  --target_rs 8 \
  --coeff_bound 16 \
  --gensize 24 \
  --pop_size 8 \
  --ntest 4 \
  --gen_batch_size 2 \
  --max_local_search_steps 0 \
  --prime_limit 7 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_r8_perturbed_quartic_followup_20260707
```

4. Gate the new queue before any submission consideration:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_anti_basin_planner.py \
  --candidate_jsonl /tmp/igp24_r8_perturbed_quartic_followup_20260707/*/candidates.jsonl \
  --progress_snapshot_json /tmp/igp24_full_sync_progress_snapshot_20260707.json \
  --output_dir /tmp/igp24_r8_perturbed_quartic_followup_gate_20260707 \
  --target_rs 8 \
  --packet_limit 12 \
  --min_packet_rows 8
```

Submission remains out of scope until a fresh queue has eligible rows, multiple
perturbation modes, mod-p diversity, no accepted-hash duplicates, and a clean
SAIR dry-run reviewed by a human.
