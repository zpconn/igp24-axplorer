# Review Only - Not Submitted

This packet was produced by the full-sync anti-basin gate for the opt-in
`r8_quartic_lift_perturbed` lane.

No SAIR dry-run or live submission was performed in this goal. The gate marked
the packet as ready for a future dry-run, but the objective explicitly forbade
submitting or dry-running these rows.

Artifacts:

- Selected queue:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/anti_basin_selected_queue.jsonl`
- Coefficients:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/anti_basin_candidate_coefficients.txt`
- Planner summary:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/anti_basin_planner_summary.json`
- Planner report:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/anti_basin_planner_report.md`

Gate summary:

- Candidate rows: 51
- Eligible rows: 51
- Selected rows: 10
- Recommendation status: `reviewed_packet_ready_for_dry_run`
- Source commit recorded by gate: `43774140844106d89871aa813888e4e23b100d7d`
- Safety flags: no GPU training, no model training, no SAIR submission, no
  SAIR dry-run, no Magma/PARI, and no API key recorded

Selected perturbation modes:

- `odd_pair_off_core`: 4
- `odd_single_off_core`: 4
- `odd_triple_off_core`: 2

Local validation confirmed that all 10 selected rows have exactly 25 integer
coefficients, nonzero constant term, leading coefficient 1, coefficient gcd 1,
exact local `r=8`, irreducible status, squarefree status, support gcd 1,
non-even support, and no anti-basin risk reasons.

Next action, only after explicit human approval: run a SAIR dry-run or live
submission using the coefficients file above, then feed accepted labels and
scoring status back into the local ledgers.
