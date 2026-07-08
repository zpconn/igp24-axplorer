# IGP24 SAIR Sync

## API Coverage

- `GET /api/public/v1/competitions/{competitionId}`
- `GET /api/public/v1/competitions/{competitionId}/me`
- `GET /api/public/v1/competitions/igp24/labels/progress`
- `GET /api/public/v1/competitions/{competitionId}/submissions/me`
- `GET /api/public/v1/competitions/{competitionId}/submissions/{submissionId}`
- `GET /api/public/v1/competitions/{competitionId}/submissions/{submissionId}/download`
- `POST /api/public/v1/competitions/{competitionId}/submissions remains dry-run/explicit only`

## Progress

- Partial sync: `False`
- Submission state complete: `True`
- Global progress complete: `True`
- Submission index complete: `True`
- Submission detail complete: `True`
- Download complete: `True`
- Degraded mode summary: 20/20 details recovered; 20/20 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 49469

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11820 | 13180 | 25000 |
| 2 | 16 | 10162 | 11259 | 21421 |
| 3 | 8 | 6313 | 17243 | 23556 |
| 4 | 12 | 6300 | 13634 | 19934 |
| 5 | 20 | 5409 | 5443 | 10852 |
| 6 | 0 | 4103 | 20736 | 24839 |
| 7 | 4 | 3593 | 16464 | 20057 |
| 8 | 6 | 504 | 5500 | 6004 |

## Submissions

- Submissions: 20
- Rows: 185
- Pending rows: 0
- Scoreable rows: 185
- Failed rows: 0
- Unmatched rows: 21
- Status counts: `{"scoreable": 185}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 185
