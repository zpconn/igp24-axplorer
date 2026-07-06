#!/usr/bin/env python3
"""Build a final manual IGP24 submission-review package.

This helper is local/file-only. It copies saved evidence and writes a manifest,
checklist, and coefficient-only candidate file for human review. It never calls
SAIR, never submits candidates, never calls Magma/PARI, and never performs
network work.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit


PLAN_JSONL = "submission_plan.jsonl"
PLAN_SUMMARY_JSON = "submission_plan_summary.json"
PLAN_REPORT_MD = "submission_plan_report.md"
PLAN_CANDIDATES_TXT = "submission_candidates.txt"
PACKAGE_MANIFEST_JSON = "package_manifest.json"
PACKAGE_CHECKLIST_MD = "submission_checklist.md"
PACKAGE_COEFFICIENTS_TXT = "submission_coefficients.txt"
PACKAGE_COEFFICIENTS_JSONL = "submission_coefficients.jsonl"

EVIDENCE_FILES = (
    "offline_verification_manifest.json",
    "verification_batch.jsonl",
    "verification_coefficients.txt",
    "pari_input.gp",
    "pari_nfdisc_results.jsonl",
    "pari_nfdisc_summary.json",
    "pari_nfdisc_report.md",
    "sympy_signature_results.jsonl",
    "sympy_signature_summary.json",
    "sympy_signature_report.md",
    "sympy_nfdisc_results.jsonl",
    "sympy_nfdisc_summary.json",
    "sympy_nfdisc_report.md",
    "magma_verification_results.jsonl",
    "magma_verification_summary.json",
    "magma_verification_report.md",
)
ONLINE_MAGMA_FILES = (
    "online_magma_manual_results.jsonl",
    "online_magma_manual_summary.json",
    "online_magma_manual_report.md",
    "online_magma_pasted_outputs_template.jsonl",
)


class PackageError(ValueError):
    """Raised when the requested package would be incomplete or unsafe."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def short_hash(value: Any) -> str:
    return str(value or "")[:12]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_coefficients(value: Any, *, context: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 25 or value[-1] != 1:
        raise PackageError(f"{context}: expected 25 exported coefficients ending in 1")
    if any(not isinstance(item, int) for item in value):
        raise PackageError(f"{context}: coefficients must be integers")
    return list(value)


def copy_file(src: Path, dst: Path) -> dict[str, Any]:
    if not src.exists() or not src.is_file():
        raise PackageError(f"missing required file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "relative_path": str(dst),
        "source_path": str(src),
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
    }


def copy_tree(src: Path, dst: Path) -> list[dict[str, Any]]:
    if not src.exists() or not src.is_dir():
        raise PackageError(f"missing required directory: {src}")
    copied: list[dict[str, Any]] = []
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(item for item in src.rglob("*") if item.is_file()):
        relative = path.relative_to(src)
        copied.append(copy_file(path, dst / relative))
    return copied


def copy_if_present(src: Path, dst: Path) -> dict[str, Any] | None:
    if not src.exists():
        return None
    return copy_file(src, dst)


def load_baseline_info(path: Path) -> dict[str, Any]:
    rows_loaded = 0
    pairs: set[tuple[str, int]] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            rows_loaded += 1
            label = str(row.get("label") or "")
            try:
                r_value = int(str(row.get("r") or ""))
            except ValueError:
                continue
            if label and r_value:
                pairs.add((label, r_value))
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "rows_loaded": rows_loaded,
        "pairs": len(pairs),
        "header": fieldnames,
    }


