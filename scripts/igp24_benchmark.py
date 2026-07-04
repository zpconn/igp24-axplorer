#!/usr/bin/env python3
"""Run short CPU-only IGP24 generation benchmarks through train.py.

The helper intentionally exercises the real Axplorer CLI instead of duplicating
the generation loop. It keeps all benchmark artifacts under the requested
output directory and summarizes JSONL ledger metadata after each run.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_STRATEGIES = ["uniform", "low_height", "sparse", "lower_degree", "structured", "four_real_seed", "mixed"]
DEFAULT_PRESETS = ["none", "r0", "r2", "r4"]
MIXED_VARIANT_WEIGHTS = {
    "mix_r4_yield": "four_real_seed:1.0",
    "mix_r4_balanced": "four_real_seed:0.8,sparse:0.2",
    "mix_r4_diverse": "four_real_seed:0.6,sparse:0.4",
}


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_int_csv(value: str) -> list[int]:
    return [int(item) for item in _parse_csv(value)]


def parse_target_rs(value: str) -> list[int | None]:
    targets: list[int | None] = []
    for item in _parse_csv(value):
        lowered = item.lower()
        if lowered in {"none", "null", "untargeted", "-"}:
            targets.append(None)
        else:
            targets.append(int(item))
    return targets


def resolve_benchmark_strategy(label: str) -> tuple[str, str, str | None]:
    if label.startswith("preset_"):
        preset = label.removeprefix("preset_")
        if preset not in DEFAULT_PRESETS or preset == "none":
            raise ValueError(f"unknown generation preset strategy label: {label}")
        return "mixed", preset, None
    if label in MIXED_VARIANT_WEIGHTS:
        return "mixed", "none", MIXED_VARIANT_WEIGHTS[label]
    if label not in DEFAULT_STRATEGIES:
        raise ValueError(f"unknown strategy: {label}")
    return label, "none", None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def summarize_records(records: list[dict[str, Any]], target_r: int | None = None) -> dict[str, Any]:
    scores = [float(record["score"]) for record in records if record.get("score") is not None]
    strategies = Counter(record.get("generation_metadata", {}).get("strategy", "missing") for record in records)
    local_attempted = 0
    local_accepted = 0
    local_records = 0
    for record in records:
        stats = record.get("local_search_metadata") or {}
        attempted = int(stats.get("attempted") or 0)
        accepted = int(stats.get("accepted") or 0)
        if attempted or accepted:
            local_records += 1
        local_attempted += attempted
        local_accepted += accepted

    best_record = max(records, key=lambda record: float(record.get("score", float("-inf"))), default=None)
    matching_records = []
    if target_r is not None:
        matching_records = [record for record in records if record.get("real_root_count") == target_r]
    matching_scores = [float(record["score"]) for record in matching_records if record.get("score") is not None]
    return {
        "ledger_records": len(records),
        "best_score": max(scores) if scores else None,
        "mean_score": statistics.fmean(scores) if scores else None,
        "median_score": statistics.median(scores) if scores else None,
        "target_r": target_r,
        "target_r_match_count": len(matching_records) if target_r is not None else None,
        "target_r_match_rate": (len(matching_records) / len(records)) if target_r is not None and records else None,
        "best_matching_score": max(matching_scores) if matching_scores else None,
        "strategy_mix": dict(sorted(strategies.items())),
        "local_search_attempted": local_attempted,
        "local_search_accepted": local_accepted,
        "local_search_records": local_records,
        "best_hash": best_record.get("canonical_hash") if best_record else None,
        "best_generation_strategy": best_record.get("generation_metadata", {}).get("strategy") if best_record else None,
        "metadata_complete": all(
            "score_components" in record and "generation_metadata" in record and "local_search_metadata" in record for record in records
        )
        if records
        else False,
    }


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def aggregate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate per-run benchmark rows by strategy and target real-root count."""

    groups: dict[tuple[str, int | None], list[dict[str, Any]]] = {}
    for result in results:
        key = (str(result["strategy"]), result.get("target_r"))
        groups.setdefault(key, []).append(result)

    aggregated = []
    for (strategy, target_r), rows in sorted(groups.items(), key=lambda item: (item[0][0], _target_label(item[0][1]))):
        attempted = sum(int(row.get("local_search_attempted") or 0) for row in rows)
        accepted = sum(int(row.get("local_search_accepted") or 0) for row in rows)
        best_scores = [float(row["best_score"]) for row in rows if row.get("best_score") is not None]
        best_matching_scores = [float(row["best_matching_score"]) for row in rows if row.get("best_matching_score") is not None]
        mean_scores = [float(row["mean_score"]) for row in rows if row.get("mean_score") is not None]
        match_rates = [float(row["target_r_match_rate"]) for row in rows if row.get("target_r_match_rate") is not None]
        match_total = (
            sum(int(row.get("target_r_match_count") or 0) for row in rows)
            if target_r is not None
            else None
        )
        aggregated.append(
            {
                "strategy": strategy,
                "target_r": target_r,
                "runs": len(rows),
                "avg_runtime_seconds": _mean([float(row["runtime_seconds"]) for row in rows]),
                "valid_candidates_total": sum(int(row.get("valid_candidates") or 0) for row in rows),
                "ledger_records_total": sum(int(row.get("ledger_records") or 0) for row in rows),
                "target_r_match_total": match_total,
                "avg_match_rate": _mean(match_rates),
                "avg_best_score": _mean(best_scores),
                "avg_best_matching_score": _mean(best_matching_scores),
                "avg_mean_score": _mean(mean_scores),
                "best_score": max(best_scores) if best_scores else None,
                "local_search_acceptance": (accepted / attempted) if attempted else 0.0,
                "all_returncode_zero": all(int(row.get("returncode") or 0) == 0 for row in rows),
                "metadata_complete": all(bool(row.get("metadata_complete")) for row in rows),
            }
        )
    return aggregated


