# Review Only - Not Submitted

This packet was produced by the full-sync anti-basin gate for the
non-composed `r20_linear_real_roots_probe` lane.

No SAIR dry-run or live submission was performed in this goal. The gate marked
the packet as ready for a future dry-run, but submission requires explicit
human approval.

Artifacts:

- Selected queue:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_selected_queue.jsonl`
- Coefficients:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_candidate_coefficients.txt`
- Planner summary:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_planner_summary.json`
- Planner report:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_planner_report.md`

Gate summary:

- Candidate rows: 8
- Eligible rows: 8
- Selected rows: 8
- Recommendation status: `reviewed_packet_ready_for_dry_run`
- Source commit recorded by gate: `1230415e45c302abd2948e8fdf54d7a701ac7868`
- Safety flags: no GPU training, no model training, no SAIR submission, no
  SAIR dry-run, no Magma/PARI, and no API key recorded

Selected perturbation modes:

- `single_low_coefficient_break`: 4
- `three_low_coefficient_break`: 4

Local validation confirmed that all 8 selected rows have exactly 25 integer
coefficients, nonzero constant term, leading coefficient 1, coefficient gcd 1,
exact local `r=20`, irreducible status, squarefree status, support gcd 1,
non-even support, unique canonical hashes, distinct mod-p signatures, and no
anti-basin risk reasons.

Next action, only after explicit human approval: run a SAIR dry-run or live
submission using the coefficients file above, then feed accepted labels and
scoring status back into the local ledgers.
