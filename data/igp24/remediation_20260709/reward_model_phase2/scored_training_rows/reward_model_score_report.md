# IGP24 Reward Model Scoring Report

- Rows scored: `635`
- Decision counts: `{"advisory_review": 2, "advisory_sparse_positive_candidate": 28, "avoid_high_collapse_risk": 605}`
- Observed outcome counts: `{"crowded_accepted_collapse": 462, "score_positive": 8, "unknown": 60, "wrong_r": 105}`
- Known risk rows among top 50 reward-ranked rows: `38`

## Top Reward Rows

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 272 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=8` |
| 276 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=2` |
| 538 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:23ab54762bd568a9d9bbbe98b406b128a5fe938221698874b499efb7eaf4325e` |
| 542 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:9eff4260b12d6bcfbaface640f8ec3e24e18e5e54bc7cd91fbdd3fce38a938d2` |
| 599 | `crowded_accepted_collapse` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:86f62f433b3f8da285f21aeea33f1ee08bc732e5a818d7e9601659d4aafbca7b` |
| 600 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:eb604c239982e2f545abd3ceda231a055861b13f2f496f41241aa47b1236d878` |
| 601 | `score_positive` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:2fe4b5059101f087ac87a10d1889e3ded1aaa881d6f343c50d0373fdb41182ba` |
| 598 | `crowded_accepted_collapse` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:de699993e8a94a05a618350522d7eaacd34f0caf956c8c74302cca32b00dbf29` |
| 630 | `wrong_r` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:9c45c5493e7a4e3ade9700843b66b32c21c8f50868f0ddd9eb8c42c386730131` |
| 596 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:85cefa437fa2615f6b3a5ff1e9eacd41a1dbabc37a1f2faff42dd863e9300c73` |
| 597 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:778075741c827ea333a5c0d58f13373e1e4b2c0b8ef0dd4a596a864c584db5e9` |
| 602 | `wrong_r` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:33772dd90765a2726c35d5d653cd17725b50ffdac30bb4e7cf195068b94851da` |
| 274 | `crowded_accepted_collapse` | 0.997 | 0.003 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=5` |
| 394 | `crowded_accepted_collapse` | 0.992 | 0.008 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:86f62f433b3f8da285f21aeea33f1ee08bc732e5a818d7e9601659d4aafbca7b` |
| 395 | `score_positive` | 0.990 | 0.010 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:eb604c239982e2f545abd3ceda231a055861b13f2f496f41241aa47b1236d878` |
| 396 | `score_positive` | 0.990 | 0.010 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:2fe4b5059101f087ac87a10d1889e3ded1aaa881d6f343c50d0373fdb41182ba` |
| 393 | `crowded_accepted_collapse` | 0.969 | 0.031 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:de699993e8a94a05a618350522d7eaacd34f0caf956c8c74302cca32b00dbf29` |
| 391 | `crowded_accepted_collapse` | 0.890 | 0.110 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:85cefa437fa2615f6b3a5ff1e9eacd41a1dbabc37a1f2faff42dd863e9300c73` |
| 392 | `crowded_accepted_collapse` | 0.890 | 0.110 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:778075741c827ea333a5c0d58f13373e1e4b2c0b8ef0dd4a596a864c584db5e9` |
| 603 | `wrong_r` | 0.849 | 0.151 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:72ed23a8d8bf5d9bd2401b0fb3b94b134794c1a5b51de7262daf2663bbdfad50` |

## Reward-Rank False-Positive Warning

