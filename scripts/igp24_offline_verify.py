#!/usr/bin/env python3
"""Prepare offline exact-verifier inputs for IGP24 review batches.

This helper is file-only by default. It validates an existing proxy-only review
batch and writes manual PARI/GP and MAGMA input scripts for later local exact
verification. It never calls SAIR, never performs network work, and never
claims exact group labels unless a future explicit verifier parser records
that provenance.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl


VERIFICATION_BATCH_JSONL = "verification_batch.jsonl"
VERIFICATION_COEFFICIENTS_TXT = "verification_coefficients.txt"
REVIEW_MANIFEST_JSON = "manifest.json"
OFFLINE_MANIFEST_JSON = "offline_verification_manifest.json"
PARI_INPUT_GP = "pari_input.gp"
MAGMA_INPUT_M = "magma_input.m"
VERIFICATION_PLAN_MD = "verification_plan.md"
PARI_RAW_OUTPUT = "pari_raw_output.txt"
MAGMA_RAW_OUTPUT = "magma_raw_output.txt"
SAFETY_NOTE = (
    "Preparation-only offline verifier artifact. No SAIR submission, network "
    "call, auto-submission, or exact group-label claim is performed."
)


class ReviewBatchError(ValueError):
    """Raised when a review batch is malformed or unsafe to prepare."""


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required review-batch file missing: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"required review-batch path is not a file: {path}")
    return path


def _validate_coefficients(value: Any, *, context: str) -> list[int]:
    if not isinstance(value, list):
        raise ReviewBatchError(f"{context}: coefficients must be a JSON list")
    if len(value) != 25:
        raise ReviewBatchError(f"{context}: expected 25 coefficients, found {len(value)}")
    if any(not isinstance(item, int) for item in value):
        raise ReviewBatchError(f"{context}: coefficients must all be integers")
    if value[-1] != 1:
        raise ReviewBatchError(f"{context}: exported coefficient vector must end in leading coefficient 1")
    return list(value)


def load_review_batch(review_batch: str | Path) -> tuple[list[dict[str, Any]], Path, dict[str, Any]]:
    """Load and validate a review-batch directory."""

    review_dir = Path(review_batch).resolve()
    if not review_dir.is_dir():
        raise FileNotFoundError(f"review batch directory does not exist: {review_dir}")

    batch_path = _require_file(review_dir / VERIFICATION_BATCH_JSONL)
    coeff_path = _require_file(review_dir / VERIFICATION_COEFFICIENTS_TXT)
    manifest_path = _require_file(review_dir / REVIEW_MANIFEST_JSON)

    records = read_jsonl(batch_path)
    coeff_lines = [line for line in coeff_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(records) != len(coeff_lines):
        raise ReviewBatchError(
            f"coefficient line count mismatch: {len(records)} batch records vs {len(coeff_lines)} coefficient lines"
        )

    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, (record, coeff_line) in enumerate(zip(records, coeff_lines), start=1):
        canonical_hash = record.get("canonical_hash")
        if not canonical_hash:
            raise ReviewBatchError(f"record {index}: missing canonical_hash")
        if canonical_hash in seen:
            raise ReviewBatchError(f"record {index}: duplicate canonical_hash {canonical_hash}")
        seen.add(str(canonical_hash))

        record_coefficients = _validate_coefficients(record.get("exported_coefficients"), context=f"record {index}")
        try:
            text_coefficients_raw = json.loads(coeff_line)
        except json.JSONDecodeError as exc:
            raise ReviewBatchError(f"coefficient line {index}: invalid JSON: {exc}") from exc
        text_coefficients = _validate_coefficients(text_coefficients_raw, context=f"coefficient line {index}")
        if text_coefficients != record_coefficients:
            raise ReviewBatchError(f"record {index}: coefficient text export does not match JSONL record")

        item = dict(record)
        item["canonical_hash"] = str(canonical_hash)
        item["exported_coefficients"] = record_coefficients
        item["offline_verification_status"] = "prepared_unverified"
        item["verified_group_label"] = None
        validated.append(item)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return validated, review_dir, manifest


def polynomial_expression(coefficients: list[int], variable: str = "x") -> str:
    """Render coefficients `[a0, ..., a24]` as an explicit polynomial string."""

    terms: list[str] = []
    for power, coeff in enumerate(coefficients):
        if coeff == 0:
            continue
        if power == 0:
            base = "1"
        elif power == 1:
            base = variable
        else:
            base = f"{variable}^{power}"
        terms.append(f"({coeff})*{base}")
    return " + ".join(terms) if terms else "0"


def build_pari_input(records: list[dict[str, Any]]) -> str:
    lines = [
        "\\\\ Generated by scripts/igp24_offline_verify.py",
        "\\\\ Manual PARI/GP input for proxy-only IGP24 review candidates.",
        "\\\\ This script prints basic exact local checks. Uncomment polgalois only",
        "\\\\ after choosing the desired local exact-verification procedure.",
        "",
        "x = Pol([0, 1]);",
        "pol_from_coeffs(v) = sum(i = 1, #v, v[i] * x^(i - 1));",
        "",
        "candidates = [",
    ]
    for record in records:
        lines.append(f"  [\"{record['canonical_hash']}\", {json.dumps(record['exported_coefficients'])}],")
    lines.extend(
        [
            "];",
            "",
            "for (i = 1, #candidates,",
            "  h = candidates[i][1];",
            "  coeffs = candidates[i][2];",
            "  f = pol_from_coeffs(coeffs);",
            "  print(\"BEGIN \", h);",
            "  print(f);",
            "  print(\"polisirreducible=\", polisirreducible(f));",
            "  print(\"real_root_count=\", polsturm(f));",
            "  \\\\ Optional exact step, intentionally manual:",
            "  \\\\ print(\"polgalois=\", polgalois(f));",
            "  print(\"END \", h);",
            ");",
            "",
        ]
    )
    return "\n".join(lines)


def build_magma_input(records: list[dict[str, Any]]) -> str:
    lines = [
        "// Generated by scripts/igp24_offline_verify.py",
        "// Manual MAGMA input for proxy-only IGP24 review candidates.",
        "// Exact GaloisGroup calls are left commented for deliberate local use.",
        "",
        "Qx<x> := PolynomialRing(Rationals());",
        "candidates := [",
    ]
    for record in records:
        lines.append(f"  <\"{record['canonical_hash']}\", {json.dumps(record['exported_coefficients'])}>,")
    lines.extend(
        [
            "];",
            "",
            "for rec in candidates do",
            "  h := rec[1];",
            "  coeffs := rec[2];",
            "  f := &+[ Integers()!coeffs[i + 1] * x^i : i in [0..#coeffs - 1] ];",
            "  print \"BEGIN\", h;",
            "  print f;",
            "  print \"IsIrreducible\", IsIrreducible(f);",
            "  print \"Signature\", Signature(f);",
            "  // Optional exact step, intentionally manual:",
            "  // G, roots, data := GaloisGroup(f);",
            "  // print \"GaloisGroup\", G;",
            "  // print \"TransitiveGroupIdentification\", TransitiveGroupIdentification(G);",
            "  print \"END\", h;",
            "end for;",
            "",
        ]
    )
    return "\n".join(lines)


def probe_tool(executable: str) -> dict[str, Any]:
    path = shutil.which(executable)
    return {
        "executable": executable,
        "path": path,
        "available": path is not None,
    }


def maybe_run_tool(
    *,
    requested: bool,
    availability: dict[str, Any],
    args: list[str],
    cwd: Path,
    timeout_seconds: int,
    raw_output_path: Path,
) -> dict[str, Any]:
    if not requested:
        return {"requested": False, "executed": False, "status": "not_requested", "raw_output_path": None}
    if not availability["available"]:
        return {
            "requested": True,
            "executed": False,
            "status": "unavailable",
            "message": f"executable not found: {availability['executable']}",
            "raw_output_path": None,
        }

    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    raw_output_path.write_text(
        completed.stdout + ("\nSTDERR:\n" + completed.stderr if completed.stderr else ""),
        encoding="utf-8",
    )
    return {
        "requested": True,
        "executed": True,
        "status": "completed",
        "returncode": completed.returncode,
        "raw_output_path": str(raw_output_path),
    }


def build_verification_plan(
    *,
    records: list[dict[str, Any]],
    review_dir: Path,
    output_dir: Path,
    tool_availability: dict[str, dict[str, Any]],
    execution: dict[str, dict[str, Any]],
) -> str:
    lines = [
        "# IGP24 Offline Verification Plan",
        "",
        SAFETY_NOTE,
        "",
        f"- Source review batch: `{review_dir}`",
        f"- Selected records: {len(records)}",
        f"- Output directory: `{output_dir}`",
        f"- PARI/GP available: `{tool_availability['pari']['available']}`",
        f"- MAGMA available: `{tool_availability['magma']['available']}`",
        f"- PARI/GP executed: `{execution['pari']['executed']}`",
        f"- MAGMA executed: `{execution['magma']['executed']}`",
        "",
        "Generated files:",
        f"- `{output_dir / PARI_INPUT_GP}`",
        f"- `{output_dir / MAGMA_INPUT_M}`",
        f"- `{output_dir / OFFLINE_MANIFEST_JSON}`",
        "",
        "Manual next steps:",
        "1. Review the candidate table below and the generated verifier scripts.",
        "2. Run local PARI/GP or MAGMA manually, or rerun this helper with an explicit `--run_pari`/`--run_magma` flag after confirming the local tool is available.",
        "3. Record raw verifier output and only then promote any exact group label.",
        "4. Keep any SAIR packaging or submission separate, explicit, and human-controlled.",
        "",
        "| Rank | Score | Hash | r | Strategy | Height |",
        "| ---: | ---: | --- | ---: | --- | ---: |",
    ]
    for rank, record in enumerate(records, start=1):
        score = record.get("score")
        score_text = f"{float(score):.6f}" if score is not None else "NA"
        lines.append(
            "| "
            f"{rank} | {score_text} | `{record['canonical_hash'][:12]}` | "
            f"{record.get('real_root_count')} | `{record.get('source_strategy')}` | "
            f"{record.get('coefficient_height')} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_manifest(
    *,
    records: list[dict[str, Any]],
    review_dir: Path,
    source_review_manifest: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    tool_availability: dict[str, dict[str, Any]],
    execution: dict[str, dict[str, Any]],
    timeout_seconds: int,
) -> dict[str, Any]:
    pari_executed = bool(execution["pari"]["executed"])
    magma_executed = bool(execution["magma"]["executed"])
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_offline_verify.py",
        "source_commit": source_commit,
        "command": command,
        "source_review_batch_dir": str(review_dir),
        "source_review_manifest": source_review_manifest,
        "selected_records": len(records),
        "selected_hashes": [record["canonical_hash"] for record in records],
        "coefficient_shape": {"length": 25, "leading_coefficient": 1},
        "timeout_seconds": timeout_seconds,
        "tool_availability": tool_availability,
        "execution": execution,
        "output_files": {
            "offline_verification_manifest_json": str(output_dir / OFFLINE_MANIFEST_JSON),
            "pari_input_gp": str(output_dir / PARI_INPUT_GP),
            "magma_input_m": str(output_dir / MAGMA_INPUT_M),
            "verification_plan_md": str(output_dir / VERIFICATION_PLAN_MD),
        },
        "safety": {
            "network_calls": False,
            "sair_submission": False,
            "auto_submission": False,
            "pari_executed": pari_executed,
            "magma_executed": magma_executed,
            "exact_group_labels_parsed": False,
            "exact_group_claims": False,
            "dry_run_preparation_only": not (pari_executed or magma_executed),
            "note": SAFETY_NOTE,
        },
    }


def write_outputs(
    *,
    records: list[dict[str, Any]],
    review_dir: Path,
    source_review_manifest: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    pari_executable: str,
    magma_executable: str,
    run_pari: bool,
    run_magma: bool,
    timeout_seconds: int,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pari_path = output_dir / PARI_INPUT_GP
    magma_path = output_dir / MAGMA_INPUT_M
    pari_path.write_text(build_pari_input(records), encoding="utf-8")
    magma_path.write_text(build_magma_input(records), encoding="utf-8")

    tool_availability = {
        "pari": probe_tool(pari_executable),
        "magma": probe_tool(magma_executable),
    }
    execution = {
        "pari": maybe_run_tool(
            requested=run_pari,
            availability=tool_availability["pari"],
            args=[tool_availability["pari"]["path"] or pari_executable, "-q", str(pari_path)],
            cwd=output_dir,
            timeout_seconds=timeout_seconds,
            raw_output_path=output_dir / PARI_RAW_OUTPUT,
        ),
        "magma": maybe_run_tool(
            requested=run_magma,
            availability=tool_availability["magma"],
            args=[tool_availability["magma"]["path"] or magma_executable, str(magma_path)],
            cwd=output_dir,
            timeout_seconds=timeout_seconds,
            raw_output_path=output_dir / MAGMA_RAW_OUTPUT,
        ),
    }

    plan_path = output_dir / VERIFICATION_PLAN_MD
    plan_path.write_text(
        build_verification_plan(
            records=records,
            review_dir=review_dir,
            output_dir=output_dir,
            tool_availability=tool_availability,
            execution=execution,
        ),
        encoding="utf-8",
    )
    manifest = build_manifest(
        records=records,
        review_dir=review_dir,
        source_review_manifest=source_review_manifest,
        output_dir=output_dir,
        command=command,
        source_commit=source_commit,
        tool_availability=tool_availability,
        execution=execution,
        timeout_seconds=timeout_seconds,
    )
    manifest_path = output_dir / OFFLINE_MANIFEST_JSON
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "offline_verification_manifest_json": manifest_path,
        "pari_input_gp": pari_path,
        "magma_input_m": magma_path,
        "verification_plan_md": plan_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare safe offline exact-verifier inputs for an IGP24 review batch")
    parser.add_argument("review_batch", type=Path, help="Review-batch directory with verification_batch.jsonl")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--run_pari", action="store_true", help="Explicitly run local PARI/GP if available")
    parser.add_argument("--run_magma", action="store_true", help="Explicitly run local MAGMA if available")
    parser.add_argument("--pari_executable", default="gp")
    parser.add_argument("--magma_executable", default="magma")
    parser.add_argument("--timeout_seconds", type=int, default=60)
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        records, review_dir, source_review_manifest = load_review_batch(args.review_batch)
    except (FileNotFoundError, ReviewBatchError) as exc:
        parser.error(str(exc))

    output_dir = args.output_dir.resolve()
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_offline_verify.py", *argv]
    paths = write_outputs(
        records=records,
        review_dir=review_dir,
        source_review_manifest=source_review_manifest,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        pari_executable=args.pari_executable,
        magma_executable=args.magma_executable,
        run_pari=args.run_pari,
        run_magma=args.run_magma,
        timeout_seconds=max(1, int(args.timeout_seconds)),
    )
    manifest = json.loads(paths["offline_verification_manifest_json"].read_text(encoding="utf-8"))

    print(f"loaded_review_records\t{len(records)}")
    print(f"pari_available\t{manifest['tool_availability']['pari']['available']}")
    print(f"magma_available\t{manifest['tool_availability']['magma']['available']}")
    print(f"pari_executed\t{manifest['safety']['pari_executed']}")
    print(f"magma_executed\t{manifest['safety']['magma_executed']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
