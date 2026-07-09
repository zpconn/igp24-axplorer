# IGP24 R24 Tower Odd-Escape Candidate Queue

CPU-only local r24 odd-perturbed tower escape probe. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 220
- Valid r=24 candidates: 27
- Selected rows: 24
- Queue status: `api_dry_run_ready`
- Selected mode counts: `{"single_odd_tower_escape": 24}`
- Selected inner-s counts: `{"10": 5, "11": 3, "13": 1, "6": 3, "7": 3, "8": 5, "9": 4}`
- Rejected counts: `{"real_root_count_mismatch": 184, "reducible_over_q": 9}`

Anti-basin rationale: every selected row has odd support, support gcd 1, and is not an exact even outer-constant-shift tower.

| rank | hash | mode | s | levels | odd perturbations | height | log disc |
| ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| 1 | `f48ecb66049a` | `single_odd_tower_escape` | 6 | `-1,-2,-3,-4,-5,-8` | `1:1` | 372258 | 165.412 |
| 2 | `d6da4886246d` | `single_odd_tower_escape` | 6 | `-1,-3,-4,-5,-6,-7` | `1:-1` | 507209 | 155.835 |
| 3 | `a256a3c49815` | `single_odd_tower_escape` | 6 | `-1,-2,-3,-6,-7,-8` | `1:3` | 527008 | 180.888 |
| 4 | `48eccac8e215` | `single_odd_tower_escape` | 7 | `-1,-2,-3,-4,-6,-7` | `1:1` | 689990 | 170.389 |
| 5 | `ddbda553f944` | `single_odd_tower_escape` | 7 | `-1,-2,-3,-4,-6,-9` | `1:1` | 771498 | 190.915 |
| 6 | `217e51b89373` | `single_odd_tower_escape` | 7 | `-1,-2,-4,-5,-8,-12` | `1:2` | 1255559 | 224.204 |
| 7 | `af0c4ce10dfc` | `single_odd_tower_escape` | 8 | `-1,-2,-3,-4,-9,-13` | `3:-1` | 1911011 | 232.929 |
| 8 | `87934ccf2357` | `single_odd_tower_escape` | 8 | `-1,-2,-3,-5,-10,-12` | `1:1` | 2095316 | 238.353 |
| 9 | `bf1e4877b6f1` | `single_odd_tower_escape` | 8 | `-1,-2,-3,-5,-11,-13` | `1:2` | 2345021 | 245.266 |
| 10 | `6a1878ef0a3d` | `single_odd_tower_escape` | 8 | `-1,-2,-3,-5,-10,-15` | `3:-2` | 2441753 | 251.968 |
| 11 | `62afb19a0df7` | `single_odd_tower_escape` | 8 | `-1,-2,-3,-4,-12,-15` | `3:-1` | 2530874 | 246.211 |
| 12 | `656c513ef280` | `single_odd_tower_escape` | 9 | `-1,-2,-3,-4,-6,-14` | `1:-2` | 2744604 | 225.530 |
| 13 | `e0d34ed6e496` | `single_odd_tower_escape` | 9 | `-1,-2,-3,-4,-12,-16` | `1:1` | 4051421 | 257.776 |
| 14 | `ffc7dd1d7b25` | `single_odd_tower_escape` | 9 | `-1,-2,-3,-4,-12,-16` | `3:2` | 4051421 | 256.683 |
| 15 | `5f8964cecf2e` | `single_odd_tower_escape` | 9 | `-1,-2,-3,-4,-13,-17` | `1:-2` | 4461505 | 262.661 |
| 16 | `7e4f69593117` | `single_odd_tower_escape` | 11 | `-1,-2,-3,-4,-6,-9` | `1:1` | 5335506 | 205.743 |
| 17 | `77923a89eb09` | `single_odd_tower_escape` | 10 | `-1,-2,-3,-4,-7,-19` | `1:1` | 5380700 | 252.073 |
| 18 | `e549545e24d8` | `single_odd_tower_escape` | 10 | `-1,-2,-3,-4,-7,-19` | `3:1` | 5380700 | 250.840 |
| 19 | `1c7f1274a9c9` | `single_odd_tower_escape` | 10 | `-1,-2,-3,-4,-9,-19` | `1:-3` | 5826200 | 262.921 |
| 20 | `292acab2e97e` | `single_odd_tower_escape` | 10 | `-1,-2,-3,-4,-7,-22` | `1:2` | 5894150 | 257.966 |
| 21 | `c814e1de3e8d` | `single_odd_tower_escape` | 10 | `-1,-2,-3,-4,-10,-21` | `3:-1` | 6529424 | 271.097 |
| 22 | `0baeb1aef967` | `single_odd_tower_escape` | 11 | `-1,-2,-3,-4,-6,-25` | `1:-1` | 9325426 | 259.049 |
| 23 | `96a7bd7e066e` | `single_odd_tower_escape` | 11 | `-1,-2,-3,-4,-8,-29` | `1:-3` | 11081730 | 278.043 |
| 24 | `d2da75f6718f` | `single_odd_tower_escape` | 13 | `-1,-2,-3,-4,-7,-13` | `1:1` | 14068418 | 240.623 |

Caveat: these rows have local exact `r=24`, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
