# IGP24 Adaptive Frobenius Benchmark

- Created: `2026-07-10T06:54:48.754704+00:00`
- Source commit: `fed1e40ab44d74f3525d3fc801b998cfef36ca8b`
- Input rows: `12`
- Evaluated rows: `7`
- Failed rows: `5`
- True-label outside-index rows: `0`
- Exact-label missing rows: `7`
- Indexed containment failures: `0`
- Final valuable-target survival rows: `1`
- Intended target survival rows: `0/7`
- Discriminant sources: `{'discriminant': 7}`
- Max usable primes: `80`
- Index metadata: `{'index_scope': 'complete_degree24_universe', 'indexed_group_count': 25000, 'expected_global_group_count': 25000, 'global_index_complete': True, 'unindexed_label_mass_unknown': False, 'soundness': 'necessary_target_exclusion_only'}`

Evidence uses only primes that do not divide the polynomial discriminant. Compatibility remains necessary target-exclusion evidence only.

## Budget Summary

| budget | rows | reached budget | valuable survival rows | intended target survival rows | containment failures | median indexed survivors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 7 | 7 | 1 | 1 | 0 | 2 |
| 40 | 7 | 7 | 1 | 0 | 0 | 2 |
| 80 | 7 | 7 | 1 | 0 | 0 | 2 |
