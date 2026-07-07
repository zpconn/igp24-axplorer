# IGP24 Live TODO

This file is the working project log for the Axplorer-based IGP24 candidate
generator. Keep it current as implementation, tests, smoke runs, and benchmark
results change.

## Current Status

- Branch: `igp24-dev`
- Remote target: `zpconn/igp24-axplorer`
- Last pull: 2026-07-06, `git pull --ff-only` -> already up to date before
  the r12 follow-up feedback import and tower-probe work.
- Active focus: local accepted-pair coverage now spans `r=4`, `r=8`, `r=12`,
  `r=16`, `r=20`, and `r=24`, with detailed accepted-pair state in
  `data/igp24/pair_status_20260706.json`. The newest accepted batch is the
  r12 degree-6-by-degree-4 tower probe: SAIR accepted all 10 rows, added
  `24T23883|r=12` and `24T24651|r=12`, and avoided `24T25000`. MAGMA/PARI/SAIR
  remain out of `train.py`, GPU sampling, CPU proxy scoring, and search hot
  loops. Dry-run remains the default for submission tooling; local MAGMA
  execution still requires explicit `--run_magma`, and live SAIR API
  submission requires explicit `--execute` plus an environment-provided API
  key.
- Current result: the 24-row next non-generic queue was manually submitted by
  the user and all 24 rows were accepted by the SAIR verifier, with scores
  still pending. Local feedback artifact
  `data/igp24/sair_accepted_label_feedback_20260706_next_queue.json` records
  2 rows as `24T24979|r=4` and 22 rows as generic `24T25000|r=4`. The refreshed
  score-aware triage under `/tmp/igp24_next_non_generic_sair_triage_20260706`
  has `verified_rows=24`, `pending_exact_label_rows=0`,
  `submission_grade_rows=0`, `classification_counts={"accepted_pair_duplicate": 2, "generic_24T25000": 22}`,
  and `accepted_pair_status_counts={"accepted_pair_duplicate_not_improved": 23, "accepted_pair_minor_discriminant_improvement": 1}`.
  Row 6 (`0ec921751862`) is a lower exact-nfdisc `24T25000|r=4` alternate, but
  it remains score-pending rather than promoted.
- Current r12 follow-up: the feedback-aware `g(x^2)` r12 queue was accepted by
  SAIR as duplicate `24T24970|r=12` and `24T24979|r=12` rows, so those records
  are tracked as score-pending alternates. The structurally different
  degree-6-by-degree-4 exact tower probe under
  `data/igp24/r12_tower_probe_20260706` was then accepted 10/10 by SAIR, with
  rows 1,3,4,6-10 as `24T24651|r=12` and rows 2,5 as `24T23883|r=12`. Tracked
  feedback is in
  `data/igp24/r12_tower_probe_sair_accepted_feedback_20260706.json`; scores
  and scoring discriminants remain pending.
- README cleanup: public-facing README now stays concise; benchmark and
  verification result detail moved to `docs/EXPERIMENTS.md`, with the full
  working log still in this TODO and design notes in `NOTES_IGP24.md`.
- SAIR API helper: added a credential-safe Public API client and CLI wrapper.
  API keys are read only from `SAIR_API_KEY` or another explicit environment
  variable, never from committed files. `scripts/igp24_sair_api.py submit`
  validates in dry-run mode by default; live submission requires `--execute`.
  Progress queries use the official `labels/progress` endpoint and should be
  used before future target queues.
  Verification: focused API/tower tests passed (`13 passed`), full suite
  passed (`182 passed`), `git diff --check` passed, JSON artifacts parsed with
  `python3 -m json.tool`, SAIR CLI dry-run validated the 10 tower coefficient
  rows without an API key, a worktree scan found no provided key fragments, and
  Stage 4 remains present at line 7516.

- Active r16 follow-up: imported the SAIR CSV export for
  `sub_02ecc2457d124584b8325b83608a2e9c`. All eight `24T24979|r=16` rows are
  accepted and `inBaseline=false`; `scoreable=false` is paired with
  `scoringStatus=pending` and `scoringReason=discriminant_pending`, so it is
  treated as provisional pending discriminant scoring, not final no-score
  status. A short CPU-only r16 diversity probe produced a 10-row manual queue
  under `data/igp24/r16_diversity_probe_20260706`; SAIR accepted all 10 rows,
  with exact-composed rows as `24T24979|r=16` and odd-perturbed rows as
  `24T25000|r=16`.
- Active anti-collapse r16 follow-up: extended
  `scripts/igp24_r16_diversity_probe.py` with opt-in two-odd, three-odd,
  four-odd, and mixed even+odd perturbation modes, full-row L1 distance checks
  against accepted r16 submissions, and divisor-2 off-block filters. The
  bounded CPU-only run under
  `data/igp24/r16_anti_collapse_probe_20260706` attempted 720 trials, found
  149 valid local `r=16` candidates, and selected 12 rows: four two-odd, four
  three-odd, and four mixed even+odd. SAIR accepted all 12 rows as
  `24T25000|r=16`, so multi-off-block divisor-2 perturbations still collapse
  into the generic r16 endpoint. Validation passed for SAIR format, local
  `r=16`, irreducible/squarefree status, unique hashes/families, no known
  accepted-hash overlap, and 2-3 divisor-2 off-block terms per row. Focused
  compile/test checks passed:
  `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_r16_diversity_probe.py tests/test_igp24.py`
  and
  `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py::test_r16_diversity_probe_helpers_build_degree24_lift tests/test_igp24.py::test_r16_diversity_probe_multi_odd_modes_escape_one_odd_support`
  -> 2 passed. No GPU, model training, SAIR API, Magma/PARI, or network work
  is part of this probe.
- Active target-aware planning pivot: added a screenshot-derived SAIR discovery
  snapshot at `data/igp24/sair_discovery_snapshot_20260706_1648.json` and a
  local target-bucket plan under `data/igp24/target_bucket_plan_20260706`.
  The snapshot is aggregate-only and not a live target list. The planner ranks
  largest remaining buckets as `r=24,16,8,12,20`, but recommends immediate
  action order `r=24,20,8,12,16` because the current r16 construction family
  has now repeatedly collapsed. It does not recommend GPU/model training until
  there is a target-conditioned sampling objective.
- Completed r24 prototype: added a CPU-only explicit high-real-root probe based
  on `prod_{a=1}^{12}(x^2-a)` plus small low-odd perturbations. A scratch local
  check found irreducible, squarefree `r=24` rows at coefficient height
  `1931559552`, then the tracked helper wrote artifacts under
  `data/igp24/r24_high_real_probe_20260706/`. This probe did not use
  GPU/model training, SAIR API, Magma/PARI, online calculators, network
  services, or automatic submission.
  - Smoke result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r24_high_real_probe.py --output_dir /tmp/igp24_r24_high_real_smoke_20260706 --seed 2424 --max_trials 24 --limit 4 --coeff_bound 5000000000 --prime_limit 7 --exact_score_timeout 5.0`
    completed in about 1.4s, attempted 24 trials, found 22 valid local `r=24`
    irreducible/squarefree candidates, selected 4 smoke rows, and rejected 2
    reducible rows. Selected coefficient heights ranged from `1931559552` to
    `2258902656`. No GPU, model training, SAIR API, Magma/PARI, network, or
    automatic submission was used.
  - Bounded tracked result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r24_high_real_probe.py --output_dir data/igp24/r24_high_real_probe_20260706 --seed 2424 --max_trials 120 --limit 8 --per_family_cap 1 --coeff_bound 5000000000 --prime_limit 7 --exact_score_timeout 5.0`
    completed in about 7s, attempted 120 trials, found 113 valid local `r=24`
    candidates, selected 8 manual-queue rows, and rejected 7 reducible rows.
    The selected queue has 3 `single_low_odd_break`, 3 `two_low_odd_break`,
    and 2 `three_low_odd_break` rows, with coefficient heights from
    `1931559552` to `2258902656`. Tracked artifacts are under
    `data/igp24/r24_high_real_probe_20260706/`.
  - Independent validation result: parsed the queue JSONL and no-brackets TXT,
    reran local exact checks on all 8 selected rows, and confirmed exactly 25
    integer coefficients per row, monic leading coefficient, nonzero constant,
    coefficient gcd 1, local `real_root_count=24`, irreducible and squarefree
    exact checks, unique hashes, and no overlap against 46 locally known
    accepted hashes from `data/igp24/pair_status_20260706.json`.
  - Test/check result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_r24_high_real_probe.py`
    -> 3 passed;
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` -> 159 passed;
    `git diff --check` passed; and
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
    confirmed Stage 4 remains present.
  - SAIR feedback result: user reported that all 8 rows were accepted as
    `24T25000|r=24`. Tracked feedback is recorded in
    `data/igp24/r24_high_real_probe_sair_accepted_feedback_20260706.json`,
    and `data/igp24/pair_status_20260706.json` now records the new
    `24T25000|r=24` pair plus seven accepted alternates. Lesson: local `r=24`
    and SAIR formatting worked, but this low-odd perturbation family is
    generic-label collapsed and should not be widened as-is.
- Completed r20 prototype: added a standalone CPU-only
  `scripts/igp24_r20_high_real_probe.py` using ten positive quadratic factors
  and two no-real-root quadratic factors,
  `prod(x^2-a) * prod(x^2+b)`, plus small low-odd perturbations. The base seed
  structurally has `real_root_count=20`.
  - Smoke result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r20_high_real_probe.py --output_dir /tmp/igp24_r20_high_real_smoke_20260706 --seed 2020 --max_trials 32 --limit 4 --coeff_bound 100000000 --prime_limit 7 --exact_score_timeout 5.0`
    completed in about 1.4s, attempted 32 trials, found 20 valid local `r=20`
    candidates, selected 4 smoke rows, rejected 11 rows over the 100M height
    bound, and rejected 1 reducible row.
  - Bounded tracked result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r20_high_real_probe.py --output_dir data/igp24/r20_high_real_probe_20260706 --seed 2020 --max_trials 160 --limit 10 --per_family_cap 1 --coeff_bound 100000000 --prime_limit 7 --exact_score_timeout 5.0`
    completed in about 6.3s, attempted 160 trials, found 95 valid local
    `r=20` candidates, selected 10 manual-queue rows, rejected 50 rows over
    the 100M height bound, and rejected 15 reducible rows. The selected queue
    has 3 `single_low_odd_break`, 3 `two_low_odd_break`, and 4
    `three_low_odd_break` rows, with coefficient heights from `10813088` to
    `49972896`. Tracked artifacts are under
    `data/igp24/r20_high_real_probe_20260706/`.
  - Independent validation result: parsed the r20 queue JSONL and no-brackets
    TXT, reran local exact checks on all 10 selected rows, and confirmed
    exactly 25 integer coefficients per row, monic leading coefficient,
    nonzero constant, coefficient gcd 1, local `real_root_count=20`,
    irreducible and squarefree exact checks, unique hashes, and no overlap
    against 54 locally known accepted hashes from
    `data/igp24/pair_status_20260706.json`.
  - Test/check result:
    structured artifact checks confirmed 8 r24 feedback rows, 14 pair-status
    pairs, and 10 selected r20 rows;
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_r20_high_real_probe.py tests/test_igp24_r24_high_real_probe.py`
    -> 6 passed;
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` -> 162 passed;
    `git diff --check` passed; and
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
    confirmed Stage 4 remains present.
  - SAIR feedback result: user reported that all 10 rows were accepted as
    `24T25000|r=20`. Tracked feedback is recorded in
    `data/igp24/r20_high_real_probe_sair_accepted_feedback_20260706.json`,
    and `data/igp24/pair_status_20260706.json` now records the new
    `24T25000|r=20` pair plus nine accepted alternates. Lesson: local `r=20`
    and SAIR formatting worked, but this low-odd mixed quadratic perturbation
    family is generic-label collapsed and should not be widened as-is.
- Active r12 structured prototype: added a standalone CPU-only
  `scripts/igp24_r12_structured_probe.py` using exact composed support
  `g(x^2)`. The degree-12 base `g(y)` starts with six positive and six
  negative real roots, then only the base coefficients are perturbed before
  lifting. This preserves exact even/composed support and introduces no odd
  powers of `x`.
  - Smoke result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r12_structured_probe.py --output_dir /tmp/igp24_r12_structured_smoke_20260706 --seed 1212 --max_trials 36 --limit 4 --coeff_bound 5000000 --prime_limit 7 --exact_score_timeout 5.0`
    completed in about 1.5s, attempted 36 trials, found 26 valid local
    `r=12` candidates, selected 4 smoke rows, rejected 5 rows over the 5M
    height bound, rejected 4 real-root mismatches, and rejected 1 reducible
    row.
  - Bounded tracked result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r12_structured_probe.py --output_dir data/igp24/r12_structured_probe_20260706 --seed 1212 --max_trials 180 --limit 10 --per_family_cap 1 --coeff_bound 5000000 --prime_limit 7 --exact_score_timeout 5.0`
    completed in about 7.2s, attempted 180 trials, found 111 valid local
    `r=12` candidates, selected 10 manual-queue rows, rejected 39 rows over
    the 5M height bound, rejected 21 real-root mismatches, and rejected 9
    reducible rows. The selected queue has 7
    `single_base_coefficient_perturbation` rows and 3
    `structured_base_coefficient_perturbation` rows, with coefficient heights
    from `773136` to `4410912`. Tracked artifacts are under
    `data/igp24/r12_structured_probe_20260706/`.
  - Independent validation result: parsed the r12 queue JSONL and no-brackets
    TXT, reran local exact checks on all 10 selected rows, and confirmed
    exactly 25 integer coefficients per row, monic leading coefficient,
    nonzero constant, coefficient gcd 1, local `real_root_count=12`,
    irreducible and squarefree exact checks, unique hashes, no odd `x` support,
    and no overlap against 64 locally known accepted hashes from
    `data/igp24/pair_status_20260706.json`.
  - Test/check result:
    structured artifact checks confirmed 10 r20 feedback rows, 15 pair-status
    pairs, and 10 selected r12 rows;
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_r12_structured_probe.py tests/test_igp24_r20_high_real_probe.py tests/test_igp24_r24_high_real_probe.py`
    -> 9 passed;
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` -> 165 passed;
    `git diff --check` passed; and
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
    confirmed Stage 4 remains present.
  - SAIR feedback result: user reported that all 10 rows were accepted.
    Rows 1 and 5 landed as `24T22770|r=12`, row 3 landed as
    `24T24970|r=12`, and rows 2, 4, 6, 7, 8, 9, and 10 landed as
    `24T24979|r=12`. Tracked feedback is recorded in
    `data/igp24/r12_structured_probe_sair_accepted_feedback_20260706.json`,
    and `data/igp24/pair_status_20260706.json` now records the three new
    accepted r12 pair keys plus duplicate accepted alternates. Lesson: exact
    `g(x^2)` support avoided `24T25000`, local r12 validation and SAIR
    formatting were correct, label diversity appeared, and `24T24979` is the
    dominant basin but not the only one.
  - Follow-up result: added
    `scripts/igp24_r12_structured_followup.py`, a bounded CPU-only,
    label-feedback-aware r12 structured helper that keeps exact `g(x^2)`
    support, avoids known accepted hashes/family keys where possible, tracks
    distance from the accepted r12 rows, and writes manual-submission artifacts
    only.
    - Smoke result:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r12_structured_followup.py --output_dir /tmp/igp24_r12_structured_followup_smoke_20260706 --seed 1213 --max_trials 48 --limit 4 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 5.0 --min_l1_to_accepted_exported 4 --min_l1_to_accepted_base_y 4`
      completed in about 2.5s, attempted 48 trials, found 27 valid local
      `r=12` candidates, selected 4 smoke rows, and rejected 9 real-root
      mismatches plus 12 reducible rows.
    - Bounded tracked result:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r12_structured_followup.py --output_dir data/igp24/r12_structured_followup_20260706 --seed 1213 --max_trials 240 --limit 10 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 5.0 --min_l1_to_accepted_exported 4 --min_l1_to_accepted_base_y 4`
      completed in about 12s, attempted 240 trials, found 155 valid local
      `r=12` candidates, selected 10 manual-queue rows, and rejected 54
      real-root mismatches plus 31 reducible rows. The selected queue has 4
      `two_base_wide_perturbation`, 3 `three_base_balanced_perturbation`, and
      3 `four_base_balanced_perturbation` rows, with coefficient heights from
      `6696912` to `8796916`. Tracked artifacts are under
      `data/igp24/r12_structured_followup_20260706/`.
    - Independent validation result: parsed the new JSON/JSONL/TXT artifacts,
      reran local exact checks on all 10 selected rows, and confirmed 25
      integer coefficients per row, monic leading coefficient, nonzero
      constant, coefficient gcd 1, local `real_root_count=12`, irreducible and
      squarefree exact checks, exact even `x` support, unique hashes, no
      accepted r12 feedback-hash overlap, and no accepted r12 structural-family
      overlap.
    - SAIR feedback result: user reported that all 10 follow-up rows were
      accepted. Rows 1-2 landed as already-known `24T24970|r=12`; rows 3-10
      landed as already-known `24T24979|r=12`. Tracked feedback is recorded in
      `data/igp24/r12_structured_followup_sair_accepted_feedback_20260706.json`,
      and `data/igp24/pair_status_20260706.json` now keeps those 10 rows as
      accepted score-pending alternates under the existing r12 pair entries.
      Lesson: exact `g(x^2)` remains robust and again avoided `24T25000`, but
      the nearby feedback-aware widening produced no new pair keys. Further
      nearby `g(x^2)` widening is lower priority.
  - Tower pivot result: added `scripts/igp24_r12_tower_probe.py`, a bounded
    CPU-only exact-composed prototype using degree pattern `6x4`:
    `h(q(x))` with `q(x)=x^4-s*x^2` and `deg(h)=6`. This preserves exact
    composition while moving away from direct degree-12 base products lifted as
    `g(x^2)`.
    - Smoke result:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r12_tower_probe.py --output_dir /tmp/igp24_r12_tower_smoke_20260706 --seed 1246 --max_trials 48 --limit 4 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 5.0`
      completed in about 2.7s, attempted 48 trials, found 22 valid local
      `r=12` candidates, selected 4 smoke rows, and rejected 14 real-root
      mismatches plus 12 reducible rows.
    - Bounded tracked result:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r12_tower_probe.py --output_dir data/igp24/r12_tower_probe_20260706 --seed 1246 --max_trials 240 --limit 10 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 5.0`
      completed in about 12.6s, attempted 240 trials, found 118 valid local
      `r=12` candidates, selected 10 manual-queue rows, and rejected 62
      real-root mismatches plus 60 reducible rows. The selected queue has 9
      `outer_constant_shift` rows and 1 `outer_two_coefficient_shift` row, with
      two selected rows each for inner parameters `s=4,5,6,7,8`. Coefficient
      heights range from `120884` to `8559386`. Tracked artifacts are under
      `data/igp24/r12_tower_probe_20260706/`.
    - Independent validation result: parsed the new JSON/JSONL/TXT artifacts,
      reran local exact checks on all 10 selected rows, and confirmed 25
      integer coefficients per row, monic leading coefficient, nonzero
      constant, coefficient gcd 1, local `real_root_count=12`, irreducible and
      squarefree exact checks, exact `h(q(x))` tower/even support, unique
      hashes, zero latest-follow-up feedback hash overlap, and zero known
      accepted-hash overlap.

## Stage 0: Scaffold

- [done] Register `igp24` Axplorer environment.
- [done] Represent monic degree-24 polynomials as `[a0, ..., a23]`.
- [done] Export candidates as `[a0, ..., a23, 1]`.
- [done] Add exact SymPy utilities for construction, validation, irreducibility,
  squarefreeness, discriminant, real-root count, translations, modular factor
  patterns, canonical hashes, and JSONL ledger records.
- [done] Add PARI, MAGMA, and SAIR verifier stubs that do not run in the
  training loop and do not auto-submit.
- [done] Add fast tests for stage-0 behavior.
- [done] Add a simple project README.

## Stage 1: Candidate Generation

- [done] Add generation strategies beyond uniform random coefficients.
  - [done] Sparse coefficient vectors.
  - [done] Low-height biased dense vectors.
  - [done] Lower-degree coefficient bias.
  - [done] Simple structured binomial/trinomial-like seeds.
- [done] Make generation strategy configurable from the CLI with
  `--igp24_generation_strategy`.
- [done] Record generation strategy in candidate metadata and ledger records.
- [done] Compare strategy yield and score quality across short benchmark
  runs.
- [done] Seed NumPy from `--seed` in the IGP24 environment so short
  process-pool-off benchmarks are reproducible.
- [done] Adjust default `mixed` weights conservatively toward the stronger
  small-sample strategies:
  `uniform:0.10,low_height:0.20,sparse:0.25,lower_degree:0.20,structured:0.25`.
- [done] Add an experimental `target_r=4`-friendlier generation
  strategy.
  - [done] Implement a bounded near-product `four_real_seed` strategy
    based on perturbed `(x^2-a)(x^2-b)(x^20+1)` seeds.
  - [done] Record strategy-specific metadata in ledger records.
  - [done] Add focused generation, metadata, and determinism tests.
  - [done] Benchmark against current `sparse` and `mixed` baselines on
    `target_r=4`.
- [done] Add opt-in target-specific generation presets.
  - [done] Add `--igp24_generation_preset` with `none`, `r0`, `r2`,
    and `r4` choices.
  - [done] Preserve default behavior when no preset is selected.
  - [done] Record preset name, target-r intent, resolved strategy, and
    resolved mixed weights in ledger metadata.
  - [done] Add focused preset tests and benchmark helper support.
  - [done] Benchmark the `r4` preset against baseline `mixed` and explicit
    `four_real_seed`.
- [done] Validate and tune the `target_r=4` preset tradeoff.
  - [done] Add benchmark-helper labels for r4 mixed-weight variants.
  - [done] Run a larger CPU-only `target_r=4` benchmark than the previous
    4-seed preset run.
  - [done] Compare baseline `mixed`, explicit `four_real_seed`,
    current `preset_r4`, and r4 mixed-weight variants.
  - [done] Interpret target-r yield versus peak proxy score before changing
    any preset or default.

## Stage 1: Scoring And Metadata

- [done] Preserve proxy-only scoring while making score components easier
  to inspect.
  - [done] Store score component breakdown in each ledger record.
  - [done] Keep `target_t` metadata-only unless exact external verification
    is actually performed.
  - [done] Keep invalid rejection reasons explicit and stable.
- [done] Add target real-root-count benchmark reporting.
  - [done] Extend benchmark helper with `--target_rs`.
  - [done] Summarize target-r match count, match rate, and best matching
    score.
  - [done] Run short untargeted vs `target_r=2` comparison.
- [done] Run larger per-strategy target real-root-count comparisons
  across `target_r=none,0,2,4`.
  - [done] Add aggregate strategy/target reporting to the benchmark
    helper so multi-seed runs are easier to audit.
  - [done] Run the larger CPU-only benchmark with at least `sparse`,
    `structured`, and `mixed`.
  - [done] Record commands, artifact paths, result tables, and
    interpretation before considering any default tuning.

## Stage 1: Local Search

- [done] Improve bounded local search observability.
  - [done] Track attempted, accepted, and rejected move counts.
  - [done] Track the accepted move type.
  - [done] Record whether accepted moves improved height, discriminant,
    root-count match, or modular diversity.
  - [done] Preserve determinism under a fixed seed.

## Stage 1: CLI And Smoke Runs

- [done] Add practical short CPU-only commands to documentation.
- [done] Run a small reproducible CPU-only generation smoke.
- [done] Record exact command, runtime, valid candidate count, best score, and
  ledger path below.
- [done] Add a small GPU-readiness and training-smoke milestone.
  - [done] Inspect and document current `train.py` CUDA support.
    - Result: `--cpu true` forces CPU; otherwise `train.py` selects MPS when
      available and CUDA after that, moves the model and training/evaluation
      batches to `args.device`, and logs CUDA memory during epochs. It does
      not preflight `torch.cuda.is_available()`, so the smoke must probe
      PyTorch CUDA before running GPU training.
  - [done] Confirm `nvidia-smi` GPU visibility and PyTorch CUDA
    availability.
    - Result: outside the managed sandbox, `nvidia-smi` saw an
      NVIDIA GeForce RTX 5090 with 32607 MiB and driver 596.49; PyTorch
      `2.12.1+cu130` reported `cuda_available=True` and device
      `NVIDIA GeForce RTX 5090`.
  - [done] Add a lightweight GPU-smoke helper only if it improves
    reproducibility of command execution and artifact summaries.
    - Result: `scripts/igp24_gpu_smoke.py` writes
      `gpu_smoke_summary.json` and `gpu_smoke_report.md`, keep all runs
      proxy-only, and skip GPU training when PyTorch CUDA is unavailable.
  - [done] Add focused tests for pure parsing/reporting logic.
    - Result: `tests/test_igp24_gpu_smoke.py` covers probe parsing, command
      construction, train-log inspection, ledger summary, and recommendation
      logic without requiring GPU hardware.
  - [done] Update README and NOTES with when to use GPU training.
  - [done] Run a tiny CPU data-generation baseline and a tiny GPU-enabled
    training smoke under `/tmp/igp24_gpu_smoke_20260704`.
    - Result: CPU baseline return code 0 in 2.39s; GPU train return code 0 in
      3.88s.
  - [done] Compare return codes, runtimes, valid candidates, ledger record
    counts, metadata completeness, and whether GPU was actually used.
    - Result: CPU baseline had 7 valid examples, 12 ledger rows, complete
      metadata, and logged `device: cpu`; GPU train had 4 valid examples after
      one tiny training epoch, 12 ledger rows, complete metadata, logged
      `device: cuda`, logged CUDA memory, and `gpu_used=True`.
  - [done] Document whether to keep CPU proxy-search primary, switch to GPU
    training, or run both in parallel.
    - Recommendation: run both in parallel. Keep CPU proxy-search, shortlist
      export, and exact-tool prep as the main candidate pipeline; use GPU
      training as a parallel sampler path for a controlled longer run.
- [done] Add a reusable per-strategy benchmark helper.
  - [done] Add `scripts/igp24_benchmark.py` to run short CPU-only `train.py`
    jobs and summarize JSONL ledgers.
  - [done] Add fast tests for benchmark summary aggregation.
  - [done] Verify helper CLI with `--help`.
  - [done] Run the helper across all generation strategies.
- [in_progress] Run a short controlled GPU sampler probe before considering a
  30-60 minute training run.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect `train.py` and existing GPU smoke helper/test surfaces.
    - Result: the next probe should reuse the existing CUDA/NVML probes and
      ledger summary logic, but needs a more explicit sampler-train command,
      timeout, and loss/memory/sample-log parser than the tiny smoke helper.
  - [done] Add a reproducible short sampler-probe helper if useful.
    - Result: `scripts/igp24_gpu_sampler_probe.py` wraps a
      capped two-epoch CUDA train/sample command, summarizes the ledger and
      train log, and writes a JSON/Markdown report.
  - [done] Add tests only for pure command construction, log parsing, and
    report/recommendation logic.
    - Result: `tests/test_igp24_gpu_sampler_probe.py` covers sample-section
      parsing, train-log loss/memory parsing, model-sample ledger filtering,
      capped command construction, baseline loading, and recommendation logic
      without requiring GPU hardware.
  - [done] Run a capped roughly 5-10 minute GPU training/sampling probe
    under `/tmp/igp24_gpu_sampler_probe_20260704`.
    - Result: completed short CUDA sampler runs in about 183-185 seconds with
      return code 0, two epochs, eight finite eval points, and `device: cuda`.
      A utilization-monitored rerun was interrupted after the user observed
      `nvidia-smi` sitting near zero utilization; no active GPU process
      remained afterward.
  - [done] Record CUDA/PyTorch status, runtime, loss/eval behavior, CUDA
    memory logs, sampled-candidate validity, ledger counts, metadata
    completeness, and whether the result justifies another short probe or a
    later medium run.
    - Result: unmonitored completed run showed PyTorch `2.12.1+cu130` on the
      RTX 5090, max CUDA reserved memory 76 MiB, final train/test losses around
      `0.618` / `1.382`, 910 valid sampled candidates out of 1024 requested,
      1728 ledger rows, 1615 `manual` model-sampled rows, and complete
      metadata. Because live utilization appeared near zero, this does not
      justify a 30-60 minute GPU run yet.
    - Recommendation: run another short GPU probe with adjusted settings that
      explicitly targets nontrivial GPU utilization, for example more
      GPU-side model/batch work and less CPU-side scoring pressure. Keep CPU
      proxy-search and exact-tool prep primary.
- [in_progress] Diagnose GPU utilization with CPU sampling/scoring isolated.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect `train.py`, `src/trainer.py`, `src/evaluator.py`, the GPU
    sampler helper, tests, README, NOTES, and this TODO.
    - Result: model and train/eval batches are moved to `args.device`, but
      each normal epoch immediately enters CPU-heavy sampling, detokenization,
      scoring, local search, and dataset update work. A train-only opt-in path
      is the smallest clean way to isolate GPU-side training.
  - [done] Add the smallest safe opt-in train-only path if needed.
    - Result: added non-default `--train_only`; normal epochs still sample,
      score, local-search, and update datasets unless this flag is explicitly
      true.
  - [done] Add or adjust a helper mode for a capped utilization-focused
    train-only GPU probe.
    - Result: extended `scripts/igp24_gpu_sampler_probe.py` with
      `--probe_mode train_only_utilization`, a larger CUDA training workload,
      `--num_samples_from_model 0`, `--train_only true`, and utilization
      reporting for max/average GPU utilization.
  - [done] Add focused tests only for pure command construction and
    recommendation/reporting logic.
    - Result: added tests for train-only command construction, train-only log
      parsing, and train-only recommendation actions. Focused test run passed:
      10 passed in 0.03s.
  - [done] Run the capped train-only utilization probe, below 10 minutes.
    - Command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode train_only_utilization --output_dir /tmp/igp24_gpu_train_only_probe_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
    - Result: return code 0, no timeout, no interruption, runtime 34.1s.
  - [done] Record device/CUDA status, runtime/timeout, max/average GPU
    utilization, max CUDA memory, train/eval loss behavior, whether
    sampling/scoring/local search was avoided, and whether any longer GPU run
    is justified.
    - Result: `nvidia-smi` saw an RTX 5090 with driver 596.49 and 32607 MiB;
      PyTorch `2.12.1+cu130` reported CUDA available and device
      `NVIDIA GeForce RTX 5090`; train log recorded `device: cuda`.
    - Utilization: 33 parsed monitor samples, max GPU utilization 95.0%,
      average GPU utilization 20.67%, max monitored GPU memory 5814 MiB.
    - Training: one epoch, 240 steps, four finite eval points, final
      train/test loss about `0.698` / `0.724`, max PyTorch CUDA allocated
      97.17 MiB, max PyTorch CUDA reserved 110.0 MiB.
    - Isolation: post-training CPU sampling/scoring/local search was skipped;
      `sample_requested_total=0`, `sample_valid_total=0`, and
      `model_sample_ledger_records=0` by design.
    - Recommendation: do not start a medium 30-60 minute run from the earlier
      sampler path. GPU training itself can load the RTX 5090, so the next
      architecture step should decouple GPU training/sampling from CPU
      scoring/local search while CPU proxy-search and exact-tool prep remain
      primary.
  - [done] Run final verification and cleanup before push.
    - Result: full `python3` pytest passed, compileall passed, helper help
      passed, import check passed, `git diff --check` passed, Stage 4 remains
      present in this TODO, literal `python -m pytest` is still blocked because
      the shell has no `python` executable, no active Python/GPU compute
      process remained after the probe, and generated `__pycache__`
      directories were cleaned.
- [in_progress] Decouple GPU model sampling from CPU proxy scoring/local
  search.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect `train.py`, `src/trainer.py`, `src/evaluator.py`,
    `src/datasets.py`, `scripts/igp24_gpu_sampler_probe.py`, README, NOTES,
    TODO, and relevant tests.
    - Result: `sample_and_score` currently generates token sequences on the
      selected device, then immediately sends them into detokenization,
      proxy scoring, optional local search, and dataset update work. The IGP24
      tokenizer can decode raw token sequences into coefficient vectors
      without scoring, so an export-only sampler can split model generation
      from CPU scoring without changing normal defaults.
  - [done] Add an opt-in export-only model-sampling path that writes raw
    token sequences and decoded coefficient vectors without scoring, local
    search, exact verification, dataset update, network calls, or submission.
    - Result: added `sample_and_export` plus `--sample_export_only` and
      `--sample_export_path` to `train.py`. The default path still uses
      `sample_and_score`; export-only mode writes unscored JSONL rows with raw
      token IDs, decoded coefficient vectors when possible, and safety flags.
  - [done] Add a small CPU-side import/scoring helper if useful to prove
    the exported samples can be consumed by the proxy pipeline, with local
    search explicit and off by default.
    - Result: added `scripts/igp24_score_sample_export.py`, which consumes
      sample-export JSONL, scores decoded coefficient vectors through the
      existing proxy scorer, leaves local search off by default, writes
      `scored_samples.jsonl`, `score_summary.json`, and `score_report.md`,
      and does not run exact verifiers, SAIR/network calls, or submission.
  - [done] Add focused tests only for export format, command construction,
    parsing/reporting, and safety flags.
    - Result: focused tests passed: 18 passed in 1.36s across the GPU helper
      and sample-export tests.
  - [done] Run a short capped split-workflow smoke, not a 30-60 minute job,
    and audit artifact paths, record counts, GPU utilization if practical, and
    scoring-consumption results.
    - GPU export command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split --output_dir /tmp/igp24_gpu_sample_export_split_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
    - GPU export result: return code 0, no timeout, no interruption, runtime
      16.8s, `device: cuda`, two finite eval points, final train/test loss
      about `0.909` / `0.729`, max monitored GPU utilization 91.0%, average
      monitored GPU utilization 11.125%, and max monitored GPU memory
      4887 MiB.
    - Export artifact:
      `/tmp/igp24_gpu_sample_export_split_20260704/gpu_model_sample_export.jsonl`
      with 256 unscored model-sample rows, all 256 decoded to coefficient
      vectors; `sample_requested_total=0`, `sample_valid_total=0`, and
      `model_sample_ledger_records=0` because CPU scoring/local search was
      avoided during GPU sampling.
    - CPU scoring command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_20260704/gpu_model_sample_export.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_20260704/cpu_scored_export --max_records 64 --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
    - CPU scoring result: read 256 exported rows, selected 64, decoded 64
      inputs, scored 64 through the proxy scorer, found 56 valid and
      8 rejected records, local search disabled. Scored output:
      `/tmp/igp24_gpu_sample_export_split_20260704/cpu_scored_export/scored_samples.jsonl`.
    - Interpretation: the GPU can now produce auditable unscored sample
      exports and the CPU proxy helper can consume them separately. This is a
      real decoupling step, but a medium 30-60 minute GPU run should still wait
      until the split path gets batching/queueing ergonomics and a larger short
      export/scoring smoke.
  - [done] Update README, NOTES, and TODO with the decoupling result and
    whether a later medium GPU run is justified.
    - Result: README and NOTES now document the `sample_export_split` GPU
      smoke, the separate CPU scoring helper command, artifact paths, record
      counts, safety boundary, and recommendation to run a larger short split
      smoke before any medium GPU run.
- [in_progress] Harden the split GPU-sampling to CPU-scoring workflow.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
    `scripts/igp24_gpu_sampler_probe.py`, `scripts/igp24_score_sample_export.py`,
    and relevant tests.
    - Result: the split is functional but audit details are spread across
      multiple files. The CPU scoring helper is the right place to write a
      combined manifest/report because it can link the source export, GPU
      probe summary, scored JSONL, score summary, command line, safety flags,
      and hash/dedup counts after scoring.
  - [done] Add a combined split-workflow manifest/report linking export
    JSONL, train log, GPU probe summary/report, CPU score summary/report, and
    scored JSONL.
    - Result: `scripts/igp24_score_sample_export.py` now writes
      `split_workflow_manifest.json` and `split_workflow_report.md` beside the
      score summary/report, auto-linking a sibling
      `gpu_sampler_probe_summary.json` when present.
  - [done] Record source commit, command lines, counts, safety flags,
    artifact paths, runtime, and duplicate/canonical-hash summaries.
    - Result: the manifest records source commit, GPU/CPU command lines,
      linked artifact paths, GPU runtime/utilization/sample-export counts, CPU
      scoring counts/runtime, proxy-only safety flags, and canonical-hash
      dedup statistics.
  - [done] Make scoring all decoded export rows or an explicit capped
    subset clear in helper arguments and summaries.
    - Result: added `--score_all true` as an explicit all-rows mode while
      preserving `--max_records` for capped runs; summaries record
      `selection_mode`.
  - [done] Add focused tests for pure manifest/reporting, dedup/hash
    summaries, command construction, and safety flags.
    - Result: focused tests passed: 22 passed in 1.15s, including a parser
      regression check that false boolean defaults are not treated as truthy.
  - [done] Run a larger short split smoke, around 512-1024 exported samples
    with a larger CPU scoring subset, capped well under 10 minutes.
    - GPU export command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split --output_dir /tmp/igp24_gpu_sample_export_split_larger_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
    - GPU export result: return code 0, no timeout, no interruption, runtime
      32.079s, logged `device: cuda`, two finite eval points, final
      train/test loss about `0.878` / `0.706`, max monitored GPU utilization
      93.0%, average monitored GPU utilization 17.516%, max monitored GPU
      memory 5457 MiB, 1024 export rows, and 1024 decoded export rows.
      GPU-side CPU scoring/local search was avoided.
    - CPU score command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_larger_20260704/gpu_model_sample_export.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export --max_records 512 --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
    - CPU score result: runtime 19.719s, 1024 rows read, 512 selected with
      `selection_mode=capped`, 512 decoded/scored, 450 valid proxy-scored,
      62 rejected, 512 unique canonical hashes, 0 duplicate hash records,
      local search disabled.
    - Artifacts:
      `/tmp/igp24_gpu_sample_export_split_larger_20260704/gpu_model_sample_export.jsonl`,
      `/tmp/igp24_gpu_sample_export_split_larger_20260704/gpu_sampler_probe_summary.json`,
      `/tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export/score_summary.json`,
      `/tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export/scored_samples.jsonl`,
      `/tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export/split_workflow_manifest.json`,
      and
      `/tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export/split_workflow_report.md`.
  - [done] Update README, NOTES, and TODO with commands, paths, counts,
    interpretation, and whether another short split smoke or a medium run is
    next.
    - Result: docs record the larger split smoke and recommend one more short
      split smoke, preferably all-row scoring or a small target-setting
      comparison, before any medium 30-60 minute GPU run.
- [in_progress] Validate the split workflow with all decoded export rows
  scored in a short handoff.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
    `scripts/igp24_gpu_sampler_probe.py`, `scripts/igp24_score_sample_export.py`,
    and relevant tests.
    - Result: the opt-in export path remains isolated from normal `train.py`
      behavior, and `scripts/igp24_score_sample_export.py` already records
      `selection_mode=all_explicit` when `--score_all true` is used.
  - [done] Add or tighten focused tests for all-row scoring/report behavior.
    - Result: added a score-all regression test proving all exported records
      are selected, `score_all` stays true, `max_records` stays unset, and the
      split manifest records `selection_mode=all_explicit`.
  - [done] Run a short GPU export smoke around the current 1024-row scale.
    - Command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split --output_dir /tmp/igp24_gpu_sample_export_split_score_all_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
    - Result: return code 0, no timeout, no interruption, runtime 32.273s,
      logged `device: cuda`, two finite eval points, final train/test loss
      about `0.911` / `0.742`, max monitored GPU utilization 94.0%, average
      monitored GPU utilization 14.516%, max monitored GPU memory 5320 MiB,
      1024 export rows, and 1023 decoded export rows. GPU-side CPU scoring
      and local search were avoided.
  - [done] Score all decoded export rows with `--score_all true`,
    `--local_search false`, and `--max_local_search_steps 0`.
    - Command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_model_sample_export.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
    - Result: runtime 36.724s, 1024 rows read and selected with
      `selection_mode=all_explicit`, 1023 decoded/scored, 1 skipped decode,
      908 valid proxy-scored, 115 rejected, 1022 unique canonical hashes,
      1 duplicate canonical-hash record, local search disabled.
    - Artifacts:
      `/tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_model_sample_export.jsonl`,
      `/tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_sampler_probe_summary.json`,
      `/tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all/score_summary.json`,
      `/tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all/scored_samples.jsonl`,
      `/tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all/split_workflow_manifest.json`,
      and
      `/tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all/split_workflow_report.md`.
  - [done] Update README, NOTES, and TODO with exact commands, artifact
    paths, counts, interpretation, and whether a later medium GPU run is
    justified.
    - Result: a later bounded 30-60 minute GPU run is now reasonable only as
      an export-only sampler run with the same manifest discipline and a
      separate CPU score/review phase. Do not return to an integrated GPU
      train/sample/score loop.
- [done] Add and run a bounded medium export-only split workflow.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect TODO, README, NOTES, `scripts/igp24_gpu_sampler_probe.py`,
    `scripts/igp24_score_sample_export.py`, `train.py`, `src/evaluator.py`,
    and relevant tests.
    - Result: `sample_export_only` remains an explicit opt-in path, normal
      `train.py` behavior remains unchanged, and a one-epoch medium helper
      mode avoids fixed export-path overwrites across epochs.
  - [done] Add an explicit bounded medium helper mode.
    - Result: added `sample_export_split_medium`, which still calls
      `train.py` with `--sample_export_only true`, `--always_search false`,
      `--max_local_search_steps 0`, `--process_pool false`, and CPU scoring
      avoided during the GPU phase. Medium caps are one epoch, 12000 training
      steps, 8192 requested export samples, and a 3600s timeout cap.
  - [done] Add focused tests for pure medium command construction,
    recommendation behavior, caps, and safety flags.
    - Result: tests now assert the medium mode is export-only, local
      search/process-pool scoring paths are off, caps are bounded, and the
      command contains no SAIR/MAGMA/PARI execution.
  - [done] Run focused tests and commit the implementation checkpoint.
    - Result: focused tests passed: 25 passed in 1.27s. Helper help now
      exposes `--probe_mode ... sample_export_split_medium`, and compileall
      passed for the edited helper/test files.
  - [done] Interrupt and retune the first medium attempt when it proved
    CPU-seed-bound.
    - First medium command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_medium --output_dir /tmp/igp24_gpu_sample_export_split_medium_20260704 --timeout_seconds 3600 --monitor_interval_seconds 5`
    - Interrupted result: return code 130 after 153.119s, no timeout, no eval
      points, 0 export rows, 1840 initial ledger rows, max monitored GPU
      utilization 98.0%, average monitored GPU utilization 10.433%, max
      monitored GPU memory 10262 MiB. Train log showed epoch 0 started only
      around 2m22s because the initial CPU seed generation was too large.
    - Retune: keep the medium GPU training/export target but reduce the
      initial CPU seed set back to the proven short-run scale (`gensize=512`,
      `pop_size=384`, `ntest=16`, `gen_batch_size=64`) so GPU training starts
      quickly.
    - Retuned focused checks: 25 passed in 1.12s; compileall and helper help
      still passed.
  - [done] Run the retuned medium GPU export-only split job with monitoring
    and an explicit 3600s timeout.
    - Command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_medium --output_dir /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704 --timeout_seconds 3600 --monitor_interval_seconds 5`
    - Result: return code 0, no timeout, no interruption, runtime
      1300.803s, logged `device: cuda`, 20 finite eval points, final
      train/test loss about `0.238` / `2.665`, max monitored GPU utilization
      99.0%, average monitored GPU utilization 95.977%, max monitored GPU
      memory 10141 MiB, 8192 export rows, and 8192 decoded export rows.
      GPU-side CPU scoring/local search/dataset update was avoided.
    - Artifacts:
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/gpu_model_sample_export_medium.jsonl`,
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/gpu_sampler_probe_summary.json`,
      and
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/gpu_sampler_probe_report.md`.
  - [done] Score all decoded rows if runtime is reasonable; otherwise
    score a clearly documented capped CPU subset, with local search disabled.
    - Command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/gpu_model_sample_export_medium.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
    - Result: return code 0, runtime 264.635s,
      `selection_mode=all_explicit`, 8192 rows read/selected, 8192
      decoded/scored, 0 skipped decode, 8188 valid proxy-scored, 4 rejected,
      384 unique canonical hashes, 7808 duplicate hash records, local search
      disabled.
    - Artifacts:
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all/score_summary.json`,
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all/scored_samples.jsonl`,
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all/split_workflow_manifest.json`,
      and
      `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all/split_workflow_report.md`.
  - [done] Update README, NOTES, and TODO with exact commands, artifact
    paths, counts, comparison against the prior short score-all handoff, and
    recommendation.
    - Result: the docs now record that the medium run fixed GPU utilization
      but exposed duplicate-heavy sampling. Recommendation: improve export
      diversity before longer GPU runs; do not return to integrated GPU
      train/sample/score, and keep CPU proxy-search plus exact-tool prep
      primary.
- [in_progress] Improve GPU export sample diversity before longer runs.
  - [done] Pull latest before starting.
    - Result: `git pull --ff-only` was already up to date.
  - [done] Inspect TODO, README, NOTES, `scripts/igp24_gpu_sampler_probe.py`,
    `scripts/igp24_score_sample_export.py`, `train.py`, `src/evaluator.py`,
    and relevant tests.
    - Result: normal `train.py` behavior remains unchanged; the smallest
      useful next step is an explicit diversity-focused export-only helper
      mode with named short-run variants, followed by separate CPU score-all
      handoffs with local search disabled.
  - [done] Add an opt-in diversity export helper mode and focused
    pure command/report tests.
    - Result: added `sample_export_split_diversity` with two named
      export-only variants: `fixed_template_t09_top9` and
      `mixed_t12_open_topk`. Both keep `--sample_export_only true`,
      `--always_search false`, `--max_local_search_steps 0`,
      `--process_pool false`, one epoch, 1200 training steps, 2048 requested
      export samples, and a 900s intended timeout cap.
    - Focused checks: 27 passed in 2.29s across GPU helper and sample-export
      tests; helper `--help` exposes the new mode/variants; compileall passed
      for the edited helper/test files; `git diff --check` passed.
  - [done] Run at least two short diversity export variants with explicit
    timeout caps.
    - Fixed-template command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t09_top9 --output_dir /tmp/igp24_gpu_sample_export_diversity_fixed_20260704 --timeout_seconds 900 --monitor_interval_seconds 2`
    - Fixed-template GPU result: return code 0, no timeout, runtime
      148.684s, `device: cuda`, 4 finite eval points, final train/test loss
      about `0.670` / `0.732`, max monitored GPU utilization 99.0%,
      average monitored GPU utilization 80.808%, max monitored GPU memory
      about 10310 MiB, 2048 export rows, 2047 decoded rows, and GPU-side CPU
      scoring/local search/dataset update avoided.
    - Mixed/high-temp command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant mixed_t12_open_topk --output_dir /tmp/igp24_gpu_sample_export_diversity_mixed_20260704 --timeout_seconds 900 --monitor_interval_seconds 2`
    - Mixed/high-temp GPU result: return code 0, no timeout, runtime
      152.369s, `device: cuda`, 4 finite eval points, final train/test loss
      about `0.265` / `2.829`, max monitored GPU utilization 99.0%,
      average monitored GPU utilization 80.135%, max monitored GPU memory
      about 10310 MiB, 2048 export rows, 2030 decoded rows, and GPU-side CPU
      scoring/local search/dataset update avoided.
  - [done] Score each export separately on the CPU proxy path with local
    search disabled.
    - Fixed-template CPU score command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/gpu_model_sample_export_diversity_fixed_template_t09_top9.jsonl --output_dir /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
    - Fixed-template CPU score result: return code 0, runtime 76.537s,
      `selection_mode=all_explicit`, 2048 rows read/selected, 2047
      decoded/scored, 1 skipped decode, 1799 valid proxy-scored, 248
      rejected, 2039 unique canonical hashes, 8 duplicate hash records, best
      score 9964.435, mean score 8720.207, local search disabled.
    - Fixed-template artifacts:
      `/tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all/score_summary.json`,
      `/tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all/scored_samples.jsonl`,
      `/tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all/split_workflow_manifest.json`,
      and
      `/tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all/split_workflow_report.md`.
    - Mixed/high-temp CPU score command:
      `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/gpu_model_sample_export_diversity_mixed_t12_open_topk.jsonl --output_dir /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
    - Mixed/high-temp CPU score result: return code 0, runtime 77.709s,
      `selection_mode=all_explicit`, 2048 rows read/selected, 2030
      decoded/scored, 18 skipped decode, 1921 valid proxy-scored, 109
      rejected, 1067 unique canonical hashes, 963 duplicate hash records,
      best score 9969.676, mean score 9396.872, local search disabled.
    - Mixed/high-temp artifacts:
      `/tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all/score_summary.json`,
      `/tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all/scored_samples.jsonl`,
      `/tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all/split_workflow_manifest.json`,
      and
      `/tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all/split_workflow_report.md`.
    - Interpretation: both short variants dramatically improve uniqueness
      relative to the duplicate-heavy medium baseline
      (384 unique / 8192 scored; 7808 duplicate records). The fixed-template
      short variant is the better diversity probe at 2039 unique / 2047 scored
      with only 8 duplicate records. The mixed/high-temp variant has better
      validity and score metrics, but weaker diversity at 1067 unique / 2030
      scored with 963 duplicate records.
  - [done] Update README, NOTES, and TODO with commands, artifact paths,
    GPU utilization, valid/rejected counts, unique/duplicate hash counts,
    best/mean score, comparison to the duplicate-heavy medium baseline, and
    next recommendation.
    - Result: README and NOTES now document the diversity helper mode, exact
      variant commands, CPU score-all handoff commands, artifacts, GPU
      utilization, score/diversity metrics, and recommendation. The fixed
      short variant is the clear uniqueness winner; the mixed/high-temp
      variant improves validity/score but duplicates more. Next GPU work
      should test diversity-preserving scale-up, such as multiple short
      fixed-template seeds with dedup-aware CPU merge/review, before another
      single longer export.
  - [in_progress] Test diversity-preserving fixed-template scale-up across
    multiple short GPU seeds before any single longer export.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, probe/scoring helpers, `train.py`,
      `src/evaluator.py`, and relevant tests.
      - Result: Stage 4 remains present; normal `train.py` and integrated
        train/sample/score defaults should stay unchanged. The smallest useful
        workflow is an opt-in seed override for the existing diversity export
        helper plus a proxy-only merge helper for scored export directories.
    - [done] Add a bounded opt-in diversity seed override and a
      dedup-aware scored-export merge helper.
      - Result: `sample_export_split_diversity` now accepts
        `--diversity_seed`; overridden seeds are threaded into the CUDA
        command, summary, report, caps, and artifact names. Added
        `scripts/igp24_merge_scored_exports.py` to merge scored export
        directories without running exact verifiers, network calls, or
        submissions.
    - [done] Run focused tests, helper help checks, and compile/import
      checks before the first periodic commit.
      - Result: focused tests passed with 31 passed in 2.31s; compileall
        passed for the edited helper/test files; GPU probe `--help` exposes
        `--diversity_seed`; merge helper `--help` passed; import check passed
        for the probe and merge helper.
    - [done] Run three short fixed-template GPU export-only seeds
      (`2301`, `2302`, `2303`) with explicit timeout caps.
      - Seed `2301` command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t09_top9 --diversity_seed 2301 --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2301` result: return code 0, no timeout, runtime 150.639s,
        `device: cuda`, 4 finite eval points, final train/test loss about
        `0.418` / `1.635`, max monitored GPU utilization 99.0%, average
        monitored GPU utilization 81.027%, max CUDA reserved 242 MiB, 2048
        export rows, 2040 decoded rows, and GPU-side CPU scoring/local
        search/dataset update avoided. During the run, `nvidia-smi` also
        showed about 98% GPU utilization and about 10958 MiB in use.
      - Seed `2301` artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/gpu_sampler_probe_report.md`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2301.jsonl`.
      - Seed `2302` command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t09_top9 --diversity_seed 2302 --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2302` result: return code 0, no timeout, runtime 152.238s,
        `device: cuda`, 4 finite eval points, final train/test loss about
        `0.298` / `2.087`, max monitored GPU utilization 99.0%, average
        monitored GPU utilization 80.0%, max CUDA reserved 242 MiB, 2048
        export rows, 2047 decoded rows, and GPU-side CPU scoring/local
        search/dataset update avoided.
      - Seed `2302` artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_sampler_probe_report.md`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2302.jsonl`.
      - Seed `2303` command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t09_top9 --diversity_seed 2303 --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2303` result: return code 0, no timeout, runtime 148.275s,
        `device: cuda`, 4 finite eval points, final train/test loss about
        `0.434` / `1.829`, max monitored GPU utilization 99.0%, average
        monitored GPU utilization 81.653%, max CUDA reserved 242 MiB, 2048
        export rows, 2043 decoded rows, and GPU-side CPU scoring/local
        search/dataset update avoided.
      - Seed `2303` artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/gpu_sampler_probe_report.md`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2303.jsonl`.
    - [done] Score each export on the CPU proxy path with
      `--score_all true`, `--local_search false`, and
      `--max_local_search_steps 0`.
      - Seed `2301` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2301.jsonl --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2301` CPU score result: return code 0, runtime 70.714s,
        `selection_mode=all_explicit`, 2048 rows read/selected, 2040
        decoded/scored, 8 skipped decode, 1881 valid proxy-scored, 159
        rejected, 1132 unique canonical hashes, 908 duplicate hash records,
        best score 9955.382, mean score 9150.606, local search disabled.
      - Seed `2301` CPU artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all/split_workflow_manifest.json`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all/split_workflow_report.md`.
      - Seed `2302` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2302.jsonl --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2302` CPU score result: return code 0, runtime 64.256s,
        `selection_mode=all_explicit`, 2048 rows read/selected, 2047
        decoded/scored, 1 skipped decode, 2031 valid proxy-scored, 16
        rejected, 452 unique canonical hashes, 1595 duplicate hash records,
        best score 9951.923, mean score 9845.475, local search disabled.
      - Seed `2302` CPU artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all/split_workflow_manifest.json`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all/split_workflow_report.md`.
      - Seed `2303` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2303.jsonl --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2303` CPU score result: return code 0, runtime 69.415s,
        `selection_mode=all_explicit`, 2048 rows read/selected, 2043
        decoded/scored, 5 skipped decode, 1983 valid proxy-scored, 60
        rejected, 772 unique canonical hashes, 1271 duplicate hash records,
        best score 9954.908, mean score 9630.741, local search disabled.
      - Seed `2303` CPU artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all/split_workflow_manifest.json`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all/split_workflow_report.md`.
    - [done] Merge the three scored JSONLs and report total scored,
      valid/rejected, unique hashes, duplicate hash records, cross-seed
      overlap, best/mean proxy score, top hash-deduped candidates, and
      artifact paths.
      - Merge command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/merged_dedup_review --top_n 25`
      - Combined merge result: 6130 scored records, 5895 valid
        proxy-scored, 235 rejected, 2356 unique canonical hashes, 3774
        duplicate hash records, 981 duplicated canonical hashes, best score
        9955.382, mean score 9542.663.
      - Cross-seed overlap: 0 shared canonical hashes for `2301` vs `2302`,
        0 for `2301` vs `2303`, 0 for `2302` vs `2303`, and 0 hashes seen
        in multiple seed sources.
      - Interpretation: multi-seed fixed-template exports do add fresh
        canonical hashes across seeds and beat the duplicate-heavy medium
        baseline on unique hashes (2356 unique / 6130 scored vs 384 unique /
        8192 scored). However, internal per-seed diversity is seed-sensitive:
        seed `2301` kept 1132 unique hashes, while seeds `2302` and `2303`
        produced only 452 and 772 unique hashes. The single earlier
        fixed-template seed `2201` remains the cleanest short diversity run
        at 2039 unique / 2047 scored.
      - Merge artifacts:
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/merged_dedup_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/merged_dedup_review/merged_dedup_report.md`,
        and
        `/tmp/igp24_gpu_multiseed_fixed_template_20260704/merged_dedup_review/top_deduped_candidates.jsonl`.
    - [done] Update README, TODO, and any relevant notes with commands,
      results, interpretation, and next recommendation.
      - Result: README now documents `--diversity_seed`, the merge helper,
        exact three-seed GPU export commands, CPU score-all commands, merge
        command, per-seed metrics, merged dedup metrics, and interpretation.
        `NOTES_IGP24.md` now records the same planning conclusion: multi-seed
        fixed-template export adds fresh cross-seed hashes, but per-run
        diversity is seed-sensitive and should be improved before a longer
        fixed-template export.
    - [done] Run final verification, confirm Stage 4 remains present, and
      audit GPU/process state.
      - Result: focused tests passed with 31 passed in 1.08s; full pytest
        passed with 72 passed in 1.52s; compileall passed for `train.py`,
        `src`, `tests`, and `scripts`; GPU probe, score helper, and merge
        helper `--help` checks passed; import check passed for `train`,
        `igp24`, score helper, probe helper, and merge helper; `git diff
        --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 2698.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active `python3` processes.
      - Cleanup: generated `__pycache__` directories from compile/test runs
        were removed; follow-up `find . -type d -name __pycache__` returned
        no paths.
      - Literal `python -m pytest` remains blocked with `/bin/bash: line 1:
        python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
    - [done] Commit and push final docs/results state.
      - Result: pushed commits through `63c357f` to `igp24-dev`.
  - [in_progress] Diagnose and improve per-run fixed-template export
    diversity before any longer fixed-template GPU run.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, GPU probe/export helpers,
      score/merge helpers, `train.py`, `src/evaluator.py`, polynomial
      canonicalization, and relevant tests.
      - Result: export JSONL rows already contain sample index, batch index,
        batch row, token IDs, decoded coefficients, temperature, top-k,
        device, strategy metadata, and safety flags. A post-export diagnostic
        helper is the smallest useful first mechanism because it can report
        exact coefficient and translation-canonical duplicate trajectories
        before CPU scoring without changing normal `train.py` defaults.
    - [done] Add a proxy-only raw export diversity diagnostic helper
      and focused tests.
      - Result: added `scripts/igp24_export_diversity_diagnostic.py`, which
        reads one or more raw sample-export JSONLs and reports decoded/invalid
        counts, exact coefficient uniqueness, translation-canonical hash
        uniqueness, token-sequence uniqueness, top duplicate groups,
        per-batch summaries, and checkpoint trajectories. It is diagnostic
        only: no scoring, no local search, no exact verifier execution, no
        SAIR/network calls, and no submission behavior.
    - [done] Add two opt-in fixed-template entropy variants to compare
      against the current `fixed_template_t09_top9` behavior.
      - Result: added `fixed_template_t10_top12` and
        `fixed_template_t11_open_topk` to the opt-in
        `sample_export_split_diversity` helper. Both preserve export-only
        GPU behavior and use `fixed_sparse_template`; normal `train.py`
        defaults and existing variants are unchanged.
    - [done] Run focused tests, compile, help, and import checks before the
      first periodic commit.
      - Result: focused tests passed with 35 passed in 1.21s; compileall
        passed for the edited helper/test files; diagnostic helper `--help`
        passed; GPU probe `--help` shows the new variants; import check
        passed for the diagnostic helper and variant registry.
    - [done] Run diagnostics on existing seed `2201` and seeds
      `2301`-`2303` to investigate why per-run diversity differed.
      - Command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/gpu_model_sample_export_diversity_fixed_template_t09_top9.jsonl /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2301.jsonl /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2302.jsonl /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2303.jsonl --labels seed2201_clean seed2301 seed2302 seed2303 --output_dir /tmp/igp24_export_diversity_diagnostic_20260704/baseline_fixed_seeds --checkpoint_interval 256 --top_n 10`
      - Result: return code 0, runtime 179.182s. Seed `2201_clean` had
        2047 decoded rows, 2039 exact unique coefficient vectors, 8 exact
        duplicate records, 2039 canonical unique hashes, 8 canonical
        duplicate records, 2039 unique token sequences, and 8 token duplicate
        records. Seed `2301` had 2040 decoded rows, 1132 exact/canonical
        uniques, 908 exact/canonical duplicate records, 1133 unique token
        sequences, and 907 token duplicate records. Seed `2302` had 2047
        decoded rows, 452 exact/canonical/token uniques, and 1595 duplicate
        records by all three views. Seed `2303` had 2043 decoded rows, 772
        exact/canonical/token uniques, and 1271 duplicate records by all
        three views.
      - Interpretation: the duplicate-heavy seeds are not mainly a
        translation-canonicalization artifact. They are exact decoded
        coefficient/token repeats emitted by the model sampler. Cross-seed
        exact and canonical overlap remained zero across all seed pairs, so
        the collapse is within-run repetition.
      - Artifacts:
        `/tmp/igp24_export_diversity_diagnostic_20260704/baseline_fixed_seeds/export_diversity_summary.json`,
        `/tmp/igp24_export_diversity_diagnostic_20260704/baseline_fixed_seeds/export_diversity_report.md`,
        and
        `/tmp/igp24_export_diversity_diagnostic_20260704/baseline_fixed_seeds/top_duplicate_groups.jsonl`.
    - [done] Run two short export-only GPU intervention probes, each
      shorter than a 30-60m run and with CPU scoring/local search avoided
      during the GPU phase.
      - Preliminary `fixed_template_t10_top32` attempt on seed `2302`:
        loaded CUDA and reached 99.0% max monitored GPU utilization, but
        exited with return code 1 after 147.326s before export rows were
        written. Cause: `RuntimeError: selected index k out of range` from
        `torch.topk`, because `top_k=32` exceeded the tokenizer vocabulary.
        This variant was replaced with bounded `fixed_template_t10_top12`.
      - `fixed_template_t10_top12` seed `2302` command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t10_top12 --diversity_seed 2302 --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302 --timeout_seconds 900 --monitor_interval_seconds 2`
      - `fixed_template_t10_top12` GPU result: return code 0, no timeout,
        runtime 150.884s, `device: cuda`, 4 finite eval points, final
        train/test loss about `0.487` / `1.780`, max monitored GPU
        utilization 99.0%, average monitored GPU utilization 80.892%, max
        CUDA reserved 242 MiB, 2048 export rows, 2041 decoded rows, and
        GPU-side CPU scoring/local search/dataset update avoided.
      - `fixed_template_t10_top12` artifacts:
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/gpu_sampler_probe_report.md`,
        and
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/gpu_model_sample_export_diversity_fixed_template_t10_top12_seed2302.jsonl`.
      - `fixed_template_t11_open_topk` seed `2302` command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t11_open_topk --diversity_seed 2302 --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302 --timeout_seconds 900 --monitor_interval_seconds 2`
      - `fixed_template_t11_open_topk` GPU result: return code 0, no
        timeout, runtime 151.480s, `device: cuda`, 4 finite eval points,
        final train/test loss about `0.633` / `0.872`, max monitored GPU
        utilization 99.0%, average monitored GPU utilization 80.851%, max
        CUDA reserved 242 MiB, 2048 export rows, 2043 decoded rows, and
        GPU-side CPU scoring/local search/dataset update avoided.
      - `fixed_template_t11_open_topk` artifacts:
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/gpu_sampler_probe_report.md`,
        and
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2302.jsonl`.
    - [done] Score only the necessary intervention exports on the CPU
      proxy path with `--score_all true`, `--local_search false`, and
      `--max_local_search_steps 0`.
      - Pre-score intervention diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2302.jsonl /tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/gpu_model_sample_export_diversity_fixed_template_t10_top12_seed2302.jsonl /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2302.jsonl --labels baseline_t09_top9_seed2302 t10_top12_seed2302 t11_open_seed2302 --output_dir /tmp/igp24_export_diversity_diagnostic_20260704/intervention_compare_seed2302 --checkpoint_interval 256 --top_n 10`
      - Pre-score diagnostic result: return code 0, runtime 137.824s.
        Baseline `t09_top9` seed `2302`: 2047 decoded rows, 452 exact /
        canonical / token uniques, and 1595 duplicate records. `t10_top12`
        seed `2302`: 2041 decoded rows, 1288 exact / canonical / token
        uniques, and 753 duplicate records. `t11_open_topk` seed `2302`:
        2043 decoded rows, 2030 exact / canonical / token uniques, and 13
        duplicate records.
      - Diagnostic interpretation: increasing entropy directly improved the
        raw repeated-token/coefficient collapse. `t11_open_topk` is the first
        intervention to recover seed-`2201`-like per-run uniqueness on the
        formerly duplicate-heavy seed `2302`.
      - Diagnostic artifacts:
        `/tmp/igp24_export_diversity_diagnostic_20260704/intervention_compare_seed2302/export_diversity_summary.json`,
        `/tmp/igp24_export_diversity_diagnostic_20260704/intervention_compare_seed2302/export_diversity_report.md`,
        and
        `/tmp/igp24_export_diversity_diagnostic_20260704/intervention_compare_seed2302/top_duplicate_groups.jsonl`.
      - `fixed_template_t10_top12` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/gpu_model_sample_export_diversity_fixed_template_t10_top12_seed2302.jsonl --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - `fixed_template_t10_top12` CPU score result: return code 0,
        runtime 72.863s, `selection_mode=all_explicit`, 2048 rows
        read/selected, 2041 decoded/scored, 7 skipped decode, 1888 valid
        proxy-scored, 153 rejected, 1288 unique canonical hashes, 753
        duplicate hash records, best score 9953.439, mean score 9177.150,
        local search disabled.
      - `fixed_template_t11_open_topk` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2302.jsonl --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - `fixed_template_t11_open_topk` CPU score result: return code 0,
        runtime 76.778s, `selection_mode=all_explicit`, 2048 rows
        read/selected, 2043 decoded/scored, 5 skipped decode, 1833 valid
        proxy-scored, 210 rejected, 2030 unique canonical hashes, 13
        duplicate hash records, best score 9956.519, mean score 8900.449,
        local search disabled.
      - Intervention merge command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all --labels baseline_t09_top9_seed2302 t10_top12_seed2302 t11_open_seed2302 --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/merged_intervention_review --top_n 25`
      - Intervention merge result: 6131 scored rows across three sources,
        5752 valid, 379 rejected, 3546 unique canonical hashes, 2585
        duplicate hash records, 220 hashes seen in multiple sources, best
        score 9956.519, mean score 9308.085. Pairwise overlap was 219
        hashes between baseline and `t10_top12`, 4 between baseline and
        `t11_open_topk`, and 5 between `t10_top12` and `t11_open_topk`.
      - CPU/merge artifacts:
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/merged_intervention_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/merged_intervention_review/merged_dedup_report.md`,
        and
        `/tmp/igp24_gpu_export_entropy_interventions_20260704/merged_intervention_review/top_deduped_candidates.jsonl`.
    - [done] Compare diagnostics and CPU dedup results against the
      duplicate-heavy fixed-template seeds and produce the next
      recommendation.
      - Result: `fixed_template_t11_open_topk` is the clear per-run
        diversity intervention. On the same duplicate-heavy seed `2302`, it
        improved from 452 unique / 2047 scored and 1595 duplicates to 2030
        unique / 2043 scored and 13 duplicates, while also finding the best
        single proxy score in the comparison. Tradeoff: validity dropped from
        2031 valid / 16 rejected for baseline to 1833 valid / 210 rejected,
        and mean proxy score dropped from 9845.475 to 8900.449. `t10_top12`
        was a middle tradeoff at 1288 unique / 2041 scored but still kept 753
        duplicates.
      - Recommendation: do not start a longer fixed-template run yet. Use
        `fixed_template_t11_open_topk` as the next short diversity-preserving
        GPU export configuration, preferably across 2-3 seeds with the raw
        export diagnostic run immediately after each export. If the next goal
        changes code, the highest-leverage control is a true dedup-aware
        export cap/stop policy, since duplicate collapse is visible in raw
        token/coefficient outputs before scoring.
    - [done] Update README, NOTES, and TODO with commands, artifacts,
      metrics, interpretation, and next action.
      - Result: README now documents the raw export diagnostic helper, the
        diagnostic finding that duplicate-heavy seeds repeat exact
        token/coefficient outputs before scoring, the bounded entropy
        intervention commands, the `top_k=32` trap, the comparison table, and
        the next recommendation. `NOTES_IGP24.md` records the planning
        conclusion: `fixed_template_t11_open_topk` is the best short
        diversity-preserving next configuration, while a future dedup-aware
        export cap/stop policy is the highest-leverage code control.
    - [done] Run final verification, confirm Stage 4 remains present, audit
      GPU/process state, and cleanup generated caches.
      - Result: focused tests passed with 35 passed in 1.26s; full pytest
        passed with 76 passed in 1.68s; compileall passed for `train.py`,
        `src`, `tests`, and `scripts`; diagnostic, GPU probe, score helper,
        and merge helper `--help` checks passed; import check passed for
        `train`, `igp24`, score helper, probe helper, merge helper, and
        diagnostic helper; `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 2907.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active `python3` processes.
      - Cleanup: generated `__pycache__` directories from compile/test runs
        were removed; follow-up `find . -type d -name __pycache__` returned
        no paths.
      - Literal `python -m pytest` remains blocked with `/bin/bash: line 1:
        python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
    - [in_progress] Commit and push final verified state.
  - [in_progress] Validate `fixed_template_t11_open_topk` across multiple
    short GPU export-only seeds.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, GPU probe helper, raw export
      diagnostic helper, score helper, merge helper, `train.py`,
      `src/evaluator.py`, and relevant tests.
      - Result: existing opt-in helper already supports
        `fixed_template_t11_open_topk` with `--diversity_seed`; raw export
        diagnostic already reports decoded rows, exact unique coefficient
        vectors, canonical unique hashes, token unique sequences, duplicate
        records, top duplicate groups, and checkpoint trajectory. No code
        changes are needed before the validation run.
    - [done] Run short export-only GPU seeds `2401`, `2402`, and
      `2403`, with raw export diagnostics immediately after each export.
      - Seed `2401` GPU command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t11_open_topk --diversity_seed 2401 --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2401` GPU result: return code 0, no timeout, runtime
        156.373s, `device: cuda`, 4 finite eval points, final train/test
        loss about `0.369` / `2.075`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 82.658%, max CUDA reserved 242
        MiB, 2048 export rows, 2043 decoded rows, and GPU-side CPU
        scoring/local search/dataset update avoided. Live `nvidia-smi`
        during the run showed about 98% GPU utilization and about 10559 MiB
        in use.
      - Seed `2401` diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2401.jsonl --labels seed2401_t11_open --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2401` diagnostic result: return code 0, runtime 42.280s,
        2048 rows read, 2043 decoded, 5 invalid decode, 675 exact unique
        coefficient vectors, 1368 exact duplicate records, 675 canonical
        unique hashes, 1368 canonical duplicate records, 675 unique token
        sequences, and 1368 token duplicate records.
      - Interpretation: seed `2401` is a duplicate-heavy failure case for
        `fixed_template_t11_open_topk`, so the intervention is not
        automatically stable across seeds. Continue the bounded seed sweep,
        but do not score this export unless later comparison requires it.
      - Seed `2401` artifacts:
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2401.jsonl`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/export_diversity_diagnostic/export_diversity_summary.json`,
        and
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2401/export_diversity_diagnostic/export_diversity_report.md`.
      - Seed `2402` GPU command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t11_open_topk --diversity_seed 2402 --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2402` GPU result: return code 0, no timeout, runtime
        154.531s, `device: cuda`, 4 finite eval points, final train/test
        loss about `0.431` / `1.642`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 82.733%, max CUDA reserved 242
        MiB, 2048 export rows, 2037 decoded rows, and GPU-side CPU
        scoring/local search/dataset update avoided.
      - Seed `2402` diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2402.jsonl --labels seed2402_t11_open --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2402` diagnostic result: return code 0, runtime 47.360s,
        2048 rows read, 2037 decoded, 11 invalid decode, 1217 exact unique
        coefficient vectors, 820 exact duplicate records, 1217 canonical
        unique hashes, 820 canonical duplicate records, 1217 unique token
        sequences, and 820 token duplicate records.
      - Interpretation: seed `2402` is a partial diversity recovery but not
        seed-`2201`/seed-`2302 t11_open` quality; continue the bounded sweep
        before deciding whether CPU scoring is useful.
      - Seed `2402` artifacts:
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2402.jsonl`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/export_diversity_diagnostic/export_diversity_summary.json`,
        and
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/export_diversity_diagnostic/export_diversity_report.md`.
      - Seed `2403` GPU command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t11_open_topk --diversity_seed 2403 --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2403` GPU result: return code 0, no timeout, runtime
        147.805s, `device: cuda`, 4 finite eval points, final train/test
        loss about `0.434` / `1.808`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 81.750%, max CUDA reserved 242
        MiB, 2048 export rows, 2026 decoded rows, and GPU-side CPU
        scoring/local search/dataset update avoided.
      - Seed `2403` diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2403.jsonl --labels seed2403_t11_open --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2403` diagnostic result: return code 0, runtime 45.994s,
        2048 rows read, 2026 decoded, 22 invalid decode, 1088 exact unique
        coefficient vectors, 938 exact duplicate records, 1088 canonical
        unique hashes, 938 canonical duplicate records, 1088 unique token
        sequences, and 938 token duplicate records.
      - Seed `2403` artifacts:
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2403.jsonl`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/export_diversity_diagnostic/export_diversity_summary.json`,
        and
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/export_diversity_diagnostic/export_diversity_report.md`.
      - Export diagnostic interpretation: `fixed_template_t11_open_topk`
        is not stable across the fresh seed block. Prior seed `2302` had
        2030 unique / 2043 decoded and only 13 duplicates, but fresh seeds
        `2401`, `2402`, and `2403` had only 675, 1217, and 1088 canonical
        unique hashes with 1368, 820, and 938 duplicates respectively.
    - [done] Decide from diagnostics which exports are worth CPU
      score-all, then score necessary exports with local search disabled.
      - Decision: skip CPU scoring seed `2401` because raw export diversity
        collapsed badly. Score seeds `2402` and `2403` because they have
        partial recovery above 1000 unique raw/canonical outputs and can
        clarify validity/score tradeoffs.
      - Seed `2402` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2402.jsonl --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2402` CPU score result: return code 0, runtime 71.768s,
        `selection_mode=all_explicit`, 2048 rows read/selected, 2037
        decoded/scored, 11 skipped decode, 1910 valid, 127 rejected, 1217
        unique canonical hashes, 820 duplicate hash records, best score
        9958.729, mean score 9301.895, and local search disabled.
      - Seed `2403` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/gpu_model_sample_export_diversity_fixed_template_t11_open_topk_seed2403.jsonl --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2403` CPU score result: return code 0, runtime 70.270s,
        `selection_mode=all_explicit`, 2048 rows read/selected, 2026
        decoded/scored, 22 skipped decode, 1913 valid, 113 rejected, 1088
        unique canonical hashes, 938 duplicate hash records, best score
        9952.131, mean score 9367.702, and local search disabled.
      - CPU score artifacts:
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all/split_workflow_manifest.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all/split_workflow_report.md`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/cpu_scored_export_all/split_workflow_manifest.json`,
        and
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/cpu_scored_export_all/split_workflow_report.md`.
    - [done] Merge scored outputs and compare against prior clean seed
      `2201`, duplicate-heavy baseline seed `2302`, and intervention seed
      `2302` where useful.
      - Merge command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2403/cpu_scored_export_all --labels seed2201_t09_clean seed2302_t09_baseline seed2302_t11_open seed2402_t11_open seed2403_t11_open --output_dir /tmp/igp24_gpu_t11_open_multiseed_20260704/merged_scored_review --top_n 25`
      - Merge result: five sources, 10200 scored rows, 9486 valid,
        714 rejected, 6822 unique canonical hashes, 3378 duplicate hash
        records, four cross-seed shared hashes, best score 9964.435, and mean
        score 9226.911.
      - Source comparison:
        `seed2201_t09_clean`: 2047 scored, 1799 valid, 248 rejected, 2039
        unique, 8 duplicates, best 9964.435, mean 8720.207.
        `seed2302_t09_baseline`: 2047 scored, 2031 valid, 16 rejected, 452
        unique, 1595 duplicates, best 9951.923, mean 9845.475.
        `seed2302_t11_open`: 2043 scored, 1833 valid, 210 rejected, 2030
        unique, 13 duplicates, best 9956.519, mean 8900.449.
        `seed2402_t11_open`: 2037 scored, 1910 valid, 127 rejected, 1217
        unique, 820 duplicates, best 9958.729, mean 9301.895.
        `seed2403_t11_open`: 2026 scored, 1913 valid, 113 rejected, 1088
        unique, 938 duplicates, best 9952.131, mean 9367.702.
      - Top merged candidates: the best overall proxy score remained from
        `seed2201_t09_clean` at 9964.435. The best fresh `t11_open` result in
        this validation was seed `2402` at 9958.729, ranked third in the
        merged dedup report.
      - Merge artifacts:
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/merged_scored_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/merged_scored_review/merged_dedup_report.md`,
        and
        `/tmp/igp24_gpu_t11_open_multiseed_20260704/merged_scored_review/top_deduped_candidates.jsonl`.
      - Stability conclusion: `fixed_template_t11_open_topk` is not stable
        enough to promote as the next longer-run configuration. It can produce
        excellent diversity on some seeds, but two of three fresh seeds
        duplicated heavily and the third still landed far below the clean
        seed `2302`/seed `2201` uniqueness regime. Do not run a longer
        fixed-template job yet; implement dedup-aware export control or live
        uniqueness monitoring next.
    - [done] Update README, NOTES, and TODO with commands, artifacts,
      metrics, stability interpretation, and next action.
      - Result: README and NOTES now record the fresh-seed validation table,
        merged review summary, artifact path, and recommendation to implement
        dedup-aware export control before any longer fixed-template run.
    - [done] Run final verification, confirm Stage 4 remains present,
      audit GPU/process state, cleanup generated caches, commit, and push.
      - Focused split/export tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`
        - Result: 35 passed in 1.18s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 76 passed in 1.58s.
      - Compileall:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks passed for `igp24_gpu_sampler_probe.py`,
        `igp24_score_sample_export.py`, `igp24_merge_scored_exports.py`, and
        `igp24_export_diversity_diagnostic.py`.
      - Import check passed:
        `imports ok True True True True True True`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 3132.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active `python3` processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [in_progress] Implement opt-in dedup-aware GPU sample-export control.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
      GPU probe helper, raw export diagnostic helper, score helper, merge
      helper, and focused tests.
      - Result: the existing `--sample_export_only` path already avoids CPU
        proxy scoring, local search, exact tools, SAIR/network, and dataset
        updates during GPU sampling, but it writes every decoded duplicate.
        The smallest safe change is default-off uniqueness accounting in
        `sample_and_export`, with probe-helper flags for a bounded dedup-aware
        smoke.
    - [done] Add default-off export controls for a target number of
      unique decoded coefficient vectors, a maximum attempt budget, periodic
      uniqueness progress logging, duplicate-skipped counters, and explicit
      stop reasons.
      - Result: `train.py` now exposes default-off
        `--sample_export_dedup`, `--sample_export_unique_target`,
        `--sample_export_max_attempts`, and
        `--sample_export_progress_interval`. `src/evaluator.py` keeps the
        normal export behavior unchanged unless those controls are enabled;
        the opt-in path skips duplicate decoded coefficient tuples, records
        attempted samples, unique decoded count, skipped duplicates, and
        `stop_reason`, and writes a sidecar summary JSON.
      - Result: `scripts/igp24_gpu_sampler_probe.py` now exposes
        `--probe_mode sample_export_split_dedup`, reusing the bounded
        export-only CUDA shape with `--diversity_variant`,
        `--diversity_seed`, `--dedup_unique_target`,
        `--dedup_max_attempts`, and `--dedup_progress_interval`.
    - [done] Add focused tests for command construction, uniqueness
      accounting, stop reasons, and report fields.
      - Result:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
        passed with 31 tests in 1.14s.
      - Result:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src/evaluator.py scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
        passed.
      - Result: `git diff --check` passed.
    - [done] Update README, NOTES, and TODO with CLI usage and
      interpretation.
      - Result: README and NOTES now document
        `--probe_mode sample_export_split_dedup`, the new `train.py` export
        flags, the sidecar `EXPORT.jsonl.summary.json`, and the key summary
        fields for interpreting duplicate avoidance.
    - [done] Run a short bounded GPU export-only smoke with the new mode,
      raw export diagnostics immediately afterward, and bounded CPU scoring
      only if diagnostics justify it.
      - First in-sandbox command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2401 --dedup_unique_target 512 --dedup_max_attempts 2048 --dedup_progress_interval 128 --output_dir /tmp/igp24_gpu_dedup_export_20260704/seed2401 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Result: sandboxed NVML/CUDA access was blocked, so the helper wrote
        a skipped GPU summary with PyTorch CUDA unavailable in that context.
        The same bounded command was rerun outside the sandbox for actual GPU
        validation.
      - GPU dedup smoke command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2401 --dedup_unique_target 512 --dedup_max_attempts 2048 --dedup_progress_interval 128 --output_dir /tmp/igp24_gpu_dedup_export_20260704/seed2401 --timeout_seconds 900 --monitor_interval_seconds 2`
      - GPU dedup smoke result: return code 0, no timeout, runtime
        147.243s, `device: cuda`, four finite eval points, final train/test
        loss about `0.323` / `1.951`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 80.736%, max CUDA reserved 242
        MiB, and GPU-phase CPU scoring/local search/dataset update avoided.
      - Dedup export result: target 512 unique decoded coefficient vectors
        reached after 1439 attempts out of a 2048-attempt budget; 516 rows
        written, 512 decoded rows, 4 invalid decode rows, 512 unique decoded
        coefficient vectors, 923 duplicate decoded rows skipped, and
        `stop_reason=unique_target_reached`.
      - Raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_export_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u512_a2048.jsonl --labels seed2401_t11_open_dedup_u512 --output_dir /tmp/igp24_gpu_dedup_export_20260704/seed2401/export_diversity_diagnostic --checkpoint_interval 128 --top_n 10`
      - Raw diagnostic result: return code 0, 516 rows read, 512 decoded,
        4 invalid decode, 512 exact unique coefficient vectors, 0 exact
        duplicate records, 512 canonical unique hashes, 0 canonical duplicate
        records, 512 token unique sequences, and 0 token duplicate records.
      - CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_export_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u512_a2048.jsonl --output_dir /tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - CPU score result: return code 0, runtime 19.968s,
        `selection_mode=all_explicit`, 516 rows read/selected, 512 decoded
        input rows, 4 skipped decode, 512 scored, 501 valid, 11 rejected, 512
        unique canonical hashes, 0 duplicate hash records, best score
        9954.661, mean score 9708.264, and local search disabled.
      - Interpretation: the dedup-aware export reduced duplicate waste on
        the known duplicate-heavy `t11_open` seed `2401`. The prior full raw
        export wrote 2048 rows with 2043 decoded, 675 unique, and 1368
        duplicate records. The new opt-in export stopped after 1439 attempts,
        wrote 516 audit rows, reached 512 decoded uniques, skipped 923
        duplicate decoded attempts, and had zero duplicates in the raw
        diagnostic and scored output.
      - Artifacts:
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u512_a2048.jsonl`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u512_a2048.jsonl.summary.json`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/export_diversity_diagnostic/export_diversity_report.md`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all/scored_samples.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all/split_workflow_manifest.json`.
    - [done] Run final verification, confirm Stage 4 remains present,
      audit GPU/process state, cleanup generated caches, commit, and push.
      - Focused split/export tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`
        - Result: 38 passed in 1.23s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 79 passed in 1.61s.
      - Compileall:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks passed for `igp24_gpu_sampler_probe.py`,
        `igp24_score_sample_export.py`, `igp24_merge_scored_exports.py`, and
        `igp24_export_diversity_diagnostic.py`.
      - Import check passed:
        `imports ok True True True True True True`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 3250.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active `python3` processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [in_progress] Validate larger dedup-aware GPU sample-export scaling.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
      GPU probe helper, raw export diagnostic helper, score helper, merge
      helper, and focused tests.
      - Result: `sample_export_split_dedup` is already implemented as an
        opt-in helper mode with default-off `train.py` flags; the larger
        validation can run without code changes. The first run should use
        duplicate-heavy seed `2401`, target 1024 unique decoded coefficient
        vectors, 4096 attempt budget, and raw diagnostic immediately after
        export.
    - [done] Run seed `2401` larger dedup-aware export-only GPU
      validation and raw diagnostic.
      - GPU dedup scale command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2401 --dedup_unique_target 1024 --dedup_max_attempts 4096 --dedup_progress_interval 256 --output_dir /tmp/igp24_gpu_dedup_scale_20260704/seed2401 --timeout_seconds 900 --monitor_interval_seconds 2`
      - GPU dedup scale result: return code 0, no timeout, runtime
        147.031s, `device: cuda`, four finite eval points, final train/test
        loss about `0.538` / `1.532`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 81.347%, max CUDA reserved 242
        MiB, and GPU-phase CPU scoring/local search/dataset update avoided.
      - Dedup export result: target 1024 unique decoded coefficient vectors
        reached after 1219 attempts out of a 4096-attempt budget; 1036 rows
        written, 1024 decoded rows, 12 invalid decode rows, 1024 unique
        decoded coefficient vectors, 183 duplicate decoded rows skipped, and
        `stop_reason=unique_target_reached`.
      - Raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_scale_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u1024_a4096.jsonl --labels seed2401_t11_open_dedup_u1024 --output_dir /tmp/igp24_gpu_dedup_scale_20260704/seed2401/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Raw diagnostic result: return code 0, 1036 rows read, 1024 decoded,
        12 invalid decode, 1024 exact unique coefficient vectors, 0 exact
        duplicate records, 1024 canonical unique hashes, 0 canonical
        duplicate records, 1024 token unique sequences, and 0 token duplicate
        records.
      - CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_scale_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u1024_a4096.jsonl --output_dir /tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - CPU score result: return code 0, runtime 38.107s,
        `selection_mode=all_explicit`, 1036 rows read/selected, 1024 decoded
        input rows, 12 skipped decode, 1024 scored, 909 valid, 115 rejected,
        1024 unique canonical hashes, 0 duplicate hash records, best score
        9952.933, mean score 8807.756, and local search disabled.
      - Interpretation: the larger target successfully scales past the
        512-unique smoke on seed `2401`: it reached 1024 uniques well before
        the 4096-attempt cap and still wrote a zero-duplicate raw/scored
        export. Compared with the 512-unique smoke, it needed fewer attempts
        per unique in this run but had lower validity/mean score after CPU
        scoring.
      - Artifacts:
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u1024_a4096.jsonl`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2401_u1024_a4096.jsonl.summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/export_diversity_diagnostic/export_diversity_report.md`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all/scored_samples.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all/split_workflow_manifest.json`.
    - [done] Decide whether a second seed such as `2402` is useful
      within the bounded plan.
      - Decision: seed `2401` reached the larger target cleanly within a
        short run, so run seed `2402` with the same 1024-unique target and
        4096-attempt budget to test cross-seed behavior.
      - Seed `2402` GPU dedup scale command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2402 --dedup_unique_target 1024 --dedup_max_attempts 4096 --dedup_progress_interval 256 --output_dir /tmp/igp24_gpu_dedup_scale_20260704/seed2402 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2402` GPU dedup scale result: return code 0, no timeout,
        runtime 147.989s, `device: cuda`, four finite eval points, final
        train/test loss about `0.316` / `1.883`, max monitored GPU
        utilization 99.0%, average monitored GPU utilization 80.514%, max
        CUDA reserved 242 MiB, and GPU-phase CPU scoring/local search/dataset
        update avoided.
      - Seed `2402` dedup export result: target 1024 unique decoded
        coefficient vectors reached after 3255 attempts out of a
        4096-attempt budget; 1026 rows written, 1024 decoded rows, 2 invalid
        decode rows, 1024 unique decoded coefficient vectors, 2229 duplicate
        decoded rows skipped, and `stop_reason=unique_target_reached`.
      - Seed `2402` raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_scale_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1024_a4096.jsonl --labels seed2402_t11_open_dedup_u1024 --output_dir /tmp/igp24_gpu_dedup_scale_20260704/seed2402/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2402` raw diagnostic result: return code 0, 1026 rows read,
        1024 decoded, 2 invalid decode, 1024 exact unique coefficient
        vectors, 0 exact duplicate records, 1024 canonical unique hashes, 0
        canonical duplicate records, 1024 token unique sequences, and 0 token
        duplicate records.
      - Seed `2402` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_scale_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1024_a4096.jsonl --output_dir /tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2402` CPU score result: return code 0, runtime 37.669s,
        `selection_mode=all_explicit`, 1026 rows read/selected, 1024 decoded
        input rows, 2 skipped decode, 1024 scored, 953 valid, 71 rejected,
        1024 unique canonical hashes, 0 duplicate hash records, best score
        9966.150, mean score 9233.465, and local search disabled.
      - Interpretation: the larger target also scales on seed `2402`, but it
        is much less attempt-efficient than seed `2401`: 3255 attempts for
        1024 uniques and 2229 duplicate attempts skipped. The written export
        is still zero-duplicate and scored cleanly, and it found the strongest
        proxy candidate in this validation block.
      - Seed `2402` artifacts:
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1024_a4096.jsonl`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1024_a4096.jsonl.summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/export_diversity_diagnostic/export_diversity_report.md`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all/scored_samples.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all/split_workflow_manifest.json`.
    - [done] Merge scored larger-dedup outputs with relevant baselines if
      multiple scored outputs exist.
      - Merge command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all --labels seed2201_t09_clean seed2302_t11_open seed2402_t11_open_full2048 seed2401_t11_dedup512 seed2401_t11_dedup1024 seed2402_t11_dedup1024 --output_dir /tmp/igp24_gpu_dedup_scale_20260704/merged_scored_review --top_n 25`
      - Merge result: six sources, 8687 scored rows, 7905 valid, 782
        rejected, 7449 unique canonical hashes, 1238 duplicate hash records,
        397 hashes seen in multiple sources, best score 9966.150, and mean
        score 9028.051.
      - Source comparison:
        `seed2201_t09_clean`: 2047 scored, 1799 valid, 248 rejected, 2039
        unique, 8 duplicates, best 9964.435, mean 8720.207.
        `seed2302_t11_open`: 2043 scored, 1833 valid, 210 rejected, 2030
        unique, 13 duplicates, best 9956.519, mean 8900.449.
        `seed2402_t11_open_full2048`: 2037 scored, 1910 valid, 127
        rejected, 1217 unique, 820 duplicates, best 9958.729, mean 9301.895.
        `seed2401_t11_dedup512`: 512 scored, 501 valid, 11 rejected, 512
        unique, 0 duplicates, best 9954.661, mean 9708.264.
        `seed2401_t11_dedup1024`: 1024 scored, 909 valid, 115 rejected,
        1024 unique, 0 duplicates, best 9952.933, mean 8807.756.
        `seed2402_t11_dedup1024`: 1024 scored, 953 valid, 71 rejected, 1024
        unique, 0 duplicates, best 9966.150, mean 9233.465.
      - Overlap notes: `seed2402_t11_open_full2048` shared 267 hashes with
        `seed2402_t11_dedup1024`; `seed2401_t11_dedup512` shared 129 hashes
        with `seed2401_t11_dedup1024`; `seed2401_t11_dedup1024` and
        `seed2402_t11_dedup1024` had zero overlap with each other.
      - Merge artifacts:
        `/tmp/igp24_gpu_dedup_scale_20260704/merged_scored_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_dedup_scale_20260704/merged_scored_review/merged_dedup_report.md`,
        and
        `/tmp/igp24_gpu_dedup_scale_20260704/merged_scored_review/top_deduped_candidates.jsonl`.
      - Scaling conclusion: the 1024-unique dedup-aware mode meaningfully
        reduces written duplicate waste across both seeds and can recover
        clean scored outputs even when the raw model stream is duplicate
        heavy. It is not uniformly attempt-efficient: seed `2402` needed
        3255 attempts for 1024 uniques, which is close enough to the
        4096-attempt cap that any larger target should keep an explicit
        attempt budget and stop-reason audit. A later medium dedup-aware run
        is justified only as a bounded target/budget experiment, not an
        unbounded longer fixed-template run.
    - [done] Update README, NOTES, and TODO with larger-target results and
      recommendation.
      - Result: README and NOTES now summarize the 1024-unique seed `2401`
        and `2402` validation table, the zero-duplicate diagnostics/scored
        outputs, and the recommendation that any medium dedup-aware run remain
        a bounded target/budget experiment with stop-reason auditing.
    - [done] Run final verification, confirm Stage 4 remains present,
      audit GPU/process state, cleanup generated caches, commit, and push.
      - Focused split/export tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`
        - Result: 38 passed in 1.22s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 79 passed in 1.62s.
      - Compileall:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks passed for `igp24_gpu_sampler_probe.py`,
        `igp24_score_sample_export.py`, `igp24_merge_scored_exports.py`, and
        `igp24_export_diversity_diagnostic.py`.
      - Import check passed:
        `imports ok True True True True True True`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 3429.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active `python3` processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [done] Run a bounded medium-style dedup-aware GPU export stress
    test.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
      GPU probe helper, raw export diagnostic helper, score helper, merge
      helper, and focused tests.
      - Result: the existing `sample_export_split_dedup` helper can run the
        stress test without code changes. The helper keeps `sample_export_only`
        true, `sample_export_dedup` true, `always_search` false,
        `max_local_search_steps` 0, and avoids GPU-phase CPU scoring/local
        search/dataset updates.
    - [done] Run seed `2402` bounded 1536-unique dedup-aware
      export-only GPU stress test.
      - GPU dedup stress command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2402 --dedup_unique_target 1536 --dedup_max_attempts 8192 --dedup_progress_interval 512 --output_dir /tmp/igp24_gpu_dedup_medium_20260704/seed2402 --timeout_seconds 1200 --monitor_interval_seconds 2`
      - GPU dedup stress result: return code 0, no timeout, runtime
        153.293s, `device: cuda`, four finite eval points, final train/test
        loss about `0.279` / `2.036`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 81.093%, max monitored GPU memory
        10410 MiB, max CUDA reserved 242 MiB, and GPU-phase CPU
        scoring/local search/dataset update avoided.
      - Dedup export result: the 1536-unique target was not reached. The run
        exhausted the 8192-attempt budget, wrote 1049 rows, decoded 1040
        written rows, had 9 invalid decode rows, reached 1040 unique decoded
        coefficient vectors, skipped 7143 duplicate decoded attempts, and
        recorded `stop_reason=attempt_budget_exhausted`.
      - Live GPU observation while running: `nvidia-smi` showed a `/python3.12`
        compute process at about 98% GPU utilization and about 10380 MiB used.
      - Export artifacts:
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1536_a8192.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1536_a8192.jsonl.summary.json`.
    - [done] Immediately run raw export diversity diagnostic and record
      exact/canonical/token duplicate counts.
      - Raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_medium_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1536_a8192.jsonl --labels seed2402_t11_open_dedup_u1536 --output_dir /tmp/igp24_gpu_dedup_medium_20260704/seed2402/export_diversity_diagnostic --checkpoint_interval 512 --top_n 10`
      - Raw diagnostic result: return code 0, runtime 25.300s, 1049 rows
        read, 1040 decoded, 9 invalid decode, 1040 exact unique coefficient
        vectors, 0 exact duplicate records, 1040 canonical unique hashes, 0
        canonical duplicate records, 1040 token unique sequences, and 0 token
        duplicate records.
      - Raw diagnostic artifacts:
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/export_diversity_diagnostic/export_diversity_report.md`,
        and
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/export_diversity_diagnostic/top_duplicate_groups.jsonl`.
    - [done] CPU-score the export only if the diagnostic justifies it,
      using `--score_all true --local_search false
      --max_local_search_steps 0`.
      - CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_medium_20260704/seed2402/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2402_u1536_a8192.jsonl --output_dir /tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - CPU score result: return code 0, runtime 38.627s,
        `selection_mode=all_explicit`, 1049 rows read/selected, 1040 decoded
        input rows, 9 skipped decode, 1040 scored, 952 valid, 88 rejected,
        1040 unique canonical hashes, 0 duplicate hash records, best score
        9958.729, mean score 9081.130, and local search disabled.
      - CPU score artifacts:
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all/score_report.md`,
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all/split_workflow_manifest.json`,
        and
        `/tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all/split_workflow_report.md`.
    - [done] Merge any scored output with the relevant prior baselines and
      dedup runs.
      - Merge command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all --labels seed2201_t09_clean seed2302_t11_open seed2402_t11_open_full2048 seed2401_t11_dedup512 seed2401_t11_dedup1024 seed2402_t11_dedup1024 seed2402_t11_dedup1536 --output_dir /tmp/igp24_gpu_dedup_medium_20260704/merged_scored_review --top_n 25`
      - Merge result: seven sources, 9727 scored rows, 8857 valid, 870
        rejected, 8121 unique canonical hashes, 1606 duplicate hash records,
        514 hashes seen in multiple sources, best score 9966.150, and mean
        score 9033.726.
      - New source comparison: `seed2402_t11_dedup1536` scored 1040 rows,
        found 952 valid, 88 rejected, 1040 unique canonical hashes, 0
        duplicate hash records, best score 9958.729, and mean score
        9081.130.
      - Overlap notes: `seed2402_t11_dedup1536` shared 341 hashes with the
        prior `seed2402_t11_dedup1024` run and 278 hashes with
        `seed2402_t11_open_full2048`. It had zero overlap with
        `seed2201_t09_clean`, `seed2302_t11_open`, `seed2401_t11_dedup512`,
        and `seed2401_t11_dedup1024`.
      - Merge artifacts:
        `/tmp/igp24_gpu_dedup_medium_20260704/merged_scored_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_dedup_medium_20260704/merged_scored_review/merged_dedup_report.md`,
        and
        `/tmp/igp24_gpu_dedup_medium_20260704/merged_scored_review/top_deduped_candidates.jsonl`.
    - [done] Decide whether the 1536 target is viable under bounded
      attempts or whether the next step should use multiple smaller dedup
      seeds.
      - Decision: the 1536-unique target is not viable for seed `2402` under
        an 8192-attempt bounded budget. The run stayed GPU-bound and produced
        a clean scored export, but it exhausted the budget at 1040 uniques
        after skipping 7143 duplicate decoded attempts. Do not run the
        optional fresh seed `2404` in this goal because the required
        condition, reaching target quickly with good GPU state, was not met.
        The next GPU sampling goal should prefer several bounded smaller
        dedup-aware seeds, or a sampler-diversity change before trying a
        larger single-seed target again.
    - [done] Update README/NOTES because the workflow recommendation changed.
      - Result: README and NOTES now summarize the bounded 1536-unique stress
        test, the clean zero-duplicate written/scored export, the exhausted
        attempt budget, and the recommendation to prefer several bounded
        smaller dedup-aware seeds or a sampler-diversity change before trying
        another larger single-seed target.
    - [done] Run final verification, confirm Stage 4 remains present,
      audit GPU/process state, cleanup generated caches, commit, and push.
      - Focused split/export tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`
        - Result: 38 passed in 1.16s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 79 passed in 1.56s.
      - Compileall:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks passed for `igp24_gpu_sampler_probe.py`,
        `igp24_score_sample_export.py`, `igp24_merge_scored_exports.py`, and
        `igp24_export_diversity_diagnostic.py`.
      - Import check passed:
        `imports ok True True True True True True`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 3566 after this final
          status update.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -C python3.12
        -o pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__ -prune -print` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [done] Run bounded multi-seed 1024-unique dedup-aware GPU export
    validation.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
      GPU probe helper, raw export diagnostic helper, score helper, merge
      helper, and relevant tests.
      - Result: the existing `sample_export_split_dedup` helper can run the
        validation without code changes. The helper keeps `sample_export_only`
        true, `sample_export_dedup` true, `always_search` false,
        `max_local_search_steps` 0, and avoids GPU-phase CPU scoring/local
        search/dataset updates. Stage 4 remains present.
    - [done] Run seed `2404` bounded 1024-unique dedup-aware
      export-only GPU validation.
      - GPU dedup command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2404 --dedup_unique_target 1024 --dedup_max_attempts 4096 --dedup_progress_interval 256 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2404` GPU result: return code 0, no timeout, runtime
        148.644s, `device: cuda`, four finite eval points, final train/test
        loss about `0.661` / `0.805`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 80.027%, max monitored GPU memory
        10773 MiB, max CUDA reserved 242 MiB, and GPU-phase CPU
        scoring/local search/dataset update avoided.
      - Seed `2404` dedup export result: target 1024 unique decoded
        coefficient vectors reached after 1027 attempts out of a
        4096-attempt budget; 1027 rows written, 1024 decoded rows, 3 invalid
        decode rows, 1024 unique decoded coefficient vectors, 0 duplicate
        decoded attempts skipped, and `stop_reason=unique_target_reached`.
      - Live GPU observation while running: `nvidia-smi` showed a
        `/python3.12` compute process at about 98% GPU utilization and about
        10538-10562 MiB used.
      - Seed `2404` export artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2404_u1024_a4096.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2404_u1024_a4096.jsonl.summary.json`.
    - [done] Immediately run raw export diversity diagnostic for seed
      `2404`, and CPU-score it only if the diagnostic justifies scoring.
      - Seed `2404` raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2404_u1024_a4096.jsonl --labels seed2404_t11_open_dedup_u1024 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2404` raw diagnostic result: return code 0, 1027 rows read,
        1024 decoded, 3 invalid decode, 1024 exact unique coefficient
        vectors, 0 exact duplicate records, 1024 canonical unique hashes, 0
        canonical duplicate records, 1024 token unique sequences, and 0 token
        duplicate records.
      - Seed `2404` raw diagnostic artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/export_diversity_diagnostic/export_diversity_report.md`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/export_diversity_diagnostic/top_duplicate_groups.jsonl`.
    - [done] CPU-score seed `2404` using `--score_all true
      --local_search false --max_local_search_steps 0`.
      - Seed `2404` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2404_u1024_a4096.jsonl --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2404` CPU score result: return code 0, runtime 37.795s,
        `selection_mode=all_explicit`, 1027 rows read/selected, 1024 decoded
        input rows, 3 skipped decode, 1024 scored, 917 valid, 107 rejected,
        1024 unique canonical hashes, 0 duplicate hash records, best score
        9963.747, mean score 8883.004, and local search disabled.
      - Seed `2404` CPU score artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all/score_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all/scored_samples.jsonl`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all/split_workflow_manifest.json`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all/split_workflow_report.md`.
    - [done] Run seed `2405` with the same bounded 1024-unique settings.
      - Seed `2405` GPU dedup command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2405 --dedup_unique_target 1024 --dedup_max_attempts 4096 --dedup_progress_interval 256 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2405` GPU result: return code 0, no timeout, runtime
        153.832s, `device: cuda`, four finite eval points, final train/test
        loss about `0.429` / `1.619`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 81.493%, max monitored GPU memory
        10602 MiB, max CUDA reserved 242 MiB, and GPU-phase CPU
        scoring/local search/dataset update avoided.
      - Seed `2405` dedup export result: target 1024 unique decoded
        coefficient vectors reached after 1611 attempts out of a
        4096-attempt budget; 1030 rows written, 1024 decoded rows, 6 invalid
        decode rows, 1024 unique decoded coefficient vectors, 581 duplicate
        decoded attempts skipped, and `stop_reason=unique_target_reached`.
      - Live GPU observation while running: `nvidia-smi` showed a
        `/python3.12` compute process at about 98% GPU utilization and about
        10517-10520 MiB used.
      - Seed `2405` export artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2405_u1024_a4096.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2405_u1024_a4096.jsonl.summary.json`.
    - [done] Run raw export diversity diagnostic and CPU-score seed
      `2405` if the diagnostic justifies scoring.
      - Seed `2405` raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2405_u1024_a4096.jsonl --labels seed2405_t11_open_dedup_u1024 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2405` raw diagnostic result: return code 0, 1030 rows read,
        1024 decoded, 6 invalid decode, 1024 exact unique coefficient
        vectors, 0 exact duplicate records, 1024 canonical unique hashes, 0
        canonical duplicate records, 1024 token unique sequences, and 0 token
        duplicate records.
      - Seed `2405` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2405_u1024_a4096.jsonl --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2405` CPU score result: return code 0, runtime 39.032s,
        `selection_mode=all_explicit`, 1030 rows read/selected, 1024 decoded
        input rows, 6 skipped decode, 1024 scored, 929 valid, 95 rejected,
        1024 unique canonical hashes, 0 duplicate hash records, best score
        9950.674, mean score 9000.689, and local search disabled.
      - Seed `2405` artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/export_diversity_diagnostic/export_diversity_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all/score_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all/scored_samples.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all/split_workflow_manifest.json`.
    - [done] Decide whether optional seed `2406` is justified. Run it only
      if seeds `2404` and `2405` both reach target cleanly, GPU state is good,
      and time remains.
      - Decision: run optional seed `2406` with the same bounded settings.
        Seeds `2404` and `2405` both reached the 1024 unique target, used CUDA
        with good monitored GPU utilization, wrote zero-duplicate exports, and
        scored cleanly.
    - [done] Run optional seed `2406` with the same bounded 1024-unique
      settings.
      - Seed `2406` GPU dedup command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_dedup --diversity_variant fixed_template_t11_open_topk --diversity_seed 2406 --dedup_unique_target 1024 --dedup_max_attempts 4096 --dedup_progress_interval 256 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2406 --timeout_seconds 900 --monitor_interval_seconds 2`
      - Seed `2406` GPU result: return code 0, no timeout, runtime
        150.415s, `device: cuda`, four finite eval points, final train/test
        loss about `0.312` / `2.032`, max monitored GPU utilization 99.0%,
        average monitored GPU utilization 81.096%, max monitored GPU memory
        10850 MiB, max CUDA reserved 242 MiB, and GPU-phase CPU
        scoring/local search/dataset update avoided.
      - Seed `2406` dedup export result: the 1024-unique target was not
        reached. The run exhausted the 4096-attempt budget, wrote 862 rows,
        decoded 852 written rows, had 10 invalid decode rows, reached 852
        unique decoded coefficient vectors, skipped 3234 duplicate decoded
        attempts, and recorded `stop_reason=attempt_budget_exhausted`.
      - Live GPU observation while running: `nvidia-smi` showed a
        `/python3.12` compute process at about 98% GPU utilization and about
        10595-10642 MiB used.
      - Seed `2406` export artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/gpu_sampler_probe_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/gpu_sampler_probe_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2406_u1024_a4096.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2406_u1024_a4096.jsonl.summary.json`.
    - [done] Run raw export diversity diagnostic and CPU-score seed
      `2406` if the diagnostic justifies scoring.
      - Seed `2406` raw diagnostic command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py /tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2406_u1024_a4096.jsonl --labels seed2406_t11_open_dedup_u1024 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/export_diversity_diagnostic --checkpoint_interval 256 --top_n 10`
      - Seed `2406` raw diagnostic result: return code 0, 862 rows read,
        852 decoded, 10 invalid decode, 852 exact unique coefficient vectors,
        0 exact duplicate records, 852 canonical unique hashes, 0 canonical
        duplicate records, 852 token unique sequences, and 0 token duplicate
        records.
      - Seed `2406` CPU score command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/gpu_model_sample_export_dedup_fixed_template_t11_open_topk_seed2406_u1024_a4096.jsonl --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
      - Seed `2406` CPU score result: return code 0, runtime 32.091s,
        `selection_mode=all_explicit`, 862 rows read/selected, 852 decoded
        input rows, 10 skipped decode, 852 scored, 794 valid, 58 rejected,
        852 unique canonical hashes, 0 duplicate hash records, best score
        9963.539, mean score 9246.803, and local search disabled.
      - Seed `2406` artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/export_diversity_diagnostic/export_diversity_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/export_diversity_diagnostic/export_diversity_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/cpu_scored_export_all/score_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/cpu_scored_export_all/score_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/cpu_scored_export_all/scored_samples.jsonl`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/cpu_scored_export_all/split_workflow_manifest.json`.
    - [done] Merge scored outputs with relevant prior baselines and dedup
      runs, then compare marginal unique coverage, overlap, validity rate,
      best score, mean score, and attempts per unique across seeds.
      - Required-seed merge command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all --labels seed2201_t09_clean seed2302_t11_open seed2402_t11_open_full2048 seed2401_t11_dedup512 seed2401_t11_dedup1024 seed2402_t11_dedup1024 seed2402_t11_dedup1536 seed2404_t11_dedup1024 seed2405_t11_dedup1024 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/merged_required_seed_review --top_n 25`
      - Required-seed merge result: nine sources, 11775 scored rows, 10703
        valid, 1072 rejected, 10167 unique canonical hashes, 1608 duplicate
        hash records, 515 hashes seen in multiple sources, best score
        9966.150, and mean score 9017.746.
      - Required-seed marginal coverage: prior seven-source review had 8121
        unique hashes; adding required seeds `2404` and `2405` raised that to
        10167, so the two required seeds added 2046 net unique hashes from
        2048 scored rows. Seed `2404` had zero overlap with all prior sources
        and seed `2405` had only tiny overlap with prior seed `2402` sources;
        seeds `2404` and `2405` had zero overlap with each other.
      - Full merge command, including optional seed `2406`:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302/cpu_scored_export_all /tmp/igp24_gpu_t11_open_multiseed_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_export_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2401/cpu_scored_export_all /tmp/igp24_gpu_dedup_scale_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_medium_20260704/seed2402/cpu_scored_export_all /tmp/igp24_gpu_dedup_multiseed_20260705/seed2404/cpu_scored_export_all /tmp/igp24_gpu_dedup_multiseed_20260705/seed2405/cpu_scored_export_all /tmp/igp24_gpu_dedup_multiseed_20260705/seed2406/cpu_scored_export_all --labels seed2201_t09_clean seed2302_t11_open seed2402_t11_open_full2048 seed2401_t11_dedup512 seed2401_t11_dedup1024 seed2402_t11_dedup1024 seed2402_t11_dedup1536 seed2404_t11_dedup1024 seed2405_t11_dedup1024 seed2406_t11_dedup_partial852 --output_dir /tmp/igp24_gpu_dedup_multiseed_20260705/merged_scored_review --top_n 25`
      - Full merge result: ten sources, 12627 scored rows, 11497 valid,
        1130 rejected, 11019 unique canonical hashes, 1608 duplicate hash
        records, 515 hashes seen in multiple sources, best score 9966.150,
        and mean score 9033.201.
      - Full-block marginal coverage: required plus optional seeds added
        2898 net unique hashes from 2900 scored rows over the previous
        seven-source review. Seed `2406` had zero overlap with all included
        sources but was attempt-inefficient, exhausting 4096 attempts at 852
        unique decoded outputs.
      - Per-seed comparison:
        `seed2404_t11_dedup1024`: 1027 attempts / 1024 uniques, 917 valid,
        107 rejected, best 9963.747, mean 8883.004, attempts per unique
        1.003.
        `seed2405_t11_dedup1024`: 1611 attempts / 1024 uniques, 929 valid,
        95 rejected, best 9950.674, mean 9000.689, attempts per unique
        1.573.
        `seed2406_t11_dedup_partial852`: 4096 attempts / 852 uniques, 794
        valid, 58 rejected, best 9963.539, mean 9246.803, attempts per unique
        4.808.
      - Interpretation: bounded smaller multi-seed 1024 exports are
        preferable to another larger single-seed target for immediate
        coverage. The required seeds `2404` and `2405` added almost entirely
        new canonical hashes with much better attempt efficiency than the
        seed-`2402` 1536-target stress test. Seed `2406` shows seed
        sensitivity remains, so the next step should not be simply extending
        every seed longer.
      - Merge artifacts:
        `/tmp/igp24_gpu_dedup_multiseed_20260705/merged_required_seed_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/merged_required_seed_review/merged_dedup_report.md`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/merged_required_seed_review/top_deduped_candidates.jsonl`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/merged_scored_review/merged_dedup_summary.json`,
        `/tmp/igp24_gpu_dedup_multiseed_20260705/merged_scored_review/merged_dedup_report.md`,
        and
        `/tmp/igp24_gpu_dedup_multiseed_20260705/merged_scored_review/top_deduped_candidates.jsonl`.
    - [done] Update README/NOTES because the workflow recommendation changed.
      - Result: README and NOTES now summarize the required seed `2404`/`2405`
        table, optional seed `2406`, the merge coverage gain, and the
        recommendation to continue bounded fresh-seed sampling or add a seed
        triage/diversity diagnostic before spending longer runs on
        duplicate-heavy seeds.
    - [done] Run final verification, confirm Stage 4 remains present,
      audit GPU/process state, cleanup generated caches, commit, and push.
      - Focused split/export tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`
        - Result: 38 passed in 1.21s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 79 passed in 1.64s.
      - Compileall:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks passed for `igp24_gpu_sampler_probe.py`,
        `igp24_score_sample_export.py`, `igp24_merge_scored_exports.py`, and
        `igp24_export_diversity_diagnostic.py`.
      - Import check passed:
        `imports ok True True True True True True`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 3821 after this final
          status update.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 idle after the
        run with no running compute processes; `ps -C python3 -C python3.12
        -o pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__ -prune -print` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [in_progress] Add cheap seed triage/diversity diagnostic for
    dedup-aware GPU exports.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, `train.py`, `src/evaluator.py`,
      GPU probe helper, raw export diagnostic helper, score helper, merge
      helper, and relevant tests.
      - Result: the triage workflow can reuse the existing
        `sample_export_split_dedup` helper mode and its generated
        `gpu_sampler_probe_summary.json` plus export sidecar
        `EXPORT.jsonl.summary.json`; no normal defaults, mixed weights,
        `preset_r4`, or ordinary `train.py` behavior need to change. Stage 4
        remains present.
    - [done] Add triage helper script and focused tests for pure
      parsing/reporting/threshold logic.
      - Implementation: added `scripts/igp24_seed_triage.py`. It runs
        `scripts/igp24_gpu_sampler_probe.py --probe_mode
        sample_export_split_dedup` per seed with default target 256,
        max attempts 1024, progress interval 128, and
        `fixed_template_t11_open_topk`; it writes
        `seed_triage_summary.json`, `seed_triage_report.md`, and
        `seed_triage_records.jsonl`.
      - Initial loose recommendation thresholds were intentionally tested and
        proved too permissive: the first report promoted all four known seeds,
        including duplicate-heavy `2406` and `2402`.
      - Updated default recommendation thresholds:
        promote only if target is reached with attempts/unique `<= 1.08` and
        duplicate skip rate `<= 0.05`; reject if attempt budget is exhausted
        far below target, attempts/unique `>= 1.15`, or duplicate skip rate
        `>= 0.12`; otherwise mark ambiguous and run a larger intermediate
        probe before any 1024-unique export.
      - Focused tests after threshold calibration:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_seed_triage.py`
        - Result: 5 passed in 0.03s.
      - Combined helper tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_seed_triage.py tests/test_igp24_gpu_sampler_probe.py`
        - Result: 26 passed in 0.05s.
      - Help check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_seed_triage.py --help`
        - Result: passed.
    - [done] Run triage on known seeds `2404`, `2405`, `2406`, and
      duplicate-heavy `2402`, then compare recommendations against known
      full-run outcomes.
      - Triage command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_seed_triage.py --seeds 2404 2405 2406 2402 --output_dir /tmp/igp24_seed_triage_20260705 --unique_target 256 --max_attempts 1024 --progress_interval 128 --timeout_seconds 900 --monitor_interval_seconds 2 --known_outcome 2404=good_full_run_seed --known_outcome 2405=acceptable_full_run_seed --known_outcome 2406=duplicate_heavy_full_run_seed --known_outcome 2402=duplicate_heavy_larger_target_seed`
      - Intended metrics: attempted samples, unique decoded count,
        duplicate skipped count, invalid decode count, stop reason,
        attempts per unique, duplicate skip rate, recommendation, and
        comparison to known full-run outcomes.
      - GPU audit during triage: `nvidia-smi` showed the RTX 5090 loaded
        during the seed probes, including 98% GPU utilization and about
        10.7-10.9 GiB monitored memory while the CUDA worker was active.
      - Initial loose-threshold result: all seeds promoted, which was not good
        enough because `2406` and `2402` are known duplicate-heavy outcomes.
        The helper defaults were tightened and the report was regenerated
        from existing artifacts with `--summarize_existing`.
      - Calibrated result table:

        | seed | known outcome | attempts | unique | duplicate skipped | invalid | attempts/unique | duplicate skip rate | recommendation |
        | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
        | 2404 | good_full_run_seed | 256 | 256 | 0 | 0 | 1.000 | 0.000 | promote_seed_to_1024_run |
        | 2405 | acceptable_full_run_seed | 268 | 256 | 11 | 1 | 1.047 | 0.041 | promote_seed_to_1024_run |
        | 2406 | duplicate_heavy_full_run_seed | 297 | 256 | 41 | 0 | 1.160 | 0.138 | reject_seed_for_full_1024_run |
        | 2402 | duplicate_heavy_larger_target_seed | 284 | 256 | 20 | 8 | 1.109 | 0.072 | ambiguous_needs_more_evidence |

      - Interpretation: the cheap target-256 triage is useful as a
        conservative gate, not as a final guarantee. It cleanly promotes the
        two known productive seeds, catches known-bad seed `2406`, and avoids
        falsely promoting seed `2402`; ambiguous seeds should get an
        intermediate 512-unique dedup probe before any full 1024-unique run.
      - Artifacts:
        `/tmp/igp24_seed_triage_20260705/seed_triage_summary.json`,
        `/tmp/igp24_seed_triage_20260705/seed_triage_report.md`, and
        `/tmp/igp24_seed_triage_20260705/seed_triage_records.jsonl`.
    - [done] Update README/NOTES if the triage workflow or recommendation
      changes, run final verification, confirm Stage 4 remains present, audit
      GPU/process state, cleanup generated caches, commit, and push.
      - Result: README and NOTES now document the seed triage helper, the
        calibrated target-256 behavior, and the recommendation to run a
        512-unique intermediate probe for ambiguous seeds before any full
        1024-unique export.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 84 passed in 1.56s.
      - Focused split/export/triage tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_seed_triage.py tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`
        - Result: 43 passed in 1.14s.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_seed_triage.py --help`,
        `scripts/igp24_gpu_sampler_probe.py --help`,
        `scripts/igp24_score_sample_export.py --help`,
        `scripts/igp24_merge_scored_exports.py --help`, and
        `scripts/igp24_export_diversity_diagnostic.py --help`
        - Result: all passed.
      - Import check: `train`, `ENVS`, score helper, GPU probe helper, merge
        helper, raw diversity diagnostic, and seed triage helper all imported;
        `igp24` was registered and expected helper functions were present.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 3930 after this final
          status update.
      - GPU/process audit: final `nvidia-smi` showed the RTX 5090 idle with
        no running compute processes; `ps -C python3 -C python3.12 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__ -prune -print` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [done] Add safe offline MAGMA verification workflow for reviewed
    IGP24 candidates.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, verifier stubs,
      `scripts/igp24_offline_verify.py`, shortlist/review helpers,
      score/merge helpers, and relevant tests.
      - Result: the existing offline helper validates review batches and
        writes manual PARI/MAGMA scripts, but it does not yet emit
        per-candidate MAGMA result JSONL, exact-label parse results, cache
        entries, timeout/unavailable statuses, or a verifier report. The new
        workflow should extend this helper and preserve all training/GPU/proxy
        defaults. Stage 4 remains present.
    - [done] Extend the offline helper with MAGMA availability
      detection, per-candidate dry-run/run records, strict timeouts, cache
      reuse, parser logic, summary/report artifacts, and support for review
      directories plus candidate/coefficient files.
      - Implementation: `scripts/igp24_offline_verify.py` now accepts a
        review-batch directory, candidate JSONL, or coefficient text file;
        writes `magma_verification_results.jsonl`,
        `magma_verification_summary.json`, `magma_verification_report.md`,
        `magma_verification_cache.json`, per-candidate MAGMA scripts, and raw
        output files; and records statuses including `dry_run`, `unavailable`,
        `timeout`, `parse_error`, `invalid_input`, and `verified`.
      - Safety: MAGMA execution remains explicit via `--run_magma`, uses a
        per-candidate timeout, preserves proxy labels separately from exact
        labels, and does not touch `train.py`, GPU sampling, CPU proxy
        scoring, SAIR, network, or submission paths.
    - [done] Add focused tests for command construction, parser behavior,
      cache reuse, timeout/unavailable handling, and report generation without
      requiring MAGMA.
      - Focused tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        - Result: 8 passed in 1.19s.
    - [done] Run tiny validation: check MAGMA availability, run a dry-run
      or 1-3 candidate MAGMA validation with a short timeout, and record the
      result/blocker and artifacts.
      - Availability check: `command -v magma`
        - Result: return code 1; MAGMA is not available on PATH.
      - Existing review batch used for validation:
        `/tmp/igp24_r4_review_batch_20260704`.
      - Dry-run validation command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_offline_magma_validation_20260705 --max_records 3 --timeout_seconds 5`
      - Result: return code 0; loaded 8 review records, selected 3 for MAGMA
        artifacts, `pari_available=False`, `magma_available=False`,
        `pari_executed=False`, `magma_executed=False`, and
        `magma_status_counts={"dry_run": 3}`. This records the exact blocker
        without running a large verifier batch.
      - Artifacts:
        `/tmp/igp24_offline_magma_validation_20260705/offline_verification_manifest.json`,
        `/tmp/igp24_offline_magma_validation_20260705/verification_plan.md`,
        `/tmp/igp24_offline_magma_validation_20260705/magma_verification_results.jsonl`,
        `/tmp/igp24_offline_magma_validation_20260705/magma_verification_summary.json`,
        `/tmp/igp24_offline_magma_validation_20260705/magma_verification_report.md`,
        `/tmp/igp24_offline_magma_validation_20260705/magma_verification_cache.json`,
        and `/tmp/igp24_offline_magma_validation_20260705/magma_candidate_scripts`.
    - [done] Update README/NOTES, run full verification, confirm Stage 4,
      audit GPU/process state, cleanup caches, commit, and push.
      - Result so far: README and NOTES now document the offline MAGMA
        workflow, dry-run defaults, explicit `--run_magma`, status meanings,
        cache/report artifacts, and the no-hot-loop/no-network/no-submission
        safety boundary.
      - Focused helper tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_review_shortlist.py tests/test_igp24_shortlist.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_sample_export.py`
        - Result: 27 passed in 2.78s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 87 passed in 3.05s.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`,
        `scripts/igp24_review_shortlist.py --help`, and
        `scripts/igp24_shortlist.py --help`
        - Result: all passed.
      - Import check: `train`, `ENVS`, `MagmaVerifier`, offline verifier,
        review helper, and shortlist helper all imported; `igp24` was
        registered and expected helper functions were present.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4022 after this final
          status update.
      - GPU/process audit: final `nvidia-smi` showed the RTX 5090 with no
        running compute processes; `ps -C python3 -C python3.12 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__ -prune -print` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [in_progress] Add MAGMA discovery and exact rerun guidance for the next
    offline verification step.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, offline verifier helper,
      review/shortlist helpers, verifier stubs, and relevant tests.
      - Result: MAGMA availability was still only PATH-based. The exact next
        step needs bounded discovery in common local install locations plus
        machine-readable rerun guidance when MAGMA is unavailable.
    - [done] Add bounded MAGMA discovery and rerun guidance.
      - Implementation: `scripts/igp24_offline_verify.py` now checks PATH,
        explicit executable paths, common local install globs, and optional
        `--magma_search_path` values. Summary JSON, manifest JSON, and the
        Markdown reports record checked candidates, selected path/source, and
        a concrete rerun command with `--run_magma` and `--magma_executable`.
      - Safety: dry-run remains default; exact MAGMA execution still requires
        explicit `--run_magma`; no generation defaults, seed triage
        thresholds, GPU sampler defaults, normal training behavior,
        SAIR/network calls, or submission paths changed.
    - [done] Add focused tests for discovery paths, unavailable guidance, and
      report/summary fields.
      - Focused tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        - Result: 10 passed in 1.36s.
    - [done] Run MAGMA discovery validation; if found, run a tiny real
      `--run_magma` batch, otherwise run dry-run validation and record exact
      blocker plus artifacts.
      - Discovery/dry-run validation command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_magma_discovery_validation_20260705 --max_records 3 --timeout_seconds 5`
      - Result: return code 0; loaded 8 review records, selected 3 for MAGMA
        artifacts, `magma_available=False`, `magma_executed=False`,
        `magma_status_counts={"dry_run": 3}`, `magma_discovery_checked=3`,
        and `magma_selected_path=None`.
      - Discovery detail: no `magma` executable was found on PATH or at
        `/usr/local/bin/magma`, `/usr/bin/magma`, or `/home/zpconn/bin/magma`;
        wildcard patterns checked for possible installs included
        `/opt/magma*/magma`, `/opt/Magma*/magma`,
        `/usr/local/magma*/magma`, `/usr/local/Magma*/magma`,
        `/home/zpconn/magma*/magma`, and `/home/zpconn/Magma*/magma`.
      - Exact blocker: MAGMA is unavailable locally, so no exact labels were
        verified and no real MAGMA process was run.
      - Rerun command recorded by the helper:
        `/usr/bin/python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_magma_discovery_validation_20260705_run_magma --max_records 3 --timeout_seconds 5 --run_magma --magma_executable /path/to/magma`
      - Artifacts:
        `/tmp/igp24_magma_discovery_validation_20260705/offline_verification_manifest.json`,
        `/tmp/igp24_magma_discovery_validation_20260705/verification_plan.md`,
        `/tmp/igp24_magma_discovery_validation_20260705/magma_verification_results.jsonl`,
        `/tmp/igp24_magma_discovery_validation_20260705/magma_verification_summary.json`,
        `/tmp/igp24_magma_discovery_validation_20260705/magma_verification_report.md`,
        `/tmp/igp24_magma_discovery_validation_20260705/magma_verification_cache.json`,
        and `/tmp/igp24_magma_discovery_validation_20260705/magma_candidate_scripts`.
    - [done] Update README/NOTES if guidance changed, run final
      verification, confirm Stage 4, audit GPU/process state, cleanup caches,
      commit, and push.
      - Result so far: README and NOTES now document discovery beyond PATH,
        common local install globs, `--magma_search_path`, direct
        `--magma_executable`, and the rerun-command guidance.
      - Focused helper tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_review_shortlist.py tests/test_igp24_shortlist.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_sample_export.py`
        - Result: 29 passed in 3.19s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 89 passed in 3.48s.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`,
        `scripts/igp24_review_shortlist.py --help`, and
        `scripts/igp24_shortlist.py --help`
        - Result: all passed, including new `--magma_search_path` help.
      - Import check: `train`, `ENVS`, `MagmaVerifier`, offline verifier,
        review helper, and shortlist helper all imported; `igp24` was
        registered and expected discovery/guidance functions were present.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4108 after this final
          status update.
      - GPU/process audit: final `nvidia-smi` showed the RTX 5090 with no
        running compute processes; `ps -C python3 -C python3.12 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__ -prune -print` returned no paths.
      - Literal `python -m pytest -q` remains blocked with `/bin/bash: line
        1: python: command not found`; `python3 -m pytest -q` is the passing
        local equivalent.
  - [done] Add safe manual free-online Magma calculator artifacts and
    pasted-output parsing.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, offline verifier helper,
      offline verifier tests, and the MAGMA verifier stub.
      - Result: local MAGMA discovery remained unavailable, but a one-candidate
        free-online calculator probe succeeded. The generated scripts still
        called invalid `Signature(f)` on a rational polynomial, so the first
        implementation fix was to remove that call from manual/bulk scripts.
    - [done] Add explicit manual-online artifacts and pasted-output parsing.
      - Implementation: `scripts/igp24_offline_verify.py` now accepts
        `--online_magma_manual` to write `online_magma_manual/` artifacts:
        one copy/paste script per selected candidate, a
        `online_magma_pasted_outputs_template.jsonl` file, parsed result
        JSONL, summary JSON, and report Markdown.
      - Implementation: `--online_magma_pasted_output` parses saved free
        calculator XML or raw text output into degree, irreducibility,
        Galois-group text, transitive group id, exact `24Tt` label, runtime,
        Magma version, and provenance.
      - Safety: the helper never submits to the online calculator, never
        batches online use, does not call SAIR/network/submission paths, does
        not run inside training/GPU sampling/CPU proxy scoring, and keeps local
        MAGMA execution gated behind `--run_magma`.
    - [done] Add and parse the successful manual online result.
      - Raw evidence file:
        `data/igp24/online_magma_manual_output_70a542863f79_20260705.xml`.
      - Parsed candidate:
        `70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb`.
      - Parsed result: degree 24, irreducible true, group text
        `Symmetric group G acting on a set of cardinality 24`, transitive
        group id 25000, exact label `24T25000`, Magma `V2.29-8`, calculator
        runtime 0.420s, provenance `Magma free online calculator`.
    - [done] Run manual-online dry-run artifact generation for 1-3 reviewed
      candidates and parse the known pasted output.
      - Command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_online_magma_manual_20260705 --max_records 3 --timeout_seconds 5 --online_magma_manual --online_magma_pasted_output data/igp24/online_magma_manual_output_70a542863f79_20260705.xml`
      - Result: return code 0; loaded 8 review records; generated manual
        online artifacts for 3 candidates; parsed one verified manual-online
        exact label `24T25000`; local `magma_available=False`; local
        `magma_executed=False`; local MAGMA rows remained dry-run with
        `magma_status_counts={"dry_run": 3}`.
      - Top-level manifest safety after the parser result:
        `online_magma_exact_group_labels_parsed=true`,
        `exact_group_labels_parsed=true`, `exact_group_claims=true`,
        `magma_executed=false`, `network_calls=false`, and
        `online_magma_automated_submission=false`.
      - Artifacts:
        `/tmp/igp24_online_magma_manual_20260705/offline_verification_manifest.json`,
        `/tmp/igp24_online_magma_manual_20260705/magma_verification_results.jsonl`,
        `/tmp/igp24_online_magma_manual_20260705/magma_verification_summary.json`,
        `/tmp/igp24_online_magma_manual_20260705/online_magma_manual/copy_paste_scripts`,
        `/tmp/igp24_online_magma_manual_20260705/online_magma_manual/online_magma_pasted_outputs_template.jsonl`,
        `/tmp/igp24_online_magma_manual_20260705/online_magma_manual/online_magma_manual_results.jsonl`,
        `/tmp/igp24_online_magma_manual_20260705/online_magma_manual/online_magma_manual_summary.json`,
        and `/tmp/igp24_online_magma_manual_20260705/online_magma_manual/online_magma_manual_report.md`.
    - [done] Run focused implementation checks and commit the first
      implementation checkpoint.
      - Focused offline verifier tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        - Result: 12 passed in 1.26s after adding manual-online artifacts.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_offline_verify.py tests/test_igp24_offline_verify.py`
        - Result: passed.
      - Commit: `8840aa4 Add manual online MAGMA artifacts`.
    - [done] Update README/NOTES/TODO and commit the parsed online result.
      - Docs: README and NOTES now describe the manual free-online calculator
        workflow, the 60s/50KB/V2.29-8 observed limits, and the first exact
        `24T25000` parsed result.
      - Commit: `2762a62 Record manual online MAGMA result`.
    - [done] Run final verification, confirm Stage 4 remains present, audit
      GPU/process state, cleanup caches, and prepare final push.
      - Manual-online dry run:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_online_magma_manual_20260705 --max_records 3 --timeout_seconds 5 --online_magma_manual --online_magma_pasted_output data/igp24/online_magma_manual_output_70a542863f79_20260705.xml`
        - Result: passed; local MAGMA unavailable/executed false; parsed one
          verified manual-online exact label `24T25000`.
      - Focused offline verifier tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        - Result: 12 passed in 1.25s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 91 passed in 4.03s.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
        - Result: passed; help exposes `--online_magma_manual` and
          `--online_magma_pasted_output`.
      - Import check: `train`, `ENVS`, offline verifier manual-online helpers,
        and `MagmaVerifier` imported; expected attributes were present.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4218 after this final
          status update.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 visible with no
        running compute processes; `ps -C python3 -C python3.12 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed before the
        final commit.
  - [done] Turn manual-online Magma artifacts into a practical
    verification queue.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect TODO, README, NOTES, offline verifier helper/tests,
      MAGMA verifier stub, and the current review/shortlist artifacts.
      - Result: current queue source is
        `/tmp/igp24_r4_review_batch_20260704`, built from
        `/tmp/igp24_r4_shortlist_20260704`; it has 8 proxy-only review
        candidates. The top six by score are quartic-lift-like, while records
        7 and 8 provide useful `four_real_seed` coverage.
    - [done] Add a deliberate non-contiguous candidate selection path and
      clearer manual-online queue report sections.
      - Implementation: `scripts/igp24_offline_verify.py` now accepts repeated
        `--candidate_hash` values, preserving the requested queue order and
        rejecting missing or duplicate hashes.
      - Implementation: `online_magma_manual_report.md` now separates already
        parsed exact labels, ready-for-manual-copy/paste candidates,
        proxy-only queue candidates, and local MAGMA dry-run status counts.
      - Safety: the queue path still performs no online submission, no SAIR
        call, no network call, and no integration with training, GPU sampling,
        CPU proxy scoring, or local search.
    - [done] Run focused implementation checks before queue generation.
      - Focused offline verifier tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        - Result: 13 passed in 1.29s after tightening the
          still-proxy-only queue partition.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_offline_verify.py tests/test_igp24_offline_verify.py`
        - Result: passed.
    - [done] Generate the practical manual-online verification queue.
      - Selection rationale: keep the already parsed top-score exact result,
        include three additional high-score quartic-lift candidates, and add
        both available `four_real_seed` review-batch candidates for useful
        strategy coverage beyond the known `24T25000` row.
      - Selected queue hashes, in order:
        `70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb`,
        `4bb12cfdfb235e11af7c51ea2b726aab2a5b3cfcd54b3d0a9f9f29f5f2525edf`,
        `8e105d4e1281a6e161a818dc685d41f37172c2460d6d3a04d024dd2699c03968`,
        `4882427239ef073a626b0003e9da228b367b985488a1bcd0f569cc91d1fcb26e`,
        `2a5559600c07d1a771ab56f2bcca07e123b6ab5f6844b3c9857a168c253bd1e0`,
        and `62df2639fa4002233ee4fa8b17d9cf3f5746a708b71e71f864edc481780179d1`.
      - Command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_manual_magma_queue_20260705 --timeout_seconds 5 --online_magma_manual --online_magma_pasted_output data/igp24/online_magma_manual_output_70a542863f79_20260705.xml --candidate_hash 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb --candidate_hash 4bb12cfdfb235e11af7c51ea2b726aab2a5b3cfcd54b3d0a9f9f29f5f2525edf --candidate_hash 8e105d4e1281a6e161a818dc685d41f37172c2460d6d3a04d024dd2699c03968 --candidate_hash 4882427239ef073a626b0003e9da228b367b985488a1bcd0f569cc91d1fcb26e --candidate_hash 2a5559600c07d1a771ab56f2bcca07e123b6ab5f6844b3c9857a168c253bd1e0 --candidate_hash 62df2639fa4002233ee4fa8b17d9cf3f5746a708b71e71f864edc481780179d1`
      - Result: loaded 6 selected review records; local
        `magma_available=False`; local `magma_executed=False`;
        `magma_status_counts={"dry_run": 6}`; parsed one already verified
        manual-online exact label `24T25000`; five candidates remain ready
        for manual copy/paste and still only proxy-scored.
      - Queue artifacts:
        `/tmp/igp24_manual_magma_queue_20260705/offline_verification_manifest.json`,
        `/tmp/igp24_manual_magma_queue_20260705/magma_verification_results.jsonl`,
        `/tmp/igp24_manual_magma_queue_20260705/online_magma_manual/copy_paste_scripts`,
        `/tmp/igp24_manual_magma_queue_20260705/online_magma_manual/online_magma_pasted_outputs_template.jsonl`,
        `/tmp/igp24_manual_magma_queue_20260705/online_magma_manual/online_magma_manual_results.jsonl`,
        `/tmp/igp24_manual_magma_queue_20260705/online_magma_manual/online_magma_manual_summary.json`,
        and `/tmp/igp24_manual_magma_queue_20260705/online_magma_manual/online_magma_manual_report.md`.
      - Artifact check: the template has 6 rows, local MAGMA result JSONL has
        6 dry-run rows, parsed online result JSONL has 1 verified row, and
        generated copy/paste scripts include `do not batch-submit` and
        `IGP24_TRANSITIVE_GROUP_ID` markers without `Signature(f)`.
    - [done] Update README/NOTES, run final verification, confirm Stage 4,
      audit GPU/process state, clean caches, and prepare final push.
      - Focused offline/review/shortlist tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_review_shortlist.py tests/test_igp24_shortlist.py`
        - Result: 19 passed in 1.28s.
      - Full pytest:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 92 passed in 3.75s.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Helper help checks:
        `scripts/igp24_offline_verify.py --help`,
        `scripts/igp24_review_shortlist.py --help`, and
        `scripts/igp24_shortlist.py --help`
        - Result: all passed; offline verifier help now exposes
          `--candidate_hash`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4310 after this final
          status update.
      - GPU/process audit: `nvidia-smi` showed the RTX 5090 visible with no
        running compute processes; `ps -C python3 -C python3.12 -o
        pid=,etime=,pcpu=,pmem=,args=` found no active Python processes.
      - Cleanup: generated `__pycache__` directories were removed; follow-up
        `find . -type d -name __pycache__ -prune -print` returned no paths.
  - [done] Pivot from generic `S_24` queue results toward
    non-generic Galois proxy evidence.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Read TODO, README, NOTES, offline verifier helper, IGP24
      environment/scoring code, shortlist/review helpers, and current manual
      Magma queue artifacts.
      - Result: the current queue artifacts and saved calculator XMLs show all
        six selected candidates are exact `24T25000`, i.e. full symmetric
        group `S_24`.
    - [done] Preserve all six manual-online exact-result XML files in repo.
      - Preserved files:
        `data/igp24/online_magma_manual_output_70a542863f79_20260705.xml`,
        `data/igp24/online_magma_manual_output_4bb12cfdfb23_20260705.xml`,
        `data/igp24/online_magma_manual_output_8e105d4e1281_20260705.xml`,
        `data/igp24/online_magma_manual_output_4882427239ef_20260705.xml`,
        `data/igp24/online_magma_manual_output_2a5559600c07_20260705.xml`,
        and `data/igp24/online_magma_manual_output_62df2639fa40_20260705.xml`.
      - Parse command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_manual_magma_queue_preserved_20260705 --timeout_seconds 5 --online_magma_manual --online_magma_pasted_output data/igp24/online_magma_manual_output_70a542863f79_20260705.xml --online_magma_pasted_output data/igp24/online_magma_manual_output_4bb12cfdfb23_20260705.xml --online_magma_pasted_output data/igp24/online_magma_manual_output_8e105d4e1281_20260705.xml --online_magma_pasted_output data/igp24/online_magma_manual_output_4882427239ef_20260705.xml --online_magma_pasted_output data/igp24/online_magma_manual_output_2a5559600c07_20260705.xml --online_magma_pasted_output data/igp24/online_magma_manual_output_62df2639fa40_20260705.xml --candidate_hash 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb --candidate_hash 4bb12cfdfb235e11af7c51ea2b726aab2a5b3cfcd54b3d0a9f9f29f5f2525edf --candidate_hash 8e105d4e1281a6e161a818dc685d41f37172c2460d6d3a04d024dd2699c03968 --candidate_hash 4882427239ef073a626b0003e9da228b367b985488a1bcd0f569cc91d1fcb26e --candidate_hash 2a5559600c07d1a771ab56f2bcca07e123b6ab5f6844b3c9857a168c253bd1e0 --candidate_hash 62df2639fa4002233ee4fa8b17d9cf3f5746a708b71e71f864edc481780179d1`
      - Result: 6 selected rows, 6 verified online manual results, verified
        labels `["24T25000"]`, local `magma_available=False`, local
        `magma_executed=False`, and local MAGMA rows remained dry-run.
    - [done] Add a safe proxy-only non-generic diagnostic helper.
      - Implementation: `scripts/igp24_non_generic_diagnostic.py` reads
        existing ledgers and ranks records by non-generic proxy evidence:
        square discriminants, exact/near composed support, sparse support,
        sampled Frobenius parity, and missing long-cycle witnesses.
      - Safety: the helper is file-only; it does not call PARI, MAGMA, SAIR,
        network APIs, training, GPU sampling, CPU proxy scoring hot loops,
        local search, or submission paths. It keeps exact labels separate from
        proxy evidence.
    - [done] Add focused diagnostic tests and run implementation checks.
      - Focused tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_non_generic_diagnostic.py`
        - Result: 5 passed in 0.02s.
      - Compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_non_generic_diagnostic.py tests/test_igp24_non_generic_diagnostic.py`
        - Result: passed.
      - Help check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py --help`
        - Result: passed.
    - [done] Generate a first non-generic diagnostic shortlist artifact.
      - Command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_r4_second_confirm_20260704 /tmp/igp24_r4_dual_quality_confirm_20260704 --target_r 4 --limit 25 --output_dir /tmp/igp24_non_generic_diagnostic_20260705`
      - Result: loaded 4870 records, diagnosed 1879 target-`r=4` candidates,
        selected 25 diagnostic rows, top non-generic proxy score 1988.966833.
      - Flag counts:
        `{"all_sampled_frobenius_even": 19, "exact_composed_support": 25, "near_composed_support": 25, "no_long_cycle_witness_in_sample": 25, "sparse_support": 8, "square_discriminant_excludes_s24": 18, "very_near_square_discriminant": 18, "very_sparse_support": 17}`.
      - Interpretation: unlike the previous high-score exact queue, this
        shortlist prioritizes structural evidence against full generic `S_24`;
        18 rows have square discriminants and all 25 have exact composed
        support. These remain proxy-only until exact verification.
      - Artifacts:
        `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_diagnostic.jsonl`,
        `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl`,
        `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_coefficients.txt`,
        `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_summary.json`,
        and `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_report.md`.
    - [done] Run final validation, audit state, and clean generated caches.
      - Focused diagnostic/review/shortlist tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_non_generic_diagnostic.py tests/test_igp24_shortlist.py tests/test_igp24_review_shortlist.py`
        - Result: 11 passed in 0.05s.
      - Full tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 97 passed in 3.74s.
      - Full compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Help checks:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py --help`
        and
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
        - Result: both passed.
      - `git diff --check`
        - Result: passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4405 after this final
          TODO update.
      - GPU/process audit:
        `nvidia-smi`
        - Result: RTX 5090 visible; no running GPU processes listed; 2944 MiB
          reported in use by display/driver state; instantaneous utilization
          6%.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        - Result: no matching Python processes printed.
      - Cleanup:
        removed generated `__pycache__` directories from the repo.
  - [done] Build the complete manual exact-verification queue for the
    non-generic diagnostic shortlist.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Read TODO, README, NOTES, non-generic diagnostic helper, offline
      verifier helper, shortlist/review helpers, tests, and the current
      diagnostic artifacts under `/tmp/igp24_non_generic_diagnostic_20260705`.
      - Result: artifacts were present; no diagnostic regeneration was needed.
        The shortlist has 25 rows, all proxy-only.
      - Audit summary from
        `/tmp/igp24_non_generic_diagnostic_20260705/non_generic_report.md`:
        24 `quartic_lift` rows and 1 `sparse` row; all 25 have
        `exact_composed_support`, `near_composed_support`, and
        `no_long_cycle_witness_in_sample`; 18 have
        `square_discriminant_excludes_s24` and
        `very_near_square_discriminant`; 19 have
        `all_sampled_frobenius_even`; 17 have `very_sparse_support`; 8 have
        `sparse_support`.
    - [done] Generate all-candidate manual-online MAGMA queue artifacts
      from the diagnostic shortlist, preserving order, hashes, coefficients,
      diagnostic flags, and proxy/exact separation.
      - Command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl --output_dir /tmp/igp24_non_generic_manual_queue_20260705 --timeout_seconds 5 --online_magma_manual`
      - Result: 25 records loaded from `candidate_jsonl`; local
        `pari_available=False`, `magma_available=False`,
        `pari_executed=False`, `magma_executed=False`; local MAGMA status
        counts `{"dry_run": 25}`.
      - Queue artifacts:
        `/tmp/igp24_non_generic_manual_queue_20260705/offline_verification_manifest.json`,
        `/tmp/igp24_non_generic_manual_queue_20260705/verification_batch.jsonl`,
        `/tmp/igp24_non_generic_manual_queue_20260705/verification_coefficients.txt`,
        `/tmp/igp24_non_generic_manual_queue_20260705/magma_verification_results.jsonl`,
        `/tmp/igp24_non_generic_manual_queue_20260705/online_magma_manual/copy_paste_scripts`,
        `/tmp/igp24_non_generic_manual_queue_20260705/online_magma_manual/online_magma_pasted_outputs_template.jsonl`,
        `/tmp/igp24_non_generic_manual_queue_20260705/online_magma_manual/online_magma_manual_results.jsonl`,
        `/tmp/igp24_non_generic_manual_queue_20260705/online_magma_manual/online_magma_manual_summary.json`,
        and
        `/tmp/igp24_non_generic_manual_queue_20260705/online_magma_manual/online_magma_manual_report.md`.
      - Artifact counts: 25 copied batch records, 25 coefficient rows, 25
        local MAGMA dry-run rows, 25 manual-online template rows, 25
        per-candidate copy/paste scripts, and 0 parsed manual-online results.
      - Script-size audit: one candidate per script; max script size 841 bytes,
        below the observed 50000 byte calculator input cap, so no extra chunk
        grouping was required.
    - [done] Preserve and parse any matching manually pasted MAGMA outputs
      already present in `/tmp` or `data/igp24`; otherwise record that all 25
      rows remain ready for manual copy/paste exact verification.
      - Result: scanning `/tmp/igp24_online_magma_manual_output_*_20260705.xml`
        and `data/igp24/online_magma_manual_output_*_20260705.xml` found 0
        matching candidate hashes for the 25 diagnostic rows. No exact labels
        were parsed for this queue yet; all 25 remain ready for manual
        copy/paste exact verification.
    - [done] Improve helper/report ergonomics if needed for the all-queue
      workflow, keeping the helper manual-only and file-only.
      - Implementation: `scripts/igp24_offline_verify.py` now writes
        `verification_batch.jsonl` and `verification_coefficients.txt` for all
        input kinds, including direct candidate JSONL inputs.
      - Implementation: online manual template rows now include queue index,
        short hash, proxy score, non-generic score, real-root count, source
        strategy, diagnostic flags, a compact evidence summary, script path,
        and script byte count.
      - Implementation: online manual summary/report now record diagnostic
        strategy counts, diagnostic flag counts, and one-candidate-per-script
        size/chunking status.
      - Focused tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        - Result: 13 passed in 1.31s.
      - Focused compile:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_offline_verify.py tests/test_igp24_offline_verify.py`
        - Result: passed.
    - [done] Update README, NOTES, and TODO with queue coverage, exact
      labels if any, local MAGMA status, and the recommended next search
      family decision.
      - README now documents the copied queue artifacts and the 25-row
        non-generic manual-online queue.
      - NOTES now records that no exact labels have been parsed for this queue
        yet and that the highest-signal next action is manual exact
        verification of the top rows before changing search direction.
      - Recommended decision rule: if exact verification confirms non-generic
        groups, expand the corresponding composed-support/square-discriminant
        `quartic_lift` branch; if square-discriminant rows parse as generic
        `24T25000`, treat that as a data or diagnostic bug before trusting
        more proxy ranks. Do not start a large GPU training run for this
        branch until exact labels arrive.
    - [done] Run final validation, confirm Stage 4, audit GPU/process state,
      clean generated caches, and prepare final push.
      - Full tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 97 passed in 3.71s.
      - Full compile check:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Help checks:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
        and
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py --help`
        - Result: both passed.
      - `git diff --check`
        - Result: passed.
      - Stage 4 check:
        `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4520 after this final
          TODO update.
      - GPU/process audit:
        `nvidia-smi`
        - Result: RTX 5090 visible; no running GPU processes listed; 2927 MiB
          reported in use by display/driver state; instantaneous utilization
          2%.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        - Result: no matching Python processes printed.
      - Cleanup: generated `__pycache__` directories were removed.
  - [done] Locally audit the 25-row non-generic manual queue structure
    before any larger search or GPU run.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Read TODO, README, NOTES, non-generic diagnostic helper, offline
      verifier helper, polynomial utilities, tests, and the current manual
      queue artifacts under `/tmp/igp24_non_generic_manual_queue_20260705`.
      - Result: the queue artifacts are present, including
        `verification_batch.jsonl`, `verification_coefficients.txt`,
        local MAGMA dry-run rows, and 25 manual-online copy/paste scripts.
    - [done] Add a local exact-algebra structure audit helper that
      recomputes discriminants, confirms square-discriminant flags, confirms
      exact composed support, extracts base polynomials `g(y)`, groups
      structural families, and emits a compact manual verification priority
      order.
      - Implementation: `scripts/igp24_queue_structure_audit.py` reads the
        manual queue JSONL, performs exact SymPy-side algebra only, writes
        JSONL/JSON/Markdown artifacts, and records safety flags showing no
        MAGMA/PARI/SAIR/network/training/GPU/CPU-search execution.
      - Tests:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_queue_structure_audit.py`
        - Result: 6 passed in 0.21s.
      - Compile/help checks:
        `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_queue_structure_audit.py tests/test_igp24_queue_structure_audit.py`
        and
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py --help`
        - Result: both passed.
    - [done] Run the local structure audit on the full 25-row queue.
      - Command:
        `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_non_generic_manual_queue_20260705/verification_batch.jsonl --output_dir /tmp/igp24_non_generic_structure_audit_20260705 --priority_limit 10`
      - Result: 25 records loaded and audited; square-discriminant claim
        counts `{"confirmed": 18, "not_claimed": 7}`; exact-composed claim
        counts `{"confirmed": 25}`; zero square-claim refutations; zero
        exact-composed refutations.
      - Structural families: 24 records have primary exact block divisor 2
        and base degree 12; one record has primary exact block divisor 3 and
        base degree 8. Strategy counts are `{"quartic_lift": 24, "sparse": 1}`.
      - Artifacts:
        `/tmp/igp24_non_generic_structure_audit_20260705/structure_audit.jsonl`,
        `/tmp/igp24_non_generic_structure_audit_20260705/manual_priority.jsonl`,
        `/tmp/igp24_non_generic_structure_audit_20260705/manual_priority_hashes.txt`,
        `/tmp/igp24_non_generic_structure_audit_20260705/structure_summary.json`,
        and
        `/tmp/igp24_non_generic_structure_audit_20260705/structure_report.md`.
      - Priority order for manual exact verification:
        1. queue 1, `65e40c41647afd86d081cf9cdbbea9cb391a5071e5bec8f8c14f985daa8b6b55`
        2. queue 19, `27eaf2acac9f94a78fdec065fdf8a8f4c1c6b27816716eea04b3ea41c25dba8b`
        3. queue 6, `5b9dee86211ecd506d2cac86cc6461ae8610105d6ad4dbf6a0cde8b302e17343`
        4. queue 2, `2dadebc8c716261688e8ab4d682b137d5c8fe667bf8a89b36a2fef9be031c521`
        5. queue 3, `3bae032a47336af98dcd9206399f013f9e8a8c7a9504ef94fb0c9899ec111b14`
        6. queue 4, `eacca9cf7c601ea27316fa032202c3e4d9d36d0951df7437012564ca1e81551e`
        7. queue 5, `e3d43c52a095f636492b7a12ffd771ebd11d34686379c31bcdbd258c1128686a`
        8. queue 7, `071ac330291fe82639d13e992017109bdd235d21d135c209d05488c21cfa3bcd`
        9. queue 8, `bfbd15116a58a07c05c2a62989fc62a538d643c8ba082e4ff4c1e0d8ba456b1e`
        10. queue 9, `be3b30d3564a75ab1a0623d2793ea00a0f92150b1985fca9c0b21b16f6b85882`
      - Interpretation: this confirms local algebraic structure only. Exact
        `24Tt` labels remain unknown until manual/local exact Galois
        verification is performed outside this helper.
    - [done] Update README/NOTES/TODO with the structure-audit handoff.
      - Result: README now documents the exact audit command, artifact paths,
        and confirmed local-structure counts. NOTES now records the
        structural-family split and manual verification order. TODO keeps the
        exact/proxy separation and Stage 4 future work intact.
    - [done] Run full validation, confirm Stage 4 remains present, audit GPU
      and Python process state, clean caches, commit, and push.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        - Result: 103 passed in 3.78s.
      - Full compile check:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        - Result: passed.
      - Help checks:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py --help`,
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`,
        and
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py --help`
        - Result: all passed.
      - `git diff --check`
        - Result: passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        - Result: Stage 4 remains present at line 4623 after this final TODO
          update.
      - GPU/process audit:
        `nvidia-smi`
        - Result: RTX 5090 visible; no running GPU processes listed; 2990 MiB
          reported in use by display/driver state; instantaneous utilization
          4%.
      - Python process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        - Result: no matching Python processes printed.
      - Cleanup: generated `__pycache__` directories were removed and a
        follow-up `find . -type d -name __pycache__ -print` printed nothing.
  - [done] Exact-verify all 25 non-generic manual-queue rows with the free
    online Magma calculator.
    - [done] Confirm local exact-verifier availability before online work.
      - Result: `magma`, `gp`, and `sage` were not on PATH. Local MAGMA
        remained unavailable; no local MAGMA/PARI execution occurred.
    - [done] Submit one-candidate Magma scripts to the online calculator and
      preserve raw XML responses.
      - Input scripts:
        `/tmp/igp24_non_generic_manual_queue_20260705/online_magma_manual/copy_paste_scripts`.
      - Output XML files:
        `data/igp24/online_magma_manual_output_*_20260705.xml`.
      - Scope: 25 one-candidate requests, outside `train.py`, GPU sampling,
        CPU proxy scoring, local search, SAIR submission, and the offline
        helper itself.
    - [done] Parse the saved XML responses with the existing offline verifier
      helper.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl --output_dir /tmp/igp24_non_generic_manual_queue_verified_20260705 --timeout_seconds 5 --online_magma_manual --online_magma_pasted_output data/igp24/online_magma_manual_output_65e40c41647a_20260705.xml ...`
      - Result: 25 parsed online-Magma results; status counts
        `{"verified": 25}`; no proxy-only queue rows remain.
      - Artifacts:
        `/tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual/online_magma_manual_results.jsonl`,
        `/tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual/online_magma_manual_summary.json`,
        and
        `/tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual/online_magma_manual_report.md`.
    - [done] Record exact-label distribution and interpretation.
      - All 25 rows parsed as degree 24 and irreducible.
      - Exact labels: 18 rows `24T24970`, 6 rows `24T24979`, 1 row
        `24T24759`.
      - Structure match: the 18 square-discriminant divisor-2 rows are
        `24T24970`; the 6 nonsquare divisor-2 tail rows are `24T24979`; the
        divisor-3/base-degree-8 coverage row `27eaf2acac9f` is `24T24759`.
      - Interpretation: the non-generic diagnostic and local structure audit
        were strongly predictive here. This branch should now prioritize
        exact-label feedback into shortlist analysis and composed-support
        family expansion, not an immediate large GPU run.
  - [done] Feed verified non-generic exact labels back into
    diagnostic/search planning.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Read TODO, README, NOTES, non-generic diagnostic helper, queue
      structure audit helper, offline verifier helper, structure-audit
      artifacts, parsed online-Magma results, and committed XML provenance.
      - Result: current authoritative inputs are the 25-row structure audit
        under `/tmp/igp24_non_generic_structure_audit_20260705`, parsed
        online-Magma results under
        `/tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual`,
        and committed XML files under `data/igp24/`.
    - [done] Add a local/file-only exact-label feedback helper that
      joins verified labels to structure-audit rows by canonical hash and
      reports label counts, label-by-structure summaries, representatives,
      and next-run recommendations.
      - Helper: `scripts/igp24_verified_label_feedback.py`.
      - Focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_verified_label_feedback.py`
        passed with 3 tests.
      - Compile/help checks:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_verified_label_feedback.py tests/test_igp24_verified_label_feedback.py`
        passed, and
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_verified_label_feedback.py --help`
        passed.
    - [done] Run the helper against the verified 25-row non-generic queue.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_verified_label_feedback.py --structure_audit_jsonl /tmp/igp24_non_generic_structure_audit_20260705/structure_audit.jsonl --magma_results_jsonl /tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual/online_magma_manual_results.jsonl --diagnostic_jsonl /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl --output_dir /tmp/igp24_verified_label_feedback_20260705`
      - Results: 25 joined rows, 25 verified rows, 25 degree-24 irreducible
        rows, exact labels `{"24T24759": 1, "24T24970": 18, "24T24979": 6}`,
        and 0 generic `24T25000` rows.
      - Structure mapping: square-discriminant divisor-2/base-degree-12 rows
        are `24T24970`; nonsquare divisor-2/base-degree-12 rows are
        `24T24979`; the divisor-3/base-degree-8 row `27eaf2acac9f` is
        `24T24759`.
      - Artifacts:
        `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl`,
        `/tmp/igp24_verified_label_feedback_20260705/verified_label_representatives.jsonl`,
        `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback_summary.json`,
        and
        `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback_report.md`.
    - [done] Update README/NOTES/experiment notes with concise public
      helper context and move detailed benchmark/reporting material out of
      the README.
      - README now documents the feedback helper briefly and links detailed
        results to `docs/EXPERIMENTS.md`.
      - `docs/EXPERIMENTS.md` records the feedback artifact paths and exact
        label-by-structure mapping.
      - `NOTES_IGP24.md` records the research interpretation and next code
        step: exact-label-aware shortlist reporting or generation knobs before
        any larger GPU training run.
    - [done] Run final validation, confirm Stage 4 remains present,
      audit GPU/process state, clean caches, commit docs, and push.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        passed with 106 tests.
      - Compileall:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper help:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_verified_label_feedback.py --help`
        passed.
      - Diff check: `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 4741 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit: `nvidia-smi` found no running GPU compute processes; the
        RTX 5090 was at 6% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up count was 0.
  - [done] Add exact-label-aware shortlist planning from verified
    feedback families.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect shortlist, non-generic diagnostic, structure audit, and
      verified-label feedback helpers.
      - Decision: add a local/file-only planner that reads existing
        `structure_audit.jsonl` rows and `verified_label_feedback.jsonl` rows,
        assigns feedback-family labels by structural key, enforces label
        coverage quotas, and writes a shortlist/report. It will not call
        MAGMA, PARI, SAIR, training, GPU sampling, CPU proxy-search loops,
        local search, network APIs, or submission paths.
    - [done] Implement the planner and focused tests.
      - Helper: `scripts/igp24_exact_label_shortlist.py`.
      - Focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_exact_label_shortlist.py`
        passed with 4 tests.
      - Compile/help checks:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_exact_label_shortlist.py tests/test_igp24_exact_label_shortlist.py`
        passed, and
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_exact_label_shortlist.py --help`
        passed.
    - [done] Run the planner on the verified 25-row structure audit
      with explicit `24T24970`/`24T24979`/`24T24759` family quotas.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_exact_label_shortlist.py --structure_audit_jsonl /tmp/igp24_non_generic_structure_audit_20260705/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --candidate_jsonl /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl --output_dir /tmp/igp24_exact_label_shortlist_20260705 --limit 12 --min_per_label 0 --label_quotas 24T24970:8,24T24979:2,24T24759:1`
      - Results: 25 annotated rows, 25 matched rows, 0 ambiguous rows, 12
        selected rows, family counts
        `{"24T24759": 1, "24T24970": 9, "24T24979": 2}`, and 12
        coefficient vectors written. The extra `24T24970` row is the
        top-ranked fill row after satisfying explicit quotas.
      - Family rules: square divisor-2/base-degree-12 -> `24T24970`
        confidence 1.0 from 18 feedback rows; nonsquare divisor-2/base-degree
        12 -> `24T24979` confidence 1.0 from 6 feedback rows; nonsquare
        divisor-3/base-degree-8 -> `24T24759` confidence 1.0 from 1 feedback
        row.
      - Artifacts:
        `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist.jsonl`,
        `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist_coefficients.txt`,
        `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist_summary.json`,
        and
        `/tmp/igp24_exact_label_shortlist_20260705/exact_label_shortlist_report.md`.
      - Fresh-candidate guard:
        rerunning the same command with `--exclude_verified_hashes` under
        `/tmp/igp24_exact_label_shortlist_exclude_verified_20260705` selected
        0 rows, confirming future fresh audits can avoid reselecting the
        already verified 25-row queue.
    - [done] Commit the planner checkpoint before documentation updates.
      - Result: committed `e14037e` (`Add IGP24 exact label shortlist
        planner`) after `git diff --check` passed.
    - [done] Update README/NOTES/experiment notes with the exact-label
      shortlist planner command, artifacts, and interpretation.
      - README now documents the planner command briefly.
      - `docs/EXPERIMENTS.md` records the planner artifact paths, 12-row
        selected family counts, and `--exclude_verified_hashes` guard result.
      - `NOTES_IGP24.md` records the learned family rules and next fresh-batch
        workflow.
    - [done] Run final validation, confirm Stage 4 remains present,
      audit GPU/process state, clean caches, commit docs, and push.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        passed with 110 tests.
      - Compileall:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper help:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_exact_label_shortlist.py --help`
        passed.
      - Diff check: `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 4827 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit: `nvidia-smi` found no running GPU compute processes; the
        RTX 5090 was at 5% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up count was 0.
  - [in_progress] Add baseline/discriminant-aware submission planning.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Read README, TODO, NOTES, experiment notes, current verifier and
      planner helpers, saved verified artifacts, and live SAIR scoring rules.
      - Scoring implication: the scoring unit is `(24Tt, r)` per team, not a
        polynomial row. Multiple variants of the same pair should collapse to
        one best representative in a submission candidate file.
      - Current artifact caveat: saved online-Magma rows verify exact labels
        but do not carry Magma-computed `r`; the candidate/diagnostic rows
        carry local `real_root_count=4`, so the submission planner must record
        the `r` source instead of pretending this is official submitted output.
    - [done] Implement `scripts/igp24_submission_plan.py` and focused
      tests for grouping, duplicate-pair suppression, discriminant ranking,
      baseline handling, and candidate-text formatting.
      - Helper: `scripts/igp24_submission_plan.py`.
      - Focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_submission_plan.py`
        passed with 4 tests.
      - Compile/help checks:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_submission_plan.py tests/test_igp24_submission_plan.py`
        passed, and
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_plan.py --help`
        passed.
    - [done] Run the planner on the current verified non-generic artifacts,
      without a baseline CSV, to collapse duplicate variants by expected
      `(24Tt, r)`.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_plan.py --verified_results /tmp/igp24_non_generic_manual_queue_verified_20260705/online_magma_manual --candidate_jsonl /tmp/igp24_non_generic_diagnostic_20260705/non_generic_shortlist.jsonl --candidate_jsonl /tmp/igp24_exact_label_shortlist_20260705 --output_dir /tmp/igp24_submission_plan_20260705`
      - Results: 25 verified rows loaded, 25 joined rows, 3 selected
        one-per-pair rows, 3 unique expected pairs, 22 duplicate pair
        candidates suppressed, and 3 coefficient lines written.
      - Selected expected pairs:
        `24T24970|r=4`, `24T24979|r=4`, and `24T24759|r=4`.
      - Baseline/discriminant status: no baseline CSV was supplied, so all
        selected rows are `baseline_unknown`; all three discriminant choices
        use `log_abs_discriminant` as a polynomial-discriminant proxy rather
        than exact `nfdisc`.
      - Caveat: `r=4` comes from candidate `real_root_count`, not from the
        saved online-Magma exact-label rows.
      - Artifacts:
        `/tmp/igp24_submission_plan_20260705/submission_plan.jsonl`,
        `/tmp/igp24_submission_plan_20260705/submission_candidates.txt`,
        `/tmp/igp24_submission_plan_20260705/submission_plan_summary.json`,
        and
        `/tmp/igp24_submission_plan_20260705/submission_plan_report.md`.
    - [done] Commit the submission planner checkpoint before broader
      documentation updates.
      - Result: committed `a10d3c5` (`Add IGP24 submission planning`) after
        `git diff --check` passed.
    - [done] Update README, experiment notes, and design notes with the
      submission planner command, artifacts, and score-strategy caveats.
      - README now documents the simple local/file-only submission-plan
        command.
      - `docs/EXPERIMENTS.md` records the 25 joined verified rows collapsing
        to 3 expected pairs with 22 duplicate pair candidates suppressed.
      - `NOTES_IGP24.md` records the scoring implication: pair diversity and
        exact discriminant/baseline evidence matter more than many variants of
        the same expected pair.
    - [done] Run final validation, confirm Stage 4 remains present,
      audit GPU/process state, and clean caches.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        passed with 114 tests.
      - Compileall:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper help:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_plan.py --help`
        passed.
      - Diff check: `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 4914 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit: `nvidia-smi` found no running GPU compute processes; the
        RTX 5090 was at 7% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up count was 0.
    - [done] Commit the docs/TODO validation update and push.
      - Result: committed `f1a79ad` (`Document IGP24 submission planning`) and
        pushed `igp24-dev` to `zpconn/igp24-axplorer`.
  - [done] Build a fresh pair-diversity candidate queue.
    - [done] Pull latest before starting.
      - Result: `git pull --ff-only` was already up to date.
    - [done] Inspect README, TODO, NOTES, experiment notes, and latest helper
      scripts.
      - Relevant helpers: `scripts/igp24_benchmark.py` for bounded CPU
        generation, `scripts/igp24_non_generic_diagnostic.py` for proxy-only
        non-generic triage, `scripts/igp24_queue_structure_audit.py` for local
        exact-algebra structure, and
        `scripts/igp24_exact_label_shortlist.py` for feedback-family planning
        with `--exclude_verified_hashes`.
      - Strategy: prefer a bounded CPU generation sweep over a GPU run because
        this step is about structural/pair novelty, not longer model training.
        Exclude already verified hashes, favor structurally unmatched or
        weakly matched families as possible new-pair evidence, and keep a small
        controlled track for the known verified families.
      - Safety boundaries: no SAIR submission/API, no MAGMA/PARI execution
        except dry-run artifact generation, no network calls, no long GPU
        training run, and no open-ended CPU search loop.
    - [done] Run a bounded fresh generation/collection pass under
      `/tmp/igp24_*_20260706`.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,quartic_lift,fixed_sparse_template,mix_r4_dual_balanced --seeds 2601,2602 --target_rs 4 --coeff_bound 4 --gensize 16 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 1 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_fresh_pair_bench_20260706`
      - Results: 10 bounded CPU runs completed in about 27 seconds total;
        217 ledger rows were written. The strongest r4 yield came from
        `mix_r4_dual_balanced` with 24 target-r matches across 37 ledger rows
        and `quartic_lift` with 23 matches across 40 ledger rows. `sparse`
        contributed 3 r4 matches; `structured` contributed no r4 matches in
        this tiny sweep.
      - Artifact: `/tmp/igp24_fresh_pair_bench_20260706`.
    - [done] Run proxy-only non-generic diagnostics on the fresh rows.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_fresh_pair_bench_20260706 --target_r 4 --limit 40 --output_dir /tmp/igp24_fresh_pair_diagnostic_20260706`
      - Results: 217 rows loaded, 59 target-r fresh rows diagnosed, 40
        selected, 6 duplicate canonical hashes skipped, and 152 non-r4 rows
        skipped. Selected flags included 23 `exact_composed_support`, 3
        `square_discriminant_excludes_s24`, 20 `very_sparse_support`, and 20
        `sparse_support`.
      - Artifacts:
        `/tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_shortlist.jsonl`,
        `/tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_summary.json`,
        and
        `/tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_report.md`.
    - [done] Run local exact-algebra structure audit on the fresh diagnostic
      shortlist.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_shortlist.jsonl --priority_limit 16 --output_dir /tmp/igp24_fresh_pair_structure_audit_20260706`
      - Results: 40/40 rows audited; 3 square-discriminant claims confirmed,
        23 exact-composed-support claims confirmed, and no square or exact
        composed claims refuted. Primary block divisor counts were
        `{"2": 16, "3": 6, "6": 1, "None": 17}`.
      - Artifacts:
        `/tmp/igp24_fresh_pair_structure_audit_20260706/structure_audit.jsonl`,
        `/tmp/igp24_fresh_pair_structure_audit_20260706/manual_priority.jsonl`,
        `/tmp/igp24_fresh_pair_structure_audit_20260706/structure_summary.json`,
        and
        `/tmp/igp24_fresh_pair_structure_audit_20260706/structure_report.md`.
    - [done] Upgrade exact-label-aware shortlist planning so fresh queue fill
      can prefer novelty instead of repeating one known feedback family.
      - Added `--max_per_family_label` to cap repeats from known feedback
        labels.
      - Added `--prefer_unmatched` so fill rows favor unmatched structural
        families after explicit label quotas are satisfied.
      - Focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_exact_label_shortlist.py`
        passed with 5 tests.
    - [done] Build the fresh diversity queue with verified-hash exclusion and
      novelty-first fill.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_exact_label_shortlist.py --structure_audit_jsonl /tmp/igp24_fresh_pair_structure_audit_20260706/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --candidate_jsonl /tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_shortlist.jsonl --output_dir /tmp/igp24_fresh_pair_diversity_queue_20260706 --limit 16 --min_per_label 0 --label_quotas 24T24970:1,24T24979:1,24T24759:1 --family_key_mode full --include_unmatched --exclude_verified_hashes --max_per_family_label 1 --prefer_unmatched`
      - Results: 40 annotated rows, 10 matched rows, 30 unmatched rows, 16
        selected rows, 16 coefficients written, 0 known verified selected
        records, and 0 hash overlap with the 25 verified feedback rows.
      - Queue mix: one controlled `24T24979` feedback-family row and 15
        unmatched rows. The unmatched rows include square-discriminant
        divisor-6/base-degree-4 evidence, fixed-template square
        divisor-2/base-degree-12 evidence, divisor-3/base-degree-8 coverage,
        sparse divisor-2/base-degree-12 coverage, and non-composed sparse
        coverage.
      - Artifacts:
        `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl`,
        `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist_coefficients.txt`,
        `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist_summary.json`,
        and
        `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist_report.md`.
    - [done] Record submission-planning status for this fresh queue.
      - Result: submission planning is intentionally blocked pending exact
        verification. The fresh queue has local structure and inferred
        feedback-family planning labels only; it has no verified exact
        `24Tt` labels, no exact submitted `r`, no exact `nfdisc`, and no
        baseline comparison.
    - [done] Commit the planner-code checkpoint before documentation updates.
      - Result: committed `e9b8b5c` (`Favor fresh IGP24 pair-diversity
        queues`) after focused tests, compile/help checks, and
        `git diff --check` passed.
    - [done] Update README, experiment notes, and design notes with the fresh
      pair-diversity queue and strategy implications.
      - README now briefly mentions the diversity options for fresh queues.
      - `docs/EXPERIMENTS.md` records fresh generation, diagnostic, audit, and
        diversity queue artifact paths plus counts and interpretation.
      - `NOTES_IGP24.md` records why novelty pressure is needed after label
        quotas and why this queue is for manual exact verification, not
        submission.
    - [done] Run final validation, confirm Stage 4 remains present,
      audit GPU/process state, and clean caches.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        passed with 115 tests.
      - Compileall:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper help checks:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_exact_label_shortlist.py --help`,
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py --help`,
        and
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py --help`
        passed.
      - Diff check: `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 5043 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit: `nvidia-smi` found no running GPU compute processes; the
        RTX 5090 was at 6% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up count was 0.
    - [done] Commit the docs/TODO validation update and push.
      - Result: committed `625407e` (`Document fresh IGP24 diversity queue`)
        and pushed `igp24-dev` to `zpconn/igp24-axplorer`.
  - [in_progress] Exact-verify the fresh pair-diversity queue and rerun
    submission planning.
    - [done] Confirm local exact-verifier availability before using online
      provenance.
      - Result: local MAGMA remains unavailable on this host; the helper
        recorded `local_magma_executed=false` and local status counts
        `{"dry_run": 16}`. No local MAGMA/PARI/SAIR execution occurred.
    - [done] Prepare online Magma manual artifacts for all 16 fresh queue
      rows.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl --output_dir /tmp/igp24_fresh_pair_manual_verify_20260706 --max_records 16 --online_magma_manual --timeout_seconds 60`
      - Result: one candidate-per-script copy/paste artifacts were written
        under
        `/tmp/igp24_fresh_pair_manual_verify_20260706/online_magma_manual`.
        The largest script was 843 bytes, under the observed 50000-byte
        calculator cap.
    - [done] Run bounded one-candidate online calculator checks and preserve
      raw XML provenance.
      - Result: 12 requests returned parseable Magma output from V2.29-8; the
        final four requests returned `<offline>The Magma calculator is
        temporarily disabled.</offline>`. Raw responses are preserved in
        `/tmp/igp24_fresh_pair_manual_verify_20260706/online_magma_manual`
        and copied into `data/igp24/online_magma_manual_output_*_20260706.xml`.
      - Provenance note: the helper is still manual/file-only and reports
        `network_calls_by_helper=false`; these bounded online POSTs were run
        separately with `curl` by the agent, not by `train.py`, GPU sampling,
        CPU proxy scoring, local search, SAIR, or the helper itself.
    - [done] Parse saved online calculator outputs with the offline verifier
      helper.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl --output_dir /tmp/igp24_fresh_pair_verified_20260706 --max_records 16 --online_magma_manual --online_magma_pasted_output /tmp/igp24_fresh_pair_manual_verify_20260706/online_magma_manual/online_magma_pasted_outputs_20260706.jsonl --timeout_seconds 60`
      - Result: 16 selected rows, status counts
        `{"verified": 12, "parse_error": 4}`. All 12 verified rows were
        degree 24 and irreducible. Exact labels were `24T24979`: 5,
        `24T24759`: 3, `24T24970`: 2, `24T9683`: 1, and `24T24648`: 1.
        No row verified as generic `24T25000`.
      - Pending hashes from calculator-disabled responses:
        `198ac88fa216`, `20b35a3fd41d`, `88437a372524`, and
        `0f3ad8602d89`.
      - Artifacts:
        `/tmp/igp24_fresh_pair_verified_20260706/online_magma_manual/online_magma_manual_results.jsonl`,
        `/tmp/igp24_fresh_pair_verified_20260706/online_magma_manual/online_magma_manual_summary.json`,
        and
        `/tmp/igp24_fresh_pair_verified_20260706/online_magma_manual/online_magma_manual_report.md`.
    - [done] Feed the fresh exact labels back into local structure summaries.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_verified_label_feedback.py --structure_audit_jsonl /tmp/igp24_fresh_pair_structure_audit_20260706/structure_audit.jsonl --magma_results_jsonl /tmp/igp24_fresh_pair_verified_20260706/online_magma_manual/online_magma_manual_results.jsonl --diagnostic_jsonl /tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_shortlist.jsonl --output_dir /tmp/igp24_fresh_pair_verified_label_feedback_20260706`
      - Result: 12 joined verified rows, all degree 24 and irreducible, with
        exact-label counts `{"24T24648": 1, "24T24759": 3, "24T24970": 2,
        "24T24979": 5, "24T9683": 1}`.
      - Structural implications:
        square divisor-6/base-degree-4 `quartic_lift` produced `24T9683`;
        fixed-template divisor-3/base-degree-8 produced one `24T24648` and
        one `24T24759`; quartic-lift divisor-3/base-degree-8 produced two
        more `24T24759`; square fixed-template divisor-2/base-degree-12
        produced two `24T24970`; nonsquare divisor-2/base-degree-12 remained
        `24T24979`.
      - Artifacts:
        `/tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl`,
        `/tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_representatives.jsonl`,
        `/tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback_summary.json`,
        and
        `/tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback_report.md`.
    - [done] Rerun local/file-only submission planning on the verified fresh
      rows.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_plan.py --verified_results /tmp/igp24_fresh_pair_verified_20260706/online_magma_manual --candidate_jsonl /tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_shortlist.jsonl --candidate_jsonl /tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl --output_dir /tmp/igp24_fresh_pair_submission_plan_20260706`
      - Result: 12 joined verified rows collapsed to five one-per-pair
        selected rows, with seven duplicate pair candidates suppressed and
        four unverified rows skipped.
      - Selected expected pairs:
        `24T24979|r=4` (`981a94588aab`),
        `24T24759|r=4` (`4be66a510402`),
        `24T9683|r=4` (`9c45c5493e7a`),
        `24T24970|r=4` (`a97caa584baa`), and
        `24T24648|r=4` (`2289d8a5e700`).
      - Caveats: all five rows are `baseline_unknown`; discriminant ordering
        uses `log_abs_discriminant` from the polynomial proxy, not exact
        `nfdisc`; `r=4` comes from local candidate `real_root_count`, not a
        Magma-computed signature field; `scoreable_claims=false`; no SAIR
        submission was made.
      - Artifacts:
        `/tmp/igp24_fresh_pair_submission_plan_20260706/submission_plan.jsonl`,
        `/tmp/igp24_fresh_pair_submission_plan_20260706/submission_candidates.txt`,
        `/tmp/igp24_fresh_pair_submission_plan_20260706/submission_plan_summary.json`,
        and
        `/tmp/igp24_fresh_pair_submission_plan_20260706/submission_plan_report.md`.
    - [done] Update README, experiment notes, and design notes with the fresh
      verification result.
      - Result: documentation records the 12/16 parsed verification result,
        the two fresh labels beyond the prior verified set (`24T9683` and
        `24T24648`), the four calculator-disabled pending rows, raw XML
        provenance, the five expected pairs in the refreshed plan, and the
        remaining exact `r`/`nfdisc`/baseline caveats.
    - [done] Run final validation, confirm Stage 4 remains present, audit
      GPU/process state, and clean caches.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        passed with 115 tests in 3.87s.
      - Compileall:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper help checks:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`,
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_plan.py --help`,
        and
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_verified_label_feedback.py --help`
        passed.
      - Diff check: `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 5162 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit: `nvidia-smi` found no running GPU compute processes; the
        RTX 5090 was at 3% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up `find . -type d -name __pycache__ -print`
        returned no paths.
  - [in_progress] Make the five verified one-per-pair representatives
    submission-grade.
    - [done] Pull latest and inspect current verifier/planner surfaces.
      - Result: `git pull --ff-only` was already up to date on `igp24-dev`.
      - Five representatives for this goal:
        `981a94588aab` (`24T24979|r=4`),
        `4be66a510402` (`24T24759|r=4`),
        `9c45c5493e7a` (`24T9683|r=4`),
        `a97caa584baa` (`24T24970|r=4`), and
        `2289d8a5e700` (`24T24648|r=4`).
      - Current code state: `scripts/igp24_submission_plan.py` already has
        `--baseline_csv`, baseline-pair lookup, and exact-`nfdisc` preference,
        but the offline/manual verifier does not yet emit exact Magma `r` in
        generated scripts or parseable PARI/GP `nfdisc` result rows.
      - Local availability: `command -v gp` and `command -v magma` returned no
        paths, so this host cannot currently compute exact `nfdisc` or local
        Magma signatures. This goal should produce ready-to-run manual
        artifacts and parsers, and only mark exact fields present when saved
        exact outputs exist.
      - Safety: no SAIR submission/API calls and no GPU/model search.
    - [done] Add exact `r`/`nfdisc` capture to verifier artifacts and wire
      merged exact evidence into submission planning.
      - Code changes: `scripts/igp24_offline_verify.py` now emits
        `IGP24_SIGNATURE` in Magma scripts, emits parseable PARI/GP
        `IGP24_NFDISC_ABS`/status markers, parses saved PARI/GP outputs into
        `pari_nfdisc_results.jsonl`, and writes a PARI nfdisc summary/report.
      - Code changes: `scripts/igp24_submission_plan.py` now merges exact label,
        exact `r`, and exact `nfdisc` evidence rows by candidate hash, searches
        nested verifier result files, prefers exact `nfdisc`, labels candidate
        `r` as a proxy, and records exact-`r`/exact-`nfdisc` status counts.
      - Focused tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_submission_plan.py`
        passed with 19 tests in 1.34s.
    - [done] Import the official frozen LMFDB baseline CSV.
      - Source:
        `https://competition.sair.foundation/downloads/igp24/lmfdb_baseline.csv`.
      - Saved file: `data/igp24/lmfdb_baseline.csv`.
      - Header: `label,r,poly_disc_abs,nfdisc_abs,scoring_disc,coeffs`.
      - Load result from the planner: 1,480 rows indexed into 622 `(label, r)`
        pairs.
    - [done] Run the updated five-representative pass against official
      baseline data and record the remaining exact-evidence blockers.
      - Artifact source commit after the checkpoint rerun:
        `88bb0ed6b5b31cd9e81198a91b22754a933e9766`.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_plan.py --verified_results /tmp/igp24_submission_grade_five_20260706 --candidate_jsonl /tmp/igp24_fresh_pair_diagnostic_20260706/non_generic_shortlist.jsonl --candidate_jsonl /tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl --baseline_csv data/igp24/lmfdb_baseline.csv --output_dir /tmp/igp24_submission_grade_five_plan_with_baseline_20260706`.
      - Result: 10 verifier rows merged to 5 selected one-per-pair rows; all
        five are `non_baseline_candidate` against the official baseline.
      - Current blocker: all five rows are still `new_pair_needs_exact_r`,
        because the saved online-Magma XML predates the new `IGP24_SIGNATURE`
        marker, local `magma` is unavailable, and no exact PARI `nfdisc` output
        is present. Current status counts are
        `exact_r_status_counts={"candidate_proxy": 5}` and
        `exact_nfdisc_status_counts={"missing": 5}`.
      - Plan artifacts:
        `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_plan.jsonl`,
        `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_candidates.txt`,
        `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_plan_summary.json`,
        and
        `/tmp/igp24_submission_grade_five_plan_with_baseline_20260706/submission_plan_report.md`.
    - [done] Prepare a bounded manual retry packet for the four fresh rows
      that previously hit calculator-disabled responses.
      - Safety: no automatic online batch verification was run; this only
        writes one-candidate copy/paste scripts and local/manual parser
        artifacts.
      - Rows:
        `198ac88fa216`,
        `20b35a3fd41d`,
        `88437a372524`, and
        `0f3ad8602d89`.
      - Artifact directory: `/tmp/igp24_pending_four_retry_20260706`.
      - Result: 4 dry-run rows, no local Magma/PARI execution, no SAIR/network
        calls. Each generated Magma script includes `IGP24_SIGNATURE`; the
        generated PARI/GP input includes `IGP24_NFDISC_ABS`.
    - [done] Update public README, notes, and experiment docs for the
      official-baseline import, exact-evidence status fields, and current
      five-row blocker.
      - README now keeps public status simple: the official baseline CSV is
        bundled, the five representatives are absent from it, and exact
        Magma `r` plus exact `nfdisc` are still required before
        submission-grade claims.
      - Detailed benchmark/artifact/status notes are in `docs/EXPERIMENTS.md`,
        `NOTES_IGP24.md`, and this TODO instead of the README.
    - [done] Run final validation, confirm Stage 4 remains present, audit
      process/GPU state, and clean caches.
      - Full pytest:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
        passed with 117 tests in 3.92s.
      - Compile check:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - CLI help checks passed for `scripts/igp24_offline_verify.py --help`
        and `scripts/igp24_submission_plan.py --help`.
      - Diff check: `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 5268 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit: `nvidia-smi` found no running GPU compute processes; the
        RTX 5090 was at 7% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up `find . -type d -name __pycache__ -print`
        returned no paths.
    - [done] Add explicit SymPy number-field-discriminant fallback
      evidence while PARI/GP remains unavailable.
      - Rationale: local `gp`, `magma`, `sage`, `wolframscript`, `singular`,
        `gap`, `cypari2`, `sageall`, and `cypari` are unavailable, but SymPy's
        `AlgebraicField.discriminant()` is installed and computed field
        discriminants quickly for the five selected degree-24 rows.
      - Safety/source boundary: this is local/file-only exact nfdisc fallback
        evidence, not the official PARI/GP workflow and not a Magma signature
        substitute.
      - Code changes: add `--run_sympy_nfdisc` to
        `scripts/igp24_offline_verify.py`, write
        `sympy_nfdisc_results.jsonl` / summary / report artifacts, and let
        `scripts/igp24_submission_plan.py` merge those rows as exact
        `nfdisc` evidence with source
        `sympy_algebraic_field_discriminant`.
      - Focused tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_submission_plan.py`
        passed with 21 tests in 4.60s after the SymPy artifact changes and
        21 tests in 4.55s after the planner provenance fix.
      - Artifact source commit for the SymPy nfdisc run:
        `6abe150816fe36828edc8c50384f50b36fdd52ec`.
      - SymPy artifact directory:
        `/tmp/igp24_submission_grade_five_20260706_sympy_nfdisc`.
      - SymPy result: `sympy_nfdisc_status_counts={"nfdisc_ok": 5}` with no
        local Magma/PARI execution, no SAIR/network calls, and no GPU/model
        search.
      - Planner rerun source commit:
        `7ff0a210b8100cb8c36f36b2dcfaadbac9576d0e`.
      - Planner artifact directory:
        `/tmp/igp24_submission_grade_five_plan_with_sympy_nfdisc_20260706`.
      - Updated planner result:
        `baseline_status_counts={"non_baseline_candidate": 5}`,
        `exact_nfdisc_status_counts={"ok": 5}`,
        `discriminant_rank_category_counts={"exact_nfdisc": 5}`,
        `exact_r_status_counts={"candidate_proxy": 5}`, and
        `scoreability_status_counts={"new_pair_needs_exact_r": 5}`.
      - Remaining blocker: exact Magma `r` is still missing because local
        Magma is unavailable and the saved online-Magma XML predates
        `IGP24_SIGNATURE`. The five rows now have exact local fallback
        `nfdisc`, but they are still not submission-grade until exact `r`
        is captured.
      - Final validation after SymPy fallback docs:
        - `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` passed with
          119 tests in 7.43s.
        - `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
          passed.
        - Helper `--help` checks passed for `scripts/igp24_offline_verify.py`
          and `scripts/igp24_submission_plan.py`.
        - `git diff --check` passed.
        - Stage 4 check:
          `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
          found Stage 4 at line 5325 after this TODO update.
        - Process audit returned no running Python processes.
        - GPU audit found no running GPU compute processes; the RTX 5090 was
          at 7% utilization with display memory only.
        - Cache cleanup completed and the follow-up `find . -type d -name __pycache__ -print`
          returned no paths.
  - [done] Add explicit SymPy exact real-root-count fallback evidence
      for submission-signature `r`.
      - Rationale: local Magma remains unavailable, but SymPy's exact
        `Poly.count_roots(-oo, oo)` computes the real-root count for the five
        selected degree-24 rows immediately. This is exact local fallback
        evidence, not Magma provenance and not a replacement for exact
        `24Tt` labels.
      - Code changes: add `--run_sympy_signature` to
        `scripts/igp24_offline_verify.py`, write
        `sympy_signature_results.jsonl` / summary / report artifacts, and let
        `scripts/igp24_submission_plan.py` prefer Magma `r` when present but
        accept `sympy_real_root_count` before falling back to candidate
        `real_root_count`.
      - Focused tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_submission_plan.py`
        passed with 24 tests in 4.63s after the exact-r fallback changes and
        24 tests in 4.55s after the planner note/blocker cleanup.
      - Artifact source commit for the five-row exact fallback run:
        `ee916aab47e2f58d8791deac2af77584f9606952`.
      - Five-row exact fallback artifact directory:
        `/tmp/igp24_submission_grade_five_20260706_sympy_exact`.
      - Five-row result:
        `sympy_signature_status_counts={"signature_ok": 5}` and
        `sympy_nfdisc_status_counts={"nfdisc_ok": 5}` with no local
        Magma/PARI execution, no SAIR/network calls, and no GPU/model search.
      - Final planner source commit:
        `75fd9bf470da189aeaffe197fd987deb963d9d49`.
      - Final planner artifact directory:
        `/tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706`.
      - Final planner result:
        `baseline_status_counts={"non_baseline_candidate": 5}`,
        `scoreability_status_counts={"new_pair_candidate": 5}`,
        `exact_r_status_counts={"ok": 5}`,
        `exact_nfdisc_status_counts={"ok": 5}`, and
        `discriminant_rank_category_counts={"exact_nfdisc": 5}`.
      - Selected rows now use exact local fallback `r` source
        `verified.sympy_real_root_count` and exact local fallback `nfdisc`
        source `sympy_algebraic_field_discriminant`.
      - Pending-four refresh:
        `/tmp/igp24_pending_four_retry_sympy_exact_20260706` has
        `sympy_signature_status_counts={"signature_ok": 4}` and
        `sympy_nfdisc_status_counts={"nfdisc_ok": 4}`. It still has no exact
        group labels, no local Magma/PARI execution, no SAIR/network calls, and
        no GPU/model search.
      - Final validation after exact-r fallback docs:
        - `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` passed with
          122 tests in 7.16s.
        - `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
          passed.
        - Helper `--help` checks passed for `scripts/igp24_offline_verify.py`
          and `scripts/igp24_submission_plan.py`.
        - `git diff --check` passed.
        - Stage 4 check:
          `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
          found Stage 4 at line 5385 after this TODO update.
        - Process audit returned no running Python processes.
        - GPU audit found no running GPU compute processes; the RTX 5090 was
          at 6% utilization with display memory only.
        - Cache cleanup completed and the follow-up `find . -type d -name __pycache__ -print`
          returned no paths.
  - [done] Build a final auditable five-row manual submission package.
    - [done] Pull latest.
      - Result: `git pull --ff-only` was already up to date on `igp24-dev`.
    - [done] Inspect final five-row planner/evidence artifacts.
      - Planner artifact:
        `/tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706`.
      - Exact evidence artifact:
        `/tmp/igp24_submission_grade_five_20260706_sympy_exact`.
      - Current selected rows match the intended hashes and labels:
        `9c45c5493e7a` (`24T9683|r=4`),
        `981a94588aab` (`24T24979|r=4`),
        `4be66a510402` (`24T24759|r=4`),
        `a97caa584baa` (`24T24970|r=4`), and
        `2289d8a5e700` (`24T24648|r=4`).
      - Current planner status:
        `baseline_status_counts={"non_baseline_candidate": 5}`,
        `scoreability_status_counts={"new_pair_candidate": 5}`,
        `exact_r_status_counts={"ok": 5}`,
        `exact_nfdisc_status_counts={"ok": 5}`, and
        `discriminant_rank_category_counts={"exact_nfdisc": 5}`.
    - [done] Check for stronger local exact-verifier availability.
      - Result: `command -v magma` and `command -v gp` returned no paths, so
        no local Magma/PARI cross-check can be run on this host.
      - The final package must therefore include ready-to-run Magma copy/paste
        scripts with `IGP24_SIGNATURE` and document the cross-check blocker.
    - [done] Add a small package helper rather than assembling the final
      directory with ad hoc shell-only copies.
      - Helper: `scripts/igp24_submission_package.py`.
      - Focused helper test:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_submission_package.py`
        passed with 2 tests in 0.04s after adding compact row summaries to the
        manifest and builder-verified checklist markers.
      - Initial helper checkpoint commit:
        `7690f5b Add IGP24 submission packaging helper`; manifest/checklist
        polish is part of the final documentation/package checkpoint.
    - [done] Generate the final local/manual package.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_submission_package.py --plan_dir /tmp/igp24_submission_grade_five_plan_with_sympy_exact_20260706 --evidence_dir /tmp/igp24_submission_grade_five_20260706_sympy_exact --baseline_csv data/igp24/lmfdb_baseline.csv --raw_magma_dir data/igp24 --output_dir /tmp/igp24_final_submission_package_20260706 --candidate_hash 981a94588aab9c05713953e0d6feef907b2d55ba4cd01ef386b57cae274248c5 --candidate_hash 4be66a510402f26a3da7dcc6a03fbf64c0d915dcc53a01a48ea904ad8555e64e --candidate_hash 9c45c5493e7a4e3ade9700843b66b32c21c8f50868f0ddd9eb8c42c386730131 --candidate_hash a97caa584baa93fa2b610cb0a7882ba766d5ffe13d2450b23aceb6ea0f361d7a --candidate_hash 2289d8a5e7007dfda908bf1aab4dabae4f0455618d42aa27e10e26c88b8b9f2d`.
      - Output directory:
        `/tmp/igp24_final_submission_package_20260706`.
      - Key files:
        `package_manifest.json`, `submission_checklist.md`,
        `submission_coefficients.txt`, and
        `submission_coefficients.jsonl`.
      - Package status:
        `selected_records=5`,
        `scoreability_status_counts={"new_pair_candidate": 5}`,
        `exact_r_status_counts={"ok": 5}`,
        `exact_nfdisc_status_counts={"ok": 5}`, and
        `sair_submission=false`.
      - Audit checks: 39 files in the package, 5 coefficient-only rows, 5
        structured coefficient rows, 5 plan rows, 5 raw Magma XML files, and
        no obvious `api_key`/secret/password strings beyond the manifest safety
        flag `contains_api_keys=false`.
      - Manifest selected pairs:
        `24T9683|r=4`, `24T24979|r=4`, `24T24759|r=4`,
        `24T24970|r=4`, and `24T24648|r=4`.
      - Remaining caveat: local `magma` and `gp` are still unavailable, so the
        package includes ready-to-run Magma copy/paste scripts with
        `IGP24_SIGNATURE` instead of fresh local Magma/PARI output.
    - [done] Update README, experiments, notes, and this TODO with the final
      package path, contents, status counts, and caveats.
    - [done] Run final validation gates and process/GPU/cache audits.
      - Focused package tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_submission_package.py`
        passed with 2 tests in 0.02s.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` passed with
        124 tests in 7.48s.
      - Compile check:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper `--help` checks passed for
        `scripts/igp24_submission_package.py`,
        `scripts/igp24_submission_plan.py`, and
        `scripts/igp24_offline_verify.py`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 5481 after this TODO update.
      - Process audit:
        `ps -C python3 -C python3.12 -o pid=,etime=,pcpu=,pmem=,args=`
        returned no running Python processes.
      - GPU audit:
        `nvidia-smi` found no running GPU compute processes; the RTX 5090 was
        at 6% utilization with display memory only.
      - Cache cleanup:
        `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
        completed, and the follow-up `find . -type d -name __pycache__ -print`
        returned no paths.
    - [done] Commit documentation/checklist updates and push `igp24-dev`.
      - Package helper checkpoint:
        `7690f5b Add IGP24 submission packaging helper`.
      - Final package/documentation checkpoint:
        `456d19c Document final IGP24 submission package`.
      - Push result:
        `git push` updated `igp24-dev` on `zpconn/igp24-axplorer`.
      - Post-push status:
        `git status --short --branch` returned
        `## igp24-dev...zpconn/igp24-dev`.
  - [in_progress] Add independent exact-tool cross-checks for the five package
    rows.
    - [done] Install PARI/GP in user space.
      - System install attempt:
        `sudo apt-get update` was blocked because sudo requires an interactive
        password.
      - User-space install:
        `apt-get download pari-gp` fetched Ubuntu package
        `pari-gp_2.15.4-2.1build1_amd64.deb`, then
        `dpkg-deb -x /tmp/pari-gp_2.15.4-2.1build1_amd64.deb /tmp/pari-gp-local`.
      - Executable:
        `/tmp/pari-gp-local/usr/bin/gp`.
      - Version:
        PARI/GP 2.15.4.
    - [done] Fix verifier script generation for actual GP/Magma execution.
      - GP fix: generated `pari_input.gp` now uses `x = 'x;` and explicit
        continuation backslashes for multi-line vectors and loop bodies.
      - Magma fix: generated Magma scripts now use
        `Zx<x> := PolynomialRing(Integers())`, because online Magma
        `NumberOfRealRoots` rejects the previous rational-polynomial element.
      - Focused tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        passed with 18 tests in 4.81s after the GP/Magma script fixes.
    - [done] Run PARI/GP cross-check on the five selected representatives.
      - Integrated artifact directory:
        `/tmp/igp24_pari_magma_crosscheck_20260706_parsed`.
      - Command included:
        `--run_pari --pari_executable /tmp/pari-gp-local/usr/bin/gp`.
      - Result:
        `pari_available=true`, `pari_executed=true`,
        `pari_nfdisc_status_counts={"nfdisc_ok": 5}`, and
        `pari_nfdisc_records=5`.
      - All five PARI rows were degree 24, irreducible, had `pari_r=4`, and
        matched the SymPy exact `nfdisc` values.
    - [done] Check the fixed Magma candidate scripts with the free online Magma
      calculator.
      - Calculator page:
        `https://magma.maths.usyd.edu.au/calc/`.
      - Raw XML responses:
        `/tmp/igp24_pari_magma_crosscheck_20260706/online_magma_manual/checked_xml`.
      - Parsed results:
        `/tmp/igp24_pari_magma_crosscheck_20260706_parsed/online_magma_manual/online_magma_manual_results.jsonl`.
      - Result:
        `online_magma_manual` status counts `{"verified": 5}`.
      - All five online Magma rows returned degree 24, irreducible,
        `IGP24_SIGNATURE 4`, no calculator warnings, and the expected labels:
        `24T24979`, `24T24759`, `24T9683`, `24T24970`, and `24T24648`.
      - No SAIR/API submission was performed.
    - [done] Build a refreshed cross-checked manual package.
      - Output directory:
        `/tmp/igp24_final_submission_package_20260706_crosschecked`.
      - Evidence source:
        `/tmp/igp24_pari_magma_crosscheck_20260706_parsed`.
      - Manifest status:
        `selected_records=5`, `scoreability_status_counts={"new_pair_candidate": 5}`,
        `exact_r_status_counts={"ok": 5}`, `exact_nfdisc_status_counts={"ok": 5}`,
        `pari_gp.available=true`, `magma.available=false`, and
        `sair_submission=false`.
      - Package audit: 5 coefficient-only rows, 5 structured coefficient rows,
        5 plan rows, 5 parsed online Magma result rows, 5 PARI `nfdisc_ok`
        rows, and 5 copied raw online Magma XML responses under
        `evidence/online_magma_manual/checked_xml`.
    - [done] Run full validation for the script fixes and cross-check package.
      - Focused offline-verifier tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
        passed with 18 tests in 4.57s.
      - Focused package tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_submission_package.py`
        passed with 2 tests in 0.03s.
      - Full tests:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q` passed with
        124 tests in 7.34s.
      - Compile check:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
        passed.
      - Helper `--help` checks passed for
        `scripts/igp24_offline_verify.py` and
        `scripts/igp24_submission_package.py`.
      - `git diff --check` passed.
      - Stage 4 check:
        `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
        found Stage 4 at line 5581 after this TODO update.
      - Process audit returned no running Python processes.
      - GPU audit found no running GPU compute processes; the RTX 5090 was at
        3% utilization with display memory only.
      - Cache cleanup completed and the follow-up
        `find . -type d -name __pycache__ -print` returned no paths.
    - [done] Commit and push the script fixes plus documentation updates.
      - Checkpoint: verifier-script fixes, PARI/GP and online Magma
        cross-check artifacts, refreshed cross-checked package notes, and
        validation results.
  - [done] Record five-row manual SAIR submission acceptance.
    - User-reported SAIR response:
      - row 1: accepted, label `24T9683`, `r=4`, reason `—`.
      - row 2: accepted, label `24T24979`, `r=4`, reason `—`.
      - row 3: accepted, label `24T24759`, `r=4`, reason `—`.
      - row 4: accepted, label `24T24970`, `r=4`, reason `—`.
      - row 5: accepted, label `24T24648`, `r=4`, reason `—`.
    - Submission source file:
      `/tmp/igp24_final_submission_package_20260706_crosschecked/submission_coefficients.txt`.
    - Interpretation: the SAIR verifier accepted all five cross-checked
      one-per-pair representatives with the expected labels and `r=4`.
    - User-reported leaderboard/scoring details for this five-row batch:
      - `24T9683|r=4`: solvable yes, scoring discriminant
        955418808601874103055463744199932705243136,
        `D0=1085452710404880000732025061376`, `exact_nfdisc`, `k=32`,
        pair score `<0.0001`.
      - `24T24648|r=4`: solvable no, scoring discriminant
        66729031783492569072130229117096669442371830499819295396528130410433747980288,
        `D0=1240040809067081589350688687340077`, `mixed_disc`, `k=28`,
        pair score `<0.0001`.
      - `24T24759|r=4`: solvable no, scoring discriminant
        767458693251145954924041967612518686365057724321977014092994900933771147,
        `D0=358371793820386579322349030641282253`, `mixed_disc`, `k=30`,
        pair score `<0.0001`.
      - `24T24970|r=4`: solvable no, scoring discriminant
        483860401956763489669011989577899250603371798115505401757696,
        `D0=3509318011999541951139623123560000`, `mixed_disc`, `k=51`,
        pair score `<0.0001`.
      - `24T24979|r=4`: solvable no, scoring discriminant
        752880562130512465229258492699316353904979173801601362034688,
        `D0=87306114061160641264533591554033`, `mixed_disc`, `k=52`,
        pair score `<0.0001`.
  - [done] Retry and resolve the four pending fresh rows.
    - [done] Pull latest.
      - Result: `git pull --ff-only` was already up to date on `igp24-dev`.
    - [done] Inspect existing pending-four artifacts.
      - Source artifact directory:
        `/tmp/igp24_pending_four_retry_sympy_exact_20260706`.
      - Source queue:
        `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl`.
      - Selected hashes:
        `198ac88fa21641db5d47feceec3ca0743a16c023cd85b72c5d9a6bc7763e0009`,
        `20b35a3fd41d4ef30a3582c463bdb19446c08cfe8872f156bd24bbb33f027b30`,
        `88437a372524fc59b12d88f01c8cf7929b778c4efad3edc3a53ebe411ab9b406`,
        and `0f3ad8602d895b7e44729fbe5604fd904f6181c786c865c1e6da4bfaf151ab33`.
      - Existing SymPy exact-r status:
        `sympy_signature_status_counts={"signature_ok": 4}`, all with
        `r=4` from `sympy_poly_count_roots`.
      - Existing SymPy exact-nfdisc status:
        `sympy_nfdisc_status_counts={"nfdisc_ok": 4}`.
      - Existing exact local fallback `nfdisc` values:
        - `198ac88fa216`: 574784031237204017882937809358206854761709291280481792.
        - `20b35a3fd41d`: 34458474498929325531941539978424194438259580701589504.
        - `88437a372524`: 32520883031235746009482154821400124768241521.
        - `0f3ad8602d89`: 76732333707577227709347318376172659671040.
      - Existing row strategies:
        `198ac88fa216` and `20b35a3fd41d` came from
        `fixed_sparse_template`; `88437a372524` and `0f3ad8602d89` came from
        `quartic_lift`.
    - [done] Regenerate verifier artifacts with the fixed current PARI/GP and
      Magma script emitters.
      - Output directory:
        `/tmp/igp24_pending_four_retry_fixed_20260706`.
      - Command included:
        `--online_magma_manual --run_pari --pari_executable /tmp/pari-gp-local/usr/bin/gp --run_sympy_nfdisc --run_sympy_signature`.
      - PARI status:
        `pari_available=true`, `pari_executed=true`,
        `pari_nfdisc_status_counts={"nfdisc_ok": 4}`.
      - SymPy status:
        `sympy_signature_status_counts={"signature_ok": 4}` and
        `sympy_nfdisc_status_counts={"nfdisc_ok": 4}`.
      - PARI/SymPy comparison:
        all four PARI `nfdisc` values match the prior SymPy exact `nfdisc`
        values; all four PARI rows are degree 24, irreducible, and have
        `pari_r=4`.
      - Script check:
        regenerated Magma scripts use
        `Zx<x> := PolynomialRing(Integers())` and print
        `IGP24_SIGNATURE`.
    - [done] Check the four fixed Magma scripts with the free online Magma
      calculator, one candidate at a time.
      - Raw XML directory:
        `/tmp/igp24_pending_four_retry_fixed_20260706/online_magma_manual/checked_xml`.
      - Parsed integrated artifact:
        `/tmp/igp24_pending_four_retry_fixed_parsed_20260706`.
      - Parser status:
        `online_magma_manual_summary.json` reports
        `status_counts={"verified": 4}`.
      - Online Magma labels/signatures:
        - `198ac88fa216`: `24T24648`, `r=4`, degree 24, irreducible,
          Magma V2.29-8, runtime 1.129s, no warnings.
        - `20b35a3fd41d`: `24T24759`, `r=4`, degree 24, irreducible,
          Magma V2.29-8, runtime 1.320s, no warnings.
        - `88437a372524`: `24T25000`, `r=4`, degree 24, irreducible,
          Magma V2.29-8, runtime 0.350s, no warnings.
        - `0f3ad8602d89`: `24T25000`, `r=4`, degree 24, irreducible,
          Magma V2.29-8, runtime 0.380s, no warnings.
    - [done] Build baseline and accepted-submission scoreability review.
      - Helper added: `scripts/igp24_scoreability_review.py`.
      - Focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_scoreability_review.py`
        passed with 2 tests.
      - Review command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_scoreability_review.py --verified_results /tmp/igp24_pending_four_retry_fixed_parsed_20260706 --candidate_jsonl /tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl --baseline_csv data/igp24/lmfdb_baseline.csv --accepted_package_manifest /tmp/igp24_final_submission_package_20260706_crosschecked/package_manifest.json --evidence_dir /tmp/igp24_pending_four_retry_fixed_parsed_20260706 --output_dir /tmp/igp24_pending_four_scoreability_review_20260706`.
      - Review artifact:
        `/tmp/igp24_pending_four_scoreability_review_20260706`.
      - Review counts:
        `reviewed_rows=4`, `actionable_rows=1`,
        `classification_counts={"accepted_pair_duplicate_not_improved": 2, "duplicate_pending_pair_not_best": 1, "scoreable_new_pair_generic_s24": 1}`.
      - Accepted-pair comparison:
        - `198ac88fa216` is another `24T24648|r=4` row, but its exact
          `nfdisc` is larger than the already accepted `2289d8a5e700`
          representative, so it is not a discriminant improvement.
        - `20b35a3fd41d` is another `24T24759|r=4` row, but its exact
          `nfdisc` is larger than the already accepted `4be66a510402`
          representative, so it is not a discriminant improvement.
      - Duplicate pending-pair comparison:
        `88437a372524` is a lower-ranked duplicate of the same
        `24T25000|r=4` pending pair; `0f3ad8602d89` is the selected
        representative under the planner's exact-discriminant ordering.
      - Actionable manual file:
        `/tmp/igp24_pending_four_scoreability_review_20260706/submission_coefficients.txt`.
      - Actionable row:
        `0f3ad8602d89`, `24T25000|r=4`,
        `nfdisc=76732333707577227709347318376172659671040`.
      - Interpretation: `24T25000` is generic full symmetric group, but the
        exact `24T25000|r=4` pair is absent from the frozen official baseline,
        so it is a valid incremental manual-submission candidate under the
        official scoring rules. It is strategically lower-signal than a new
        non-generic label, but it is not a no-score row.
    - [done] Package outcome.
      - The review directory contains a clean coefficient file, annotated
        coefficient file, all-four-row review JSONL, actionable-row JSONL,
        manifest, checklist, copied baseline CSV, copied exact evidence, and
        raw online Magma XML for the actionable row.
      - No SAIR API call, automatic submission, GPU/model search, CPU search
        loop, or local search was performed.
  - [done] Record one-row `24T25000|r=4` submission acceptance.
    - User reported the one-row submission from
      `/tmp/igp24_pending_four_scoreability_review_20260706/submission_coefficients.txt`
      was accepted.
    - Local status change: treat `24T25000|r=4` as accepted/credited, not
      pending, for all subsequent queue planning.
  - [done] Prepare the next non-generic manual-verification queue after
    six accepted pairs.
    - [done] Pull latest.
      - Result: `git pull --ff-only` was already up to date on `igp24-dev`.
    - [done] Inspect existing queue-building tooling and artifacts.
      - Existing helpers inspected:
        `scripts/igp24_non_generic_diagnostic.py`,
        `scripts/igp24_queue_structure_audit.py`,
        `scripts/igp24_exact_label_shortlist.py`, and
        `scripts/igp24_offline_verify.py`.
      - Source artifacts selected for this no-GPU planning pass:
        `/tmp/igp24_fresh_pair_structure_audit_20260706/structure_audit.jsonl`,
        `/tmp/igp24_fresh_pair_diversity_queue_20260706/exact_label_shortlist.jsonl`,
        `/tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl`,
        `/tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl`,
        and
        `/tmp/igp24_pending_four_scoreability_review_20260706/scoreability_review.jsonl`.
      - Design decision: add a small committed pair-status ledger and a
        ledger-aware queue planner that reuses the existing exact-label family
        matching logic, then hand the selected JSONL to
        `scripts/igp24_offline_verify.py` for one-candidate online-Magma
        copy/paste scripts. No GPU/model search is needed for this pass.
    - [done] Add local pair-status ledger.
      - File: `data/igp24/pair_status_20260706.json`.
      - Accepted pairs now recorded:
        `24T9683|r=4`, `24T24979|r=4`, `24T24759|r=4`,
        `24T24970|r=4`, `24T24648|r=4`, and `24T25000|r=4`.
      - The ledger also records user-reported leaderboard scoring
        discriminants, `D0`, discriminant type, `k`, and pair-score text for
        the first five accepted rows.
    - [done] Add ledger-aware next-queue planner and focused tests.
      - Helper: `scripts/igp24_next_verification_queue.py`.
      - Tests: `tests/test_igp24_next_verification_queue.py`.
      - Behavior: reuses existing exact-label family rules and saved
        structure-audit rows, then filters duplicate canonical hashes,
        accepted pairs, pending pairs, baseline pairs, generic `24T25000`
        hints unless explicitly allowed, and accepted/pending/baseline family
        hints.
      - First focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_next_verification_queue.py`
        passed with 4 tests.
    - [done] Run a strict fresh-only planner dry run.
      - Source audit:
        `/tmp/igp24_next_queue_structure_audit_20260706/structure_audit.jsonl`.
      - Result:
        `annotated_records=40`, `eligible_records=15`,
        `selected_records=15`,
        `filter_reason_counts={"accepted_family_hint": 7, "known_exact_accepted_pair": 18, "survived_accepted_pending_baseline_generic_filters": 15}`.
      - Decision: 15 rows was below the desired 20-30 range, so broadened to
        older saved scored artifacts while staying file-only and avoiding any
        GPU/model search.
    - [done] Broaden the file-only diagnostic input from saved artifacts.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_fresh_pair_bench_20260706 /tmp/igp24_r4_second_confirm_20260704 /tmp/igp24_r4_dual_quality_confirm_20260704 --target_r 4 --limit 160 --output_dir /tmp/igp24_next_non_generic_diagnostic_20260706`.
      - Result:
        `loaded_records=5087`, `diagnosed_records=1919`,
        `selected_records=160`, `top_non_generic_score=2035.0`.
      - Flag counts:
        `{"all_sampled_frobenius_even": 46, "exact_composed_support": 136, "near_composed_support": 160, "no_long_cycle_witness_in_sample": 112, "sparse_support": 92, "square_discriminant_excludes_s24": 21, "very_near_square_discriminant": 21, "very_sparse_support": 68}`.
    - [done] Structure-audit the broadened shortlist.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_next_non_generic_diagnostic_20260706/non_generic_shortlist.jsonl --priority_limit 160 --output_dir /tmp/igp24_next_non_generic_structure_audit_20260706`.
      - Result:
        `records_loaded=160`, `records_audited=160`,
        `square_claim_status_counts={"confirmed": 21, "not_claimed": 139}`,
        `exact_composed_claim_status_counts={"confirmed": 136, "not_claimed": 24}`,
        `square_claim_refuted=0`, `exact_composed_claim_refuted=0`.
    - [done] Build the next ledger-aware manual-verification queue.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_next_verification_queue.py --structure_audit_jsonl /tmp/igp24_next_non_generic_structure_audit_20260706/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --known_verified_jsonl /tmp/igp24_pending_four_scoreability_review_20260706/scoreability_review.jsonl --candidate_jsonl /tmp/igp24_next_non_generic_diagnostic_20260706/non_generic_shortlist.jsonl --pair_status_json data/igp24/pair_status_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --limit 25 --max_per_structural_family 2 --output_dir /tmp/igp24_next_non_generic_queue_20260706`.
      - Result:
        `annotated_records=160`, `eligible_records=24`,
        `selected_records=24`.
      - Filter counts:
        `{"accepted_family_hint": 95, "known_exact_accepted_pair": 41, "survived_accepted_pending_baseline_generic_filters": 24}`.
      - Baseline/ledger inputs:
        622 official baseline pairs loaded from
        `data/igp24/lmfdb_baseline.csv`; 6 accepted local ledger pairs loaded
        from `data/igp24/pair_status_20260706.json`.
      - Selected-row summary:
        all 24 rows are `unmatched`; strategy counts are
        `{"four_real_seed": 8, "quartic_lift": 16}`.
      - Artifacts:
        `/tmp/igp24_next_non_generic_queue_20260706/next_verification_queue.jsonl`,
        `/tmp/igp24_next_non_generic_queue_20260706/next_verification_coefficients.txt`,
        `/tmp/igp24_next_non_generic_queue_20260706/next_verification_hashes.txt`,
        `/tmp/igp24_next_non_generic_queue_20260706/next_verification_queue_manifest.json`,
        and
        `/tmp/igp24_next_non_generic_queue_20260706/next_verification_queue_report.md`.
    - [done] Generate the manual Magma/PARI review packet.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_next_non_generic_queue_20260706/next_verification_queue.jsonl --output_dir /tmp/igp24_next_non_generic_manual_queue_20260706 --timeout_seconds 5 --online_magma_manual`.
      - Result:
        `loaded_review_records=24`, `input_kind=candidate_jsonl`,
        `pari_available=False`, `magma_available=False`,
        `pari_executed=False`, `magma_executed=False`,
        `magma_status_counts={"dry_run": 24}`.
      - Manual artifact:
        `/tmp/igp24_next_non_generic_manual_queue_20260706`.
      - The online-Magma copy/paste directory contains 24 one-candidate
        scripts under
        `/tmp/igp24_next_non_generic_manual_queue_20260706/online_magma_manual/copy_paste_scripts`.
  - [done] Process the 24-row queue into a score-aware decision set.
    - [done] Pull latest.
      - Result: `git pull --ff-only` was already up to date on `igp24-dev`.
    - [done] Inspect queue and manual exact-output state.
      - Queue artifact:
        `/tmp/igp24_next_non_generic_queue_20260706`.
      - Manual packet:
        `/tmp/igp24_next_non_generic_manual_queue_20260706`.
      - Existing manual-output status:
        `online_magma_manual_results.jsonl` has 0 rows; the pasted-output
        template has 24 blank `pasted_output` fields. Therefore exact Magma
        labels are not available yet.
    - [done] Run exact local fallback evidence for all 24 rows.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_next_non_generic_queue_20260706/next_verification_queue.jsonl --output_dir /tmp/igp24_next_non_generic_exact_fallback_20260706 --timeout_seconds 30 --online_magma_manual --run_pari --pari_executable /tmp/pari-gp-local/usr/bin/gp --run_sympy_nfdisc --run_sympy_signature`.
      - Result:
        `loaded_review_records=24`, `pari_available=True`,
        `magma_available=False`, `pari_executed=True`,
        `magma_executed=False`,
        `pari_nfdisc_status_counts={"nfdisc_ok": 24}`,
        `sympy_nfdisc_status_counts={"nfdisc_ok": 24}`,
        `sympy_signature_status_counts={"signature_ok": 24}`,
        `magma_status_counts={"dry_run": 24}`.
      - Exact fallback artifact:
        `/tmp/igp24_next_non_generic_exact_fallback_20260706`.
    - [done] Add score-aware triage helper and focused tests.
      - Helper: `scripts/igp24_score_aware_triage.py`.
      - Tests: `tests/test_igp24_score_aware_triage.py`.
      - Behavior: joins queue rows, saved Magma/manual labels when present,
        PARI/SymPy exact fallback evidence, official baseline pairs, and the
        local pair-status ledger. It classifies rows as new non-baseline pair,
        accepted-pair duplicate/improvement, baseline pair, generic
        `24T25000`, invalid/unverified, or exact-result missing. It also
        encodes the SAIR scoring lesson: prior accepted rows scored `<0.0001`,
        so accepted-pair duplicates are only interesting if exact
        discriminants improve materially.
      - Focused validation:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_score_aware_triage.py`
        passed with 5 tests.
    - [done] Run score-aware triage on the 24-row queue.
      - Command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_aware_triage.py --queue_jsonl /tmp/igp24_next_non_generic_queue_20260706/next_verification_queue.jsonl --offline_dir /tmp/igp24_next_non_generic_exact_fallback_20260706 --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --output_dir /tmp/igp24_next_non_generic_score_triage_20260706`.
      - Result:
        `reviewed_rows=24`, `verified_rows=0`,
        `pending_exact_label_rows=24`, `failed_rows=0`,
        `submission_grade_rows=0`,
        `classification_counts={"exact_result_missing": 24}`,
        `labels_found_counts={}`,
        `exact_r_status_counts={"ok": 24}`,
        `exact_nfdisc_status_counts={"ok": 24}`.
      - Decision: do not build or submit a manual coefficient package yet.
        Exact `r` and `nfdisc` are present, but exact Magma labels are still
        required for score-aware submission decisions.
      - Artifacts:
        `/tmp/igp24_next_non_generic_score_triage_20260706/score_aware_triage.jsonl`,
        `/tmp/igp24_next_non_generic_score_triage_20260706/score_aware_triage_summary.json`,
        `/tmp/igp24_next_non_generic_score_triage_20260706/score_aware_triage_report.md`,
        `/tmp/igp24_next_non_generic_score_triage_20260706/manual_magma_checklist.md`,
        and empty submission-grade files
        `/tmp/igp24_next_non_generic_score_triage_20260706/submission_grade_rows.jsonl`
        and
        `/tmp/igp24_next_non_generic_score_triage_20260706/submission_grade_coefficients.txt`.
    - [done] Import the user-reported SAIR acceptance labels for that 24-row
      queue without waiting for delayed score rows.
      - Feedback artifact:
        `data/igp24/sair_accepted_label_feedback_20260706_next_queue.json`.
      - User-reported verifier result: all 24 rows accepted; rows 1-2 were
        `24T24979`, rows 3-24 were `24T25000`, all with `r=4`.
      - Score status: pending; acceptance is treated as exact label feedback,
        not proof of useful leaderboard score.
      - Helper change:
        `scripts/igp24_score_aware_triage.py` now accepts repeatable
        `--sair_label_feedback_json` inputs and records
        `exact_label_source_counts` plus `accepted_pair_status_counts`.
      - Rerun command:
        `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_aware_triage.py --queue_jsonl /tmp/igp24_next_non_generic_queue_20260706/next_verification_queue.jsonl --offline_dir /tmp/igp24_next_non_generic_exact_fallback_20260706 --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --output_dir /tmp/igp24_next_non_generic_sair_triage_20260706`.
      - Result:
        `reviewed_rows=24`, `verified_rows=24`,
        `pending_exact_label_rows=0`, `failed_rows=0`,
        `submission_grade_rows=0`,
        `labels_found_counts={"24T24979": 2, "24T25000": 22}`,
        `classification_counts={"accepted_pair_duplicate": 2, "generic_24T25000": 22}`,
        `exact_label_source_counts={"sair_accepted_label_feedback": 24}`,
        and
        `accepted_pair_status_counts={"accepted_pair_duplicate_not_improved": 23, "accepted_pair_minor_discriminant_improvement": 1}`.
      - Interpretation: the queue was verifier-clean but not score-aware
        submission-grade. The unmatched/non-generic proxy was too weak: 22
        rows collapsed to generic `S24`, and the two non-generic rows duplicated
        the already accepted `24T24979|r=4` pair.
      - Ledger update: row 6 (`0ec921751862`) is recorded as a lower
        exact-nfdisc `24T25000|r=4` accepted alternate with score still
        pending; the current credited representative is not replaced until
        scores confirm an actual scoring improvement.

## Tests And Checks

- [done] Add and test an explicit `r=8` solvable/composed-family
  construction.
  - Goal source:
    `/home/zpconn/.codex/attachments/58476f2b-b483-4310-adce-d9507baf5cc4/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev` at `ecd3192`.
  - Starting status:
    `git status --short --branch`.
    - Result: clean on `igp24-dev`.
  - Required artifacts read:
    `/tmp/igp24_r8_targeted_bench_20260706/aggregate_summary.json`,
    `/tmp/igp24_r8_targeted_bench_20260706/summary.json`,
    `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_summary.json`,
    and
    `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_target_analysis_summary.json`.
    - Result: previous bounded `r=8` run covered 10 short CPU-only runs,
      160 valid examples, 297 ledger records, and 0 `r=8` rows; every tested
      existing strategy had `target_r_match_total=0`.
  - Existing-template diagnosis:
    - `four_real_seed` and `quartic_lift` are intentionally biased toward
      `r=4`: they use two positive quadratic/quartic-lift roots, giving two
      positive `x^2` or `x^6` fibers and therefore four real roots.
    - `structured` and `fixed_sparse_template` favor sparse/exact-composed
      support, but do not encode four positive lower-degree fibers; in the
      bounded `r=8` pass they landed mostly at `r=0/2/4`.
    - A pure `g(x^6)` `r=8` seed would need a monic quartic `g` with four
      positive real roots. Exhaustive exact checking for coefficient bound 4
      found no such quartic, so a coefficient-bound-4 pure quartic lift cannot
      be the whole construction.
  - [pending] Design and implement a narrow explicit construction, add tests,
    run a tiny smoke, and only scale if smoke produces valid `r=8` rows.
  - Implementation:
    - Added opt-in generation strategy `r8_quartic_lift` to
      `src/envs/igp24.py`.
    - Construction: pure `g(x^6)` quartic lifts where `g` has four positive
      real roots, so each positive quartic fiber contributes two real roots
      and the degree-24 lift has intended `real_root_count=8`.
    - Metadata records template name, core support `[0,6,12,18]`, quartic
      coefficients, positive-root count, minimum coefficient bound,
      perturbation method `none_pure_composed_seed`, `target_r_heuristic=8`,
      and exact composed-support divisor `6`.
    - Added `r8_quartic_lift` to `scripts/igp24_benchmark.py` as an accepted
      explicit strategy, but kept it out of the default benchmark run set
      because it requires `coeff_bound >= 14`.
  - Focused tests:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`.
    - Result: 26 passed in 1.09s.
  - Compile check for changed files:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src/envs/igp24.py scripts/igp24_benchmark.py tests/test_igp24.py tests/test_igp24_benchmark.py`.
    - Result: passed.
  - Tiny smoke probe:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies r8_quartic_lift --seeds 824 --target_rs 8 --gensize 6 --pop_size 4 --ntest 1 --gen_batch_size 1 --max_local_search_steps 0 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 16 --output_dir /tmp/igp24_r8_quartic_lift_smoke_20260706`.
    - Result: 1 CPU-only run, returncode 0, 4 valid examples, 4 ledger
      records, 4 `r=8` matches, match rate 1.000, best matching score
      10185.844543.
    - Interpretation: the explicit construction clears the smoke gate; it can
      intentionally produce valid degree-24 `r=8` candidates locally.
  - Bounded construction probe:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies r8_quartic_lift --seeds 824,825,826 --target_rs 8 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 2 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 16 --output_dir /tmp/igp24_r8_quartic_lift_bench_20260706`.
    - Result: 3 CPU-only runs, all returncode 0, 16 valid examples, 16
      ledger records, 16 `r=8` matches, average match rate 1.000, and best
      matching score 10185.844543.
    - Artifacts:
      `/tmp/igp24_r8_quartic_lift_bench_20260706/summary.json`,
      `/tmp/igp24_r8_quartic_lift_bench_20260706/summary.jsonl`,
      and
      `/tmp/igp24_r8_quartic_lift_bench_20260706/aggregate_summary.json`.
  - Non-generic diagnostic:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_r8_quartic_lift_bench_20260706 --target_r 8 --strategies r8_quartic_lift --limit 12 --output_dir /tmp/igp24_r8_quartic_lift_diagnostic_20260706`.
    - Result: `loaded_records=16`, `diagnosed_records=6`,
      `selected_records=6`, `top_non_generic_score=2038.711136`.
    - Flag counts:
      `{"all_sampled_frobenius_even": 6, "exact_composed_support": 6, "near_composed_support": 6, "no_long_cycle_witness_in_sample": 6, "square_discriminant_excludes_s24": 6, "very_near_square_discriminant": 6, "very_sparse_support": 6}`.
    - Artifacts:
      `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_summary.json`,
      `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_diagnostic.jsonl`,
      `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_shortlist.jsonl`,
      and
      `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_report.md`.
  - Score-1 target-analysis rerun on the explicit `r=8` construction:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score1_target_analysis.py --score1_snapshot_json data/igp24/top_contestant_score1_snapshot_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json --candidate_input /tmp/igp24_r8_quartic_lift_bench_20260706 --diagnostic_jsonl /tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_diagnostic.jsonl --target_rs 8 --candidate_limit 12 --output_dir /tmp/igp24_r8_quartic_lift_score1_analysis_20260706`.
    - Result: `selected_candidate_records=6`,
      `selected_candidate_r_counts={"8": 6}`, and `queue_status=produced`.
    - Artifacts:
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_target_analysis_summary.json`,
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_target_rankings.jsonl`,
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_queue.jsonl`,
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`,
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_hashes.txt`,
      and
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_target_analysis_report.md`.
  - Structure audit:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_queue.jsonl --priority_limit 6 --output_dir /tmp/igp24_r8_quartic_lift_structure_audit_20260706`.
    - Result: `records_loaded=6`, `records_audited=6`,
      `square_claim_status_counts={"confirmed": 6}`,
      `exact_composed_claim_status_counts={"confirmed": 6}`,
      `priority_records=6`, `square_claim_refuted=0`, and
      `exact_composed_claim_refuted=0`.
  - Dry-run manual verification packet:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_queue.jsonl --output_dir /tmp/igp24_r8_quartic_lift_manual_queue_20260706 --timeout_seconds 5 --online_magma_manual`.
    - Result: `loaded_review_records=6`, `input_kind=candidate_jsonl`,
      `pari_available=false`, `magma_available=false`,
      `pari_executed=false`, `magma_executed=false`, and
      `magma_status_counts={"dry_run": 6}`.
    - Artifacts:
      `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/verification_batch.jsonl`,
      `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/verification_coefficients.txt`,
      `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/verification_plan.md`,
      and
      `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/online_magma_manual`.
  - Current recommendation: manually verify the 6-row `r=8` queue before
    widening the construction. The construction works locally and gives strong
    proxy anti-`S24`/imprimitive evidence, but exact labels are still unknown.
  - Periodic checkpoint commit:
    `59d4698 Add explicit r8 quartic lift strategy`.
    - After the commit, the smoke/bench/diagnostic/queue artifacts above were
      regenerated so their `source_commit` fields point at `59d4698`.
  - [done] Run final validation, confirm Stage 4, audit process/GPU state,
    commit, and push.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 149 passed in 6.25s.
    - Full compile check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
      - Result: passed.
    - JSON/JSONL artifact validation:
      - Parsed JSON summaries/manifests:
        `/tmp/igp24_r8_quartic_lift_smoke_20260706/summary.json`,
        `/tmp/igp24_r8_quartic_lift_smoke_20260706/aggregate_summary.json`,
        `/tmp/igp24_r8_quartic_lift_bench_20260706/summary.json`,
        `/tmp/igp24_r8_quartic_lift_bench_20260706/aggregate_summary.json`,
        `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_summary.json`,
        `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_target_analysis_summary.json`,
        `/tmp/igp24_r8_quartic_lift_structure_audit_20260706/structure_summary.json`,
        `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/offline_verification_manifest.json`,
        `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/magma_verification_summary.json`,
        and
        `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/online_magma_manual/online_magma_manual_summary.json`.
      - Parsed JSONL artifacts:
        `/tmp/igp24_r8_quartic_lift_smoke_20260706/summary.jsonl`
        with 1 record,
        `/tmp/igp24_r8_quartic_lift_bench_20260706/summary.jsonl`
        with 3 records,
        `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_diagnostic.jsonl`
        with 6 records,
        `/tmp/igp24_r8_quartic_lift_diagnostic_20260706/non_generic_shortlist.jsonl`
        with 6 records,
        `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_target_rankings.jsonl`
        with 50 records,
        `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_queue.jsonl`
        with 6 records,
        `/tmp/igp24_r8_quartic_lift_structure_audit_20260706/structure_audit.jsonl`
        with 6 records,
        `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/verification_batch.jsonl`
        with 6 records, and
        `/tmp/igp24_r8_quartic_lift_manual_queue_20260706/online_magma_manual/online_magma_manual_results.jsonl`
        with 0 records.
    - No-brackets queue coefficient validation:
      `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`.
      - Result: 6 rows, each with exactly 25 integer coefficients, no
        brackets, nonzero constant coefficient, monic leading coefficient, and
        coefficient gcd 1.
      - Note: `non_generic_coefficients.txt` and offline verifier
        `verification_coefficients.txt` are internal bracketed helper
        artifacts; the submission-style queue coefficient file above is the
        no-brackets artifact.
    - Whitespace check:
      `git diff --check`.
      - Result: passed.
    - Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 6816 after this TODO
        update.
    - Process audit:
      `ps -eo pid,ppid,stat,comm,args | awk '$4 ~ /^(python|python3|pytest|magma|gp)$/ {print}'`.
      - Result: no lingering Python, pytest, Magma, or GP workers.
    - GPU audit:
      `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
      - Result: no GPU compute apps; no GPU/model training was started.

- [done] Ground the six explicit `r=8` quartic-lift rows in a
  repo-tracked submission and feedback packet.
  - Goal source:
    `/home/zpconn/.codex/attachments/db6b7ac2-a9cc-4610-a46d-84e1a2b121d4/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev`.
  - Required artifacts read:
    `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706`,
    `/tmp/igp24_r8_quartic_lift_structure_audit_20260706`,
    and
    `/tmp/igp24_r8_quartic_lift_manual_queue_20260706`.
  - No-brackets coefficient verification:
    `/tmp/igp24_r8_quartic_lift_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`.
    - Result: 6 rows, exactly 25 integer coefficients per row, no brackets,
      nonzero constant coefficient, monic leading coefficient, and
      coefficient gcd 1.
  - Repo-tracked submission packet added:
    `data/igp24/r8_quartic_lift_submission_packet_20260706.json`.
    - Includes the six coefficient rows, canonical hashes, short hashes,
      `source_strategy=r8_quartic_lift`, expected `r=8`, local
      `real_root_count=8`, proxy scores, local polynomial discriminant
      evidence, square-discriminant/exact-composed-support audit status, and
      explicit `pending_sair_feedback` markers for labels, exact scoring
      discriminants, solvability, teams/k, and pair scores.
  - Submission-ready no-brackets coefficient copy:
    `data/igp24/r8_quartic_lift_submission_coefficients_20260706.txt`.
    - This is the path to paste into the SAIR UI. It contains no labels,
      signatures, discriminants, or brackets.
  - Manual feedback template:
    `data/igp24/r8_quartic_lift_sair_feedback_template_20260706.csv`.
    - Fields: row number, canonical hash, short hash, label, r,
      accepted/rejected status, reason, scoring discriminant, discriminant
      type, teams/k, pair score, solvable, and notes.
  - Submission instructions:
    `data/igp24/r8_quartic_lift_submission_instructions_20260706.md`.
  - Periodic checkpoint commit:
    `084fd44 Add r8 quartic lift submission packet`.
  - Pending feedback task:
    after SAIR returns verifier/scoring feedback, fill the CSV template and
    update the packet or add a companion feedback JSON with exact labels,
    exact `r`, scoring discriminants, discriminant types, teams/k, solvability,
    and pair scores.
  - SAIR acceptance feedback recorded after user report:
    - User-reported verifier result: 6/6 rows accepted.
    - Row labels:
      row 1 `24T1310|r=8`, row 2 `24T1310|r=8`,
      row 3 `24T661|r=8`, row 4 `24T657|r=8`,
      row 5 `24T9993|r=8`, and row 6 `24T9993|r=8`.
    - Distinct accepted pair keys:
      `24T657|r=8`, `24T661|r=8`, `24T1310|r=8`, and
      `24T9993|r=8`.
    - Updated feedback CSV:
      `data/igp24/r8_quartic_lift_sair_feedback_template_20260706.csv`.
    - Added accepted-feedback JSON:
      `data/igp24/r8_quartic_lift_sair_accepted_feedback_20260706.json`.
    - Updated submission packet status:
      `accepted_labels_scores_pending`.
    - Updated local pair-status ledger:
      `data/igp24/pair_status_20260706.json`.
    - Scores, scoring discriminants, discriminant types, teams/k, and
      solvability are still pending.
    - Accepted-feedback validation:
      - Result: accepted-feedback JSON parsed, updated CSV parsed, packet
        status is `accepted_labels_scores_pending`, all six packet rows carry
        the expected accepted label/status, and the local pair-status ledger
        includes the four accepted score-pending `r=8` pair keys with duplicate
        accepted rows preserved as alternates.
  - Focused data validation:
    - Result: packet JSON parsed, CSV feedback template parsed, 6 packet rows
      matched the tracked coefficient file, all coefficient rows have exactly
      25 integers, no brackets, nonzero constant coefficient, monic leading
      coefficient, and coefficient gcd 1.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 149 passed in 7.41s.
  - Whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 6899 after this TODO update.

- [done] Test whether the explicit composed-family path extends to
  `r=16` via `r16_quadratic_lift`.
  - Goal source:
    `/home/zpconn/.codex/attachments/ad505068-bc52-4f56-a222-4d8899d61bfd/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev`.
  - Required files read:
    `TODO_IGP24.md`, `NOTES_IGP24.md`, `docs/EXPERIMENTS.md`,
    `src/envs/igp24.py`, `scripts/igp24_benchmark.py`,
    `tests/test_igp24.py`, `tests/test_igp24_benchmark.py`,
    `data/igp24/r8_quartic_lift_sair_accepted_feedback_20260706.json`,
    and `data/igp24/pair_status_20260706.json`.
  - Current intent: cheaply find explicit degree-12 base polynomials `g(y)`
    with exactly 8 positive real roots, form `g(x^2)`, and only then add an
    opt-in generator/tests/smoke if local `real_root_count=16` is confirmed.
  - Safety scope: no GPU/model training, broad search, SAIR API automation,
    online Magma automation, or long benchmark in this goal.
  - Construction probe:
    - A first near-product perturbation search found exact-valid
      `g(x^2)` candidates with local `real_root_count=16` at coefficient
      height 3158.
    - A faster integer-convolution scan over small quadratic factors found a
      lower-height product family around coefficient height 703. Small
      coefficient perturbations of that base stayed `r=16` and passed local
      irreducible/exact scoring.
    - Selected eight explicit base templates of degree 12 with 8 positive
      base roots and minimum `coeff_bound=703`.
  - Implementation checkpoint:
    - Added opt-in strategy `r16_quadratic_lift` to `src/envs/igp24.py`.
    - Construction: pure `g(x^2)` degree-24 lifts where degree-12 `g` has
      exactly 8 positive real roots, so each positive base fiber contributes
      two real roots and the degree-24 polynomial has intended
      `real_root_count=16`.
    - Metadata records template name, core support `[0,2,...,22]`, base
      coefficients, positive base root count, base degree, minimum coefficient
      bound, perturbation source, `target_r_heuristic=16`, and composed
      support divisor `2`.
    - Added `r16_quadratic_lift` to `scripts/igp24_benchmark.py` as an
      accepted explicit strategy, but kept it out of the default benchmark run
      set alongside `r8_quartic_lift`.
  - Focused tests:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`.
    - Result: 28 passed in 0.85s.
  - Compile check for changed files:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src/envs/igp24.py scripts/igp24_benchmark.py tests/test_igp24.py tests/test_igp24_benchmark.py`.
    - Result: passed.
  - Whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 6953 after this TODO update.
  - Periodic checkpoint commit:
    `b66a2a0 Add explicit r16 quadratic lift strategy`.
  - Tiny smoke probe:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies r16_quadratic_lift --seeds 1601 --target_rs 16 --gensize 4 --pop_size 4 --ntest 1 --gen_batch_size 1 --max_local_search_steps 0 --prime_limit 7 --exact_score_timeout 3.0 --coeff_bound 703 --output_dir /tmp/igp24_r16_quadratic_lift_smoke_20260706`.
    - Result: 1 CPU-only run, returncode 0, 4 valid examples, 4 ledger
      records, 4 `r=16` matches, match rate 1.000, best matching score
      9411.793318.
  - Bounded construction probe:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies r16_quadratic_lift --seeds 1601,1602,1603 --target_rs 16 --gensize 8 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 1 --prime_limit 7 --exact_score_timeout 3.0 --coeff_bound 703 --output_dir /tmp/igp24_r16_quadratic_lift_bench_20260706`.
    - Result: 3 CPU-only runs, all returncode 0, 17 valid examples, 19
      ledger records, 19 `r=16` matches, average match rate 1.000, and best
      matching score 9414.762585.
    - Artifacts:
      `/tmp/igp24_r16_quadratic_lift_bench_20260706/summary.json`,
      `/tmp/igp24_r16_quadratic_lift_bench_20260706/summary.jsonl`,
      and
      `/tmp/igp24_r16_quadratic_lift_bench_20260706/aggregate_summary.json`.
  - Non-generic diagnostic:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_r16_quadratic_lift_bench_20260706 --target_r 16 --strategies r16_quadratic_lift --limit 12 --output_dir /tmp/igp24_r16_quadratic_lift_diagnostic_20260706`.
    - Result: `loaded_records=19`, `diagnosed_records=10`,
      `selected_records=10`, `top_non_generic_score=725.0`,
      `flag_counts={"exact_composed_support": 10, "near_composed_support": 10, "no_long_cycle_witness_in_sample": 6}`,
      and `skipped_counts={"duplicate_canonical_hash": 9}`.
  - Score-1 target-analysis queue:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score1_target_analysis.py --score1_snapshot_json data/igp24/top_contestant_score1_snapshot_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json --sair_label_feedback_json data/igp24/r8_quartic_lift_sair_accepted_feedback_20260706.json --candidate_input /tmp/igp24_r16_quadratic_lift_bench_20260706 --diagnostic_jsonl /tmp/igp24_r16_quadratic_lift_diagnostic_20260706/non_generic_diagnostic.jsonl --target_rs 16 --candidate_limit 8 --output_dir /tmp/igp24_r16_quadratic_lift_score1_analysis_20260706`.
    - Result: `selected_candidate_records=8`,
      `selected_candidate_r_counts={"16": 8}`, and
      `queue_status=produced`.
    - No-brackets coefficient file:
      `/tmp/igp24_r16_quadratic_lift_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`.
  - Structure audit:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_r16_quadratic_lift_score1_analysis_20260706/score1_saved_candidate_queue.jsonl --priority_limit 8 --output_dir /tmp/igp24_r16_quadratic_lift_structure_audit_20260706`.
    - Result: `records_loaded=8`, `records_audited=8`,
      `square_claim_status_counts={"not_claimed": 8}`,
      `exact_composed_claim_status_counts={"confirmed": 8}`,
      `primary_block_divisor_counts={"2": 8}`, `priority_records=8`,
      `square_claim_refuted=0`, and `exact_composed_claim_refuted=0`.
  - Dry-run manual verification packet:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r16_quadratic_lift_score1_analysis_20260706/score1_saved_candidate_queue.jsonl --output_dir /tmp/igp24_r16_quadratic_lift_manual_queue_20260706 --timeout_seconds 5 --online_magma_manual`.
    - Result: `loaded_review_records=8`, `input_kind=candidate_jsonl`,
      `pari_available=false`, `magma_available=false`,
      `pari_executed=false`, `magma_executed=false`, and
      `magma_status_counts={"dry_run": 8}`.
  - SAIR verifier feedback:
    - User-reported table rows 1-8 were all accepted as `24T24979|r=16`;
      the pasted count line said 6/6, but the row table contained eight rows.
    - Tracked coefficient copy:
      `data/igp24/r16_quadratic_lift_submission_coefficients_20260706.txt`.
    - Tracked feedback artifact:
      `data/igp24/r16_quadratic_lift_sair_accepted_feedback_20260706.json`.
    - Ledger update: added one distinct accepted pair,
      `24T24979|r=16`, with rows 2-8 preserved as accepted alternates.
    - Baseline check: `24T24979|r=16` has 0 rows in the frozen baseline, so
      this is a potentially scoreable new pair once SAIR scoring returns.
    - Scores, scoring discriminants, discriminant type, solvability, and
      teams/k remain pending.
  - SAIR CSV scoring-status export:
    - Artifact:
      `data/igp24/r16_quadratic_lift_sair_status_export_20260706.csv`.
    - Submission id: `sub_02ecc2457d124584b8325b83608a2e9c`.
    - Result: all eight rows remain `accepted`, `label=24T24979`, `r=16`,
      `scoreable=false`, `scoringStatus=pending`,
      `scoringReason=discriminant_pending`, `noScoreReason` blank,
      `inBaseline=false`, `baselineUnlocked=false`, and discriminant fields
      blank.
    - Interpretation: `scoreable=false` is provisional while SAIR computes the
      discriminant; it is not recorded as final unscoreable/no-score status.
    - Ledger update: `24T24979|r=16` score status refined to
      `discriminant_pending`, the SAIR submission id and CSV source were
      recorded, and all seven accepted alternates were preserved.
  - Bounded r16 diversification helper:
    - Added `scripts/igp24_r16_diversity_probe.py`.
    - Purpose: build a small local queue that tries to avoid the accepted
      `24T24979|r=16` template by using different degree-12 base root layouts
      for `g(x^2)`, including both exact-composed rows and rows with one tiny
      odd-power perturbation.
    - Safety: CPU-only, file-only, no GPU/model training, no GPU sampling, no
      SAIR API/submission, no Magma/PARI/network calls, and no local search.
    - Added focused helper test:
      `tests/test_igp24.py::test_r16_diversity_probe_helpers_build_degree24_lift`.
  - Focused helper validation:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py::test_r16_diversity_probe_helpers_build_degree24_lift`.
    - Result: 1 passed in 0.29s.
  - Compile check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_r16_diversity_probe.py tests/test_igp24.py`.
    - Result: passed.
  - Short CPU-only diversification probe:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r16_diversity_probe.py --output_dir data/igp24/r16_diversity_probe_20260706 --seed 1616 --max_trials 240 --limit 10 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 4.0 --min_l1_to_accepted_even 5000`.
    - Result: `trials_attempted=240`, `valid_r16_candidates=189`,
      `selected_rows=10`, `selected_mode_counts={"exact_composed_new_base": 5, "odd_perturbed_near_composed": 5}`,
      `rejected_counts={"coefficient_height_exceeds_bound": 32, "real_root_count_mismatch": 19}`,
      and `queue_status=produced`.
    - Artifacts:
      `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_coefficients.txt`,
      `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_queue.jsonl`,
      `data/igp24/r16_diversity_probe_20260706/r16_diversified_candidate_hashes.txt`,
      `data/igp24/r16_diversity_probe_20260706/r16_diversified_summary.json`,
      and
      `data/igp24/r16_diversity_probe_20260706/r16_diversified_report.md`.
    - Queue shape: 10 no-brackets SAIR-format rows, 10 unique hashes, 10
      unique family keys, and no selected hash overlaps the accepted/known
      pair-status ledger hashes.
    - Local exact validation: all 10 rows have 25 integer coefficients,
      nonzero constant coefficient, monic leading coefficient, coefficient
      gcd 1, local `real_root_count=16`, `irreducible=true`,
      `squarefree=true`, and no exact label claim.
    - Structural evidence: exact-composed rows carry exact divisor-2 support;
      odd-perturbed rows carry near-composed divisor-2 support. All selected
      rows record modular-factorization proxy evidence and their minimum L1
      distance from the accepted r16 even-coefficient templates.
  - SAIR verifier feedback for diversified r16 queue:
    - User-reported at `Jul 6, 2026, 04:20 PM`: 10/10 accepted.
    - Tracked feedback artifact:
      `data/igp24/r16_diversity_probe_sair_accepted_feedback_20260706.json`.
    - Row labels: rows 1, 3, 5, 7, and 9 were accepted as `24T24979|r=16`;
      rows 2, 4, 6, 8, and 10 were accepted as `24T25000|r=16`.
    - Baseline check: both `24T24979|r=16` and `24T25000|r=16` have 0 rows
      in the frozen baseline.
    - Ledger update: appended five accepted `24T24979|r=16` alternates and
      added new accepted score-pending pair `24T25000|r=16` with four
      alternates.
    - Interpretation: exact-composed new-base rows still collapse to
      `24T24979|r=16`; odd-power perturbations do move the exact label, but
      this batch moved into generic-looking `24T25000|r=16`, not a lower
      non-generic label. Scores, scoring discriminants, solvability, and
      teams/k remain pending.
  - Acceptance feedback validation:
    - Result: parsed
      `data/igp24/r16_diversity_probe_sair_accepted_feedback_20260706.json`;
      confirmed 10 accepted rows, label counts `{"24T24979": 5, "24T25000": 5}`,
      ledger updates for `24T24979|r=16` and `24T25000|r=16`, and 0 frozen
      baseline rows for both pairs.
    - Full test suite rerun:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 152 passed in 7.61s.
  - Anti-collapse r16 probe helper update:
    - Extended `scripts/igp24_r16_diversity_probe.py` with opt-in
      multi-perturbation modes and filters:
      `two_odd_perturbed_near_composed`,
      `three_odd_perturbed_near_composed`,
      `four_odd_perturbed_near_composed`, and
      `mixed_even_odd_perturbed`.
    - Added accepted-feedback loaders so the probe can compare candidates
      against both the first r16 SAIR CSV rows and the accepted rows from
      `data/igp24/r16_diversity_probe_20260706`.
    - Added full-row L1 metadata, divisor-2 off-block term/exponent metadata,
      and min/max off-block filters. This explicitly excludes the prior
      collapse corridors: exact divisor-2 `g(x^2)` rows and one-odd
      near-composed rows.
    - Focused validation:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_r16_diversity_probe.py tests/test_igp24.py`
      and
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py::test_r16_diversity_probe_helpers_build_degree24_lift tests/test_igp24.py::test_r16_diversity_probe_multi_odd_modes_escape_one_odd_support`.
      - Result: 2 passed in 0.73s.
    - Checkpoint commit: `52de629 Add anti-collapse r16 probe modes`.
  - Anti-collapse r16 probe run:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_r16_diversity_probe.py --output_dir data/igp24/r16_anti_collapse_probe_20260706 --seed 2616 --max_trials 720 --limit 12 --per_family_cap 1 --coeff_bound 20000000 --prime_limit 7 --exact_score_timeout 4.0 --min_l1_to_accepted_even 5000 --min_l1_to_accepted_full 5000 --no-include_exact --no-include_odd --include_two_odd --include_three_odd --include_mixed_even_odd --min_off_block_terms 2 --max_off_block_terms 4`.
    - Result: `trials_attempted=720`, `valid_r16_candidates=149`,
      `selected_rows=12`,
      `selected_mode_counts={"mixed_even_odd_perturbed": 4, "three_odd_perturbed_near_composed": 4, "two_odd_perturbed_near_composed": 4}`,
      `rejected_counts={"coefficient_height_exceeds_bound": 112, "real_root_count_mismatch": 298, "reducible_over_q": 91, "too_close_to_accepted_even_coefficients": 70}`,
      and `queue_status=produced`.
    - Artifacts:
      `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_coefficients.txt`,
      `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_queue.jsonl`,
      `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_candidate_hashes.txt`,
      `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_summary.json`,
      `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_rejected_trials.jsonl`,
      and
      `data/igp24/r16_anti_collapse_probe_20260706/r16_diversified_report.md`.
    - Local validation: parsed all new artifacts; confirmed 12 rows with 25
      integer coefficients, nonzero constant, monic leading coefficient,
      coefficient gcd 1, local `real_root_count=16`, irreducible and
      squarefree exact checks, stable canonical hashes, no overlap with the
      accepted/known r16 ledger hashes, no duplicate family keys, no exact or
      one-odd collapse modes, and diagnostic divisor-2 off-block counts in
      range. Off-block counts were `{"2": 8, "3": 4}`, and minimum full-row L1
      distance to accepted r16 rows was 411103.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 153 passed in 7.30s.
    - Final whitespace check:
      `git diff --check`.
      - Result: passed.
    - Final Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 7213 after this TODO update.
    - Process/GPU audit: `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`
      returned no GPU compute apps; `ps -eo pid,ppid,stat,comm,args` showed
      no lingering Python, pytest, Magma, GP, or training workers beyond the
      audit command itself.
  - SAIR verifier feedback for anti-collapse r16 queue:
    - User-reported result: 12/12 accepted, all as `24T25000|r=16`.
    - Tracked feedback artifact:
      `data/igp24/r16_anti_collapse_probe_sair_accepted_feedback_20260706.json`.
    - Ledger update: appended 12 accepted `24T25000|r=16` alternates to
      `data/igp24/pair_status_20260706.json`, with source modes and
      off-block term counts recorded.
    - Interpretation: exact divisor-2 `g(x^2)` rows reliably land as
      `24T24979|r=16`; one-odd and multi-off-block near-composed divisor-2
      perturbations reliably land as `24T25000|r=16`. Do not spend more
      submissions widening this same r16 corridor unless a genuinely different
      construction is available.
  - Discovery snapshot artifact:
    - Added `data/igp24/sair_discovery_snapshot_20260706_1648.json`.
    - Source: user-provided screenshot analysis captured 2026-07-06 16:48
      America/Chicago, not live API data.
    - Totals: `total_valid_signatures=165836`,
      `solved_signatures=112825`, `uncovered_signatures=53011`,
      `lmfdb_baseline=622`, and `uncovered_solvable=51992` (98.1% of
      uncovered signatures).
    - Largest remaining buckets by count:
      `r=24:12126`, `r=16:10902`, `r=8:6988`, `r=12:6919`,
      and `r=20:5773`.
    - Caveat: exact uncovered `(24Tt, r)` target lists must come from the SAIR
      API; the screenshot only gives aggregate r-bucket coverage.
  - Target-aware bucket planner:
    - Added `scripts/igp24_target_bucket_plan.py`.
    - Focused validation:
      `python3 -m compileall scripts/igp24_target_bucket_plan.py tests/test_igp24_target_bucket_plan.py`
      passed, and bare `pytest` was unavailable on PATH.
    - Focused tests:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_target_bucket_plan.py`.
      - Result: 3 passed in 0.04s.
    - Planner run:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_target_bucket_plan.py --discovery_snapshot_json data/igp24/sair_discovery_snapshot_20260706_1648.json --pair_status_json data/igp24/pair_status_20260706.json --output_dir data/igp24/target_bucket_plan_20260706`.
      - Result: `api_target_list_available=false`,
        `top_remaining_rs=[24,16,8,12,20]`, and
        `top_action_rs=[24,20,8,12,16]`.
      - Artifacts:
        `data/igp24/target_bucket_plan_20260706/target_bucket_plan.json`,
        `data/igp24/target_bucket_plan_20260706/target_bucket_plan.md`, and
        `data/igp24/target_bucket_plan_20260706/target_bucket_plan_summary.json`.
      - Recommendation: prioritize a new explicit `r=24`
        solvable/high-real-root construction; prototype `r=20` and `r=12`;
        continue bounded `r=8` composed-family work because it already
        produced multiple accepted labels; keep `r=16` globally important but
        do not widen the current divisor-2 corridor; do not start GPU/model
        training until a target-conditioned sampling objective exists.
    - Structured artifact validation: parsed the 12-row anti-collapse
      feedback JSON, pair-status ledger, discovery snapshot JSON, target-plan
      JSON, target-plan summary JSON, and target-plan Markdown; confirmed all
      12 feedback rows are accepted `24T25000|r=16`, the pair ledger contains
      the 12 hashes, the snapshot has 165836 valid signatures and 53011
      uncovered signatures, and the planner reports
      `top_action_rs=[24,20,8,12,16]`.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 156 passed in 7.74s.
    - Final whitespace check:
      `git diff --check`.
      - Result: passed.
    - Final Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 7287 after this TODO update.
  - Structured artifact validation:
    - Result: parsed the SAIR status CSV, pair-status JSON, r16 accepted
      feedback JSON, diversified queue JSONL, diversified summary JSON, and
      diversified coefficient TXT; confirmed 8 pending-scoring SAIR rows and
      10 diversified queue rows.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 152 passed in 7.01s.
  - Final whitespace check:
    `git diff --check`.
    - Result: passed.
  - Final Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 7141 after this TODO update.
  - Process/GPU audit:
    - `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`
      returned no GPU compute apps.
    - `ps -eo pid,ppid,stat,comm,args` showed no lingering Python, pytest,
      Magma, GP, or training workers beyond the audit command itself.
  - Artifact and coefficient validation:
    - Result: parsed the smoke, bounded probe, diagnostic, score-1 queue,
      structure audit, and manual verification JSON/JSONL artifacts.
    - Result: the no-brackets queue coefficient file has 8 rows, each with
      exactly 25 integer coefficients, no brackets, nonzero constant
      coefficient, monic leading coefficient, and coefficient gcd 1.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 151 passed in 6.13s.
  - Current recommendation: wait for the `24T24979|r=16` score details and
    then diversify the `r=16` family, because this first accepted packet
    proves the construction works but collapsed to one label.
  - Final whitespace check:
    `git diff --check`.
    - Result: passed.
  - Final Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 7020 after this TODO update.
  - Process audit:
    `ps -eo pid,ppid,stat,comm,args | awk '$4 ~ /^(python|python3|pytest|magma|gp)$/ {print}'`.
    - Result: no lingering Python, pytest, Magma, or GP workers.
  - GPU audit:
    `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
    - Result: no GPU compute apps; no GPU/model training was started.

- [done] Run a bounded CPU-only `r=8` lower-label target-generation
  pass.
  - Goal source:
    `/home/zpconn/.codex/attachments/f4264d24-a929-42dc-9355-21eb325415d5/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev` at `59b9f77`.
  - Starting status:
    `git status --short --branch`.
    - Result: clean on `igp24-dev`.
  - Score-1 analysis inputs read:
    `/tmp/igp24_score1_target_analysis_20260706/score1_target_analysis_summary.json`,
    `/tmp/igp24_score1_target_analysis_20260706/score1_target_rankings.jsonl`,
    and
    `/tmp/igp24_score1_target_analysis_20260706/score1_target_analysis_report.md`.
    - Result: the top 13 ranked targets are all `r=8` pairs
      `24T324`, `24T319`, `24T316`, `24T315`, `24T314`, `24T313`,
      `24T307`, `24T304`, `24T302`, `24T301`, `24T294`, `24T293`,
      and `24T290`; all are absent from the frozen baseline and local
      accepted-pair ledger, and all have zero saved `r=8` candidate coverage.
    - Important caveat: these are exact target labels from the external
      score-1 snapshot, not labels we can claim for generated rows.
  - Generator/template inspection:
    `scripts/igp24_benchmark.py` is the existing bounded CPU-only entry point
    for running `train.py` data-generation-only probes with `--target_r`.
    Existing generators include `sparse`, `lower_degree`, `structured`,
    `quartic_lift`, `fixed_sparse_template`, and `mixed`.
    - Interpretation: current built-in presets cover `r=0`, `r=2`, and
      `r=4`, but there is no dedicated `r=8` preset/template. The most
      plausible current knobs for an immediate probe are target-scored
      `structured`, `lower_degree`, `sparse`, `fixed_sparse_template`, and a
      mixed blend biased toward structured sparse support.
  - Planned bounded run:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies structured,lower_degree,sparse,fixed_sparse_template,mixed --seeds 801,802 --target_rs 8 --gensize 16 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 4 --sparse_terms 4 --low_height_bound 2 --mixed_strategy_weights sparse:0.20,lower_degree:0.20,structured:0.45,fixed_sparse_template:0.15 --output_dir /tmp/igp24_r8_targeted_bench_20260706`.
    - Scope: 10 short CPU-only runs, no model training, no GPU sampling, no
      SAIR/API/submission, no Magma/PARI/online calculator execution.
  - Bounded benchmark result:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies structured,lower_degree,sparse,fixed_sparse_template,mixed --seeds 801,802 --target_rs 8 --gensize 16 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3.0 --coeff_bound 4 --sparse_terms 4 --low_height_bound 2 --mixed_strategy_weights sparse:0.20,lower_degree:0.20,structured:0.45,fixed_sparse_template:0.15 --output_dir /tmp/igp24_r8_targeted_bench_20260706`.
    - Result: 10 runs, all returncode 0, 160 valid examples, 297 ledger
      records, and 0 records with `real_root_count=8`.
    - Best proxy score: 10012.734145702047 from `mixed` seed 801.
    - Aggregate strategy result: every tested strategy had
      `target_r_match_total=0` and `avg_match_rate=0.0`.
    - Observed real-root distribution across all ledger records:
      `{"0": 38, "2": 211, "4": 47, "6": 1}`.
    - Interpretation: the current target-scored versions of `structured`,
      `lower_degree`, `sparse`, `fixed_sparse_template`, and the structured
      sparse-biased `mixed` blend did not reach the uncovered `r=8` score-1
      target mode, even though they produced ordinary valid rows.
    - Artifacts:
      `/tmp/igp24_r8_targeted_bench_20260706/summary.json`,
      `/tmp/igp24_r8_targeted_bench_20260706/summary.jsonl`,
      and
      `/tmp/igp24_r8_targeted_bench_20260706/aggregate_summary.json`.
  - `r=8` non-generic diagnostic:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_r8_targeted_bench_20260706 --target_r 8 --limit 12 --output_dir /tmp/igp24_r8_targeted_diagnostic_20260706`.
    - Result: `loaded_records=297`, `diagnosed_records=0`,
      `selected_records=0`, `top_non_generic_score=NA`, and
      `skipped_counts={"target_r_mismatch": 297}`.
    - Artifacts:
      `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_summary.json`,
      `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_diagnostic.jsonl`,
      `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_shortlist.jsonl`,
      and
      `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_report.md`.
  - Score-1 target-analysis rerun on the bounded `r=8` artifacts:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score1_target_analysis.py --score1_snapshot_json data/igp24/top_contestant_score1_snapshot_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json --candidate_input /tmp/igp24_r8_targeted_bench_20260706 --diagnostic_jsonl /tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_diagnostic.jsonl --target_rs 8 --candidate_limit 12 --output_dir /tmp/igp24_r8_targeted_score1_analysis_20260706`.
    - Result: `selected_candidate_records=0`, `selected_candidate_r_counts={}`,
      `candidate_skipped_counts={"duplicate_hash": 4, "target_r_mismatch": 293}`,
      and `queue_status=not_produced`.
    - No manual-verification queue was produced, and no rows were padded.
    - Artifacts:
      `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_target_analysis_summary.json`,
      `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_target_rankings.jsonl`,
      `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_saved_candidate_queue.jsonl`,
      and
      `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_target_analysis_report.md`.
  - Current recommendation: do not widen this same benchmark style or start a
    big GPU/model run yet. The immediate lesson is that the current
    coefficient templates are biased toward `r=0/2/4`; the next meaningful
    step should be a new explicit `r=8` solvable/composed-family construction
    or template, for example an imprimitive even/composed support designed to
    make eight real roots plausible before exact-label verification.
  - Periodic checkpoint commit:
    `e7c8615 Record bounded r8 target probe`.
  - [done] Update notes/experiments, run final validation, commit, and push.
    - Documentation updates:
      `NOTES_IGP24.md` and `docs/EXPERIMENTS.md` now record the `r=8`
      benchmark result, artifact paths, no-queue outcome, and recommendation
      to design an explicit `r=8` solvable/composed-family construction next.
      `README.md` was unchanged because no public/basic workflow changed.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 147 passed in 6.10s.
    - Compile check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
      - Result: passed.
    - JSON/JSONL artifact validation:
      - Parsed JSON summaries:
        `/tmp/igp24_r8_targeted_bench_20260706/summary.json`,
        `/tmp/igp24_r8_targeted_bench_20260706/aggregate_summary.json`,
        `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_summary.json`,
        and
        `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_target_analysis_summary.json`.
      - Parsed JSONL artifacts:
        `/tmp/igp24_r8_targeted_bench_20260706/summary.jsonl`
        with 10 records,
        `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_diagnostic.jsonl`
        with 0 records,
        `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_shortlist.jsonl`
        with 0 records,
        `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_target_rankings.jsonl`
        with 50 records, and
        `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_saved_candidate_queue.jsonl`
        with 0 records.
    - Queue/coefficient validation:
      `/tmp/igp24_r8_targeted_diagnostic_20260706/non_generic_coefficients.txt`
      and
      `/tmp/igp24_r8_targeted_score1_analysis_20260706/score1_saved_candidate_coefficients.txt`
      both validated as empty 0-row queue files; no padded rows were produced.
    - Whitespace check:
      `git diff --check`.
      - Result: passed.
    - Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 6635 after this TODO
        update.
    - Process audit:
      `ps -eo pid,ppid,stat,comm,args | awk '$4 ~ /^(python|python3|pytest|magma|gp)$/ {print}'`.
      - Result: no lingering Python, pytest, Magma, or GP workers.
    - GPU audit:
      `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
      - Result: no GPU compute apps; no GPU/model training was started.

- [done] Build score-1-style lower-label target analysis and saved
  manual-verification queue.
  - Goal source:
    `/home/zpconn/.codex/attachments/ba85c5a5-ecaf-42f6-b983-06600b8e11a8/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev` at `1912baf`.
  - Implementation:
    `scripts/igp24_score1_target_analysis.py`.
    - Local/file-only helper that joins
      `data/igp24/top_contestant_score1_snapshot_20260706.json`,
      `data/igp24/lmfdb_baseline.csv`,
      `data/igp24/pair_status_20260706.json`, saved exact-label feedback,
      SAIR accepted-label feedback, and saved proxy candidate/diagnostic
      artifacts.
    - It ranks target `(label, r)` pairs separately from proxy candidate rows
      and never claims exact labels from proxy evidence.
    - Safety: no SAIR/API calls, no online Magma automation, no Magma/PARI
      execution, no model training, no GPU sampling, no local search, and no
      CPU search loop.
  - Focused implementation tests:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_score1_target_analysis.py tests/test_igp24_next_verification_queue.py tests/test_igp24_score_aware_triage.py`.
    - Result: 17 passed in 0.05s.
  - Saved-artifact diagnostic for the available score-1 signature mode:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_target_r_bench_larger_20260704 /tmp/igp24_target_r_bench /tmp/igp24_strategy_bench_final /tmp/igp24_quartic_lift_bench_20260704 /tmp/igp24_fixed_sparse_template_bench_20260704 /tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_model_sample_export.jsonl /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/gpu_model_sample_export_diversity_fixed_template_t09_top9.jsonl /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/gpu_model_sample_export_diversity_mixed_t12_open_topk.jsonl --target_r 0 --limit 80 --output_dir /tmp/igp24_score1_r0_saved_diagnostic_20260706`.
    - Result: `loaded_records=8290`, `diagnosed_records=351`,
      `selected_records=80`, `top_non_generic_score=2085.0`.
      Flag counts:
      `{"all_sampled_frobenius_even": 40, "exact_composed_support": 80, "near_composed_support": 80, "near_square_discriminant": 1, "no_long_cycle_witness_in_sample": 66, "sparse_support": 2, "square_discriminant_excludes_s24": 40, "very_near_square_discriminant": 40, "very_sparse_support": 78}`.
    - Artifacts:
      `/tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_diagnostic.jsonl`,
      `/tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_shortlist.jsonl`,
      `/tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_summary.json`,
      and
      `/tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_report.md`.
  - Score-1 target analysis and saved-candidate queue:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score1_target_analysis.py --score1_snapshot_json data/igp24/top_contestant_score1_snapshot_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json --candidate_input /tmp/igp24_target_r_bench_larger_20260704 --candidate_input /tmp/igp24_target_r_bench --candidate_input /tmp/igp24_strategy_bench_final --candidate_input /tmp/igp24_quartic_lift_bench_20260704 --candidate_input /tmp/igp24_fixed_sparse_template_bench_20260704 --candidate_input /tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_model_sample_export.jsonl --candidate_input /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/gpu_model_sample_export_diversity_fixed_template_t09_top9.jsonl --candidate_input /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/gpu_model_sample_export_diversity_mixed_t12_open_topk.jsonl --diagnostic_jsonl /tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_diagnostic.jsonl --target_rs 0,8,12,16,24 --candidate_limit 12 --output_dir /tmp/igp24_score1_target_analysis_20260706`.
    - Result:
      `target_rows=50`,
      `target_r_counts={"0": 12, "8": 13, "12": 8, "16": 10, "24": 6, "4": 1}`,
      `target_baseline_presence_counts={"not_in_baseline": 50}`,
      `target_local_pair_status_counts={"not_in_local_ledger": 50}`,
      `target_generator_plausibility_counts={"needs_targeted_generation": 37, "saved_candidates_present": 13}`,
      `selected_candidate_records=12`,
      `selected_candidate_r_counts={"0": 12}`,
      and `queue_status=produced`.
    - Interpretation: the score-1 snapshot is completely absent from both the
      frozen baseline and our accepted ledger. Saved artifacts only cover
      `r=0` plus the single visible `r=4` signature; they do not cover the
      high-priority `r=8/12/16/24` modes. The saved `r=0` pool still yields a
      credible 12-row proxy-strong manual-verification queue.
    - Artifacts:
      `/tmp/igp24_score1_target_analysis_20260706/score1_target_rankings.jsonl`,
      `/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_queue.jsonl`,
      `/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_coefficients.txt`,
      `/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_hashes.txt`,
      `/tmp/igp24_score1_target_analysis_20260706/score1_target_analysis_summary.json`,
      and
      `/tmp/igp24_score1_target_analysis_20260706/score1_target_analysis_report.md`.
  - Structure audit for the 12-row saved `r=0` queue:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_queue.jsonl --priority_limit 12 --output_dir /tmp/igp24_score1_saved_candidate_structure_audit_20260706`.
    - Result: `records_loaded=12`, `records_audited=12`,
      `square_claim_status_counts={"confirmed": 12}`,
      `exact_composed_claim_status_counts={"confirmed": 12}`,
      `priority_records=12`, `square_claim_refuted=0`, and
      `exact_composed_claim_refuted=0`.
  - Dry-run manual verification packet:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_queue.jsonl --output_dir /tmp/igp24_score1_saved_candidate_manual_queue_20260706 --timeout_seconds 5 --online_magma_manual`.
    - Result: `loaded_review_records=12`, `input_kind=candidate_jsonl`,
      `pari_available=false`, `magma_available=false`,
      `pari_executed=false`, `magma_executed=false`, and
      `magma_status_counts={"dry_run": 12}`.
    - Artifacts:
      `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/verification_batch.jsonl`,
      `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/verification_plan.md`,
      and
      `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/online_magma_manual`.
  - Coefficient-format check:
    `/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_coefficients.txt`.
    - Result: 12 valid no-brackets lines, each with 25 integers, nonzero
      constant coefficient, and leading coefficient 1.
  - Current recommendation: use the 12 saved `r=0` proxy-strong candidates
    for manual exact verification if the user wants an immediate probe. For
    the next search step, prioritize a bounded generator/diagnostic pass for
    `r=8` first, then `r=12/16/24`, because the score-1 target ranking says
    those signatures are high-value and currently uncovered locally.
  - Periodic checkpoint commit:
    `76fc040 Add score-1 target analysis`.
  - [done] Run final validation, update notes/experiments, commit, and
    push.
    - Helper smoke check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score1_target_analysis.py --help`.
      - Result: CLI help rendered successfully.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 147 passed in 6.49s.
    - Compile check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
      - Result: passed.
    - JSON/JSONL artifact validation:
      - Parsed JSON summaries/manifests:
        `/tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_summary.json`,
        `/tmp/igp24_score1_target_analysis_20260706/score1_target_analysis_summary.json`,
        `/tmp/igp24_score1_saved_candidate_structure_audit_20260706/structure_summary.json`,
        `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/offline_verification_manifest.json`,
        `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/magma_verification_summary.json`,
        and
        `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/online_magma_manual/online_magma_manual_summary.json`.
      - Parsed JSONL artifacts:
        `/tmp/igp24_score1_r0_saved_diagnostic_20260706/non_generic_diagnostic.jsonl`
        with 351 records,
        `/tmp/igp24_score1_target_analysis_20260706/score1_target_rankings.jsonl`
        with 50 records,
        `/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_queue.jsonl`
        with 12 records,
        `/tmp/igp24_score1_saved_candidate_structure_audit_20260706/structure_audit.jsonl`
        with 12 records,
        `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/verification_batch.jsonl`
        with 12 records, and
        `/tmp/igp24_score1_saved_candidate_manual_queue_20260706/online_magma_manual/online_magma_manual_results.jsonl`
        with 0 records.
    - Coefficient validation:
      `/tmp/igp24_score1_target_analysis_20260706/score1_saved_candidate_coefficients.txt`.
      - Result: 12 valid no-brackets rows, each with 25 integer
        coefficients, nonzero constant coefficient, monic leading
        coefficient, and coefficient gcd 1.
    - Whitespace check:
      `git diff --check`.
      - Result: passed.
    - Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 6501 after this TODO
        update.
    - Process audit:
      `ps -eo pid,ppid,stat,comm,args | awk '$4 ~ /^(python|python3|pytest|magma|gp)$/ {print}'`.
      - Result: no lingering Python, pytest, Magma, or GP workers.
    - GPU audit:
      `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
      - Result: no GPU compute apps; no GPU/model training was started.
- [done] Record the 3-row strong anti-`S24` manual submission result and the
  new external score-1 strategy snapshot.
  - User-reported SAIR verifier result for
    `/tmp/igp24_strong_anti_s24_manual_queue_20260706/manual_coefficients_no_brackets.txt`:
    all 3 rows accepted.
    - Row 1: `24T21844`, `r=4`.
    - Row 2: `24T24970`, `r=4`.
    - Row 3: `24T24970`, `r=4`.
  - Feedback artifact:
    `data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json`.
    - Score status: pending.
    - Interpretation: row 1 is a new accepted local pair
      `24T21844|r=4`; rows 2-3 are accepted `24T24970|r=4`
      alternates/duplicates unless delayed SAIR scores show a better scored
      discriminant.
  - Pair-status ledger update:
    `data/igp24/pair_status_20260706.json`.
    - Added `24T21844|r=4` as accepted, score pending.
    - Added the two `24T24970|r=4` accepted rows as score-pending alternates.
  - External score-1 snapshot:
    `data/igp24/top_contestant_score1_snapshot_20260706.json`.
    - User supplied a #1-contestant table with 50 visible score-1 rows.
    - Compact local summary records the score-1 `(label, r)` pairs instead of
      copying all very large discriminant values.
    - Strategic read: those rows are unique `teams_k=1`, solvable,
      `exact_nfdisc` rows concentrated in low labels and mostly
      `r in {0,8,12,16,24}`; only one visible row is `r=4`. That argues for
      pivoting away from crowded high-label `r=4` mining toward targeted
      lower-label solvable-family/signature exploration before the next batch.
  - Post-feedback strict planner sanity check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_next_verification_queue.py --structure_audit_jsonl /tmp/igp24_strong_anti_s24_structure_audit_20260706/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json --known_verified_jsonl /tmp/igp24_pending_four_scoreability_review_20260706/scoreability_review.jsonl --candidate_jsonl /tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mined.jsonl --pair_status_json data/igp24/pair_status_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --limit 12 --max_per_structural_family 1 --avoid_sair_negative_families --require_strong_anti_s24_evidence --output_dir /tmp/igp24_strong_anti_s24_post_accept_strict_queue_20260706`.
    - Result: `annotated_records=15`, `eligible_records=0`,
      `selected_records=0`,
      `filter_reason_counts={"accepted_family_hint": 12, "sair_feedback_accepted_pair_duplicate_hash": 3}`,
      `anti_s24_evidence_status_counts={"strong": 15}`, and
      `sair_feedback_family_status_counts={"None": 12, "accepted_duplicate_prone": 3}`.
    - Interpretation: the mined strong anti-`S24` pool is now exhausted under
      the stricter post-acceptance filters; do not resubmit from it.
  - Score-aware triage with the new accepted-label feedback:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_aware_triage.py --queue_jsonl /tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_queue.jsonl --offline_dir /tmp/igp24_strong_anti_s24_manual_queue_20260706 --baseline_csv data/igp24/lmfdb_baseline.csv --pair_status_json data/igp24/pair_status_20260706.json --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json --output_dir /tmp/igp24_strong_anti_s24_sair_triage_20260706`.
    - Result: `reviewed_rows=3`, `verified_rows=3`,
      `pending_exact_label_rows=0`, `failed_rows=0`,
      `submission_grade_rows=0`,
      `classification_counts={"exact_evidence_incomplete": 3}`, and
      `labels_found_counts={"24T21844": 1, "24T24970": 2}`.
    - Interpretation: the accepted labels are usable feedback, but exact local
      discriminant/scoring evidence is still incomplete; keep delayed scores
      pending and do not promote duplicate alternates yet.
  - Validation:
    - JSON checks:
      `python3 -m json.tool data/igp24/sair_accepted_label_feedback_20260706_strong_anti_s24_queue.json`,
      `python3 -m json.tool data/igp24/pair_status_20260706.json`,
      `python3 -m json.tool data/igp24/top_contestant_score1_snapshot_20260706.json`,
      `python3 -m json.tool /tmp/igp24_strong_anti_s24_post_accept_strict_queue_20260706/next_verification_queue_manifest.json`,
      and
      `python3 -m json.tool /tmp/igp24_strong_anti_s24_sair_triage_20260706/score_aware_triage_summary.json`.
      - Result: all parsed successfully.
    - Focused tests:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_next_verification_queue.py tests/test_igp24_score_aware_triage.py`.
      - Result: 12 passed in 0.02s.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 142 passed in 7.45s.
    - Diff whitespace check:
      `git diff --check`.
      - Result: passed.
    - Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 6362 after this TODO update.
- [done] Mine or create fresh strong anti-`S24` evidence after the
  exhausted strict saved-pool pass.
  - Goal source:
    `/home/zpconn/.codex/attachments/49ecb61a-27a4-434d-8fa6-e0b516ebc9c9/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev` at `b3932c9`.
  - Initial saved-artifact finding:
    `/tmp/igp24_next_non_generic_diagnostic_20260706/non_generic_diagnostic.jsonl`
    has 1,919 diagnosed `r=4` rows, but after excluding the exhausted
    160-row structure-audit pool, 0 remaining rows have square-discriminant
    anti-`S24` evidence. Broader `/tmp/igp24_*` saved ledgers exist, so the
    next step is broader saved mining before any new CPU generation.
  - [done] Add a local/file-only saved-mining helper:
    `scripts/igp24_strong_anti_s24_mine.py`.
    - It reads diagnostic JSONL, excludes exhausted hashes, derives structural
      family keys, joins saved exact-label feedback and user-reported SAIR
      accepted-label feedback, avoids generic-prone and accepted-duplicate
      families, and writes a fresh strong anti-`S24` pool.
    - Safety: no SAIR/API calls, no online Magma automation, no Magma/PARI
      execution, no model training, no GPU sampling, no local search, and no
      CPU search loop.
  - [done] Add focused tests:
    `tests/test_igp24_strong_anti_s24_mine.py`.
    - Focused check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_strong_anti_s24_mine.py tests/test_igp24_next_verification_queue.py`.
      - Result: 10 passed in 0.02s.
  - [done] Attempt broad saved-artifact diagnostic over `/tmp/igp24_*`.
    - Command:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_* --target_r 4 --limit 500 --output_dir /tmp/igp24_strong_anti_s24_broad_diagnostic_20260706`.
    - Result: failed on one malformed old `candidates.jsonl`
      (`JSONDecodeError`), so the broad pass was narrowed to known clean saved
      benchmark ledgers.
  - [done] Run the broad saved-artifact diagnostic on clean saved ledgers.
    - Command:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py /tmp/igp24_fresh_pair_bench_20260706 /tmp/igp24_r4_second_confirm_20260704 /tmp/igp24_r4_dual_quality_confirm_20260704 /tmp/igp24_quartic_lift_bench_20260704 /tmp/igp24_r4_dual_mix_bench_20260704 /tmp/igp24_r4_mix_variant_bench_20260704 /tmp/igp24_fixed_sparse_template_bench_20260704 /tmp/igp24_four_real_seed_bench_20260704 /tmp/igp24_r4_preset_bench_20260704 --target_r 4 --limit 500 --output_dir /tmp/igp24_strong_anti_s24_broad_diagnostic_20260706`.
    - Result: `loaded_records=9080`, `diagnosed_records=3071`,
      `selected_records=500`, `top_non_generic_score=2035.0`.
      Important flag counts include
      `square_discriminant_excludes_s24=36`,
      `very_near_square_discriminant=36`, `near_square_discriminant=2`,
      `exact_composed_support=186`, and `near_composed_support=500`.
    - Artifacts:
      `/tmp/igp24_strong_anti_s24_broad_diagnostic_20260706/non_generic_diagnostic.jsonl`
      and the matching shortlist/report files.
  - [done] Mine saved diagnostics for fresh strong anti-`S24` rows.
    - Command:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_strong_anti_s24_mine.py --diagnostic_jsonl /tmp/igp24_strong_anti_s24_broad_diagnostic_20260706/non_generic_diagnostic.jsonl --exclude_hash_jsonl /tmp/igp24_next_non_generic_structure_audit_20260706/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --known_verified_jsonl /tmp/igp24_pending_four_scoreability_review_20260706/scoreability_review.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --pair_status_json data/igp24/pair_status_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --target_r 4 --limit 40 --output_dir /tmp/igp24_strong_anti_s24_saved_mining_20260706`.
    - Result: `records_scanned=3071`, `strong_anti_s24_records=36`,
      `eligible_records=15`, `selected_records=15`.
      `filter_reason_counts={"exhausted_pool_hash": 160, "missing_strong_anti_s24_evidence": 2896, "survived_strong_anti_s24_mining_filters": 15}`.
      Selected strategy counts:
      `{"fixed_sparse_template": 3, "quartic_lift": 6, "sparse": 4, "structured": 2}`.
    - Artifacts:
      `/tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mined.jsonl`,
      `/tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_coefficients.txt`,
      `/tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_hashes.txt`,
      `/tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mining_summary.json`,
      and
      `/tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mining_report.md`.
  - [done] Run structure audit on the 15 mined rows.
    - Command:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py /tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mined.jsonl --priority_limit 15 --output_dir /tmp/igp24_strong_anti_s24_structure_audit_20260706`.
    - Result: `records_loaded=15`, `records_audited=15`,
      `square_claim_status_counts={"confirmed": 15}`,
      `exact_composed_claim_status_counts={"confirmed": 15}`,
      `priority_records=15`, `square_claim_refuted=0`,
      and `exact_composed_claim_refuted=0`.
    - Artifacts:
      `/tmp/igp24_strong_anti_s24_structure_audit_20260706/structure_audit.jsonl`,
      `/tmp/igp24_strong_anti_s24_structure_audit_20260706/manual_priority.jsonl`,
      `/tmp/igp24_strong_anti_s24_structure_audit_20260706/structure_summary.json`,
      and
      `/tmp/igp24_strong_anti_s24_structure_audit_20260706/structure_report.md`.
  - [done] Rerun the strict feedback-aware planner on the mined/audited rows.
    - Command:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_next_verification_queue.py --structure_audit_jsonl /tmp/igp24_strong_anti_s24_structure_audit_20260706/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --known_verified_jsonl /tmp/igp24_pending_four_scoreability_review_20260706/scoreability_review.jsonl --candidate_jsonl /tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mined.jsonl --pair_status_json data/igp24/pair_status_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --limit 12 --max_per_structural_family 1 --avoid_sair_negative_families --require_strong_anti_s24_evidence --output_dir /tmp/igp24_strong_anti_s24_strict_queue_20260706`.
    - Result: `annotated_records=15`, `eligible_records=3`,
      `selected_records=3`.
      `filter_reason_counts={"accepted_family_hint": 12, "survived_accepted_pending_baseline_generic_filters": 3}`.
      All 15 had `anti_s24_evidence_status_counts={"strong": 15}` and
      no SAIR negative-family match
      (`sair_feedback_family_status_counts={"None": 15}`).
    - Selected hashes:
      `33772dd90765a2726c35d5d653cd17725b50ffdac30bb4e7cf195068b94851da`,
      `72ed23a8d8bf5d9bd2401b0fb3b94b134794c1a5b51de7262daf2663bbdfad50`,
      and
      `33e431d55c37368ed565f364fb75690cad8e5e7d8dc2c83422a1db895e3a4b4d`.
    - Selected structural families:
      `square=True|divisor=4|base_degree=6|sparse=very_sparse|strategy=structured`,
      `square=True|divisor=2|base_degree=12|sparse=very_sparse|strategy=structured`,
      and
      `square=True|divisor=2|base_degree=12|sparse=sparse|strategy=sparse`.
    - Artifacts:
      `/tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_queue.jsonl`,
      `/tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_coefficients.txt`,
      `/tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_hashes.txt`,
      `/tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_queue_manifest.json`,
      and
      `/tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_queue_report.md`.
  - [done] Prepare a manual dry-run verification packet for the 3 survivors.
    - Command:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_queue.jsonl --output_dir /tmp/igp24_strong_anti_s24_manual_queue_20260706 --timeout_seconds 5 --online_magma_manual`.
    - Result: `loaded_review_records=3`, `input_kind=candidate_jsonl`,
      `pari_available=false`, `magma_available=false`,
      `pari_executed=false`, `magma_executed=false`, and
      `magma_status_counts={"dry_run": 3}`.
    - Artifacts:
      `/tmp/igp24_strong_anti_s24_manual_queue_20260706/verification_batch.jsonl`,
      `/tmp/igp24_strong_anti_s24_manual_queue_20260706/verification_coefficients.txt`,
      `/tmp/igp24_strong_anti_s24_manual_queue_20260706/verification_plan.md`,
      and
      `/tmp/igp24_strong_anti_s24_manual_queue_20260706/online_magma_manual`.
  - [done] Add a no-brackets manual coefficient file for possible hand use.
    - Artifact:
      `/tmp/igp24_strong_anti_s24_manual_queue_20260706/manual_coefficients_no_brackets.txt`.
    - Result: 3 lines, each with exactly 25 comma-separated integers, nonzero
      constant coefficient, and leading coefficient 1.
  - [done] Check for locally available scores for the 24-row accepted-label
    feedback batch.
    - Search scope: `data/igp24`, TODO/docs/notes, and `/tmp` score/SAIR
      artifacts.
    - Result: no new score artifact found; keep
      `data/igp24/sair_accepted_label_feedback_20260706_next_queue.json`
      score fields pending.
  - Current interpretation: saved-artifact mining was sufficient; no CPU
    generation and no GPU/model training were needed. The strict planner found
    3 credible fresh rows, all strong square-discriminant anti-`S24` and
    unmatched. Because fewer than 8 survived, do not pad the queue. Treat this
    as a small optional manual-verification queue rather than a full batch.
  - [done] Periodic implementation checkpoint:
    `5db2c92 Add strong anti-S24 saved mining pass`.
  - [done] Update `NOTES_IGP24.md` and `docs/EXPERIMENTS.md`; README unchanged
    because no public/basic workflow changed.
  - [done] Run final validation, confirm Stage 4 remains present, and audit
    process/GPU state.
    - Focused tests:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_strong_anti_s24_mine.py tests/test_igp24_next_verification_queue.py tests/test_igp24_queue_structure_audit.py`.
      - Result: 16 passed in 0.21s.
    - Full test suite:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
      - Result: 142 passed in 7.11s.
    - Full compile check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
      - Result: passed.
    - Helper help check:
      `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_strong_anti_s24_mine.py --help`.
      - Result: passed and shows diagnostic, feedback, baseline, target-r,
        limit, and output options.
    - JSON validation:
      `python3 -m json.tool /tmp/igp24_strong_anti_s24_saved_mining_20260706/strong_anti_s24_mining_summary.json`,
      `python3 -m json.tool /tmp/igp24_strong_anti_s24_structure_audit_20260706/structure_summary.json`,
      `python3 -m json.tool /tmp/igp24_strong_anti_s24_strict_queue_20260706/next_verification_queue_manifest.json`,
      and
      `python3 -m json.tool /tmp/igp24_strong_anti_s24_manual_queue_20260706/offline_verification_manifest.json`.
      - Result: all parsed successfully.
    - No-brackets coefficient validation:
      `/tmp/igp24_strong_anti_s24_manual_queue_20260706/manual_coefficients_no_brackets.txt`.
      - Result: 3 valid lines, 25 integers per line, no brackets, nonzero
        constant coefficient, leading coefficient 1.
    - Diff whitespace check:
      `git diff --check`.
      - Result: passed.
    - Stage 4 check:
      `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
      - Result: Stage 4 remains present at line 6293 after this TODO update.
    - Process audit:
      `ps -eo pid,ppid,stat,comm,args | awk '$4 ~ /^(python|python3|pytest|magma|gp)$/ {print}'`.
      - Result: no lingering Python, training, pytest, Magma, or GP worker
        processes.
    - GPU audit:
      `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
      - Result: no GPU compute apps reported.
- [done] Turn the 24-row SAIR acceptance feedback into stricter
  anti-generic queue planning.
  - Goal source:
    `/home/zpconn/.codex/attachments/e4042da5-4f78-4e81-91f9-039e8d7ec0c2/pasted-text-1.txt`.
  - Pull/latest check:
    `git pull --ff-only`.
    - Result: already up to date on `igp24-dev` at `d8843af`.
  - Current finding before edits: the old next-queue manifest had
    `eligible_records=24`, all with `feedback_family_match_status=unmatched`.
    SAIR later accepted those rows as 2 already accepted `24T24979|r=4`
    duplicates and 22 generic `24T25000|r=4`, so "unmatched" must become
    weaker evidence in the next planner pass.
  - Implementation in progress: add local-only SAIR feedback ingestion to
    `scripts/igp24_next_verification_queue.py`, mark generic-prone and
    accepted-duplicate feedback families, add explicit anti-`S24` evidence
    fields, and require stronger evidence for the next strict pass. No
    SAIR/API, Magma/PARI, GPU, training, CPU search, or submission path is
    being added.
  - Focused implementation check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_next_verification_queue.py`.
    - Result: 6 passed in 0.02s.
  - Strict saved-pool rerun:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_next_verification_queue.py --structure_audit_jsonl /tmp/igp24_next_non_generic_structure_audit_20260706/structure_audit.jsonl --verified_label_feedback_jsonl /tmp/igp24_verified_label_feedback_20260705/verified_label_feedback.jsonl --verified_label_feedback_jsonl /tmp/igp24_fresh_pair_verified_label_feedback_20260706/verified_label_feedback.jsonl --sair_label_feedback_json data/igp24/sair_accepted_label_feedback_20260706_next_queue.json --known_verified_jsonl /tmp/igp24_pending_four_scoreability_review_20260706/scoreability_review.jsonl --candidate_jsonl /tmp/igp24_next_non_generic_diagnostic_20260706/non_generic_shortlist.jsonl --pair_status_json data/igp24/pair_status_20260706.json --baseline_csv data/igp24/lmfdb_baseline.csv --limit 12 --max_per_structural_family 1 --avoid_sair_negative_families --require_strong_anti_s24_evidence --output_dir /tmp/igp24_sair_feedback_strict_queue_20260706`.
    - Result:
      `annotated_records=160`, `eligible_records=0`, `selected_records=0`,
      `filter_reason_counts={"known_exact_accepted_pair": 39, "sair_feedback_accepted_pair_duplicate_hash": 2, "sair_feedback_generic_hash": 22, "sair_generic_prone_family": 2, "weak_anti_s24_evidence": 95}`,
      `anti_s24_evidence_status_counts={"medium": 95, "strong": 41, "weak": 24}`,
      and
      `sair_feedback_family_status_counts={"None": 134, "accepted_duplicate_prone": 2, "generic_prone": 24}`.
    - Artifacts:
      `/tmp/igp24_sair_feedback_strict_queue_20260706/next_verification_queue_manifest.json`,
      `/tmp/igp24_sair_feedback_strict_queue_20260706/next_verification_queue_report.md`,
      and empty queue/coefficient files because no row survived.
  - Contrast rerun without `--require_strong_anti_s24_evidence`:
    `/tmp/igp24_sair_feedback_negative_only_queue_20260706`.
    - Result: still `eligible_records=0` and `selected_records=0`; the SAIR
      negative feedback plus existing accepted-pair ledger is already enough
      to exhaust this saved pool.
  - Interim interpretation: do not force an 8-12 row queue from this saved
    pool. The next bounded search should specifically target stronger
    anti-`S24` evidence, especially exact square discriminants or new verified
    non-generic families, before another manual submission queue.
  - Documentation updated:
    `NOTES_IGP24.md` and `docs/EXPERIMENTS.md`; README unchanged because no
    public/basic workflow changed.
  - Periodic implementation checkpoint:
    `fb3b968 Add feedback-aware queue planning filters`.
  - Final focused tests:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_next_verification_queue.py tests/test_igp24_score_aware_triage.py`.
    - Result: 12 passed in 0.04s.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 138 passed in 7.39s.
  - Full compile check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
    - Result: passed.
  - Helper help check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_next_verification_queue.py --help`.
    - Result: passed and shows `--sair_label_feedback_json`,
      `--avoid_sair_negative_families`, and
      `--require_strong_anti_s24_evidence`.
  - Strict manifest JSON validation:
    `python3 -m json.tool /tmp/igp24_sair_feedback_strict_queue_20260706/next_verification_queue_manifest.json`.
    - Result: parsed successfully.
  - Diff whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 6120 after this TODO update.
  - Process audit:
    `ps -eo pid,ppid,stat,comm,args | rg 'python|train.py|igp24|pytest|magma|gp'`.
    - Result: no lingering Python, training, pytest, Magma, or GP worker
      processes beyond the audit command itself.
  - GPU audit:
    `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
    - Result: no GPU compute apps reported.
- [done] Run final 24-row score-aware triage validation.
  - Focused tests:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_score_aware_triage.py tests/test_igp24_next_verification_queue.py`.
    - Result: 9 passed in 0.03s.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 135 passed in 7.55s.
  - Full compile check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
    - Result: passed.
  - Helper help checks:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_aware_triage.py --help`
    and
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`.
    - Result: both passed.
  - Diff whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 5980 after this TODO update.
  - Process audit:
    `ps -eo pid,ppid,stat,comm,args | rg 'python|train.py|igp24|pytest|magma|gp'`.
    - Result: no lingering Python, training, pytest, Magma, or GP worker
      processes beyond the audit command itself.
  - GPU audit:
    `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
    - Result: no GPU compute apps reported.
  - Cache cleanup:
    `find . -type d -name __pycache__ -prune -exec rm -rf {} +`,
    followed by `find . -type d -name __pycache__ -print`.
    - Result: no `__pycache__` directories remain.
- [done] Validate SAIR accepted-label feedback import for the 24-row queue.
  - Focused tests:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_score_aware_triage.py tests/test_igp24_next_verification_queue.py`.
    - Result: 10 passed in 0.03s.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 136 passed in 7.48s.
  - Full compile check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
    - Result: passed.
  - Helper help check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_aware_triage.py --help`.
    - Result: passed and shows repeatable `--sair_label_feedback_json`.
  - JSON validation:
    `python3 -m json.tool data/igp24/sair_accepted_label_feedback_20260706_next_queue.json`
    and
    `python3 -m json.tool data/igp24/pair_status_20260706.json`.
    - Result: both parsed successfully.
  - Diff whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 6043 after this TODO update.
  - Process audit:
    `ps -eo pid,ppid,stat,comm,args | rg 'python|train.py|igp24|pytest|magma|gp'`.
    - Result: no lingering Python, training, pytest, Magma, or GP worker
      processes beyond the audit command itself.
  - GPU audit:
    `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
    - Result: no GPU compute apps reported.
- [done] Run final next-queue planning validation.
  - Focused test:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_next_verification_queue.py`.
    - Result: 4 passed in 0.01s.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 130 passed in 7.21s.
  - Full compile check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
    - Result: passed.
  - Helper help checks:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_next_verification_queue.py --help`
    and
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`.
    - Result: both passed.
  - Diff whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "^### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`.
    - Result: Stage 4 remains present at line 5882 after this TODO update.
  - Process audit:
    `ps -eo pid,ppid,stat,comm,args | rg 'python|train.py|igp24|pytest|magma|gp'`.
    - Result: no lingering Python, training, pytest, Magma, or GP worker
      processes beyond the audit command itself.
  - GPU audit:
    `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
    - Result: no GPU compute apps reported.
  - Cache cleanup:
    `find . -type d -name __pycache__ -prune -exec rm -rf {} +`,
    followed by `find . -type d -name __pycache__ -print`.
    - Result: no `__pycache__` directories remain.
- [done] Run final pending-four scoreability validation.
  - Focused test:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_scoreability_review.py`.
    - Result: 2 passed in 0.03s.
  - Full test suite:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
    - Result: 126 passed in 7.58s.
  - Full compile check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
    - Result: passed.
  - Helper help check:
    `env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_scoreability_review.py --help`.
    - Result: passed.
  - Diff whitespace check:
    `git diff --check`.
    - Result: passed.
  - Stage 4 check:
    `rg -n "Stage 4|stage 4|Stage-4|stage-4" TODO_IGP24.md`.
    - Result: Stage 4 remains present; main heading is still present.
  - Process audit:
    `ps -eo pid,ppid,stat,comm,args | rg 'python|train.py|igp24|pytest|magma|gp'`.
    - Result: no lingering Python, training, pytest, Magma, or GP worker
      processes beyond the audit command itself.
  - GPU audit:
    `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
    - Result: no GPU compute apps reported.
  - Cache cleanup:
    `find . -type d -name __pycache__ -prune -exec rm -rf {} +`,
    followed by `find . -type d -name __pycache__ -print`.
    - Result: no `__pycache__` directories remain.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
  - Latest result: 115 passed in 3.87s after fresh online-verification
    documentation and XML provenance work.
- [done] Run focused non-generic diagnostic/review/shortlist tests:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_non_generic_diagnostic.py tests/test_igp24_shortlist.py tests/test_igp24_review_shortlist.py`.
  - Latest result: 11 passed in 0.05s after non-generic diagnostic work.
- [done] Run focused offline verifier tests:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`.
  - Latest result: 13 passed in 1.31s after non-generic manual-queue
    ergonomics work.
- [done] Run focused local structure-audit tests:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_queue_structure_audit.py`.
  - Latest result: 6 passed in 0.21s after queue structure-audit work.
- [done] Run focused split/export/triage tests:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_seed_triage.py tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_export_diversity_diagnostic.py`.
  - Latest result: 43 passed in 1.14s after seed triage calibration.
- [done] Run focused offline verifier/review/shortlist tests:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py tests/test_igp24_review_shortlist.py tests/test_igp24_shortlist.py tests/test_igp24_merge_scored_exports.py tests/test_igp24_sample_export.py`.
  - Latest result: 19 passed in 1.28s for the focused offline/review/shortlist
    queue subset after verification-queue work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
  - Latest result: passed after fresh online-verification documentation work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`.
  - Latest result: passed after verification-queue work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`.
  - Latest result: passed after verification-queue work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`.
  - Latest result: passed after fresh online-verification final validation; helper exposes
    `--candidate_hash`, `--online_magma_manual`, and
    `--online_magma_pasted_output`.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_non_generic_diagnostic.py --help`.
  - Latest result: passed after queue structure-audit final validation.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_queue_structure_audit.py --help`.
  - Latest result: passed after queue structure-audit work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_verified_label_feedback.py --help`.
  - Latest result: passed after fresh online-verification final validation.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_exact_label_shortlist.py --help`.
  - Latest result: passed after exact-label shortlist planning work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`.
  - Latest result: passed after short GPU sampler probe work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --help`.
  - Latest result: passed after GPU readiness smoke work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`.
  - Latest result: passed after opt-in dedup-aware export control work;
    helper exposes `sample_export_split_dedup`, `--dedup_unique_target`,
    `--dedup_max_attempts`, and `--dedup_progress_interval`.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`.
  - Latest result: passed after opt-in dedup-aware export control work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py --help`.
  - Latest result: passed after opt-in dedup-aware export control work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py --help`.
  - Latest result: passed after opt-in dedup-aware export control work.
- [done] Run an import check proving `train`, the environment registry,
  `igp24`, and the split/merge helpers remain discoverable.
  - Latest command:
    `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_score_sample_export as score; import scripts.igp24_gpu_sampler_probe as probe; import scripts.igp24_merge_scored_exports as merge; import scripts.igp24_export_diversity_diagnostic as diag; print('imports ok', 'igp24' in ENVS, hasattr(score, 'build_split_manifest'), hasattr(probe, 'build_sample_export_dedup_command'), 'sample_export_split_dedup' in probe.get_parser().format_help(), hasattr(merge, 'merge_sources'), hasattr(diag, 'build_summary'))"`
  - Latest result: `imports ok True True True True True True`.
- [done] Run an import check proving the offline verifier manual-online
  helpers remain discoverable.
  - Latest command:
    `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_offline_verify as offline; from src.igp24.verifiers.magma import MagmaVerifier; print('imports ok', 'igp24' in ENVS, hasattr(offline, 'build_online_magma_manual_input'), hasattr(offline, 'parse_online_magma_pasted_output'), hasattr(offline, 'write_online_magma_manual_artifacts'), hasattr(MagmaVerifier(), 'is_available'))"`
  - Latest result: `imports ok True True True True True`.
- [blocked] Run literal `python -m pytest`, or record the blocker.
  - Latest result: blocked with `/bin/bash: line 1: python: command not found`.
- [done] If local dependency issues block the literal command, record the
  exact blocker and run the closest available equivalent.

## Command Log

- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before multi-seed
    `fixed_template_t11_open_topk` stability validation.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before per-run GPU export diversity
    diagnostic work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before multi-seed fixed-template GPU export
    scale-up work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before short controlled GPU sampler probe work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before train-only GPU utilization diagnosis
    work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before GPU sample-export decoupling work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before split workflow hardening work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before score-all split handoff validation.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before medium export-only split workflow work.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before GPU export diversity work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 25 passed in 1.27s after adding bounded medium export-only mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed; helper now exposes
    `--probe_mode {sampler,train_only_utilization,sample_export_split,sample_export_split_medium}`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after adding the medium export-only mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_medium --output_dir /tmp/igp24_gpu_sample_export_split_medium_20260704 --timeout_seconds 3600 --monitor_interval_seconds 5`
  - Result: interrupted intentionally with return code 130 after 153.119s
    because the first medium caps were CPU-seed-bound; no eval/export records
    were produced, and the mode was retuned to use the proven small initial
    CPU seed scale before rerunning.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 25 passed in 1.12s after retuning medium initial CPU seed caps.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after retuning medium initial CPU seed caps.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_medium --output_dir /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704 --timeout_seconds 3600 --monitor_interval_seconds 5`
  - Result: completed in 1300.803s with return code 0, no timeout,
    `device: cuda`, 20 finite eval points, max monitored GPU utilization
    99.0%, average monitored GPU utilization 95.977%, max monitored GPU
    memory 10141 MiB, and 8192 decoded unscored export rows. GPU-side CPU
    scoring/local search/dataset update was avoided.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/gpu_model_sample_export_medium.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
  - Result: completed in 264.635s with return code 0,
    `selection_mode=all_explicit`, 8192 rows read/selected, 8192
    decoded/scored, 8188 valid, 4 rejected, 384 unique canonical hashes,
    7808 duplicate hash records, local search disabled, and split
    manifest/report written under
    `/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 27 passed in 2.29s after adding the diversity export helper mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed; helper now exposes
    `--probe_mode ... sample_export_split_diversity` and
    `--diversity_variant {fixed_template_t09_top9,mixed_t12_open_topk}`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after adding the diversity export helper mode.
- 2026-07-04: `git diff --check`
  - Result: passed after adding the diversity export helper mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant fixed_template_t09_top9 --output_dir /tmp/igp24_gpu_sample_export_diversity_fixed_20260704 --timeout_seconds 900 --monitor_interval_seconds 2`
  - Result: completed in 148.684s with return code 0, no timeout,
    `device: cuda`, 4 finite eval points, max monitored GPU utilization
    99.0%, average monitored GPU utilization 80.808%, max monitored GPU
    memory about 10310 MiB, 2048 export rows, 2047 decoded rows, and
    GPU-side CPU scoring/local search/dataset update avoided.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split_diversity --diversity_variant mixed_t12_open_topk --output_dir /tmp/igp24_gpu_sample_export_diversity_mixed_20260704 --timeout_seconds 900 --monitor_interval_seconds 2`
  - Result: completed in 152.369s with return code 0, no timeout,
    `device: cuda`, 4 finite eval points, max monitored GPU utilization
    99.0%, average monitored GPU utilization 80.135%, max monitored GPU
    memory about 10310 MiB, 2048 export rows, 2030 decoded rows, and
    GPU-side CPU scoring/local search/dataset update avoided.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/gpu_model_sample_export_diversity_fixed_template_t09_top9.jsonl --output_dir /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
  - Result: completed in 76.537s with return code 0,
    `selection_mode=all_explicit`, 2048 rows read/selected, 2047
    decoded/scored, 1 skipped decode, 1799 valid, 248 rejected, 2039 unique
    canonical hashes, 8 duplicate hash records, best score 9964.435, mean
    score 8720.207, local search disabled, and split manifest/report written
    under
    `/tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/gpu_model_sample_export_diversity_mixed_t12_open_topk.jsonl --output_dir /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
  - Result: completed in 77.709s with return code 0,
    `selection_mode=all_explicit`, 2048 rows read/selected, 2030
    decoded/scored, 18 skipped decode, 1921 valid, 109 rejected, 1067 unique
    canonical hashes, 963 duplicate hash records, best score 9969.676, mean
    score 9396.872, local search disabled, and split manifest/report written
    under
    `/tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 27 passed in 1.10s after the GPU diversity sweep work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 68 passed in 1.57s after the GPU diversity sweep work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after the GPU diversity sweep work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after the GPU diversity sweep work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed after the GPU diversity sweep work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_score_sample_export as score; import scripts.igp24_gpu_sampler_probe as probe; print('imports ok', 'igp24' in ENVS, hasattr(score, 'build_split_manifest'), hasattr(probe, 'build_sample_export_diversity_command'))"`
  - Result: `imports ok True True True`.
- 2026-07-04: `git diff --check`
  - Result: passed after the GPU diversity sweep work.
- 2026-07-04:
  `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
  - Result: Stage 4 remains present at line 2519.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 visible and idle after the GPU diversity sweep work.
- 2026-07-04: `ps -C python3 -o pid=,etime=,pcpu=,pmem=,args=`
  - Result: no active `python3` processes after final checks.
- 2026-07-04: `find . -type d -name __pycache__`
  - Result: no generated `__pycache__` directories remained after cleanup.
- 2026-07-04: `python -m pytest`
  - Result: still blocked with `/bin/bash: line 1: python: command not found`;
    `python3 -m pytest -q` is the passing local equivalent.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 25 passed in 1.08s after the medium split final checks.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 66 passed in 1.44s after the medium split final checks.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after the medium split final checks.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after the medium split final checks.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed after the medium split final checks.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_score_sample_export as score; import scripts.igp24_gpu_sampler_probe as probe; print('imports ok', 'igp24' in ENVS, hasattr(score, 'build_split_manifest'), hasattr(probe, 'build_sample_export_split_medium_command'))"`
  - Result: `imports ok True True True`.
- 2026-07-04: `git diff --check`
  - Result: passed after the medium split final checks.
- 2026-07-04:
  `rg -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
  - Result: Stage 4 remains present at line 2353.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 visible and idle after the medium split final checks.
- 2026-07-04: `ps -C python3 -o pid=,etime=,pcpu=,pmem=,args=`
  - Result: no active `python3` processes after the medium split final checks.
- 2026-07-04: `find . -type d -name __pycache__`
  - Result: no generated `__pycache__` directories remained after cleanup.
- 2026-07-04: `python -m pytest`
  - Result: still blocked with `/bin/bash: line 1: python: command not found`;
    `python3 -m pytest -q` is the passing local equivalent.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 23 passed in 2.42s after adding score-all manifest regression
    coverage.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split --output_dir /tmp/igp24_gpu_sample_export_split_score_all_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
  - Result: return code 0 in 32.273s, no timeout/interruption, logged
    `device: cuda`, max monitored GPU utilization 94.0%, average monitored GPU
    utilization 14.516%, max monitored GPU memory 5320 MiB, 1024 export rows,
    1023 decoded export rows, and GPU-side CPU scoring/local search avoided.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_model_sample_export.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all --score_all true --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
  - Result: return code 0 in 36.724s, `selection_mode=all_explicit`, 1024
    rows read/selected, 1023 decoded/scored, 1 skipped decode, 908 valid,
    115 rejected, 1022 unique canonical hashes, 1 duplicate hash record,
    local search disabled, and split manifest/report written under
    `/tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 23 passed in 1.08s after score-all split handoff validation.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 64 passed in 1.49s after score-all split handoff validation.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after score-all split handoff validation.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after score-all split handoff validation.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed after score-all split handoff validation.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_score_sample_export as score; import scripts.igp24_gpu_sampler_probe as probe; print('imports ok', 'igp24' in ENVS, hasattr(score, 'build_split_manifest'), hasattr(probe, 'build_sample_export_split_command'))"`
  - Result: `imports ok True True True`.
- 2026-07-04: `git diff --check`
  - Result: passed after score-all split handoff validation.
- 2026-07-04:
  `grep -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
  - Result: Stage 4 remains present at line 2210.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 visible; no running GPU processes listed after the
    score-all split handoff.
- 2026-07-04: `ps -C python3 -o pid=,etime=,pcpu=,pmem=,args=`
  - Result: no active `python3` processes after final checks.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 22 passed in 1.15s after adding split manifest/report,
    dedup/hash summaries, explicit `--score_all`, false-boolean parser
    regression coverage, and the 1024-row split probe command.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed; helper now exposes `--score_all` and
    `--gpu_probe_summary`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after increasing the `sample_export_split` helper command
    to a 1024-row export target.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_score_sample_export.py scripts/igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after split workflow hardening changes.
- 2026-07-04: `git diff --check`
  - Result: passed after split workflow hardening changes.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split --output_dir /tmp/igp24_gpu_sample_export_split_larger_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
  - Result: return code 0 in 32.079s, no timeout/interruption, logged
    `device: cuda`, max monitored GPU utilization 93.0%, average monitored GPU
    utilization 17.516%, max monitored GPU memory 5457 MiB, 1024 export rows,
    1024 decoded export rows, and GPU-side CPU scoring/local search avoided.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_larger_20260704/gpu_model_sample_export.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export --max_records 512 --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
  - Result: return code 0 in 19.719s, 1024 rows read, 512 selected/scored,
    450 valid, 62 rejected, 512 unique canonical hashes, 0 duplicate hash
    records, local search disabled, and split manifest/report written under
    `/tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 63 passed in 1.56s after split workflow hardening.
- 2026-07-04: `python -m pytest -q`
  - Result: blocked with `/bin/bash: line 1: python: command not found`; use
    the recorded `python3` command on this shell.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after split workflow hardening.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after split workflow hardening.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed after split workflow hardening.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_score_sample_export as score; import scripts.igp24_gpu_sampler_probe as probe; print('imports ok', 'igp24' in ENVS, hasattr(score, 'build_split_manifest'), hasattr(probe, 'build_sample_export_split_command'))"`
  - Result: `imports ok True True True`.
- 2026-07-04: `git diff --check`
  - Result: passed after split workflow hardening.
- 2026-07-04:
  `grep -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
  - Result: Stage 4 remains present at line 2115.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 visible; no running GPU processes listed after the larger
    split smoke.
- 2026-07-04: `ps -C python3 -o pid=,etime=,pcpu=,pmem=,args=`
  - Result: no active `python3` processes after final checks.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: 18 passed in 1.36s after adding export-only model sampling,
    sample-export scoring helper, and split-probe command construction.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed; helper now exposes
    `--probe_mode {sampler,train_only_utilization,sample_export_split}`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed; helper documents sample-export input, output directory,
    record cap, proxy-scoring options, and explicit local-search flag.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src/evaluator.py scripts/igp24_gpu_sampler_probe.py scripts/igp24_score_sample_export.py tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py`
  - Result: passed after adding the split GPU sample-export workflow.
- 2026-07-04: `git diff --check`
  - Result: passed after adding the split GPU sample-export workflow.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode sample_export_split --output_dir /tmp/igp24_gpu_sample_export_split_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
  - Result: passed outside the managed sandbox in 16.8s with return code 0,
    no timeout, no interruption, `device: cuda`, two finite eval points, max
    monitored GPU utilization 91.0%, average monitored GPU utilization
    11.125%, max monitored GPU memory 4887 MiB, final train/test loss about
    `0.909` / `0.729`, 256 unscored sample-export rows, 256 decoded
    coefficient vectors, and no post-training CPU scoring/local search.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py /tmp/igp24_gpu_sample_export_split_20260704/gpu_model_sample_export.jsonl --output_dir /tmp/igp24_gpu_sample_export_split_20260704/cpu_scored_export --max_records 64 --coeff_bound 4 --prime_limit 11 --exact_score_timeout 2 --local_search false --max_local_search_steps 0`
  - Result: passed; read 256 exported rows, selected 64, decoded 64 inputs,
    scored 64 through the CPU proxy scorer, found 56 valid and 8 rejected
    records, and kept local search disabled.
- 2026-07-04: audited
  `/tmp/igp24_gpu_sample_export_split_20260704/gpu_sampler_probe_summary.json`
  and `/tmp/igp24_gpu_sample_export_split_20260704/cpu_scored_export/score_summary.json`.
  - Result: export rows include raw `token_ids`, 24 decoded coefficients,
    appended leading coefficient exports, `score=null`, `scoring_status=unscored`,
    `local_search_status=not_run`, `verification_status=not_run`, and safety
    flags for no exact verifiers, no SAIR/network calls, and no submission.
    Scored rows record `source_export_path`, `source_sample_index`,
    proxy-scored verification status, local search disabled, and the same
    no-network/no-submission safety boundary.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py`
  - Result: 10 passed in 0.03s after adding the train-only utilization probe
    mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed; helper now exposes
    `--probe_mode {sampler,train_only_utilization}`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after adding `--train_only` and train-only probe mode.
- 2026-07-04: `git diff --check`
  - Result: passed after adding the train-only utilization probe mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --probe_mode train_only_utilization --output_dir /tmp/igp24_gpu_train_only_probe_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
  - Result: passed outside the managed sandbox in 34.1s with return code 0,
    no timeout, no interruption, `device: cuda`, four finite eval points, max
    monitored GPU utilization 95.0%, average monitored GPU utilization
    20.67%, max monitored GPU memory 5814 MiB, final train/test loss about
    `0.698` / `0.724`, and post-training sampling/scoring/local search
    skipped.
- 2026-07-04: audited
  `/tmp/igp24_gpu_train_only_probe_20260704/gpu_sampler_probe_summary.json`.
  - Result: 33 parsed utilization samples, PyTorch `2.12.1+cu130`, CUDA
    available on `NVIDIA GeForce RTX 5090`, max PyTorch CUDA allocated
    97.17 MiB, max PyTorch CUDA reserved 110.0 MiB, `sample_requested_total=0`,
    `sample_valid_total=0`, `model_sample_ledger_records=0`, 451 initial
    ledger records, metadata complete, and recommendation
    `decouple_gpu_training_from_cpu_scoring`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 59 passed in 1.57s after GPU sample-export split work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after GPU sample-export split work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after adding `sample_export_split` probe mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`
  - Result: passed after adding the CPU sample-export scoring helper.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git diff --check`
  - Result: passed after GPU sample-export split work.
- 2026-07-04:
  `grep -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
  - Result: Stage 4 remained present at line 1991.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 still visible; no running compute processes listed after
    the sample-export split smoke.
- 2026-07-04: `ps -C python3 -o pid=,etime=,pcpu=,pmem=,args=`
  - Result: no active `python3` processes were listed after the sample-export
    split smoke.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: removed generated bytecode caches after final verification.
- 2026-07-04: `find . -type d -name __pycache__ -print`
  - Result after cleanup: no output; generated bytecode caches cleaned.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 51 passed in 0.77s after train-only GPU utilization probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after train-only GPU utilization probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after train-only GPU utilization probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git diff --check`
  - Result: passed after final docs/results updates.
- 2026-07-04:
  `grep -n "### Stage 4: Competition Packaging And Reproducibility" TODO_IGP24.md`
  - Result: Stage 4 remained present at line 1852.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 still visible; no running compute processes listed after
    the train-only probe.
- 2026-07-04: `ps -C python3 -o pid=,etime=,pcpu=,pmem=,args=`
  - Result: no active `python3` processes were listed after the train-only
    probe.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: removed generated bytecode caches after final verification.
- 2026-07-04: `find . -type d -name __pycache__ -print`
  - Result after cleanup: no output; generated bytecode caches cleaned.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 48 passed in 0.77s after short GPU sampler probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after short GPU sampler probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after short GPU sampler probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed after short GPU sampler probe work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -print`
  - Result before cleanup: generated bytecode caches existed after
    verification commands.
- 2026-07-04: `find . -type d -name __pycache__ -exec rm -rf {} +`
  - Result: removed generated bytecode caches.
- 2026-07-04: `find . -type d -name __pycache__ -print`
  - Result after cleanup: no output; generated bytecode caches cleaned.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py`
  - Result: 6 passed in 0.02s after adding the short GPU sampler probe helper.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed; helper exposes output directory, repo root, Python
    executable, timeout, run id, baseline summary, and strict mode.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after adding the short GPU sampler probe helper.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --output_dir /tmp/igp24_gpu_sampler_probe_20260704 --timeout_seconds 600`
  - Result: passed outside the managed sandbox in about 183-185 seconds. The
    completed runs logged `device: cuda`, two epochs, eight finite eval points,
    max CUDA reserved memory 76 MiB, final train/test loss around `0.618` /
    `1.382`, 910 valid sampled candidates out of 1024 requested, 1728 ledger
    rows, 1615 `manual` model-sampled rows, and complete metadata.
  - Interpretation update: this proves the training/sampling path can produce
    valid proxy candidates, but it does not prove meaningful GPU utilization.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --output_dir /tmp/igp24_gpu_sampler_probe_20260704 --timeout_seconds 600 --monitor_interval_seconds 1`
  - Result: interrupted intentionally after live observation showed the GPU
    sitting near zero utilization. The wrapper was stopped with Ctrl-C; the
    summary file only contains probe data because interruption happened before
    the run summary was written.
  - Follow-up check: `nvidia-smi` showed no active compute processes after the
    interruption. A partial run log still showed `device: cuda`, two epochs,
    eight finite eval points, and valid samples, but no complete utilization
    report was written.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py`
  - Result: 7 passed in 0.01s after adding utilization parsing and interrupt
    cleanup.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_sampler_probe.py tests/test_igp24_gpu_sampler_probe.py`
  - Result: passed after adding utilization parsing and interrupt cleanup.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`
  - Result: passed; helper now exposes `--monitor_interval_seconds`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before GPU-readiness and training-smoke work.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 41 passed in 0.77s after GPU readiness smoke work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after GPU readiness smoke work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after GPU readiness smoke work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --help`
  - Result: passed after GPU readiness smoke work.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -print`
  - Result before cleanup: generated bytecode caches existed under repo
    package, script, test, and root directories after verification commands.
- 2026-07-04: `find . -type d -name __pycache__ -exec rm -rf {} +`
  - Result: removed generated bytecode caches.
- 2026-07-04: `find . -type d -name __pycache__ -print`
  - Result after cleanup: no output; generated bytecode caches cleaned.
- 2026-07-04: `nvidia-smi`
  - Result: RTX 5090 visible, driver 596.49, CUDA 13.2, 32607 MiB total GPU
    memory. No active compute process was listed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"`
  - Result outside the managed sandbox:
    `2.12.1+cu130 True NVIDIA GeForce RTX 5090`.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --output_dir /tmp/igp24_gpu_smoke_20260704 --timeout_seconds 180`
  - Result inside the managed sandbox: diagnostic report was written, but
    `nvidia-smi` returned 255 and PyTorch reported CUDA unavailable because GPU
    access was blocked by the operating system. Reran outside the managed
    sandbox for authoritative CUDA/NVML results.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --output_dir /tmp/igp24_gpu_smoke_20260704 --timeout_seconds 180`
  - Result outside the managed sandbox: passed; report written to
    `/tmp/igp24_gpu_smoke_20260704/gpu_smoke_report.md`.
  - Probe result: `nvidia-smi` return code 0, RTX 5090, 32607 MiB, driver
    596.49; PyTorch `2.12.1+cu130`, CUDA available, CUDA tensor smoke true.
  - CPU baseline: return code 0, 2.39s, 7 valid examples, 12 ledger rows,
    metadata complete, logged `device: cpu`.
  - GPU train: return code 0, 3.88s, 4 valid examples after one tiny training
    epoch, 12 ledger rows, metadata complete, logged `device: cuda`, logged
    CUDA memory, `gpu_used=True`.
  - Recommendation: run CPU proxy-search and GPU training in parallel; do not
    replace the CPU proxy/exact-tool-prep pipeline from this tiny smoke.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_smoke.py`
  - Result: 6 passed in 0.01s after fixing train-log device parsing for
    prefixed logger lines.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_smoke.py tests/test_igp24_gpu_smoke.py`
  - Result: passed after fixing train-log device parsing.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_smoke.py`
  - Result: 6 passed in 0.02s after adding the GPU readiness helper.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --help`
  - Result: passed; helper exposes output directory, repo root, timeout,
    fixed run id, forced GPU train, and strict-mode options.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_gpu_smoke.py tests/test_igp24_gpu_smoke.py`
  - Result: passed after adding the GPU readiness helper and tests.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before fixed-support sparse template generation
    work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 24 passed in 1.16s after adding `fixed_sparse_template`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src/envs/igp24.py scripts/igp24_benchmark.py tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: passed after adding `fixed_sparse_template`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper documents `fixed_sparse_template` as a direct
    benchmark strategy alongside `quartic_lift`.
- 2026-07-04:
  `/usr/bin/time -f elapsed_seconds %e env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,fixed_sparse_template --seeds 1101,1102,1103,1104 --target_rs 2 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_fixed_sparse_template_bench_20260704`
  - Result: command-format blocker; `/usr/bin/time` received `%e` as the
    command because the format string was not quoted. Reran with portable
    `time -p`.
- 2026-07-04:
  `/usr/bin/time -p env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,fixed_sparse_template --seeds 1101,1102,1103,1104 --target_rs 2 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_fixed_sparse_template_bench_20260704`
  - Result: passed; 12 CPU-only `target_r=2` benchmark runs completed in
    `real 50.42` seconds.
- 2026-07-04: audited
  `/tmp/igp24_fixed_sparse_template_bench_20260704/summary.json`.
  - Result: 12 rows, all return codes 0, all metadata complete, strategies
    were `fixed_sparse_template`, `sparse`, and `structured`, target set was
    `[2]`, valid candidates totaled 216, ledger records totaled 391, and
    target-r matching records totaled 258.
- 2026-07-04: audited fixed-template benchmark ledger metadata.
  - Result: 130 `fixed_sparse_template` ledger rows checked; no missing
    template/support/bound metadata. Template counts were `low_high_bridge`: 48,
    `divisor_ladder_3`: 39, `r2_tail_bridge`: 23, and `r2_even_spine`: 20.
    Local search introduced 100 extra nonzero outside-template indices across
    those rows, recorded under `fixed_sparse_extra_nonzero_indices`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 35 passed in 0.74s after fixed-sparse-template work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before safe offline-verifier preparation
    workflow work.
- 2026-07-04: `python3 -c "import shutil; print('gp', shutil.which('gp')); print('magma', shutil.which('magma'))"`
  - Result: `gp None`; `magma None`. Local exact verifier binaries are not on
    PATH at setup time, so the first smoke should remain dry-run/preparation
    only and record the blocker.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_offline_verify.py`
  - Result: 5 passed in 0.03s after adding the offline-verifier preparation
    helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_offline_verify.py tests/test_igp24_offline_verify.py`
  - Result: passed after adding the offline-verifier preparation helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
  - Result: passed; CLI documents review-batch input, output directory,
    explicit `--run_pari`/`--run_magma` opt-ins, executable names, timeout, and
    repo-root options.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py /tmp/igp24_r4_review_batch_20260704 --output_dir /tmp/igp24_r4_offline_verify_20260704`
  - Result: passed in default preparation-only mode. Loaded 8 review records,
    wrote `offline_verification_manifest.json`, `pari_input.gp`,
    `magma_input.m`, and `verification_plan.md`. Local `gp` and `magma`
    availability were both false; no local verifier execution was requested or
    performed.
- 2026-07-04: audited `/tmp/igp24_r4_offline_verify_20260704`.
  - Result: selected record count is 8, selected hashes are unique, coefficient
    shape is recorded as length 25 with leading coefficient 1, PARI/GP and
    MAGMA are unavailable on PATH, `pari_executed=false`,
    `magma_executed=false`, `dry_run_preparation_only=true`, and safety flags
    record no network calls, no SAIR submission, no auto-submission, no exact
    group-label parsing, and no exact group claims. No `*raw_output*` files
    were created.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 33 passed in 0.95s after safe offline-verifier preparation helper
    work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before safe review-batch tooling work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_review_shortlist.py`
  - Result: 3 passed in 0.01s after adding the review-batch helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_review_shortlist.py tests/test_igp24_review_shortlist.py`
  - Result: passed after adding the review-batch helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`
  - Result: initially exposed a direct-execution import-path blocker
    (`ModuleNotFoundError: No module named 'scripts'`). Fixed the helper's
    repo-root path setup and reran successfully; CLI documents shortlist input,
    output directory, batch size, sort key, strategy cap/minimum, source-ledger
    following, and repo-root options.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py /tmp/igp24_r4_shortlist_20260704 --batch_size 8 --min_strategies 2 --per_strategy_cap 6 --output_dir /tmp/igp24_r4_review_batch_20260704`
  - Result: passed; loaded 25 shortlist records and selected 8 review records.
    Top score was 10214.147570701043. Strategy counts were `quartic_lift`: 6
    and `four_real_seed`: 2.
- 2026-07-04: audited `/tmp/igp24_r4_review_batch_20260704`.
  - Result: `review_report.md`, `verification_batch.jsonl`,
    `verification_coefficients.txt`, and `manifest.json` exist. The batch has
    8 rows, 8 unique canonical hashes, all exported coefficient vectors have
    length 25 and end in fixed leading coefficient 1, every row records source
    ledger and source shortlist paths, `verified_group_label` is null for every
    row, and manifest safety flags record proxy-only/review-export-only with no
    verifier execution, submission, network calls, or exact group claims.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 28 passed in 0.92s after safe review-batch helper work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before safe shortlist/export helper work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_shortlist.py`
  - Result: 3 passed in 0.01s after adding the shortlist/export helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts/igp24_shortlist.py tests/test_igp24_shortlist.py`
  - Result: passed after adding the shortlist/export helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`
  - Result: passed; helper documents input paths, output directory,
    target-r filtering, strategy filtering, top-N limit, sort key, and
    ascending sort option.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py /tmp/igp24_r4_second_confirm_20260704 /tmp/igp24_r4_dual_quality_confirm_20260704 --target_r 4 --limit 25 --output_dir /tmp/igp24_r4_shortlist_20260704`
  - Result: passed; loaded 4,870 source records and selected 25 deduplicated
    `target_r=4` proxy candidates. Top score was 10214.147570701043.
    Strategy counts were `quartic_lift`: 23 and `four_real_seed`: 2.
- 2026-07-04: audited `/tmp/igp24_r4_shortlist_20260704`.
  - Result: `shortlist.jsonl`, `coefficients.json`, `coefficients.txt`, and
    `manifest.json` exist. The shortlist has 25 rows, 25 unique canonical
    hashes, all real-root counts are 4, all exported coefficient vectors have
    length 25 and end in fixed leading coefficient 1, all rows include source
    ledger paths, scores are sorted descending, and manifest safety flags show
    proxy-only/export-only with no verifier execution or submission.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 25 passed in 1.03s after safe shortlist/export helper work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before second r4 preset confirmation work.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies preset_r4,quartic_lift,mix_r4_dual_yield,mix_r4_dual_quality,four_real_seed,mix_r4_dual_balanced --seeds 1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_second_confirm_20260704`
  - Result: passed; 96 CPU-only `target_r=4` confirmation runs completed in
    397.34 seconds wall-clock.
- 2026-07-04: audited
  `/tmp/igp24_r4_second_confirm_20260704/summary.json`.
  - Result:
    `96 True True ['four_real_seed', 'mix_r4_dual_balanced', 'mix_r4_dual_quality', 'mix_r4_dual_yield', 'preset_r4', 'quartic_lift'] [4]`
    and `1715 2821 1887`.
- 2026-07-04: audited
  `/tmp/igp24_r4_second_confirm_20260704/aggregate_summary.json`.
  - Result: 6 aggregate rows; required aggregate fields for match rate,
    average best, average mean, best score, and local-search acceptance were
    present.
- 2026-07-04: inspected all second-confirmation dual-mix ledgers for mix
  metadata.
  - Result: 1,403 dual-label ledger records checked, no mixed-weight metadata
    mismatches. Observed strategy mix was `dual_yield`: 372
    `four_real_seed`, 104 `quartic_lift`; `dual_quality`: 325
    `quartic_lift`, 132 `four_real_seed`; `dual_balanced`: 228
    `four_real_seed`, 202 `quartic_lift`, 40 `sparse`.
- 2026-07-04: combined the prior 12-seed confirmation with the fresh 16-seed
  block for a 28-seed comparison.
  - Result: `four_real_seed` had the highest combined match rate at 0.702;
    `mix_r4_dual_quality` had the strongest combined average best score
    10204.712 and average mean score 10131.587; `quartic_lift` kept the best
    single proxy score at 10214.148; `mix_r4_dual_yield` remained a middle
    tradeoff at 0.694 match rate and 10129.761 average mean; `preset_r4`
    trailed at 0.585 match rate and 10108.354 average mean.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.68s after second r4 preset confirmation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before larger `mix_r4_dual_quality`
    confirmation work.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies preset_r4,four_real_seed,quartic_lift,mix_r4_dual_quality,mix_r4_dual_yield,mix_r4_dual_balanced --seeds 901,902,903,904,905,906,907,908,909,910,911,912 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_dual_quality_confirm_20260704`
  - Result: passed; 72 CPU-only `target_r=4` confirmation runs completed in
    289.85 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_dual_quality_confirm_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `72 True True ['four_real_seed', 'mix_r4_dual_balanced', 'mix_r4_dual_quality', 'mix_r4_dual_yield', 'preset_r4', 'quartic_lift'] [4]`
    and `1282 2049 1317`.
- 2026-07-04: inspected all confirmation dual-mix ledgers for mix metadata.
  - Result: 1,027 dual-label ledger records checked, no mixed-weight metadata
    mismatches. Observed strategy mix was `dual_yield`: 244
    `four_real_seed`, 91 `quartic_lift`; `dual_quality`: 244
    `quartic_lift`, 98 `four_real_seed`; `dual_balanced`: 162
    `quartic_lift`, 146 `four_real_seed`, 42 `sparse`.
- 2026-07-04: checked `resolve_generation_preset('r4', 'uniform', 'uniform:1')`.
  - Result: `preset_r4` still resolves to `mixed` with
    `four_real_seed:0.8,sparse:0.2`; no preset retune was applied.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.77s after larger r4 dual-quality confirmation
    work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `find . -type d -name __pycache__ -prune -exec rm -rf {} +`
  - Result: cleaned generated `__pycache__` directories; follow-up search
    found none.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before benchmark-only dual-family r4 mix work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_benchmark.py`
  - Result: 6 passed in 0.01s after adding benchmark-only dual r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts tests`
  - Result: passed after adding benchmark-only dual r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper mentions `mix_r4_dual_yield`,
    `mix_r4_dual_quality`, and `mix_r4_dual_balanced`.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies four_real_seed,quartic_lift,preset_r4,mix_r4_dual_yield,mix_r4_dual_quality,mix_r4_dual_balanced --seeds 801,802,803,804,805,806 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_dual_mix_bench_20260704`
  - Result: passed; 36 CPU-only `target_r=4` dual-mix benchmark runs
    completed in 150.98 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_dual_mix_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `36 True True ['four_real_seed', 'mix_r4_dual_balanced', 'mix_r4_dual_quality', 'mix_r4_dual_yield', 'preset_r4', 'quartic_lift'] [4]`
    and `640 1046 718`.
- 2026-07-04: inspected all dual-mix benchmark ledgers for mix metadata.
  - Result: 537 dual-label ledger records checked, no mixed-weight metadata
    mismatches. Observed strategy mix was `dual_yield`: 134 `four_real_seed`,
    37 `quartic_lift`; `dual_quality`: 120 `quartic_lift`, 60
    `four_real_seed`; `dual_balanced`: 84 `four_real_seed`, 86
    `quartic_lift`, 16 `sparse`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.68s after dual-family r4 mix work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after dual-family r4 mix work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper mentions the dual r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before Stage 2 `target_r=4`
    structured-family work.
- 2026-07-04: local scorer probe for quartic-lift templates
  `(y-a)(y-b)(y+c)(y+d)` with `y=x^6` and small off-support perturbations at
  `coeff_bound=4`.
  - Result: two bounded root templates were available. In 200-sample probes,
    odd perturbations produced 149 valid records with 77 at `r=4`,
    near-multiple perturbations produced 147 valid records with 73 at `r=4`,
    and all non-support perturbations produced 131 valid records with 79 at
    `r=4`. This justifies implementing a bounded `quartic_lift` strategy for
    comparison.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 22 passed in 0.85s after adding `quartic_lift`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src tests scripts`
  - Result: passed after adding `quartic_lift`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after adding `quartic_lift`.
- 2026-07-04: `quartic_lift` template probe through
  `IGP24DataPoint._quartic_lift_templates()` at `coeff_bound=4`.
  - Result: bounded templates are `(1,2,1,1)` with quartic coefficients
    `[2,1,-3,-1,1]` and `(1,3,1,1)` with `[3,2,-4,-2,1]`.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies mixed,four_real_seed,preset_r4,quartic_lift --seeds 701,702,703,704,705,706 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_quartic_lift_bench_20260704`
  - Result: passed; 24 CPU-only `target_r=4` comparison runs completed in
    104.35 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_quartic_lift_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `24 True True ['four_real_seed', 'mixed', 'preset_r4', 'quartic_lift'] [4]`
    and `430 708 391`.
- 2026-07-04: inspected `quartic_lift` benchmark ledgers for metadata.
  - Result: all six sampled `quartic_lift` run ledgers included
    `strategy='quartic_lift'`, the quartic-lift seed template, core support
    `[0,6,12,18]`, quartic coefficients, and perturbation coefficients.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 22 passed in 0.68s after `quartic_lift` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after `quartic_lift` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper mentions `quartic_lift`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before larger `target_r=4` preset validation.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_benchmark.py`
  - Result: 6 passed in 0.02s after adding benchmark-only r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts tests`
  - Result: passed after adding benchmark-only r4 mix labels.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper documents `mix_r4_yield`,
    `mix_r4_balanced`, and `mix_r4_diverse` benchmark-only labels.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies mixed,four_real_seed,preset_r4,mix_r4_yield,mix_r4_balanced,mix_r4_diverse --seeds 601,602,603,604,605,606 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_mix_variant_bench_20260704`
  - Result: passed; 36 CPU-only `target_r=4` tradeoff runs completed in
    157.13 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_mix_variant_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result:
    `36 True True ['four_real_seed', 'mix_r4_balanced', 'mix_r4_diverse', 'mix_r4_yield', 'mixed', 'preset_r4'] [4]`
    and `646 1089 555`.
- 2026-07-04: inspected r4 mix-variant ledgers for metadata.
  - Result: `mix_r4_yield`, `mix_r4_balanced`, and `mix_r4_diverse` records
    included the intended resolved mixed strategy weights.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 21 passed in 0.62s after r4 mix validation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after r4 mix validation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after r4 mix validation work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 21 passed in 1.00s after adding target-specific preset support.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src tests scripts`
  - Result: passed after adding target-specific preset support.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; helper documents `preset_r0`, `preset_r2`, and
    `preset_r4` benchmark labels.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies mixed,four_real_seed,preset_r4 --seeds 501,502,503,504 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_r4_preset_bench_20260704`
  - Result: passed; 12 CPU-only `target_r=4` preset benchmark runs completed
    in 53.88 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_r4_preset_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result: `12 True True ['four_real_seed', 'mixed', 'preset_r4'] [4]`
    and `215 379 180`.
- 2026-07-04: inspected `preset_r4` benchmark ledgers for metadata.
  - Result: 125 preset ledger records included `generation_preset='r4'`,
    `preset_target_r=4`, `resolved_generation_strategy='mixed'`, and resolved
    mixed weights `four_real_seed:0.8,sparse:0.2`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 21 passed in 0.66s after target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after target-specific preset work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before `target_r=4` generation work.
- 2026-07-04: local scorer probe for odd-perturbed
  `(x^2-a)(x^2-b)(x^20+1)` seeds at `coeff_bound=4`.
  - Result: across three 200-sample probes, valid samples had high `r=4`
    representation; this justifies trying a small explicit generator strategy.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24.py tests/test_igp24_benchmark.py`
  - Result: 18 passed in 0.70s after adding `four_real_seed`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall src tests scripts`
  - Result: passed after adding `four_real_seed`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after adding `four_real_seed`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 train.py --env_name igp24 --help`
  - Result: passed; this code path prints global `train.py` options only.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,mixed,four_real_seed --seeds 401,402,403,404 --target_rs 4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_four_real_seed_bench_20260704`
  - Result: passed; 12 CPU-only `target_r=4` benchmark runs completed in
    52.10 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_four_real_seed_bench_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['strategy'] for r in data}), sorted({r['target_r'] for r in data})); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data), sum(r.get('target_r_match_count') or 0 for r in data))"`
  - Result: `12 True True ['four_real_seed', 'mixed', 'sparse'] [4]` and
    `216 380 144`.
- 2026-07-04: inspected `four_real_seed` benchmark ledgers for metadata.
  - Result: 123 `four_real_seed` ledger records included
    `target_r_heuristic=4`, the perturbed seed template, and perturbation
    metadata.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 18 passed in 0.65s after `four_real_seed` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after `four_real_seed` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after `four_real_seed` work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before larger target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_benchmark.py`
  - Result: 5 passed in 0.02s after adding aggregate benchmark summaries.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall scripts tests`
  - Result: passed after adding aggregate benchmark summaries.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed after adding aggregate benchmark summaries.
- 2026-07-04:
  `/usr/bin/time -f 'elapsed_seconds %e' env PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,mixed --seeds 301,302,303,304 --target_rs none,0,2,4 --coeff_bound 4 --gensize 18 --pop_size 8 --ntest 2 --gen_batch_size 2 --max_local_search_steps 4 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_target_r_bench_larger_20260704`
  - Result: passed; 48 larger CPU-only target-r benchmark runs completed in
    193.26 seconds wall-clock.
- 2026-07-04:
  `python3 -c "import json; p='/tmp/igp24_target_r_bench_larger_20260704/summary.json'; data=json.load(open(p)); print(len(data), all(r['returncode']==0 for r in data), all(r.get('metadata_complete') for r in data), sorted({r['target_r'] for r in data}, key=lambda x: -1 if x is None else x)); print(sum(r.get('valid_candidates') or 0 for r in data), sum(r.get('ledger_records') or 0 for r in data))"`
  - Result: `48 True True [None, 0, 2, 4]` and `864 1561`.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 18 passed in 0.70s after larger target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after larger target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `git pull --ff-only`
  - Result: fast-forwarded README update from `f60e285` to `9b00f3d`.
- 2026-07-04: `git pull --ff-only`
  - Result: already up to date before target-r benchmark work.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 17 passed in 0.86s after adding target-r benchmark summary tests.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after adding target-r benchmark helper support.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; `--target_rs` is listed in the helper usage.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies sparse,structured,mixed --seeds 201,202 --target_rs none,2 --coeff_bound 4 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 3 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_target_r_bench`
  - Result: passed; 12 short CPU-only target-r benchmark runs completed.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 17 passed in 0.64s on final target-r benchmark check.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed on final target-r benchmark check.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 13 passed in 1.04s for the initial benchmark helper.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`
  - Result: passed; printed benchmark helper usage.
- 2026-07-04:
  `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --strategies uniform,low_height,sparse,lower_degree,structured,mixed --seeds 101,102 --coeff_bound 4 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --max_local_search_steps 3 --prime_limit 11 --exact_score_timeout 3 --output_dir /tmp/igp24_strategy_bench_final`
  - Result: passed; 12 short CPU-only runs completed.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 16 passed in 0.64s after valid-count parser, mixed weights, and
    seed-reset fixes.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed after valid-count parser, mixed weights, and seed-reset
    fixes.
- 2026-07-04: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 16 passed in 0.68s on final check.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-04: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`
  - Result: passed on final check.
- 2026-07-03: `git pull --ff-only`
  - Result: already up to date.
- 2026-07-03: `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`
  - Result: 11 passed in 0.66s after generation/scoring/local-search metadata
    changes.
- 2026-07-03: `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests`
  - Result: passed.
- 2026-07-03: `PYTHONPATH=/tmp/igp24_pydeps python3 -c "from src.envs import ENVS; print(sorted(ENVS))"`
  - Result: `['igp24', 'isosceles', 'sphere', 'square']`.
- 2026-07-03: `python -m pytest`
  - Result: blocked with `/bin/bash: line 1: python: command not found`.
- 2026-07-03:
  `/usr/bin/time -f 'elapsed_seconds %e' bash -lc 'PYTHONPATH=/tmp/igp24_pydeps python3 train.py --env_name igp24 --exp_name igp24_stage1_mixed_smoke --dump_path /tmp/igp24_stage1_smoke --seed 123 --coeff_bound 4 --gensize 12 --pop_size 6 --ntest 2 --gen_batch_size 2 --data_generation_only true --always_search true --max_local_search_steps 3 --prime_limit 11 --exact_score_timeout 3 --process_pool false --num_workers 1 --cpu true --igp24_generation_strategy mixed --igp24_sparse_terms 4 --igp24_low_height_bound 2 --igp24_ledger_path /tmp/igp24_stage1_mixed_candidates.jsonl'`
  - Result: passed, `elapsed_seconds 5.51`.

## Benchmark And Smoke Results

### 2026-07-03 Mixed Strategy CPU Smoke

- Command: see command log above.
- Runtime: 5.51 seconds wall-clock from `/usr/bin/time`.
- Generated valid examples reported by Axplorer stats: 12.
- Score summary:
  - Mean: 9928.237993556737.
  - Median: 9931.467170953914.
  - Max/best score: 9943.432289451468.
- Ledger path: `/tmp/igp24_stage1_mixed_candidates.jsonl`.
- Ledger records: 21 unique canonical hashes, 44K.
- Strategy mix in ledger:
  - `low_height`: 6.
  - `lower_degree`: 2.
  - `sparse`: 5.
  - `structured`: 2.
  - `uniform`: 6.
- Best strategy: `low_height`.
- Best canonical hash:
  `bb48609ade17fbf3a8e958ccaa87a5b39353bb4de00ccbbb8d617cd04c0cd484`.
- Metadata check: every ledger record included `score_components`,
  `generation_metadata`, and `local_search_metadata`.
- Local search telemetry: 12 ledger records included nonzero attempted move
  counts.

### 2026-07-04 Per-Strategy CPU Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_strategy_bench_final`.
- Summary files:
  - `/tmp/igp24_strategy_bench_final/summary.json`
  - `/tmp/igp24_strategy_bench_final/summary.jsonl`
- Configuration:
  - Strategies: `uniform`, `low_height`, `sparse`, `lower_degree`,
    `structured`, `mixed`.
  - Seeds: `101`, `102`.
  - `coeff_bound=4`, `gensize=12`, `max_local_search_steps=3`,
    `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- All 12 runs returned code 0.
- All summary records included parsed valid-candidate counts and complete
  score/generation/local-search metadata.

| Strategy | Runs | Avg Runtime | Valid Total | Ledger Records | Avg Best | Avg Mean | Best | Local Acceptance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `uniform` | 2 | 5.08s | 24 | 44 | 9929.100 | 9909.405 | 9933.489 | 0.507 |
| `low_height` | 2 | 4.73s | 24 | 45 | 9950.229 | 9932.816 | 9950.780 | 0.507 |
| `sparse` | 2 | 2.74s | 24 | 40 | 9957.878 | 9933.097 | 9971.765 | 0.486 |
| `lower_degree` | 2 | 3.24s | 24 | 43 | 9945.981 | 9932.596 | 9947.996 | 0.478 |
| `structured` | 2 | 2.60s | 23 | 39 | 9963.893 | 9944.075 | 9966.440 | 0.530 |
| `mixed` | 2 | 3.58s | 24 | 45 | 9959.846 | 9925.957 | 9960.447 | 0.493 |

Interpretation:

- `structured` had the strongest average mean score and the fastest
  high-scoring runs in this tiny comparison.
- `sparse` found the best single candidate and was also fast.
- `uniform` was slowest and lowest-scoring here.
- `mixed` remained viable but diluted the strongest strategies; default mixed
  weights now lean toward `sparse` and `structured` while preserving all
  strategies for diversity.
- These are small proxy-scoring runs only; do not overfit without larger runs
  and later exact verification.

### 2026-07-04 Target-r CPU Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_target_r_bench`.
- Summary files:
  - `/tmp/igp24_target_r_bench/summary.json`
  - `/tmp/igp24_target_r_bench/summary.jsonl`
- Configuration:
  - Strategies: `sparse`, `structured`, `mixed`.
  - Targets: untargeted and `target_r=2`.
  - Seeds: `201`, `202`.
  - `coeff_bound=4`, `gensize=12`, `max_local_search_steps=3`,
    `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- All 12 runs returned code 0.
- All summary records included target-r fields and complete
  score/generation/local-search metadata.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sparse` | untargeted | 2 | 3.38s | 24 | 41 | NA | NA | 9958.046 | NA | 9930.899 | 9959.898 | 0.455 |
| `sparse` | `r=2` | 2 | 2.69s | 24 | 41 | 36 | 0.868 | 10207.559 | 10207.559 | 10158.324 | 10208.925 | 0.439 |
| `structured` | untargeted | 2 | 2.55s | 24 | 45 | NA | NA | 9964.574 | NA | 9941.921 | 9965.166 | 0.493 |
| `structured` | `r=2` | 2 | 2.65s | 24 | 44 | 25 | 0.564 | 10208.513 | 10208.513 | 10119.278 | 10215.166 | 0.515 |
| `mixed` | untargeted | 2 | 3.48s | 24 | 42 | NA | NA | 9952.847 | NA | 9931.606 | 9954.384 | 0.493 |
| `mixed` | `r=2` | 2 | 3.43s | 24 | 41 | 26 | 0.627 | 10202.847 | 10202.847 | 10119.258 | 10204.384 | 0.530 |

Interpretation:

- `target_r=2` produced high match rates for all three compared strategies in
  this tiny run.
- `sparse` had the strongest `r=2` match rate at 0.868 and the best sparse
  target-r average score.
- `structured` retained the strongest untargeted average mean score and found
  the best single target-r score, but its `r=2` match rate was lower than
  `sparse`.
- `mixed` remained useful but did not beat the best specialized strategy under
  this short run.
- No new generation default change is warranted from this small target-r run
  alone; use larger target-r benchmarks before tuning again.

### 2026-07-04 Larger Target-r CPU Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_target_r_bench_larger_20260704`.
- Summary files:
  - `/tmp/igp24_target_r_bench_larger_20260704/summary.json`
  - `/tmp/igp24_target_r_bench_larger_20260704/summary.jsonl`
  - `/tmp/igp24_target_r_bench_larger_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: `sparse`, `structured`, `mixed`.
  - Targets: untargeted, `target_r=0`, `target_r=2`, and `target_r=4`.
  - Seeds: `301`, `302`, `303`, `304`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 193.26 seconds.
- All 48 runs returned code 0.
- Artifact audit:
  - Summary rows: 48.
  - Valid candidates: 864.
  - Ledger records: 1,561.
  - All summary records included complete score/generation/local-search
    metadata.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `mixed` | `r=0` | 4 | 4.95s | 72 | 135 | 41 | 0.303 | 10210.117 | 10210.117 | 10061.147 | 10222.117 | 0.424 |
| `mixed` | `r=2` | 4 | 4.97s | 72 | 135 | 92 | 0.680 | 10208.197 | 10208.197 | 10127.371 | 10213.260 | 0.417 |
| `mixed` | `r=4` | 4 | 4.88s | 72 | 135 | 28 | 0.209 | 10201.770 | 10201.770 | 10042.195 | 10205.289 | 0.431 |
| `mixed` | untargeted | 4 | 4.96s | 72 | 135 | NA | NA | 9963.787 | NA | 9931.598 | 9972.117 | 0.417 |
| `sparse` | `r=0` | 4 | 3.63s | 72 | 135 | 33 | 0.246 | 10196.939 | 10196.939 | 10053.043 | 10204.853 | 0.417 |
| `sparse` | `r=2` | 4 | 3.70s | 72 | 134 | 100 | 0.745 | 10202.643 | 10202.643 | 10139.115 | 10208.544 | 0.430 |
| `sparse` | `r=4` | 4 | 3.78s | 72 | 137 | 26 | 0.191 | 10192.821 | 10192.821 | 10041.827 | 10207.005 | 0.426 |
| `sparse` | untargeted | 4 | 4.03s | 72 | 137 | NA | NA | 9955.183 | NA | 9932.331 | 9958.544 | 0.419 |
| `structured` | `r=0` | 4 | 3.26s | 72 | 120 | 60 | 0.501 | 10215.071 | 10215.071 | 10108.438 | 10216.978 | 0.364 |
| `structured` | `r=2` | 4 | 3.16s | 72 | 119 | 75 | 0.629 | 10213.416 | 10213.416 | 10128.951 | 10216.622 | 0.413 |
| `structured` | `r=4` | 4 | 3.25s | 72 | 119 | 4 | 0.034 | 10126.258 | 10204.226 | 10017.312 | 10209.825 | 0.424 |
| `structured` | untargeted | 4 | 3.28s | 72 | 120 | NA | NA | 9965.160 | NA | 9942.122 | 9966.978 | 0.389 |

Interpretation:

- `structured` looks best for `target_r=0` in this run: strongest average
  best score, strongest average mean score, and the highest `r=0` match rate.
- `sparse` still looks best for reliably hitting `target_r=2`: highest match
  rate at 0.745 and the strongest `r=2` average mean score.
- `structured` found the strongest `r=2` peak and average best scores, so a
  larger `r=2` run should probably compare `sparse` reliability against
  `structured` peak quality rather than picking only one.
- `target_r=4` remains weak for the current families. `mixed` and `sparse`
  found some matching records, but match rates stayed low; `structured` nearly
  missed this target entirely.
- Untargeted results still favor `structured` on average score, while `mixed`
  found the best single untargeted candidate in this batch.
- No global generation default change is justified from this proxy-only run.
  A practical next tuning step would be target-specific run presets, especially
  `structured` for `r=0`, `sparse` plus `structured` for `r=2`, and new
  `r=4`-friendly families before retuning `mixed`.

### 2026-07-04 Four-real Seed Target-r Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_four_real_seed_bench_20260704`.
- Summary files:
  - `/tmp/igp24_four_real_seed_bench_20260704/summary.json`
  - `/tmp/igp24_four_real_seed_bench_20260704/summary.jsonl`
  - `/tmp/igp24_four_real_seed_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: `sparse`, `mixed`, `four_real_seed`.
  - Target: `target_r=4`.
  - Seeds: `401`, `402`, `403`, `404`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 52.10 seconds.
- All 12 runs returned code 0.
- Artifact audit:
  - Summary rows: 12.
  - Valid candidates: 216.
  - Ledger records: 380.
  - Target-r matching records: 144.
  - All summary records included complete score/generation/local-search
    metadata.
  - `four_real_seed` ledger records included `target_r_heuristic=4`,
    `seed_template`, and perturbation metadata.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 4 | 4.18s | 72 | 123 | 97 | 0.792 | 10193.136 | 10193.136 | 10145.343 | 10195.370 | 0.346 |
| `mixed` | `r=4` | 4 | 5.04s | 72 | 130 | 26 | 0.200 | 10191.476 | 10191.476 | 10043.085 | 10197.883 | 0.438 |
| `sparse` | `r=4` | 4 | 3.67s | 72 | 127 | 21 | 0.164 | 10194.103 | 10194.103 | 10037.574 | 10207.604 | 0.423 |

Interpretation:

- `four_real_seed` materially improved `target_r=4` match rate in this short
  proxy-scored run: 0.792 average match rate versus 0.200 for `mixed` and
  0.164 for `sparse`.
- `four_real_seed` also had the strongest average mean score, which is expected
  because target-r bonus dominates once many generated candidates match
  `r=4`.
- `sparse` still found the best single candidate score in this batch, so the
  new strategy should be treated as a high-yield target-r generator rather than
  a universal quality winner.
- Local-search acceptance was lower for `four_real_seed`; this may indicate the
  current mutation moves often disturb the `r=4` shape.
- No global `mixed` default was changed. A later target-specific preset could
  include `four_real_seed` for `target_r=4`, but it needs a larger run and
  eventually exact external verification before promotion.

### 2026-07-04 R4 Preset Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_preset_bench_20260704`.
- Summary files:
  - `/tmp/igp24_r4_preset_bench_20260704/summary.json`
  - `/tmp/igp24_r4_preset_bench_20260704/summary.jsonl`
  - `/tmp/igp24_r4_preset_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: baseline `mixed`, explicit `four_real_seed`, and
    `preset_r4`.
  - Preset resolution: `preset_r4` runs as `--igp24_generation_strategy mixed`
    and `--igp24_generation_preset r4`, resolving to
    `four_real_seed:0.8,sparse:0.2`.
  - Target: `target_r=4`.
  - Seeds: `501`, `502`, `503`, `504`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 53.88 seconds.
- All 12 runs returned code 0.
- Artifact audit:
  - Summary rows: 12.
  - Valid candidates: 215.
  - Ledger records: 379.
  - Target-r matching records: 180.
  - All summary records included complete score/generation/local-search
    metadata.
  - `preset_r4` ledger records included preset name, target-r intent, resolved
    strategy, and resolved mixed weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 4 | 4.27s | 71 | 123 | 89 | 0.728 | 10193.071 | 10193.071 | 10132.778 | 10195.370 | 0.364 |
| `mixed` | `r=4` | 4 | 5.05s | 72 | 131 | 28 | 0.213 | 10195.711 | 10195.711 | 10047.644 | 10201.811 | 0.442 |
| `preset_r4` | `r=4` | 4 | 4.00s | 72 | 125 | 63 | 0.503 | 10198.249 | 10198.249 | 10096.563 | 10203.117 | 0.406 |

Interpretation:

- `preset_r4` improved over baseline `mixed` on `r=4` match rate and average
  mean score, while preserving some sparse diversity.
- Explicit `four_real_seed` still had the strongest `r=4` match rate in this
  bounded run: 0.728 versus 0.503 for `preset_r4`.
- `preset_r4` found the best single score and strongest average best score in
  this batch, so the sparse-diversity blend may help peak quality even though
  it dilutes target-r yield.
- The preset did not beat explicit `four_real_seed` on target-r match rate; do
  not promote it as strictly better. Treat it as a named convenience preset
  with a yield/quality tradeoff that needs larger validation.
- Default generation remains unchanged because presets are opt-in.

### 2026-07-04 R4 Mix Variant Validation

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_mix_variant_bench_20260704`.
- Summary files:
  - `/tmp/igp24_r4_mix_variant_bench_20260704/summary.json`
  - `/tmp/igp24_r4_mix_variant_bench_20260704/summary.jsonl`
  - `/tmp/igp24_r4_mix_variant_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: baseline `mixed`, explicit `four_real_seed`, current
    `preset_r4`, and benchmark-only mix labels `mix_r4_yield`,
    `mix_r4_balanced`, and `mix_r4_diverse`.
  - Mix labels:
    - `mix_r4_yield`: `four_real_seed:1.0`.
    - `mix_r4_balanced`: `four_real_seed:0.8,sparse:0.2`.
    - `mix_r4_diverse`: `four_real_seed:0.6,sparse:0.4`.
  - Target: `target_r=4`.
  - Seeds: `601`, `602`, `603`, `604`, `605`, `606`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 157.13 seconds.
- All 36 runs returned code 0.
- Artifact audit:
  - Summary rows: 36.
  - Valid candidates: 646.
  - Ledger records: 1,089.
  - Target-r matching records: 555.
  - All summary records included complete score/generation/local-search
    metadata.
  - Mix-variant ledger records included the intended resolved mixed weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 6 | 4.29s | 107 | 174 | 133 | 0.765 | 10193.551 | 10193.551 | 10140.093 | 10195.370 | 0.347 |
| `mix_r4_balanced` | `r=4` | 6 | 4.12s | 108 | 182 | 101 | 0.555 | 10195.700 | 10195.700 | 10106.215 | 10198.632 | 0.372 |
| `mix_r4_diverse` | `r=4` | 6 | 3.88s | 108 | 185 | 71 | 0.393 | 10195.487 | 10195.487 | 10076.236 | 10201.230 | 0.404 |
| `mix_r4_yield` | `r=4` | 6 | 4.20s | 107 | 173 | 112 | 0.652 | 10192.954 | 10192.954 | 10120.969 | 10198.193 | 0.349 |
| `mixed` | `r=4` | 6 | 5.32s | 108 | 193 | 37 | 0.192 | 10194.609 | 10194.609 | 10044.129 | 10204.040 | 0.406 |
| `preset_r4` | `r=4` | 6 | 4.06s | 108 | 182 | 101 | 0.555 | 10195.700 | 10195.700 | 10106.215 | 10198.632 | 0.372 |

Interpretation:

- Explicit `four_real_seed` remains the best high-yield `target_r=4` option:
  it had the highest average match rate at 0.765 and the highest average mean
  score.
- Current `preset_r4` exactly matches the benchmark-only balanced label,
  `mix_r4_balanced`, as expected. It improved over baseline `mixed` on match
  rate, average best score, and average mean score.
- The diversity-heavy `mix_r4_diverse` found the best single proxy score in
  this batch, but its match rate fell to 0.393. Extra sparse diversity appears
  to help peak exploration at the cost of target-r yield.
- The pure `mix_r4_yield` label used mixed dispatch with 100%
  `four_real_seed`; because it consumed random choices differently than the
  explicit strategy, it was not identical to explicit `four_real_seed` and had
  a lower 0.652 match rate in this run.
- Do not change `preset_r4` from `four_real_seed:0.8,sparse:0.2` yet. It is a
  reasonable balanced preset, while explicit `four_real_seed` should remain
  the documented recommendation when `r=4` yield is the only priority.
- No default generation change is justified; this is still proxy-only and has
  no exact `24Tt` verification.

### 2026-07-04 Quartic-lift Target-r Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_quartic_lift_bench_20260704`.
- Summary files:
  - `/tmp/igp24_quartic_lift_bench_20260704/summary.json`
  - `/tmp/igp24_quartic_lift_bench_20260704/summary.jsonl`
  - `/tmp/igp24_quartic_lift_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: baseline `mixed`, explicit `four_real_seed`, current
    `preset_r4`, and new `quartic_lift`.
  - Target: `target_r=4`.
  - Seeds: `701`, `702`, `703`, `704`, `705`, `706`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 104.35 seconds.
- All 24 runs returned code 0.
- Artifact audit:
  - Summary rows: 24.
  - Valid candidates: 430.
  - Ledger records: 708.
  - Target-r matching records: 391.
  - All summary records included complete score/generation/local-search
    metadata.
  - `quartic_lift` ledger records included the seed template, core support,
    quartic coefficients, and perturbation coefficients.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 6 | 4.18s | 107 | 166 | 126 | 0.757 | 10196.049 | 10196.049 | 10137.886 | 10203.007 | 0.381 |
| `mixed` | `r=4` | 6 | 5.22s | 108 | 196 | 39 | 0.197 | 10191.736 | 10191.736 | 10041.856 | 10194.638 | 0.424 |
| `preset_r4` | `r=4` | 6 | 4.06s | 107 | 180 | 109 | 0.608 | 10195.473 | 10195.473 | 10112.317 | 10201.396 | 0.390 |
| `quartic_lift` | `r=4` | 6 | 3.78s | 108 | 166 | 117 | 0.705 | 10206.896 | 10206.896 | 10139.839 | 10210.196 | 0.352 |

Interpretation:

- `quartic_lift` is a promising quality-oriented r4 family. It had the
  strongest average best score, strongest average matching score, strongest
  average mean score, and best single proxy score in this batch.
- Explicit `four_real_seed` still had the strongest r4 yield: 0.757 average
  match rate versus 0.705 for `quartic_lift` and 0.608 for `preset_r4`.
- `quartic_lift` beat the current balanced `preset_r4` on match rate and proxy
  score in this run, but one bounded proxy-only benchmark is not enough to
  retune the preset.
- Local-search acceptance was lowest for `quartic_lift`; future work should
  inspect whether generic mutations disrupt the quartic-lift shape.
- Keep default mixed weights and `preset_r4` unchanged. The next useful step is
  a larger r4 comparison that includes both `four_real_seed` and
  `quartic_lift`, or a benchmark-only mixed variant combining them.

### 2026-07-04 R4 Dual-family Mix Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_dual_mix_bench_20260704`.
- Summary files:
  - `/tmp/igp24_r4_dual_mix_bench_20260704/summary.json`
  - `/tmp/igp24_r4_dual_mix_bench_20260704/summary.jsonl`
  - `/tmp/igp24_r4_dual_mix_bench_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: explicit `four_real_seed`, explicit `quartic_lift`, current
    `preset_r4`, and benchmark-only dual labels `mix_r4_dual_yield`,
    `mix_r4_dual_quality`, and `mix_r4_dual_balanced`.
  - Mix labels:
    - `mix_r4_dual_yield`: `four_real_seed:0.75,quartic_lift:0.25`.
    - `mix_r4_dual_quality`: `four_real_seed:0.25,quartic_lift:0.75`.
    - `mix_r4_dual_balanced`:
      `four_real_seed:0.45,quartic_lift:0.45,sparse:0.10`.
  - Target: `target_r=4`.
  - Seeds: `801`, `802`, `803`, `804`, `805`, `806`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 150.98 seconds.
- All 36 runs returned code 0.
- Artifact audit:
  - Summary rows: 36.
  - Valid candidates: 640.
  - Ledger records: 1,046.
  - Target-r matching records: 718.
  - All summary records included complete score/generation/local-search
    metadata.
  - All 537 dual-label ledger records checked had the expected mixed weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 6 | 4.41s | 106 | 171 | 121 | 0.709 | 10192.989 | 10192.989 | 10129.971 | 10195.878 | 0.358 |
| `mix_r4_dual_balanced` | `r=4` | 6 | 4.07s | 108 | 186 | 120 | 0.649 | 10206.061 | 10206.061 | 10123.920 | 10212.713 | 0.355 |
| `mix_r4_dual_quality` | `r=4` | 6 | 4.04s | 108 | 180 | 139 | 0.774 | 10201.181 | 10201.181 | 10147.115 | 10207.040 | 0.359 |
| `mix_r4_dual_yield` | `r=4` | 6 | 4.30s | 106 | 171 | 126 | 0.734 | 10196.517 | 10196.517 | 10136.035 | 10205.056 | 0.387 |
| `preset_r4` | `r=4` | 6 | 4.38s | 108 | 190 | 115 | 0.604 | 10195.842 | 10195.842 | 10112.710 | 10205.003 | 0.376 |
| `quartic_lift` | `r=4` | 6 | 3.95s | 104 | 148 | 97 | 0.657 | 10201.844 | 10201.844 | 10130.628 | 10207.040 | 0.362 |

Interpretation:

- `mix_r4_dual_quality` was the best overall tradeoff in this bounded run:
  highest average match rate at 0.774, strongest average mean score, and a
  strong average best score.
- `mix_r4_dual_yield` also improved over explicit `four_real_seed` on match
  rate and score metrics, though less dramatically than the quality-leaning
  mix.
- `mix_r4_dual_balanced` found the best single proxy score at 10212.713, but
  its match rate was below the other two dual mixes.
- Current `preset_r4` trailed all three dual labels on match rate and average
  best score in this run.
- Despite that, do not change `preset_r4` yet. This was a bounded proxy-only
  benchmark with one seed block. The evidence justifies a larger confirmation
  run, likely centered on `mix_r4_dual_quality`, before retuning any preset.

### 2026-07-04 R4 Dual-quality Confirmation

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_dual_quality_confirm_20260704`.
- Summary files:
  - `/tmp/igp24_r4_dual_quality_confirm_20260704/summary.json`
  - `/tmp/igp24_r4_dual_quality_confirm_20260704/summary.jsonl`
  - `/tmp/igp24_r4_dual_quality_confirm_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: current `preset_r4`, explicit `four_real_seed`, explicit
    `quartic_lift`, `mix_r4_dual_quality`, `mix_r4_dual_yield`, and
    `mix_r4_dual_balanced`.
  - Target: `target_r=4`.
  - Seeds: `901`, `902`, `903`, `904`, `905`, `906`, `907`, `908`, `909`,
    `910`, `911`, `912`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 289.85 seconds.
- All 72 runs returned code 0.
- Artifact audit:
  - Summary rows: 72.
  - Valid candidates: 1,282.
  - Ledger records: 2,049.
  - Target-r matching records: 1,317.
  - All summary records included complete score/generation/local-search
    metadata.
  - All 1,027 dual-label ledger records checked had the expected mixed
    weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 12 | 4.19s | 216 | 352 | 241 | 0.688 | 10195.219 | 10195.219 | 10126.379 | 10201.043 | 0.361 |
| `mix_r4_dual_balanced` | `r=4` | 12 | 4.03s | 215 | 350 | 212 | 0.609 | 10198.942 | 10198.942 | 10117.771 | 10207.509 | 0.407 |
| `mix_r4_dual_quality` | `r=4` | 12 | 3.95s | 214 | 342 | 218 | 0.639 | 10203.367 | 10203.367 | 10125.458 | 10207.509 | 0.377 |
| `mix_r4_dual_yield` | `r=4` | 12 | 4.09s | 214 | 335 | 229 | 0.683 | 10199.688 | 10199.688 | 10128.913 | 10206.711 | 0.385 |
| `preset_r4` | `r=4` | 12 | 4.19s | 213 | 348 | 206 | 0.590 | 10193.351 | 10193.351 | 10109.302 | 10202.793 | 0.384 |
| `quartic_lift` | `r=4` | 12 | 3.71s | 210 | 322 | 211 | 0.650 | 10204.553 | 10204.553 | 10129.814 | 10214.148 | 0.366 |

Interpretation:

- `mix_r4_dual_quality` again beat current `preset_r4` on average match rate
  and score metrics, but it was not the strongest confirmed option overall.
- Explicit `quartic_lift` beat `mix_r4_dual_quality` on match rate, average
  best score, average mean score, and best single proxy score in this seed
  block.
- `mix_r4_dual_yield` nearly matched explicit `four_real_seed` on match rate
  and beat `mix_r4_dual_quality` on average mean score.
- This is mixed evidence for retuning specifically to
  `four_real_seed:0.25,quartic_lift:0.75`. The larger run confirms that the
  current `preset_r4` is probably stale, but it does not cleanly confirm the
  dual-quality mix as the new preset.
- Decision: keep `preset_r4` unchanged for now. The next retuning step should
  directly compare `quartic_lift`, `mix_r4_dual_yield`, and current `preset_r4`
  on a second 12-seed block or add a quartic-heavy preset candidate before
  changing the user-facing preset.

### 2026-07-04 Second R4 Preset Confirmation

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_second_confirm_20260704`.
- Summary files:
  - `/tmp/igp24_r4_second_confirm_20260704/summary.json`
  - `/tmp/igp24_r4_second_confirm_20260704/summary.jsonl`
  - `/tmp/igp24_r4_second_confirm_20260704/aggregate_summary.json`
- Configuration:
  - Strategies: current `preset_r4`, explicit `quartic_lift`,
    `mix_r4_dual_yield`, `mix_r4_dual_quality`, explicit
    `four_real_seed`, and `mix_r4_dual_balanced`.
  - Target: `target_r=4`.
  - Fresh disjoint seeds: `1001`, `1002`, `1003`, `1004`, `1005`,
    `1006`, `1007`, `1008`, `1009`, `1010`, `1011`, `1012`, `1013`,
    `1014`, `1015`, `1016`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 397.34 seconds.
- All 96 runs returned code 0.
- Artifact audit:
  - Summary rows: 96.
  - Valid candidates: 1,715.
  - Ledger records: 2,821.
  - Target-r matching records: 1,887.
  - All summary records included complete score/generation/local-search
    metadata.
  - Aggregate rows included match rate, average best, average mean, best
    score, and local-search acceptance fields.
  - All 1,403 dual-label ledger records checked had the expected mixed
    weights.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Best Match | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | `r=4` | 16 | 4.29s | 281 | 479 | 341 | 0.712 | 10196.345 | 10196.345 | 10129.904 | 10205.378 | 0.375 |
| `mix_r4_dual_balanced` | `r=4` | 16 | 4.09s | 288 | 470 | 311 | 0.665 | 10203.000 | 10203.000 | 10126.958 | 10206.711 | 0.365 |
| `mix_r4_dual_quality` | `r=4` | 16 | 3.96s | 285 | 457 | 321 | 0.703 | 10205.721 | 10205.721 | 10136.184 | 10213.786 | 0.363 |
| `mix_r4_dual_yield` | `r=4` | 16 | 4.12s | 287 | 476 | 334 | 0.702 | 10200.852 | 10200.852 | 10130.398 | 10212.926 | 0.356 |
| `preset_r4` | `r=4` | 16 | 4.44s | 287 | 494 | 288 | 0.582 | 10193.953 | 10193.953 | 10107.642 | 10203.816 | 0.372 |
| `quartic_lift` | `r=4` | 16 | 3.94s | 287 | 445 | 292 | 0.657 | 10204.829 | 10204.829 | 10131.884 | 10213.786 | 0.352 |

Combined with the prior 12-seed confirmation:

| Strategy | Runs | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Mean | Best | Local Acceptance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `four_real_seed` | 28 | 497 | 831 | 582 | 0.702 | 10195.863 | 10128.393 | 10205.378 | 0.369 |
| `mix_r4_dual_balanced` | 28 | 503 | 820 | 523 | 0.641 | 10201.261 | 10123.021 | 10207.509 | 0.383 |
| `mix_r4_dual_quality` | 28 | 499 | 799 | 539 | 0.676 | 10204.712 | 10131.587 | 10213.786 | 0.369 |
| `mix_r4_dual_yield` | 28 | 501 | 811 | 563 | 0.694 | 10200.353 | 10129.761 | 10212.926 | 0.368 |
| `preset_r4` | 28 | 500 | 842 | 494 | 0.585 | 10193.695 | 10108.354 | 10203.816 | 0.377 |
| `quartic_lift` | 28 | 497 | 767 | 503 | 0.654 | 10204.711 | 10130.997 | 10214.148 | 0.358 |

Interpretation:

- Current `preset_r4` again trailed the stronger r4 families and mixes on
  both match rate and score metrics. It is useful as historical context but no
  longer looks competitive in these proxy runs.
- The fresh 16-seed block favored `mix_r4_dual_quality` on average best score,
  average mean score, and best single score, while `four_real_seed` retained a
  slightly higher match rate.
- `mix_r4_dual_yield` did not clearly win the yield/quality tradeoff: its
  match rate was close to `mix_r4_dual_quality`, but its average best and
  average mean scores were lower.
- `quartic_lift` did not clearly beat the mix labels overall. It had strong
  quality metrics and ties the fresh-block best single proxy score, but its
  match rate was lower than both dual-yield and dual-quality.
- Across both confirmation blocks, evidence still splits by objective:
  `four_real_seed` for match rate, `mix_r4_dual_quality` for average proxy
  quality, and `quartic_lift` for the best single proxy score.
- Decision: keep `preset_r4` unchanged again. The current preset is likely
  stale, but neither requested retune target is clearly dominant enough to
  change the user-facing preset on proxy-only evidence. A better next step is
  to add safe batch export/shortlist tooling for top r4 proxy candidates so the
  strongest families can feed later offline exact verification.

### 2026-07-04 R4 Shortlist Export Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_shortlist_20260704`.
- Inputs:
  - `/tmp/igp24_r4_second_confirm_20260704`
  - `/tmp/igp24_r4_dual_quality_confirm_20260704`
- Filters: `target_r=4`, top 25 by descending proxy score, deduplicated by
  canonical hash.
- Output files:
  - `/tmp/igp24_r4_shortlist_20260704/shortlist.jsonl`
  - `/tmp/igp24_r4_shortlist_20260704/coefficients.json`
  - `/tmp/igp24_r4_shortlist_20260704/coefficients.txt`
  - `/tmp/igp24_r4_shortlist_20260704/manifest.json`
- Loaded source records: 4,870.
- Selected records: 25.
- Unique canonical hashes: 25.
- Top score: 10214.147570701043.
- Last selected score: 10205.676526314839.
- Strategy counts:
  - `quartic_lift`: 23.
  - `four_real_seed`: 2.
- Audit:
  - All selected rows have `real_root_count=4`.
  - All exported coefficient vectors have length 25 and end in the fixed
    leading coefficient 1.
  - All selected rows include `source_ledger_path`.
  - Scores are sorted descending.
  - Manifest safety flags record `proxy_only=true`,
    `verifier_executed=false`, `submission_executed=false`, and
    `exact_group_claims=false`.
- Caveat: this is still proxy-scored export data only. It prepares candidates
  for later human-reviewed offline exact verification and does not certify any
  exact group label.

### 2026-07-04 R4 Review Batch Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_review_batch_20260704`.
- Input shortlist: `/tmp/igp24_r4_shortlist_20260704`.
- Selection criteria: top proxy score, batch size 8, at least 2 strategies
  where available, and a per-strategy cap of 6.
- Output files:
  - `/tmp/igp24_r4_review_batch_20260704/review_report.md`
  - `/tmp/igp24_r4_review_batch_20260704/verification_batch.jsonl`
  - `/tmp/igp24_r4_review_batch_20260704/verification_coefficients.txt`
  - `/tmp/igp24_r4_review_batch_20260704/manifest.json`
- Loaded shortlist records: 25.
- Selected records: 8.
- Unique canonical hashes: 8.
- Top score: 10214.147570701043.
- Strategy counts:
  - `quartic_lift`: 6.
  - `four_real_seed`: 2.
- Audit:
  - All exported coefficient vectors have length 25 and end in the fixed
    leading coefficient 1.
  - Every row records both `source_ledger_path` and `source_shortlist_path`.
  - Every review record keeps `verified_group_label=null` and an explicit
    proxy-only caveat.
  - Manifest safety flags record `proxy_only=true`,
    `review_export_only=true`, `verifier_executed=false`,
    `submission_executed=false`, `network_calls=false`, and
    `exact_group_claims=false`.
- Caveat: this is a human-review batch for later offline exact-verifier
  experiments. It did not run PARI, MAGMA, SAIR, network calls, exact group
  verification, or any submission path.

### 2026-07-04 R4 Offline Verification Prep Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_r4_offline_verify_20260704`.
- Input review batch: `/tmp/igp24_r4_review_batch_20260704`.
- Mode: default preparation-only dry run; no `--run_pari` or `--run_magma`
  flags were used.
- Output files:
  - `/tmp/igp24_r4_offline_verify_20260704/offline_verification_manifest.json`
  - `/tmp/igp24_r4_offline_verify_20260704/pari_input.gp`
  - `/tmp/igp24_r4_offline_verify_20260704/magma_input.m`
  - `/tmp/igp24_r4_offline_verify_20260704/verification_plan.md`
- Loaded review records: 8.
- Unique selected hashes: 8.
- Tool availability:
  - PARI/GP `gp`: unavailable on PATH.
  - MAGMA `magma`: unavailable on PATH.
- Execution:
  - PARI/GP requested: false; executed: false.
  - MAGMA requested: false; executed: false.
  - No raw verifier output files were created.
- Audit:
  - Manifest records coefficient shape as length 25 with fixed leading
    coefficient 1.
  - Generated PARI/GP and MAGMA scripts include the candidate hashes and
    commented exact Galois-group steps for deliberate manual use.
  - Manifest safety flags record `network_calls=false`,
    `sair_submission=false`, `auto_submission=false`,
    `pari_executed=false`, `magma_executed=false`,
    `exact_group_labels_parsed=false`, `exact_group_claims=false`, and
    `dry_run_preparation_only=true`.
- Caveat: this smoke only prepares local verifier inputs. It does not verify
  candidates, parse exact group labels, contact SAIR, make network calls, or
  submit anything.

### 2026-07-04 Fixed Sparse Template r2 Benchmark

- Command: see command log above.
- Output directory: `/tmp/igp24_fixed_sparse_template_bench_20260704`.
- Configuration:
  - Strategies: `sparse`, `structured`, `fixed_sparse_template`.
  - Target: `target_r=2`.
  - Seeds: `1101`, `1102`, `1103`, `1104`.
  - `coeff_bound=4`, `gensize=18`, `pop_size=8`,
    `max_local_search_steps=4`, `prime_limit=11`.
  - CPU-only, `process_pool=false`, no MAGMA/PARI/SAIR/CUDA.
- Wall-clock runtime: 50.42 seconds from `/usr/bin/time -p`.
- All 12 runs returned code 0.
- Artifact audit:
  - Summary rows: 12.
  - Valid candidates: 216.
  - Ledger records: 391.
  - Target-r matching records: 258.
  - All summary rows had complete score/generation/local-search metadata.
  - 130 `fixed_sparse_template` ledger rows included template name, support
    indices, coefficient bound, and extra nonzero indices introduced by local
    search where applicable.

| Strategy | Target | Runs | Avg Runtime | Valid Total | Ledger Records | Match Total | Avg Match Rate | Avg Best | Avg Mean | Best | Local Acceptance |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_sparse_template` | `r=2` | 4 | 4.66s | 72 | 130 | 90 | 0.692 | 10192.027 | 10118.108 | 10193.846 | 0.420 |
| `sparse` | `r=2` | 4 | 4.40s | 72 | 133 | 88 | 0.658 | 10199.870 | 10124.774 | 10205.840 | 0.472 |
| `structured` | `r=2` | 4 | 3.54s | 72 | 128 | 80 | 0.626 | 10214.248 | 10128.146 | 10219.375 | 0.408 |

Interpretation:

- `fixed_sparse_template` had the highest average `r=2` match rate in this
  small block, 0.692 versus 0.658 for `sparse` and 0.626 for `structured`.
- The new family lagged the baselines on proxy quality: `structured` had the
  strongest average best, average mean, and best single proxy score; `sparse`
  was second on those score metrics.
- Treat `fixed_sparse_template` as a useful r2-yield/diversity probe, not as a
  default or preset candidate from this one bounded proxy benchmark.
- No generation default, default mixed weight, or `preset_r4` change is
  justified here. Exact verification remains unrun because local PARI/GP and
  MAGMA are unavailable.

### 2026-07-04 GPU Readiness Smoke

- Command: see command log above.
- Output directory: `/tmp/igp24_gpu_smoke_20260704`.
- Artifacts:
  - `/tmp/igp24_gpu_smoke_20260704/gpu_smoke_summary.json`
  - `/tmp/igp24_gpu_smoke_20260704/gpu_smoke_report.md`
  - `/tmp/igp24_gpu_smoke_20260704/cpu_candidates.jsonl`
  - `/tmp/igp24_gpu_smoke_20260704/gpu_candidates.jsonl`
- Probe result outside the managed sandbox:
  - GPU: NVIDIA GeForce RTX 5090, 32607 MiB, driver 596.49.
  - PyTorch: `2.12.1+cu130`, CUDA available, CUDA tensor smoke true,
    device `NVIDIA GeForce RTX 5090`.
- Smoke comparison:

| Run | Return Code | Runtime | Valid Candidates | Ledger Rows | Metadata Complete | Logged Device | GPU Used |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| CPU baseline | 0 | 2.39s | 7 | 12 | true | `cpu` | false |
| GPU train | 0 | 3.88s | 4 | 12 | true | `cuda` | true |

Interpretation:

- This machine can run the IGP24 Axplorer training path on CUDA outside the
  managed sandbox. The tiny GPU train exercised model placement, training
  batches, evaluation, sampling, CUDA memory logging, and ledger metadata.
- The managed sandbox can block NVML/CUDA access for child processes; use an
  unsandboxed run when the goal is to measure GPU hardware behavior.
- Do not switch away from CPU proxy-search wholesale from this tiny smoke.
  Run both in parallel: CPU proxy generation/search remains the main candidate
  pipeline, while GPU training is now a viable parallel sampler path for a
  controlled longer run.

## Blockers / Environment Notes

- The previous stage-0 run used a temporary dependency target at
  `/tmp/igp24_pydeps` because the base shell did not have `python`, `numpy`,
  `sympy`, `pytest`, or `torch` available directly.
- Current shell still lacks a `python` executable; use `python3` with
  `PYTHONPATH=/tmp/igp24_pydeps` for local checks unless a proper environment is
  activated.
- Benchmark helper initially parsed valid candidates from stdout only, but
  Axplorer logging writes the count to stderr. Fixed by parsing combined
  stdout/stderr.
- Initial benchmark attempts showed that fixed `--seed` did not control NumPy
  generation. Fixed by seeding NumPy in `IGP24Environment`.
- GPU/NVML/CUDA checks can differ between the managed sandbox and an
  unsandboxed process. The authoritative 2026-07-04 GPU smoke was run outside
  the managed sandbox and proved PyTorch CUDA on the RTX 5090.

## Future Stages

Keep these future-stage items visible while the live log changes. Break them
down further as they become active.

### Stage 2: Structured Families And Exact-Tool Prep

- [done] Add an opt-in fixed-support sparse template generation family.
  - [done] Add a `fixed_sparse_template` strategy distinct from random
    `sparse`, using a small hand-auditable set of support templates.
  - [done] Keep the strategy opt-in only; do not change default mixed
    weights, default generation behavior, or `preset_r4`.
  - [done] Record ledger metadata for template name, support indices,
    coefficient bound, and any target-r intent.
  - [done] Add focused tests for coefficient shape, template metadata,
    deterministic generation, CLI strategy validity, and unchanged defaults.
  - [done] Document the strategy in README/NOTES/TODO.
  - [done] Run a bounded CPU-only benchmark against `sparse` and
    `structured`, including at least `target_r=2`, and interpret proxy-only
    results without retuning defaults.
- [done] Add safe offline exact-verifier preparation workflow.
  - [done] Add a preparation-only CLI that reads review-batch directories,
    validates `verification_batch.jsonl`, `verification_coefficients.txt`, and
    `manifest.json`, and refuses malformed coefficient exports.
  - [done] Emit `offline_verification_manifest.json`, `pari_input.gp`,
    `magma_input.m`, and `verification_plan.md` for manual local verifier runs.
  - [done] Probe local PARI/GP and MAGMA availability without installing or
    downloading anything, and record unavailable-tool blockers.
  - [done] Gate any local verifier execution behind explicit opt-in flags,
    keep dry-run/preparation as the default, and never add SAIR/network or
    auto-submission behavior.
  - [done] Add fast fixture-based tests for batch loading, coefficient
    validation, script generation, manifest safety flags, and unavailable
    verifier handling.
  - [done] Document the workflow in README/NOTES/TODO.
  - [done] Smoke it against
    `/tmp/igp24_r4_review_batch_20260704`.
- [done] Add safe human-review tooling for exported shortlists.
  - [done] Add a review/export-only CLI that reads shortlist export
    directories and optionally follows `source_ledger_path` to richer ledger
    records.
  - [done] Support batch size, canonical-hash deduplication, score sorting,
    and source-strategy diversity constraints where possible.
  - [done] Emit `review_report.md`, `verification_batch.jsonl`,
    `verification_coefficients.txt`, and `manifest.json` with source
    shortlist, source ledgers, command, criteria, timestamp, and safety flags.
  - [done] Add fast fixture-based tests covering shortlist loading,
    source-ledger rehydration, diverse top-N selection, output files, and
    proxy-only safety flags.
  - [done] Document the review-batch command and safety boundary in
    README/NOTES/TODO.
  - [done] Run and audit an r4 review-batch smoke export from the existing
    `/tmp/igp24_r4_shortlist_20260704` shortlist.
- [done] Add safe batch export/shortlist helpers for verifier input
  files.
  - [done] Add an export-only CLI that reads benchmark directories and/or
    ledger JSONL files without running MAGMA/PARI/SAIR or network calls.
  - [done] Support target-r filtering, generation-strategy filtering,
    top-N limits, canonical-hash deduplication, and score sorting.
  - [done] Emit an audit manifest, JSONL shortlist, and coefficient export
    suitable for later human-reviewed offline verifier input.
  - [done] Add fast fixture-based tests for filtering, deduplication,
    sorting, manifest creation, and coefficient export shape.
  - [done] Document usage and the safety boundary in README/NOTES/TODO.
  - [done] Run and audit a small r4 shortlist smoke export from existing
    benchmark artifacts.
- [done] Run second direct r4 preset confirmation.
  - [done] Run a fresh disjoint-seed CPU-only `target_r=4` comparison
    across `preset_r4`, `quartic_lift`, `mix_r4_dual_yield`,
    `mix_r4_dual_quality`, `four_real_seed`, and
    `mix_r4_dual_balanced`.
  - [done] Audit return codes, expected summary row count, metadata
    completeness, aggregate fields, and dual-mix ledger metadata.
  - [done] Decide whether `preset_r4` should remain unchanged, retune
    toward `quartic_lift`, or retune to the dual-yield mix.
  - [done] If retuning, update focused tests plus README/NOTES/TODO; if
    not retuning, document the tradeoff and next task.
- [done] Confirm whether `preset_r4` should retune to
  `mix_r4_dual_quality`.
  - [done] Run a larger 12-seed CPU-only `target_r=4` confirmation across
    `preset_r4`, `four_real_seed`, `quartic_lift`, and dual r4 mix labels.
  - [done] Audit return codes, metadata completeness, expected row count,
    and mix metadata in ledgers.
  - [done] Decide whether `mix_r4_dual_quality` clearly beats current
    `preset_r4` on match rate and average score metrics.
  - [done] If evidence is strong, retune `preset_r4`; otherwise document why
    it remains unchanged.
- [done] Test benchmark-only r4 dual-family mixes.
  - [done] Add helper-only labels combining `four_real_seed`,
    `quartic_lift`, and optional sparse diversity.
  - [done] Add focused benchmark-helper tests for dual-mix label
    resolution.
  - [done] Run a bounded CPU-only `target_r=4` comparison against
    `four_real_seed`, `quartic_lift`, `preset_r4`, and the dual labels.
  - [done] Interpret whether any dual mix improves the current r4
    yield/quality tradeoff before changing any preset/default.
- [done] Add a `target_r=4` quartic-lift structured family.
  - [done] Probe bounded quartic-in-`x^6` templates with small perturbations.
  - [done] Implement a distinct `quartic_lift` generation strategy with
    ledger metadata.
  - [done] Add deterministic generation and metadata tests.
  - [done] Benchmark `quartic_lift` against `mixed`, `four_real_seed`, and
    `preset_r4`.
  - [done] Document whether it improves target-r yield, peak proxy score,
    or diversity before changing any preset/default.
- [in_progress] Add more structured polynomial families:
  - [pending] sparse families with fixed support templates,
  - [done] first compositional/tower-style construction:
    `quartic_lift`, a quartic-in-`x^6` family for `target_r=4`,
  - [done] first high-real-root `r=24` local prototype:
    positive quadratic product seeds plus low-odd perturbations, tracked under
    `data/igp24/r24_high_real_probe_20260706`,
  - [done] first high-real-root `r=20` local prototype:
    ten-positive/two-negative quadratic product seeds plus low-odd
    perturbations, tracked under
    `data/igp24/r20_high_real_probe_20260706`,
  - [done] first structure-preserving `r=12` exact-composed prototype:
    degree-12 base perturbations lifted as `g(x^2)`, tracked under
    `data/igp24/r12_structured_probe_20260706`,
  - [done] feedback-aware `r=12` exact-composed follow-up:
    record SAIR labels for the first r12 structured queue, then search nearby
    but structurally distinct `g(x^2)` base perturbation families without
    adding odd `x` powers,
  - [done] first `r=12` degree-6-by-degree-4 exact-composed tower prototype:
    outer degree-6 polynomial composed with `q(x)=x^4-s*x^2`, tracked under
    `data/igp24/r12_tower_probe_20260706`; SAIR accepted the 10-row queue and
    added `24T23883|r=12` plus `24T24651|r=12`,
  - [pending] compositional and tower constructions with degrees multiplying to
    24,
  - [pending] resolvent-inspired families,
  - [pending] solvable or imprimitive group families.
- [pending] Add group metadata and target-family tags without claiming exact
  `24Tt` labels.
- [pending] Add better group-specific modular cycle-type filters.
- [pending] Build PARI and MAGMA wrappers for offline/batched exact checks,
  still outside the training loop.
- [pending] Add safe batch export helpers for verifier input files.

### Stage 3: Verification And Long Runs

- [pending] Consider an optional Rust/PyO3 or multiprocessing verifier bridge.
- [pending] Add batched exact verification workflows for candidates exported
  from the ledger.
- [done] Add credential-safe SAIR Public API helper for label progress,
  submission validation, submission listing, submission reads, and downloads.
  It reads keys from the environment only and defaults submission to dry-run.
- [pending] Add leaderboard-aware target selection using the live SAIR
  `labels/progress` endpoint before each new queue.
- [pending] Run longer generation/training jobs only after short benchmark
  comparisons justify them.
- [pending] Keep SAIR submission explicit and API-gated; never auto-submit
  from training, sampling, proxy scoring, or search hot loops.

### Stage 4: Competition Packaging And Reproducibility

- [pending] Curate a final set of externally verified candidates with exact
  group/signature metadata and verifier provenance.
- [pending] Produce reproducible run manifests for any candidates promoted to
  submission consideration:
  - [pending] source commit,
  - [pending] command line,
  - [pending] random seeds,
  - [pending] environment details,
  - [pending] ledger record hashes,
  - [pending] verifier outputs.
- [pending] Add leaderboard-aware reporting once exact verification exists:
  - [pending] best candidates by target,
  - [pending] discriminant comparisons,
  - [pending] duplicate/canonical-equivalence checks,
  - [pending] rejected-candidate audit trail.
- [pending] Build safe manual submission packaging for SAIR:
  - [pending] export-only by default,
  - [pending] explicit human review checklist,
  - [pending] live API submission only through an explicit `--execute` path,
  - [pending] no API keys in logs or artifacts.
- [pending] Archive benchmark, training, and verification artifacts needed for
  post-competition reproducibility.

## Recommended Next Tasks

- [done] Implement configurable generation strategies and tests.
- [done] Add score component metadata to ledger records.
- [done] Add local-search stats metadata and tests.
- [done] Run and document a short CPU-only generation benchmark.
- [done] Run per-strategy comparisons with equal `gensize` and fixed seeds.
- [done] Run short per-strategy comparisons including target real-root counts.
- [done] Run larger per-strategy target-r comparisons before further tuning
  defaults.
- [done] Add an experimental `target_r=4`-friendlier `four_real_seed`
  generation family.
- [done] Add target-specific benchmark presets or docs for promising
  strategy/target pairs.
- [done] Run a larger `target_r=4` validation with `four_real_seed`,
  `preset_r4`, and tuned target-specific mixes before promoting presets.
- [done] Run a longer focused `target_r=2` comparison between `sparse`,
  `structured`, and the new fixed-support sparse template family.
- [pending] Use fixed-support sparse templates as an opt-in diversity/yield
  probe only; do not promote to defaults or presets without larger proxy runs
  and later exact verifier evidence.
- [done] Run a small GPU training smoke before treating model training as a
  main path; keep CPU proxy-search primary unless CUDA/PyTorch and tiny
  training both work cleanly.
- [in_progress] Run a controlled longer GPU sampler experiment, while keeping CPU
  proxy-search, shortlist export, and exact-tool prep primary until longer GPU
  evidence justifies changing the plan.
- [done] Add one more `target_r=4` structured family before retuning the
  balanced `preset_r4` weights again.
- [done] Run a larger r4 comparison or benchmark-only mix that combines
  `four_real_seed` yield with `quartic_lift` peak proxy quality before changing
  `preset_r4`.
- [done] Run a larger confirmation benchmark centered on
  `mix_r4_dual_quality` before retuning `preset_r4`.
- [done] Run a second confirmation that directly compares `quartic_lift`,
  `mix_r4_dual_yield`, and current `preset_r4` before changing the r4 preset.
- [done] Add safe batch export/shortlist helpers for top proxy candidates
  from the strongest r4 strategies so later offline exact verification can
  inspect them without adding any automatic SAIR submission path.
- [done] Manually review the exported r4 shortlist and choose a small batch
  for offline exact-verifier experiments, keeping any SAIR submission explicit
  and human-controlled.
- [done] Prepare manual offline exact-verifier inputs for
  `/tmp/igp24_r4_review_batch_20260704`, record local tool availability, and
  keep any SAIR submission explicit and human-controlled.
- [pending] Run manual offline exact-verifier experiments only after local
  PARI/MAGMA tooling is available, record verifier provenance and outputs, and
  keep any SAIR submission explicit and human-controlled.
