#!/usr/bin/env python3
"""Build a million-row exact structural corpus for meaningful AXG training.

This is an offline data builder. It performs no network reads, no SAIR calls,
and no submissions. Every emitted polynomial is monic degree 24, has an exact
real-root certificate, is irreducible by Eisenstein, and preserves a stated
power-composition block system. Quartic-in-x6 rows additionally require a
proof that the outer quartic Galois group is S4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.constructions.eisenstein_composition import (  # noqa: E402
    build_eisenstein_power_composition,
    quartic_outer_s4_certificate,
)
from src.igp24.group_compatibility import read_jsonl  # noqa: E402


DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/structural_pretraining_20260710"
TARGET_RS = (8, 12, 16, 20, 24)
SCHEMA_VERSION = "igp24_exact_structural_pretraining_v1"


@dataclass(frozen=True)
class FamilyConfig:
    family_id: str
    split: str
    outer_degree: int
    inner_power: int
    prime: int
    center_start: int
    center_count: int
    positive_stride: int
    negative_stride: int
    rank_offset: int
    require_outer_s4: bool = False

    def supports_r(self, target_r: int) -> bool:
        positive_outer_roots = int(target_r) // 2
        return (
            int(target_r) in TARGET_RS
            and int(target_r) % 4 == 0
            and positive_outer_roots <= self.outer_degree
            and positive_outer_roots % 2 == 0
            and (self.outer_degree - positive_outer_roots) % 2 == 0
        )


TRAIN_FAMILIES = (
    FamilyConfig("train_d12_x2_p2_low", "train", 12, 2, 2, 1, 72, 5, 11, 101),
    FamilyConfig("train_d12_x2_p3_low", "train", 12, 2, 3, 1, 72, 7, 13, 211),
    FamilyConfig("train_d12_x2_p5_mid", "train", 12, 2, 5, 17, 72, 11, 17, 307),
    FamilyConfig("train_d12_x2_p7_mid", "train", 12, 2, 7, 33, 72, 13, 19, 401),
    FamilyConfig("train_d6_x4_p2", "train", 6, 4, 2, 1, 128, 17, 23, 503),
    FamilyConfig("train_d4_x6_p2_outer_s4", "train", 4, 6, 2, 1, 128, 19, 29, 601, True),
)

EVAL_FAMILIES = (
    FamilyConfig("eval_d12_x2_p3_high", "eval", 12, 2, 3, 113, 72, 23, 31, 701),
    FamilyConfig("eval_d6_x4_p5_high", "eval", 6, 4, 5, 129, 128, 29, 37, 809),
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def unrank_combination(size: int, count: int, rank: int) -> tuple[int, ...]:
    """Return the zero-based lexicographic combination at ``rank``."""

    if count < 0 or count > size:
        raise ValueError("invalid_combination_size")
    total = math.comb(size, count)
    if total <= 0:
        raise ValueError("empty_combination_space")
    remaining_rank = int(rank) % total
    result: list[int] = []
    candidate = 0
    for remaining_count in range(count, 0, -1):
        while candidate < size:
            suffix_count = math.comb(size - candidate - 1, remaining_count - 1)
            if remaining_rank < suffix_count:
                result.append(candidate)
                candidate += 1
                break
            remaining_rank -= suffix_count
            candidate += 1
    return tuple(result)


def centers_for_index(config: FamilyConfig, target_r: int, index: int) -> tuple[int, ...]:
    positive_count = int(target_r) // 2
    negative_count = config.outer_degree - positive_count
    positive_space = math.comb(config.center_count, positive_count)
    negative_space = math.comb(config.center_count, negative_count)
    base = int(index) + config.rank_offset + int(target_r) * 1_000_003
    positive_rank = (base * config.positive_stride + config.rank_offset) % positive_space
    negative_rank = (base * config.negative_stride + config.rank_offset * 3) % negative_space
    domain = tuple(range(config.center_start, config.center_start + config.center_count))
    positives = tuple(domain[position] for position in unrank_combination(config.center_count, positive_count, positive_rank))
    negative_magnitudes = tuple(
        domain[position] for position in unrank_combination(config.center_count, negative_count, negative_rank)
    )
    return tuple(sorted(tuple(-value for value in negative_magnitudes) + positives))


def allocate_quota(total: int, families: Sequence[FamilyConfig], target_r: int) -> list[tuple[FamilyConfig, int]]:
    eligible = [config for config in families if config.supports_r(target_r)]
    if not eligible:
        raise ValueError(f"no_family_supports_r:{target_r}")
    base, remainder = divmod(int(total), len(eligible))
    return [(config, base + (1 if index < remainder else 0)) for index, config in enumerate(eligible)]


def build_quota_plan(train_rows: int, eval_rows: int) -> list[dict[str, Any]]:
    if int(train_rows) % len(TARGET_RS) or int(eval_rows) % len(TARGET_RS):
        raise ValueError("train_and_eval_targets_must_be_divisible_by_target_r_count")
    plan: list[dict[str, Any]] = []
    for split, total, families in (
        ("train", int(train_rows), TRAIN_FAMILIES),
        ("eval", int(eval_rows), EVAL_FAMILIES),
    ):
        per_r = total // len(TARGET_RS)
        for target_r in TARGET_RS:
            for config, quota in allocate_quota(per_r, families, target_r):
                plan.append({"split": split, "target_r": target_r, "family": config, "quota": quota})
    return plan


def load_known_hashes(paths: Iterable[Path]) -> set[str]:
    hashes: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            value = row.get("canonical_hash") or row.get("candidate_hash")
            if value:
                hashes.add(str(value))
    return hashes


def record_for_candidate(
    *,
    config: FamilyConfig,
    target_r: int,
    parameter_index: int,
    shard_group: int,
    certificate: Any,
    canonical_hash: str,
    outer_s4: dict[str, Any] | None,
) -> dict[str, Any]:
    family = config.family_id
    split_group = f"{family}:r{int(target_r)}:parameter_shard_{int(shard_group):04d}"
    return {
        "schema_version": SCHEMA_VERSION,
        "canonical_hash": canonical_hash,
        "coefficients": list(certificate.exported_coefficients),
        "r": int(target_r),
        "train_eval_split": config.split,
        "source_role": "exact_structural_pretraining",
        "derived_class_label": "exact_local_valid",
        "generator_training": {
            "eligible": True,
            "weight": 1.0,
            "role": "exact_local_exploration",
            "reason": "exact Eisenstein irreducibility, exact interval root count, preserved power-composition structure",
            "construction_family": family,
            "split_group_key": split_group,
        },
        "features": {
            "construction_family": family,
            "template_family": f"eisenstein_outer_d{config.outer_degree}_power_x{config.inner_power}",
            "parameter_index": int(parameter_index),
            "eisenstein_prime": config.prime,
            "outer_degree": config.outer_degree,
            "inner_power": config.inner_power,
            "block_size": config.inner_power,
            "block_count": config.outer_degree,
            "exact_real_root_count": int(target_r),
            "irreducibility_proof": "eisenstein",
            "real_root_proof": "paired_integer_centers_midpoint_ivt",
            "squarefree_proof": "irreducible_characteristic_zero",
            "outer_s4_proved": bool(outer_s4 and outer_s4.get("proved")),
            "outer_s4_witness_prime": (
                (outer_s4.get("three_cycle_witness") or {}).get("prime") if outer_s4 else None
            ),
            "structural_soundness": "exact_composition_upper_bound_not_exact_degree24_label",
            "packet_eligible": False,
        },
    }


def completed_shard(path: Path, metadata_path: Path, quota: int) -> dict[str, Any] | None:
    if not path.exists() or not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if int(metadata.get("row_count") or 0) != int(quota):
        return None
    if metadata.get("sha256") != sha256_file(path):
        return None
    return metadata


def register_existing_hashes(path: Path, seen_hashes: set[str]) -> None:
    for row in read_jsonl(path):
        canonical_hash = str(row["canonical_hash"])
        if canonical_hash in seen_hashes:
            raise ValueError(f"duplicate_canonical_hash_in_completed_corpus:{canonical_hash}")
        seen_hashes.add(canonical_hash)


def build_shard(
    *,
    output_dir: Path,
    config: FamilyConfig,
    target_r: int,
    quota: int,
    seen_hashes: set[str],
    excluded_hashes: set[str],
    split_group_size: int,
    resume: bool,
) -> dict[str, Any]:
    relative = Path(config.split) / f"r{target_r}" / f"{config.family_id}.jsonl"
    path = output_dir / relative
    metadata_path = path.with_suffix(".meta.json")
    if resume and (metadata := completed_shard(path, metadata_path, quota)) is not None:
        register_existing_hashes(path, seen_hashes)
        return {**metadata, "path": str(relative), "resumed": True}

    path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = path.with_suffix(".jsonl.partial")
    counters: Counter[str] = Counter()
    witness_primes: Counter[str] = Counter()
    started = time.perf_counter()
    parameter_index = 0
    emitted = 0
    digest = hashlib.sha256()
    with partial_path.open("wb") as handle:
        while emitted < int(quota):
            centers = centers_for_index(config, target_r, parameter_index)
            parameter_index += 1
            certificate = build_eisenstein_power_composition(
                centers,
                prime=config.prime,
                inner_power=config.inner_power,
            )
            if certificate.real_root_count != int(target_r):
                raise ValueError("internal_target_r_certificate_mismatch")
            outer_s4 = None
            if config.require_outer_s4:
                outer_s4 = quartic_outer_s4_certificate(certificate.outer_coefficients)
                if not outer_s4["proved"]:
                    counters["outer_s4_not_proved"] += 1
                    continue
                witness_primes[str((outer_s4["three_cycle_witness"] or {})["prime"])] += 1
            canonical_hash = certificate.canonical_hash
            if canonical_hash in excluded_hashes:
                counters["known_hash_excluded"] += 1
                continue
            if canonical_hash in seen_hashes:
                counters["canonical_duplicate"] += 1
                continue
            row = record_for_candidate(
                config=config,
                target_r=target_r,
                parameter_index=parameter_index - 1,
                shard_group=emitted // max(1, int(split_group_size)),
                certificate=certificate,
                canonical_hash=canonical_hash,
                outer_s4=outer_s4,
            )
            encoded = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            handle.write(encoded)
            digest.update(encoded)
            seen_hashes.add(canonical_hash)
            emitted += 1
            if emitted % 10_000 == 0:
                elapsed = max(time.perf_counter() - started, 1e-9)
                print(
                    json.dumps(
                        {
                            "event": "shard_progress",
                            "family": config.family_id,
                            "r": target_r,
                            "emitted": emitted,
                            "quota": quota,
                            "rows_per_second": emitted / elapsed,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        handle.flush()
        os.fsync(handle.fileno())
    partial_path.replace(path)
    runtime = time.perf_counter() - started
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "path": str(relative),
        "family": asdict(config),
        "target_r": int(target_r),
        "row_count": emitted,
        "parameter_attempt_count": parameter_index,
        "rejection_counts": dict(sorted(counters.items())),
        "outer_s4_witness_prime_counts": dict(sorted(witness_primes.items())),
        "sha256": digest.hexdigest(),
        "size_bytes": path.stat().st_size,
        "runtime_seconds": runtime,
        "rows_per_second": emitted / max(runtime, 1e-9),
        "resumed": False,
    }
    write_json(metadata_path, metadata)
    return metadata


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Exact Structural Pretraining Corpus",
        "",
        f"- Created: `{manifest['created_at_utc']}`",
        f"- Source commit: `{manifest['source_commit']}`",
        f"- Status: `{manifest['status']}`",
        f"- Unique train rows: `{manifest['train_row_count']}`",
        f"- Unique evaluation rows: `{manifest['eval_row_count']}`",
        f"- Target-r counts: `{json.dumps(manifest['row_counts_by_split_r'], sort_keys=True)}`",
        f"- Construction families: `{len(manifest['row_counts_by_family'])}`",
        f"- Canonical collisions rejected: `{manifest['canonical_duplicate_rejection_count']}`",
        f"- Known hashes rejected: `{manifest['known_hash_rejection_count']}`",
        f"- Corpus bytes: `{manifest['total_size_bytes']}`",
        f"- Runtime seconds: `{manifest['runtime_seconds']:.3f}`",
        "- Network/SAIR/submission calls: `none`",
        "",
        "## Mathematical Contract",
        "",
        "Every row is monic degree 24 and exactly irreducible by an Eisenstein certificate. "
        "Its real-root count is certified by disjoint midpoint/IVT intervals in the outer polynomial, "
        "and its `h(x^m)` form preserves an imprimitive block system. These facts do not establish an "
        "exact degree-24 transitive-group label. Quartic-in-x6 rows additionally prove outer group S4.",
        "",
        "## Training Contract",
        "",
        "Counts refer to unique post-generation canonical hashes. Evaluation families and parameter "
        "ranges are disjoint from training families. Repeated sampler draws and epochs do not count as "
        "additional examples. Rows are pretraining-only and packet-ineligible.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train_rows", type=int, default=1_000_000)
    parser.add_argument("--eval_rows", type=int, default=100_000)
    parser.add_argument("--split_group_size", type=int, default=2_000)
    parser.add_argument("--known_submissions_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args(argv)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    source_commit = get_source_commit(REPO_ROOT)
    plan = build_quota_plan(args.train_rows, args.eval_rows)
    excluded_hashes = load_known_hashes(args.known_submissions_jsonl)
    seen_hashes: set[str] = set()
    shard_summaries = []
    for item in plan:
        config = item["family"]
        print(
            json.dumps(
                {
                    "event": "shard_start",
                    "split": item["split"],
                    "r": item["target_r"],
                    "family": config.family_id,
                    "quota": item["quota"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        summary = build_shard(
            output_dir=output_dir,
            config=config,
            target_r=item["target_r"],
            quota=item["quota"],
            seen_hashes=seen_hashes,
            excluded_hashes=excluded_hashes,
            split_group_size=args.split_group_size,
            resume=args.resume,
        )
        shard_summaries.append(summary)
        print(json.dumps({"event": "shard_complete", **summary}, sort_keys=True), flush=True)

    row_counts_by_split = Counter()
    row_counts_by_split_r = Counter()
    row_counts_by_family = Counter()
    duplicate_rejections = 0
    known_rejections = 0
    for summary in shard_summaries:
        split = summary["family"]["split"]
        count = int(summary["row_count"])
        row_counts_by_split[split] += count
        row_counts_by_split_r[f"{split}|r={summary['target_r']}"] += count
        row_counts_by_family[summary["family"]["family_id"]] += count
        duplicate_rejections += int((summary.get("rejection_counts") or {}).get("canonical_duplicate", 0))
        known_rejections += int((summary.get("rejection_counts") or {}).get("known_hash_excluded", 0))

    train_count = int(row_counts_by_split["train"])
    eval_count = int(row_counts_by_split["eval"])
    complete = train_count >= int(args.train_rows) and eval_count >= int(args.eval_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "status": "ready_for_post_loader_readiness_audit" if complete else "incomplete",
        "safety": {
            "network_reads": False,
            "network_posts": False,
            "sair_calls": False,
            "live_submissions": False,
        },
        "counting_semantics": "unique canonical generated rows; repeated draws and epochs excluded",
        "target_rs": list(TARGET_RS),
        "requested_train_rows": int(args.train_rows),
        "requested_eval_rows": int(args.eval_rows),
        "train_row_count": train_count,
        "eval_row_count": eval_count,
        "unique_canonical_hash_count": len(seen_hashes),
        "row_counts_by_split_r": dict(sorted(row_counts_by_split_r.items())),
        "row_counts_by_family": dict(sorted(row_counts_by_family.items())),
        "canonical_duplicate_rejection_count": duplicate_rejections,
        "known_hash_rejection_count": known_rejections,
        "known_hash_exclusion_source_count": len(args.known_submissions_jsonl),
        "total_size_bytes": sum(int(summary["size_bytes"]) for summary in shard_summaries),
        "runtime_seconds": time.perf_counter() - started,
        "recommended_loader_caps": {
            "igp24_generator_cap_per_pair": 0,
            "igp24_generator_cap_per_label": 0,
            "igp24_generator_cap_per_family": 300_000,
            "igp24_generator_cap_per_basin_fingerprint": 0,
        },
        "files": [
            {
                "path": summary["path"],
                "sha256": summary["sha256"],
                "row_count": summary["row_count"],
                "split": summary["family"]["split"],
                "target_r": summary["target_r"],
                "construction_family": summary["family"]["family_id"],
            }
            for summary in shard_summaries
        ],
        "shards": shard_summaries,
    }
    write_json(output_dir / "corpus_manifest.json", manifest)
    (output_dir / "corpus_report.md").write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"event": "corpus_complete", **manifest}, sort_keys=True), flush=True)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
