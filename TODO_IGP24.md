# IGP24 Live TODO

This file is the working project log for the Axplorer-based IGP24 candidate
generator. Keep it current as implementation, tests, smoke runs, and benchmark
results change.

## Current Status

- Branch: `igp24-dev`
- Remote target: `zpconn/igp24-axplorer`
- Last pull: 2026-07-04, `git pull --ff-only` -> already up to date before
  per-run GPU export diversity diagnostic work.
- Active focus: diagnosing and improving per-run fixed-template GPU export
  diversity before any longer fixed-template GPU export. The current plan is
  to add a raw export diversity diagnostic, compare the clean seed `2201`
  against duplicate-heavy seeds `2301`-`2303`, then run two short opt-in
  fixed-template entropy interventions against the known duplicate-heavy
  behavior. Keep CPU proxy-search, shortlist export, and exact-tool prep
  primary. This remains proxy-only: no exact `24Tt` labels, no MAGMA/PARI
  execution, no SAIR/network calls, and no auto-submission behavior.

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
      - Result: added `fixed_template_t10_top32` and
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
    - [pending] Run two short export-only GPU intervention probes, each
      shorter than a 30-60m run and with CPU scoring/local search avoided
      during the GPU phase.
    - [pending] Score only the necessary intervention exports on the CPU
      proxy path with `--score_all true`, `--local_search false`, and
      `--max_local_search_steps 0`.
    - [pending] Compare diagnostics and CPU dedup results against the
      duplicate-heavy fixed-template seeds and produce the next
      recommendation.
    - [pending] Update README, NOTES, and TODO with commands, artifacts,
      metrics, interpretation, and next action.
    - [pending] Run final verification, confirm Stage 4 remains present,
      audit GPU/process state, cleanup generated caches, commit, and push.

## Tests And Checks

- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q`.
  - Latest result: 72 passed in 1.52s after the multi-seed fixed-template
    scale-up work.
- [done] Run focused split/export tests:
  `PYTHONPATH=/tmp/igp24_pydeps python3 -m pytest -q tests/test_igp24_gpu_sampler_probe.py tests/test_igp24_sample_export.py tests/test_igp24_merge_scored_exports.py`.
  - Latest result: 31 passed in 1.08s after the multi-seed fixed-template
    scale-up work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 -m compileall train.py src tests scripts`.
  - Latest result: passed after the multi-seed fixed-template scale-up work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py --help`.
  - Latest result: passed after safe review-batch helper work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py --help`.
  - Latest result: passed after adding the safe review-batch helper.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py --help`.
  - Latest result: passed after adding the safe offline-verifier preparation
    helper.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py --help`.
  - Latest result: passed after short GPU sampler probe work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py --help`.
  - Latest result: passed after GPU readiness smoke work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py --help`.
  - Latest result: passed after the multi-seed fixed-template scale-up work;
    helper exposes `--diversity_seed`.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py --help`.
  - Latest result: passed after the multi-seed fixed-template scale-up work.
- [done] Run `PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py --help`.
  - Latest result: passed after adding the merge helper.
- [done] Run an import check proving `train`, the environment registry,
  `igp24`, and the split/merge helpers remain discoverable.
  - Latest command:
    `PYTHONPATH=/tmp/igp24_pydeps python3 -c "import train; from src.envs import ENVS; import scripts.igp24_score_sample_export as score; import scripts.igp24_gpu_sampler_probe as probe; import scripts.igp24_merge_scored_exports as merge; print('imports ok', 'igp24' in ENVS, hasattr(score, 'build_split_manifest'), hasattr(probe, 'build_sample_export_diversity_command'), hasattr(merge, 'merge_sources'))"`
  - Latest result: `imports ok True True True True`.
- [blocked] Run literal `python -m pytest`, or record the blocker.
  - Latest result: blocked with `/bin/bash: line 1: python: command not found`.
- [done] If local dependency issues block the literal command, record the
  exact blocker and run the closest available equivalent.

## Command Log

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
- [pending] Add leaderboard-aware target selection after exact verification is
  available.
- [pending] Run longer generation/training jobs only after short benchmark
  comparisons justify them.
- [pending] Keep SAIR submission explicit and manual; never auto-submit.

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
  - [pending] no automatic submission path,
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
