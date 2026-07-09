# IGP24 4x6 Alternate Composition Diagnostic

CPU-only local 4x6 alternate-composition diagnostic. It does not train models, use a GPU sampler, call SAIR/Magma/PARI/network APIs, or submit anything.

- Trials attempted: 220
- Valid candidates: 0
- Selected rows: 0
- Queue status: `diagnostic_too_few_valid_rows`
- Selected r counts: `{}`
- Selected mode counts: `{}`
- Valid mode counts: `{}`
- Rejected counts: `{"coefficient_height_exceeds_bound": 160, "even_support_g_x_squared_like,support_gcd_not_one": 18, "not_squarefree": 1, "real_root_count_not_target_bucket": 33, "reducible_over_q": 8}`

## Submission Readiness

- Status: `diagnostic_only_not_ready`
- Planner scoring recommended: `False`
- Submitted by this tool: `False`
- Reason: Too few locally valid/diverse 4x6 rows survived local gates.

## Selected Rows

| rank | hash | r | mode | family | height | log disc |
| ---: | --- | ---: | --- | --- | ---: | ---: |

Caveat: these rows have local exact real-root, irreducible, and squarefree checks only. The helper claims no exact `24Tt` label.
