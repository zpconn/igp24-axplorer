# IGP24 Phase 2 Reward/Risk Model

- Created UTC: `2026-07-10T10:13:45.541886+00:00`
- Source dataset: `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_exact13879_crossr_axg121.jsonl`
- Rows: `604`
- Advisory status: `advisory_insufficient_positive_data`
- Train rows: `411`
- Eval rows: `193`
- Train/eval group overlap: `[]`
- Outcome counts: `{"crowded_accepted_collapse": 388, "low_team_scoreable": 1, "no_valuable_target_survival": 154, "score_positive": 8, "unknown": 14, "wrong_r": 39}`

## Eval Metrics

- Supervised eval rows: `193`
- Unknown eval rows excluded: `0`
- Mean uncertainty entropy: `0.437`
- Abstention rate: `0.363`

## Per-Class Eval Metrics

| class | precision | recall | f1 | support |
| --- | ---: | ---: | ---: | ---: |
| `accepted_duplicate` | 0.000 | 0.000 | 0.000 | 0 |
| `crowded_accepted_collapse` | 1.000 | 0.791 | 0.883 | 67 |
| `invalid` | 0.000 | 0.000 | 0.000 | 0 |
| `low_team_scoreable` | 0.000 | 0.000 | 0.000 | 0 |
| `no_valuable_target_survival` | 1.000 | 0.667 | 0.800 | 120 |
| `score_positive` | 0.000 | 0.000 | 0.000 | 0 |
| `wrong_r` | 0.130 | 1.000 | 0.231 | 6 |

## Uncertainty

- All-record evaluated rows: `590`
- All-record mean entropy: `0.191`
- All-record abstention rate: `0.119`

## Positive vs Crowded Diagnostic

- Score-positive rows: `9`
- Crowded-collapse rows: `388`
- Total collapse-risk rows: `581`
- Mean positive reward probability: `0.742`
- Mean crowded reward probability: `0.114`
- Mean collapse-risk reward probability: `0.155`
- Positive mean ranks above crowded mean: `True`
- Positive mean ranks above collapse-risk mean: `True`

## Highest Historical Collapse-Risk Families

| family | rows | mean collapse risk | mean reward prob | observed outcomes |
| --- | ---: | ---: | ---: | --- |
| `alt_composition_4x6` | 36 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 12, "no_valuable_target_survival": 24}` |
| `split_group_key:canonical_hash:0f3ad8602d895b7e44729fbe5604fd904f6181c786c865c1e6da4bfaf151ab33` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:5795238c64cc937c60fc0ae2fd41381b5cd07c0a2c4694bff9909ffd195b978b` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:65cf18194d24d13996856c8be7de183d7e1d0de1b96a7496d57ff0879476e8f5` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:e5a27b5013e52507174f666844289c4a4e9fb6f63bf85f7c73724a0c8b27eb9c` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:0ec921751862f6e9c5ddd145b8174f19d0a2e58f8b5c0867f5ebde1f8a6c9120` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:0fc476540a1158ac455b8ed1bdb8c1e106e1b7a008ba3b834a66c2833846cba7` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:21860e8f6e79938dd3d10c8a66cadfb3ca3e72ea5ed9b2b61dcdadb94878189a` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:352113ba024b27afc9efc3dc73d27387fa75aaccccb6035a79c0b11650da8181` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |
| `split_group_key:canonical_hash:5b73ddd3fd68c81e35b7ba2c21a253f53936610a3bb817c4af86e43b862ffbfe` | 1 | 1.000 | 0.000 | `{"wrong_r": 1}` |

## Limitations

- This is an advisory risk/reward model, not an exact Galois-group verifier.
- Unknown rows are excluded from supervised training and are not treated as negative.
- Rows with adaptive no-valuable-target survival are supervised collapse-risk evidence, not exact labels.
- Positive supervision remains sparse; use uncertainty and abstention in downstream gates.
- Family-grouped and leave-one-family-out metrics are more meaningful than random row splits.
