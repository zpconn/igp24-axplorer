# IGP24 Adaptive Frobenius Benchmark

- Created: `2026-07-10T10:18:40.653082+00:00`
- Source commit: `af8061a5cc018c58d85da4de076c230e0c4ddb4b`
- Input rows: `2`
- Evaluated rows: `1`
- Failed rows: `1`
- True-label outside-index rows: `0`
- Exact-label missing rows: `1`
- Indexed containment failures: `0`
- Final valuable-target survival rows: `1`
- Intended target survival rows: `0/0`
- Discriminant sources: `{'discriminant': 1}`
- Max usable primes: `40`
- Index metadata: `{'index_scope': 'complete_degree24_universe', 'indexed_group_count': 25000, 'expected_global_group_count': 25000, 'global_index_complete': True, 'unindexed_label_mass_unknown': False, 'soundness': 'necessary_target_exclusion_only'}`

Evidence uses only primes that do not divide the polynomial discriminant. Compatibility remains necessary target-exclusion evidence only.

## Budget Summary

| budget | rows | reached budget | valuable survival rows | intended target survival rows | containment failures | median indexed survivors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 1 | 1 | 1 | 0 | 0 | 225 |
| 10 | 1 | 1 | 1 | 0 | 0 | 225 |
| 20 | 1 | 1 | 1 | 0 | 0 | 94 |
| 40 | 1 | 1 | 1 | 0 | 0 | 24 |
