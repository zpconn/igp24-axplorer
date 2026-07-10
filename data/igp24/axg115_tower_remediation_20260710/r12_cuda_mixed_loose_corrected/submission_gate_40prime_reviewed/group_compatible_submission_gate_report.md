# IGP24 Group-Compatible Submission Gate

This is a local review gate only. It did not submit to SAIR, call the SAIR API, or read an API key.

## Status

- [x] Local exact validity and packet checks passed.
- [x] Local SAIR dry-run formatting/body-size validation passed.
- [x] Complete SAIR sync summary supplied.
- [ ] Exact Galois labels verified: `False`
- [ ] Live submission recommended now: `False`

Reason: local gate passed, but compatibility is necessary evidence only; exact labels remain unknown and live SAIR submission requires explicit user approval

## Packet Summary

- Rows: `3`
- Possible uncovered pairs: `0`
- Possible low-team pairs: `8`
- Possible crowded pairs: `22`
- Current uncovered pairs after progress cross-check: `0`
- Current low-team pairs after progress cross-check: `8`
- Stale possible-uncovered pairs: `0`
- Known submitted hashes: `0`
- Known submitted pairs: `[]`
- Minimum Frobenius primes required: `40`
- Insufficient adaptive Frobenius rows: `0`
- Body bytes: `202`
- Coefficient SHA256: `c5b6b7daa70d34fb4bf325c90778ce10cf87740bf82c5e8fdbf07387bafdfc94`

## Selected Rows

| rank | hash | r | compatible labels | Frobenius primes | current uncovered | known pair | local status |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | `2d819cabad22` | 4 | 21 | 40 | 0 | - | local_gate_passed_compatibility_only |
| 2 | `8866c86236ea` | 12 | 7 | 40 | 0 | - | local_gate_passed_compatibility_only |
| 3 | `6951fa0c500f` | 4 | 7 | 40 | 0 | - | local_gate_passed_compatibility_only |

## Remaining Gates

- `compatibility_only_exact_label_unknown`
- `fresh_sair_sync_present_but_should_refresh_immediately_before_live_submission`
- `explicit_user_approval_required_for_exact_live_packet`

## Safety

- Compatibility evidence is necessary evidence only; it is not an exact-label claim.
- The coefficient file is normalized for manual review but is not submitted automatically.
- Live submission still requires explicit user approval of the exact packet.