def parse_valid_examples(output: str) -> int | None:
    matches = re.findall(r"Valid examples:\s*(\d+)", output)
    if not matches:
        return None
    return int(matches[-1])


def _target_label(target_r: int | None) -> str:
    return "untargeted" if target_r is None else f"r{target_r}"


def run_one(args: argparse.Namespace, strategy: str, seed: int, target_r: int | None = None) -> dict[str, Any]:
    resolved_strategy, generation_preset, mixed_weights_override = resolve_benchmark_strategy(strategy)
    mixed_strategy_weights = mixed_weights_override or args.mixed_strategy_weights
    run_name = f"{strategy}_{_target_label(target_r)}_seed_{seed}"
    run_dir = args.output_dir / run_name
    ledger_path = run_dir / "candidates.jsonl"
    dump_path = run_dir / "dump"
    run_dir.mkdir(parents=True, exist_ok=True)
    if ledger_path.exists():
        ledger_path.unlink()
    if dump_path.exists():
        shutil.rmtree(dump_path)

    cmd = [
        sys.executable,
        "train.py",
        "--env_name",
        "igp24",
        "--exp_name",
        f"igp24_bench_{strategy}_{seed}",
        "--dump_path",
        str(dump_path),
        "--seed",
        str(seed),
        "--coeff_bound",
        str(args.coeff_bound),
        "--gensize",
        str(args.gensize),
        "--pop_size",
        str(args.pop_size),
        "--ntest",
        str(args.ntest),
        "--gen_batch_size",
        str(args.gen_batch_size),
        "--data_generation_only",
        "true",
        "--always_search",
        str(args.always_search).lower(),
        "--max_local_search_steps",
        str(args.max_local_search_steps),
        "--prime_limit",
        str(args.prime_limit),
        "--exact_score_timeout",
        str(args.exact_score_timeout),
        "--process_pool",
        "false",
        "--num_workers",
        "1",
        "--cpu",
        "true",
        "--igp24_generation_strategy",
        resolved_strategy,
        "--igp24_generation_preset",
        generation_preset,
        "--igp24_sparse_terms",
        str(args.sparse_terms),
        "--igp24_low_height_bound",
        str(args.low_height_bound),
        "--igp24_mixed_strategy_weights",
        mixed_strategy_weights,
        "--igp24_ledger_path",
        str(ledger_path),
    ]
    if target_r is not None:
        cmd.extend(["--target_r", str(target_r)])

    start = time.perf_counter()
    completed = subprocess.run(cmd, cwd=args.repo_root, text=True, capture_output=True, check=False)
    elapsed = time.perf_counter() - start
    records = read_jsonl(ledger_path)
    summary = summarize_records(records, target_r=target_r)
    result: dict[str, Any] = {
        "strategy": strategy,
        "resolved_generation_strategy": resolved_strategy,
        "generation_preset": generation_preset,
        "mixed_strategy_weights_override": mixed_weights_override,
        "seed": seed,
        "target_r": target_r,
        "coeff_bound": args.coeff_bound,
        "gensize": args.gensize,
        "local_search_steps": args.max_local_search_steps,
        "runtime_seconds": elapsed,
        "returncode": completed.returncode,
        "valid_candidates": parse_valid_examples(completed.stdout + "\n" + completed.stderr),
        "ledger_path": str(ledger_path),
        "command": cmd,
        "stdout_tail": completed.stdout.splitlines()[-20:],
        "stderr_tail": completed.stderr.splitlines()[-20:],
        **summary,
    }
    return result


