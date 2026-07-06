# IGP24 Experiment Notes

This file keeps benchmark and verification detail out of the public README
while preserving the current experimental state. The complete working log is in
`TODO_IGP24.md`; design rationale lives in `NOTES_IGP24.md`.

## Verified Non-Generic Queue

The most important current result is the 2026-07-05 non-generic verification
queue.

Source artifacts:

- Diagnostic shortlist:
  `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl`
- Manual verification queue:
  `/tmp/igp24_non_generic_manual_queue_20260705`
- Local structure audit:
  `/tmp/igp24_non_generic_structure_audit_20260705`
- Parsed online Magma results:
  `/tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual`
- Raw saved Magma calculator XML:
  `data/igp24/online_magma_manual_output_*_20260705.xml`

The queue contains 25 target-`r=4` candidates selected for non-generic proxy
evidence: exact composed support, square discriminants, sparse support, and
small-prime modular-pattern signals.

Local exact-algebra audit results:

- 25/25 rows audited.
- 18/18 square-discriminant claims confirmed.
- 25/25 exact composed-support claims confirmed.
- 24 rows have primary block divisor `2` and base degree `12`.
- 1 row has primary block divisor `3` and base degree `8`.

Magma verification results:

| exact label | count | structural source |
| --- | ---: | --- |
| `24T24970` | 18 | square-discriminant divisor-2 composed-support family |
| `24T24979` | 6 | nonsquare divisor-2 composed-support tail |
| `24T24759` | 1 | divisor-3/base-degree-8 coverage row |

Every verified row was degree 24 and irreducible. None were `24T25000`.

Exact-label feedback artifacts:

- Joined feedback:
  `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl`
- Representatives:
  `/tmp/igp24_verified_label_feedback_20260705/verified_label_representatives.jsonl`
- Summary:
  `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback_summary.json`
- Report:
  `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback_report.md`

The feedback join mapped exact labels back to local structure:

- Square-discriminant divisor-2/base-degree-12 rows: 18 `24T24970`.
- Nonsquare divisor-2/base-degree-12 rows: 6 `24T24979`.
- Divisor-3/base-degree-8 row `27eaf2acac9f`: 1 `24T24759`.

Exact-label-aware shortlist artifacts:

- Shortlist:
  `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist.jsonl`
- Coefficients:
  `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist_coefficients.txt`
- Summary:
  `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist_summary.json`
- Report:
  `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist_report.md`

The planner selected a 12-row family-balanced queue using explicit quotas
`24T24970:8,24T24979:2,24T24759:1` and one fill row. The selected family
counts were 9 `24T24970`, 2 `24T24979`, and 1 `24T24759`. A guard run with
`--exclude_verified_hashes` selected 0 rows on this already verified audit,
which is the expected behavior for future fresh-candidate audits.

Interpretation: the non-generic diagnostic and local structure audit were
strong predictors for this queue. The next search work should feed exact labels
back into shortlist analysis and deliberately expand composed-support families,
especially the divisor-2 `quartic_lift` branch while keeping a small divisor-3
coverage track.

Submission planning artifacts:

- Plan:
  `/tmp/igp24_submission_plan_20260705/submission_plan.jsonl`
- Candidate text:
  `/tmp/igp24_submission_plan_20260705/submission_candidates.txt`
- Summary:
  `/tmp/igp24_submission_plan_20260705/submission_plan_summary.json`
- Report:
  `/tmp/igp24_submission_plan_20260705/submission_plan_report.md`

The submission planner joined the 25 saved verified rows to the diagnostic and
exact-label shortlist artifacts, then collapsed them to one representative per
expected `(24Tt, r)` pair. It selected three candidate lines:
`24T24970|r=4`, `24T24979|r=4`, and `24T24759|r=4`. The remaining 22 rows were
suppressed as duplicate expected pairs.

No baseline CSV was supplied, so all three selected rows remain
`baseline_unknown`; they should not be described as scoreable until official
baseline and exact discriminant evidence is available. The selected
discriminant source is currently `log_abs_discriminant`, a polynomial
discriminant proxy, not exact `nfdisc`. The `r=4` value comes from candidate
`real_root_count`, because the saved online-Magma exact-label rows do not carry
a Magma-computed `r`.

## GPU And Split Export Findings

GPU training and sample export are useful only when decoupled from CPU-heavy
proxy scoring and local search.

Important observations from the 2026-07-04 GPU probes:

- Tiny CUDA smoke: PyTorch saw the RTX 5090 and `train.py` logged
  `device: cuda`.
- Integrated train/sample/scoring runs did not visibly load the GPU because
  post-epoch CPU scoring and local search dominated.
- Train-only utilization probe loaded the GPU: max monitored utilization 95%.
- Split export mode loaded the GPU and wrote unscored samples for later CPU
  scoring.
- Medium split export reached high utilization but suffered heavy duplicate
  collapse in some sampler settings.
- Dedup-aware export control reduced duplicate export waste and gave cleaner
  CPU-scored handoffs.

Current recommendation: keep CPU proxy scoring, shortlist export, and exact
verification handoff as the main pipeline. Use GPU training/sample export only
as a bounded, audited sampler path. Do not start a larger GPU run until the
verified exact labels are wired back into candidate selection.

## CPU Benchmark Findings

The CPU benchmark helper compares generation strategies, target real-root
counts, score distributions, validity rates, and local-search behavior.

Broad conclusions from the current logs:

- `structured` and `sparse` were the strongest early small-sample baselines.
- `four_real_seed` improved target-`r=4` yield.
- `quartic_lift` gave strong target-`r=4` proxy quality and later produced
  exact non-generic labels in the verified queue.
- `fixed_sparse_template` is useful for controlled support experiments but
  needs careful dedup-aware sampling when used with GPU export.
- The default `mixed` strategy remains conservative; experimental families are
  opt-in.

Benchmark commands and full result tables are recorded in `TODO_IGP24.md`.

## Key Helper Scripts

- `scripts/igp24_benchmark.py`: repeated short CPU benchmarks.
- `scripts/igp24_gpu_smoke.py`: CUDA readiness smoke.
- `scripts/igp24_gpu_sampler_probe.py`: split GPU train/sample/export probes.
- `scripts/igp24_score_sample_export.py`: CPU scoring for exported samples.
- `scripts/igp24_merge_scored_exports.py`: merge and deduplicate scored runs.
- `scripts/igp24_export_diversity_diagnostic.py`: raw export diversity checks.
- `scripts/igp24_seed_triage.py`: cheap dedup-aware seed triage.
- `scripts/igp24_non_generic_diagnostic.py`: proxy non-generic shortlist.
- `scripts/igp24_queue_structure_audit.py`: exact local algebra structure audit.
- `scripts/igp24_offline_verify.py`: exact verification handoff and parsing.
- `scripts/igp24_verified_label_feedback.py`: exact-label feedback summaries.
- `scripts/igp24_exact_label_shortlist.py`: feedback-family shortlist planner.
- `scripts/igp24_submission_plan.py`: one-per-pair manual submission planning.

## Reproducibility Notes

Most historical artifacts are under `/tmp` and are not committed. Committed
verification provenance includes the raw online Magma XML files in
`data/igp24/`.

For each experiment, prefer recording:

- source commit,
- command line,
- random seed,
- input artifact paths,
- output directory,
- verifier provenance,
- exact label status if any,
- and whether the run touched GPU, network, Magma, PARI, or SAIR paths.
