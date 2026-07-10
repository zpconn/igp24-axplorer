# Final offline remediation report

## Decision

**Do not submit.** AXG-1.23 is a real million-example model iteration, but it
did not improve candidate quality. Direct `R24,M2` inference produced zero
exact-r24 rows, and exact structural projection retained a valuable target in
70/800 model rows versus 75/800 paired random controls.

## Evidence

- Complete degree-24 index: 25,000/25,000 groups and 942,607 cycle rows.
- Historical corrected calibration: 233/234 rows evaluable, zero true-label
  containment failures, but 36 valuable false positives still present at ten
  primes.
- AXG-1.23: 1,000,000 unique train rows, 100,000 separate eval rows, 31,250
  optimizer steps, one complete without-replacement corpus traversal, and 97%
  peak RTX 5090 utilization.
- Fresh SAIR read-only cross-check: 29 submissions, 234 scoreable rows, zero
  pending/unmatched rows, 233 unique submitted hashes, and no hash-set change.
- Seventy model-side hashes remain novel and retain necessary valuable-target
  evidence, but all seventy also retain crowded `24T24979`. The only valuable
  alternatives are `24T24969|r=24` and `24T24971|r=24`.
- Exact group labels are unknown. Expected points remain unavailable and the
  distinct valuable-pair best-case ceiling is two, not seventy.

AXG-1.24 should model construction parameters directly or use a constrained
decoder. It must retain the minimum one-million-unique-example rule and beat a
paired baseline clearly before promotion. No live SAIR submission was made.
