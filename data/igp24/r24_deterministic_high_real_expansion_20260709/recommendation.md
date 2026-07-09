# Recommendation

Post-submit update: the 11-row deterministic r24 packet was submitted after
explicit approval and accepted by SAIR, but all rows collapsed to the known
`24T25000|r=24` basin.

Why this is the best next move:

- r24 is still the largest remaining bucket.
- The lane is not the blocked r16/r8/r20 `24T25000` neighborhood.
- The sync state is complete, with no pending rows.
- The packet has 11 selected rows, 0 risk reasons, 11 basin fingerprints, and
  7 mod-p signatures.

Packet path:

`data/igp24/r24_deterministic_high_real_expansion_20260709/anti_basin_gate/anti_basin_candidate_coefficients.txt`

Submission:

`sub_55fba0a7253d4a72b8ab7a6e80d5cede`

Result:

- 11/11 accepted
- 11/11 scoreable after full post-submit sync
- pair: `24T25000|r=24`
- no new pair

Next action: use the accepted feedback as negative memory and do not widen this
deterministic r24 lane without a materially different construction.