def index_by_hash(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_hash = str(row.get("candidate_hash") or row.get("canonical_hash") or "")
        if candidate_hash:
            indexed[candidate_hash] = row
    return indexed


def validate_plan_rows(rows: list[dict[str, Any]], expected_hashes: list[str]) -> list[dict[str, Any]]:
    if len(rows) != len(expected_hashes):
        raise PackageError(f"expected {len(expected_hashes)} plan rows, found {len(rows)}")
    expected_set = set(expected_hashes)
    actual_set = {str(row.get("canonical_hash") or "") for row in rows}
    if actual_set != expected_set:
        raise PackageError(f"plan hash set mismatch: expected {sorted(expected_set)}, found {sorted(actual_set)}")
    pair_counts = Counter(str(row.get("pair_key") or "") for row in rows)
    duplicate_pairs = sorted(pair for pair, count in pair_counts.items() if count != 1)
    if "" in pair_counts:
        raise PackageError("expected every plan row to include pair_key")
    if duplicate_pairs:
        raise PackageError(f"expected one row per pair; duplicate/missing pair counts for {duplicate_pairs}")
    for row in rows:
        candidate_hash = str(row.get("canonical_hash") or "")
        prefix = candidate_hash[:12]
        validate_coefficients(row.get("exported_coefficients"), context=prefix)
        required = {
            "baseline_status": "non_baseline_candidate",
            "scoreability_status": "new_pair_candidate",
            "exact_r_status": "ok",
            "exact_nfdisc_status": "ok",
            "discriminant_rank_category": "exact_nfdisc",
        }
        for key, expected in required.items():
            if row.get(key) != expected:
                raise PackageError(f"{prefix}: expected {key}={expected!r}, found {row.get(key)!r}")
    return rows


def summarize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": row.get("submission_plan_rank"),
        "pair_key": row.get("pair_key"),
        "verified_group_label": row.get("verified_group_label"),
        "expected_r": row.get("expected_r"),
        "expected_r_source": row.get("expected_r_source"),
        "canonical_hash": row.get("canonical_hash"),
        "short_hash": row.get("short_hash"),
        "baseline_status": row.get("baseline_status"),
        "baseline_rows": row.get("baseline_rows"),
        "scoreability_status": row.get("scoreability_status"),
        "exact_r_status": row.get("exact_r_status"),
        "exact_nfdisc_status": row.get("exact_nfdisc_status"),
        "exact_nfdisc_source": row.get("exact_nfdisc_source"),
        "exact_nfdisc_abs": row.get("exact_nfdisc_abs"),
        "discriminant_rank_category": row.get("discriminant_rank_category"),
    }


