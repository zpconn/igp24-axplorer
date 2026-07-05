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
import glob
import hashlib
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl
from src.igp24.verifiers.magma import MagmaVerifier


VERIFICATION_BATCH_JSONL = "verification_batch.jsonl"
VERIFICATION_COEFFICIENTS_TXT = "verification_coefficients.txt"
REVIEW_MANIFEST_JSON = "manifest.json"
OFFLINE_MANIFEST_JSON = "offline_verification_manifest.json"
PARI_INPUT_GP = "pari_input.gp"
MAGMA_INPUT_M = "magma_input.m"
VERIFICATION_PLAN_MD = "verification_plan.md"
PARI_RAW_OUTPUT = "pari_raw_output.txt"
MAGMA_RESULTS_JSONL = "magma_verification_results.jsonl"
MAGMA_SUMMARY_JSON = "magma_verification_summary.json"
MAGMA_REPORT_MD = "magma_verification_report.md"
MAGMA_CACHE_JSON = "magma_verification_cache.json"
MAGMA_CANDIDATE_SCRIPTS_DIR = "magma_candidate_scripts"
MAGMA_RAW_OUTPUT_DIR = "magma_raw_outputs"
ONLINE_MAGMA_MANUAL_DIR = "online_magma_manual"
ONLINE_MAGMA_COPY_PASTE_SCRIPTS_DIR = "copy_paste_scripts"
ONLINE_MAGMA_PASTED_OUTPUT_TEMPLATE_JSONL = "online_magma_pasted_outputs_template.jsonl"
ONLINE_MAGMA_RESULTS_JSONL = "online_magma_manual_results.jsonl"
ONLINE_MAGMA_SUMMARY_JSON = "online_magma_manual_summary.json"
ONLINE_MAGMA_REPORT_MD = "online_magma_manual_report.md"
MAGMA_SCRIPT_SCHEMA_VERSION = 1
ONLINE_MAGMA_MANUAL_SCHEMA_VERSION = 1
SAFETY_NOTE = (
    "Offline verifier artifact. No SAIR submission, network call, or "
    "auto-submission is performed; exact group labels are recorded only when "
    "an explicit local MAGMA run returns parseable provenance."
)
MAGMA_SAFETY_NOTE = (
    "Offline MAGMA verification is explicit, local-only, timeout-bound, and "
    "separate from GPU training/sampling and CPU proxy scoring."
)
ONLINE_MAGMA_CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
ONLINE_MAGMA_CALCULATOR_VERSION = "2.29-8"
ONLINE_MAGMA_MAX_TIME_SECONDS = 60
ONLINE_MAGMA_MAX_INPUT_BYTES = 50000
ONLINE_MAGMA_SAFETY_NOTE = (
    "Online MAGMA calculator artifacts are manual copy/paste aids only. The "
    "helper does not submit requests, batch online work, call SAIR, or run "
    "inside training, GPU sampling, or CPU proxy scoring."
)
DEFAULT_MAGMA_SEARCH_PATTERNS = [
    "/usr/local/bin/magma",
    "/usr/bin/magma",
    "/opt/magma*/magma",
    "/opt/Magma*/magma",
    "/usr/local/magma*/magma",
    "/usr/local/Magma*/magma",
    str(Path.home() / "magma*" / "magma"),
    str(Path.home() / "Magma*" / "magma"),
    str(Path.home() / "bin" / "magma"),
]


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


def _validate_decoded_coefficients(value: Any, *, context: str) -> list[int]:
    if not isinstance(value, list):
        raise ReviewBatchError(f"{context}: decoded coefficients must be a JSON list")
    if len(value) != 24:
        raise ReviewBatchError(f"{context}: expected 24 decoded coefficients, found {len(value)}")
    if any(not isinstance(item, int) for item in value):
        raise ReviewBatchError(f"{context}: decoded coefficients must all be integers")
    return list(value) + [1]


def _coerce_exported_coefficients(record: dict[str, Any], *, context: str) -> list[int]:
    if "exported_coefficients" in record:
        return _validate_coefficients(record.get("exported_coefficients"), context=f"{context}.exported_coefficients")
    if "coefficients" in record:
        value = record.get("coefficients")
        if isinstance(value, list) and len(value) == 24:
            return _validate_decoded_coefficients(value, context=f"{context}.coefficients")
        return _validate_coefficients(value, context=f"{context}.coefficients")
    if "decoded_coefficients" in record:
        return _validate_decoded_coefficients(record.get("decoded_coefficients"), context=f"{context}.decoded_coefficients")
    raise ReviewBatchError(f"{context}: missing exported_coefficients, coefficients, or decoded_coefficients")


def coefficients_sha256(coefficients: list[int]) -> str:
    payload = json.dumps(coefficients, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def command_text(argv: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def _synthetic_hash(prefix: str, index: int, coefficients: list[int] | None = None) -> str:
    if coefficients is None:
        return f"{prefix}_{index:04d}"
    return f"coeff_{coefficients_sha256(coefficients)[:16]}"


def _candidate_record_from_raw(
    raw: Any,
    *,
    index: int,
    source_path: Path,
    source_kind: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "canonical_hash": f"invalid_{index:04d}",
            "exported_coefficients": None,
            "source_input_path": str(source_path),
            "source_input_kind": source_kind,
            "input_index": index,
            "input_validation_error": "record must be a JSON object",
            "offline_verification_status": "invalid_input",
            "verified_group_label": None,
        }

    item = dict(raw)
    item["source_input_path"] = str(source_path)
    item["source_input_kind"] = source_kind
    item["input_index"] = index
    if item.get("input_validation_error") and not any(
        key in item for key in ("exported_coefficients", "coefficients", "decoded_coefficients")
    ):
        item["canonical_hash"] = str(item.get("canonical_hash") or f"invalid_{index:04d}")
        item["exported_coefficients"] = None
        item["offline_verification_status"] = "invalid_input"
        item["verified_group_label"] = None
        return item
    try:
        coefficients = _coerce_exported_coefficients(item, context=f"record {index}")
    except ReviewBatchError as exc:
        item["canonical_hash"] = str(item.get("canonical_hash") or f"invalid_{index:04d}")
        item["exported_coefficients"] = None
        item["input_validation_error"] = str(exc)
        item["offline_verification_status"] = "invalid_input"
        item["verified_group_label"] = None
        return item

    item["exported_coefficients"] = coefficients
    item["coefficient_sha256"] = coefficients_sha256(coefficients)
    item["canonical_hash"] = str(item.get("canonical_hash") or _synthetic_hash("coeff", index, coefficients))
    item["offline_verification_status"] = "prepared_unverified"
    item["verified_group_label"] = None
    return item


def load_candidate_jsonl(path: str | Path) -> tuple[list[dict[str, Any]], Path, dict[str, Any]]:
    """Load candidate records from a JSONL file, preserving invalid rows as records."""

    source_path = Path(path).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"candidate JSONL file does not exist: {source_path}")

    records: list[dict[str, Any]] = []
    for index, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raw = {"input_validation_error": f"invalid JSON: {exc}"}
        records.append(_candidate_record_from_raw(raw, index=index, source_path=source_path, source_kind="candidate_jsonl"))
    manifest = {
        "input_kind": "candidate_jsonl",
        "source_path": str(source_path),
        "records_loaded": len(records),
        "safety": {"proxy_only": True, "review_export_only": False},
    }
    return records, source_path, manifest


def load_coefficients_file(path: str | Path) -> tuple[list[dict[str, Any]], Path, dict[str, Any]]:
    """Load one JSON coefficient vector per line from a text file."""

    source_path = Path(path).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"coefficient file does not exist: {source_path}")

    records: list[dict[str, Any]] = []
    for index, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            raw_coefficients = json.loads(line)
            raw = {"exported_coefficients": raw_coefficients}
        except json.JSONDecodeError as exc:
            raw = {"input_validation_error": f"invalid JSON: {exc}"}
        records.append(_candidate_record_from_raw(raw, index=index, source_path=source_path, source_kind="coefficients_file"))
    manifest = {
        "input_kind": "coefficients_file",
        "source_path": str(source_path),
        "records_loaded": len(records),
        "safety": {"proxy_only": True, "review_export_only": False},
    }
    return records, source_path, manifest


