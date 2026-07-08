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
- Degraded mode summary: 22/22 details recovered; 22/22 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 49462

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11817 | 13183 | 25000 |
| 2 | 16 | 10159 | 11262 | 21421 |
| 3 | 8 | 6313 | 17243 | 23556 |
| 4 | 12 | 6300 | 13634 | 19934 |
| 5 | 20 | 5408 | 5444 | 10852 |
| 6 | 0 | 4103 | 20736 | 24839 |
| 7 | 4 | 3593 | 16464 | 20057 |
| 8 | 6 | 504 | 5500 | 6004 |

## Submissions

- Submissions: 22
- Rows: 193
- Pending rows: 8
- Scoreable rows: 185
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"pending": 8, "scoreable": 185}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 8
- Scoreable rows to review: 185
