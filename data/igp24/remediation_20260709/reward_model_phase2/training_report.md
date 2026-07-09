# IGP24 Phase 2 Reward/Risk Model

- Created UTC: `2026-07-09T21:21:47.420927+00:00`
- Source dataset: `data/igp24/active_learning/axg_training_dataset_20260709_axg113_high_real.jsonl`
- Rows: `635`
- Advisory status: `advisory_insufficient_positive_data`
- Train rows: `519`
- Eval rows: `116`
- Train/eval group overlap: `[]`
- Outcome counts: `{"crowded_accepted_collapse": 462, "score_positive": 8, "unknown": 60, "wrong_r": 105}`

## Eval Metrics

- Supervised eval rows: `116`
- Unknown eval rows excluded: `0`
- Mean uncertainty entropy: `0.064`
- Abstention rate: `0.000`

## Per-Class Eval Metrics

| class | precision | recall | f1 | support |
| --- | ---: | ---: | ---: | ---: |
| `accepted_duplicate` | 0.000 | 0.000 | 0.000 | 0 |
| `crowded_accepted_collapse` | 1.000 | 0.943 | 0.971 | 106 |
| `invalid` | 0.000 | 0.000 | 0.000 | 0 |
| `low_team_scoreable` | 0.000 | 0.000 | 0.000 | 0 |
| `score_positive` | 0.111 | 1.000 | 0.200 | 1 |
| `wrong_r` | 1.000 | 0.778 | 0.875 | 9 |

## Uncertainty

- All-record evaluated rows: `575`
- All-record mean entropy: `0.063`
- All-record abstention rate: `0.000`

## Positive vs Crowded Diagnostic

- Score-positive rows: `8`
- Crowded-collapse rows: `462`
- Mean positive reward probability: `0.997`
- Mean crowded reward probability: `0.030`
- Positive mean ranks above crowded mean: `True`

## Highest Historical Collapse-Risk Families

| family | rows | mean collapse risk | mean reward prob | observed outcomes |
| --- | ---: | ---: | ---: | --- |
| `split_group_key:canonical_hash:8fc8dbbbfc9b98b355e64c8adbeaa379b757386a06c91d6bce66b7dd39340ed7` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:e6a03865c30924fdc18ef6755c044bf629ce81c63fbbea4c24fa696e0c41c8ff` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:a59933013ae1efe32fa976f66fff13b143c5c5da3f01acece76d22766643e61d` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:ad0ef274532e94ac65ab9acd8281148fc59a4da4fc749b44206435648c288c8d` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:0b90da296af33599cfa715f8821c1e3021bec18106fbee2e554d9c7119942bbc` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:0f98c40d6d72514031d5dece408d9511783a170976d129dad451d7a4508f3290` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:6e76dce206cc4b8138cd812c294840e34c4e80f29a3f5f7dc98b6d8ee9cfe229` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:912faa568e1b612b4b7b039e2614c94977b89096ccf4d3eaaa12c94c03a08335` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:d6c7fbef97bb4f66fc572c08443889f9c1173d61e915b2dedb31f9c919805a20` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |
| `split_group_key:canonical_hash:e25a29a187392e901a235329ac0a0146acd1040e6df1adf3b8b0512facb8f1cb` | 1 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 1}` |

## Limitations

- This is an advisory risk/reward model, not an exact Galois-group verifier.
- Unknown rows are excluded from supervised training and are not treated as negative.
- Positive supervision remains sparse; use uncertainty and abstention in downstream gates.
- Family-grouped and leave-one-family-out metrics are more meaningful than random row splits.
