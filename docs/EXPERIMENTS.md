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

## Fresh Pair-Diversity Queue

The 2026-07-06 fresh queue tested whether a small bounded local generation
pass could find new structural families instead of more variants of the three
already verified expected pairs.

Fresh source artifact:

- `/tmp/igp24_fresh_pair_bench_20260706`

Command:

```bash
python3 scripts/igp24_benchmark.py \
  --strategies sparse,structured,quartic_lift,fixed_sparse_template,mix_r4_dual_balanced \
  --seeds 2601,2602 \
  --target_rs 4 \
  --coeff_bound 4 \
  --gensize 16 \
  --pop_size 8 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 1 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_fresh_pair_bench_20260706
```

The sweep completed 10 tiny CPU runs and wrote 217 ledger rows. The r4 matches
were concentrated in `mix_r4_dual_balanced` (24/37 ledger rows),
`quartic_lift` (23/40), and `fixed_sparse_template` (15/48), with a small
`sparse` contribution (3/49). The tiny `structured` runs produced no r4 rows.

Diagnostic and audit artifacts:

- `/tmp/igp24_fresh_pair_diagnostic_20260706`
- `/tmp/igp24_fresh_pair_structure_audit_20260706`
- `/tmp/igp24_fresh_pair_diversity_queue_20260706`

The non-generic diagnostic loaded 217 rows, diagnosed 59 target-r rows, and
selected 40. The local structure audit confirmed 3 square-discriminant claims
and 23 exact-composed-support claims, with no refutations. Primary block
divisor counts were `2:16`, `3:6`, `6:1`, and `None:17`.

The final diversity queue used exact-label-aware planning with:
`--family_key_mode full`, `--include_unmatched`, `--exclude_verified_hashes`,
`--max_per_family_label 1`, and `--prefer_unmatched`. It selected 16 unique
fresh hashes with zero overlap against the 25 verified feedback hashes:
one controlled `24T24979` feedback-family row and 15 unmatched rows.

Interpretation: the most interesting fresh rows were not proven new scoreable
pairs at queue-construction time, but they were better verification targets
than repeating the old three expected pairs. They included
square-discriminant divisor-6/base-degree-4 evidence, fixed-template square
divisor-2/base-degree-12 evidence, divisor-3/base-degree-8 coverage, sparse
divisor-2/base-degree-12 coverage, and non-composed sparse coverage.

## Fresh Online Magma Verification

The 2026-07-06 fresh queue was partially exact-verified through saved online
Magma calculator output.

Source and provenance artifacts:

- Queue:
  `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl`
- Manual calculator artifacts:
  `/tmp/igp24_fresh_pair_manual_verify_20260706/online_magma_manual`
- Parsed online Magma results:
  `/tmp/igp24_fresh_pair_verified_20260706/online_magma_manual`
- Fresh exact-label feedback:
  `/tmp/igp24_fresh_pair_verified_label_feedback_20260706`
- Fresh submission plan:
  `/tmp/igp24_fresh_pair_submission_plan_20260706`
- Raw saved Magma calculator XML:
  `data/igp24/online_magma_manual_output_*_20260706.xml`

Local MAGMA was unavailable, so the offline verifier helper stayed in dry-run
mode for local execution. The helper generated one-candidate calculator
scripts and parsed a saved pasted-output JSONL. The helper itself did not make
network calls; the raw XML files were collected separately by bounded
one-candidate `curl` POSTs to the online calculator and then parsed from disk.
No SAIR submission or API call was made.

Parsing results:

- 16 fresh queue rows selected.
- 12 rows verified; 4 rows returned a calculator-disabled response.
- All 12 verified rows were degree 24 and irreducible.
- No verified row was generic `24T25000`.

| exact label | count | structural source |
| --- | ---: | --- |
| `24T24979` | 5 | nonsquare divisor-2/base-degree-12 rows |
| `24T24759` | 3 | divisor-3/base-degree-8 rows |
| `24T24970` | 2 | square fixed-template divisor-2/base-degree-12 rows |
| `24T9683` | 1 | square divisor-6/base-degree-4 `quartic_lift` row |
| `24T24648` | 1 | fixed-template divisor-3/base-degree-8 row |

