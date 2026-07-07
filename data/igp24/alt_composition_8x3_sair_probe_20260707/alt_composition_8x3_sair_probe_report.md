# IGP24 8x3 SAIR Probe Packet

Small reviewed verification packet for the alternate-composition `8x3|r=24` lane.

- This is `8x3`, not `6x4`.
- This is not exact even `g(x^2)` support.
- This is not the odd-escaped `6x4` tower lane.
- This is a small verification probe, not a widening run.
- The packet builder did not call SAIR, Magma, PARI, the network, GPU, or training code.

- Selected rows: 8
- Source ranks: `[1, 2, 3, 4, 5, 6, 7, 8]`
- Height range: 21465432 to 47192058

| row | source rank | hash | family | height |
| ---: | ---: | --- | --- | ---: |
| 1 | 1 | `3207fcbad6f7` | `8x3|s=8|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:1` | 21465432 |
| 2 | 2 | `f6d01d13d4d0` | `8x3|s=8|mode=outer_constant_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:1` | 21465432 |
| 3 | 3 | `88f1e7761002` | `8x3|s=8|mode=outer_constant_shift|levels=-3,-2,-1,1,2,3,4,5|outer_y=0:10` | 21465432 |
| 4 | 4 | `2c8838b3f843` | `8x3|s=8|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-10` | 21465432 |
| 5 | 5 | `438b2f438a1e` | `8x3|s=8|mode=outer_constant_shift|levels=-2,-1,1,2,3,4,5,6|outer_y=0:3` | 32548464 |
| 6 | 6 | `687873704268` | `8x3|s=8|mode=outer_constant_shift|levels=-2,-1,1,2,3,4,5,6|outer_y=0:-2` | 32548464 |
| 7 | 7 | `ab9559414dc6` | `8x3|s=9|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-1` | 47192058 |
| 8 | 8 | `dacbce3e07e4` | `8x3|s=9|mode=outer_constant_shift|levels=-5,-4,-3,-2,-1,1,2,3|outer_y=0:-10` | 47192058 |

## SAIR Submission

- Submission id: `sub_25c17affdf3c4505a8f10cfda2d94217`
- Submit response: `data/igp24/alt_composition_8x3_sair_probe_20260707/alt_composition_8x3_sair_submit_response.json`
- Dry-run response: `data/igp24/alt_composition_8x3_sair_probe_20260707/alt_composition_8x3_sair_dry_run_response.json`
