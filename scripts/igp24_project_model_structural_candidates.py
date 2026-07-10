#!/usr/bin/env python3
"""Project AXG outputs into exact structural candidates and a matched baseline.

This is an offline experiment. It performs no network access, no SAIR calls,
no exact Galois verification, and no submission.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.constructions.eisenstein_composition import build_eisenstein_power_composition  # noqa: E402
from src.igp24.model_projection import (  # noqa: E402
    R24_M2_PROJECTION_FAMILIES,
    deterministic_baseline_centers,
    deterministic_projection_jitter,
    outer_coefficients_from_power_composition,
    project_outer_roots_to_family,
)


SCHEMA_VERSION = "igp24_axg_structural_projection_v1"


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_excluded_hashes(manifest_path: Path, known_paths: Iterable[Path]) -> tuple[set[str], Counter[str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hashes: set[str] = set()
    counts: Counter[str] = Counter()
    for entry in manifest.get("files") or []:
        shard = manifest_path.parent / str(entry["path"])
        for row in read_jsonl(shard):
            value = row.get("canonical_hash")
            if value:
                hashes.add(str(value))
                counts["training_or_eval_corpus"] += 1
    for path in known_paths:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            value = row.get("canonical_hash") or row.get("candidate_hash")
            if value:
                hashes.add(str(value))
                counts[f"known:{path.name}"] += 1
    return hashes, counts


def source_coefficients(row: dict[str, Any]) -> list[int] | None:
    for key in ("decoded_coefficients", "coefficients", "exported_coefficients"):
        values = row.get(key)
        if isinstance(values, list):
            return [int(value) for value in values]
    return None


def candidate_record(
    *,
    lane: str,
    source_hash: str,
    source_index: int,
    variant: int,
    certificate: Any,
    projection: Any | None,
    family_id: str,
) -> dict[str, Any]:
    record = {
        "schema_version": SCHEMA_VERSION,
        "canonical_hash": certificate.canonical_hash,
        "coefficients": list(certificate.exported_coefficients),
        "r": 24,
        "source_lane": lane,
        "source_model_hash": source_hash,
        "source_model_index": int(source_index),
        "projection_variant": int(variant),
        "features": {
            "construction_family": family_id,
            "eisenstein_prime": certificate.prime,
            "outer_degree": certificate.outer_degree,
            "inner_power": certificate.inner_power,
            "integer_centers": list(projection.centers if projection is not None else ()),
            "exact_real_root_count": certificate.real_root_count,
            "irreducibility_proof": "eisenstein",
            "real_root_proof": "paired_integer_centers_midpoint_ivt",
            "structural_soundness": "exact_composition_upper_bound_not_exact_degree24_label",
            "model_role": "parameter_proposal_only" if lane == "model_projected" else "matched_random_baseline",
            "packet_eligible": False,
        },
        "verification": {
            "local_validity": "exact_by_construction",
            "exact_group_label": None,
            "adaptive_frobenius": "not_run",
            "submission_recommendation": False,
        },
        "safety": {
            "network_reads": False,
            "network_posts": False,
            "sair_calls": False,
            "live_submission": False,
        },
    }
    if projection is not None:
        record["features"].update(
            {
                "integer_centers": list(projection.centers),
                "center_estimates": [round(value, 8) for value in projection.center_estimates],
                "assignment_rmse": projection.assignment_rmse,
                "imaginary_rmse": projection.imaginary_rmse,
                "normalized_projection_error": projection.normalized_projection_error,
            }
        )
    return record


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw_samples_jsonl", type=Path, required=True)
    parser.add_argument("--training_manifest", type=Path, required=True)
    parser.add_argument("--known_hashes_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--max_raw_rows", type=int, default=512)
    parser.add_argument("--variants_per_family", type=int, default=1)
    args = parser.parse_args()

    started = time.perf_counter()
    excluded_hashes, exclusion_counts = load_excluded_hashes(args.training_manifest, args.known_hashes_jsonl)
    counters: Counter[str] = Counter()
    model_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    model_hashes: set[str] = set()
    baseline_hashes: set[str] = set()
    raw_rows = []
    for row in read_jsonl(args.raw_samples_jsonl):
        coefficients = source_coefficients(row)
        if coefficients is None:
            counters["raw_missing_coefficients"] += 1
            continue
        try:
            outer = outer_coefficients_from_power_composition(coefficients, inner_power=2)
        except (TypeError, ValueError):
            counters["raw_invalid_m2_support"] += 1
            continue
        source_hash = str(row.get("decoded_hash") or row.get("coefficient_hash") or "")
        if not source_hash:
            counters["raw_missing_hash"] += 1
            continue
        raw_rows.append((source_hash, outer))
        if len(raw_rows) >= int(args.max_raw_rows):
            break

    for source_index, (source_hash, outer) in enumerate(raw_rows):
        for family in R24_M2_PROJECTION_FAMILIES:
            for variant in range(int(args.variants_per_family)):
                jitter = deterministic_projection_jitter(source_hash, family.family_id, variant, family.outer_degree)
                try:
                    projection = project_outer_roots_to_family(outer, family, jitter=jitter)
                    certificate = build_eisenstein_power_composition(
                        projection.centers,
                        prime=family.prime,
                        inner_power=family.inner_power,
                    )
                except (ArithmeticError, TypeError, ValueError):
                    counters["model_projection_failed"] += 1
                    continue
                candidate_hash = certificate.canonical_hash
                if candidate_hash in excluded_hashes:
                    counters["model_excluded_known_hash"] += 1
                elif candidate_hash in model_hashes:
                    counters["model_duplicate_hash"] += 1
                else:
                    model_hashes.add(candidate_hash)
                    model_rows.append(
                        candidate_record(
                            lane="model_projected",
                            source_hash=source_hash,
                            source_index=source_index,
                            variant=variant,
                            certificate=certificate,
                            projection=projection,
                            family_id=family.family_id,
                        )
                    )

                baseline_centers = deterministic_baseline_centers(source_hash, family, variant=variant)
                try:
                    baseline_certificate = build_eisenstein_power_composition(
                        baseline_centers,
                        prime=family.prime,
                        inner_power=family.inner_power,
                    )
                except ValueError:
                    counters["baseline_construction_failed"] += 1
                    continue
                baseline_hash = baseline_certificate.canonical_hash
                if baseline_hash in excluded_hashes:
                    counters["baseline_excluded_known_hash"] += 1
                elif baseline_hash in baseline_hashes:
                    counters["baseline_duplicate_hash"] += 1
                else:
                    baseline_hashes.add(baseline_hash)
                    baseline_rows.append(
                        candidate_record(
                            lane="matched_random_baseline",
                            source_hash=source_hash,
                            source_index=source_index,
                            variant=variant,
                            certificate=baseline_certificate,
                            projection=None,
                            family_id=family.family_id,
                        )
                    )
                    baseline_rows[-1]["features"]["integer_centers"] = list(baseline_centers)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "model_projected_candidates.jsonl"
    baseline_path = args.output_dir / "matched_baseline_candidates.jsonl"
    write_jsonl(model_path, model_rows)
    write_jsonl(baseline_path, baseline_rows)
    overlap = model_hashes & baseline_hashes
    errors = sorted(float(row["features"]["normalized_projection_error"]) for row in model_rows)

    def percentile(fraction: float) -> float | None:
        if not errors:
            return None
        return errors[min(len(errors) - 1, int(fraction * (len(errors) - 1)))]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": get_source_commit(REPO_ROOT),
        "raw_samples_jsonl": str(args.raw_samples_jsonl),
        "training_manifest": str(args.training_manifest),
        "known_hashes_jsonl": [str(path) for path in args.known_hashes_jsonl],
        "raw_rows_used": len(raw_rows),
        "variants_per_family": int(args.variants_per_family),
        "projection_family_count": len(R24_M2_PROJECTION_FAMILIES),
        "excluded_canonical_hash_count": len(excluded_hashes),
        "exclusion_source_row_counts": dict(sorted(exclusion_counts.items())),
        "model_projected_candidate_count": len(model_rows),
        "matched_baseline_candidate_count": len(baseline_rows),
        "cross_lane_hash_overlap_count": len(overlap),
        "projection_error": {
            "minimum": errors[0] if errors else None,
            "median": percentile(0.5),
            "p90": percentile(0.9),
            "maximum": errors[-1] if errors else None,
        },
        "counters": dict(sorted(counters.items())),
        "outputs": {
            "model_projected_candidates": str(model_path),
            "matched_baseline_candidates": str(baseline_path),
        },
        "interpretation": {
            "model_role": "parameter_proposal_only",
            "exact_local_validity": True,
            "exact_real_root_count": 24,
            "group_label_verified": False,
            "packet_eligible": False,
            "next_gate": "matched adaptive Frobenius target-exclusion comparison",
        },
        "runtime_seconds": time.perf_counter() - started,
        "safety": {
            "network_reads": False,
            "network_posts": False,
            "sair_calls": False,
            "live_submission": False,
        },
    }
    summary_path = args.output_dir / "projection_summary.json"
    write_json(summary_path, summary)
    report = "\n".join(
        [
            "# AXG structural projection",
            "",
            f"- Raw model rows used: {len(raw_rows)}",
            f"- Fresh model-projected candidates: {len(model_rows)}",
            f"- Fresh matched-baseline candidates: {len(baseline_rows)}",
            f"- Excluded corpus/submission hashes loaded: {len(excluded_hashes)}",
            f"- Cross-lane canonical overlap: {len(overlap)}",
            "- Every emitted row is exact r=24 and Eisenstein irreducible by construction.",
            "- Exact degree-24 Galois labels are unknown; no row is packet-eligible.",
            "- No network access or submission was performed.",
            "",
        ]
    )
    (args.output_dir / "projection_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
