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
and expanded the planning set from three to five expected pairs. The remaining
four calculator-disabled rows were resolved in the follow-up retry pass below.

## Pending-Four Retry Resolution

The four calculator-disabled fresh rows were retried with the fixed PARI/GP
and Magma script emitters. PARI/GP ran from the user-space executable
`/tmp/pari-gp-local/usr/bin/gp`, and the free online Magma calculator checked
one candidate at a time. The integrated artifact is
`/tmp/igp24_pending_four_retry_fixed_parsed_20260706`; raw calculator XML is
preserved under
`/tmp/igp24_pending_four_retry_fixed_20260706/online_magma_manual/checked_xml`.

All four rows verified as degree 24, irreducible, with exact `r=4`; PARI
`nfdisc` matched the existing SymPy exact `nfdisc` values.

| pair | hash | exact nfdisc | review class |
| --- | --- | ---: | --- |
| `24T24648|r=4` | `198ac88fa216` | 574784031237204017882937809358206854761709291280481792 | accepted-pair duplicate, not improved |
| `24T24759|r=4` | `20b35a3fd41d` | 34458474498929325531941539978424194438259580701589504 | accepted-pair duplicate, not improved |
| `24T25000|r=4` | `0f3ad8602d89` | 76732333707577227709347318376172659671040 | actionable generic `S24` new pair |
| `24T25000|r=4` | `88437a372524` | 32520883031235746009482154821400124768241521 | duplicate pending pair, lower ranked |

The scoreability review helper is `scripts/igp24_scoreability_review.py`.
Output was written to `/tmp/igp24_pending_four_scoreability_review_20260706`.
It compares exact labels/signatures, PARI `nfdisc`, the frozen baseline, the
five already accepted pairs, and duplicate pending pairs. The clean manual
coefficient file for the single actionable row is:
`/tmp/igp24_pending_four_scoreability_review_20260706/submission_coefficients.txt`.

Interpretation: `24T25000` is the generic full symmetric group, so it is less
interesting as search guidance than the non-generic labels. However, the
official scoring rules score verified `(24Tt, r)` pairs outside the frozen
baseline, and `24T25000|r=4` is absent from the frozen baseline. The one-line
package is therefore a valid incremental manual-submission candidate. The two
accepted-pair duplicates do not improve our already accepted discriminants.

The one-line `24T25000|r=4` submission was later accepted by the SAIR verifier,
so local planning now treats it as a sixth accepted/credited pair. The next
queue work deliberately shifts back to non-generic discovery rather than more
generic `S_24` variants.

## Next Non-Generic Queue After Six Accepted Pairs

The next queue pass is local/file-only. It uses saved scored/search artifacts,
the official frozen baseline CSV, exact-label feedback from prior Magma
checks, and a committed local pair-status ledger. It does not run GPU/model
search, CPU generation/search loops, Magma/PARI, online requests, or SAIR
submissions.

Committed helper artifacts:

- Pair-status ledger: `data/igp24/pair_status_20260706.json`
- Planner: `scripts/igp24_next_verification_queue.py`
- Focused tests: `tests/test_igp24_next_verification_queue.py`

The ledger records six accepted local pairs:
`24T9683|r=4`, `24T24979|r=4`, `24T24759|r=4`, `24T24970|r=4`,
`24T24648|r=4`, and `24T25000|r=4`. For the first five accepted rows, it also
records the user-reported leaderboard scoring discriminants, `D0` values,
discriminant type, team count `k`, and pair-score text.

Source pass:

- Diagnostic output: `/tmp/igp24_next_non_generic_diagnostic_20260706`
- Structure audit: `/tmp/igp24_next_non_generic_structure_audit_20260706`
- Queue output: `/tmp/igp24_next_non_generic_queue_20260706`
- Manual review packet:
  `/tmp/igp24_next_non_generic_manual_queue_20260706`

The broader diagnostic scanned saved artifacts only:
`/tmp/igp24_fresh_pair_bench_20260706`,
`/tmp/igp24_r4_second_confirm_20260704`, and
`/tmp/igp24_r4_dual_quality_confirm_20260704`. It loaded 5,087 saved records,
diagnosed 1,919 target-`r=4` records, and selected 160. The structure audit
then confirmed 21 square-discriminant claims and 136 exact-composed-support
claims, with no refutations.

The ledger-aware planner loaded 622 official baseline pairs and six accepted
local ledger pairs. It annotated 160 audited rows, found 24 eligible rows, and
selected all 24. Filter counts were:

```text
accepted_family_hint: 95
known_exact_accepted_pair: 41
survived_accepted_pending_baseline_generic_filters: 24
```

All 24 selected rows are unmatched by prior exact-label feedback. Strategy
counts are 16 `quartic_lift` rows and 8 `four_real_seed` rows. The manual
review packet contains 24 one-candidate online-Magma copy/paste scripts, a
coefficient file, PARI input, manifest, and dry-run reports. Local Magma and
PARI were unavailable in this pass, and neither tool was executed.

Interpretation: this is a better waiting-period task than more GPU training.
The six accepted pairs are already credited; the next score bottleneck is
discovering another exact non-baseline `(24Tt, r)` pair. These 24 rows are not
submission candidates yet, but they are a clean manual-verification queue
designed to avoid already accepted, baseline, generic, and duplicate-hash rows.

Follow-up exact fallback and score-aware triage:

- Exact fallback artifact:
  `/tmp/igp24_next_non_generic_exact_fallback_20260706`
- Score-aware triage artifact:
  `/tmp/igp24_next_non_generic_score_triage_20260706`
- New helper: `scripts/igp24_score_aware_triage.py`
- Focused tests: `tests/test_igp24_score_aware_triage.py`

No pasted online-Magma results were present for this queue:
`online_magma_manual_results.jsonl` had 0 rows and the pasted-output template
still had 24 blank `pasted_output` fields. A local exact fallback pass was run
instead, using the user-space PARI/GP binary at `/tmp/pari-gp-local/usr/bin/gp`
plus explicit SymPy fallback evidence. It produced:

```text
pari_nfdisc_status_counts={"nfdisc_ok": 24}
sympy_nfdisc_status_counts={"nfdisc_ok": 24}
sympy_signature_status_counts={"signature_ok": 24}
magma_status_counts={"dry_run": 24}
```

