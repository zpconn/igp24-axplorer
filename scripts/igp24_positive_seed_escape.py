#!/usr/bin/env python3
"""Generate local exact-valid escape mutations around score-positive AXG seeds.

This helper is intentionally offline. It reads the active-learning JSONL,
selects generator-training score-positive seeds, applies bounded odd-support
mutations that break obvious even/support-gcd basins, and writes only locally
valid, exact-target-r, known-hash-excluded candidates. It does not call SAIR,
use network access, run GAP/Magma/PARI, or submit anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.evaluator import sample_support_profile  # noqa: E402
from src.igp24.polynomial import (  # noqa: E402
    DEGREE,
    analysis_to_record,
    score_candidate,
    stable_canonical_hash,
)

SUMMARY_JSON = "positive_seed_escape_summary.json"
CANDIDATES_JSONL = "positive_seed_escape_candidates.jsonl"
REJECTED_JSONL = "positive_seed_escape_rejected.jsonl"
REPORT_MD = "positive_seed_escape_report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def parse_int_csv(value: str | None, *, default: Iterable[int] = ()) -> list[int]:
    if not value:
        return [int(item) for item in default]
    return [int(part.strip()) for part in str(value).split(",") if part.strip()]


def coefficient_vector(record: dict[str, Any]) -> list[int] | None:
    for key in ("coefficients", "exported_coefficients", "decoded_coefficients"):
        value = record.get(key)
        if not isinstance(value, list):
            continue
        try:
            coeffs = [int(item) for item in value]
        except (TypeError, ValueError):
            return None
        if len(coeffs) == DEGREE + 1 and coeffs[-1] == 1:
            return coeffs[:-1]
        if len(coeffs) == DEGREE:
            return coeffs
    polynomial = record.get("polynomial")
    if isinstance(polynomial, str):
        parts = [part.strip() for part in polynomial.split(",") if part.strip()]
        if len(parts) == DEGREE + 1:
            try:
                coeffs = [int(part) for part in parts]
            except ValueError:
                return None
            if coeffs[-1] == 1:
                return coeffs[:-1]
    return None


def row_hash_values(record: dict[str, Any]) -> set[str]:
    hashes: set[str] = set()
    for key in (
        "canonical_hash",
        "hash",
        "coefficient_hash",
        "decoded_hash",
        "exported_coefficient_hash",
        "stable_canonical_hash",
    ):
        value = record.get(key)
        if isinstance(value, str) and value:
            hashes.add(value)
    coeffs = coefficient_vector(record)
    if coeffs is not None:
        try:
            hashes.add(stable_canonical_hash(coeffs))
        except Exception:
            pass
    return hashes


def load_known_hashes(paths: Iterable[Path]) -> set[str]:
    known: set[str] = set()
    for path in paths:
        for row in read_jsonl(path):
            known.update(row_hash_values(row))
    return known


def selected_seed_rows(
    active_learning_rows: Iterable[dict[str, Any]],
    *,
    target_rs: set[int],
    roles: set[str],
) -> list[dict[str, Any]]:
    seeds_by_hash: dict[str, dict[str, Any]] = {}
    for row in active_learning_rows:
        generator = row.get("generator_training") if isinstance(row.get("generator_training"), dict) else {}
        if not generator.get("eligible"):
            continue
        if float(generator.get("weight") or 0.0) <= 0.0:
            continue
        role = str(generator.get("role") or "")
        if role not in roles:
            continue
        r_value = row.get("r")
        if r_value is None:
            features = row.get("features") if isinstance(row.get("features"), dict) else {}
            r_value = features.get("r")
        try:
            r_int = int(r_value)
        except (TypeError, ValueError):
            continue
        if target_rs and r_int not in target_rs:
            continue
        coeffs = coefficient_vector(row)
        if coeffs is None:
            continue
        hash_value = str(row.get("canonical_hash") or stable_canonical_hash(coeffs))
        seeds_by_hash.setdefault(hash_value, {**row, "coefficients": coeffs, "r": r_int})
    return list(seeds_by_hash.values())


def mutation_plans(
    *,
    odd_exponents: list[int],
    deltas: list[int],
    max_trials: int,
    include_pairs: bool,
) -> Iterable[list[tuple[int, int]]]:
    count = 0
    for exponent in odd_exponents:
        for delta in deltas:
            yield [(int(exponent), int(delta))]
            count += 1
            if count >= max_trials:
                return
    if not include_pairs:
        return
    for left_index, left in enumerate(odd_exponents):
        for right in odd_exponents[left_index + 1 :]:
            for left_delta in deltas:
                for right_delta in deltas:
                    yield [(int(left), int(left_delta)), (int(right), int(right_delta))]
                    count += 1
                    if count >= max_trials:
                        return


def mutate_coefficients(coefficients: list[int], plan: list[tuple[int, int]]) -> list[int]:
    mutated = [int(value) for value in coefficients]
    if len(mutated) != DEGREE:
        raise ValueError("expected 24 coefficient values")
    for exponent, delta in plan:
        if exponent < 0 or exponent >= DEGREE:
            raise ValueError(f"mutation exponent out of range: {exponent}")
        mutated[exponent] += int(delta)
    return mutated


def candidate_metadata(seed: dict[str, Any], plan: list[tuple[int, int]], profile: dict[str, Any]) -> dict[str, Any]:
    generator = seed.get("generator_training") if isinstance(seed.get("generator_training"), dict) else {}
    feedback = seed.get("sair_feedback") if isinstance(seed.get("sair_feedback"), dict) else {}
    return {
        "strategy": "positive_seed_escape",
        "source": "local_exact_positive_seed_mutation",
        "construction_family": "positive_seed_escape_odd_support_mutation",
        "source_family": "positive_seed_escape",
        "source_seed_hash": seed.get("canonical_hash"),
        "source_seed_pair": generator.get("pair_key") or feedback.get("pair_key"),
        "source_seed_label": generator.get("label") or feedback.get("label"),
        "source_seed_role": generator.get("role"),
        "target_r": seed.get("r"),
        "target_r_intent": seed.get("r"),
        "odd_escape_mutations": [{"x_exponent": int(exponent), "delta": int(delta)} for exponent, delta in plan],
        "support_pattern": profile.get("support_pattern"),
        "support_gcd": profile.get("support_gcd"),
        "even_support_like": profile.get("even_support_like"),
        "odd_support_exponents": profile.get("odd_support_exponents"),
        "sparse_support_submode": profile.get("sparse_support_submode"),
    }


def generate_candidates(
    *,
    seeds: list[dict[str, Any]],
    known_hashes: set[str],
    odd_exponents: list[int],
    deltas: list[int],
    max_trials_per_seed: int,
    max_candidates: int,
    coeff_bound: int,
    prime_limit: int,
    exact_score_timeout: float,
    require_support_gcd_one: bool,
    include_pair_mutations: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_hashes = set(known_hashes)
    rejection_counts: Counter[str] = Counter()
    exact_r_counts: Counter[str] = Counter()
    source_seed_counts: Counter[str] = Counter()
    total_trials = 0

    for seed in seeds:
        if max_candidates > 0 and len(candidates) >= max_candidates:
            break
        seed_hash = str(seed.get("canonical_hash") or "")
        target_r = int(seed["r"])
        seed_coefficients = coefficient_vector(seed)
        if seed_coefficients is None:
            rejection_counts["seed_missing_coefficients"] += 1
            rejected.append({"source_seed_hash": seed_hash, "reason": "seed_missing_coefficients"})
            continue
        for plan in mutation_plans(
            odd_exponents=odd_exponents,
            deltas=deltas,
            max_trials=int(max_trials_per_seed),
            include_pairs=include_pair_mutations,
        ):
            if max_candidates > 0 and len(candidates) >= max_candidates:
                break
            total_trials += 1
            try:
                coeffs = mutate_coefficients(seed_coefficients, plan)
            except ValueError as exc:
                reason = f"mutation_failed:{exc}"
                rejection_counts[reason] += 1
                rejected.append({"source_seed_hash": seed_hash, "mutation_plan": plan, "reason": reason})
                continue

            profile = sample_support_profile(coeffs)
            if profile.get("even_support_like") is True:
                rejection_counts["even_support_like"] += 1
                rejected.append({"source_seed_hash": seed_hash, "mutation_plan": plan, "reason": "even_support_like"})
                continue
            if require_support_gcd_one and profile.get("support_gcd") != 1:
                rejection_counts["support_gcd_not_one"] += 1
                rejected.append({"source_seed_hash": seed_hash, "mutation_plan": plan, "reason": "support_gcd_not_one"})
                continue
            if coeffs[0] == 0:
                rejection_counts["zero_constant_term"] += 1
                rejected.append({"source_seed_hash": seed_hash, "mutation_plan": plan, "reason": "zero_constant_term"})
                continue

            score, analysis = score_candidate(
                coeffs,
                coeff_bound=int(coeff_bound),
                target_r=target_r,
                prime_limit=int(prime_limit),
                exact_score_timeout=float(exact_score_timeout),
                seen_hashes=seen_hashes,
                translation_radius=0,
            )
            if analysis.real_root_count is not None:
                exact_r_counts[f"r={int(analysis.real_root_count)}"] += 1
            if not analysis.valid:
                reason = str(analysis.rejection_reason or "invalid")
                rejection_counts[reason] += 1
                rejected.append(
                    {
                        "source_seed_hash": seed_hash,
                        "mutation_plan": plan,
                        "reason": reason,
                        "canonical_hash": analysis.canonical_hash or None,
                    }
                )
                continue
            if int(analysis.real_root_count or -1) != target_r:
                rejection_counts["target_r_mismatch"] += 1
                rejected.append(
                    {
                        "source_seed_hash": seed_hash,
                        "mutation_plan": plan,
                        "reason": "target_r_mismatch",
                        "observed_r": analysis.real_root_count,
                        "target_r": target_r,
                        "canonical_hash": analysis.canonical_hash,
                    }
                )
                continue
            if analysis.canonical_hash in seen_hashes:
                rejection_counts["known_or_duplicate_hash"] += 1
                rejected.append(
                    {
                        "source_seed_hash": seed_hash,
                        "mutation_plan": plan,
                        "reason": "known_or_duplicate_hash",
                        "canonical_hash": analysis.canonical_hash,
                    }
                )
                continue

            seen_hashes.add(analysis.canonical_hash)
            source_seed_counts[seed_hash[:12]] += 1
            record = analysis_to_record(
                analysis,
                score,
                target_r=target_r,
                experiment_name="positive_seed_escape",
                verification_status="proxy_scored",
                generation_metadata=candidate_metadata(seed, plan, profile),
            )
            record["record_type"] = "igp24_positive_seed_escape_candidate"
            record["source_seed"] = {
                "canonical_hash": seed.get("canonical_hash"),
                "short_hash": str(seed.get("canonical_hash") or "")[:12],
                "r": target_r,
                "generator_training": seed.get("generator_training"),
                "sair_feedback": seed.get("sair_feedback"),
            }
            record["known_submission_hash_match"] = False
            record["sample_export_source"] = "positive_seed_escape"
            record["live_submission_recommended_now"] = False
            candidates.append(record)

    summary = {
        "total_trials": total_trials,
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "rejection_reason_counts": dict(rejection_counts),
        "exact_r_counts": dict(exact_r_counts),
        "source_seed_candidate_counts": dict(source_seed_counts),
    }
    return candidates, rejected, summary


def summarize(
    *,
    active_learning_jsonl: Path,
    known_hashes_jsonl: list[Path],
    output_dir: Path,
    seeds: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    generation_summary: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    role_counts = Counter(str((row.get("generator_training") or {}).get("role") or "unknown") for row in seeds)
    seed_pair_counts = Counter(
        str((row.get("generator_training") or {}).get("pair_key") or (row.get("sair_feedback") or {}).get("pair_key") or "unknown")
        for row in seeds
    )
    candidate_pair_counts = Counter(str((row.get("source_seed") or {}).get("sair_feedback", {}).get("pair_key") or "unknown") for row in candidates)
    return {
        "record_type": "igp24_positive_seed_escape_summary",
        "schema_version": 1,
        "created_at": utc_now(),
        "source_commit": get_source_commit(REPO_ROOT),
        "tool": "scripts/igp24_positive_seed_escape.py",
        "safety": {
            "calls_sair": False,
            "uses_network": False,
            "submits": False,
            "runs_gap_magma_pari": False,
            "exact_label_verification": False,
        },
        "inputs": {
            "active_learning_jsonl": str(active_learning_jsonl),
            "known_hashes_jsonl": [str(path) for path in known_hashes_jsonl],
            "target_rs": parse_int_csv(args.target_rs),
            "roles": [part.strip() for part in str(args.roles).split(",") if part.strip()],
            "max_trials_per_seed": int(args.max_trials_per_seed),
            "max_candidates": int(args.max_candidates),
            "odd_exponents": parse_int_csv(args.odd_exponents),
            "deltas": parse_int_csv(args.deltas),
            "include_pair_mutations": bool(args.include_pair_mutations),
            "require_support_gcd_one": bool(args.require_support_gcd_one),
            "coeff_bound": int(args.coeff_bound),
            "prime_limit": int(args.prime_limit),
        },
        "selected_seed_count": len(seeds),
        "selected_seed_role_counts": dict(role_counts),
        "selected_seed_pair_counts": dict(seed_pair_counts),
        "candidate_count": len(candidates),
        "candidate_source_pair_counts": dict(candidate_pair_counts),
        "rejected_count": len(rejected),
        **generation_summary,
        "live_submission_recommended_now": False,
        "submission_recommendation": "false_offline_local_escape_candidates_require_adaptive_review",
        "output_files": {
            "summary_json": str(output_dir / SUMMARY_JSON),
            "candidates_jsonl": str(output_dir / CANDIDATES_JSONL),
            "rejected_jsonl": str(output_dir / REJECTED_JSONL),
            "report_md": str(output_dir / REPORT_MD),
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Positive Seed Escape",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Selected seeds: `{summary['selected_seed_count']}`",
        f"- Trials: `{summary['total_trials']}`",
        f"- Local exact candidates: `{summary['candidate_count']}`",
        f"- Rejected trials: `{summary['rejected_count']}`",
        f"- Live submission recommended now: `{summary['live_submission_recommended_now']}`",
        "",
        "This helper is local/offline. Candidates are exact-local rows only and still require adaptive Frobenius review.",
        "",
        "## Seed Pairs",
        "",
    ]
    for pair, count in sorted(summary.get("selected_seed_pair_counts", {}).items()):
        lines.append(f"- `{pair}`: {count}")
    lines.extend(["", "## Rejections", ""])
    for reason, count in sorted(summary.get("rejection_reason_counts", {}).items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{reason}`: {count}")
    lines.extend(["", "## Exact r Observations", ""])
    for r_value, count in sorted(summary.get("exact_r_counts", {}).items()):
        lines.append(f"- `{r_value}`: {count}")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output_dir: Path, *, summary: dict[str, Any], candidates: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / SUMMARY_JSON, summary)
    write_jsonl(output_dir / CANDIDATES_JSONL, candidates)
    write_jsonl(output_dir / REJECTED_JSONL, rejected)
    (output_dir / REPORT_MD).write_text(render_report(summary), encoding="utf-8")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active_learning_jsonl", type=Path, required=True)
    parser.add_argument("--known_hashes_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_rs", default="8,12")
    parser.add_argument("--roles", default="score_positive")
    parser.add_argument("--odd_exponents", default="1,3,5,7,9,11,13,15,17,19,21,23")
    parser.add_argument("--deltas", default="-9,-5,-3,-2,-1,1,2,3,5,9")
    parser.add_argument("--max_trials_per_seed", type=int, default=160)
    parser.add_argument("--max_candidates", type=int, default=40)
    parser.add_argument("--coeff_bound", type=int, default=1_000_000_000_000_000)
    parser.add_argument("--prime_limit", type=int, default=7)
    parser.add_argument("--exact_score_timeout", type=float, default=3.0)
    parser.add_argument("--require_support_gcd_one", action="store_true", default=False)
    parser.add_argument("--include_pair_mutations", action="store_true", default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    target_rs = set(parse_int_csv(args.target_rs))
    roles = {part.strip() for part in str(args.roles).split(",") if part.strip()}
    active_rows = read_jsonl(args.active_learning_jsonl)
    seeds = selected_seed_rows(active_rows, target_rs=target_rs, roles=roles)
    known_hashes = load_known_hashes(args.known_hashes_jsonl)
    candidates, rejected, generation_summary = generate_candidates(
        seeds=seeds,
        known_hashes=known_hashes,
        odd_exponents=parse_int_csv(args.odd_exponents),
        deltas=parse_int_csv(args.deltas),
        max_trials_per_seed=int(args.max_trials_per_seed),
        max_candidates=int(args.max_candidates),
        coeff_bound=int(args.coeff_bound),
        prime_limit=int(args.prime_limit),
        exact_score_timeout=float(args.exact_score_timeout),
        require_support_gcd_one=bool(args.require_support_gcd_one),
        include_pair_mutations=bool(args.include_pair_mutations),
    )
    summary = summarize(
        active_learning_jsonl=args.active_learning_jsonl,
        known_hashes_jsonl=args.known_hashes_jsonl,
        output_dir=args.output_dir,
        seeds=seeds,
        candidates=candidates,
        rejected=rejected,
        generation_summary=generation_summary,
        args=args,
    )
    write_outputs(args.output_dir, summary=summary, candidates=candidates, rejected=rejected)
    print(f"selected_seed_count\t{summary['selected_seed_count']}")
    print(f"candidate_count\t{summary['candidate_count']}")
    print(f"rejected_count\t{summary['rejected_count']}")
    print(f"summary\t{summary['output_files']['summary_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
