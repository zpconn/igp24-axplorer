# AXG-1.4 Training Summary

Status: four bounded CUDA provenance-aware target-r exports completed; no SAIR submission was made.

AXG-1.4 keeps the AXG-1.2/AXG-1.3 decimal coefficient target-r control-token path and adds export-time provenance plus stricter proposal gates for support shape, template family, perturbation mode, and basin fingerprint diversity.

## Commands

Representative GPU command template:

```bash
python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_target_r_conditioned \
  --target_r <12|16|20|24> \
  --target_r_conditioned_max_steps 7200 \
  --target_r_model_sample_attempts 3072 \
  --target_r_conditioned_temperature 1.15 \
  --target_r_conditioned_top_k -1 \
  --target_r_conditioned_unique_target 384 \
  --target_r_conditioned_generation_strategy mixed \
  --target_r_conditioned_avoid_even_support_like \
  --target_r_conditioned_require_support_gcd_one \
  --target_r_conditioned_basin_fingerprint_cap 8
```

## Results

| r | gpu s | max gpu % | avg gpu % | export rows | decoded | scored | valid | target survivors | survivor basins | selected | decision |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 12 | 230.4 | 88.0 | 76.8 | 97 | 22 | 22 | 21 | 14 | 6 | 3 | `hold_no_submission` |
| 16 | 235.9 | 87.0 | 77.6 | 124 | 40 | 40 | 40 | 22 | 8 | 3 | `hold_no_submission` |
| 20 | 241.1 | 86.0 | 76.1 | 122 | 35 | 35 | 34 | 18 | 8 | 4 | `reviewed_packet_ready_for_dry_run` |
| 24 | 231.3 | 89.0 | 76.5 | 140 | 39 | 39 | 39 | 28 | 12 | 2 | `hold_no_submission` |

Main GPU runtime: 938.742s (15.65m). The first r16 calibration run took 237.094s and is excluded from the main total.

## Decision

The r20 packet passed local anti-basin gates with four selected rows, two perturbation modes, two template families, and four basin fingerprints. It was not submitted because the fresh SAIR sync was partial at `submissions/{id}`, so submission/scoring state was incomplete.

r12, r16, and r24 stayed on hold because strict provenance gates found too few eligible rows and/or insufficient mode, family, or basin diversity.

## Comparison To AXG-1.3

AXG-1.3 found more raw target-r survivors (172 vs 82), but AXG-1.4 produced the first locally ready packet under strict provenance gates. The bottleneck moved from unknown model-sample provenance to live sync completeness plus exact review of the r20 packet.
