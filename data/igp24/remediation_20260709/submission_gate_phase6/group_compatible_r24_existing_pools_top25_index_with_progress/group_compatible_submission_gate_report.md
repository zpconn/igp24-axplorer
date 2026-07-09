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

- Rows: `2`
- Possible uncovered pairs: `18`
- Possible low-team pairs: `0`
- Possible crowded pairs: `2`
- Body bytes: `280`
- Coefficient SHA256: `4466c0796f20d8a877e7713cefa3afa1b1641abbaca2044b44256c2d05a76a76`

## Selected Rows

| rank | hash | r | compatible labels | uncovered | low-team | crowded | local status |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `c814e1de3e8d` | 24 | 19 | 17 | 0 | 2 | local_gate_passed_compatibility_only |
| 2 | `2c8838b3f843` | 24 | 4 | 2 | 0 | 2 | local_gate_passed_compatibility_only |

## Remaining Gates

- `compatibility_only_exact_label_unknown`
- `fresh_sair_sync_present_but_should_refresh_immediately_before_live_submission`
- `explicit_user_approval_required_for_exact_live_packet`

## Safety

- Compatibility evidence is necessary evidence only; it is not an exact-label claim.
- The coefficient file is normalized for manual review but is not submitted automatically.
- Live submission still requires explicit user approval of the exact packet.
