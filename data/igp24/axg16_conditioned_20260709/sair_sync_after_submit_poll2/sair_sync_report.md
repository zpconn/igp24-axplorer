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
- Degraded mode summary: 25/25 details recovered; 25/25 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47721

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11478 | 13522 | 25000 |
| 2 | 16 | 9803 | 11618 | 21421 |
| 3 | 8 | 6106 | 17450 | 23556 |
| 4 | 12 | 6073 | 13861 | 19934 |
| 5 | 20 | 5193 | 5659 | 10852 |
| 6 | 0 | 3951 | 20888 | 24839 |
| 7 | 4 | 3442 | 16615 | 20057 |
| 8 | 6 | 482 | 5522 | 6004 |

## Submissions

- Submissions: 25
- Rows: 215
- Pending rows: 0
- Scoreable rows: 215
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 215}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 215
