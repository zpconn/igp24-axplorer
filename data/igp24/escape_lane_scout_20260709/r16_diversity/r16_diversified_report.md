# IGP24 R16 Diversified Candidate Queue

CPU-only local r16 diversification probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 220
- Valid r=16 candidates: 48
- Selected rows: 24
- Mode counts: `{"four_odd_perturbed_near_composed": 6, "mixed_even_odd_perturbed": 7, "three_odd_perturbed_near_composed": 7, "two_odd_perturbed_near_composed": 4}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 22, "real_root_count_mismatch": 36, "reducible_over_q": 33, "too_close_to_accepted_even_coefficients": 26, "too_few_divisor2_off_block_terms": 55}`

| rank | hash | mode | off-block | height | score | non-generic | flags | min full L1 |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | `3db3346a5e52` | `two_odd_perturbed_near_composed` | 2 | 254304 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 213223 |
| 2 | `ad05b6acc31f` | `mixed_even_odd_perturbed` | 2 | 309440 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 333055 |
| 3 | `eae6516b0ef9` | `three_odd_perturbed_near_composed` | 3 | 475632 | 0.000 | 80.000 | weak_near_composed_support,all_sampled_frobenius_even | 628137 |
| 4 | `e8d5eddcdfae` | `four_odd_perturbed_near_composed` | 4 | 1244160 | 0.000 | 75.000 | weak_near_composed_support,all_sampled_frobenius_even | 2525571 |
| 5 | `15b1c81627b4` | `two_odd_perturbed_near_composed` | 2 | 3479940 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 6311491 |
| 6 | `efb96272cc74` | `mixed_even_odd_perturbed` | 2 | 841227 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 1708566 |
| 7 | `6b6bc6581bdf` | `three_odd_perturbed_near_composed` | 3 | 898128 | 0.000 | 80.000 | weak_near_composed_support,all_sampled_frobenius_even | 1706578 |
| 8 | `1099b1a38538` | `four_odd_perturbed_near_composed` | 4 | 2432430 | 0.000 | 35.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 5433581 |
| 9 | `6e0f9bc7da59` | `two_odd_perturbed_near_composed` | 2 | 18544000 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 39263563 |
| 10 | `191d50334214` | `mixed_even_odd_perturbed` | 2 | 1081080 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 1708564 |
| 11 | `52aceb854f0e` | `three_odd_perturbed_near_composed` | 3 | 207360 | 0.000 | 40.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 511029 |
| 12 | `bb26882d278e` | `four_odd_perturbed_near_composed` | 4 | 7539840 | 0.000 | 35.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 27231129 |
| 13 | `19ecd9d5550c` | `two_odd_perturbed_near_composed` | 2 | 3993600 | 0.000 | 60.000 | near_composed_support | 9359073 |
| 14 | `6ee2d4e0ec36` | `mixed_even_odd_perturbed` | 2 | 1530000 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 2627950 |
| 15 | `0632ae3f417f` | `three_odd_perturbed_near_composed` | 3 | 254304 | 0.000 | 40.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 213225 |
| 16 | `5d8e5c0048d9` | `four_odd_perturbed_near_composed` | 4 | 254304 | 0.000 | 15.000 | weak_near_composed_support | 213227 |
| 17 | `f540e183055e` | `mixed_even_odd_perturbed` | 2 | 2438000 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 4348190 |
| 18 | `dda6de4dc0e1` | `three_odd_perturbed_near_composed` | 3 | 268800 | 0.000 | 40.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 477603 |
| 19 | `152bacdf258d` | `four_odd_perturbed_near_composed` | 4 | 7918511 | 0.000 | 15.000 | weak_near_composed_support | 20401815 |
| 20 | `d587da6ff2ab` | `mixed_even_odd_perturbed` | 2 | 3692772 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 9202965 |
| 21 | `15fde057e976` | `three_odd_perturbed_near_composed` | 3 | 598752 | 0.000 | 40.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 640952 |
| 22 | `70c6e21c7395` | `four_odd_perturbed_near_composed` | 4 | 8164800 | 0.000 | 15.000 | weak_near_composed_support | 18299589 |
| 23 | `478ab1b32cad` | `mixed_even_odd_perturbed` | 2 | 3692775 | 0.000 | 80.000 | near_composed_support,no_long_cycle_witness_in_sample | 9202966 |
| 24 | `ee95964ca035` | `three_odd_perturbed_near_composed` | 3 | 1992216 | 0.000 | 40.000 | weak_near_composed_support,no_long_cycle_witness_in_sample | 6320163 |

Artifacts:
- Queue JSONL: `data/igp24/escape_lane_scout_20260709/r16_diversity/r16_diversified_candidate_queue.jsonl`
- Coefficients TXT: `data/igp24/escape_lane_scout_20260709/r16_diversity/r16_diversified_candidate_coefficients.txt`
- Hashes TXT: `data/igp24/escape_lane_scout_20260709/r16_diversity/r16_diversified_candidate_hashes.txt`
- Summary JSON: `data/igp24/escape_lane_scout_20260709/r16_diversity/r16_diversified_summary.json`
