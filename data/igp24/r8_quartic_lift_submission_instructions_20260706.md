# R8 Quartic-Lift Manual Submission Packet

Submit the coefficient file below to SAIR as plain polynomial lines:

`data/igp24/r8_quartic_lift_submission_coefficients_20260706.txt`

The file has 6 rows. Each row has exactly 25 comma-separated integer coefficients, no brackets, no labels, no claimed signatures, and no discriminants.

After SAIR returns verifier/scoring feedback, update:

`data/igp24/r8_quartic_lift_sair_feedback_template_20260706.csv`

Fill in the returned label, r, accepted/rejected status, reason, scoring discriminant, discriminant type, teams/k, pair score, solvability, and any notes. The JSON packet keeps the local proxy/structure status and intentionally marks exact labels and scores as pending until that feedback is available.

Status update: the user reported that SAIR accepted all six rows. The accepted labels are now recorded in the CSV template, the packet JSON, and `data/igp24/r8_quartic_lift_sair_accepted_feedback_20260706.json`. Scores and scoring discriminants are still pending.