def write_outputs(results: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    aggregate_path = output_dir / "aggregate_summary.json"
    aggregate_path.write_text(json.dumps(aggregate_results(results), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    jsonl_path = output_dir / "summary.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")


def print_table(results: list[dict[str, Any]]) -> None:
    print(
        "strategy\ttarget_r\tseed\treturncode\truntime_s\tvalid_candidates\tledger_records\t"
        "target_matches\tmatch_rate\tbest_score\tbest_matching_score\tmean_score\tlocal_acceptance"
    )
    for result in results:
        attempted = int(result.get("local_search_attempted") or 0)
        accepted = int(result.get("local_search_accepted") or 0)
        acceptance = (accepted / attempted) if attempted else 0.0
        best_score = result.get("best_score")
        best_matching_score = result.get("best_matching_score")
        mean_score = result.get("mean_score")
        best_score_text = f"{best_score:.6f}" if best_score is not None else "NA"
        best_matching_score_text = f"{best_matching_score:.6f}" if best_matching_score is not None else "NA"
        mean_score_text = f"{mean_score:.6f}" if mean_score is not None else "NA"
        match_rate = result.get("target_r_match_rate")
        match_rate_text = f"{match_rate:.3f}" if match_rate is not None else "NA"
        target_text = _target_label(result.get("target_r"))
        print(
            f"{result['strategy']}\t{target_text}\t{result['seed']}\t{result['returncode']}\t"
            f"{result['runtime_seconds']:.2f}\t{result.get('valid_candidates')}\t{result['ledger_records']}\t"
            f"{result.get('target_r_match_count')}\t{match_rate_text}\t"
            f"{best_score_text}\t"
            f"{best_matching_score_text}\t"
            f"{mean_score_text}\t"
            f"{acceptance:.3f}"
        )


def print_aggregate_table(results: list[dict[str, Any]]) -> None:
    print()
    print(
        "strategy\ttarget_r\truns\tavg_runtime_s\tvalid_total\tledger_records\t"
        "target_matches\tavg_match_rate\tavg_best\tavg_best_matching\tavg_mean\tbest\tlocal_acceptance"
    )
    for result in aggregate_results(results):
        avg_runtime = result.get("avg_runtime_seconds")
        avg_best = result.get("avg_best_score")
        avg_best_matching = result.get("avg_best_matching_score")
        avg_mean = result.get("avg_mean_score")
        best = result.get("best_score")
        avg_match_rate = result.get("avg_match_rate")
        match_total_text = str(result.get("target_r_match_total")) if result.get("target_r") is not None else "NA"
        match_rate_text = f"{avg_match_rate:.3f}" if avg_match_rate is not None else "NA"
        avg_best_text = f"{avg_best:.3f}" if avg_best is not None else "NA"
        avg_best_matching_text = f"{avg_best_matching:.3f}" if avg_best_matching is not None else "NA"
        avg_mean_text = f"{avg_mean:.3f}" if avg_mean is not None else "NA"
        best_text = f"{best:.3f}" if best is not None else "NA"
        print(
            f"{result['strategy']}\t{_target_label(result.get('target_r'))}\t{result['runs']}\t"
            f"{avg_runtime:.2f}\t"
            f"{result['valid_candidates_total']}\t{result['ledger_records_total']}\t"
            f"{match_total_text}\t{match_rate_text}\t{avg_best_text}\t"
            f"{avg_best_matching_text}\t{avg_mean_text}\t{best_text}\t"
            f"{result['local_search_acceptance']:.3f}"
        )


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Short CPU-only benchmark runner for IGP24 generation strategies")
    parser.add_argument(
        "--strategies",
        default=",".join(DEFAULT_STRATEGIES),
        help=(
            "Comma-separated generation strategies; use preset_r0/preset_r2/preset_r4 for presets "
            "or mix_r4_yield/mix_r4_balanced/mix_r4_diverse for benchmark-only r4 mix variants"
        ),
    )
    parser.add_argument("--seeds", default="101", help="Comma-separated integer seeds")
    parser.add_argument("--target_rs", default="none", help="Comma-separated target real-root counts; use none for untargeted")
    parser.add_argument("--coeff_bound", type=int, default=4)
    parser.add_argument("--gensize", type=int, default=12)
    parser.add_argument("--pop_size", type=int, default=6)
    parser.add_argument("--ntest", type=int, default=2)
    parser.add_argument("--gen_batch_size", type=int, default=2)
    parser.add_argument("--max_local_search_steps", type=int, default=3)
    parser.add_argument("--prime_limit", type=int, default=11)
    parser.add_argument("--exact_score_timeout", type=float, default=3.0)
    parser.add_argument("--sparse_terms", type=int, default=4)
    parser.add_argument("--low_height_bound", type=int, default=2)
    parser.add_argument(
        "--mixed_strategy_weights",
        default="uniform:0.10,low_height:0.20,sparse:0.25,lower_degree:0.20,structured:0.25",
        help="Comma-separated name:weight entries forwarded to mixed generation runs",
    )
    parser.add_argument("--always_search", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()
    args.strategies = _parse_csv(args.strategies)
    args.seeds = _parse_int_csv(args.seeds)
    args.target_rs = parse_target_rs(args.target_rs)
    args.output_dir = args.output_dir.resolve()
    args.repo_root = args.repo_root.resolve()

    results = []
    for strategy in args.strategies:
        try:
            resolve_benchmark_strategy(strategy)
        except ValueError as exc:
            parser.error(str(exc))
        for target_r in args.target_rs:
            for seed in args.seeds:
                result = run_one(args, strategy, seed, target_r=target_r)
                results.append(result)
                if result["returncode"] != 0:
                    write_outputs(results, args.output_dir)
                    print_table(results)
                    print_aggregate_table(results)
                    return result["returncode"]

    write_outputs(results, args.output_dir)
    print_table(results)
    print_aggregate_table(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
