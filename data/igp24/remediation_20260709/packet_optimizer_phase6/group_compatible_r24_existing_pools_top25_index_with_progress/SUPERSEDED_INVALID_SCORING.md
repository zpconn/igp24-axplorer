# Superseded: Invalid Scoring Semantics

Created: 2026-07-09

This artifact is preserved for provenance, but its score fields must not be
used for submission or planning decisions.

The original optimizer summary reported:

- selected rows: `2`
- selected possible uncovered pairs: `18`
- `expected_score_ceiling`: `19.000000238418`
- `expected_score_estimate`: `4.40006742191`

Those values are mathematically invalid. One degree-24 polynomial has exactly
one true Galois label, so mutually exclusive compatible target labels cannot be
summed into a per-row official score ceiling. A two-row packet cannot have a
best-case uncovered-signature ceiling above two points when each uncovered pair
is worth at most one point.

The compatibility index used here was also partial: it contained only a small
target/nuisance subset of the 25,000 degree-24 transitive groups. Its survivor
count is therefore not a global ambiguity count or a probability denominator.
The old `1/sqrt(compatible_label_count)` heuristic was uncalibrated and has
been removed.

Use newer packet-optimizer outputs that report:

- `best_case_points`
- `best_case_packet_points`
- `valuable_targets_not_ruled_out`
- `expected_points_status = unavailable_uncalibrated`

unless a row has an exact verified pair and can use official score economics
directly.
