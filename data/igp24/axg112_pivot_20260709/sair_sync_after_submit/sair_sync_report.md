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
- Degraded mode summary: 29/29 details recovered; 29/29 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47007

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11369 | 13631 | 25000 |
| 2 | 16 | 9719 | 11702 | 21421 |
| 3 | 8 | 5987 | 17569 | 23556 |
| 4 | 12 | 5914 | 14020 | 19934 |
| 5 | 20 | 5175 | 5677 | 10852 |
| 6 | 0 | 3843 | 20996 | 24839 |
| 7 | 4 | 3351 | 16706 | 20057 |
| 8 | 6 | 470 | 5534 | 6004 |

## Submissions

- Submissions: 29
- Rows: 234
- Pending rows: 1
- Scoreable rows: 233
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"pending": 1, "scoreable": 233}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 1
- Scoreable rows to review: 233
