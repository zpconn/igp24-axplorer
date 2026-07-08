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
- Degraded mode summary: 21/21 details recovered; 21/21 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 49464

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11818 | 13182 | 25000 |
| 2 | 16 | 10160 | 11261 | 21421 |
| 3 | 8 | 6313 | 17243 | 23556 |
| 4 | 12 | 6300 | 13634 | 19934 |
| 5 | 20 | 5408 | 5444 | 10852 |
| 6 | 0 | 4103 | 20736 | 24839 |
| 7 | 4 | 3593 | 16464 | 20057 |
| 8 | 6 | 504 | 5500 | 6004 |

## Submissions

- Submissions: 21
- Rows: 189
- Pending rows: 4
- Scoreable rows: 185
- Failed rows: 0
- Unmatched rows: 21
- Status counts: `{"pending": 4, "scoreable": 185}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 4
- Scoreable rows to review: 185
