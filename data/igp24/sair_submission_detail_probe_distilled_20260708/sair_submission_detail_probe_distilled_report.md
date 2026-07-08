# SAIR Submission Detail Probe Distilled Summary

This is a compact record of a manual read-only submission-detail probe run during SAIR detail-endpoint instability. Raw per-submission API bodies remain in `/tmp` and are not committed here.

## Totals

- Requested submissions: 20
- Recovered submissions: 19
- Failed submissions: 1
- Recovered verified rows: 173
- Status counts: `{"accepted": 173}`
- Scoring counts: `{"pending": 18, "scoreable": 155}`

## Failed Read

- `sub_ef0fdc26a49c42ae9b77422b6c521d96`: status `503`, code `IGP24_SERVICE_UNAVAILABLE`, message `The IGP24 competition service is temporarily unavailable. Please try again shortly.`

## Pending Pairs

| pair | rows |
| --- | ---: |
| `24T25000|r=8` | 9 |
| `24T25000|r=20` | 8 |
| `24T24979|r=8` | 1 |

## Top Pair Counts

| pair | rows |
| --- | ---: |
| `24T25000|r=4` | 23 |
| `24T25000|r=20` | 18 |
| `24T25000|r=16` | 17 |
| `24T24932|r=24` | 16 |
| `24T25000|r=24` | 16 |
| `24T24979|r=12` | 15 |
| `24T24979|r=16` | 13 |
| `24T24651|r=24` | 9 |
| `24T25000|r=8` | 9 |
| `24T24651|r=12` | 8 |
| `24T24932|r=12` | 4 |
| `24T24970|r=12` | 3 |

## Submission Rows

| submission | verified | scoring | pairs |
| --- | ---: | --- | --- |
| `sub_2a6f8c6e61a045ad886c8d37041327f2` | 5 | `{"scoreable": 5}` | 24T24648|r=4:1, 24T24759|r=4:1, 24T24970|r=4:1, 24T24979|r=4:1, 24T9683|r=4:1 |
| `sub_743fdd6e963c41498817f10ebdd39b5d` | 1 | `{"scoreable": 1}` | 24T25000|r=4:1 |
| `sub_76742af07fb7489c92232b3bc22bbeb1` | 24 | `{"scoreable": 24}` | 24T24979|r=4:2, 24T25000|r=4:22 |
| `sub_11f2ec82cabc4ae98f807d3df922a199` | 3 | `{"scoreable": 3}` | 24T21844|r=4:1, 24T24970|r=4:2 |
| `sub_5f42a87ac9bf484eaf2eafdcfe76808d` | 6 | `{"scoreable": 6}` | 24T1310|r=8:2, 24T657|r=8:1, 24T661|r=8:1, 24T9993|r=8:2 |
| `sub_02ecc2457d124584b8325b83608a2e9c` | 8 | `{"scoreable": 8}` | 24T24979|r=16:8 |
| `sub_8ac1fdf9e9f64ec3a9bb4ed3669be6e8` | 10 | `{"scoreable": 10}` | 24T24979|r=16:5, 24T25000|r=16:5 |
| `sub_5975e0ab848b4ab7b18fd58768b10954` | 12 | `{"scoreable": 12}` | 24T25000|r=16:12 |
| `sub_5ae80eef209f4882a28854adf6bdd4d2` | 8 | `{"scoreable": 8}` | 24T25000|r=24:8 |
| `sub_88f73b4be4cb4ff08a8a16fa192bcad5` | 10 | `{"scoreable": 10}` | 24T25000|r=20:10 |
| `sub_5f372f76678d4e15b0e769b8b64ac876` | 10 | `{"scoreable": 10}` | 24T22770|r=12:2, 24T24970|r=12:1, 24T24979|r=12:7 |
| `sub_40b8ff2598d24bb383c86f9e4dbb9edf` | 10 | `{"scoreable": 10}` | 24T24970|r=12:2, 24T24979|r=12:8 |
| `sub_a1fa1196ad8b48b88a7fa4c31f153d0c` | 10 | `{"scoreable": 10}` | 24T23883|r=12:2, 24T24651|r=12:8 |
| `sub_54bf941fa9a64d7984a51cfe52ce049e` | 10 | `{"scoreable": 10}` | 24T23883|r=24:1, 24T24651|r=24:9 |
| `sub_d7bc66004b0c4db2a89071c651c7583e` | 8 | `{"scoreable": 8}` | 24T25000|r=24:8 |
| `sub_25c17affdf3c4505a8f10cfda2d94217` | 8 | `{"scoreable": 8}` | 24T24932|r=24:8 |
| `sub_442d9ff1c6974974ab38df65e70dddf0` | 12 | `{"scoreable": 12}` | 24T24932|r=12:4, 24T24932|r=24:8 |
| `sub_4622b4196ca64a9d91441cf5184acafe` | 10 | `{"pending": 10}` | 24T24979|r=8:1, 24T25000|r=8:9 |
| `sub_3557a403ea664b2f97ac059f9083b206` | 8 | `{"pending": 8}` | 24T25000|r=20:8 |

## Use

Use this as outage-era audit/provenance only. It is not a live submission gate because one detail fetch failed and the artifact predates the newer pending-aware sync status fields.
