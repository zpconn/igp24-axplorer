# IGP24 Adaptive Frobenius Benchmark

- Created: `2026-07-10T02:33:15.131773+00:00`
- Source commit: `713f314523419e242ed7ca47a6caec1da963dd60`
- Input rows: `234`
- Evaluated rows: `233`
- Failed rows: `1`
- True-label outside-index rows: `0`
- Indexed containment failures: `0`
- Final valuable-target survival rows: `36`
- Discriminant sources: `{'computed_sympy_polynomial_discriminant': 233}`
- Max usable primes: `10`
- Index metadata: `{'index_scope': 'complete_degree24_universe', 'indexed_group_count': 25000, 'expected_global_group_count': 25000, 'global_index_complete': True, 'unindexed_label_mass_unknown': False, 'soundness': 'necessary_target_exclusion_only'}`

Evidence uses only primes that do not divide the polynomial discriminant. Compatibility remains necessary target-exclusion evidence only.

## Budget Summary

| budget | rows | reached budget | valuable survival rows | containment failures | median indexed survivors |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 233 | 233 | 73 | 0 | 2 |
| 10 | 233 | 233 | 36 | 0 | 1 |