The score-aware triage then reviewed all 24 rows against the official baseline
and the local accepted-pair ledger. Because exact Magma labels were still
missing, all rows were classified as `exact_result_missing`:

```text
reviewed_rows=24
verified_rows=0
pending_exact_label_rows=24
failed_rows=0
submission_grade_rows=0
classification_counts={"exact_result_missing": 24}
exact_r_status_counts={"ok": 24}
exact_nfdisc_status_counts={"ok": 24}
```

Interpretation: exact `r` and exact `nfdisc` are no longer the bottleneck for
this queue; exact Magma labels are. The triage helper records the SAIR scoring
lesson explicitly: the first accepted five rows all scored `<0.0001`, so
accepted-pair duplicates should only be considered if their exact
discriminants improve materially. No manual submission package was built from
this queue yet. The next required action is manual Magma verification using
`/tmp/igp24_next_non_generic_score_triage_20260706/manual_magma_checklist.md`.

SAIR acceptance feedback, scores pending:

- Feedback artifact:
  `data/igp24/sair_accepted_label_feedback_20260706_next_queue.json`
- Refreshed triage artifact:
  `/tmp/igp24_next_non_generic_sair_triage_20260706`
- Command:
  `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_aware_triage.py --queue_jsonl /tmp/igp24_next_non_generic_queue_20260706/next_verification_queue.jsonl --offline_dir /tmp/igp24_next_non_generic_exact_fallback_20260706 --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --output_dir /tmp/igp24_next_non_generic_sair_triage_20260706`

The user manually submitted the bracketless coefficient file from the exact
fallback artifact, and the SAIR verifier accepted all 24 rows. Rows 1-2 were
reported as `24T24979`, rows 3-24 as `24T25000`, all with `r=4`. Scores were
not yet available when this was recorded.

The refreshed score-aware triage found:

```text
reviewed_rows=24
verified_rows=24
pending_exact_label_rows=0
failed_rows=0
submission_grade_rows=0
labels_found_counts={"24T24979": 2, "24T25000": 22}
classification_counts={"accepted_pair_duplicate": 2, "generic_24T25000": 22}
exact_label_source_counts={"sair_accepted_label_feedback": 24}
accepted_pair_status_counts={"accepted_pair_duplicate_not_improved": 23, "accepted_pair_minor_discriminant_improvement": 1}
```

Interpretation: the queue was verifier-clean but not score-aware
submission-grade. The unmatched structural-proxy strategy did not find a new
pair; it mostly collapsed to generic `S24`, plus two already accepted
`24T24979|r=4` duplicates. Row 6 (`0ec921751862`) is a lower exact-nfdisc
`24T25000|r=4` accepted alternate with ratio about `0.596` versus the current
ledger representative, but it remains score-pending because SAIR can score by a
mixed discriminant rather than exact `nfdisc`.

Feedback-aware strict planner pass:

- Strict output:
  `/tmp/igp24_sair_feedback_strict_queue_20260706`
- Contrast output without the strong anti-`S24` requirement:
  `/tmp/igp24_sair_feedback_negative_only_queue_20260706`
- Helper: `scripts/igp24_next_verification_queue.py`
- New planner inputs/options:
  `--sair_label_feedback_json`,
  `--avoid_sair_negative_families`, and
  `--require_strong_anti_s24_evidence`

The strict pass re-ran the saved 160-row structure audit and joined the
24-row SAIR feedback by hash and structural family. It produced no new manual
queue:

```text
annotated_records=160
eligible_records=0
selected_records=0
filter_reason_counts={"known_exact_accepted_pair": 39, "sair_feedback_accepted_pair_duplicate_hash": 2, "sair_feedback_generic_hash": 22, "sair_generic_prone_family": 2, "weak_anti_s24_evidence": 95}
anti_s24_evidence_status_counts={"medium": 95, "strong": 41, "weak": 24}
sair_feedback_family_status_counts={"None": 134, "accepted_duplicate_prone": 2, "generic_prone": 24}
```

A contrast rerun with the same SAIR negative-family filters but without
`--require_strong_anti_s24_evidence` still had `eligible_records=0` and
`selected_records=0`. That means the decisive update was the accepted-label
feedback plus the existing accepted-pair ledger; the strong-evidence gate is
useful reporting discipline, but it did not by itself exhaust the saved pool.

Interpretation: do not force another 8-12 row submission from this saved pool.
The next bounded search should target stronger anti-`S24` evidence up front,
especially exact square discriminants or new verified non-generic families,
before another manual verification queue is worth the user effort.

Fresh strong anti-`S24` saved mining:

- Broad diagnostic output:
  `/tmp/igp24_strong_anti_s24_broad_diagnostic_20260706`
- Mined pool:
  `/tmp/igp24_strong_anti_s24_saved_mining_20260706`
- Structure audit:
  `/tmp/igp24_strong_anti_s24_structure_audit_20260706`
- Strict planner:
  `/tmp/igp24_strong_anti_s24_strict_queue_20260706`
- Manual dry-run packet:
  `/tmp/igp24_strong_anti_s24_manual_queue_20260706`
- Manual no-brackets coefficients:
  `/tmp/igp24_strong_anti_s24_manual_queue_20260706/manual_coefficients_no_brackets.txt`

The first attempt to diagnose all `/tmp/igp24_*` ledgers hit a malformed old
`candidates.jsonl`, so the run was narrowed to known clean saved benchmark
directories. That local-only diagnostic loaded 9,080 records, diagnosed 3,071
`r=4` rows, selected 500 diagnostics, and found 36 rows with
`square_discriminant_excludes_s24`.

`scripts/igp24_strong_anti_s24_mine.py` then excluded the exhausted 160-row
pool, joined saved exact-label feedback, joined the 24-row SAIR accepted-label
feedback, applied baseline and pair-status filters, and kept only square
anti-`S24` rows outside generic-prone or accepted-duplicate feedback families:

```text
records_scanned=3071
strong_anti_s24_records=36
eligible_records=15
selected_records=15
filter_reason_counts={"exhausted_pool_hash": 160, "missing_strong_anti_s24_evidence": 2896, "survived_strong_anti_s24_mining_filters": 15}
selected_strategy_counts={"fixed_sparse_template": 3, "quartic_lift": 6, "sparse": 4, "structured": 2}
```

