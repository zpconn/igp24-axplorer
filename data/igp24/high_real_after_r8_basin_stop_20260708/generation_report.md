# High-Real Candidate Source Summary

This pass did not start a new model training run and did not call the SAIR API.
`SAIR_API_KEY` was not present in the environment, so the evaluation used the
latest complete local sync:
`data/igp24/sair_sync_20260708_r8_followup_after_submit/`.

The candidate queue was built from existing bounded AXG-1.4 provenance-aware
CUDA sample exports. Those samples already include the provenance required for
the post-r8-stop gate: construction family, target real-root intent,
template/family id, perturbation mode, support pattern, support gcd, basin
fingerprint, mod-p pattern when sampled, and source lineage.

| lane | source candidates | target-r survivors | eligible after gate | selected |
| --- | ---: | ---: | ---: | ---: |
| r24 model sample export | 39 | 28 | 2 | 2 |
| r16 model sample export | 40 | 22 | 5 | 3 |
| r20 model sample export | 35 | 18 | 7 | 4 |

The chosen primary lane is r24 because it has the largest remaining-signature
bucket and avoids widening the pending `24T25000|r=20` basin. r16 is the best
near-term refinement backup. r20 locally forms a four-row packet, but it is
held until the pending `24T25000|r=20` rows resolve.
