# IGP24 R16 Diversified Candidate Queue

CPU-only local r16 diversification probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 240
- Valid r=16 candidates: 189
- Selected rows: 10
- Mode counts: `{"exact_composed_new_base": 5, "odd_perturbed_near_composed": 5}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 32, "real_root_count_mismatch": 19}`

| rank | hash | mode | height | score | non-generic | flags | min L1 to accepted |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | `4d1e653e605a` | `exact_composed_new_base` | 317088 | 0.000 | 785.000 | exact_composed_support,near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 987428 |
| 2 | `13094bd39221` | `odd_perturbed_near_composed` | 325430 | 0.000 | 170.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1612797 |
| 3 | `707b2cbef380` | `exact_composed_new_base` | 325430 | 0.000 | 785.000 | exact_composed_support,near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1612794 |
| 4 | `7bcf04f2e733` | `odd_perturbed_near_composed` | 399168 | 0.000 | 170.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1624599 |
| 5 | `ec8fd21eb76d` | `exact_composed_new_base` | 444752 | 0.000 | 785.000 | exact_composed_support,near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 2162154 |
| 6 | `c9e9a9399712` | `odd_perturbed_near_composed` | 437040 | 0.000 | 170.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1612797 |
| 7 | `71f1618abe1a` | `exact_composed_new_base` | 552960 | 0.000 | 785.000 | exact_composed_support,near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 2178756 |
| 8 | `e7657687d139` | `odd_perturbed_near_composed` | 444752 | 0.000 | 170.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 2162157 |
| 9 | `b69dd0857b61` | `exact_composed_new_base` | 585216 | 0.000 | 785.000 | exact_composed_support,near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 2162160 |
| 10 | `dbce4e2bc909` | `odd_perturbed_near_composed` | 552960 | 0.000 | 170.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 2178759 |

Artifacts:
- Queue JSONL: `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_hashes.txt`
- Summary JSON: `data/igp24/r16_diversity_probe_20260706/r16_diversified_summary.json`
