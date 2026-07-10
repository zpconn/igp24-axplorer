# IGP24 Reward Model Scoring Report

- Rows scored: `605`
- Decision counts: `{"abstain_uncertain": 70, "advisory_conflicted_sparse_positive": 48, "advisory_sparse_positive_candidate": 47, "avoid_high_collapse_risk": 440}`
- Observed outcome counts: `{"crowded_accepted_collapse": 389, "low_team_scoreable": 1, "no_valuable_target_survival": 154, "score_positive": 8, "unknown": 14, "wrong_r": 39}`
- Known risk rows among top 50 reward-ranked rows: `43`

## Top Reward Rows

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 92 | `low_team_scoreable` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 242 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=8` |
| 246 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=2` |
| 173 | `crowded_accepted_collapse` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 88 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 89 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 90 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 91 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 310 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 311 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 313 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 314 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 312 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 315 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 329 | `crowded_accepted_collapse` | 0.996 | 0.004 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 330 | `crowded_accepted_collapse` | 0.996 | 0.004 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 319 | `crowded_accepted_collapse` | 0.994 | 0.006 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 320 | `crowded_accepted_collapse` | 0.994 | 0.006 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 316 | `crowded_accepted_collapse` | 0.993 | 0.007 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 317 | `crowded_accepted_collapse` | 0.993 | 0.007 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |

## Reward-Rank False-Positive Warning

Known risk rows still appear in the reward-ranked shortlist. Treat the model as advisory until group compatibility and richer labels are available.

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 173 | `crowded_accepted_collapse` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 88 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 89 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 90 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 91 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 310 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 311 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 313 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 314 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 312 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 315 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 329 | `crowded_accepted_collapse` | 0.996 | 0.004 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 330 | `crowded_accepted_collapse` | 0.996 | 0.004 | `advisory_sparse_positive_candidate` | `model_sample_export` |
| 319 | `crowded_accepted_collapse` | 0.994 | 0.006 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 320 | `crowded_accepted_collapse` | 0.994 | 0.006 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 316 | `crowded_accepted_collapse` | 0.993 | 0.007 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 317 | `crowded_accepted_collapse` | 0.993 | 0.007 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 318 | `crowded_accepted_collapse` | 0.993 | 0.007 | `advisory_sparse_positive_candidate` | `positive_quadratic_product_plus_low_odd_perturbation` |
| 215 | `crowded_accepted_collapse` | 0.989 | 0.011 | `advisory_sparse_positive_candidate` | `degree12_base_six_positive_roots_lifted_by_x2` |
| 211 | `crowded_accepted_collapse` | 0.988 | 0.012 | `advisory_sparse_positive_candidate` | `degree12_base_six_positive_roots_lifted_by_x2` |

## Top Collapse-Risk Rows

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 182 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 183 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 184 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 185 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 186 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 187 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 188 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 189 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 190 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 191 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 192 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 193 | `crowded_accepted_collapse` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 40 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 41 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 42 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 43 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 44 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 45 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 46 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 47 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
