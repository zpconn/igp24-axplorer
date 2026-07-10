# IGP24 Phase 2 Reward/Risk Model

- Created UTC: `2026-07-10T10:42:11.595887+00:00`
- Source dataset: `data/igp24/active_learning/axg_training_dataset_20260710_postremediation_exact13879_crossr_exact23883_exact9993_axg121.jsonl`
- Rows: `606`
- Advisory status: `advisory_insufficient_positive_data`
- Train rows: `413`
- Eval rows: `193`
- Train/eval group overlap: `[]`
- Outcome counts: `{"accepted_duplicate": 6, "crowded_accepted_collapse": 384, "low_team_scoreable": 1, "no_valuable_target_survival": 154, "score_positive": 8, "unknown": 14, "wrong_r": 39}`

## Eval Metrics

- Supervised eval rows: `193`
- Unknown eval rows excluded: `0`
- Mean uncertainty entropy: `0.442`
- Abstention rate: `0.363`

## Per-Class Eval Metrics

| class | precision | recall | f1 | support |
| --- | ---: | ---: | ---: | ---: |
| `accepted_duplicate` | 0.000 | 0.000 | 0.000 | 0 |
| `crowded_accepted_collapse` | 1.000 | 0.940 | 0.969 | 67 |
| `invalid` | 0.000 | 0.000 | 0.000 | 0 |
| `low_team_scoreable` | 0.000 | 0.000 | 0.000 | 0 |
| `no_valuable_target_survival` | 1.000 | 0.667 | 0.800 | 120 |
| `score_positive` | 0.000 | 0.000 | 0.000 | 0 |
| `wrong_r` | 0.130 | 1.000 | 0.231 | 6 |

## Uncertainty

- All-record evaluated rows: `592`
- All-record mean entropy: `0.144`
- All-record abstention rate: `0.118`

## Positive vs Crowded Diagnostic

- Score-positive rows: `9`
- Crowded-collapse rows: `384`
- Total collapse-risk rows: `583`
- Mean positive reward probability: `1.000`
- Mean crowded reward probability: `0.010`
- Mean collapse-risk reward probability: `0.066`
- Positive mean ranks above crowded mean: `True`
- Positive mean ranks above collapse-risk mean: `True`

## Highest Historical Collapse-Risk Families

| family | rows | mean collapse risk | mean reward prob | observed outcomes |
| --- | ---: | ---: | ---: | --- |
| `alt_composition_4x6` | 36 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 12, "no_valuable_target_survival": 24}` |
| `alt_composition_8x3` | 20 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 20}` |
| `r8_quartic_lift_perturbed` | 10 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 10}` |
| `odd_perturbed_r24_6x4_tower_escape` | 8 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 8}` |
| `twenty_linear_real_roots_two_no_real_quadratics_plus_coefficient_perturbation` | 8 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 8}` |
| `degree12_base_six_positive_roots_lifted_by_x2` | 6 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 6}` |
| `quartic_in_x6` | 4 | 1.000 | 0.000 | `{"accepted_duplicate": 4}` |
| `r8_quartic_lift_score_followup` | 4 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 4}` |
| `split_group_key:canonical_hash:3e8fad1c89acdaa94dd2484eedbda1a84aca93e0b428efce30b0b3b404318e70` | 3 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 3}` |
| `split_group_key:canonical_hash:00e496a1ba318dac2178d022d2cbaa3b6b4405d9b5aa5424f0c72ecdf9f0b63b` | 2 | 1.000 | 0.000 | `{"crowded_accepted_collapse": 2}` |

## Limitations

- This is an advisory risk/reward model, not an exact Galois-group verifier.
- Unknown rows are excluded from supervised training and are not treated as negative.
- Rows with adaptive no-valuable-target survival are supervised collapse-risk evidence, not exact labels.
- Positive supervision remains sparse; use uncertainty and abstention in downstream gates.
- Family-grouped and leave-one-family-out metrics are more meaningful than random row splits.
