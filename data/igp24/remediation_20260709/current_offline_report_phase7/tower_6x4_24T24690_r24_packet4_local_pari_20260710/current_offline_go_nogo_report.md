# IGP24 Current Offline Go/No-Go Report

This report is local/file-only. It does not call SAIR, run exact verifiers, train models, generate candidates, or submit.

## Recommendation

- Live submission recommended now: `False`
- Recommendation: `do_not_submit`
- Blockers: `["adaptive_rows_still_missing_exact_labels", "exact_magma_labels_missing", "explicit_user_live_submission_approval_missing", "fresh_sair_sync_required_immediately_before_live_submission", "intended_target_ruled_out_by_adaptive_evidence", "score_aware_triage_has_no_submission_grade_rows"]`
- Warnings: `["packet_uses_single_construction_family"]`

## Packet

- Selected rows: `4`
- Candidate count considered: `16`
- Best-case packet points: `4.0`
- Expected points status: `unavailable_uncalibrated`
- Possible uncovered pairs: `28`
- Possible low-team pairs: `37`
- Construction families: `{"tower_6x4": 4}`

## Verification

- Reviewed rows: `4`
- Verified exact-label rows: `0`
- Pending exact-label rows: `4`
- Known-submission hash rows: `0`
- Submission-grade rows: `0`
- Exact r status counts: `{"ok": 4}`
- Exact nfdisc status counts: `{"ok": 4}`

## Adaptive Evidence

- Max usable primes: `40`
- Evaluated rows: `16`
- Failed rows: `0`
- Intended target survival: `0/16`
- Valuable target survival rows: `14`

## Architecture Calibration

- Full group index complete: `True`
- Indexed group count: `25000`
- Historical evaluated rows: `233`
- Historical containment failures: `0`
- Historical valuable false-positive rows at 10 primes: `36`
- Chronological replay minimum gate passed: `True`

## Candidates

- Novel candidate count against synced submission history: `4`
- Selected short hashes: `["9da7a6f4dac4", "16a66dd8583f", "093d4ca1da4c", "b03eb2c2a86a"]`

| hash | label | r | progress | teams | nfdisc status | known submitted | class | submission-grade |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `9da7a6f4dac4` |  | 24 | exact_pair_missing |  | ok | False | exact_result_missing | False |
| `16a66dd8583f` |  | 24 | exact_pair_missing |  | ok | False | exact_result_missing | False |
| `093d4ca1da4c` |  | 24 | exact_pair_missing |  | ok | False | exact_result_missing | False |
| `b03eb2c2a86a` |  | 24 | exact_pair_missing |  | ok | False | exact_result_missing | False |

Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only. Exact labels, fresh progress, known-hash checks, and score-aware gates must all clear before any live packet.