The structure audit confirmed all 15 square-discriminant and exact-composed
claims. The strict feedback-aware planner, with
`--avoid_sair_negative_families`, `--require_strong_anti_s24_evidence`, and
one representative per structural family, reduced the pool to 3 unmatched
strong rows:

```text
annotated_records=15
eligible_records=3
selected_records=3
filter_reason_counts={"accepted_family_hint": 12, "survived_accepted_pending_baseline_generic_filters": 3}
selected_hashes=[
  "33772dd90765a2726c35d5d653cd17725b50ffdac30bb4e7cf195068b94851da",
  "72ed23a8d8bf5d9bd2401b0fb3b94b134794c1a5b51de7262daf2663bbdfad50",
  "33e431d55c37368ed565f364fb75690cad8e5e7d8dc2c83422a1db895e3a4b4d"
]
```

Interpretation: saved mining was enough; no CPU generation and no GPU/model
training were needed. The 3 survivors are credible enough for optional manual
verification, but not enough for a full 8-12 row batch. Do not pad with weaker
rows.

Manual SAIR result for the 3-row queue:

```text
row 1: accepted 24T21844 r=4
row 2: accepted 24T24970 r=4
row 3: accepted 24T24970 r=4
```

The feedback is recorded in
`data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json`.
`24T21844|r=4` is now an accepted local pair. The two `24T24970|r=4` rows are
score-pending accepted alternates/duplicates of an already accepted pair. A
post-feedback strict planner rerun at
`/tmp/igp24_strong_anti_s24_post_accept_strict_queue_20260706` selected 0
rows from the 15-row mined pool:

```text
annotated_records=15
eligible_records=0
selected_records=0
filter_reason_counts={"accepted_family_hint": 12, "sair_feedback_accepted_pair_duplicate_hash": 3}
```

The 3-row probe was therefore useful: it found one new pair and converted the
remaining strong mined pool into concrete feedback. It is now exhausted under
the stricter filters.

Score-aware triage with the new feedback, at
`/tmp/igp24_strong_anti_s24_sair_triage_20260706`, found all three exact
labels but still classified all rows as `exact_evidence_incomplete`. This is
expected because the user supplied labels/statuses, not delayed score rows or
exact local discriminants for the alternates. Keep the duplicate
`24T24970|r=4` rows pending unless scores show an improvement.

#1-contestant score-1 snapshot:

The user supplied a score table for the current #1 contestant. A compact
local summary is recorded at
`data/igp24/top_contestant_score1_snapshot_20260706.json`: 50 visible rows,
all `teams_k=1`, solvable, exact-`nfdisc`, and score 1. The rows are
concentrated in lower labels such as `24T105`-`24T111` and `24T290`-`24T324`,
with signatures mostly in `{0,8,12,16,24}` and only one visible `r=4` row.

Interpretation: the next search should not merely continue high-label `r=4`
anti-`S24` mining. To chase meaningful score, pivot toward targeted
lower-label solvable families and non-`r=4` signature modes, while preserving
exact `nfdisc`/baseline comparison as a gating requirement.

Score-1 target-analysis pass:

- Helper: `scripts/igp24_score1_target_analysis.py`
- Saved `r=0` diagnostic:
  `/tmp/igp24_score1_r0_saved_diagnostic_20260706`
- Target analysis:
  `/tmp/igp24_score1_target_analysis_20260706`
- Structure audit:
  `/tmp/igp24_score1_saved_candidate_structure_audit_20260706`
- Manual dry-run packet:
  `/tmp/igp24_score1_saved_candidate_manual_queue_20260706`

The helper is file-only and keeps exact targets separate from proxy
candidates. It ranks score-1 snapshot `(label, r)` pairs against the frozen
baseline, the local accepted-pair ledger, saved exact-label feedback, and the
saved proxy candidate coverage.

Target-analysis result:

```text
target_rows=50
target_r_counts={"0": 12, "8": 13, "12": 8, "16": 10, "24": 6, "4": 1}
target_baseline_presence_counts={"not_in_baseline": 50}
target_local_pair_status_counts={"not_in_local_ledger": 50}
target_generator_plausibility_counts={"needs_targeted_generation": 37, "saved_candidates_present": 13}
```

Interpretation: every visible score-1 target pair is absent from our local
accepted ledger and from the frozen baseline. The existing saved artifacts
only cover `r=0` and the single visible `r=4` target signature, not the
high-priority `r=8/12/16/24` signatures.

The saved `r=0` diagnostic loaded 8,290 saved records, diagnosed 351 `r=0`
records, selected 80, and found 40 square-discriminant rows. The target
analysis selected a 12-row `r=0` manual-verification queue:

```text
selected_candidate_records=12
selected_candidate_r_counts={"0": 12}
selected_candidate_strategy_counts={"structured": 12}
candidate_skipped_counts={"duplicate_hash": 1674, "target_r_mismatch": 1496, "weak_proxy_evidence": 243}
```

The structure audit confirmed all 12 square-discriminant and exact-composed
claims, with zero refutations. `scripts/igp24_offline_verify.py` then wrote a
dry-run manual verification packet with 12 one-candidate Magma scripts and no
local Magma/PARI execution. The no-brackets coefficient file is
`/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_coefficients.txt`.

Recommendation: this 12-row `r=0` queue is a reasonable immediate manual
probe, but it is still proxy-only until exact labels return. The next search
work should prioritize a bounded `r=8` generator/diagnostic pass, then
`r=12/16/24`, because those high-value score-1 signatures are uncovered in the
saved pool.

Bounded `r=8` target-generation pass:

- Benchmark artifacts:
  `/tmp/igp24_r8_targeted_bench_20260706`
- Non-generic diagnostic:
  `/tmp/igp24_r8_targeted_diagnostic_20260706`
- Score-1 analysis rerun:
  `/tmp/igp24_r8_targeted_score1_analysis_20260706`

Command:

```text
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies structured,lower_degree,sparse,fixed_sparse_template,mixed --seeds 801,802 --target_rs 8 --gensize 16 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 4 --sparse_terms 4 --low_height_bound 2 --mixed_strategy_weights sparse:0.20,lower_degree:0.20,structured:0.45,fixed_sparse_template:0.15 --output_dir /tmp/igp24_r8_targeted_bench_20260706
```

Result:

