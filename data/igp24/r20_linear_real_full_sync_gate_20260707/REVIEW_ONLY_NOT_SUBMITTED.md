# Submitted After Review

This packet was produced by the full-sync anti-basin gate for the
non-composed `r20_linear_real_roots_probe` lane.

No SAIR dry-run or live submission was performed when the packet was created.
It was later submitted through the credential-safe SAIR API helper after
explicit human approval.

Artifacts:

- Selected queue:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_selected_queue.jsonl`
- Coefficients:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_candidate_coefficients.txt`
- Planner summary:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_planner_summary.json`
- Planner report:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/anti_basin_planner_report.md`
- Dry-run response:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/r20_linear_real_sair_dry_run.json`
- Live submit response:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/r20_linear_real_sair_submit.json`
- First status poll:
  `data/igp24/r20_linear_real_full_sync_gate_20260707/r20_linear_real_sair_status_poll1.json`
- Accepted feedback import:
  `data/igp24/r20_linear_real_sair_accepted_feedback_20260707.json`

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

Submission result:

- Submission id: `sub_3557a403ea664b2f97ac059f9083b206`
- Submit response: 8 queued, 0 rejected
- First status poll: 8 accepted, 0 failed, 0 queued
- SAIR labels: 8 rows accepted as `24T25000|r=20`
- First scoring state: `scoreable=false`, `scoringStatus=pending`,
  `discSource=None`, and no `fieldDiscAbs` values yet
- Feedback ingest: appended 8 accepted alternates to the existing local
  `24T25000|r=20` pair and added no new pair keys

Updated lesson: local exact `r=20`, irreducibility, squarefree status, support
gcd 1, and non-even support all held, but this low-perturbation linear-real
lane still collapsed to the known `24T25000|r=20` basin. Do not submit more
from this lane without a stronger anti-`24T25000` discriminator or a
materially different construction.
