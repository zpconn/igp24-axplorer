# AXG-1.23 distilled result

AXG-1.23 is the first named iteration to satisfy the million-example rule. It
traversed 1,000,000 unique canonical training rows exactly once, used a
separate 100,000-row family/split-disjoint holdout, and ran 31,250 optimizer
steps on the RTX 5090. The 25.37M-parameter checkpoint reached train/eval loss
1.3000/1.9092. Eval loss stayed flat while train loss fell, so the loss curve
does not establish held-out family generalization.

Direct `R24,M2` inference decoded 4,059 of 4,096 attempts and almost always
preserved M2 support, but produced zero exact-r24 rows. An uncapped raw pass
provided 512 unique M2 outputs. Treating those outputs only as parameter
proposals, the exact projection layer built 1,569 fresh Eisenstein-irreducible,
exact-r24 `h(x^2)` rows after excluding all 1.1M corpus hashes and known SAIR
submission hashes.

The decisive paired comparison screened 800 model-projected rows and 800
same-source random controls with up to 40 explicitly unramified primes against
the complete 25,000-group index. Model/control valuable-target survival was
70/800 versus 75/800. The rate difference was -0.625 percentage points with an
approximate 95% interval of [-3.44, +2.19] points. Both lanes reached only
`24T24969|r=24` and `24T24971|r=24`.

Decision: **do not promote AXG-1.23**. It learned coefficient syntax and power
support, but not the global real-root condition and not a parameter proposal
distribution better than random. AXG-1.24 must still use at least one million
unique examples, but should model construction parameters directly or use a
constrained decoder. Promotion requires a measured paired-baseline win. No
live SAIR submission was made.
