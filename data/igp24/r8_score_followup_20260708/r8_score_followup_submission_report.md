# r8 Score-Followup Submission Report

The previously dry-runed 4-row r8 score-followup packet was submitted to SAIR
after explicit operator approval.

## Submission

- Coefficient file:
  `data/igp24/r8_score_followup_20260708/anti_collapse_gate/anti_basin_candidate_coefficients.txt`
- Submission id: `sub_87b36ed9fbe84cd4aa3c6075c0ce3cd7`
- Submitted at: `2026-07-08T22:20:42Z`
- Queued rows: 4
- Rejected rows: 0
- Submit response:
  `data/igp24/r8_score_followup_20260708/anti_collapse_gate/sair_submit.json`

## First Poll

The first status poll verified all rows immediately:

| row | status | label | r | scoreable | scoring |
| ---: | --- | --- | ---: | --- | --- |
| 1 | accepted | `24T25000` | 8 | false | `discriminant_pending` |
| 2 | accepted | `24T25000` | 8 | false | `discriminant_pending` |
| 3 | accepted | `24T25000` | 8 | false | `discriminant_pending` |
| 4 | accepted | `24T25000` | 8 | false | `discriminant_pending` |

Status artifact:
`data/igp24/r8_score_followup_20260708/anti_collapse_gate/sair_status_poll1.json`

## Feedback Ingest

Feedback artifact:
`data/igp24/r8_score_followup_20260708/anti_collapse_gate/r8_score_followup_sair_accepted_feedback_20260708.json`

Pair-status update:

- New pairs added: 0
- Alternates added: 4
- Already present: 0

This was already a known local pair, so the four rows were appended as
alternates to `24T25000|r=8`; no representative was replaced.

## Post-Submit Sync

Fresh sync directory:
`data/igp24/sair_sync_20260708_r8_followup_after_submit/`

Sync result:

- Complete sync: true
- Degraded mode: false
- Submissions: 22
- Submission rows: 193
- Pending rows: 8
- Scoreable rows: 185
- Unmatched rows: 0
- Remaining signatures: 49,462
- Pending pairs: 4 rows at `24T25000|r=8` and 4 rows at `24T25000|r=20`

## Interpretation

The packet verified cleanly but did not escape the generic `24T25000` basin.
It landed in `24T25000|r=8`, which was already known locally and is a crowded
label family. The useful result is negative steering evidence: the
`24T9993`-sourced `r8_quartic_lift_score_followup` templates e/f plus
`odd_pair_off_core` perturbations should now be treated as exhausted unless a
future generator changes the construction family or adds a much stronger label
discriminator.

Recommendation: do not submit more r8 quartic-in-`x^6` odd off-core variants
from this neighborhood. Pivot to a materially different r8 construction or
return to higher-opportunity target buckets with stronger anti-`24T25000`
constraints.

## Validation

- Compile check passed for `scripts/igp24_anti_basin_feedback.py`,
  `scripts/igp24_sair_api.py`, and `scripts/igp24_sair_sync.py`.
- Focused tests passed:
  `PYTHONPATH=/tmp/igp24_pydeps:. UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uvx pytest -q tests/test_igp24_anti_basin_feedback.py tests/test_igp24_sair_api.py tests/test_igp24_sair_sync.py`
  -> `17 passed in 0.41s`.
- Artifact parse check passed for 16 JSON files and 19 JSONL files with
  25,786 JSONL rows.
- `git diff --check` passed.
- Secret-shaped scan across touched scripts, tests, TODO, README, pair-status,
  and the new r8/post-submit sync artifacts found no matches.
