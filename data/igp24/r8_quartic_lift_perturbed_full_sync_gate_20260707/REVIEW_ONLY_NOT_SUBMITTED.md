# Review-Only Gate Packet, Later Submitted After Approval

Update: this packet was later submitted only after explicit user approval on
2026-07-07. Submission artifacts:

- Dry-run response:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/r8_quartic_lift_perturbed_sair_dry_run.json`
- Live submit response:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/r8_quartic_lift_perturbed_sair_submit.json`
- Status poll:
  `data/igp24/r8_quartic_lift_perturbed_full_sync_gate_20260707/r8_quartic_lift_perturbed_sair_status_poll1.json`
- Joined accepted-feedback artifact:
  `data/igp24/r8_quartic_lift_perturbed_sair_accepted_feedback_20260707.json`

SAIR accepted all 10 rows. Labels were 9 rows as `24T25000|r=8` and 1 row as
`24T24979|r=8`; all 10 had discriminant/scoring status pending on the first
two polls.

This packet was produced by the full-sync anti-basin gate for the opt-in
`r8_quartic_lift_perturbed` lane.

At gate-generation time, no SAIR dry-run or live submission was performed. The
gate marked the packet as ready for a future dry-run, but that earlier
objective explicitly forbade submitting or dry-running these rows.

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

Post-submission lesson: off-core perturbation successfully escaped the local
pure `g(x^6)` support obstruction, but not the tracked high-label basin. Do not
widen this exact perturbed r8 lane blindly until scores/discriminants return
or a stronger label-steering discriminator is added.