def load_verification_input(path: str | Path) -> tuple[list[dict[str, Any]], Path, dict[str, Any], str]:
    """Load a review-batch directory, candidate JSONL, or coefficient text file."""

    source_path = Path(path).resolve()
    if source_path.is_dir():
        records, loaded_path, manifest = load_review_batch(source_path)
        return records, loaded_path, manifest, "review_batch"
    if source_path.suffix == ".jsonl":
        records, loaded_path, manifest = load_candidate_jsonl(source_path)
        return records, loaded_path, manifest, "candidate_jsonl"
    records, loaded_path, manifest = load_coefficients_file(source_path)
    return records, loaded_path, manifest, "coefficients_file"


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
        item["coefficient_sha256"] = coefficients_sha256(record_coefficients)
        item["source_input_path"] = str(review_dir)
        item["source_input_kind"] = "review_batch"
        item["input_index"] = index
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


def safe_filename(value: str, *, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned[:80] or fallback


def build_online_magma_manual_input(record: dict[str, Any]) -> str:
    """Build a one-candidate script suitable for manual online calculator paste."""

    coefficients = record.get("exported_coefficients")
    if not isinstance(coefficients, list):
        raise ReviewBatchError("record has no validated exported_coefficients")
    canonical_hash = str(record.get("canonical_hash") or "")
    return "\n".join(
        [
            "// Generated by scripts/igp24_offline_verify.py",
            f"// Online MAGMA manual copy/paste script schema {ONLINE_MAGMA_MANUAL_SCHEMA_VERSION}.",
            f"// Paste manually at {ONLINE_MAGMA_CALCULATOR_URL}; do not batch-submit.",
            f"// Observed calculator caps: {ONLINE_MAGMA_MAX_TIME_SECONDS}s, {ONLINE_MAGMA_MAX_INPUT_BYTES} bytes, Magma V{ONLINE_MAGMA_CALCULATOR_VERSION}.",
            "SetSeed(1);",
            "Qx<x> := PolynomialRing(Rationals());",
            f"candidate_hash := {json.dumps(canonical_hash)};",
            f"coeffs := {json.dumps(coefficients)};",
            "f := &+[ Integers()!coeffs[i + 1] * x^i : i in [0..#coeffs - 1] ];",
            "print \"IGP24_BEGIN\", candidate_hash;",
            "print \"IGP24_DEGREE\", Degree(f);",
            "print \"IGP24_IS_IRREDUCIBLE\", IsIrreducible(f);",
            "G, roots, data := GaloisGroup(f);",
            "print \"IGP24_GALOIS_GROUP\", G;",
            "tid := TransitiveGroupIdentification(G);",
            "print \"IGP24_TRANSITIVE_GROUP_ID\", tid;",
            "print \"IGP24_END\", candidate_hash;",
            "quit;",
            "",
        ]
    )


def build_magma_verification_input(record: dict[str, Any], *, timeout_seconds: int) -> str:
    """Build a per-candidate MAGMA script that attempts exact Galois labeling."""

    coefficients = record.get("exported_coefficients")
    if not isinstance(coefficients, list):
        raise ReviewBatchError("record has no validated exported_coefficients")
    canonical_hash = str(record.get("canonical_hash") or "")
    return "\n".join(
        [
            "// Generated by scripts/igp24_offline_verify.py",
            f"// MAGMA per-candidate exact verifier script schema {MAGMA_SCRIPT_SCHEMA_VERSION}.",
            f"// External timeout managed by Python helper: {int(timeout_seconds)} seconds.",
            "SetSeed(1);",
            "Qx<x> := PolynomialRing(Rationals());",
            f"candidate_hash := {json.dumps(canonical_hash)};",
            f"coeffs := {json.dumps(coefficients)};",
            "f := &+[ Integers()!coeffs[i + 1] * x^i : i in [0..#coeffs - 1] ];",
            "print \"IGP24_BEGIN\", candidate_hash;",
            "print \"IGP24_DEGREE\", Degree(f);",
            "print \"IGP24_IS_IRREDUCIBLE\", IsIrreducible(f);",
            "G, roots, data := GaloisGroup(f);",
            "print \"IGP24_GALOIS_GROUP\", G;",
            "tid := TransitiveGroupIdentification(G);",
            "print \"IGP24_TRANSITIVE_GROUP_ID\", tid;",
            "print \"IGP24_END\", candidate_hash;",
            "quit;",
            "",
        ]
    )


def build_magma_command(executable_path: str, script_path: Path) -> list[str]:
    return [executable_path, str(script_path)]


def parse_magma_output(text: str) -> dict[str, Any]:
    """Parse the machine-readable markers emitted by build_magma_verification_input."""

    candidate_hash: str | None = None
    transitive_group_id: int | None = None
    signature_r: int | None = None
    degree: int | None = None
    is_irreducible: bool | None = None
    galois_group_text: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip().replace('"', "")
        if not line:
            continue
        if "IGP24_BEGIN" in line:
            value = line.split("IGP24_BEGIN", 1)[1].strip()
            if value:
                candidate_hash = value.split()[0]
        elif "IGP24_DEGREE" in line:
            numbers = re.findall(r"-?\d+", line.split("IGP24_DEGREE", 1)[1])
            if numbers:
                degree = int(numbers[-1])
        elif "IGP24_IS_IRREDUCIBLE" in line:
            lowered = line.lower()
            if "true" in lowered:
                is_irreducible = True
            elif "false" in lowered:
                is_irreducible = False
        elif "IGP24_SIGNATURE" in line:
            numbers = re.findall(r"-?\d+", line.split("IGP24_SIGNATURE", 1)[1])
            if numbers:
                signature_r = int(numbers[0])
        elif "IGP24_GALOIS_GROUP" in line:
            value = line.split("IGP24_GALOIS_GROUP", 1)[1].strip()
            if value:
                galois_group_text = value
        elif "IGP24_TRANSITIVE_GROUP_ID" in line:
            numbers = re.findall(r"\d+", line.split("IGP24_TRANSITIVE_GROUP_ID", 1)[1])
            if numbers:
                transitive_group_id = int(numbers[-1])
        else:
            label_match = re.search(r"\b24T(\d+)\b", line)
            if label_match:
                transitive_group_id = int(label_match.group(1))

    verified_group_label = f"24T{transitive_group_id}" if transitive_group_id is not None else None
    return {
        "candidate_hash": candidate_hash,
        "degree": degree,
        "is_irreducible": is_irreducible,
        "signature_r": signature_r,
        "galois_group_text": galois_group_text,
        "transitive_group_id": transitive_group_id,
        "verified_group_label": verified_group_label,
        "parse_status": "verified" if verified_group_label else "parse_error",
    }


def _coerce_optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_online_magma_pasted_output(text: str) -> dict[str, Any]:
    """Return calculator headers and plain output lines from XML or raw text."""

    stripped = text.strip()
    headers: dict[str, str] = {}
    warnings: list[str] = []
    lines: list[str] = []
    if stripped.startswith("<?xml") or stripped.startswith("<calculator"):
        try:
            root = ElementTree.fromstring(stripped)
        except ElementTree.ParseError:
            lines = [html.unescape(line) for line in text.splitlines()]
        else:
            header_node = root.find("headers")
            if header_node is not None:
                headers = {child.tag: (child.text or "") for child in list(header_node)}
                warnings = [child.text or "" for child in header_node.findall("warning")]
            lines = [line.text or "" for line in root.findall("./results/line")]
    else:
        lines = [html.unescape(line) for line in text.splitlines()]
    return {
        "headers": headers,
        "warnings": warnings,
        "lines": lines,
        "output_text": "\n".join(lines),
    }


def parse_online_magma_pasted_output(
    text: str,
    *,
    expected_candidate_hash: str | None = None,
    source_path: Path | None = None,
) -> dict[str, Any]:
    """Parse manually pasted free-calculator output into an exact result row."""

    normalized = normalize_online_magma_pasted_output(text)
    parsed = parse_magma_output(normalized["output_text"])
    parsed_hash = parsed.get("candidate_hash")
    candidate_hash = str(parsed_hash or expected_candidate_hash or "")
    hash_match = expected_candidate_hash is None or parsed_hash in (None, expected_candidate_hash)
    parse_status = str(parsed.get("parse_status"))
    if not hash_match:
        parse_status = "hash_mismatch"
    version_raw = normalized["headers"].get("version")
    version = f"V{version_raw}" if version_raw else None
    return {
        "schema_version": ONLINE_MAGMA_MANUAL_SCHEMA_VERSION,
        "record_type": "igp24_online_magma_manual_result",
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "candidate_hash": candidate_hash or None,
        "expected_candidate_hash": expected_candidate_hash,
        "candidate_hash_match": hash_match,
        "degree": parsed.get("degree"),
        "is_irreducible": parsed.get("is_irreducible"),
        "galois_group_text": parsed.get("galois_group_text"),
        "transitive_group_id": parsed.get("transitive_group_id"),
        "verified_group_label": parsed.get("verified_group_label"),
        "exact_verification_status": parse_status,
        "status": parse_status,
        "magma_runtime_seconds": _coerce_optional_float(normalized["headers"].get("time")),
        "magma_memory_usage": normalized["headers"].get("memory") or None,
        "magma_seed": _coerce_optional_int(normalized["headers"].get("seed")),
        "magma_version": version,
        "magma_version_raw": version_raw,
        "calculator_headers": normalized["headers"],
        "calculator_warnings": normalized["warnings"],
        "raw_output_source_path": str(source_path) if source_path else None,
        "provenance": {
            "tool": "Magma free online calculator",
            "calculator_url": ONLINE_MAGMA_CALCULATOR_URL,
            "manual_probe": True,
            "manual_paste_required": True,
            "observed_magma_version": ONLINE_MAGMA_CALCULATOR_VERSION,
            "observed_runtime_cap_seconds": ONLINE_MAGMA_MAX_TIME_SECONDS,
            "observed_input_limit_bytes": ONLINE_MAGMA_MAX_INPUT_BYTES,
        },
        "safety": {
            "network_calls_by_helper": False,
            "automated_online_submission": False,
            "batch_online_submission": False,
            "sair_submission": False,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
        },
    }


def read_cache(cache_path: Path) -> dict[str, Any]:
    if not cache_path.exists():
        return {"schema_version": 1, "entries": {}}
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    if "entries" not in data:
        data = {"schema_version": 1, "entries": data}
    data.setdefault("schema_version", 1)
    data.setdefault("entries", {})
    return data


def write_cache(cache_path: Path, cache: dict[str, Any]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(cache)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cache_key_for_record(record: dict[str, Any]) -> str | None:
    coefficients = record.get("exported_coefficients")
    if not isinstance(coefficients, list):
        return None
    return f"magma_exact_v{MAGMA_SCRIPT_SCHEMA_VERSION}:{coefficients_sha256(coefficients)}"


def _result_projection(record: dict[str, Any], *, index: int) -> dict[str, Any]:
    coefficients = record.get("exported_coefficients")
    coefficient_hash = coefficients_sha256(coefficients) if isinstance(coefficients, list) else None
    return {
        "schema_version": 1,
        "record_type": "igp24_magma_verification_result",
        "input_index": int(record.get("input_index") or index),
        "canonical_hash": record.get("canonical_hash"),
        "coefficient_sha256": coefficient_hash,
        "score": record.get("score"),
        "real_root_count": record.get("real_root_count"),
        "source_strategy": record.get("source_strategy")
        or (record.get("generation_metadata") or {}).get("strategy"),
        "source_input_path": record.get("source_input_path"),
        "source_input_kind": record.get("source_input_kind"),
        "proxy_verification_status": record.get("verification_status"),
        "proxy_verified_group_label": record.get("verified_group_label"),
        "status": None,
        "exact_verification_status": None,
        "verified_group_label": None,
        "transitive_group_id": None,
        "signature_r": None,
        "magma_degree": None,
        "magma_is_irreducible": None,
        "message": "",
        "cache_hit": False,
        "magma_process_executed": False,
    }


def _cached_result(entry: dict[str, Any], record: dict[str, Any], *, index: int, cache_path: Path) -> dict[str, Any]:
    result = _result_projection(record, index=index)
    result.update(entry)
    result["cache_hit"] = True
    result["cache_path"] = str(cache_path)
    result["runtime_seconds"] = 0.0
    result["message"] = "reused cached MAGMA verification result"
    return result


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def run_magma_candidate(
    record: dict[str, Any],
    *,
    index: int,
    output_dir: Path,
    availability: dict[str, Any],
    run_magma: bool,
    timeout_seconds: int,
    cache: dict[str, Any],
    cache_path: Path,
    refresh_cache: bool,
) -> dict[str, Any]:
    result = _result_projection(record, index=index)
    validation_error = record.get("input_validation_error")
    if validation_error:
        result.update(
            {
                "status": "invalid_input",
                "exact_verification_status": "invalid_input",
                "message": str(validation_error),
            }
        )
        return result

    key = cache_key_for_record(record)
    result["cache_key"] = key
    if key and not refresh_cache and key in cache.get("entries", {}):
        return _cached_result(cache["entries"][key], record, index=index, cache_path=cache_path)

    script_dir = output_dir / MAGMA_CANDIDATE_SCRIPTS_DIR
    raw_dir = output_dir / MAGMA_RAW_OUTPUT_DIR
    script_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    hash_text = safe_filename(str(record.get("canonical_hash") or f"candidate_{index:04d}"), fallback=f"candidate_{index:04d}")
    script_path = script_dir / f"{index:04d}_{hash_text}.m"
    raw_output_path = raw_dir / f"{index:04d}_{hash_text}.txt"
    script_path.write_text(build_magma_verification_input(record, timeout_seconds=timeout_seconds), encoding="utf-8")
    executable = availability.get("path") or availability.get("executable") or "magma"
    command = build_magma_command(str(executable), script_path)
    result.update(
        {
            "script_path": str(script_path),
            "raw_output_path": str(raw_output_path),
            "magma_command": command,
            "timeout_seconds": int(timeout_seconds),
        }
    )

    if not run_magma:
        result.update(
            {
                "status": "dry_run",
                "exact_verification_status": "dry_run",
                "message": "MAGMA execution was not requested; script generated only",
            }
        )
        return result

    if not availability.get("available"):
        result.update(
            {
                "status": "unavailable",
                "exact_verification_status": "unavailable",
                "message": f"MAGMA executable not found: {availability.get('executable')}",
            }
        )
        return result

    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=output_dir,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        runtime = time.perf_counter() - start
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        raw_output_path.write_text(stdout + ("\nSTDERR:\n" + stderr if stderr else ""), encoding="utf-8")
        result.update(
            {
                "status": "timeout",
                "exact_verification_status": "timeout",
                "runtime_seconds": runtime,
                "timed_out": True,
                "magma_process_executed": True,
                "message": f"MAGMA timed out after {timeout_seconds}s",
            }
        )
        return result

    runtime = time.perf_counter() - start
    raw_output = completed.stdout + ("\nSTDERR:\n" + completed.stderr if completed.stderr else "")
    raw_output_path.write_text(raw_output, encoding="utf-8")
    parsed = parse_magma_output(raw_output)
    status = parsed["parse_status"]
    message = "parsed exact MAGMA transitive group id" if status == "verified" else "MAGMA output did not include a parseable transitive group id"
    if completed.returncode != 0 and status != "verified":
        message = f"MAGMA exited with return code {completed.returncode}; no parseable transitive group id"
    result.update(
        {
            "status": status,
            "exact_verification_status": status,
            "runtime_seconds": runtime,
            "timed_out": False,
            "magma_process_executed": True,
            "returncode": completed.returncode,
            "magma_degree": parsed.get("degree"),
            "magma_is_irreducible": parsed.get("is_irreducible"),
            "signature_r": parsed.get("signature_r"),
            "transitive_group_id": parsed.get("transitive_group_id"),
            "verified_group_label": parsed.get("verified_group_label"),
            "message": message,
            "stdout_tail": completed.stdout.splitlines()[-20:],
            "stderr_tail": completed.stderr.splitlines()[-20:],
        }
    )
    if key and status == "verified":
        cache.setdefault("entries", {})[key] = {
            key_name: value
            for key_name, value in result.items()
            if key_name
            not in {
                "cache_hit",
                "raw_output_path",
                "script_path",
                "magma_command",
                "stdout_tail",
                "stderr_tail",
                "runtime_seconds",
            }
        }
    return result


def run_magma_verification(
    *,
    records: list[dict[str, Any]],
    output_dir: Path,
    availability: dict[str, Any],
    run_magma: bool,
    timeout_seconds: int,
    cache_path: Path,
    refresh_cache: bool,
    max_records: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_records = records if max_records is None else records[: max(0, int(max_records))]
    cache = read_cache(cache_path)
    results = [
        run_magma_candidate(
            record,
            index=index,
            output_dir=output_dir,
            availability=availability,
            run_magma=run_magma,
            timeout_seconds=timeout_seconds,
            cache=cache,
            cache_path=cache_path,
            refresh_cache=refresh_cache,
        )
        for index, record in enumerate(selected_records, start=1)
    ]
    write_cache(cache_path, cache)
    counts: dict[str, int] = {}
    for result in results:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
    process_executed = any(bool(result.get("magma_process_executed")) for result in results)
    execution = {
        "requested": bool(run_magma),
        "executed": process_executed,
        "status": "completed" if run_magma and availability.get("available") else ("unavailable" if run_magma else "dry_run"),
        "results": counts,
        "cache_path": str(cache_path),
        "cache_entries": len(cache.get("entries", {})),
        "max_records": max_records,
    }
    return results, execution


def build_magma_summary(
    *,
    records: list[dict[str, Any]],
    results: list[dict[str, Any]],
    output_dir: Path,
    input_path: Path,
    input_kind: str,
    command: list[str],
    source_commit: str | None,
    tool_availability: dict[str, dict[str, Any]],
    execution: dict[str, dict[str, Any]],
    timeout_seconds: int,
    cache_path: Path,
    max_records: int | None,
    magma_guidance: dict[str, Any],
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
    verified = [result for result in results if result.get("status") == "verified"]
    return {
        "schema_version": 1,
        "record_type": "igp24_offline_magma_verification_summary",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_offline_verify.py",
        "source_commit": source_commit,
        "command": command,
        "input_path": str(input_path),
        "input_kind": input_kind,
        "records_loaded": len(records),
        "records_selected_for_magma": len(results),
        "max_records": max_records,
        "timeout_seconds": timeout_seconds,
        "status_counts": dict(sorted(counts.items())),
        "verified_records": len(verified),
        "verified_group_labels": sorted({str(result.get("verified_group_label")) for result in verified}),
        "tool_availability": tool_availability,
        "magma_discovery": (tool_availability.get("magma") or {}).get("discovery", {}),
        "magma_rerun_guidance": magma_guidance,
        "execution": execution,
        "output_files": {
            "magma_results_jsonl": str(output_dir / MAGMA_RESULTS_JSONL),
            "magma_summary_json": str(output_dir / MAGMA_SUMMARY_JSON),
            "magma_report_md": str(output_dir / MAGMA_REPORT_MD),
            "magma_cache_json": str(cache_path),
            "magma_candidate_scripts_dir": str(output_dir / MAGMA_CANDIDATE_SCRIPTS_DIR),
            "magma_raw_output_dir": str(output_dir / MAGMA_RAW_OUTPUT_DIR),
        },
        "safety": {
            "offline_only": True,
            "proxy_labels_preserved": True,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "network_calls": False,
            "sair_submission": False,
            "auto_submission": False,
            "magma_requested": bool(execution["magma"].get("requested")),
            "magma_executed": bool(execution["magma"].get("executed")),
            "exact_group_labels_parsed": bool(verified),
            "note": MAGMA_SAFETY_NOTE,
        },
    }


def build_magma_report(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    magma_discovery = summary.get("magma_discovery") or {}
    magma_guidance = summary.get("magma_rerun_guidance") or {}
    checked = magma_discovery.get("candidates_checked") or []
    lines = [
        "# IGP24 Offline MAGMA Verification Report",
        "",
        MAGMA_SAFETY_NOTE,
        "",
        f"- Input: `{summary.get('input_path')}`",
        f"- Input kind: `{summary.get('input_kind')}`",
        f"- Records loaded: {summary.get('records_loaded')}",
        f"- Records selected for MAGMA: {summary.get('records_selected_for_magma')}",
        f"- Timeout seconds: {summary.get('timeout_seconds')}",
        f"- MAGMA available: `{summary.get('tool_availability', {}).get('magma', {}).get('available')}`",
        f"- MAGMA executed: `{summary.get('execution', {}).get('magma', {}).get('executed')}`",
        f"- Status counts: `{json.dumps(summary.get('status_counts', {}), sort_keys=True)}`",
        f"- MAGMA discovery checked paths: {len(checked)}",
        f"- MAGMA selected path: `{magma_discovery.get('path')}`",
        f"- Rerun guidance: {magma_guidance.get('message')}",
        f"- Rerun command: `{magma_guidance.get('rerun_command_text')}`",
        "",
        "| index | status | exact label | hash | score | r | cache | message |",
        "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for result in results:
        score = result.get("score")
        score_text = f"{float(score):.6f}" if score is not None else ""
        message = str(result.get("message") or "").replace("|", "\\|")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(result.get("input_index")),
                    str(result.get("status")),
                    str(result.get("verified_group_label") or ""),
                    f"`{str(result.get('canonical_hash') or '')[:12]}`",
                    score_text,
                    str(result.get("real_root_count") if result.get("real_root_count") is not None else ""),
                    str(bool(result.get("cache_hit"))),
                    message,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Results JSONL: `{summary.get('output_files', {}).get('magma_results_jsonl')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('magma_summary_json')}`",
            f"- Cache JSON: `{summary.get('output_files', {}).get('magma_cache_json')}`",
            f"- Candidate scripts: `{summary.get('output_files', {}).get('magma_candidate_scripts_dir')}`",
            f"- Raw outputs: `{summary.get('output_files', {}).get('magma_raw_output_dir')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_magma_artifacts(
    *,
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Path]:
    results_path = output_dir / MAGMA_RESULTS_JSONL
    summary_path = output_dir / MAGMA_SUMMARY_JSON
    report_path = output_dir / MAGMA_REPORT_MD
    _write_jsonl(results_path, results)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_magma_report(summary, results), encoding="utf-8")
    return {
        "magma_results_jsonl": results_path,
        "magma_summary_json": summary_path,
        "magma_report_md": report_path,
    }


def load_online_magma_pasted_outputs(paths: list[Path] | None) -> list[dict[str, Any]]:
    """Load pasted online-calculator outputs from JSONL or raw text files."""

    rows: list[dict[str, Any]] = []
    for path in paths or []:
        source_path = path.resolve()
        text = source_path.read_text(encoding="utf-8")
        if source_path.suffix == ".jsonl":
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                raw = json.loads(line)
                if not isinstance(raw, dict):
                    raise ReviewBatchError(f"{source_path}:{line_number}: pasted output row must be a JSON object")
                pasted_output = raw.get("pasted_output") or raw.get("output") or raw.get("raw_output")
                if not isinstance(pasted_output, str) or not pasted_output.strip():
                    raise ReviewBatchError(f"{source_path}:{line_number}: missing pasted_output text")
                result = parse_online_magma_pasted_output(
                    pasted_output,
                    expected_candidate_hash=raw.get("candidate_hash"),
                    source_path=source_path,
                )
                result["pasted_output_row"] = line_number
                result["pasted_output_note"] = raw.get("note")
                rows.append(result)
        else:
            rows.append(parse_online_magma_pasted_output(text, source_path=source_path))
    return rows


def build_online_magma_manual_summary(
    *,
    records: list[dict[str, Any]],
    results: list[dict[str, Any]],
    output_dir: Path,
    input_path: Path,
    input_kind: str,
    command: list[str],
    source_commit: str | None,
    pasted_output_paths: list[Path] | None,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
    verified = [result for result in results if result.get("status") == "verified"]
    manual_dir = output_dir / ONLINE_MAGMA_MANUAL_DIR
    return {
        "schema_version": ONLINE_MAGMA_MANUAL_SCHEMA_VERSION,
        "record_type": "igp24_online_magma_manual_summary",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_offline_verify.py",
        "source_commit": source_commit,
        "command": command,
        "input_path": str(input_path),
        "input_kind": input_kind,
        "records_selected_for_manual_online_magma": len(records),
        "pasted_output_paths": [str(path.resolve()) for path in pasted_output_paths or []],
        "status_counts": dict(sorted(counts.items())),
        "verified_records": len(verified),
        "verified_group_labels": sorted({str(result.get("verified_group_label")) for result in verified}),
        "calculator_constraints": {
            "calculator_url": ONLINE_MAGMA_CALCULATOR_URL,
            "observed_version": ONLINE_MAGMA_CALCULATOR_VERSION,
            "max_time_seconds": ONLINE_MAGMA_MAX_TIME_SECONDS,
            "max_input_bytes": ONLINE_MAGMA_MAX_INPUT_BYTES,
        },
        "output_files": {
            "online_magma_copy_paste_scripts_dir": str(manual_dir / ONLINE_MAGMA_COPY_PASTE_SCRIPTS_DIR),
            "online_magma_pasted_output_template_jsonl": str(manual_dir / ONLINE_MAGMA_PASTED_OUTPUT_TEMPLATE_JSONL),
            "online_magma_results_jsonl": str(manual_dir / ONLINE_MAGMA_RESULTS_JSONL),
            "online_magma_summary_json": str(manual_dir / ONLINE_MAGMA_SUMMARY_JSON),
            "online_magma_report_md": str(manual_dir / ONLINE_MAGMA_REPORT_MD),
        },
        "safety": {
            "manual_only": True,
            "network_calls_by_helper": False,
            "automated_online_submission": False,
            "batch_online_submission": False,
            "sair_submission": False,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "proxy_labels_preserved": True,
            "note": ONLINE_MAGMA_SAFETY_NOTE,
        },
    }


def build_online_magma_manual_report(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Online MAGMA Manual Report",
        "",
        ONLINE_MAGMA_SAFETY_NOTE,
        "",
        f"- Input: `{summary.get('input_path')}`",
        f"- Input kind: `{summary.get('input_kind')}`",
        f"- Records selected: {summary.get('records_selected_for_manual_online_magma')}",
        f"- Calculator URL: `{summary.get('calculator_constraints', {}).get('calculator_url')}`",
        f"- Observed calculator version: `{summary.get('calculator_constraints', {}).get('observed_version')}`",
        f"- Calculator caps: {summary.get('calculator_constraints', {}).get('max_time_seconds')}s, {summary.get('calculator_constraints', {}).get('max_input_bytes')} bytes",
        f"- Status counts: `{json.dumps(summary.get('status_counts', {}), sort_keys=True)}`",
        "",
        "Manual flow:",
        "1. Open the calculator URL in a browser.",
        "2. Paste one generated script from the copy-paste scripts directory.",
        "3. Paste the returned output into the JSONL template's `pasted_output` field.",
        "4. Rerun this helper with `--online_magma_pasted_output` pointing at that JSONL.",
        "",
        "| status | exact label | hash | degree | irreducible | runtime | version | group |",
        "| --- | --- | --- | ---: | --- | ---: | --- | --- |",
    ]
    for result in results:
        runtime = result.get("magma_runtime_seconds")
        runtime_text = f"{float(runtime):.3f}" if runtime is not None else ""
        group = str(result.get("galois_group_text") or "").replace("|", "\\|")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(result.get("status")),
                    str(result.get("verified_group_label") or ""),
                    f"`{str(result.get('candidate_hash') or '')[:12]}`",
                    str(result.get("degree") or ""),
                    str(result.get("is_irreducible") if result.get("is_irreducible") is not None else ""),
                    runtime_text,
                    str(result.get("magma_version") or ""),
                    group,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Copy/paste scripts: `{summary.get('output_files', {}).get('online_magma_copy_paste_scripts_dir')}`",
            f"- Pasted-output template: `{summary.get('output_files', {}).get('online_magma_pasted_output_template_jsonl')}`",
            f"- Parsed results JSONL: `{summary.get('output_files', {}).get('online_magma_results_jsonl')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('online_magma_summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_online_magma_manual_artifacts(
    *,
    records: list[dict[str, Any]],
    output_dir: Path,
    input_path: Path,
    input_kind: str,
    command: list[str],
    source_commit: str | None,
    max_records: int | None,
    pasted_output_paths: list[Path] | None,
) -> dict[str, Path]:
    selected_records = records if max_records is None else records[: max(0, int(max_records))]
    manual_dir = output_dir / ONLINE_MAGMA_MANUAL_DIR
    script_dir = manual_dir / ONLINE_MAGMA_COPY_PASTE_SCRIPTS_DIR
    script_dir.mkdir(parents=True, exist_ok=True)

    template_rows: list[dict[str, Any]] = []
    for index, record in enumerate(selected_records, start=1):
        hash_text = safe_filename(str(record.get("canonical_hash") or f"candidate_{index:04d}"), fallback=f"candidate_{index:04d}")
        script_path = script_dir / f"{index:04d}_{hash_text}.m"
        script_path.write_text(build_online_magma_manual_input(record), encoding="utf-8")
        template_rows.append(
            {
                "schema_version": ONLINE_MAGMA_MANUAL_SCHEMA_VERSION,
                "candidate_hash": record.get("canonical_hash"),
                "script_path": str(script_path),
                "calculator_url": ONLINE_MAGMA_CALCULATOR_URL,
                "pasted_output": "",
                "note": "Paste exactly one manually returned online MAGMA calculator output here; do not batch-submit.",
            }
        )

    template_path = manual_dir / ONLINE_MAGMA_PASTED_OUTPUT_TEMPLATE_JSONL
    _write_jsonl(template_path, template_rows)
    results = load_online_magma_pasted_outputs(pasted_output_paths)
    results_path = manual_dir / ONLINE_MAGMA_RESULTS_JSONL
    _write_jsonl(results_path, results)
    summary = build_online_magma_manual_summary(
        records=selected_records,
        results=results,
        output_dir=output_dir,
        input_path=input_path,
        input_kind=input_kind,
        command=command,
        source_commit=source_commit,
        pasted_output_paths=pasted_output_paths,
    )
    summary_path = manual_dir / ONLINE_MAGMA_SUMMARY_JSON
    report_path = manual_dir / ONLINE_MAGMA_REPORT_MD
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_online_magma_manual_report(summary, results), encoding="utf-8")
    return {
        "online_magma_copy_paste_scripts_dir": script_dir,
        "online_magma_pasted_output_template_jsonl": template_path,
        "online_magma_results_jsonl": results_path,
        "online_magma_summary_json": summary_path,
        "online_magma_report_md": report_path,
    }


def _is_explicit_path(value: str) -> bool:
    return any(separator in value for separator in ("/", os.sep))


def _candidate_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_executable": os.access(path, os.X_OK) if path.exists() else False,
    }


def _candidate_available(candidate: dict[str, Any]) -> bool:
    return bool(candidate.get("exists") and candidate.get("is_file") and candidate.get("is_executable"))


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for candidate in candidates:
        key = str(candidate.get("path"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def discover_magma_executable(
    executable: str,
    *,
    extra_search_patterns: list[str] | None = None,
    common_search_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Find MAGMA from PATH, explicit path, or bounded common local locations."""

    candidates: list[dict[str, Any]] = []
    path_result = shutil.which(executable)
    if path_result:
        candidate = _candidate_status(Path(path_result))
        candidate.update({"source": "PATH", "query": executable})
        candidates.append(candidate)

    if _is_explicit_path(executable):
        candidate = _candidate_status(Path(executable).expanduser())
        candidate.update({"source": "explicit_executable", "query": executable})
        candidates.append(candidate)

    common_patterns = list(common_search_patterns if common_search_patterns is not None else DEFAULT_MAGMA_SEARCH_PATTERNS)
    extra_patterns = list(extra_search_patterns or [])
    patterns = common_patterns + extra_patterns
    for pattern in patterns:
        matches = sorted(glob.glob(os.path.expanduser(pattern)))
        if not matches and not any(ch in pattern for ch in "*?[]"):
            matches = [os.path.expanduser(pattern)]
        for match in matches:
            candidate = _candidate_status(Path(match))
            candidate.update({"source": "search_pattern", "query": pattern})
            candidates.append(candidate)

    candidates = _dedupe_candidates(candidates)
    selected = next((candidate for candidate in candidates if _candidate_available(candidate)), None)
    return {
        "executable": executable,
        "path": selected["path"] if selected else None,
        "available": selected is not None,
        "selected_source": selected.get("source") if selected else None,
        "selected_query": selected.get("query") if selected else None,
        "candidates_checked": candidates,
        "common_search_patterns": common_patterns,
        "extra_search_patterns": extra_patterns,
    }


def build_magma_rerun_command(
    *,
    command: list[str],
    run_magma: bool,
    magma_path: str | None,
    output_dir: Path,
    fallback_output_dir: Path | None = None,
) -> list[str]:
    rerun = list(command)
    if "--run_magma" not in rerun:
        rerun.append("--run_magma")
    if magma_path:
        if "--magma_executable" in rerun:
            index = rerun.index("--magma_executable") + 1
            if index < len(rerun):
                rerun[index] = magma_path
        else:
            rerun.extend(["--magma_executable", magma_path])
    if not run_magma:
        target_output = str(fallback_output_dir or output_dir.with_name(output_dir.name + "_run_magma"))
        if "--output_dir" in rerun:
            index = rerun.index("--output_dir") + 1
            if index < len(rerun):
                rerun[index] = target_output
        else:
            rerun.extend(["--output_dir", target_output])
    return rerun


def build_magma_guidance(
    *,
    availability: dict[str, Any],
    command: list[str],
    run_magma: bool,
    output_dir: Path,
) -> dict[str, Any]:
    if availability.get("available"):
        rerun = build_magma_rerun_command(
            command=command,
            run_magma=run_magma,
            magma_path=str(availability.get("path")),
            output_dir=output_dir,
        )
        return {
            "status": "ready" if run_magma else "available_but_not_requested",
            "message": "MAGMA was found; exact verification requires an explicit --run_magma run."
            if not run_magma
            else "MAGMA was found and execution was requested.",
            "rerun_command": rerun,
            "rerun_command_text": command_text(rerun),
        }

    rerun = build_magma_rerun_command(
        command=command,
        run_magma=False,
        magma_path="/path/to/magma",
        output_dir=output_dir,
    )
    return {
        "status": "unavailable",
        "message": "MAGMA was not found on PATH or in the bounded common local search locations. Install MAGMA or pass --magma_executable /path/to/magma, then rerun the command below.",
        "rerun_command": rerun,
        "rerun_command_text": command_text(rerun),
    }


def probe_tool(
    executable: str,
    *,
    tool_name: str | None = None,
    version_timeout_seconds: int = 10,
    magma_extra_search_patterns: list[str] | None = None,
    magma_common_search_patterns: list[str] | None = None,
) -> dict[str, Any]:
    path = shutil.which(executable)
    available = path is not None
    if tool_name == "magma":
        discovery = discover_magma_executable(
            executable,
            extra_search_patterns=magma_extra_search_patterns,
            common_search_patterns=magma_common_search_patterns,
        )
        path = discovery.get("path")
        available = bool(discovery.get("available")) and MagmaVerifier(executable=str(path or executable)).is_available()
    result: dict[str, Any] = {
        "executable": executable,
        "path": path,
        "available": available,
    }
    if tool_name == "magma":
        result["discovery"] = discovery
    if not path:
        return result

    version_command = [path, "-v"]
    result["version_command"] = version_command
    try:
        completed = subprocess.run(
            version_command,
            text=True,
            capture_output=True,
            timeout=version_timeout_seconds,
            check=False,
        )
    except Exception as exc:
        result["version_status"] = "probe_failed"
        result["version_message"] = str(exc)
        return result
    result["version_status"] = "completed" if completed.returncode == 0 else "nonzero"
    result["version_returncode"] = completed.returncode
    result["version_output"] = (completed.stdout or completed.stderr).strip().splitlines()[:5]
    return result


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
    magma_guidance: dict[str, Any],
) -> str:
    magma_discovery = (tool_availability.get("magma") or {}).get("discovery", {})
    checked = magma_discovery.get("candidates_checked") or []
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
        f"- MAGMA discovery checked paths: {len(checked)}",
        f"- MAGMA selected path: `{magma_discovery.get('path')}`",
        f"- MAGMA rerun command: `{magma_guidance.get('rerun_command_text')}`",
        "",
        "Generated files:",
        f"- `{output_dir / PARI_INPUT_GP}`",
        f"- `{output_dir / MAGMA_INPUT_M}`",
        f"- `{output_dir / OFFLINE_MANIFEST_JSON}`",
        f"- `{output_dir / MAGMA_RESULTS_JSONL}`",
        f"- `{output_dir / MAGMA_SUMMARY_JSON}`",
        f"- `{output_dir / MAGMA_REPORT_MD}`",
        f"- `{output_dir / MAGMA_CACHE_JSON}`",
        "",
        "Manual next steps:",
        "1. Review the candidate table below, generated verifier scripts, and MAGMA result report.",
        "2. Run local PARI/GP manually, or rerun this helper with an explicit `--run_magma` flag after confirming the local tool is available.",
        "3. Promote an exact group label only from `magma_verification_results.jsonl` rows with status `verified` and recorded MAGMA provenance.",
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
    input_path: Path,
    input_kind: str,
    source_review_manifest: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    tool_availability: dict[str, dict[str, Any]],
    execution: dict[str, dict[str, Any]],
    timeout_seconds: int,
    magma_guidance: dict[str, Any],
) -> dict[str, Any]:
    pari_executed = bool(execution["pari"]["executed"])
    magma_executed = bool(execution["magma"]["executed"])
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_offline_verify.py",
        "source_commit": source_commit,
        "command": command,
        "source_review_batch_dir": str(input_path) if input_kind == "review_batch" else None,
        "source_input_path": str(input_path),
        "source_input_kind": input_kind,
        "source_review_manifest": source_review_manifest,
        "selected_records": len(records),
        "selected_hashes": [record["canonical_hash"] for record in records],
        "coefficient_shape": {"length": 25, "leading_coefficient": 1},
        "timeout_seconds": timeout_seconds,
        "tool_availability": tool_availability,
        "magma_discovery": (tool_availability.get("magma") or {}).get("discovery", {}),
        "magma_rerun_guidance": magma_guidance,
        "execution": execution,
        "output_files": {
            "offline_verification_manifest_json": str(output_dir / OFFLINE_MANIFEST_JSON),
            "pari_input_gp": str(output_dir / PARI_INPUT_GP),
            "magma_input_m": str(output_dir / MAGMA_INPUT_M),
            "verification_plan_md": str(output_dir / VERIFICATION_PLAN_MD),
            "magma_results_jsonl": str(output_dir / MAGMA_RESULTS_JSONL),
            "magma_summary_json": str(output_dir / MAGMA_SUMMARY_JSON),
            "magma_report_md": str(output_dir / MAGMA_REPORT_MD),
            "magma_cache_json": str(output_dir / MAGMA_CACHE_JSON),
            "magma_candidate_scripts_dir": str(output_dir / MAGMA_CANDIDATE_SCRIPTS_DIR),
            "magma_raw_output_dir": str(output_dir / MAGMA_RAW_OUTPUT_DIR),
        },
        "safety": {
            "network_calls": False,
            "sair_submission": False,
            "auto_submission": False,
            "pari_executed": pari_executed,
            "magma_executed": magma_executed,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "exact_group_labels_parsed": bool((execution.get("magma") or {}).get("results", {}).get("verified")),
            "exact_group_claims": bool((execution.get("magma") or {}).get("results", {}).get("verified")),
            "dry_run_preparation_only": not (pari_executed or magma_executed),
            "note": SAFETY_NOTE,
        },
    }


def write_outputs(
    *,
    records: list[dict[str, Any]],
    input_path: Path,
    input_kind: str = "review_batch",
    source_review_manifest: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    pari_executable: str,
    magma_executable: str,
    run_pari: bool,
    run_magma: bool,
    timeout_seconds: int,
    cache_path: Path | None = None,
    refresh_cache: bool = False,
    max_records: int | None = None,
    magma_search_patterns: list[str] | None = None,
    magma_common_search_patterns: list[str] | None = None,
    online_magma_manual: bool = False,
    online_magma_pasted_outputs: list[Path] | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pari_path = output_dir / PARI_INPUT_GP
    magma_path = output_dir / MAGMA_INPUT_M
    pari_path.write_text(build_pari_input(records), encoding="utf-8")
    magma_path.write_text(build_magma_input(records), encoding="utf-8")
    cache_path = cache_path or (output_dir / MAGMA_CACHE_JSON)

    tool_availability = {
        "pari": probe_tool(pari_executable, tool_name="pari"),
        "magma": probe_tool(
            magma_executable,
            tool_name="magma",
            magma_extra_search_patterns=magma_search_patterns,
            magma_common_search_patterns=magma_common_search_patterns,
        ),
    }
    magma_guidance = build_magma_guidance(
        availability=tool_availability["magma"],
        command=command,
        run_magma=run_magma,
        output_dir=output_dir,
    )
    magma_results, magma_execution = run_magma_verification(
        records=records,
        output_dir=output_dir,
        availability=tool_availability["magma"],
        run_magma=run_magma,
        timeout_seconds=timeout_seconds,
        cache_path=cache_path,
        refresh_cache=refresh_cache,
        max_records=max_records,
    )
    execution = {
        "pari": maybe_run_tool(
            requested=run_pari,
            availability=tool_availability["pari"],
            args=[tool_availability["pari"]["path"] or pari_executable, "-q", str(pari_path)],
            cwd=output_dir,
            timeout_seconds=timeout_seconds,
            raw_output_path=output_dir / PARI_RAW_OUTPUT,
        ),
        "magma": magma_execution,
    }
    magma_summary = build_magma_summary(
        records=records,
        results=magma_results,
        output_dir=output_dir,
        input_path=input_path,
        input_kind=input_kind,
        command=command,
        source_commit=source_commit,
        tool_availability=tool_availability,
        execution=execution,
        timeout_seconds=timeout_seconds,
        cache_path=cache_path,
        max_records=max_records,
        magma_guidance=magma_guidance,
    )
    magma_paths = write_magma_artifacts(summary=magma_summary, results=magma_results, output_dir=output_dir)
    online_paths: dict[str, Path] = {}
    online_summary: dict[str, Any] | None = None
    if online_magma_manual or online_magma_pasted_outputs:
        online_paths = write_online_magma_manual_artifacts(
            records=records,
            output_dir=output_dir,
            input_path=input_path,
            input_kind=input_kind,
            command=command,
            source_commit=source_commit,
            max_records=max_records,
            pasted_output_paths=online_magma_pasted_outputs,
        )
        online_summary = json.loads(online_paths["online_magma_summary_json"].read_text(encoding="utf-8"))

    plan_path = output_dir / VERIFICATION_PLAN_MD
    plan_path.write_text(
        build_verification_plan(
            records=records,
            review_dir=input_path,
            output_dir=output_dir,
            tool_availability=tool_availability,
            execution=execution,
            magma_guidance=magma_guidance,
        ),
        encoding="utf-8",
    )
    manifest = build_manifest(
        records=records,
        input_path=input_path,
        input_kind=input_kind,
        source_review_manifest=source_review_manifest,
        output_dir=output_dir,
        command=command,
        source_commit=source_commit,
        tool_availability=tool_availability,
        execution=execution,
        timeout_seconds=timeout_seconds,
        magma_guidance=magma_guidance,
    )
    if online_paths:
        manifest["output_files"].update({name: str(path) for name, path in online_paths.items()})
        manifest["online_magma_manual"] = online_summary
        manifest["safety"]["online_magma_manual_artifacts"] = True
        manifest["safety"]["online_magma_automated_submission"] = False
    manifest_path = output_dir / OFFLINE_MANIFEST_JSON
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "offline_verification_manifest_json": manifest_path,
        "pari_input_gp": pari_path,
        "magma_input_m": magma_path,
        "verification_plan_md": plan_path,
        **magma_paths,
        "magma_cache_json": cache_path,
        **online_paths,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and optionally run safe offline exact verification for IGP24 candidates")
    parser.add_argument(
        "verification_input",
        type=Path,
        help="Review-batch directory, candidate JSONL, or coefficient text file",
    )
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--run_pari", action="store_true", help="Explicitly run local PARI/GP if available")
    parser.add_argument("--run_magma", action="store_true", help="Explicitly run local per-candidate MAGMA exact verification if available")
    parser.add_argument("--pari_executable", default="gp")
    parser.add_argument("--magma_executable", default="magma")
    parser.add_argument("--timeout_seconds", type=int, default=60)
    parser.add_argument("--max_records", type=int, default=None, help="Limit records selected for MAGMA verification/dry-run artifacts")
    parser.add_argument("--cache_path", type=Path, default=None, help="Optional MAGMA result cache path; defaults inside output_dir")
    parser.add_argument(
        "--magma_search_path",
        action="append",
        default=[],
        help="Extra local file path or glob pattern to inspect while discovering MAGMA",
    )
    parser.add_argument("--refresh_cache", action="store_true", help="Ignore existing cached MAGMA verified results")
    parser.add_argument(
        "--online_magma_manual",
        action="store_true",
        help="Write manual free-online-Magma copy/paste scripts and paste-result templates; never submits online requests",
    )
    parser.add_argument(
        "--online_magma_pasted_output",
        action="append",
        type=Path,
        default=[],
        help="JSONL or raw text file containing manually pasted free-online-Magma output to parse",
    )
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        records, input_path, source_review_manifest, input_kind = load_verification_input(args.verification_input)
    except (FileNotFoundError, ReviewBatchError) as exc:
        parser.error(str(exc))

    output_dir = args.output_dir.resolve()
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_offline_verify.py", *argv]
    paths = write_outputs(
        records=records,
        input_path=input_path,
        input_kind=input_kind,
        source_review_manifest=source_review_manifest,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        pari_executable=args.pari_executable,
        magma_executable=args.magma_executable,
        run_pari=args.run_pari,
        run_magma=args.run_magma,
        timeout_seconds=max(1, int(args.timeout_seconds)),
        cache_path=args.cache_path.resolve() if args.cache_path else None,
        refresh_cache=bool(args.refresh_cache),
        max_records=args.max_records,
        magma_search_patterns=list(args.magma_search_path or []),
        online_magma_manual=bool(args.online_magma_manual),
        online_magma_pasted_outputs=[path.resolve() for path in args.online_magma_pasted_output or []],
    )
    manifest = json.loads(paths["offline_verification_manifest_json"].read_text(encoding="utf-8"))
    magma_summary = json.loads(paths["magma_summary_json"].read_text(encoding="utf-8"))

    print(f"loaded_review_records\t{len(records)}")
    print(f"input_kind\t{input_kind}")
    print(f"pari_available\t{manifest['tool_availability']['pari']['available']}")
    print(f"magma_available\t{manifest['tool_availability']['magma']['available']}")
    print(f"pari_executed\t{manifest['safety']['pari_executed']}")
    print(f"magma_executed\t{manifest['safety']['magma_executed']}")
    print(f"magma_status_counts\t{json.dumps(magma_summary['status_counts'], sort_keys=True)}")
    print(f"magma_discovery_checked\t{len((magma_summary.get('magma_discovery') or {}).get('candidates_checked') or [])}")
    print(f"magma_selected_path\t{(magma_summary.get('magma_discovery') or {}).get('path')}")
    print(f"magma_rerun_command\t{(magma_summary.get('magma_rerun_guidance') or {}).get('rerun_command_text')}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
