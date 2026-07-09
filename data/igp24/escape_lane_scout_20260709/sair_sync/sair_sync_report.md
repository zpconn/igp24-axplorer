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
- Degraded mode summary: 24/24 details recovered; 24/24 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47834

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11523 | 13477 | 25000 |
| 2 | 16 | 9820 | 11601 | 21421 |
| 3 | 8 | 6112 | 17444 | 23556 |
| 4 | 12 | 6093 | 13841 | 19934 |
| 5 | 20 | 5201 | 5651 | 10852 |
| 6 | 0 | 3956 | 20883 | 24839 |
| 7 | 4 | 3448 | 16609 | 20057 |
| 8 | 6 | 482 | 5522 | 6004 |

## Submissions

- Submissions: 24
- Rows: 208
- Pending rows: 0
- Scoreable rows: 208
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 208}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 208