def raw_magma_xml_paths(raw_magma_dir: Path, rows: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for row in rows:
        prefix = short_hash(row.get("canonical_hash"))
        matches = sorted(raw_magma_dir.glob(f"online_magma_manual_output_{prefix}_*.xml"))
        if not matches:
            raise PackageError(f"{prefix}: missing raw saved Magma XML in {raw_magma_dir}")
        paths.append(matches[-1])
    return paths


def build_manifest(
    *,
    rows: list[dict[str, Any]],
    plan_summary: dict[str, Any],
    baseline_info: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    copied_files: list[dict[str, Any]],
    evidence_dir: Path,
    plan_dir: Path,
    raw_magma_dir: Path,
    local_tool_availability: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "record_type": "igp24_manual_submission_package_manifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_submission_package.py",
        "source_commit": source_commit,
        "command": command,
        "output_dir": str(output_dir),
        "plan_dir": str(plan_dir),
        "evidence_dir": str(evidence_dir),
        "raw_magma_dir": str(raw_magma_dir),
        "selected_records": len(rows),
        "selected_hashes": [str(row.get("canonical_hash")) for row in rows],
        "selected_pairs": [str(row.get("pair_key")) for row in rows],
        "selected_record_summaries": [summarize_row(row) for row in rows],
        "baseline": baseline_info,
        "plan_summary": {
            "source_commit": plan_summary.get("source_commit"),
            "baseline_status_counts": plan_summary.get("baseline_status_counts"),
            "scoreability_status_counts": plan_summary.get("scoreability_status_counts"),
            "exact_r_status_counts": plan_summary.get("exact_r_status_counts"),
            "exact_nfdisc_status_counts": plan_summary.get("exact_nfdisc_status_counts"),
            "discriminant_rank_category_counts": plan_summary.get("discriminant_rank_category_counts"),
        },
        "local_tool_availability": local_tool_availability,
        "submission_files": {
            "coefficient_txt": str(output_dir / PACKAGE_COEFFICIENTS_TXT),
            "coefficient_jsonl": str(output_dir / PACKAGE_COEFFICIENTS_JSONL),
            "manifest_json": str(output_dir / PACKAGE_MANIFEST_JSON),
            "checklist_md": str(output_dir / PACKAGE_CHECKLIST_MD),
        },
        "copied_files": copied_files,
        "safety": {
            "local_file_only": True,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "automated_online_verification": False,
            "gpu_training": False,
            "cpu_search_loop": False,
            "contains_api_keys": False,
            "manual_review_package_only": True,
        },
    }


def build_checklist(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    pair_counts = Counter(str(row.get("pair_key") or "") for row in rows)
    one_row_per_pair = bool(rows) and all(count == 1 for count in pair_counts.values())
    all_absent_from_baseline = all(row.get("baseline_status") == "non_baseline_candidate" for row in rows)
    exact_label_sources = all(row.get("verified_group_label") for row in rows)
    exact_r_sources = all(row.get("exact_r_status") == "ok" and row.get("expected_r_source") for row in rows)
    exact_nfdisc_sources = all(row.get("exact_nfdisc_status") == "ok" and row.get("exact_nfdisc_source") for row in rows)
    no_submission = not manifest.get("safety", {}).get("sair_submission") and not manifest.get("safety", {}).get("sair_api_calls")
    local_tools = manifest.get("local_tool_availability", {})
    cross_check_unavailable = not local_tools.get("magma", {}).get("available") and not local_tools.get("pari_gp", {}).get("available")

    def mark(value: bool) -> str:
        return "x" if value else " "

    lines = [
        "# IGP24 Manual Submission Package Checklist",
        "",
        "This package is for manual review only. No SAIR submission or API call was performed.",
        "",
        "## Builder-Verified Checks",
        "",
        f"- [{mark(manifest.get('selected_records') == 5)}] Exactly five rows: `{manifest.get('selected_records') == 5}`",
        f"- [{mark(one_row_per_pair)}] One row per `(24Tt, r)` pair.",
        f"- [{mark(all_absent_from_baseline)}] All selected rows are absent from the official baseline.",
        f"- [{mark(exact_label_sources)}] Exact labels are backed by saved/manual Magma output.",
        f"- [{mark(exact_r_sources)}] Exact `r` is backed by local SymPy fallback evidence.",
        f"- [{mark(exact_nfdisc_sources)}] Exact `nfdisc` is backed by local SymPy fallback evidence.",
        f"- [{mark(cross_check_unavailable)}] Magma/PARI independent cross-check is still unavailable on this host, if not separately supplied.",
        f"- [{mark(no_submission)}] No SAIR/API submission has been performed.",
        "",
        "## Selected Rows",
        "",
        "| rank | pair | hash | label | r source | nfdisc source | nfdisc | status |",
        "| ---: | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("submission_plan_rank")),
                    f"`{row.get('pair_key')}`",
                    f"`{row.get('short_hash')}`",
                    str(row.get("verified_group_label")),
                    str(row.get("expected_r_source")),
                    str(row.get("exact_nfdisc_source")),
                    str(row.get("exact_nfdisc_abs")),
                    str(row.get("scoreability_status")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Package Files",
            "",
            f"- Coefficients: `{manifest.get('submission_files', {}).get('coefficient_txt')}`",
            f"- Structured coefficients: `{manifest.get('submission_files', {}).get('coefficient_jsonl')}`",
            f"- Manifest: `{manifest.get('submission_files', {}).get('manifest_json')}`",
            "",
            "## Safety",
            "",
            "- This helper is local/file-only.",
            "- It did not call Magma, PARI, SAIR, online calculators, training, GPU sampling, or search loops.",
            "- The coefficient file is not submitted automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def build_package(
    *,
    plan_dir: Path,
    evidence_dir: Path,
    baseline_csv: Path,
    raw_magma_dir: Path,
    output_dir: Path,
    expected_hashes: list[str],
    command: list[str],
    source_commit: str | None,
    local_tool_availability: dict[str, Any],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_rows = validate_plan_rows(read_jsonl(plan_dir / PLAN_JSONL), expected_hashes)
    plan_summary = json.loads((plan_dir / PLAN_SUMMARY_JSON).read_text(encoding="utf-8"))

    copied_files: list[dict[str, Any]] = []
    plan_out = output_dir / "plan"
    for name in (PLAN_JSONL, PLAN_SUMMARY_JSON, PLAN_REPORT_MD, PLAN_CANDIDATES_TXT):
        copied = copy_if_present(plan_dir / name, plan_out / name)
        if copied:
            copied_files.append(copied)

    evidence_out = output_dir / "evidence"
    for name in EVIDENCE_FILES:
        copied = copy_if_present(evidence_dir / name, evidence_out / name)
        if copied:
            copied_files.append(copied)
    online_out = evidence_out / "online_magma_manual"
    for name in ONLINE_MAGMA_FILES:
        copied = copy_if_present(evidence_dir / "online_magma_manual" / name, online_out / name)
        if copied:
            copied_files.append(copied)
    copied_files.extend(copy_tree(evidence_dir / "online_magma_manual" / "copy_paste_scripts", online_out / "copy_paste_scripts"))
    copied_files.extend(copy_tree(evidence_dir / "magma_candidate_scripts", evidence_out / "magma_candidate_scripts"))

    raw_out = output_dir / "raw_magma_xml"
    for path in raw_magma_xml_paths(raw_magma_dir, plan_rows):
        copied_files.append(copy_file(path, raw_out / path.name))

    baseline_out = output_dir / "baseline" / baseline_csv.name
    copied_files.append(copy_file(baseline_csv, baseline_out))
    baseline_info = load_baseline_info(baseline_csv)

    coefficients_txt = output_dir / PACKAGE_COEFFICIENTS_TXT
    with coefficients_txt.open("w", encoding="utf-8") as handle:
        for row in plan_rows:
            coefficients = validate_coefficients(row.get("exported_coefficients"), context=short_hash(row.get("canonical_hash")))
            handle.write(",".join(str(value) for value in coefficients) + "\n")
    copied_files.append(
        {
            "relative_path": str(coefficients_txt),
            "source_path": "generated",
            "bytes": coefficients_txt.stat().st_size,
            "sha256": sha256_file(coefficients_txt),
        }
    )

    coefficients_jsonl = output_dir / PACKAGE_COEFFICIENTS_JSONL
    write_jsonl(
        coefficients_jsonl,
        [
            {
                "rank": row.get("submission_plan_rank"),
                "pair_key": row.get("pair_key"),
                "canonical_hash": row.get("canonical_hash"),
                "coefficients": validate_coefficients(row.get("exported_coefficients"), context=short_hash(row.get("canonical_hash"))),
            }
            for row in plan_rows
        ],
    )
    copied_files.append(
        {
            "relative_path": str(coefficients_jsonl),
            "source_path": "generated",
            "bytes": coefficients_jsonl.stat().st_size,
            "sha256": sha256_file(coefficients_jsonl),
        }
    )

    manifest = build_manifest(
        rows=plan_rows,
        plan_summary=plan_summary,
        baseline_info=baseline_info,
        output_dir=output_dir,
        command=command,
        source_commit=source_commit,
        copied_files=copied_files,
        evidence_dir=evidence_dir,
        plan_dir=plan_dir,
        raw_magma_dir=raw_magma_dir,
        local_tool_availability=local_tool_availability,
    )
    manifest_path = output_dir / PACKAGE_MANIFEST_JSON
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist_path = output_dir / PACKAGE_CHECKLIST_MD
    checklist_path.write_text(build_checklist(manifest, plan_rows), encoding="utf-8")
    return {
        "package_manifest_json": manifest_path,
        "submission_checklist_md": checklist_path,
        "submission_coefficients_txt": coefficients_txt,
        "submission_coefficients_jsonl": coefficients_jsonl,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local/manual IGP24 submission-review package")
    parser.add_argument("--plan_dir", type=Path, required=True)
    parser.add_argument("--evidence_dir", type=Path, required=True)
    parser.add_argument("--baseline_csv", type=Path, required=True)
    parser.add_argument("--raw_magma_dir", type=Path, default=REPO_ROOT / "data" / "igp24")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--candidate_hash", action="append", default=[], help="Expected canonical hash; repeat exactly once per selected row")
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    expected_hashes = [str(value) for value in args.candidate_hash or [] if str(value)]
    if not expected_hashes:
        parser.error("at least one --candidate_hash is required")
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_submission_package.py", *argv]
    local_tool_availability = {
        "magma": {"available": shutil.which("magma") is not None},
        "pari_gp": {"available": shutil.which("gp") is not None},
    }
    try:
        paths = build_package(
            plan_dir=args.plan_dir.resolve(),
            evidence_dir=args.evidence_dir.resolve(),
            baseline_csv=args.baseline_csv.resolve(),
            raw_magma_dir=args.raw_magma_dir.resolve(),
            output_dir=args.output_dir.resolve(),
            expected_hashes=expected_hashes,
            command=command,
            source_commit=get_source_commit(args.repo_root.resolve()),
            local_tool_availability=local_tool_availability,
        )
    except (FileNotFoundError, json.JSONDecodeError, PackageError, ValueError) as exc:
        parser.error(str(exc))
    manifest = json.loads(paths["package_manifest_json"].read_text(encoding="utf-8"))
    print(f"selected_records\t{manifest['selected_records']}")
    print(f"selected_pairs\t{json.dumps(manifest['selected_pairs'])}")
    print(f"scoreability_status_counts\t{json.dumps(manifest['plan_summary'].get('scoreability_status_counts'), sort_keys=True)}")
    print(f"exact_r_status_counts\t{json.dumps(manifest['plan_summary'].get('exact_r_status_counts'), sort_keys=True)}")
    print(f"exact_nfdisc_status_counts\t{json.dumps(manifest['plan_summary'].get('exact_nfdisc_status_counts'), sort_keys=True)}")
    print(f"sair_submission\t{manifest['safety']['sair_submission']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
