# IGP24 Construction Registry

- Created: `2026-07-09T22:09:18.343416+00:00`
- Source commit: `d5582dfaae3f0bc57ff9b745366b8bbb024fec40`
- Families: `8`
- Exact-label claims: `0`
- Soundness: `declared_structural_routing_only_not_exact_label_evidence`
- Safety: Read-only construction registry report. It does not generate candidates, call external algebra systems or SAIR, or recommend live submission.
- Target label: `24T19906`
- Target r: `24`
- Target group record available: `False`
- Live submission recommended now: `False`

## Ranked Families

| rank | family | score | supports r | blocks | warnings |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `quartic_in_x6` | 67.0 | `True` | `6,12` | known_collapse_labels_in_avoid_set=24T24979,24T25000 |
| 2 | `gx2_degree12_lift` | 67.0 | `True` | `2,12` | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 3 | `tower_6x4` | 61.0 | `True` | `4,6,12` | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 4 | `positive_quadratic_product` | 61.0 | `True` | `2,12` | known_collapse_labels_in_avoid_set=24T23883,24T24651,24T25000 |
| 5 | `composition_8x3` | 61.0 | `True` | `3,8,12` | known_collapse_labels_in_avoid_set=24T25000 |
| 6 | `composition_4x6` | 57.0 | `True` | `4,6,12` | known_collapse_labels_in_avoid_set=24T25000 |
| 7 | `generic_sparse_random` | 53.0 | `True` | `-` | known_collapse_labels_in_avoid_set=24T24970,24T24979,24T25000 |
| 8 | `linear_real_product` | -173.0 | `False` | `-` | unsupported_r=24, known_collapse_labels_in_avoid_set=24T25000 |

## Registry Families

### gx2_degree12_lift

- Display name: g(x^2) degree-12 lift
- Degree pattern: `[12, 2]`
- Expected block sizes: `[2, 12]`
- Imprimitive expectation: `forced`
- Supported r values: `[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]`
- Known collapse labels: `['24T24970', '24T24979', '24T25000']`
- Known score-positive pairs: `['24T22770|r=12']`
- Exact-label claimed: `False`
- Notes: Useful for even-r imprimitive scouting, but recent nearby lanes collapsed into crowded labels.

### quartic_in_x6

- Display name: quartic in x^6
- Degree pattern: `[4, 6]`
- Expected block sizes: `[6, 12]`
- Imprimitive expectation: `forced`
- Supported r values: `[0, 4, 8, 12, 16, 20, 24]`
- Known collapse labels: `['24T24979', '24T25000']`
- Known score-positive pairs: `['24T9993|r=8']`
- Exact-label claimed: `False`
- Notes: Historically found the best project score row, but nearby follow-up lanes became crowded.

### tower_6x4

- Display name: 6 by 4 tower/composition
- Degree pattern: `[6, 4]`
- Expected block sizes: `[4, 6, 12]`
- Imprimitive expectation: `forced`
- Supported r values: `[0, 4, 8, 12, 16, 20, 24]`
- Known collapse labels: `['24T23883', '24T24651', '24T25000']`
- Known score-positive pairs: `[]`
- Exact-label claimed: `False`
- Notes: Keep as a structured lane only when block compatibility is useful and old tower basins are avoided.

### composition_8x3

- Display name: 8 by 3 composition
- Degree pattern: `[8, 3]`
- Expected block sizes: `[3, 8, 12]`
- Imprimitive expectation: `forced`
- Supported r values: `[0, 4, 8, 12, 16, 20, 24]`
- Known collapse labels: `['24T25000']`
- Known score-positive pairs: `[]`
- Exact-label claimed: `False`
- Notes: Prior submissions mostly collapsed; require materially different compatibility evidence before widening.

### composition_4x6

- Display name: 4 by 6 composition
- Degree pattern: `[4, 6]`
- Expected block sizes: `[4, 6, 12]`
- Imprimitive expectation: `forced`
- Supported r values: `[0, 4, 8, 12, 16, 20, 24]`
- Known collapse labels: `['24T25000']`
- Known score-positive pairs: `[]`
- Exact-label claimed: `False`
- Notes: Use only with a new inner-root family and compatibility evidence.

### linear_real_product

- Display name: linear-real-root product seed
- Degree pattern: `[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]`
- Expected block sizes: `[]`
- Imprimitive expectation: `not_forced`
- Supported r values: `[20]`
- Known collapse labels: `['24T25000']`
- Known score-positive pairs: `[]`
- Exact-label claimed: `False`
- Notes: A non-composed high-real lane; promising only if cycle compatibility escapes crowded labels.

### positive_quadratic_product

- Display name: positive quadratic product seed
- Degree pattern: `[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]`
- Expected block sizes: `[2, 12]`
- Imprimitive expectation: `likely`
- Supported r values: `[24]`
- Known collapse labels: `['24T23883', '24T24651', '24T25000']`
- Known score-positive pairs: `[]`
- Exact-label claimed: `False`
- Notes: Useful for r24 local validity pressure, but historical output collapsed heavily.

### generic_sparse_random

- Display name: generic sparse/random model export
- Degree pattern: `[24]`
- Expected block sizes: `[]`
- Imprimitive expectation: `unknown`
- Supported r values: `[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]`
- Known collapse labels: `['24T24970', '24T24979', '24T25000']`
- Known score-positive pairs: `[]`
- Exact-label claimed: `False`
- Notes: Keep as a baseline/source of raw diversity; never treat shape novelty as exact group targeting.
