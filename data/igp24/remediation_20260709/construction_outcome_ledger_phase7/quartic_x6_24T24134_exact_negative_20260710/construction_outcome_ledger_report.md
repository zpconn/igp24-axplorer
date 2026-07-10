# IGP24 Construction Outcome Ledger

- Created: `2026-07-10T05:15:48.200723+00:00`
- Source commit: `a8a4c552d44d448bf666f6db52dda2a7b3aa3009`
- Rows: `4`
- Routes: `1`
- Exact-label rows: `4`
- Target-hit rows: `0`
- False-target rows: `4`
- Submission-grade rows: `0`
- Outcome classes: `{"false_target_discovered_not_improved": 4}`
- Recommended actions: `{"block_repeat_exact_basin": 1}`
- Safety: Construction outcome ledger is local/file-only. It reads exact-label triage artifacts and writes route outcome summaries; it does not submit to SAIR or execute algebra systems.

## Route Outcomes

| route | family | rows | target hits | false targets | action | observed pairs |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `24T24134|r=8` | `quartic_in_x6` | 4 | 0 | 4 | `block_repeat_exact_basin` | `{"24T10010|r=8": 1, "24T12493|r=8": 1, "24T7635|r=8": 1, "24T9962|r=8": 1}` |

A blocked route here means an exact-label reviewed basin missed its intended target on every exact row. It does not prove the target impossible; it says not to repeat the same exact basin without a material structural change.
