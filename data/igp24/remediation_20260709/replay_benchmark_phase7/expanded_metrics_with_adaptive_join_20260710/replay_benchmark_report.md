# IGP24 Chronological Replay Benchmark

This benchmark replays historical selected packets against later SAIR feedback and the current remediated packet optimizer. It does not use live APIs or authorize submission.

## Aggregate

- Cases: 7
- Evidence inputs: [{'path': 'data/igp24/remediation_20260709/adaptive_frobenius_phase5/scoreable_rows_234x10primes_full_index_poly_disc_patterns_20260709/adaptive_frobenius_benchmark_rows.jsonl', 'exists': True, 'rows_loaded': 233}]
- Old accepted rows: 41
- Old crowded-collapse rate: 1.0
- Old distinct verified pairs: 7
- Estimated old points per 100 submitted rows: 3.79846e-07
- Major collapse cases: 7
- Major collapse cases stopped/downranked by remediated replay: 7
- Remediated source unique-decode rate: 1.0
- Remediated source target-r match rate: 0.885714
- Remediated source compatibility-evidence rate: 1.0
- Joined adaptive-evidence rows: 41
- Remediated source valuable-survival rate: 0.0
- True-label containment evaluated rows: 41
- True-label containment rate: 1.0
- True-label containment missing-evidence rows: 0
- Phase 7 minimum gate passed: `True`

## Cases

| case | submitted | accepted | labels | pairs | collapse rate | duplicate pair rate | old points/100 | source unique | compat rows | containment | remediated selected | stop/downrank |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| `sub_87b36ed9fbe84cd4aa3c6075c0ce3cd7` | 2026-07-08T22:20:42Z | 4 | {"24T25000": 4} | {"24T25000|r=8": 4} | 1.0 | 0.75 | 1.45e-09 | 1.0 | 4 | 4/4 | 0 | True |
| `sub_55fba0a7253d4a72b8ab7a6e80d5cede` | 2026-07-09T14:26:00Z | 11 | {"24T25000": 11} | {"24T25000|r=24": 11} | 1.0 | 0.909091 | 4.71964e-07 | 1.0 | 11 | 11/11 | 0 | True |
| `sub_11fc452b521044619796f738cc4b22c3` | 2026-07-09T16:06:17Z | 7 | {"24T25000": 7} | {"24T25000|r=12": 3, "24T25000|r=20": 2, "24T25000|r=24": 2} | 1.0 | 0.571429 | 1.092e-06 | 1.0 | 7 | 7/7 | 0 | True |
| `sub_cdd210208d4e4c0b9b692c1389458c2c` | None | 6 | {"24T25000": 6} | {"24T25000|r=8": 6} | 1.0 | 0.833333 | 9.67e-10 | 1.0 | 6 | 6/6 | 0 | True |
| `sub_2f897a63341b46b382139d6d8de88792` | 2026-07-09T18:40:58Z | 3 | {"24T25000": 3} | {"24T25000|r=16": 2, "24T25000|r=20": 1} | 1.0 | 0.333333 | 9.06833e-07 | 1.0 | 3 | 3/3 | 0 | True |
| `sub_e558f7c55b3d45a0a926c5a9c6d05d75` | 2026-07-09T19:45:12Z | 4 | {"24T25000": 4} | {"24T25000|r=4": 3, "24T25000|r=8": 1} | 1.0 | 0.5 | 1.45e-09 | 1.0 | 4 | 4/4 | 0 | True |
| `sub_51983ad56663418187e9adc3142c1162` | 2026-07-09T20:18:19Z | 6 | {"24T24979": 6} | {"24T24979|r=12": 6} | 1.0 | 0.833333 | 3.3e-11 | 1.0 | 6 | 6/6 | 0 | True |

## Interpretation

A pass here is not leaderboard progress. It is evidence that the remediated stack no longer approves the historical collapse packets that produced crowded-label outcomes such as `24T25000` and `24T24979`.
Joined adaptive evidence is used only for replay calibration metrics such as true-label containment and valuable-survival rate; it does not fabricate optimizer-compatible pair lists for old packets.
