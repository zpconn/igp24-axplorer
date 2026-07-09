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

- Partial sync: `True`
- Submission state complete: `False`
- Global progress complete: `True`
- Submission index complete: `True`
- Submission detail complete: `False`
- Download complete: `False`
- Degraded mode summary: 20/23 details recovered; 20/20 downloads recovered
- Failing endpoint: `submissions/{id}`
- Labels: 25000
- Remaining signatures: 49354

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11814 | 13186 | 25000 |
| 2 | 16 | 10148 | 11273 | 21421 |
| 3 | 8 | 6291 | 17265 | 23556 |
| 4 | 12 | 6273 | 13661 | 19934 |
| 5 | 20 | 5404 | 5448 | 10852 |
| 6 | 0 | 4094 | 20745 | 24839 |
| 7 | 4 | 3573 | 16484 | 20057 |
| 8 | 6 | 498 | 5506 | 6004 |

## Submissions

- Submissions: 23
- Rows: 174
- Pending rows: 12
- Scoreable rows: 162
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"pending": 12, "scoreable": 162}`

## Decision

- Submission recommended now: `False`
- Reason: partial sync only; submission/scoring state is incomplete
- Wait-for-scoring rows: 12
- Scoreable rows to review: 162
