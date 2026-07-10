# IGP24 Adaptive Frobenius Benchmark

- Created: `2026-07-10T00:22:15.274845+00:00`
- Source commit: `039d27efd15bfc7fa5ba1934a6e3550099b3c5d7`
- Input rows: `234`
- Evaluated rows: `234`
- Failed rows: `0`
- True-label outside-index rows: `70`
- Indexed containment failures: `0`
- Final valuable-target survival rows: `0`
- Discriminant sources: `{'computed_sympy_polynomial_discriminant': 53, 'field_disc_abs': 181}`
- Max usable primes: `10`
- Index metadata: `{'index_scope': 'target_subset', 'indexed_group_count': 27, 'expected_global_group_count': 25000, 'global_index_complete': False, 'unindexed_label_mass_unknown': True, 'soundness': 'necessary_target_exclusion_only'}`

Evidence uses only primes that do not divide the polynomial discriminant. Compatibility remains necessary target-exclusion evidence only.

## Budget Summary

| budget | rows | reached budget | valuable survival rows | containment failures | median indexed survivors |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 234 | 234 | 4 | 0 | 1 |
| 10 | 234 | 234 | 0 | 0 | 1 |