```text
runs=10
valid_candidates_total=160
ledger_records_total=297
target_r_match_total=0
best_score=10012.734145702047
r_counts={"0": 38, "2": 211, "4": 47, "6": 1}
```

Every tested strategy had `target_r_match_total=0`; the local proxy scorer and
bounded local search produced valid rows, but none with `real_root_count=8`.
The diagnostic therefore reported `diagnosed_records=0`,
`selected_records=0`, and `skipped_counts={"target_r_mismatch": 297}`. The
score-1 target-analysis rerun reported `selected_candidate_records=0` and
`queue_status=not_produced`; no manual queue was produced and no weak rows were
padded in.

Interpretation: the current local templates are useful for low-height
`r=0/2/4` exploration, but they do not currently reach the high-value `r=8`
score-1 target mode. The next useful step is a new explicit `r=8`
solvable/composed-family construction or template, not widening this same
benchmark shape and not launching a big GPU/model run yet.

Explicit `r=8` quartic-lift construction:

- Strategy: `r8_quartic_lift`
- Smoke artifacts:
  `/tmp/igp24_r8_quartic_lift_smoke_20260706`
- Bounded benchmark artifacts:
  `/tmp/igp24_r8_quartic_lift_bench_20260706`
- Non-generic diagnostic:
  `/tmp/igp24_r8_quartic_lift_diagnostic_20260706`
- Score-1 queue analysis:
  `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706`
- Structure audit:
  `/tmp/igp24_r8_quartic_lift_structure_audit_20260706`
- Dry-run manual verification packet:
  `/tmp/igp24_r8_quartic_lift_manual_queue_20260706`

Construction: pure quartic lifts `g(x^6)` where `g` has four positive real
roots. Each positive quartic fiber gives two real roots for `x^6=y`, so the
degree-24 lift has intended `real_root_count=8`. The previous coefficient
bound 4 cannot support a pure quartic lift with four positive roots; the
implemented opt-in strategy uses bound-16 templates and records metadata for
core support, quartic coefficients, positive-root count, minimum coefficient
bound, and exact composed-support divisor.

Smoke command:

```text
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies r8_quartic_lift --seeds 824 --target_rs 8 --gensize 6 --pop_size 4 --ntest 1 --gen_batch_size 1 --max_local_search_steps 0 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 16 --output_dir /tmp/igp24_r8_quartic_lift_smoke_20260706
```

Smoke result:

```text
valid_candidates=4
ledger_records=4
target_matches=4
match_rate=1.000
best_matching_score=10185.844543
```

Bounded command:

```text
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies r8_quartic_lift --seeds 824,825,826 --target_rs 8 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 2 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 16 --output_dir /tmp/igp24_r8_quartic_lift_bench_20260706
```

Bounded result:

```text
runs=3
valid_candidates_total=16
ledger_records_total=16
target_r_match_total=16
avg_match_rate=1.0
best_score=10185.844542850695
```

The diagnostic deduplicated the bounded output to 6 rows:

```text
diagnosed_records=6
selected_records=6
top_non_generic_score=2038.711136
flag_counts={"all_sampled_frobenius_even": 6, "exact_composed_support": 6, "near_composed_support": 6, "no_long_cycle_witness_in_sample": 6, "square_discriminant_excludes_s24": 6, "very_near_square_discriminant": 6, "very_sparse_support": 6}
```

The score-1 queue analysis produced a 6-row `r=8` queue, and the structure
audit confirmed all 6 square-discriminant and exact-composed-support claims
with zero refutations. The no-brackets coefficient file is
`/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`.

Recommendation: manually verify the six `r=8` rows before widening the
construction. The construction solves the local `r=8` generation problem, but
exact 24T labels are still unknown and must remain outside proxy claims.

Repo-tracked submission/feedback packet:

- Packet JSON:
  `data/igp24/r8_quartic_lift_submission_packet_20260706.json`
- SAIR-ready coefficient file:
  `data/igp24/r8_quartic_lift_submission_coefficients_20260706.txt`
- Manual feedback template:
  `data/igp24/r8_quartic_lift_sair_feedback_template_20260706.csv`
- Instructions:
  `data/igp24/r8_quartic_lift_submission_instructions_20260706.md`

The tracked coefficient file is the no-brackets six-row file suitable for
manual SAIR submission. The packet intentionally keeps label, exact scoring
discriminant, solvability, teams/k, and pair-score fields pending until SAIR
feedback exists. The practical lesson is that explicit composed construction
can reliably produce local `r=8` rows, while exact label and score value still
depend on verifier/submission feedback.

SAIR verifier feedback:

| row | exact label | r | status |
| ---: | --- | ---: | --- |
| 1 | `24T1310` | 8 | accepted |
| 2 | `24T1310` | 8 | accepted |
| 3 | `24T661` | 8 | accepted |
| 4 | `24T657` | 8 | accepted |
| 5 | `24T9993` | 8 | accepted |
| 6 | `24T9993` | 8 | accepted |

Accepted-feedback artifact:

- `data/igp24/r8_quartic_lift_sair_accepted_feedback_20260706.json`

The six accepted rows cover four distinct accepted pair keys:
`24T657|r=8`, `24T661|r=8`, `24T1310|r=8`, and `24T9993|r=8`. Scores and
scoring discriminants were not available when recorded.

## Explicit R16 Quadratic-Lift Probe

The `r=16` extension follows the successful composed-family pattern: use
degree-24 polynomials `g(x^2)` where degree-12 `g` has eight positive real
roots. A cheap construction probe found exact-valid perturbations at
coefficient height 703, so the implementation is opt-in as
`r16_quadratic_lift` and excluded from default benchmark runs.

Artifacts:

- Smoke:
  `/tmp/igp24_r16_quadratic_lift_smoke_20260706`
- Bounded benchmark:
  `/tmp/igp24_r16_quadratic_lift_bench_20260706`
- Non-generic diagnostic:
  `/tmp/igp24_r16_quadratic_lift_diagnostic_20260706`
- Score-1 queue analysis:
  `/tmp/igp24_r16_quadratic_lift_score1_analysis_20260706`
- Structure audit:
  `/tmp/igp24_r16_quadratic_lift_structure_audit_20260706`
- Dry-run manual verification packet:
  `/tmp/igp24_r16_quadratic_lift_manual_queue_20260706`

Smoke result:

