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
- Degraded mode summary: 27/27 details recovered; 27/27 downloads recovered
- Failing endpoint: `None`
- Labels: 25000
- Remaining signatures: 47077

| rank | r | remaining | discovered | allowed |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 24 | 11391 | 13609 | 25000 |
| 2 | 16 | 9735 | 11686 | 21421 |
| 3 | 8 | 5995 | 17561 | 23556 |
| 4 | 12 | 5925 | 14009 | 19934 |
| 5 | 20 | 5182 | 5670 | 10852 |
| 6 | 0 | 3843 | 20996 | 24839 |
| 7 | 4 | 3355 | 16702 | 20057 |
| 8 | 6 | 471 | 5533 | 6004 |

## Submissions

- Submissions: 27
- Rows: 224
- Pending rows: 0
- Scoreable rows: 224
- Failed rows: 0
- Unmatched rows: 0
- Status counts: `{"scoreable": 224}`

## Decision

- Submission recommended now: `False`
- Reason: sync only; no generated queue passed score-aware and anti-basin submission gates
- Wait-for-scoring rows: 0
- Scoreable rows to review: 224
