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
- Degraded mode summary: 26/26 details recovered; 26/26 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47124

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11412 | 13588 | 25000 |
| 2 | 16 | 9742 | 11679 | 21421 |
| 3 | 8 | 5997 | 17559 | 23556 |
| 4 | 12 | 5934 | 14000 | 19934 |
| 5 | 20 | 5184 | 5668 | 10852 |
| 6 | 0 | 3847 | 20992 | 24839 |
| 7 | 4 | 3357 | 16700 | 20057 |
| 8 | 6 | 471 | 5533 | 6004 |

## Submissions

- Submissions: 26
- Rows: 221
- Pending rows: 0
- Scoreable rows: 221
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 221}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 221
