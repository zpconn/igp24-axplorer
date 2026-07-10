# IGP24 Current Offline Go/No-Go Report

This report is local/file-only. It does not call SAIR, run exact verifiers, train models, generate candidates, or submit.

## Recommendation

- Live submission recommended now: `False`
- Recommendation: `do_not_submit`
- Blockers: `["explicit_user_live_submission_approval_missing", "no_packet_rows_selected", "score_aware_triage_has_no_submission_grade_rows"]`
- Warnings: `["adaptive_exact_label_missing_field_superseded_by_score_aware_triage"]`

## Packet

- Selected rows: `0`
- Candidate count considered: `2`
- Best-case packet points: `0`
- Expected points status: `unavailable_uncalibrated`
- Exact submission-grade estimated points: `None`
- Exact submission-grade maximum points: `None`
- Possible uncovered pairs: `0`
- Possible low-team pairs: `0`
- Construction families: `{}`

## Verification

- Reviewed rows: `2`
- Verified exact-label rows: `2`
- Pending exact-label rows: `0`
- Known-submission hash rows: `0`
- Submission-grade rows: `0`
- Exact r status counts: `{"ok": 2}`
- Exact nfdisc status counts: `{"ok": 2}`

## Adaptive Evidence

- Max usable primes: `40`
- Evaluated rows: `2`
- Failed rows: `0`
- Intended target survival: `0/0`
- Valuable target survival rows: `2`

## Architecture Calibration

- Full group index complete: `True`
- Indexed group count: `25000`
- Historical evaluated rows: `233`
- Historical containment failures: `0`
- Historical valuable false-positive rows at 10 primes: `36`
- Chronological replay minimum gate passed: `True`

## SAIR Sync

- Sync artifact provided: `True`
- Sync status: `fresh_complete`
- Created at: `2026-07-10T09:13:15.943767+00:00`
- Age hours: `1.577628`
- Full submission state complete: `True`
- Pending rows: `0`
- Scoreable rows: `234`

## Exact Score

- Exact submission-grade rows: `0`
- Estimated official points: `None`
- Maximum possible points: `None`
- Basis: `None`

## Candidates

- Novel candidate count against synced submission history: `2`
- Selected short hashes: `["425c30453d4a", "8f32835b516d"]`

| hash | label | r | progress | teams | nfdisc status | known submitted | class | submission-grade |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `425c30453d4a` | 24T9993 | 8 | allowed_discovered | 12 | ok | False | accepted_pair_duplicate | False |
| `8f32835b516d` | 24T23883 | 8 | allowed_discovered | 47 | ok | False | sair_discovered_pair_not_improved | False |

Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only. Exact labels, fresh progress, known-hash checks, and score-aware gates must all clear before any live packet.
