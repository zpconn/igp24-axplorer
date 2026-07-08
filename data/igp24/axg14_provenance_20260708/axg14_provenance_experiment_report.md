# AXG-1.4 Provenance-Aware Target-r Probe

AXG-1.4 added export-time provenance, support/basin filters, and proposal gates for template-family and basin-fingerprint diversity.

## Decision

- SAIR submission: `false`.
- Reason: the r20 packet passed local gates, but the fresh SAIR sync was partial (`submissions/{id}` service unavailable), so submission state was incomplete.

## Main Runs

| target | gpu_s | max_gpu | avg_gpu | scored | valid | target survivors | survivor basins | selected | decision | reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| r12 | 230.4 | 88.0 | 76.8 | 22 | 21 | 14 | 6 | 3 | `hold_no_submission` | only_3_eligible_rows_below_min_4; only_3_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity |
| r16 | 235.9 | 87.0 | 77.6 | 40 | 40 | 22 | 8 | 3 | `hold_no_submission` | only_3_eligible_rows_below_min_4; only_3_model_generated_rows_below_min_4; selected_rows_do_not_have_enough_basin_fingerprint_diversity |
| r20 | 241.1 | 86.0 | 76.1 | 35 | 34 | 18 | 8 | 4 | `reviewed_packet_ready_for_dry_run` | anti-basin gates passed |
| r24 | 231.3 | 89.0 | 76.5 | 39 | 39 | 28 | 12 | 2 | `hold_no_submission` | only_2_eligible_rows_below_min_4; only_2_model_generated_rows_below_min_4; selected_rows_do_not_have_multiple_perturbation_modes; selected_rows_do_not_have_enough_template_family_diversity; selected_rows_do_not_have_enough_basin_fingerprint_diversity |

## Aggregate

- Main GPU runtime: `938.742s` (`15.65m`).
- Total scored records: `136`.
- Total valid records: `134`.
- Total target-r survivors: `82`.
- Ready packets: `['r20']`.

## Interpretation

AXG-1.4 improved proposal explainability and produced one locally clean r20 packet. The stricter provenance filters reduced raw decoded volume versus AXG-1.3, but selected rows now carry mode, family, support, and basin evidence. The next bottleneck is SAIR sync completeness plus exact/live verification of the r20 packet, not another blind GPU run.
