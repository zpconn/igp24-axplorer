#!/usr/bin/env python3
"""Independently audit a checksummed IGP24 structural pretraining corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.polynomial import construct_polynomial, stable_canonical_hash  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sample_indices(row_count: int, sample_count: int) -> set[int]:
    take = min(max(0, int(sample_count)), int(row_count))
    if take <= 0:
        return set()
    if take == 1:
        return {row_count // 2}
    return {round(index * (row_count - 1) / (take - 1)) for index in range(take)}


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    exported = [int(value) for value in row["coefficients"]]
    coefficients = exported[:-1]
    expected_r = int(row["r"])
    features = row.get("features") or {}
    inner_power = int(features["inner_power"])
    polynomial = construct_polynomial(coefficients)
    canonical_hash = stable_canonical_hash(coefficients)
    support = [power for power, value in enumerate(coefficients) if value]
    actual_r = int(polynomial.count_roots(-sp.oo, sp.oo))
    irreducible = bool(polynomial.is_irreducible)
    squarefree = polynomial.gcd(polynomial.diff()).degree() == 0
    outer_s4_order = None
    if features.get("outer_s4_proved"):
        outer_coefficients = [coefficients[index] for index in range(0, 24, inner_power)] + [1]
        y = sp.Symbol("y")
        outer = sp.Poly(
            sum(value * y**power for power, value in enumerate(outer_coefficients)),
            y,
            domain=sp.ZZ,
        )
        outer_group, _alternating = outer.galois_group()
        outer_s4_order = int(outer_group.order())
    checks = {
        "degree_24_monic": len(exported) == 25 and exported[-1] == 1,
        "nonzero_constant": coefficients[0] != 0,
        "canonical_hash_matches": canonical_hash == row["canonical_hash"],
        "exact_r_matches": actual_r == expected_r,
        "irreducible_over_q": irreducible,
        "squarefree_over_q": squarefree,
        "inner_power_support_preserved": all(power % inner_power == 0 for power in support),
        "outer_s4_claim_matches": outer_s4_order in {None, 24},
        "packet_ineligible": features.get("packet_eligible") is False,
    }
    return {
        "canonical_hash": row["canonical_hash"],
        "construction_family": features.get("construction_family"),
        "r": expected_r,
        "inner_power": inner_power,
        "support": support,
        "outer_s4_order": outer_s4_order,
        "checks": checks,
        "passed": all(checks.values()),
    }


def render_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# IGP24 Structural Corpus Independent Audit",
            "",
            f"- Created: `{summary['created_at_utc']}`",
            f"- Source commit: `{summary['source_commit']}`",
            f"- Manifest files: `{summary['file_count']}`",
            f"- Manifest rows: `{summary['manifest_row_count']}`",
            f"- Sampled exact rows: `{summary['sampled_row_count']}`",
            f"- File integrity failures: `{summary['file_integrity_failure_count']}`",
            f"- Exact row failures: `{summary['sampled_row_failure_count']}`",
            f"- Status: `{summary['status']}`",
            "- Network/SAIR/submission calls: `none`",
            "",
            "The audit recomputes file SHA-256 values and, on deterministic stratified rows, "
            "recomputes canonical hashes, exact Q-irreducibility, exact real-root counts, "
            "squarefreeness, composition support, and claimed outer-S4 orders.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--samples_per_file", type=int, default=1)
    args = parser.parse_args(argv)

    started = time.perf_counter()
    manifest_path = args.manifest.resolve()
    corpus_root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    file_results = []
    sampled_rows = []
    check_failures = Counter()
    for item in manifest["files"]:
        path = corpus_root / item["path"]
        expected_rows = int(item["row_count"])
        selected = sample_indices(expected_rows, args.samples_per_file)
        observed_rows = 0
        selected_rows = []
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index in selected:
                    selected_rows.append(json.loads(line))
                observed_rows += 1
        observed_sha256 = sha256_file(path)
        file_passed = observed_rows == expected_rows and observed_sha256 == item["sha256"]
        file_results.append(
            {
                "path": item["path"],
                "expected_rows": expected_rows,
                "observed_rows": observed_rows,
                "expected_sha256": item["sha256"],
                "observed_sha256": observed_sha256,
                "passed": file_passed,
            }
        )
        for row in selected_rows:
            result = audit_row(row)
            sampled_rows.append(result)
            for name, passed in result["checks"].items():
                if not passed:
                    check_failures[name] += 1

    file_failures = sum(not result["passed"] for result in file_results)
    row_failures = sum(not result["passed"] for result in sampled_rows)
    passed = file_failures == 0 and row_failures == 0
    summary = {
        "schema_version": "igp24_structural_corpus_audit_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": get_source_commit(REPO_ROOT),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "file_count": len(file_results),
        "manifest_row_count": sum(int(item["row_count"]) for item in manifest["files"]),
        "sampled_row_count": len(sampled_rows),
        "file_integrity_failure_count": file_failures,
        "sampled_row_failure_count": row_failures,
        "check_failure_counts": dict(sorted(check_failures.items())),
        "runtime_seconds": time.perf_counter() - started,
        "status": "passed" if passed else "failed",
        "safety": {"network": False, "sair": False, "submission": False},
        "files": file_results,
        "sampled_rows": sampled_rows,
    }
    output_dir = args.output_dir.resolve()
    write_json(output_dir / "structural_corpus_audit_summary.json", summary)
    (output_dir / "structural_corpus_audit_report.md").write_text(render_report(summary), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key not in {"files", "sampled_rows"}}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
