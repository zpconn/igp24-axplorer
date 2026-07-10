# IGP24 Reward Model Scoring Report

- Rows scored: `507`
- Decision counts: `{"abstain_uncertain": 14, "advisory_conflicted_sparse_positive": 46, "advisory_sparse_positive_candidate": 15, "avoid_high_collapse_risk": 432}`
- Observed outcome counts: `{"crowded_accepted_collapse": 388, "no_valuable_target_survival": 72, "score_positive": 8, "wrong_r": 39}`
- Known risk rows among top 50 reward-ranked rows: `44`

## Top Reward Rows

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 144 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=8` |
| 148 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=2` |
| 32 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 33 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 34 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 35 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 146 | `crowded_accepted_collapse` | 0.978 | 0.022 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=5` |
| 410 | `score_positive` | 0.965 | 0.035 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:23ab54762bd568a9d9bbbe98b406b128a5fe938221698874b499efb7eaf4325e` |
| 414 | `score_positive` | 0.965 | 0.035 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:9eff4260b12d6bcfbaface640f8ec3e24e18e5e54bc7cd91fbdd3fce38a938d2` |
| 468 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:85cefa437fa2615f6b3a5ff1e9eacd41a1dbabc37a1f2faff42dd863e9300c73` |
| 469 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:778075741c827ea333a5c0d58f13373e1e4b2c0b8ef0dd4a596a864c584db5e9` |
| 470 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:de699993e8a94a05a618350522d7eaacd34f0caf956c8c74302cca32b00dbf29` |
| 471 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:86f62f433b3f8da285f21aeea33f1ee08bc732e5a818d7e9601659d4aafbca7b` |
| 472 | `score_positive` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:eb604c239982e2f545abd3ceda231a055861b13f2f496f41241aa47b1236d878` |
| 473 | `score_positive` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:2fe4b5059101f087ac87a10d1889e3ded1aaa881d6f343c50d0373fdb41182ba` |
| 152 | `crowded_accepted_collapse` | 0.724 | 0.276 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,7|neg=1,2,3,4,5,6|y=0` |
| 150 | `crowded_accepted_collapse` | 0.466 | 0.534 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,7|y=4` |
| 151 | `crowded_accepted_collapse` | 0.466 | 0.534 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,7|neg=1,2,3,4,5,6|y=3` |
| 153 | `crowded_accepted_collapse` | 0.466 | 0.534 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,7|y=1` |
| 271 | `crowded_accepted_collapse` | 0.427 | 0.573 | `abstain_uncertain` | `r8_quartic_lift_score_followup` |

## Reward-Rank False-Positive Warning

Known risk rows still appear in the reward-ranked shortlist. Treat the model as advisory until group compatibility and richer labels are available.

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 32 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 33 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 34 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 35 | `crowded_accepted_collapse` | 0.998 | 0.002 | `advisory_sparse_positive_candidate` | `quartic_in_x6` |
| 146 | `crowded_accepted_collapse` | 0.978 | 0.022 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=5` |
| 468 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:85cefa437fa2615f6b3a5ff1e9eacd41a1dbabc37a1f2faff42dd863e9300c73` |
| 469 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:778075741c827ea333a5c0d58f13373e1e4b2c0b8ef0dd4a596a864c584db5e9` |
| 470 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:de699993e8a94a05a618350522d7eaacd34f0caf956c8c74302cca32b00dbf29` |
| 471 | `crowded_accepted_collapse` | 0.824 | 0.176 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:86f62f433b3f8da285f21aeea33f1ee08bc732e5a818d7e9601659d4aafbca7b` |
| 152 | `crowded_accepted_collapse` | 0.724 | 0.276 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,7|neg=1,2,3,4,5,6|y=0` |
| 150 | `crowded_accepted_collapse` | 0.466 | 0.534 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,7|y=4` |
| 151 | `crowded_accepted_collapse` | 0.466 | 0.534 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,7|neg=1,2,3,4,5,6|y=3` |
| 153 | `crowded_accepted_collapse` | 0.466 | 0.534 | `advisory_conflicted_sparse_positive` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,7|y=1` |
| 271 | `crowded_accepted_collapse` | 0.427 | 0.573 | `abstain_uncertain` | `r8_quartic_lift_score_followup` |
| 117 | `crowded_accepted_collapse` | 0.408 | 0.592 | `advisory_conflicted_sparse_positive` | `degree12_base_six_positive_roots_lifted_by_x2` |
| 113 | `crowded_accepted_collapse` | 0.382 | 0.618 | `abstain_uncertain` | `degree12_base_six_positive_roots_lifted_by_x2` |
| 115 | `crowded_accepted_collapse` | 0.382 | 0.618 | `abstain_uncertain` | `degree12_base_six_positive_roots_lifted_by_x2` |
| 116 | `crowded_accepted_collapse` | 0.347 | 0.653 | `abstain_uncertain` | `degree12_base_six_positive_roots_lifted_by_x2` |
| 269 | `crowded_accepted_collapse` | 0.329 | 0.671 | `abstain_uncertain` | `r8_quartic_lift_score_followup` |
| 270 | `crowded_accepted_collapse` | 0.329 | 0.671 | `abstain_uncertain` | `r8_quartic_lift_score_followup` |

## Top Collapse-Risk Rows

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 0 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 1 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 2 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 3 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 4 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 5 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 6 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 7 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 8 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 9 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 10 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 11 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 12 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 13 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 14 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 15 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 16 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 17 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 18 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
| 19 | `no_valuable_target_survival` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `alt_composition_4x6` |