```text
valid_candidates=4
ledger_records=4
target_matches=4
match_rate=1.000
best_matching_score=9411.793318
```

Bounded result:

```text
runs=3
valid_candidates_total=17
ledger_records_total=19
target_r_match_total=19
avg_match_rate=1.000
best_score=9414.762585
```

Diagnostic and audit summary:

```text
diagnosed_records=10
selected_records=10
flag_counts={"exact_composed_support": 10, "near_composed_support": 10, "no_long_cycle_witness_in_sample": 6}
structure_audit_records=8
exact_composed_claim_status_counts={"confirmed": 8}
primary_block_divisor_counts={"2": 8}
square_claim_status_counts={"not_claimed": 8}
```

The score-1 queue analysis produced 8 local `r=16` rows. The no-brackets
coefficient file is
`/tmp/igp24_r16_quadratic_lift_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`.
User-reported SAIR feedback accepted all eight table rows as `24T24979|r=16`
(the pasted count line said 6/6, but the table contained rows 1-8). No scores
or scoring discriminants were available when recorded.

Accepted feedback:

| Row | Label | r | Status |
| --- | --- | --- | --- |
| 1 | `24T24979` | 16 | accepted |
| 2 | `24T24979` | 16 | accepted |
| 3 | `24T24979` | 16 | accepted |
| 4 | `24T24979` | 16 | accepted |
| 5 | `24T24979` | 16 | accepted |
| 6 | `24T24979` | 16 | accepted |
| 7 | `24T24979` | 16 | accepted |
| 8 | `24T24979` | 16 | accepted |

Accepted-feedback artifact:

- `data/igp24/r16_quadratic_lift_sair_accepted_feedback_20260706.json`
- `data/igp24/r16_quadratic_lift_sair_status_export_20260706.csv`

The eight accepted rows cover one distinct accepted pair key,
`24T24979|r=16`, plus seven accepted alternates. The pair is absent from the
frozen baseline, so the label/signature is potentially scoreable; final score
depends on the pending scoring discriminant and team count.

The SAIR CSV export for submission `sub_02ecc2457d124584b8325b83608a2e9c`
reports `scoreable=false`, `scoringStatus=pending`,
`scoringReason=discriminant_pending`, blank discriminant fields, and
`inBaseline=false` for all eight rows. This is recorded as pending
discriminant scoring rather than final unscoreable status.

## Diversified R16 Probe

After the first r16 submission collapsed to `24T24979|r=16`, a bounded
CPU-only probe generated a more diverse manual queue. The helper constructs
degree-12 base polynomials with eight positive roots, forms `g(x^2)`, and also
tries tiny odd-power perturbations to escape the exact composed family while
preserving local `r=16`.

Command:

```text
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r16_diversity_probe.py --output_dir data/igp24/r16_diversity_probe_20260706 --seed 1616 --max_trials 240 --limit 10 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 4.0 --min_l1_to_accepted_even 5000
```

Result:

```text
trials_attempted=240
valid_r16_candidates=189
selected_rows=10
selected_mode_counts={"exact_composed_new_base": 5, "odd_perturbed_near_composed": 5}
rejected_counts={"coefficient_height_exceeds_bound": 32, "real_root_count_mismatch": 19}
queue_status=produced
```

Artifacts:

- `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_coefficients.txt`
- `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_queue.jsonl`
- `data/igp24/r16_diversity_probe_20260706/r16_diversified_summary.json`
- `data/igp24/r16_diversity_probe_20260706/r16_diversified_report.md`

Validation reran exact local scoring for all 10 selected coefficient rows:
each row has 25 integer coefficients, nonzero constant term, monic leading
coefficient, coefficient gcd 1, `real_root_count=16`, irreducible and
squarefree status, a unique canonical hash, and no overlap with accepted/known
ledger hashes. The helper makes no exact 24T-label claim.

User-reported SAIR feedback accepted all 10 diversified rows:

| Row | Local mode | Label | r | Status |
| ---: | --- | --- | ---: | --- |
| 1 | exact-composed | `24T24979` | 16 | accepted |
| 2 | odd-perturbed | `24T25000` | 16 | accepted |
| 3 | exact-composed | `24T24979` | 16 | accepted |
| 4 | odd-perturbed | `24T25000` | 16 | accepted |
| 5 | exact-composed | `24T24979` | 16 | accepted |
| 6 | odd-perturbed | `24T25000` | 16 | accepted |
| 7 | exact-composed | `24T24979` | 16 | accepted |
| 8 | odd-perturbed | `24T25000` | 16 | accepted |
| 9 | exact-composed | `24T24979` | 16 | accepted |
| 10 | odd-perturbed | `24T25000` | 16 | accepted |

Accepted-feedback artifact:

- `data/igp24/r16_diversity_probe_sair_accepted_feedback_20260706.json`

Both `24T24979|r=16` and `24T25000|r=16` are absent from the frozen baseline.
This confirms that odd-power perturbations can move the exact label, but this
particular escape route moved to generic-looking `24T25000|r=16`. Scores and
scoring discriminants were not available when recorded.

## Five-Representative Baseline Pass

The official frozen baseline CSV was imported from
`https://competition.sair.foundation/downloads/igp24/lmfdb_baseline.csv` and
saved as `data/igp24/lmfdb_baseline.csv`. The planner loaded 1,480 rows and
collapsed them into 622 official `(label, r)` pairs.

Updated exact-evidence helpers now:

- emit `IGP24_SIGNATURE` in generated Magma scripts,
- emit parseable PARI/GP `IGP24_NFDISC_ABS` markers,
- parse saved PARI/GP `nfdisc` output into `pari_nfdisc_results.jsonl`,
- optionally compute local SymPy `AlgebraicField.discriminant()` fallback
  evidence into `sympy_nfdisc_results.jsonl`,
- merge exact label, exact `r`, and exact `nfdisc` evidence by candidate hash,
- and report exact-`r`/exact-`nfdisc` status counts.

Focused validation passed:

```bash
env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q \
  tests/test_igp24_offline_verify.py tests/test_igp24_submission_plan.py
```

Result: 19 passed in 1.34s.

After adding the explicit SymPy fallback, the focused validation passed again:
21 tests in 4.55s.
After adding the explicit SymPy signature fallback, the focused validation
passed with 24 tests in 4.55s.

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

