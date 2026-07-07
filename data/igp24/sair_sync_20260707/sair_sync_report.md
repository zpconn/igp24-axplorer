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
- Remaining signatures: 51983

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11998 | 13002 | 25000 |
| 2 | 16 | 10676 | 10745 | 21421 |
| 3 | 8 | 6822 | 16734 | 23556 |
| 4 | 12 | 6740 | 13194 | 19934 |
| 5 | 20 | 5629 | 5223 | 10852 |
| 6 | 0 | 4336 | 20503 | 24839 |
| 7 | 4 | 3848 | 16209 | 20057 |
| 8 | 6 | 555 | 5449 | 6004 |

## Submissions

- Submissions: 18
- Rows: 167
- Pending rows: 32
- Scoreable rows: 135
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"pending": 32, "scoreable": 135}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 32
- Scoreable rows to review: 135
