#!/usr/bin/env python3
"""Plan manual IGP24 submission candidates from saved verified artifacts.

This helper is local/file-only. It joins saved exact-verification rows to
saved candidate rows, collapses duplicates to one representative per expected
`(24Tt, r)` pair, and writes a manual candidate file. It does not call PARI,
MAGMA, SAIR, training, GPU sampling, CPU search loops, local search, network
APIs, or submission paths.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl


PLAN_JSONL = "submission_plan.jsonl"
SUMMARY_JSON = "submission_plan_summary.json"
REPORT_MD = "submission_plan_report.md"
CANDIDATES_TXT = "submission_candidates.txt"
SAFETY_NOTE = (
    "Submission planning is local/file-only and manual-output-only. It does "
    "not submit to SAIR, call SAIR APIs, call PARI, call MAGMA, train models, "
    "sample on GPU, run CPU search loops, run local search, or make network "
    "calls."
)

VERIFIED_RESULT_NAMES = (
    "online_magma_manual_results.jsonl",
    "magma_verification_results.jsonl",
    "verification_results.jsonl",
)
CANDIDATE_NAMES = (
    "non_generic_shortlist.jsonl",
    "exact_label_shortlist.jsonl",
    "shortlist.jsonl",
    "verification_batch.jsonl",
    "manual_priority.jsonl",
)

LABEL_FIELDS = (
    "computed_label",
    "verified_group_label",
    "expected_label",
    "label",
    "galois_label",
    "galois_group",
    "group_label",
)
R_FIELDS = ("computed_r", "signature_r", "real_root_count", "r", "expected_r")
EXACT_DISC_FIELDS = (
    "field_disc_abs",
    "nfdisc_abs",
    "exact_nfdisc_abs",
    "number_field_discriminant_abs",
)
SCORING_DISC_FIELDS = ("scoring_disc_abs",)
MIXED_DISC_FIELDS = ("mixed_disc_abs",)
POLY_DISC_FIELDS = (
    "poly_disc_abs",
    "polynomial_discriminant_abs",
    "local_discriminant_abs",
    "discriminant_abs",
    "local_discriminant",
    "discriminant",
)
LOG_DISC_FIELDS = ("log_abs_discriminant", "local_log_abs_discriminant")


class SubmissionPlanError(ValueError):
    """Raised when submission-planning inputs are inconsistent."""


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return int(value)
        return None
    if isinstance(value, str):
        text = value.strip().replace("_", "")
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            return None
        return value if math.isfinite(value) else None
    return None


def _coerce_int_list(value: Any) -> list[int] | None:
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        return None
    return list(value)


def exported_coefficients(record: dict[str, Any] | None) -> list[int] | None:
    if not record:
        return None
    raw = _coerce_int_list(record.get("exported_coefficients"))
    if raw is not None and len(raw) == 25 and raw[-1] == 1 and raw[0] != 0:
        return raw
    raw = _coerce_int_list(record.get("coefficients"))
    if raw is not None:
        if len(raw) == 24 and raw[0] != 0:
            return raw + [1]
        if len(raw) == 25 and raw[-1] == 1 and raw[0] != 0:
            return raw
    raw = _coerce_int_list(record.get("decoded_coefficients"))
    if raw is not None and len(raw) == 24 and raw[0] != 0:
        return raw + [1]
    return None


def normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"24\s*T\s*(\d+)", text, flags=re.IGNORECASE)
    if match:
        return f"24T{int(match.group(1))}"
    numeric = _coerce_int(text)
    if numeric is not None and 1 <= numeric <= 25000:
        return f"24T{numeric}"
    return None


def extract_label(record: dict[str, Any]) -> str | None:
    for field in LABEL_FIELDS:
        label = normalize_label(record.get(field))
        if label:
            return label
    transitive_id = _coerce_int(record.get("transitive_group_id"))
    if transitive_id is not None:
        return normalize_label(transitive_id)
    return None


def extract_r(
    *,
    verified: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> tuple[int | None, str]:
    for source, record in (("verified", verified), ("candidate", candidate or {})):
        for field in R_FIELDS:
            value = _coerce_int(record.get(field))
            if value is not None:
                return value, f"{source}.{field}"
    return None, "missing"


def _path_records(paths: Iterable[Path], common_names: tuple[str, ...]) -> tuple[list[dict[str, Any]], list[Path]]:
    records: list[dict[str, Any]] = []
    resolved: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        path = Path(raw).resolve()
        candidates: list[Path] = []
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            for name in common_names:
                direct = path / name
                if direct.exists():
                    candidates.append(direct)
            if not candidates:
                candidates = sorted(path.glob("**/*.jsonl"))
        else:
            raise FileNotFoundError(f"input path does not exist: {path}")
        for candidate in candidates:
            absolute = candidate.resolve()
            if absolute in seen:
                continue
            seen.add(absolute)
            resolved.append(absolute)
            for row in read_jsonl(absolute):
                item = dict(row)
                item.setdefault("source_jsonl_path", str(absolute))
                records.append(item)
    return records, resolved


def _merge_candidate(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    paths = list(merged.get("source_candidate_paths") or [])
    source_path = new.get("source_jsonl_path")
    if source_path and source_path not in paths:
        paths.append(str(source_path))
    merged["source_candidate_paths"] = paths
    for key, value in new.items():
        if key == "source_jsonl_path":
            continue
        if key not in merged or merged.get(key) in (None, "", [], {}):
            merged[key] = value
    return merged


def index_candidates(candidate_rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in candidate_rows:
        canonical_hash = row.get("canonical_hash") or row.get("candidate_hash")
        if not isinstance(canonical_hash, str) or not canonical_hash:
            continue
        item = dict(row)
        item["canonical_hash"] = canonical_hash
        item["source_candidate_paths"] = [str(row["source_jsonl_path"])] if row.get("source_jsonl_path") else []
        indexed[canonical_hash] = _merge_candidate(indexed.get(canonical_hash, {}), item)
    return indexed


def _first_int_field(records: Iterable[dict[str, Any] | None], fields: tuple[str, ...]) -> tuple[str | None, int | None]:
    for record in records:
        if not record:
            continue
        for field in fields:
            value = _coerce_int(record.get(field))
            if value is not None:
                return field, abs(value)
    return None, None


def _first_float_field(records: Iterable[dict[str, Any] | None], fields: tuple[str, ...]) -> tuple[str | None, float | None]:
    for record in records:
        if not record:
            continue
        for field in fields:
            value = _coerce_float(record.get(field))
            if value is not None:
                return field, value
    return None, None


def discriminant_choice(
    *,
    verified: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    records = [verified, candidate or {}]
    for category, fields, source_name in (
        ("exact_nfdisc", EXACT_DISC_FIELDS, "exact_nfdisc"),
        ("scoring_or_mixed_disc", SCORING_DISC_FIELDS + MIXED_DISC_FIELDS, "scoring_or_mixed_disc"),
        ("polynomial_disc", POLY_DISC_FIELDS, "polynomial_disc"),
    ):
        field, value = _first_int_field(records, fields)
        if value is not None:
            return {
                "rank_category": category,
                "source": field,
                "value": value,
                "sort_value": value,
                "kind": source_name,
            }
    field, value = _first_float_field(records, LOG_DISC_FIELDS)
    if value is not None:
        return {
            "rank_category": "log_polynomial_disc_proxy",
            "source": field,
            "value": value,
            "sort_value": value,
            "kind": "log_proxy",
        }
    return {
        "rank_category": "missing",
        "source": None,
        "value": None,
        "sort_value": math.inf,
        "kind": "missing",
    }


def _disc_rank_key(record: dict[str, Any]) -> tuple[int, Any, float, str]:
    category_order = {
        "exact_nfdisc": 0,
        "scoring_or_mixed_disc": 1,
        "polynomial_disc": 2,
        "log_polynomial_disc_proxy": 3,
        "missing": 4,
    }
    category = str(record.get("discriminant_rank_category") or "missing")
    sort_value = record.get("discriminant_sort_value")
    if sort_value is None:
        sort_value = math.inf
    score = _coerce_float(record.get("score")) or 0.0
    return (category_order.get(category, 9), sort_value, -score, str(record.get("canonical_hash") or ""))


def load_baseline_csv(path: Path | None) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    if path is None:
        return {}, {"baseline_loaded": False, "baseline_path": None, "pairs": 0}
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"baseline CSV does not exist: {path}")
    baseline: dict[tuple[str, int], dict[str, Any]] = {}
    rows_loaded = 0
    rows_indexed = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows_loaded += 1
            label = extract_label(row)
            r_value = None
            for field in R_FIELDS + ("real_roots", "num_real_roots"):
                r_value = _coerce_int(row.get(field))
                if r_value is not None:
                    break
            if label is None or r_value is None:
                continue
            disc_field, nfdisc = _first_int_field([row], ("nfdisc_abs", "field_disc_abs", "number_field_discriminant_abs"))
            key = (label, r_value)
            entry = baseline.setdefault(
                key,
                {
                    "label": label,
                    "r": r_value,
                    "baseline_rows": 0,
                    "baseline_nfdisc_abs": None,
                    "baseline_nfdisc_source": disc_field,
                },
            )
            entry["baseline_rows"] += 1
            if nfdisc is not None and (entry["baseline_nfdisc_abs"] is None or nfdisc < entry["baseline_nfdisc_abs"]):
                entry["baseline_nfdisc_abs"] = nfdisc
                entry["baseline_nfdisc_source"] = disc_field
            rows_indexed += 1
    return baseline, {
        "baseline_loaded": True,
        "baseline_path": str(path),
        "rows_loaded": rows_loaded,
        "rows_indexed": rows_indexed,
        "pairs": len(baseline),
    }


def classify_baseline(record: dict[str, Any], baseline: dict[tuple[str, int], dict[str, Any]], *, baseline_loaded: bool) -> dict[str, Any]:
    label = record.get("verified_group_label")
    r_value = record.get("expected_r")
    if not baseline_loaded:
        return {
            "baseline_status": "baseline_unknown",
            "baseline_nfdisc_abs": None,
            "scoreable_claimed": False,
            "scoreability_note": "No baseline CSV was supplied; scoreability is unknown.",
        }
    if not isinstance(label, str) or not isinstance(r_value, int):
        return {
            "baseline_status": "invalid_pair_for_baseline_check",
            "baseline_nfdisc_abs": None,
            "scoreable_claimed": False,
            "scoreability_note": "Missing label or r for baseline lookup.",
        }
    entry = baseline.get((label, r_value))
    if entry is None:
        return {
            "baseline_status": "non_baseline_candidate",
            "baseline_nfdisc_abs": None,
            "scoreable_claimed": False,
            "scoreability_note": "Pair is absent from supplied baseline CSV, but official scoreability still requires official verification.",
        }
    baseline_nfdisc = entry.get("baseline_nfdisc_abs")
    exact_disc = record.get("exact_nfdisc_abs")
    if exact_disc is not None and baseline_nfdisc is not None and int(exact_disc) < int(baseline_nfdisc):
        status = "baseline_improvement_candidate"
        note = "Exact nfdisc is below supplied baseline; official scoreability still requires official verification."
    elif exact_disc is not None and baseline_nfdisc is not None:
        status = "baseline_not_improved"
        note = "Exact nfdisc is not below supplied baseline."
    else:
        status = "baseline_requires_exact_nfdisc"
        note = "Pair is in supplied baseline, but no exact nfdisc improvement is available."
    return {
        "baseline_status": status,
        "baseline_nfdisc_abs": baseline_nfdisc,
        "scoreable_claimed": False,
        "scoreability_note": note,
    }


def build_joined_rows(
    *,
    verified_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    baseline: dict[tuple[str, int], dict[str, Any]],
    baseline_loaded: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = index_candidates(candidate_rows)
    joined: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for verified in verified_rows:
        status = str(verified.get("status") or verified.get("exact_verification_status") or "")
        label = extract_label(verified)
        canonical_hash = verified.get("candidate_hash") or verified.get("canonical_hash")
        if status and status not in {"verified", "ok"}:
            skipped["not_verified"] += 1
            continue
        if label is None:
            skipped["missing_verified_label"] += 1
            continue
        if not isinstance(canonical_hash, str) or not canonical_hash:
            skipped["missing_candidate_hash"] += 1
            continue
        candidate = candidates.get(canonical_hash)
        r_value, r_source = extract_r(verified=verified, candidate=candidate)
        disc = discriminant_choice(verified=verified, candidate=candidate)
        exact_field, exact_nfdisc = _first_int_field([verified, candidate or {}], EXACT_DISC_FIELDS)
        coeffs = exported_coefficients(candidate) or exported_coefficients(verified)
        pair_key = f"{label}|r={r_value if r_value is not None else 'unknown'}"
        row = {
            "schema_version": 1,
            "record_type": "igp24_submission_plan_candidate",
            "canonical_hash": canonical_hash,
            "short_hash": canonical_hash[:12],
            "verified_group_label": label,
            "expected_r": r_value,
            "expected_r_source": r_source,
            "pair_key": pair_key,
            "degree": verified.get("degree"),
            "is_irreducible": verified.get("is_irreducible"),
            "verification_status": "verified",
            "raw_output_source_path": verified.get("raw_output_source_path"),
            "magma_runtime_seconds": verified.get("magma_runtime_seconds"),
            "magma_version": verified.get("magma_version"),
            "score": (candidate or {}).get("score"),
            "non_generic_score": (candidate or {}).get("non_generic_score"),
            "real_root_count": (candidate or {}).get("real_root_count"),
            "coefficient_height": (candidate or {}).get("coefficient_height"),
            "exported_coefficients": coeffs,
            "source_candidate_paths": (candidate or {}).get("source_candidate_paths") or [],
            "source_ledger_path": (candidate or {}).get("source_ledger_path"),
            "exact_nfdisc_abs": exact_nfdisc,
            "exact_nfdisc_source": exact_field,
            "discriminant_rank_category": disc["rank_category"],
            "discriminant_source": disc["source"],
            "discriminant_value": disc["value"],
            "discriminant_sort_value": disc["sort_value"],
            "discriminant_kind": disc["kind"],
            "submission_planning_caveat": SAFETY_NOTE,
        }
        row.update(classify_baseline(row, baseline, baseline_loaded=baseline_loaded))
        joined.append(row)
    return joined, {
        "verified_rows_loaded": len(verified_rows),
        "candidate_rows_loaded": len(candidate_rows),
        "candidate_hashes_indexed": len(candidates),
        "joined_rows": len(joined),
        "skipped_counts": dict(sorted(skipped.items())),
    }


def select_best_per_pair(rows: list[dict[str, Any]], *, limit: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_pair[str(row.get("pair_key"))].append(row)

    selected: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for pair_key, pair_rows in sorted(by_pair.items()):
        ordered = sorted(pair_rows, key=_disc_rank_key)
        best = dict(ordered[0])
        best["pair_candidate_count"] = len(pair_rows)
        best["duplicate_pair_candidates_suppressed"] = max(0, len(pair_rows) - 1)
        selected.append(best)
        for row in ordered[1:]:
            suppressed.append(
                {
                    "pair_key": pair_key,
                    "canonical_hash": row.get("canonical_hash"),
                    "selected_canonical_hash": best.get("canonical_hash"),
                    "reason": "duplicate_expected_pair_lower_ranked",
                    "discriminant_rank_category": row.get("discriminant_rank_category"),
                    "discriminant_value": row.get("discriminant_value"),
                }
            )

    baseline_order = {
        "non_baseline_candidate": 0,
        "baseline_improvement_candidate": 1,
        "baseline_unknown": 2,
        "baseline_requires_exact_nfdisc": 3,
        "baseline_not_improved": 4,
        "invalid_pair_for_baseline_check": 5,
    }
    selected.sort(
        key=lambda row: (
            baseline_order.get(str(row.get("baseline_status")), 9),
            _disc_rank_key(row),
            str(row.get("pair_key") or ""),
        )
    )
    if limit is not None:
        selected = selected[: max(0, int(limit))]
    for rank, row in enumerate(selected, start=1):
        row["submission_plan_rank"] = rank
    return selected, suppressed


def _counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(field)) for record in records).items()))


def _coefficient_line(record: dict[str, Any]) -> str | None:
    coeffs = exported_coefficients(record)
    if coeffs is None:
        return None
    coeff_text = ",".join(str(value) for value in coeffs)
    comment = (
        f" # NOT_SUBMITTED expected_pair={record.get('pair_key')} "
        f"r_source={record.get('expected_r_source')} "
        f"baseline_status={record.get('baseline_status')} "
        f"disc_source={record.get('discriminant_source') or 'missing'} "
        f"hash={record.get('short_hash')}"
    )
    return coeff_text + comment


def build_summary(
    *,
    verified_paths: list[Path],
    candidate_paths: list[Path],
    baseline_info: dict[str, Any],
    diagnostics: dict[str, Any],
    selected: list[dict[str, Any]],
    suppressed: list[dict[str, Any]],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
) -> dict[str, Any]:
    candidate_lines = sum(1 for record in selected if _coefficient_line(record) is not None)
    unique_pairs = len({record.get("pair_key") for record in selected})
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_submission_plan.py",
        "source_commit": source_commit,
        "command": command,
        "verified_result_paths": [str(path) for path in verified_paths],
        "candidate_paths": [str(path) for path in candidate_paths],
        "baseline": baseline_info,
        "input_diagnostics": diagnostics,
        "selected_records": len(selected),
        "unique_pairs_selected": unique_pairs,
        "duplicate_pair_candidates_suppressed": len(suppressed),
        "candidate_lines_written": candidate_lines,
        "selected_pair_counts": _counts(selected, "pair_key"),
        "selected_label_counts": _counts(selected, "verified_group_label"),
        "selected_r_counts": _counts(selected, "expected_r"),
        "baseline_status_counts": _counts(selected, "baseline_status"),
        "discriminant_rank_category_counts": _counts(selected, "discriminant_rank_category"),
        "output_files": {
            "submission_plan_jsonl": str(output_dir / PLAN_JSONL),
            "submission_candidates_txt": str(output_dir / CANDIDATES_TXT),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "recommendations": [
            "Do not submit automatically; inspect this plan and submit manually only after baseline/discriminant review.",
            "The current verified rows collapse by expected pair, so fresh scoring progress needs new labels or new signatures.",
            "Supply the official baseline CSV before claiming non-baseline status or baseline-improvement scoreability.",
            "If a pair is baseline, compute exact nfdisc and compare to the baseline threshold before submission.",
            "Within one submission, keep only one row per expected pair; later submissions can improve discriminants.",
        ],
        "safety": {
            "local_file_only": True,
            "manual_output_only": True,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "pari_executed": False,
            "magma_executed": False,
            "gpu_training": False,
            "cpu_search_loop": False,
            "local_search_executed": False,
            "scoreable_claims": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]], suppressed: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Submission Plan",
        "",
        SAFETY_NOTE,
        "",
        f"- Verified result paths: `{json.dumps(summary.get('verified_result_paths'))}`",
        f"- Candidate paths: `{json.dumps(summary.get('candidate_paths'))}`",
        f"- Baseline: `{json.dumps(summary.get('baseline'), sort_keys=True)}`",
        f"- Selected records: {summary.get('selected_records')}",
        f"- Unique expected pairs selected: {summary.get('unique_pairs_selected')}",
        f"- Duplicate pair candidates suppressed: {summary.get('duplicate_pair_candidates_suppressed')}",
        f"- Candidate lines written: {summary.get('candidate_lines_written')}",
        f"- Baseline status counts: `{json.dumps(summary.get('baseline_status_counts'), sort_keys=True)}`",
        f"- Discriminant source counts: `{json.dumps(summary.get('discriminant_rank_category_counts'), sort_keys=True)}`",
        "",
        "## Selected One-Per-Pair Rows",
        "",
        "| rank | pair | hash | r source | baseline status | disc source | disc value | suppressed |",
        "| ---: | --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in selected:
        disc_value = row.get("discriminant_value")
        disc_text = str(disc_value) if disc_value is not None else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("submission_plan_rank")),
                    f"`{row.get('pair_key')}`",
                    f"`{row.get('short_hash')}`",
                    str(row.get("expected_r_source")),
                    str(row.get("baseline_status")),
                    str(row.get("discriminant_source") or ""),
                    disc_text,
                    str(row.get("duplicate_pair_candidates_suppressed")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Suppressed Duplicate Pair Candidates",
            "",
            f"- Suppressed rows: {len(suppressed)}",
            "",
            "## Recommendations",
            "",
        ]
    )
    for recommendation in summary.get("recommendations") or []:
        lines.append(f"- {recommendation}")
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Plan JSONL: `{summary.get('output_files', {}).get('submission_plan_jsonl')}`",
            f"- Candidate TXT: `{summary.get('output_files', {}).get('submission_candidates_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    *,
    selected: list[dict[str, Any]],
    suppressed: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / PLAN_JSONL
    candidates_path = output_dir / CANDIDATES_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD

    with plan_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    lines = [
        "# IGP24 submission candidate file - NOT SUBMITTED",
        "# Generated for manual review only. Comments are ignored by the official verifier.",
        "# One selected row per expected (24Tt, r) pair.",
    ]
    for record in selected:
        line = _coefficient_line(record)
        if line is not None:
            lines.append(line)
        else:
            lines.append(f"# MISSING_COEFFICIENTS pair={record.get('pair_key')} hash={record.get('short_hash')}")
    candidates_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, selected, suppressed), encoding="utf-8")
    return {
        "submission_plan_jsonl": plan_path,
        "submission_candidates_txt": candidates_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a manual IGP24 submission plan from saved verified artifacts")
    parser.add_argument("--verified_results", nargs="+", type=Path, required=True, help="Verified result JSONL files or directories")
    parser.add_argument("--candidate_jsonl", action="append", type=Path, default=[], help="Candidate JSONL file or directory; repeatable")
    parser.add_argument("--baseline_csv", type=Path, help="Optional official baseline CSV")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        verified_rows, verified_paths = _path_records(args.verified_results, VERIFIED_RESULT_NAMES)
        candidate_rows, candidate_paths = _path_records(args.candidate_jsonl, CANDIDATE_NAMES) if args.candidate_jsonl else ([], [])
        baseline, baseline_info = load_baseline_csv(args.baseline_csv)
        joined, diagnostics = build_joined_rows(
            verified_rows=verified_rows,
            candidate_rows=candidate_rows,
            baseline=baseline,
            baseline_loaded=bool(baseline_info.get("baseline_loaded")),
        )
        selected, suppressed = select_best_per_pair(joined, limit=args.limit)
    except (FileNotFoundError, SubmissionPlanError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    output_dir = args.output_dir.resolve()
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_submission_plan.py", *argv]
    summary = build_summary(
        verified_paths=verified_paths,
        candidate_paths=candidate_paths,
        baseline_info=baseline_info,
        diagnostics=diagnostics,
        selected=selected,
        suppressed=suppressed,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
    )
    paths = write_outputs(selected=selected, suppressed=suppressed, summary=summary, output_dir=output_dir)
    print(f"verified_rows_loaded\t{diagnostics['verified_rows_loaded']}")
    print(f"joined_rows\t{diagnostics['joined_rows']}")
    print(f"selected_records\t{summary['selected_records']}")
    print(f"unique_pairs_selected\t{summary['unique_pairs_selected']}")
    print(f"duplicate_pair_candidates_suppressed\t{summary['duplicate_pair_candidates_suppressed']}")
    print(f"baseline_status_counts\t{json.dumps(summary['baseline_status_counts'], sort_keys=True)}")
    print(f"candidate_lines_written\t{summary['candidate_lines_written']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
