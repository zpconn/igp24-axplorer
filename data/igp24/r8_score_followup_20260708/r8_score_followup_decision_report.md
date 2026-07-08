# IGP24 r8 Score-Followup Decision Report

This pass followed up the strongest visible local score signal,
`24T9993|r=8`, without starting a larger GPU/model run and without live
SAIR submission.

## Fresh SAIR State

- Sync directory: `data/igp24/sair_sync_20260708_r8_followup/`
- Sync status: complete, not partial.
- Degraded mode summary: `21/21 details recovered; 21/21 downloads recovered`.
- Labels synced: 25,000.
- Remaining signatures: 49,464.
- Submission rows: 189 total, 185 scoreable, 4 pending.
- Pending pair overlay: 4 pending rows, all `24T25000|r=20`.
- Top remaining buckets: `r=24` has 11,818 remaining, `r=16` has 10,160,
  `r=8` has 6,313, `r=12` has 6,300, and `r=20` has 5,408.

The pending `24T25000|r=20` overlay did not collide with the selected r8 rows.

## Lane Definition

The source signal was `24T9993|r=8`, with user-reported visible points
`0.0019` and 10 solved teams. Earlier pure `r8_quartic_lift` rows were
exhausted because they overlapped already submitted pure-template rows. This
lane therefore perturbed the two `24T9993`-source quartic templates:

- `four_positive_fibers_e`: `[1,-8,16,-9,1]`
- `four_positive_fibers_f`: `[1,-9,16,-8,1]`

Every accepted row preserved explicit provenance fields for source, family,
generation strategy, template family, basin fingerprint, perturbation mode,
support pattern, and mod-p signature.

## Generation Results

Three bounded local generation runs were used:

| run | seed | trials | accepted | template mix | mode |
| --- | ---: | ---: | ---: | --- | --- |
| `generation` | 3201 | 240 | 16 | e=7, f=9 | `odd_pair_off_core` |
| `generation_single` | 3211 | 180 | 0 | none | none |
| `generation_triple` | 3221 | 220 | 18 | e=11, f=7 | `odd_pair_off_core` |

The single-term run found no exact local r8 rows in this bounded attempt. The
two-term and mixed up-to-three-term runs produced exact local r8 rows, all in
the `odd_pair_off_core` mode.

The combined lane accepted 32 unique exact local candidates after deduplicating
34 generated rows and rejecting 2 duplicates. The combined pool contains both
source templates, 32 basin fingerprints, and 32 locally valid rows.

## Local Exact Filters

The lane kept only rows with:

- 25 integer coefficients in exported SAIR order.
- Nonzero constant term and monic leading coefficient.
- Coefficient gcd 1.
- Exact local `r=8`.
- Irreducible and squarefree local checks.
- A unique canonical hash and coefficient line.
- Complete required provenance.

Rejected rows were retained with reasons in the generation and lane artifacts.

## Anti-Collapse Gate

The anti-collapse planner used the fresh sync overlay plus the accepted
feedback/basin profile. It scored 32 candidates, found 32 eligible, and
selected 4 rows. The selected packet passed all hard gates:

- `recommended_for_sair_packet=true`
- status: `reviewed_packet_ready_for_dry_run`
- selected rows: 4
- risk count: 0
- selected source count: 4 `lane_generate:r8_score_followup` rows
- template families: 3 rows from template e and 1 row from template f
- basin fingerprints: 4 distinct
- mod-p signatures: 4 distinct
- selected r values: `[8]`
- pending high-label basin collisions: none

Selected short hashes:

- `fab80a856ba7`
- `fa9b5c0d83b8`
- `ee2a23e49c9f`
- `ed07d10ea581`

The selected coefficient file is:
`data/igp24/r8_score_followup_20260708/anti_collapse_gate/anti_basin_candidate_coefficients.txt`

## SAIR Dry Run

Dry-run command:

```bash
PYTHONPATH=/tmp/igp24_pydeps:. python3 scripts/igp24_sair_api.py submit \
  --coefficients_txt data/igp24/r8_score_followup_20260708/anti_collapse_gate/anti_basin_candidate_coefficients.txt \
  --description "r8 score-followup 24T9993 dry-run 20260708" \
  --output_json data/igp24/r8_score_followup_20260708/anti_collapse_gate/sair_dry_run.json
```

Dry-run result:

- `ok=true`
- `dry_run=true`
- `polynomial_count=4`
- `would_post=/api/public/v1/competitions/igp24/submissions`

Manual coefficient validation confirmed all 4 rows have exactly 25 integer
coefficients, nonzero constant coefficient, and leading coefficient 1.

## Decision

This pass produced a dry-run-only packet ready for manual review. No live SAIR
submission was made.

The packet is materially different from the recent `24T25000|r=20` collapse:
it targets `r=8`, uses `24T9993`-source templates e/f, has odd off-core support
with support gcd 1, has four distinct basin fingerprints, and has four
distinct sampled mod-p signatures. The main residual risk is that all selected
rows still use one perturbation mode, `odd_pair_off_core`; this was accepted
for this lane because the bounded single-term variant produced zero exact r8
survivors and the template/basin/mod-p diversity gates passed.

Postscript: after explicit operator approval, this packet was submitted as
`sub_87b36ed9fbe84cd4aa3c6075c0ce3cd7`. All 4 rows were accepted as
`24T25000|r=8` with discriminants pending. See
`data/igp24/r8_score_followup_20260708/r8_score_followup_submission_report.md`.

## Validation

- Compile check passed for `scripts/igp24_anti_basin_planner.py`,
  `scripts/igp24_r8_score_followup_generate.py`,
  `scripts/igp24_r8_score_followup_lane.py`, and
  `scripts/igp24_sair_api.py`.
- Focused tests passed:
  `PYTHONPATH=/tmp/igp24_pydeps:. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uvx pytest -q tests/test_igp24_anti_basin_planner.py tests/test_igp24_r8_score_followup_lane.py tests/test_igp24_sair_api.py`
  -> `21 passed in 0.87s`.
- Artifact parse check passed for 12 JSON files and 19 JSONL files with
  25,799 JSONL rows.
- `git diff --check` passed.
- Secret-shaped scan across touched scripts, tests, TODO, README, and the new
  r8/sync artifacts found no matches.
