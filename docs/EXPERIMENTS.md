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
