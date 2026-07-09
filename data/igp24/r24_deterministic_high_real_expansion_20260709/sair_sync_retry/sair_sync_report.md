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
- Degraded mode summary: 23/23 details recovered; 23/23 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47891

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11535 | 13465 | 25000 |
| 2 | 16 | 9826 | 11595 | 21421 |
| 3 | 8 | 6119 | 17437 | 23556 |
| 4 | 12 | 6105 | 13829 | 19934 |
| 5 | 20 | 5209 | 5643 | 10852 |
| 6 | 0 | 3963 | 20876 | 24839 |
| 7 | 4 | 3452 | 16605 | 20057 |
| 8 | 6 | 482 | 5522 | 6004 |

## Submissions

- Submissions: 23
- Rows: 197
- Pending rows: 0
- Scoreable rows: 197
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 197}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 197
