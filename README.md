# IGP24 Axplorer

Research scaffold for using Axplorer as a candidate generator for the
[SAIR IGP24 inverse Galois competition](https://competition.sair.foundation/competitions/igp24/overview).

This project generates, scores, locally improves, deduplicates, and exports
monic degree-24 integer polynomials:

```text
f(x) = x^24 + a23*x^23 + ... + a1*x + a0
```

Internally, candidates are represented by the 24 free coefficients:

```text
[a0, a1, ..., a23]
```

Exported candidates append the fixed leading coefficient:

```text
[a0, a1, ..., a23, 1]
```

## Status

This is a candidate generator and proxy scorer. It is not an exact Galois group
verifier.

Exact `24Tt` labels require later verification with external tooling such as
PARI, MAGMA, or SAIR infrastructure. The current modular factorization data is
only proxy evidence.

Current features:

- configurable coefficient generation strategies,
- exact SymPy prefilters for basic polynomial validity,
- proxy score component metadata,
- bounded deterministic local search with telemetry,
- JSONL candidate ledger with canonical hash deduplication,
- dry-run verifier stubs for future PARI, MAGMA, and SAIR integration.

## Setup

Create the environment from `environment.yml`:

```bash
micromamba env create -f environment.yml
micromamba activate env_axplorer
```

If your machine needs a custom PyTorch or CUDA setup, install that separately
for your hardware.

## GPU Smoke

GPU use is for model training and sampling only. The IGP24 scoring, local
search, shortlist export, and offline-verifier preparation paths remain
CPU/proxy workflows unless explicitly changed later.

Run the readiness helper before making GPU training a main path:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_smoke.py \
  --output_dir /tmp/igp24_gpu_smoke_20260704
```

The helper records `nvidia-smi`, PyTorch CUDA availability, a tiny CPU
data-generation baseline, and a tiny GPU-enabled `train.py` run when CUDA is
available. It writes `gpu_smoke_summary.json` and `gpu_smoke_report.md` under
the output directory. Keep CPU proxy-search primary unless that report proves
PyTorch CUDA works and the training log shows `device: cuda`.

Current result on this machine, from 2026-07-04: the RTX 5090 is visible,
PyTorch `2.12.1+cu130` reports CUDA available, the tiny CPU baseline and tiny
GPU training smoke both returned 0, and the GPU train log shows `device: cuda`.
Use GPU training as a parallel sampler path; keep CPU proxy-search, shortlist
export, and exact-tool prep as the main candidate pipeline.

A later short sampler probe generated valid model-sampled proxy candidates, but
live `nvidia-smi` observation showed that path was not meaningfully loading the
GPU. A follow-up train-only utilization probe on 2026-07-04 isolated
GPU-side training from post-epoch sampling/scoring/local search:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode train_only_utilization \
  --output_dir /tmp/igp24_gpu_train_only_probe_20260704 \
  --timeout_seconds 600 \
  --monitor_interval_seconds 1
```

That run completed in 34.1s with `device: cuda`, four finite eval points, max
monitored GPU utilization 95%, average utilization 20.7%, and zero requested
model samples. Conclusion: GPU-sized training can load the RTX 5090; the
earlier sampler path was CPU-bound by scoring/local search. The next GPU step
should decouple GPU training/sampling from CPU scoring before any medium
30-60 minute run.

The first split workflow is now available as an opt-in export path. It trains
and samples on CUDA, then writes unscored model samples without proxy scoring,
local search, or dataset updates:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split \
  --output_dir /tmp/igp24_gpu_sample_export_split_20260704 \
  --timeout_seconds 600 \
  --monitor_interval_seconds 1
```

The 2026-07-04 split smoke completed in 16.8s with `device: cuda`, max
monitored GPU utilization 91%, and 256 decoded unscored sample-export rows at:

```text
/tmp/igp24_gpu_sample_export_split_20260704/gpu_model_sample_export.jsonl
```

Score exported samples later on the CPU proxy path:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_sample_export_split_20260704/gpu_model_sample_export.jsonl \
  --output_dir /tmp/igp24_gpu_sample_export_split_20260704/cpu_scored_export \
  --max_records 64 \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0
```

That CPU handoff smoke scored 64 exported rows, found 56 valid proxy-scored
records and 8 rejected records, with local search disabled. This proves the
split is usable.

The split helper was then hardened so the CPU scoring phase writes a combined
`split_workflow_manifest.json` and `split_workflow_report.md` linking the
export JSONL, GPU probe summary/report, train log, CPU score summary/report,
scored JSONL, source commit, command lines, safety flags, and canonical-hash
dedup counts. Use `--max_records N` for an explicit capped subset, or
`--score_all true` to score all decoded export rows.

The larger short split smoke on 2026-07-04 used:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split \
  --output_dir /tmp/igp24_gpu_sample_export_split_larger_20260704 \
  --timeout_seconds 600 \
  --monitor_interval_seconds 1

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_sample_export_split_larger_20260704/gpu_model_sample_export.jsonl \
  --output_dir /tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export \
  --max_records 512 \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0
```

That run completed the GPU phase in 32.1s with `device: cuda`, no timeout,
max monitored GPU utilization 93%, average utilization 17.5%, max monitored
GPU memory 5457 MiB, and 1024 decoded unscored export rows. The CPU phase
scored a capped 512-row subset in 19.7s, with 450 valid proxy-scored records,
62 rejected records, 512 unique canonical hashes, zero duplicate hash records,
and local search disabled. The combined manifest is at:

```text
/tmp/igp24_gpu_sample_export_split_larger_20260704/cpu_scored_export/split_workflow_manifest.json
```

The follow-up score-all short handoff on 2026-07-04 used:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split \
  --output_dir /tmp/igp24_gpu_sample_export_split_score_all_20260704 \
  --timeout_seconds 600 \
  --monitor_interval_seconds 1

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_sample_export_split_score_all_20260704/gpu_model_sample_export.jsonl \
  --output_dir /tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0
```

That run completed the GPU phase in 32.3s with `device: cuda`, no timeout,
max monitored GPU utilization 94%, average utilization 14.5%, max monitored
GPU memory 5320 MiB, 1024 exported rows, and 1023 decoded rows. The CPU phase
used `selection_mode=all_explicit`, selected all 1024 exported rows, skipped
one undecoded row, scored 1023 rows in 36.7s, and found 908 valid proxy-scored
records, 115 rejected records, 1022 unique canonical hashes, and one duplicate
hash record. The combined manifest is at:

```text
/tmp/igp24_gpu_sample_export_split_score_all_20260704/cpu_scored_export_all/split_workflow_manifest.json
```

The first bounded medium split run on 2026-07-04 used the same export-only
discipline:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_medium \
  --output_dir /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704 \
  --timeout_seconds 3600 \
  --monitor_interval_seconds 5

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/gpu_model_sample_export_medium.jsonl \
  --output_dir /tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0
```

That run completed the GPU phase in 1300.8s with `device: cuda`, no timeout,
max monitored GPU utilization 99.0%, average utilization 96.0%, max monitored
GPU memory 10141 MiB, 8192 exported rows, and 8192 decoded rows. The CPU phase
used `selection_mode=all_explicit`, scored all 8192 rows in 264.6s, and found
8188 valid proxy-scored records, 4 rejected records, 384 unique canonical
hashes, and 7808 duplicate hash records. The combined manifest is at:

```text
/tmp/igp24_gpu_sample_export_split_medium_retuned_20260704/cpu_scored_export_all/split_workflow_manifest.json
```

The follow-up bounded diversity sweep on 2026-07-04 compared two short
export-only variants:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant fixed_template_t09_top9 \
  --output_dir /tmp/igp24_gpu_sample_export_diversity_fixed_20260704 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/gpu_model_sample_export_diversity_fixed_template_t09_top9.jsonl \
  --output_dir /tmp/igp24_gpu_sample_export_diversity_fixed_20260704/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant mixed_t12_open_topk \
  --output_dir /tmp/igp24_gpu_sample_export_diversity_mixed_20260704 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/gpu_model_sample_export_diversity_mixed_t12_open_topk.jsonl \
  --output_dir /tmp/igp24_gpu_sample_export_diversity_mixed_20260704/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0
```

Both GPU phases loaded the RTX 5090 well: max monitored utilization 99%, about
80% average utilization, and about 10.3 GiB monitored memory. The fixed-template
short variant scored 2047 rows in 76.5s with 1799 valid records, 2039 unique
canonical hashes, and only 8 duplicate hash records. The mixed/high-temperature
variant scored 2030 rows in 77.7s with 1921 valid records, 1067 unique
canonical hashes, and 963 duplicate hash records.

Recommendation: use the diversity sweep before any longer GPU export. The
short fixed-template shape is promising for uniqueness, while the
mixed/high-temperature shape is better for validity and proxy score but
duplicates more. Do not switch back to an integrated GPU train/sample/score
loop; keep CPU proxy-search, shortlist export, and exact-tool prep as the main
pipeline.

The next multi-seed fixed-template check added `--diversity_seed` to the
diversity helper and a merge helper for scored export directories. The three
bounded GPU export-only commands were:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant fixed_template_t09_top9 \
  --diversity_seed 2301 \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant fixed_template_t09_top9 \
  --diversity_seed 2302 \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant fixed_template_t09_top9 \
  --diversity_seed 2303 \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2
```

The matching CPU score-all handoffs used local search disabled:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2301.jsonl \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2302.jsonl \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_score_sample_export.py \
  /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/gpu_model_sample_export_diversity_fixed_template_t09_top9_seed2303.jsonl \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all \
  --score_all true \
  --coeff_bound 4 \
  --prime_limit 11 \
  --exact_score_timeout 2 \
  --local_search false \
  --max_local_search_steps 0
```

Merge scored export directories with:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_merge_scored_exports.py \
  /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2301/cpu_scored_export_all \
  /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2302/cpu_scored_export_all \
  /tmp/igp24_gpu_multiseed_fixed_template_20260704/seed2303/cpu_scored_export_all \
  --output_dir /tmp/igp24_gpu_multiseed_fixed_template_20260704/merged_dedup_review \
  --top_n 25
```

All three GPU phases used CUDA, avoided GPU-phase CPU scoring/local search, and
hit 99% max monitored GPU utilization. Seed `2301` also showed about 98% live
GPU utilization and 10.9 GiB in use in `nvidia-smi`.

| seed | gpu_s | decoded | cpu_s | valid | rejected | unique_hashes | dup_hash_records | best | mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2301 | 150.6 | 2040 | 70.7 | 1881 | 159 | 1132 | 908 | 9955.382 | 9150.606 |
| 2302 | 152.2 | 2047 | 64.3 | 2031 | 16 | 452 | 1595 | 9951.923 | 9845.475 |
| 2303 | 148.3 | 2043 | 69.4 | 1983 | 60 | 772 | 1271 | 9954.908 | 9630.741 |

The merged dedup review scored 6130 rows, found 5895 valid records, 235
rejected records, 2356 unique canonical hashes, and 3774 duplicate hash
records. Pairwise cross-seed overlap was zero for all seed pairs. That means
multi-seed fixed-template export adds fresh canonical hashes and beats the
duplicate-heavy medium baseline on unique count, but per-seed diversity is
unstable. The earlier seed `2201` short fixed-template run remains the
cleanest single short export at 2039 unique hashes out of 2047 scored rows.

The follow-up per-run diagnostic added a raw export diversity helper:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_export_diversity_diagnostic.py \
  EXPORT_1.jsonl EXPORT_2.jsonl \
  --labels run1 run2 \
  --output_dir /tmp/igp24_export_diversity_diagnostic_20260704/example \
  --checkpoint_interval 256 \
  --top_n 10
```

This helper reads model sample-export JSONL files before CPU scoring and
reports decoded rows, exact coefficient uniqueness, translation-canonical hash
uniqueness, token-sequence uniqueness, top duplicate groups, per-batch counts,
and checkpoint trajectories. It does not score candidates, run local search,
call exact verifiers, call SAIR/network APIs, or submit anything.

On the existing fixed-template exports, the diagnostic showed that duplicate
collapse was already present in raw token/coefficient output: seed `2302` had
452 unique exact coefficient vectors out of 2047 decoded rows, matching its
452 canonical hashes after CPU scoring. It was not mainly a
translation-canonicalization artifact.

Two opt-in fixed-template entropy interventions were then compared on the same
duplicate-heavy seed `2302`:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant fixed_template_t10_top12 \
  --diversity_seed 2302 \
  --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/t10_top12_seed2302 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2

PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_diversity \
  --diversity_variant fixed_template_t11_open_topk \
  --diversity_seed 2302 \
  --output_dir /tmp/igp24_gpu_export_entropy_interventions_20260704/t11_open_seed2302 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2
```

Both GPU phases used CUDA, avoided GPU-phase CPU scoring/local search, and hit
99% max monitored GPU utilization. A preliminary `top_k=32` variant was
discarded because it exceeded the tokenizer vocabulary and failed at
`torch.topk`; use `fixed_template_t10_top12` for the bounded top-k variant.

| variant | scored | valid | rejected | unique_hashes | dup_hash_records | best | mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline t09 top9 | 2047 | 2031 | 16 | 452 | 1595 | 9951.923 | 9845.475 |
| t10 top12 | 2041 | 1888 | 153 | 1288 | 753 | 9953.439 | 9177.150 |
| t11 open top-k | 2043 | 1833 | 210 | 2030 | 13 | 9956.519 | 8900.449 |

The follow-up `fixed_template_t11_open_topk` multi-seed validation used fresh
seeds `2401`, `2402`, and `2403` with the same export-only discipline and raw
diagnostics after each export. All three GPU exports loaded CUDA and avoided
GPU-phase CPU scoring/local search/dataset updates.

| seed | gpu_s | max/avg gpu util | decoded | raw unique | raw dupes | scored | valid | rejected | best | mean |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2401 | 156.4 | 99.0% / 82.7% | 2043 | 675 | 1368 | skipped | - | - | - | - |
| 2402 | 154.5 | 99.0% / 82.7% | 2037 | 1217 | 820 | 2037 | 1910 | 127 | 9958.729 | 9301.895 |
| 2403 | 147.8 | 99.0% / 81.8% | 2026 | 1088 | 938 | 2026 | 1913 | 113 | 9952.131 | 9367.702 |

The merged scored review across `seed2201_t09_clean`,
`seed2302_t09_baseline`, `seed2302_t11_open`, `seed2402_t11_open`, and
`seed2403_t11_open` found 10200 scored rows, 9486 valid records, 6822 unique
canonical hashes, 3378 duplicate hash records, and only four cross-seed shared
hashes. The best overall proxy score remained from `seed2201_t09_clean`
at 9964.435; the best fresh `t11_open` result was seed `2402` at 9958.729.
The report is:

```text
/tmp/igp24_gpu_t11_open_multiseed_20260704/merged_scored_review/merged_dedup_report.md
```

Recommendation: do not start a longer fixed-template run yet.
`fixed_template_t11_open_topk` can work very well on some seeds, but it is not
stable enough across fresh seeds. The best next code change is a dedup-aware
export cap/stop policy or live uniqueness monitor, since duplicate collapse is
visible before CPU scoring.

The dedup-aware export control is now available as an opt-in mode. Defaults are
unchanged. When enabled, the export path tracks decoded coefficient tuples,
writes only first-seen decoded tuples, skips repeated decoded tuples, and stops
when either the unique target or attempt budget is reached. It still does not
score candidates, run local search, call exact verifiers, call SAIR/network
APIs, or submit anything.

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_dedup \
  --diversity_variant fixed_template_t11_open_topk \
  --diversity_seed 2401 \
  --dedup_unique_target 512 \
  --dedup_max_attempts 2048 \
  --dedup_progress_interval 128 \
  --output_dir /tmp/igp24_gpu_dedup_export_20260704/seed2401 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2
```

The underlying `train.py` flags are:

```text
--sample_export_dedup true
--sample_export_unique_target 512
--sample_export_max_attempts 2048
--sample_export_progress_interval 128
```

For a dedup-aware export, inspect both the export JSONL and its sidecar summary:

```text
EXPORT.jsonl
EXPORT.jsonl.summary.json
```

Important summary fields are `attempted_samples`, `records_written`,
`unique_decoded_coefficients`, `duplicate_decoded_records_skipped`, and
`stop_reason`. A good short smoke should show `stop_reason=unique_target_reached`
or a clear `attempt_budget_exhausted` result with fewer duplicate rows written
than the raw diagnostic would otherwise report.

The first bounded dedup-aware smoke used duplicate-heavy
`fixed_template_t11_open_topk` seed `2401` with target 512 and budget 2048. It
completed in 147.2s on CUDA, reached the unique target after 1439 attempts,
wrote 516 rows, decoded 512 rows, skipped 923 duplicate decoded attempts, and
recorded `stop_reason=unique_target_reached`. The raw diagnostic found 512
exact/canonical/token uniques and zero duplicate records. CPU score-all with
local search disabled scored 512 rows, found 501 valid records, 11 rejected
records, 512 unique hashes, zero duplicate hash records, best score 9954.661,
and mean score 9708.264. This confirms the opt-in control reduces duplicate
export waste on the known bad seed without changing exact-tool or submission
safety.

The larger 1024-unique validation used the same dedup-aware mode with a
4096-attempt budget on seeds `2401` and `2402`:

| seed | attempts | written | decoded | duplicate skipped | stop reason | valid | rejected | best | mean |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 2401 | 1219 | 1036 | 1024 | 183 | unique_target_reached | 909 | 115 | 9952.933 | 8807.756 |
| 2402 | 3255 | 1026 | 1024 | 2229 | unique_target_reached | 953 | 71 | 9966.150 | 9233.465 |

Both written exports had 1024 exact/canonical/token uniques and zero duplicate
records in the raw diagnostic and CPU-scored output. Seed `2402` was much less
attempt-efficient but found the best merged proxy score in this comparison.
Recommendation: a later medium dedup-aware run is justified only as another
bounded target/budget experiment with stop-reason auditing, not as an unbounded
longer fixed-template run.

A bounded 1536-unique stress test on seed `2402` used the same export-only
dedup path with an 8192-attempt budget and a 1200-second timeout:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_gpu_sampler_probe.py \
  --probe_mode sample_export_split_dedup \
  --diversity_variant fixed_template_t11_open_topk \
  --diversity_seed 2402 \
  --dedup_unique_target 1536 \
  --dedup_max_attempts 8192 \
  --dedup_progress_interval 512 \
  --output_dir /tmp/igp24_gpu_dedup_medium_20260704/seed2402 \
  --timeout_seconds 1200 \
  --monitor_interval_seconds 2
```

It stayed on CUDA and loaded the GPU well, but exhausted the attempt budget:
8192 attempts, 1049 rows written, 1040 decoded/unique rows, 9 invalid decodes,
7143 duplicate decoded attempts skipped, and
`stop_reason=attempt_budget_exhausted`. The raw diagnostic still found zero
exact/canonical/token duplicate records in the written export, and CPU
score-all with local search disabled scored 1040 rows with 952 valid, 88
rejected, 1040 unique hashes, best score 9958.729, and mean score 9081.130.

Conclusion: the 1536 target is not a good next single-seed target for
duplicate-heavy seed `2402` under this bounded budget. Prefer several bounded
smaller dedup-aware seeds, or change sampler diversity, before trying another
larger single-seed target.

A follow-up bounded multi-seed check used fresh
`fixed_template_t11_open_topk` seeds `2404` and `2405` at target 1024 with a
4096-attempt budget. Both reached the target with clean written exports:

| seed | attempts | written | decoded | duplicate skipped | stop reason | valid | rejected | best | mean |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 2404 | 1027 | 1027 | 1024 | 0 | unique_target_reached | 917 | 107 | 9963.747 | 8883.004 |
| 2405 | 1611 | 1030 | 1024 | 581 | unique_target_reached | 929 | 95 | 9950.674 | 9000.689 |

An optional seed `2406` was run because the first two were clean and
GPU-bound. It exhausted the 4096-attempt budget at 852 uniques after skipping
3234 duplicate decoded attempts, but the partial export was still
zero-duplicate and scored 794 valid / 58 rejected with best/mean scores
9963.539 / 9246.803.

The two required seeds added 2046 net unique canonical hashes from 2048 scored
rows over the prior seven-source review; including seed `2406` added 2898 net
unique hashes from 2900 scored rows. Recommendation: bounded smaller multi-seed
dedup exports are the better immediate coverage path than another larger
single-seed target. Continue with a few more bounded fresh seeds or add a seed
triage/diversity diagnostic before spending longer runs on duplicate-heavy
seeds.

Before spending a full 1024-unique export on a fresh seed, run the cheap
dedup-aware seed triage helper:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_seed_triage.py \
  --seeds 2404 2405 2406 2402 \
  --output_dir /tmp/igp24_seed_triage_20260705 \
  --unique_target 256 \
  --max_attempts 1024 \
  --progress_interval 128 \
  --timeout_seconds 900 \
  --monitor_interval_seconds 2
```

The calibrated target-256 probe promotes only very clean seeds, rejects clear
early duplicate pressure, and marks the gray zone ambiguous. On known outcomes
it promoted productive seeds `2404` and `2405`, rejected duplicate-heavy
`2406`, and marked duplicate-heavy larger-target seed `2402` ambiguous instead
of falsely promoting it. Treat ambiguous seeds as needing an intermediate
512-unique dedup probe before any full 1024-unique export.

## Run A Small Smoke Job

```bash
python train.py \
  --env_name igp24 \
  --exp_name igp24_smoke \
  --coeff_bound 10 \
  --gensize 100 \
  --pop_size 20 \
  --data_generation_only true \
  --always_search true \
  --max_local_search_steps 20 \
  --igp24_generation_strategy mixed \
  --igp24_sparse_terms 4 \
  --igp24_low_height_bound 3 \
  --cpu true
```

Useful IGP24-specific generation flags:

```text
--igp24_generation_strategy mixed
--igp24_generation_preset none
--igp24_sparse_terms 4
--igp24_low_height_bound 3
--igp24_mixed_strategy_weights uniform:0.10,low_height:0.20,sparse:0.25,lower_degree:0.20,structured:0.25,four_real_seed:0.00,quartic_lift:0.00,fixed_sparse_template:0.00
```

`--igp24_generation_strategy` can be `mixed`, `uniform`, `low_height`,
`sparse`, `lower_degree`, `structured`, `four_real_seed`, or
`quartic_lift`, or `fixed_sparse_template`.

The strategies are:

- `uniform`: dense coefficients sampled from the full search box.
- `low_height`: dense coefficients sampled from a smaller inner box.
- `sparse`: a configurable number of nonzero free coefficients.
- `lower_degree`: coefficients biased toward low-degree terms.
- `structured`: simple sparse binomial/trinomial-like seeds.
- `four_real_seed`: an experimental `target_r=4`-oriented near-product seed
  with small odd perturbations.
- `quartic_lift`: an experimental `target_r=4`-oriented quartic-in-`x^6`
  seed with small off-support perturbations.
- `fixed_sparse_template`: an opt-in sparse family that chooses from a small
  hand-auditable set of fixed coefficient supports before sampling bounded
  nonzero coefficients.
- `mixed`: a weighted mix of the above.

The default `mixed` weights keep `four_real_seed`, `quartic_lift`, and
`fixed_sparse_template` at zero weight. Use them explicitly when running
targeted experiments.

Target-specific presets are opt-in with `--igp24_generation_preset`. The
default `none` preserves the explicit strategy and weight settings. Available
presets are:

- `r0`: use `structured` generation.
- `r2`: use a sparse/structured mixed strategy.
- `r4`: use a `four_real_seed`/sparse mixed strategy.

Ledger records include the preset name, target-r intent, resolved strategy, and
resolved mixed weights.

Candidate records are written as JSONL by default:

```text
data/igp24/candidates.jsonl
```

Each ledger record includes exported coefficients, polynomial metadata, score
components, generation metadata, local-search metadata, and verification status.
Records remain proxy-scored unless an external verifier is used later.

## Compare Generation Strategies

Use the benchmark helper for short, reproducible CPU-only comparisons:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies uniform,low_height,sparse,lower_degree,structured,mixed \
  --seeds 101,102 \
  --target_rs none \
  --coeff_bound 4 \
  --gensize 12 \
  --pop_size 6 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 3 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_strategy_bench
```

The helper runs `train.py`, writes per-run ledgers under the output directory,
and produces `summary.json`, `summary.jsonl`, and `aggregate_summary.json`.
These include valid-candidate counts, ledger counts, scores, runtimes, strategy
mix, target-r match rates, and local-search acceptance statistics.

To compare target real-root counts, pass one or more targets with `--target_rs`.
Use `none` for untargeted runs:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies sparse,structured,mixed \
  --seeds 301,302,303,304 \
  --target_rs none,0,2,4 \
  --coeff_bound 4 \
  --gensize 18 \
  --pop_size 8 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 4 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_target_r_bench_larger
```

Target-r summaries include match counts, match rates, and best matching scores
when a target is supplied. The aggregate summary groups repeated seeds by
strategy and target.

For a focused `target_r=4` comparison, include the experimental strategy
or the `r4` preset explicitly:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_benchmark.py \
  --strategies mixed,four_real_seed,preset_r4,quartic_lift \
  --seeds 501,502,503,504 \
  --target_rs 4 \
  --coeff_bound 4 \
  --gensize 18 \
  --pop_size 8 \
  --ntest 2 \
  --gen_batch_size 2 \
  --max_local_search_steps 4 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --output_dir /tmp/igp24_r4_preset_bench
```

The benchmark helper also accepts r4 mix labels for tuning experiments:

- `mix_r4_yield`: `four_real_seed:1.0`
- `mix_r4_balanced`: `four_real_seed:0.8,sparse:0.2`
- `mix_r4_diverse`: `four_real_seed:0.6,sparse:0.4`
- `mix_r4_dual_yield`: `four_real_seed:0.75,quartic_lift:0.25`
- `mix_r4_dual_quality`: `four_real_seed:0.25,quartic_lift:0.75`
- `mix_r4_dual_balanced`: `four_real_seed:0.45,quartic_lift:0.45,sparse:0.10`

These labels are benchmark-only conveniences. Use `preset_r4` for the actual
opt-in generation preset, `four_real_seed` directly when r4 yield is the main
priority, or the dual labels to compare `four_real_seed` yield with
`quartic_lift` peak proxy quality.

For fixed-support sparse experiments, include `fixed_sparse_template` directly
in `--strategies`, for example alongside `sparse` and `structured` for
`target_r=2` comparisons.

## Export Proxy Shortlists

Use the shortlist helper to collect top proxy-scored candidates from existing
benchmark directories or ledger JSONL files:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_shortlist.py \
  /tmp/igp24_r4_second_confirm_20260704 \
  /tmp/igp24_r4_dual_quality_confirm_20260704 \
  --target_r 4 \
  --limit 25 \
  --output_dir /tmp/igp24_r4_shortlist
```

The helper writes `shortlist.jsonl`, `coefficients.json`,
`coefficients.txt`, and `manifest.json`. It is export-only: it does not run
PARI, MAGMA, SAIR, network calls, exact group verification, or submission.
Treat every exported candidate as proxy-scored until a human-reviewed offline
exact verifier confirms it.

## Review A Shortlist

Use the review helper to turn a proxy shortlist into a small manual review
batch for later offline verifier experiments:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_review_shortlist.py \
  /tmp/igp24_r4_shortlist_20260704 \
  --batch_size 8 \
  --min_strategies 2 \
  --per_strategy_cap 6 \
  --output_dir /tmp/igp24_r4_review_batch
```

The helper writes `review_report.md`, `verification_batch.jsonl`,
`verification_coefficients.txt`, and `manifest.json`. It may follow recorded
`source_ledger_path` values to enrich records, but it still only reads and
writes local files. It does not run exact verifiers or submit anything.

## Prepare Offline Verification

Use the offline verification helper to validate a review batch, candidate
JSONL, or coefficient text file. By default it is a dry run: it writes manual
PARI/GP and MAGMA input files plus per-candidate MAGMA scripts and result
artifacts, but it does not execute MAGMA unless explicitly requested.

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_r4_review_batch_20260704 \
  --output_dir /tmp/igp24_r4_offline_verify \
  --max_records 3 \
  --timeout_seconds 5
```

It writes `offline_verification_manifest.json`, `pari_input.gp`,
`magma_input.m`, `verification_plan.md`, `magma_verification_results.jsonl`,
`magma_verification_summary.json`, `magma_verification_report.md`,
`magma_verification_cache.json`, and per-candidate scripts/raw-output
directories. Each result row records one exact-verification status, such as
`dry_run`, `unavailable`, `timeout`, `parse_error`, `invalid_input`, or
`verified`. Proxy-only labels remain separate from exact `verified_group_label`
values.

MAGMA discovery checks PATH, an explicit `--magma_executable` path, a bounded
set of common local install locations such as `/usr/local/bin/magma`,
`/opt/magma*/magma`, and `~/magma*/magma`, plus any extra
`--magma_search_path` file or glob patterns. The summary and report record
which paths were checked, whether a runnable binary was found, and the exact
rerun command to use once MAGMA is installed or added to PATH.

To run local MAGMA on a very small batch, first confirm the tool is installed,
then use an explicit timeout-bound command:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_r4_review_batch_20260704 \
  --output_dir /tmp/igp24_r4_magma_verify_small \
  --run_magma \
  --max_records 3 \
  --timeout_seconds 30
```

If MAGMA lives outside the default locations, pass it directly:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_r4_review_batch_20260704 \
  --output_dir /tmp/igp24_r4_magma_verify_small \
  --run_magma \
  --magma_executable /path/to/magma \
  --max_records 3 \
  --timeout_seconds 30
```

If local MAGMA is unavailable, the helper can prepare a manual free-online
Magma calculator handoff. This mode writes one copy/paste script per selected
candidate plus a JSONL template for pasting returned output. It does not submit
requests to the online calculator and should not be used for automated batches.
Use repeated `--candidate_hash` values when the exact-verification queue should
pick a deliberate non-contiguous set from a review batch, for example to keep
the highest proxy-score candidates while also including strategy coverage.

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_r4_review_batch_20260704 \
  --output_dir /tmp/igp24_online_magma_manual_20260705 \
  --max_records 3 \
  --timeout_seconds 5 \
  --online_magma_manual \
  --candidate_hash 70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb
```

After manually pasting one generated script into the calculator and saving the
returned output, parse it with:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 scripts/igp24_offline_verify.py \
  /tmp/igp24_r4_review_batch_20260704 \
  --output_dir /tmp/igp24_online_magma_manual_20260705 \
  --max_records 3 \
  --timeout_seconds 5 \
  --online_magma_manual \
  --online_magma_pasted_output data/igp24/online_magma_manual_output_70a542863f79_20260705.xml
```

The observed free calculator constraints are a 60 second runtime cap, 50000
byte input limit, and Magma V2.29-8. The first manual probe recorded candidate
`70a542863f79ad17cf1a61789241eae078e6984669278e551f7015795d2f03cb` as
degree 24, irreducible, and `24T25000` with group text
`Symmetric group G acting on a set of cardinality 24`; the calculator-reported
runtime was 0.420s. Treat this as manually pasted exact-verifier provenance,
separate from proxy labels and separate from local MAGMA availability.

MAGMA is never called from `train.py`, GPU sampling, or CPU proxy scoring.
SAIR submission and network calls remain out of scope.

## Recent Smoke Result

The current smoke run used CPU-only mixed generation:

```bash
PYTHONPATH=/tmp/igp24_pydeps python3 train.py \
  --env_name igp24 \
  --exp_name igp24_stage1_mixed_smoke \
  --dump_path /tmp/igp24_stage1_smoke \
  --seed 123 \
  --coeff_bound 4 \
  --gensize 12 \
  --pop_size 6 \
  --ntest 2 \
  --gen_batch_size 2 \
  --data_generation_only true \
  --always_search true \
  --max_local_search_steps 3 \
  --prime_limit 11 \
  --exact_score_timeout 3 \
  --process_pool false \
  --num_workers 1 \
  --cpu true \
  --igp24_generation_strategy mixed \
  --igp24_sparse_terms 4 \
  --igp24_low_height_bound 2 \
  --igp24_ledger_path /tmp/igp24_stage1_mixed_candidates.jsonl
```

Result: 12 valid generated examples, best score `9943.432289451468`, and
metadata present on all ledger records. See `TODO_IGP24.md` for the live command
log and benchmark notes.

## Run Tests

```bash
python -m pytest
```

The tests cover polynomial construction, export format, exact utility checks,
generation strategies, proxy scoring, local-search determinism and telemetry,
ledger deduplication, verifier stubs, and environment registration.

## Main Files

- `src/envs/igp24.py`: Axplorer environment and coefficient tokenizer.
- `src/igp24/polynomial.py`: exact polynomial utilities and proxy scoring.
- `src/igp24/ledger.py`: JSONL candidate ledger.
- `src/igp24/verifiers/`: PARI, MAGMA, and SAIR stubs.
- `NOTES_IGP24.md`: architecture notes and scoring/generation rationale.
- `TODO_IGP24.md`: live project log, task status, commands, and benchmark notes.

## License

This fork follows the upstream Axplorer license. See `LICENSE`.
