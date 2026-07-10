# IGP24 Current Offline Go/No-Go Report

This report is local/file-only. It does not call SAIR, run exact verifiers, train models, generate candidates, or submit.

## Recommendation

- Live submission recommended now: `False`
- Recommendation: `do_not_submit`
- Blockers: `["explicit_user_live_submission_approval_missing", "fresh_sair_sync_required_immediately_before_live_submission", "score_aware_triage_has_no_submission_grade_rows"]`
- Warnings: `["adaptive_exact_label_missing_field_superseded_by_score_aware_triage", "packet_uses_single_construction_family"]`

## Packet

- Selected rows: `4`
- Candidate count considered: `16`
- Best-case packet points: `4.0`
- Expected points status: `unavailable_uncalibrated`
- Possible uncovered pairs: `27`
- Possible low-team pairs: `250`
- Construction families: `{"quartic_in_x6": 4}`

## Verification

- Reviewed rows: `4`
- Verified exact-label rows: `4`
- Pending exact-label rows: `0`
- Known-submission hash rows: `0`
- Submission-grade rows: `0`
- Exact r status counts: `{"ok": 4}`
- Exact nfdisc status counts: `{"ok": 4}`

## Adaptive Evidence

- Max usable primes: `80`
- Evaluated rows: `4`
- Failed rows: `0`
- Intended target survival: `4/4`
- Valuable target survival rows: `4`

## Architecture Calibration

- Full group index complete: `True`
- Indexed group count: `25000`
- Historical evaluated rows: `233`
- Historical containment failures: `0`
- Historical valuable false-positive rows at 10 primes: `36`
- Chronological replay minimum gate passed: `True`

## Candidates

- Novel candidate count against synced submission history: `4`
- Selected short hashes: `["4b6fc1786722", "d4aed028ad97", "caa861f3b409", "5f06b5464de9"]`

| hash | label | r | progress | teams | nfdisc status | known submitted | class | submission-grade |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `4b6fc1786722` | 24T7635 | 8 | allowed_discovered | 13 | ok | False | sair_discovered_pair_not_improved | False |
| `d4aed028ad97` | 24T10010 | 8 | allowed_discovered | 10 | ok | False | sair_discovered_pair_not_improved | False |
| `caa861f3b409` | 24T12493 | 8 | allowed_discovered | 30 | ok | False | sair_discovered_pair_not_improved | False |
| `5f06b5464de9` | 24T9962 | 8 | allowed_discovered | 24 | ok | False | sair_discovered_pair_not_improved | False |

Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only. Exact labels, fresh progress, known-hash checks, and score-aware gates must all clear before any live packet.
