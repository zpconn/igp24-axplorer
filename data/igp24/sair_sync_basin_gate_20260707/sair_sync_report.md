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
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 51378

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11982 | 13018 | 25000 |
| 2 | 16 | 10534 | 10887 | 21421 |
| 3 | 8 | 6706 | 16850 | 23556 |
| 4 | 12 | 6586 | 13348 | 19934 |
| 5 | 20 | 5574 | 5278 | 10852 |
| 6 | 0 | 4315 | 20524 | 24839 |
| 7 | 4 | 3790 | 16267 | 20057 |
| 8 | 6 | 550 | 5454 | 6004 |

## Submissions

- Submissions: 20
- Rows: 185
- Pending rows: 50
- Scoreable rows: 135
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"pending": 50, "scoreable": 135}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 50
- Scoreable rows to review: 135
