# IGP24 Broad Historical Group Backtest

- Created: `2026-07-10T02:40:49.329971+00:00`
- Source commit: `713f314523419e242ed7ca47a6caec1da963dd60`
- Scoreable rows: `234`
- Observed labels/pairs: `16` / `28`
- Evaluated rows: `233`
- Skipped rows: `1`
- True-label outside-index rows: `0`
- Indexed containment failures: `0`
- Valuable-target false-positive rows: `36`
- Index metadata: `{'index_scope': 'complete_degree24_universe', 'indexed_group_count': 25000, 'expected_global_group_count': 25000, 'global_index_complete': True, 'unindexed_label_mass_unknown': False, 'soundness': 'necessary_target_exclusion_only'}`
- Safety: `{'calls_sair': False, 'uses_network': False, 'runs_gap_magma_pari': False, 'generates_candidates': False, 'submits': False}`

Compatibility is necessary target-exclusion evidence only. With a partial index, outside-index labels remain unknown mass.

## Prime Budget Summary

| budget | rows | valuable survival rows | containment failures | median indexed survivors |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 233 | 73 | 0 | 2 |
| 10 | 233 | 36 | 0 | 1 |
