# IGP24 SAIR Sync

## API Coverage

- `GET /api/public/v1/competitions/{competitionId}`
- `GET /api/public/v1/competitions/{competitionId}/me`
- `GET /api/public/v1/competitions/igp24/labels/progress`
- `GET /api/public/v1/competitions/{competitionId}/submissions/me`
- `GET /api/public/v1/competitions/{competitionId}/submissions/{submissionId}`
- `POST /api/public/v1/competitions/{competitionId}/submissions remains dry-run/explicit only`

## Progress

- Partial sync: `True`
- Submission state complete: `False`
- Failing endpoint: `submissions/{id}`
- Labels: 25000
- Remaining signatures: 51009

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11935 | 13065 | 25000 |
| 2 | 16 | 10447 | 10974 | 21421 |
| 3 | 8 | 6656 | 16900 | 23556 |
| 4 | 12 | 6538 | 13396 | 19934 |
| 5 | 20 | 5519 | 5333 | 10852 |
| 6 | 0 | 4282 | 20557 | 24839 |
| 7 | 4 | 3755 | 16302 | 20057 |
| 8 | 6 | 549 | 5455 | 6004 |

## Submissions

- Submissions: 20
- Rows: 78
- Pending rows: 18
- Scoreable rows: 60
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"pending": 18, "scoreable": 60}`

## Decision

- Submission recommended now: `False`
- Reason: partial sync only; submission/scoring state is incomplete
- Wait-for-scoring rows: 18
- Scoreable rows to review: 60