An explicit local SymPy nfdisc fallback pass was then run from source commit
`6abe150816fe36828edc8c50384f50b36fdd52ec`:

- `/tmp/igp24_submission_grade_five_20260706_sympy_nfdisc/sympy_nfdisc_results.jsonl`
- `/tmp/igp24_submission_grade_five_20260706_sympy_nfdisc/sympy_nfdisc_summary.json`
- `/tmp/igp24_submission_grade_five_20260706_sympy_nfdisc/sympy_nfdisc_report.md`

SymPy status counts: `{"nfdisc_ok": 5}`. The planner rerun from source commit
`7ff0a210b8100cb8c36f36b2dcfaadbac9576d0e` wrote:

- `/tmp/igp24_submission_grade_five_plan_with_sympy_nfdisc_20260706/submission_plan.jsonl`
- `/tmp/igp24_submission_grade_five_plan_with_sympy_nfdisc_20260706/submission_candidates.txt`
- `/tmp/igp24_submission_grade_five_plan_with_sympy_nfdisc_20260706/submission_plan_summary.json`
- `/tmp/igp24_submission_grade_five_plan_with_sympy_nfdisc_20260706/submission_plan_report.md`

Updated status counts:

- `baseline_status_counts={"non_baseline_candidate": 5}`
- `scoreability_status_counts={"new_pair_needs_exact_r": 5}`
- `exact_r_status_counts={"candidate_proxy": 5}`
- `exact_nfdisc_status_counts={"ok": 5}`
- `discriminant_rank_category_counts={"exact_nfdisc": 5}`

Exact local fallback `nfdisc` values:

| pair | hash | nfdisc source | exact nfdisc |
| --- | --- | --- | ---: |
| `24T9683|r=4` | `9c45c5493e7a` | `sympy_algebraic_field_discriminant` | 955418808601874103055463744199932705243136 |
| `24T24979|r=4` | `981a94588aab` | `sympy_algebraic_field_discriminant` | 1861637811973941745404031266095896941559808 |
| `24T24759|r=4` | `4be66a510402` | `sympy_algebraic_field_discriminant` | 7257477504600764033843223515092729030395849 |
| `24T24970|r=4` | `a97caa584baa` | `sympy_algebraic_field_discriminant` | 6681964085859090457451944972407263119355674624 |
| `24T24648|r=4` | `2289d8a5e700` | `sympy_algebraic_field_discriminant` | 3025607503381130745702964775405115504596600759660544 |

An explicit local SymPy signature fallback pass was then run from source commit
`ee916aab47e2f58d8791deac2af77584f9606952`, computing exact real-root counts
with `Poly.count_roots(-oo, oo)`. The final planner rerun from source commit
`75fd9bf470da189aeaffe197fd987deb963d9d49` wrote:

- `/tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706/submission_plan.jsonl`
- `/tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706/submission_candidates.txt`
- `/tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706/submission_plan_summary.json`
- `/tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706/submission_plan_report.md`

Final status counts:

- `baseline_status_counts={"non_baseline_candidate": 5}`
- `scoreability_status_counts={"new_pair_candidate": 5}`
- `exact_r_status_counts={"ok": 5}`
- `exact_nfdisc_status_counts={"ok": 5}`
- `discriminant_rank_category_counts={"exact_nfdisc": 5}`

Final selected rows:

| pair | hash | r source | nfdisc source | exact nfdisc |
| --- | --- | --- | --- | ---: |
| `24T9683|r=4` | `9c45c5493e7a` | `verified.sympy_real_root_count` | `sympy_algebraic_field_discriminant` | 955418808601874103055463744199932705243136 |
| `24T24979|r=4` | `981a94588aab` | `verified.sympy_real_root_count` | `sympy_algebraic_field_discriminant` | 1861637811973941745404031266095896941559808 |
| `24T24759|r=4` | `4be66a510402` | `verified.sympy_real_root_count` | `sympy_algebraic_field_discriminant` | 7257477504600764033843223515092729030395849 |
| `24T24970|r=4` | `a97caa584baa` | `verified.sympy_real_root_count` | `sympy_algebraic_field_discriminant` | 6681964085859090457451944972407263119355674624 |
| `24T24648|r=4` | `2289d8a5e700` | `verified.sympy_real_root_count` | `sympy_algebraic_field_discriminant` | 3025607503381130745702964775405115504596600759660544 |

Interpretation update: the five selected expected pairs are absent from the
official baseline and now have exact local fallback `r` plus exact local
fallback `nfdisc`. The helper still does not submit to SAIR, and Magma/PARI
remain preferred independent cross-checks when available, but the planner now
correctly marks the five rows as `new_pair_candidate`.

A final local/manual submission-review package was then built at
`/tmp/igp24_final_submission_package_20260706` using
`scripts/igp24_submission_package.py`. The package is not a SAIR submission and
does not call SAIR, Magma, PARI, online calculators, training, GPU sampling, or
search loops.

Package contents and checks:

- `package_manifest.json`: structured manifest with five selected row
  summaries, official baseline CSV hash, source artifact paths, copied-file
  checksums, local tool availability, and safety flags.
- `submission_checklist.md`: human-readable checklist confirming exactly five
  rows, one row per `(24Tt, r)` pair, all five absent from the baseline, saved
  Magma label provenance, SymPy exact-r and exact-nfdisc evidence, no SAIR/API
  submission, and the local Magma/PARI cross-check caveat.
- `submission_coefficients.txt`: coefficient-only file with five 25-integer
  rows and no comments.
- `submission_coefficients.jsonl`: structured coefficient export with rank,
  pair, canonical hash, and coefficients.
- copied plan artifacts under `plan/`,
  exact-evidence artifacts under `evidence/`, saved raw Magma XML under
  `raw_magma_xml/`, and the frozen baseline CSV under `baseline/`.

Package audit status:

- `selected_records=5`
- `selected_pairs=["24T9683|r=4", "24T24979|r=4", "24T24759|r=4", "24T24970|r=4", "24T24648|r=4"]`
- `baseline_status_counts={"non_baseline_candidate": 5}`
- `scoreability_status_counts={"new_pair_candidate": 5}`
- `exact_r_status_counts={"ok": 5}`
- `exact_nfdisc_status_counts={"ok": 5}`
- 5 coefficient rows, 5 structured coefficient rows, 5 plan rows, and 5 raw
  Magma XML provenance files.