Known risk rows still appear in the reward-ranked shortlist. Treat the model as advisory until group compatibility and richer labels are available.

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 599 | `crowded_accepted_collapse` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:86f62f433b3f8da285f21aeea33f1ee08bc732e5a818d7e9601659d4aafbca7b` |
| 598 | `crowded_accepted_collapse` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:de699993e8a94a05a618350522d7eaacd34f0caf956c8c74302cca32b00dbf29` |
| 630 | `wrong_r` | 1.000 | 0.000 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:9c45c5493e7a4e3ade9700843b66b32c21c8f50868f0ddd9eb8c42c386730131` |
| 596 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:85cefa437fa2615f6b3a5ff1e9eacd41a1dbabc37a1f2faff42dd863e9300c73` |
| 597 | `crowded_accepted_collapse` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:778075741c827ea333a5c0d58f13373e1e4b2c0b8ef0dd4a596a864c584db5e9` |
| 602 | `wrong_r` | 0.999 | 0.001 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:33772dd90765a2726c35d5d653cd17725b50ffdac30bb4e7cf195068b94851da` |
| 274 | `crowded_accepted_collapse` | 0.997 | 0.003 | `advisory_sparse_positive_candidate` | `single_base_coefficient_perturbation|pos=1,2,3,4,5,6|neg=1,2,3,4,5,6|y=5` |
| 394 | `crowded_accepted_collapse` | 0.992 | 0.008 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:86f62f433b3f8da285f21aeea33f1ee08bc732e5a818d7e9601659d4aafbca7b` |
| 393 | `crowded_accepted_collapse` | 0.969 | 0.031 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:de699993e8a94a05a618350522d7eaacd34f0caf956c8c74302cca32b00dbf29` |
| 391 | `crowded_accepted_collapse` | 0.890 | 0.110 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:85cefa437fa2615f6b3a5ff1e9eacd41a1dbabc37a1f2faff42dd863e9300c73` |
| 392 | `crowded_accepted_collapse` | 0.890 | 0.110 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:778075741c827ea333a5c0d58f13373e1e4b2c0b8ef0dd4a596a864c584db5e9` |
| 603 | `wrong_r` | 0.849 | 0.151 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:72ed23a8d8bf5d9bd2401b0fb3b94b134794c1a5b51de7262daf2663bbdfad50` |
| 263 | `crowded_accepted_collapse` | 0.832 | 0.168 | `advisory_sparse_positive_candidate` | `pos=1,2,4,5,7,9|neg=1,2,4,5,7,9|y=1,5,9` |
| 604 | `wrong_r` | 0.779 | 0.221 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:33e431d55c37368ed565f364fb75690cad8e5e7d8dc2c83422a1db895e3a4b4d` |
| 633 | `wrong_r` | 0.779 | 0.221 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:a97caa584baa93fa2b610cb0a7882ba766d5ffe13d2450b23aceb6ea0f361d7a` |
| 262 | `crowded_accepted_collapse` | 0.759 | 0.241 | `advisory_sparse_positive_candidate` | `pos=1,2,4,5,7,9|neg=1,2,4,5,7,9|y=1,6` |
| 605 | `wrong_r` | 0.686 | 0.314 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:95dd827ceadb2482572fd9f504917b34c067491fec88bacc78b6893165f18490` |
| 606 | `wrong_r` | 0.686 | 0.314 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:2ba8637f2f40b567c6d9b73274a0e55f4dfc4f71b542a4d7e8a2d6941b2376bd` |
| 631 | `wrong_r` | 0.686 | 0.314 | `advisory_sparse_positive_candidate` | `split_group_key:canonical_hash:981a94588aab9c05713953e0d6feef907b2d55ba4cd01ef386b57cae274248c5` |
| 342 | `crowded_accepted_collapse` | 0.335 | 0.665 | `advisory_review` | `positive_quadratic_product_plus_low_odd_perturbation` |

## Top Collapse-Risk Rows

| row | outcome | reward p | collapse p | decision | family |
| ---: | --- | ---: | ---: | --- | --- |
| 157 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 145 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 158 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 160 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 162 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 149 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 22 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 170 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 173 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 176 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 180 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 155 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 161 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 186 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 37 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 41 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 61 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 65 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 174 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
| 175 | `wrong_r` | 0.000 | 1.000 | `avoid_high_collapse_risk` | `model_sample_export` |
