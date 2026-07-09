# IGP24 Broad Historical Group Backtest

- Created: `2026-07-09T23:51:42.539443+00:00`
- Source commit: `199f079589bb151393f44dc994f534310395efaf`
- Scoreable rows: `234`
- Observed labels/pairs: `16` / `28`
- Evaluated rows: `169`
- Skipped rows: `65`
- True-label outside-index rows: `59`
- Indexed containment failures: `0`
- Valuable-target false-positive rows: `31`
- Index metadata: `{'index_scope': 'target_subset', 'indexed_group_count': 27, 'expected_global_group_count': 25000, 'global_index_complete': False, 'unindexed_label_mass_unknown': True, 'soundness': 'necessary_target_exclusion_only'}`
- Safety: `{'calls_sair': False, 'uses_network': False, 'runs_gap_magma_pari': False, 'generates_candidates': False, 'submits': False}`

Compatibility is necessary target-exclusion evidence only. With a partial index, outside-index labels remain unknown mass.

## Prime Budget Summary

| budget | rows | valuable survival rows | containment failures | median indexed survivors |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 169 | 31 | 0 | 1 |
| 10 | 169 | 31 | 0 | 1 |
| 20 | 169 | 31 | 0 | 1 |
| 40 | 169 | 31 | 0 | 1 |
| 80 | 169 | 31 | 0 | 1 |
