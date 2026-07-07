# SAIR Live Target Plan

## Snapshot

- Pages: 5
- Labels: 25000
- Published: True
- First generatedAt: `2026-07-07T01:20:36Z`
- Last generatedAt: `2026-07-07T01:20:43Z`
- Remaining signatures: 52335

## Coverage By r

| r | allowed | discovered | remaining | discovered % | remaining % |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 24839 | 20475 | 4364 | 82.43 | 17.57 |
| 2 | 5760 | 5593 | 167 | 97.10 | 2.90 |
| 4 | 20057 | 16169 | 3888 | 80.62 | 19.38 |
| 6 | 6004 | 5446 | 558 | 90.71 | 9.29 |
| 8 | 23556 | 16675 | 6881 | 70.79 | 29.21 |
| 10 | 3288 | 2864 | 424 | 87.10 | 12.90 |
| 12 | 19934 | 13142 | 6792 | 65.93 | 34.07 |
| 14 | 2581 | 2177 | 404 | 84.35 | 15.65 |
| 16 | 21421 | 10681 | 10740 | 49.86 | 50.14 |
| 18 | 2168 | 1767 | 401 | 81.50 | 18.50 |
| 20 | 10852 | 5180 | 5672 | 47.73 | 52.27 |
| 22 | 376 | 376 | 0 | 100.00 | 0.00 |
| 24 | 25000 | 12956 | 12044 | 51.82 | 48.18 |

## Top Remaining Targets

| rank | pair | label teams | signature teams | remaining signatures on label | score |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 24T18897|r=24 | 0 | 0 | 12 | 1056.00 |
| 2 | 24T19906|r=24 | 0 | 0 | 12 | 1056.00 |
| 3 | 24T22306|r=24 | 0 | 0 | 12 | 1056.00 |
| 4 | 24T22631|r=24 | 0 | 0 | 12 | 1056.00 |
| 5 | 24T22667|r=24 | 0 | 0 | 12 | 1056.00 |
| 6 | 24T23413|r=24 | 0 | 0 | 12 | 1056.00 |
| 7 | 24T24093|r=24 | 0 | 0 | 12 | 1056.00 |
| 8 | 24T24768|r=24 | 0 | 0 | 12 | 1056.00 |
| 9 | 24T7872|r=24 | 0 | 0 | 11 | 1054.00 |
| 10 | 24T12889|r=24 | 0 | 0 | 11 | 1054.00 |
| 11 | 24T12891|r=24 | 0 | 0 | 11 | 1054.00 |
| 12 | 24T15037|r=24 | 0 | 0 | 11 | 1054.00 |
| 13 | 24T15038|r=24 | 0 | 0 | 11 | 1054.00 |
| 14 | 24T15069|r=24 | 0 | 0 | 11 | 1054.00 |
| 15 | 24T15083|r=24 | 0 | 0 | 11 | 1054.00 |
| 16 | 24T15092|r=24 | 0 | 0 | 11 | 1054.00 |
| 17 | 24T18559|r=24 | 0 | 0 | 11 | 1054.00 |
| 18 | 24T21404|r=24 | 0 | 0 | 11 | 1054.00 |
| 19 | 24T21405|r=24 | 0 | 0 | 11 | 1054.00 |
| 20 | 24T22567|r=24 | 0 | 0 | 11 | 1054.00 |
| 21 | 24T22735|r=24 | 0 | 0 | 11 | 1054.00 |
| 22 | 24T22736|r=24 | 0 | 0 | 11 | 1054.00 |
| 23 | 24T23412|r=24 | 0 | 0 | 11 | 1054.00 |
| 24 | 24T23718|r=24 | 0 | 0 | 11 | 1054.00 |
| 25 | 24T23719|r=24 | 0 | 0 | 11 | 1054.00 |

## Decision

- Recommended lane: target-conditioned high-real-root search, starting with r=24/r=16/r=20 labels that have no credited teams
- GPU training now: False
- Automatic submission now: False
- Caveat: The API identifies exact remaining (24Tt, r) signatures, but the current local generators do not directly condition on 24T label. New queues should therefore be small, validated, and treated as exploratory exact-label probes rather than guaranteed target hits.
