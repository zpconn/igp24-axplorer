# IGP24 Current Offline Go/No-Go Report

This report is local/file-only. It does not call SAIR, run exact verifiers, train models, generate candidates, or submit.

## Recommendation

- Live submission recommended now: `False`
- Recommendation: `do_not_submit`
- Blockers: `["explicit_user_live_submission_approval_missing"]`
- Warnings: `["adaptive_exact_label_missing_field_superseded_by_score_aware_triage"]`

## Packet

- Selected rows: `1`
- Candidate count considered: `1`
- Best-case packet points: `1.0`
- Expected points status: `unavailable_uncalibrated`
- Exact submission-grade estimated points: `0.015625`
- Exact submission-grade maximum points: `0.015625`
- Possible uncovered pairs: `25`
- Possible low-team pairs: `32`
- Construction families: `{"model_sample_export": 1}`

## Verification

- Reviewed rows: `1`
- Verified exact-label rows: `1`
- Pending exact-label rows: `0`
- Known-submission hash rows: `0`
- Submission-grade rows: `1`
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

## SAIR Sync

- Sync artifact provided: `True`
- Sync status: `fresh_complete`
- Created at: `2026-07-10T09:13:15.943767+00:00`
- Age hours: `0.250416`
- Full submission state complete: `True`
- Pending rows: `0`
- Scoreable rows: `234`

## Exact Score

- Exact submission-grade rows: `1`
- Estimated official points: `0.015625`
- Maximum possible points: `0.015625`
- Basis: `exact_verified_pairs_official_score_economics`

## Candidates

- Novel candidate count against synced submission history: `1`
- Selected short hashes: `["ee63944ba7bf"]`

| hash | label | r | progress | teams | nfdisc status | known submitted | class | submission-grade |
| --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `ee63944ba7bf` | 24T13879 | 24 | allowed_discovered | 7 | ok | False | sair_discovered_pair_material_discriminant_improvement | True |

Compatibility and adaptive Frobenius evidence remain necessary target-exclusion evidence only. Exact labels, fresh progress, known-hash checks, and score-aware gates must all clear before any live packet.
