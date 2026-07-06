# IGP24 Target Bucket Plan

Exact uncovered (24Tt, r) target lists are not derivable from this screenshot snapshot. Pull fresh SAIR API data before search or submission planning that depends on exact target membership.

## Snapshot

- Captured at: `2026-07-06T16:48:00-05:00`
- Capture method: `user-provided screenshot analysis, not live API data`
- Total valid signatures: 165836
- Uncovered signatures: 53011
- Uncovered solvable: 51992 (98.1%)
- LMFDB baseline signatures: 622

## Largest Remaining Buckets

| r | remaining | total | remaining % | local accepted pairs | note |
| ---: | ---: | ---: | ---: | ---: | --- |
| 24 | 12126 | 25000 | 48.5 | 0 | largest remaining bucket; no proven local explicit generator yet |
| 16 | 10902 | 21421 | 50.9 | 2 | large bucket, but current divisor-2 r16 families repeatedly collapsed |
| 8 | 6988 | 23556 | 29.7 | 4 | productive r8_quartic_lift path already produced four accepted labels from six rows |
| 12 | 6919 | 19934 | 34.7 | 0 | large high-real-root bucket; no proven local explicit generator yet |
| 20 | 5773 | 10852 | 53.2 | 0 | large undercovered high-real-root bucket; no proven local explicit generator yet |
| 0 | 4384 | 24839 | 17.6 | 0 | saved proxy rows exist, but this is not a largest remaining bucket |
| 4 | 3941 | 20057 | 19.6 | 7 | locally mature but crowded; many submissions collapsed to known/generic labels |
| 6 | 566 | 6004 | 9.4 | 0 | small cleanup bucket |

## Recommended Action Buckets

| rank | r | action score | remaining | local evidence | recommendation |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 24 | 109.97 | 12126 | largest remaining bucket; no proven local explicit generator yet | Prioritize a new explicit r24 solvable/high-real-root construction. |
| 2 | 20 | 73.57 | 5773 | large undercovered high-real-root bucket; no proven local explicit generator yet | Prototype an explicit r20 solvable/high-real-root construction. |
| 3 | 8 | 69.85 | 6988 | r8_quartic_lift produced multiple accepted labels from a six-row submission | Continue bounded r8 solvable/composed-family variations as a near-term submission lane. |
| 4 | 12 | 67.23 | 6919 | large high-real-root bucket; no proven local explicit generator yet | Build an explicit solvable/composed r12 construction before broad sampling. |
| 5 | 16 | 51.25 | 10902 | exact divisor-2 g(x^2) rows landed as 24T24979|r=16; odd and multi-odd near-composed divisor-2 rows landed as 24T25000|r=16 | Keep r16 as globally important, but do not widen the current g(x^2)/odd-perturbation corridor. |
| 6 | 0 | 21.66 | 4384 | saved proxy rows exist, but this is not a largest remaining bucket | Treat r=0 as a lower-priority side lane unless fresh API targets show an easy gap. |
| 7 | 4 | 5.99 | 3941 | many r4 follow-up rows collapsed to generic 24T25000|r=4 | Avoid broad r=4 mining unless exact score/discriminant improvement is the target. |
| 8 | 18 | -21.23 | 408 | small cleanup bucket | Use only for exact API-guided cleanup. |

## Strategy

- Do not widen the current r16 divisor-2 perturbation family; it repeatedly collapsed to 24T24979/24T25000.
- Prioritize a new explicit r24 solvable/high-real-root construction because r=24 is the largest remaining bucket.
- Prototype r20 and r12 solvable/high-real-root constructions; both are large undercovered buckets without proven local generators.
- Continue bounded r8 composed-family work because r8_quartic_lift already produced multiple accepted labels.
- Do not start GPU/model training until there is a target-conditioned sampling objective derived from API target data or a successful construction family.

## Artifacts

- target_bucket_plan_json: `data/igp24/target_bucket_plan_20260706/target_bucket_plan.json`
- target_bucket_plan_md: `data/igp24/target_bucket_plan_20260706/target_bucket_plan.md`
- target_bucket_plan_summary_json: `data/igp24/target_bucket_plan_20260706/target_bucket_plan_summary.json`
