# IGP24 Current Offline Go/No-Go Report

This report is local/file-only. It does not call SAIR, run exact verifiers, train models, generate candidates, or submit.

## Recommendation

- Live submission recommended now: `False`
- Recommendation: `do_not_submit`
- Blockers: `["adaptive_rows_still_missing_exact_labels", "exact_magma_labels_missing", "explicit_user_live_submission_approval_missing", "fresh_sair_sync_required_immediately_before_live_submission", "score_aware_triage_has_no_submission_grade_rows"]`
- Warnings: `[]`

## Packet

- Selected rows: `1`
- Candidate count considered: `1`
- Best-case packet points: `1.0`
- Expected points status: `unavailable_uncalibrated`
- Possible uncovered pairs: `25`
- Possible low-team pairs: `33`
- Construction families: `{"model_sample_export": 1}`

## Verification

- Reviewed rows: `1`
- Verified exact-label rows: `0`
- Pending exact-label rows: `1`
- Known-submission hash rows: `0`
- Submission-grade rows: `0`
- Exact r status counts: `{"ok": 1}`
- Exact nfdisc status counts: `{"ok": 1}`

## Adaptive Evidence

- Max usable primes: `40`
- Evaluated rows: `1`
- Failed rows: `0`
- Intended target survival: `0/0`
- Valuable target survival rows: `1`

## Architecture Calibration

- Full group index complete: `True`
- Indexed group count: `25000`
- Historical evaluated rows: `233`
- Historical containment failures: `0`
- Historical valuable false-positive rows at 10 primes: `36`
- Chronological replay minimum gate passed: `True`

## Candidates

- Novel candidate count against synced submission history: `1`
- Selected short hashes: `["ee63944ba7bf"]`

| hash | label | r | progress | teams | nfdisc status | known submitted | class | submission-grade |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `ee63944ba7bf` |  | 24 | exact_pair_missing |  | ok | False | exact_result_missing | False |

Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only. Exact labels, fresh progress, known-hash checks, and score-aware gates must all clear before any live packet.
