# Pending Collision Report

- Focus pair: `24T25000|r=20`
- Selected rows: 4
- Focus pending rows: 8
- Exact coefficient-hash overlaps: 0
- Full submission state complete: `False`
- Degraded sync summary: None
- Live submission allowed: `False`
- Evidence strength: `weak_for_label_novelty_strong_for_exact_hash_nonoverlap`

## Selected Provenance

- Template families: `{"model:mixed:r20:dense_mixed_support_gcd1": 2, "model:mixed:r20:medium_mixed_support_gcd1": 2}`
- Basin fingerprints: `{"33465526667f9ca21a77d799": 1, "64f19fed392372573952bfad": 1, "99b6cb3c4c0d9ae3b90a6dbd": 1, "f29ba57c997c51c793139aa4": 1}`
- Perturbation modes: `{"dense_mixed_support_gcd1": 2, "medium_mixed_support_gcd1": 2}`
- Mod-p signatures: `{"None": 3, "p2:1-2-3-18;p3:1-1-1-8-13;p5:1-2-10-11;p7:1-1-1-4-17": 1}`

## Pending Pressure

- Pending pair counts: `{"24T24979|r=8": 1, "24T25000|r=20": 8, "24T25000|r=8": 9}`
- Support-key overlap with focus pending rows: `["(25, 1, False, (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23))"]`

## Conclusion

No exact selected-vs-pending coefficient hash overlap was found, but the focus pair still has pending SAIR rows and sync is not complete; treat the packet as review-only until pending rows resolve.