Pending rows from calculator-disabled responses:

- `198ac88fa216`
- `20b35a3fd41d`
- `88437a372524`
- `0f3ad8602d89`

The refreshed local/file-only submission planner selected one representative
per expected pair:

| pair | hash | discriminant source |
| --- | --- | --- |
| `24T24979|r=4` | `981a94588aab` | `log_abs_discriminant` |
| `24T24759|r=4` | `4be66a510402` | `log_abs_discriminant` |
| `24T9683|r=4` | `9c45c5493e7a` | `log_abs_discriminant` |
| `24T24970|r=4` | `a97caa584baa` | `log_abs_discriminant` |
| `24T24648|r=4` | `2289d8a5e700` | `log_abs_discriminant` |

Important caveats:

- The discriminant ordering is still polynomial log-discriminant proxy
  evidence, not exact `nfdisc`.
- The `r=4` values come from local candidate `real_root_count`; the saved
  online Magma rows do not yet carry a Magma-computed signature field.
- The planner writes manual review artifacts only and has
  `scoreable_claims=false`.

Interpretation: the novelty pressure worked. The fresh queue found two exact
labels not present in the previous 25 verified rows, `24T9683` and `24T24648`,
and expanded the planning set from three to five expected pairs. The next
verification work should retry the four pending rows and add exact signature,
exact `nfdisc`, and official baseline comparison before submission decisions.

## Five-Representative Baseline Pass

The official frozen baseline CSV was imported from
`https://competition.sair.foundation/downloads/igp24/lmfdb_baseline.csv` and
saved as `data/igp24/lmfdb_baseline.csv`. The planner loaded 1,480 rows and
collapsed them into 622 official `(label, r)` pairs.

Updated exact-evidence helpers now:

- emit `IGP24_SIGNATURE` in generated Magma scripts,
- emit parseable PARI/GP `IGP24_NFDISC_ABS` markers,
- parse saved PARI/GP `nfdisc` output into `pari_nfdisc_results.jsonl`,
- merge exact label, exact `r`, and exact `nfdisc` evidence by candidate hash,
- and report exact-`r`/exact-`nfdisc` status counts.

Focused validation passed:

```bash
env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q \
  tests/test_igp24_offline_verify.py tests/test_igp24_submission_plan.py
```

Result: 19 passed in 1.34s.

The five-representative artifact pass was regenerated from source commit
`88bb0ed6b5b31cd9e81198a91b22754a933e9766`:

- `/tmp/igp24_submission_grade_five_20260706/offline_verification_manifest.json`
- `/tmp/igp24_submission_grade_five_20260706/pari_input.gp`
- `/tmp/igp24_submission_grade_five_20260706/pari_nfdisc_results.jsonl`
- `/tmp/igp24_submission_grade_five_20260706/online_magma_manual/copy_paste_scripts`

Local verifier availability remained unchanged: no local `gp`, no local
`magma`, no PARI execution, no Magma execution, no SAIR submission/API call,
and no GPU/model search.

Baseline-aware plan output:

- `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_plan.jsonl`
- `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_candidates.txt`
- `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_plan_summary.json`
- `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_plan_report.md`

Status counts:

- `baseline_status_counts={"non_baseline_candidate": 5}`
- `scoreability_status_counts={"new_pair_needs_exact_r": 5}`
- `exact_r_status_counts={"candidate_proxy": 5}`
- `exact_nfdisc_status_counts={"missing": 5}`

Interpretation: the five selected expected pairs are not in the official
baseline, which is promising for eventual score. They are not submission-grade
yet because the exact Magma `r` marker and exact number-field discriminant are
still missing.

The four calculator-disabled rows were not automatically retried online. A
manual retry packet was prepared at `/tmp/igp24_pending_four_retry_20260706`
instead. It contains one-candidate Magma copy/paste scripts with
`IGP24_SIGNATURE` and PARI/GP input with `IGP24_NFDISC_ABS` for:

- `198ac88fa216`
- `20b35a3fd41d`
- `88437a372524`
- `0f3ad8602d89`

That packet is dry-run/manual-only: no local Magma, no local PARI, no SAIR/API
call, no network submission, and no GPU/model search.

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
