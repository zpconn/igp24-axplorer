# IGP24 R16 Diversified Candidate Queue

CPU-only local r16 diversification probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 720
- Valid r=16 candidates: 149
- Selected rows: 12
- Mode counts: `{"mixed_even_odd_perturbed": 4, "three_odd_perturbed_near_composed": 4, "two_odd_perturbed_near_composed": 4}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 112, "real_root_count_mismatch": 298, "reducible_over_q": 91, "too_close_to_accepted_even_coefficients": 70}`

| rank | hash | mode | off-block | height | score | non-generic | flags | min full L1 |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | `2259d4517994` | `mixed_even_odd_perturbed` | 2 | 245952 | 0.000 | 140.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 411103 |
| 2 | `a1a2119de550` | `two_odd_perturbed_near_composed` | 2 | 829440 | 0.000 | 140.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1035542 |
| 3 | `624066636c9c` | `three_odd_perturbed_near_composed` | 3 | 174988 | 0.000 | 100.000 | weak_near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 705601 |
| 4 | `d3e8fd316db0` | `mixed_even_odd_perturbed` | 2 | 2663680 | 0.000 | 140.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 7044485 |
| 5 | `f4ac64303241` | `two_odd_perturbed_near_composed` | 2 | 898128 | 0.000 | 140.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1706576 |
| 6 | `b2b4087281e1` | `three_odd_perturbed_near_composed` | 3 | 598752 | 0.000 | 100.000 | weak_near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 640951 |
| 7 | `9984288bf73a` | `mixed_even_odd_perturbed` | 2 | 3993600 | 0.000 | 140.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 9359069 |
| 8 | `1c3b415990a7` | `two_odd_perturbed_near_composed` | 2 | 165784 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 516018 |
| 9 | `0e75eeff23ce` | `three_odd_perturbed_near_composed` | 3 | 829440 | 0.000 | 100.000 | weak_near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 1035543 |
| 10 | `338645796e79` | `mixed_even_odd_perturbed` | 2 | 5990400 | 0.000 | 140.000 | near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 13816299 |
| 11 | `70b58279f77a` | `two_odd_perturbed_near_composed` | 2 | 174988 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 705600 |
| 12 | `5132e59962c6` | `three_odd_perturbed_near_composed` | 3 | 1926000 | 0.000 | 100.000 | weak_near_composed_support,all_sampled_frobenius_even,no_long_cycle_witness_in_sample | 3380671 |

Artifacts:
- Queue JSONL: `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_hashes.txt`
- Summary JSON: `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_summary.json`