- Local tool availability in the manifest remains
  `magma.available=false`, `pari_gp.available=false`.

Follow-up exact-tool cross-check, 2026-07-06:

The host did not allow a system `sudo apt-get install pari-gp`, so PARI/GP was
installed in user space by downloading the Ubuntu `pari-gp` package and
unpacking it under `/tmp/pari-gp-local`. The resulting executable was
`/tmp/pari-gp-local/usr/bin/gp`, reporting PARI/GP 2.15.4.

This uncovered and fixed two verifier-script portability issues:

- GP batch mode needs explicit line continuations for the generated multi-line
  vectors and loop body.
- GP should use `x = 'x;`; the previous `Pol([0, 1])` built a constant
  polynomial in this context.
- Magma `NumberOfRealRoots` should receive an integer-polynomial ring element;
  the generated Magma scripts now use `Zx<x> := PolynomialRing(Integers())`
  instead of a rational-polynomial ring.

The integrated cross-check artifact is:
`/tmp/igp24_pari_magma_crosscheck_20260706_parsed`.

A refreshed cross-checked manual package was also built at
`/tmp/igp24_final_submission_package_20260706_crosschecked`. Compared with the
earlier package, this copy uses the fixed GP/Magma scripts, includes PARI/GP
`nfdisc_ok` results, includes parsed online Magma `IGP24_SIGNATURE 4`/label
results, and copies the five raw online Magma XML responses under
`evidence/online_magma_manual/checked_xml`.

PARI/GP status:

- command source: final package plan JSONL
- `pari_available=true`
- `pari_executed=true`
- `pari_nfdisc_status_counts={"nfdisc_ok": 5}`
- all five PARI `nfdisc` values match the SymPy `nfdisc` values above
- all five PARI rows are degree 24, irreducible, and have `pari_r=4`

Online Magma calculator status:

- endpoint: `https://magma.maths.usyd.edu.au/calc/`
- raw XML responses:
  `/tmp/igp24_pari_magma_crosscheck_20260706/online_magma_manual/checked_xml`
- parsed results:
  `/tmp/igp24_pari_magma_crosscheck_20260706_parsed/online_magma_manual/online_magma_manual_results.jsonl`
- `online_magma_manual` status counts: `{"verified": 5}`
- all five rows returned degree 24, irreducible, `IGP24_SIGNATURE 4`, no
  calculator warnings, and the expected transitive group id.

Cross-check table:

| pair | hash | Magma r | Magma label | PARI nfdisc |
| --- | --- | ---: | --- | ---: |
| `24T24979|r=4` | `981a94588aab` | 4 | `24T24979` | 1861637811973941745404031266095896941559808 |
| `24T24759|r=4` | `4be66a510402` | 4 | `24T24759` | 7257477504600764033843223515092729030395849 |
| `24T9683|r=4` | `9c45c5493e7a` | 4 | `24T9683` | 955418808601874103055463744199932705243136 |
| `24T24970|r=4` | `a97caa584baa` | 4 | `24T24970` | 6681964085859090457451944972407263119355674624 |
| `24T24648|r=4` | `2289d8a5e700` | 4 | `24T24648` | 3025607503381130745702964775405115504596600759660544 |

The helper still did not submit to SAIR. The remaining exact-tool caveat is
only that Magma was not installed locally; the five fixed scripts were checked
through the free online Magma calculator and parsed back into local artifacts.

Manual SAIR submission result:

The five-row coefficient file from
`/tmp/igp24_final_submission_package_20260706_crosschecked/submission_coefficients.txt`
was submitted manually through the SAIR UI. The reported verifier response
accepted all five rows:

| row | status | label | r | reason |
| ---: | --- | --- | ---: | --- |
| 1 | accepted | `24T9683` | 4 | — |
| 2 | accepted | `24T24979` | 4 | — |
| 3 | accepted | `24T24759` | 4 | — |
| 4 | accepted | `24T24970` | 4 | — |
| 5 | accepted | `24T24648` | 4 | — |

This confirms that the submitted rows passed SAIR verification with the same
labels and signatures as the local/online cross-check artifacts.

The four calculator-disabled rows were not automatically retried online. A
manual retry packet was prepared at `/tmp/igp24_pending_four_retry_20260706`
instead. It contains one-candidate Magma copy/paste scripts with
`IGP24_SIGNATURE` and PARI/GP input with `IGP24_NFDISC_ABS` for:

- `198ac88fa216`
- `20b35a3fd41d`
- `88437a372524`
- `0f3ad8602d89`

That packet was later refreshed at
`/tmp/igp24_pending_four_retry_sympy_exact_20260706` with the same local SymPy
fallback checks: `sympy_signature_status_counts={"signature_ok": 4}` and
`sympy_nfdisc_status_counts={"nfdisc_ok": 4}`. It is still dry-run/manual-only:
no local Magma, no local PARI, no SAIR/API call, no network submission, and no
GPU/model search.

## Anti-Collapse R16 Probe

The first two r16 submissions taught a clear structural lesson:

- exact divisor-2 `g(x^2)` rows collapsed to `24T24979|r=16`,
- one-odd near-composed rows escaped that label but collapsed to
  `24T25000|r=16`.

The second probe was designed to avoid both buckets while staying CPU-only and
manual-submission-only. It extends `scripts/igp24_r16_diversity_probe.py` with
multi-perturbation modes, full-row distance checks against accepted r16 rows,
and divisor-2 off-block filters.

Command:

```bash
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r16_diversity_probe.py \
  --output_dir data/igp24/r16_anti_collapse_probe_20260706 \
  --seed 2616 \
  --max_trials 720 \
  --limit 12 \
  --per_family_cap 1 \
  --coeff_bound 20000000 \
  --prime_limit 7 \
  --exact_score_timeout 4.0 \
  --min_l1_to_accepted_even 5000 \
  --min_l1_to_accepted_full 5000 \
  --no-include_exact \
  --no-include_odd \
  --include_two_odd \
  --include_three_odd \
  --include_mixed_even_odd \
  --min_off_block_terms 2 \
  --max_off_block_terms 4
```

Result:

- `trials_attempted=720`
- `valid_r16_candidates=149`
- `selected_rows=12`
- selected modes:
  `{"mixed_even_odd_perturbed": 4, "three_odd_perturbed_near_composed": 4, "two_odd_perturbed_near_composed": 4}`
- rejected counts:
  `{"coefficient_height_exceeds_bound": 112, "real_root_count_mismatch": 298, "reducible_over_q": 91, "too_close_to_accepted_even_coefficients": 70}`
- off-block counts among selected rows: `{"2": 8, "3": 4}`
- minimum full-row L1 distance to accepted r16 rows: 411103

Tracked artifacts:

- `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_coefficients.txt`
- `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_queue.jsonl`
- `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_hashes.txt`
- `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_summary.json`
- `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_rejected_trials.jsonl`
- `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_report.md`

Validation confirmed all 12 selected rows have 25 integer coefficients,
nonzero constant coefficient, monic leading coefficient, coefficient gcd 1,
local `real_root_count=16`, irreducible and squarefree exact checks, unique
hashes, unique family keys, no accepted-hash overlap, and no exact/one-odd
collapse modes.

SAIR feedback:

- user-reported result: 12/12 accepted,
- all 12 rows landed as `24T25000|r=16`,
- tracked feedback:
  `data/igp24/r16_anti_collapse_probe_sair_accepted_feedback_20260706.json`,
- pair-status ledger updated with 12 accepted `24T25000|r=16` alternates.

Interpretation: the current r16 divisor-2 corridor is now clearly
label-collapsed. Exact `g(x^2)` rows land as `24T24979|r=16`; one-odd and
multi-off-block near-composed rows land as `24T25000|r=16`. Future r16 work
should require a genuinely different construction.

## Target-Bucket Planning

A screenshot-derived discovery snapshot was recorded at
`data/igp24/sair_discovery_snapshot_20260706_1648.json`. It is aggregate-only
and should be replaced by SAIR API data when exact uncovered target lists are
needed.

Snapshot highlights:

- total valid signatures: 165,836
- solved signatures: 112,825
- uncovered signatures: 53,011
- LMFDB baseline signatures: 622
- uncovered solvable signatures: 51,992, about 98.1% of uncovered signatures

Largest remaining buckets:

| r | remaining |
| ---: | ---: |
| 24 | 12126 |
| 16 | 10902 |
| 8 | 6988 |
| 12 | 6919 |
| 20 | 5773 |

Planner command:

```bash
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_target_bucket_plan.py \
  --discovery_snapshot_json data/igp24/sair_discovery_snapshot_20260706_1648.json \
  --pair_status_json data/igp24/pair_status_20260706.json \
  --output_dir data/igp24/target_bucket_plan_20260706
```

Planner result:

- exact API target list available: `false`
- largest remaining r buckets: `[24, 16, 8, 12, 20]`
- recommended action order: `[24, 20, 8, 12, 16]`
- no GPU/model training recommended yet

Tracked artifacts:

- `data/igp24/target_bucket_plan_20260706/target_bucket_plan.json`
- `data/igp24/target_bucket_plan_20260706/target_bucket_plan.md`
- `data/igp24/target_bucket_plan_20260706/target_bucket_plan_summary.json`

The planner keeps r16 globally important but deprioritizes the current r16
divisor-2 perturbation family. It recommends a new explicit r24
solvable/high-real-root construction first, then r20/r12 construction work,
while keeping r8 active because it already produced multiple accepted labels.

## R24 High-Real-Root Probe

The first r24 target-aware construction is a standalone local helper,
`scripts/igp24_r24_high_real_probe.py`. It starts from explicit all-real seeds
`prod(x^2-a)` and adds one to three small low-odd perturbations. The base seed
has 24 real roots but is reducible; the perturbations test whether
irreducibility can be recovered while preserving `real_root_count=24`.

Smoke command:

```bash
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r24_high_real_probe.py \
  --output_dir /tmp/igp24_r24_high_real_smoke_20260706 \
  --seed 2424 \
  --max_trials 24 \
  --limit 4 \
  --coeff_bound 5000000000 \
  --prime_limit 7 \
  --exact_score_timeout 5.0
```

Smoke result:

- `trials_attempted=24`
- `valid_r24_candidates=22`
- `selected_rows=4`
- rejected counts: `{"reducible_over_q": 2}`

Tracked bounded command:

```bash
env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r24_high_real_probe.py \
  --output_dir data/igp24/r24_high_real_probe_20260706 \
  --seed 2424 \
  --max_trials 120 \
  --limit 8 \
  --per_family_cap 1 \
  --coeff_bound 5000000000 \
  --prime_limit 7 \
  --exact_score_timeout 5.0
```

Tracked bounded result:

- `trials_attempted=120`
- `valid_r24_candidates=113`
- `selected_rows=8`
- queue status: `manual_queue_ready`
- selected modes:
  `{"single_low_odd_break": 3, "three_low_odd_break": 2, "two_low_odd_break": 3}`
- rejected counts: `{"reducible_over_q": 7}`
- selected coefficient-height range: `1931559552` to `2258902656`

Tracked artifacts:

- `data/igp24/r24_high_real_probe_20260706/r24_high_real_candidate_coefficients.txt`
- `data/igp24/r24_high_real_probe_20260706/r24_high_real_candidate_queue.jsonl`
- `data/igp24/r24_high_real_probe_20260706/r24_high_real_candidate_hashes.txt`
- `data/igp24/r24_high_real_probe_20260706/r24_high_real_summary.json`
- `data/igp24/r24_high_real_probe_20260706/r24_high_real_rejected_trials.jsonl`
- `data/igp24/r24_high_real_probe_20260706/r24_high_real_report.md`

Independent validation reran local exact checks on all 8 selected rows and
confirmed 25 integer coefficients, monic leading coefficient, nonzero constant
coefficient, coefficient gcd 1, local `real_root_count=24`, irreducible and
squarefree exact checks, unique hashes, and no overlap against 46 locally known
accepted hashes from `data/igp24/pair_status_20260706.json`.

Interpretation: this is the first successful local r24 high-real-root queue.
It is useful because r24 is the largest remaining aggregate bucket in the
snapshot-derived plan. It is still proxy/local only: no exact `24Tt` labels are
claimed, no SAIR API or network service was used, and no automatic submission
path exists.

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
- `scripts/igp24_submission_package.py`: local/manual submission-review
  package builder.

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
