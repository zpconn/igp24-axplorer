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
- Remaining signatures: 46499

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11300 | 13700 | 25000 |
| 2 | 16 | 9659 | 11762 | 21421 |
| 3 | 8 | 5888 | 17668 | 23556 |
| 4 | 12 | 5832 | 14102 | 19934 |
| 5 | 20 | 5154 | 5698 | 10852 |
| 6 | 0 | 3779 | 21060 | 24839 |
| 7 | 4 | 3269 | 16788 | 20057 |
| 8 | 6 | 460 | 5544 | 6004 |

## Submissions

- Submissions: 29
- Rows: 234
- Pending rows: 0
- Scoreable rows: 234
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 234}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 234
