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
- Degraded mode summary: 25/25 details recovered; 25/25 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47588

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11465 | 13535 | 25000 |
| 2 | 16 | 9799 | 11622 | 21421 |
| 3 | 8 | 6083 | 17473 | 23556 |
| 4 | 12 | 6034 | 13900 | 19934 |
| 5 | 20 | 5191 | 5661 | 10852 |
| 6 | 0 | 3929 | 20910 | 24839 |
| 7 | 4 | 3424 | 16633 | 20057 |
| 8 | 6 | 476 | 5528 | 6004 |

## Submissions

- Submissions: 25
- Rows: 215
- Pending rows: 0
- Scoreable rows: 215
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 215}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 215
