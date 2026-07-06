#!/usr/bin/env python3
"""Analyze score-1-style IGP24 targets and saved proxy candidates.

This helper is local/file-only. It joins a user-provided score-1 snapshot with
the frozen baseline, the local pair-status ledger, saved exact-label feedback,
and optional saved proxy/diagnostic artifacts. It ranks target `(label, r)`
pairs and, when saved proxy candidates are credible enough, writes a tiny
manual-verification queue. It never claims exact labels from proxy rows and
never calls SAIR, Magma, PARI, online calculators, training, GPU sampling, CPU
search loops, or local search.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_non_generic_diagnostic import diagnose_record, record_coefficients
from scripts.igp24_score_aware_triage import load_sair_label_feedback, normalize_label, pair_key
from scripts.igp24_shortlist import get_source_commit, load_records, read_jsonl, resolve_ledger_paths


TARGETS_JSONL = "score1_target_rankings.jsonl"
CANDIDATES_JSONL = "score1_saved_candidate_queue.jsonl"
COEFFICIENTS_TXT = "score1_saved_candidate_coefficients.txt"
HASHES_TXT = "score1_saved_candidate_hashes.txt"
SUMMARY_JSON = "score1_target_analysis_summary.json"
REPORT_MD = "score1_target_analysis_report.md"
DEGREE = 24
DEFAULT_TARGET_RS = (0, 8, 12, 16, 24)
SAFETY_NOTE = (
    "Score-1 target analysis is local/file-only. It does not submit to SAIR, "
    "call SAIR APIs, call Magma/PARI, use online calculators, train models, "
    "sample on GPU, run CPU search loops, or run local search."
)


class Score1TargetAnalysisError(ValueError):
    """Raised when score-1 target-analysis inputs are malformed."""


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip().replace("_", "")
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _parse_int_csv(value: str | None, *, default: Iterable[int]) -> list[int]:
    if value is None:
        return list(default)
    out: list[int] = []
    for item in str(value).split(","):
        item = item.strip()
        if not item:
            continue
        parsed = _coerce_int(item)
        if parsed is None:
            raise Score1TargetAnalysisError(f"invalid integer list item: {item!r}")
        out.append(parsed)
    return out


def _short_hash(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value[:12]


def _label_number(label: str | None) -> int | None:
    if label is None or not label.startswith("24T"):
        return None
    return _coerce_int(label[3:])


def label_band(label: str | None) -> str:
    number = _label_number(label)
    if number is None:
        return "unknown"
    if number <= 499:
        return "00001-00499"
    if number <= 999:
        return "00500-00999"
    if number <= 4999:
        return "01000-04999"
    if number <= 19999:
        return "05000-19999"
    return "20000-25000"


def _coefficients(record: dict[str, Any]) -> list[int] | None:
    for field in ("exported_coefficients", "coefficients", "decoded_coefficients"):
        value = record.get(field)
        if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
            continue
        if len(value) == DEGREE + 1 and value[-1] == 1 and value[0] != 0:
            return list(value)
        if len(value) == DEGREE and value[0] != 0:
            return list(value) + [1]
    coeffs = record_coefficients(record)
    if coeffs is not None and coeffs and coeffs[0] != 0:
        return coeffs + [1]
    return None


def _hash_key(record: dict[str, Any]) -> str | None:
    value = record.get("canonical_hash") or record.get("candidate_hash")
    return value if isinstance(value, str) and value else None


def _first_present(record: dict[str, Any], fields: Iterable[str]) -> Any:
    for field in fields:
        if field in record and record.get(field) is not None:
            return record.get(field)
    return None


def load_score1_snapshot(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise Score1TargetAnalysisError(f"{path}: expected JSON object with rows or a row list")
    targets: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        label = normalize_label(row.get("label") or row.get("verified_group_label"))
        r_value = _coerce_int(_first_present(row, ("r", "computed_r", "signature_r")))
        key = pair_key(label, r_value)
        if not key:
            raise Score1TargetAnalysisError(f"{path}: row {index} needs label and r")
        targets.append({"label": label, "r": r_value, "pair_key": key, "snapshot_rank": index})
    return targets, {
        "path": str(path),
        "rows_loaded": len(rows),
        "targets_loaded": len(targets),
        "shared_properties": payload.get("shared_properties") if isinstance(payload, dict) else {},
    }


def load_baseline_pairs(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    pairs: dict[str, dict[str, Any]] = {}
    rows_loaded = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows_loaded += 1
            label = normalize_label(row.get("label"))
            r_value = _coerce_int(row.get("r"))
            key = pair_key(label, r_value)
            if key:
                pairs[key] = {
                    "pair_key": key,
                    "label": label,
                    "r": r_value,
                    "baseline_nfdisc_abs": _coerce_int(row.get("nfdisc_abs")),
                    "baseline_poly_disc_abs": _coerce_int(row.get("poly_disc_abs")),
                    "baseline_scoring_disc": row.get("scoring_disc"),
                }
    return pairs, {"path": str(path), "rows_loaded": rows_loaded, "pairs": len(pairs)}


def load_pair_status(path: Path) -> tuple[dict[str, dict[str, Any]], set[str], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pairs: dict[str, dict[str, Any]] = {}
    known_hashes: set[str] = set()
    for raw in payload.get("pairs") or []:
        if not isinstance(raw, dict):
            continue
        label = normalize_label(raw.get("label"))
        r_value = _coerce_int(raw.get("r"))
        key = str(raw.get("pair_key") or pair_key(label, r_value) or "")
        if not key:
            continue
        item = dict(raw)
        item["pair_key"] = key
        item["label"] = label
        item["r"] = r_value
        item["status"] = str(raw.get("status") or "unknown")
        pairs[key] = item
        for field in ("canonical_hash", "candidate_hash"):
            value = raw.get(field)
            if isinstance(value, str) and value:
                known_hashes.add(value)
        for alternate in raw.get("accepted_alternates") or []:
            if isinstance(alternate, dict):
                value = alternate.get("canonical_hash") or alternate.get("candidate_hash")
                if isinstance(value, str) and value:
                    known_hashes.add(value)
    return pairs, known_hashes, {
        "path": str(path),
        "records": len(pairs),
        "known_hashes": len(known_hashes),
        "status_counts": dict(sorted(Counter(item["status"] for item in pairs.values()).items())),
    }


def load_verified_feedback(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], set[str], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    hashes: set[str] = set()
    inputs: list[dict[str, Any]] = []
    for path in paths:
        resolved = path.resolve()
        loaded = read_jsonl(resolved)
        rows.extend(loaded)
        for row in loaded:
            key = _hash_key(row)
            if key:
                hashes.add(key)
        inputs.append({"path": str(resolved), "rows_loaded": len(loaded)})
    return rows, hashes, {"inputs": inputs, "rows_loaded": len(rows), "known_hashes": len(hashes)}


def pair_counts_from_feedback(rows: Iterable[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        label = normalize_label(row.get("verified_group_label") or row.get("label") or row.get("known_exact_label"))
        r_value = _coerce_int(row.get("computed_r") or row.get("signature_r") or row.get("r"))
        key = pair_key(label, r_value)
        if key:
            counts[key] += 1
    return counts


def annotate_targets(
    targets: list[dict[str, Any]],
    *,
    baseline_pairs: dict[str, dict[str, Any]],
    pair_status: dict[str, dict[str, Any]],
    feedback_pair_counts: Counter[str],
    saved_r_counts: Counter[int],
) -> list[dict[str, Any]]:
    snapshot_counts = Counter(target["pair_key"] for target in targets)
    annotated: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_saved_r_count = max(saved_r_counts.values(), default=0)
    for target in targets:
        key = target["pair_key"]
        if key in seen:
            continue
        seen.add(key)
        label = target["label"]
        r_value = int(target["r"])
        baseline = baseline_pairs.get(key)
        ledger = pair_status.get(key)
        local_status = str(ledger.get("status")) if ledger else "not_in_local_ledger"
        saved_count = int(saved_r_counts.get(r_value, 0))
        underexplored = saved_count == 0 or (max_saved_r_count > 0 and saved_count / max_saved_r_count < 0.2)
        generator_plausibility = "saved_candidates_present" if saved_count else "needs_targeted_generation"
        target_score = 0.0
        target_score += 10.0 * snapshot_counts[key]
        if local_status != "accepted":
            target_score += 5.0
        if baseline is None:
            target_score += 4.0
        else:
            target_score += 1.0
        if underexplored:
            target_score += 3.0
        if saved_count:
            target_score += 1.0
        if r_value in DEFAULT_TARGET_RS:
            target_score += 1.0
        if _label_number(label) is not None and _label_number(label) <= 499:
            target_score += 1.0
        annotated.append(
            {
                "pair_key": key,
                "label": label,
                "label_number": _label_number(label),
                "label_band": label_band(label),
                "r": r_value,
                "score1_snapshot_frequency": snapshot_counts[key],
                "in_baseline": baseline is not None,
                "baseline_scoring_disc": baseline.get("baseline_scoring_disc") if baseline else None,
                "local_pair_status": local_status,
                "saved_feedback_exact_pair_count": int(feedback_pair_counts.get(key, 0)),
                "saved_candidate_r_count": saved_count,
                "signature_underexplored": underexplored,
                "generator_plausibility": generator_plausibility,
                "target_priority_score": round(target_score, 3),
                "targeting_note": (
                    "Saved candidates exist for this signature; inspect proxy-strong rows."
                    if saved_count
                    else "No saved candidates for this signature; needs a bounded targeted generator/search pass."
                ),
            }
        )
    annotated.sort(key=lambda row: (float(row["target_priority_score"]), -int(row["r"]), str(row["pair_key"])), reverse=True)
    for rank, row in enumerate(annotated, start=1):
        row["target_rank"] = rank
    return annotated


def _diagnostic_flags(record: dict[str, Any]) -> list[str]:
    value = record.get("non_generic_flags")
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _diagnostic_evidence(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("non_generic_evidence")
    return value if isinstance(value, dict) else {}


def _is_diagnostic_record(record: dict[str, Any]) -> bool:
    return isinstance(record.get("non_generic_evidence"), dict) or isinstance(record.get("non_generic_flags"), list)


def _as_diagnostic(record: dict[str, Any]) -> dict[str, Any] | None:
    if _is_diagnostic_record(record):
        item = dict(record)
        item["exported_coefficients"] = _coefficients(item)
        return item if item["exported_coefficients"] is not None else None
    if not _hash_key(record) or _coefficients(record) is None:
        return None
    try:
        diagnosed = diagnose_record(record)
    except Exception:
        return None
    diagnosed["source_ledger_path"] = record.get("source_ledger_path")
    return diagnosed


def _block(record: dict[str, Any]) -> dict[str, Any]:
    value = _diagnostic_evidence(record).get("block_structure")
    return value if isinstance(value, dict) else {}


def _is_strong_proxy_candidate(record: dict[str, Any]) -> bool:
    flags = set(_diagnostic_flags(record))
    block = _block(record)
    return (
        "square_discriminant_excludes_s24" in flags
        or bool(_diagnostic_evidence(record).get("square_discriminant"))
        or bool(block.get("exact_block_divisors"))
    )


def _candidate_sort_key(record: dict[str, Any]) -> tuple[float, float, float, str]:
    flags = set(_diagnostic_flags(record))
    return (
        1.0 if "square_discriminant_excludes_s24" in flags or _diagnostic_evidence(record).get("square_discriminant") else 0.0,
        float(record.get("non_generic_score") or 0.0),
        float(record.get("score") or 0.0),
        str(record.get("canonical_hash") or ""),
    )


def load_candidate_records(candidate_inputs: Iterable[Path], diagnostic_paths: Iterable[Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    resolved_candidate_paths: list[str] = []
    resolved_diagnostic_paths: list[str] = []
    if candidate_inputs:
        ledger_paths = resolve_ledger_paths(candidate_inputs)
        resolved_candidate_paths = [str(path) for path in ledger_paths]
        for record in load_records(ledger_paths):
            diagnostic = _as_diagnostic(record)
            if diagnostic is not None:
                diagnostics.append(diagnostic)
    for path in diagnostic_paths:
        resolved = path.resolve()
        resolved_diagnostic_paths.append(str(resolved))
        for record in read_jsonl(resolved):
            diagnostic = _as_diagnostic(record)
            if diagnostic is not None:
                diagnostics.append(diagnostic)
    return diagnostics, {
        "candidate_ledger_paths": resolved_candidate_paths,
        "diagnostic_jsonl": resolved_diagnostic_paths,
        "records_loaded": len(diagnostics),
    }


def select_saved_candidates(
    diagnostics: Iterable[dict[str, Any]],
    *,
    target_rs: set[int],
    known_hashes: set[str],
    feedback_hashes: set[str],
    limit: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    selected: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    seen: set[str] = set()
    for record in diagnostics:
        canonical_hash = _hash_key(record)
        if not canonical_hash:
            skipped["missing_hash"] += 1
            continue
        if canonical_hash in seen:
            skipped["duplicate_hash"] += 1
            continue
        seen.add(canonical_hash)
        r_value = _coerce_int(record.get("real_root_count"))
        if r_value not in target_rs:
            skipped["target_r_mismatch"] += 1
            continue
        if canonical_hash in known_hashes or canonical_hash in feedback_hashes:
            skipped["known_feedback_or_accepted_hash"] += 1
            continue
        if _coefficients(record) is None:
            skipped["missing_coefficients"] += 1
            continue
        if not _is_strong_proxy_candidate(record):
            skipped["weak_proxy_evidence"] += 1
            continue
        item = dict(record)
        item["canonical_hash"] = canonical_hash
        item["short_hash"] = _short_hash(canonical_hash)
        item["exported_coefficients"] = _coefficients(item)
        item["score1_candidate_filter_status"] = "eligible_proxy_candidate"
        item["score1_candidate_filter_reason"] = "target_signature_and_strong_proxy_evidence"
        item["exact_label_claimed_by_helper"] = False
        item["score1_target_caveat"] = (
            "Proxy-only candidate for manual exact verification. This helper does not claim a lower-label exact group."
        )
        selected.append(item)
    selected.sort(key=_candidate_sort_key, reverse=True)
    selected = selected[: max(0, int(limit))]
    for rank, item in enumerate(selected, start=1):
        item["score1_candidate_rank"] = rank
    return selected, dict(sorted(skipped.items()))


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def _r_counter_from_candidates(diagnostics: Iterable[dict[str, Any]]) -> Counter[int]:
    counts: Counter[int] = Counter()
    for row in diagnostics:
        r_value = _coerce_int(row.get("real_root_count"))
        if r_value is not None:
            counts[r_value] += 1
    return counts


def build_summary(
    *,
    snapshot_info: dict[str, Any],
    baseline_info: dict[str, Any],
    pair_status_info: dict[str, Any],
    verified_feedback_info: dict[str, Any],
    sair_feedback_inputs: list[dict[str, Any]],
    candidate_info: dict[str, Any],
    target_rows: list[dict[str, Any]],
    selected_candidates: list[dict[str, Any]],
    candidate_skipped_counts: dict[str, int],
    output_dir: Path,
    target_rs: list[int],
    command: list[str],
    source_commit: str | None,
) -> dict[str, Any]:
    queue_status = "not_produced"
    if selected_candidates:
        queue_status = "produced" if len(selected_candidates) >= 5 else "tiny_not_padded"
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_score1_target_analysis.py",
        "source_commit": source_commit,
        "command": command,
        "score1_snapshot": snapshot_info,
        "baseline": baseline_info,
        "pair_status": pair_status_info,
        "verified_feedback": verified_feedback_info,
        "sair_label_feedback_inputs": sair_feedback_inputs,
        "candidate_inputs": candidate_info,
        "target_rs": target_rs,
        "target_rows": len(target_rows),
        "target_r_counts": _counts(target_rows, "r"),
        "target_label_band_counts": _counts(target_rows, "label_band"),
        "target_baseline_presence_counts": dict(
            sorted(Counter("in_baseline" if row.get("in_baseline") else "not_in_baseline" for row in target_rows).items())
        ),
        "target_local_pair_status_counts": _counts(target_rows, "local_pair_status"),
        "target_generator_plausibility_counts": _counts(target_rows, "generator_plausibility"),
        "top_targets": target_rows[:12],
        "candidate_skipped_counts": candidate_skipped_counts,
        "selected_candidate_records": len(selected_candidates),
        "selected_candidate_r_counts": _counts(selected_candidates, "real_root_count"),
        "selected_candidate_strategy_counts": _counts(selected_candidates, "source_strategy"),
        "selected_candidate_hashes": [row.get("canonical_hash") for row in selected_candidates],
        "queue_status": queue_status,
        "recommendation": (
            "Use the saved proxy candidate queue for manual exact verification before broad search."
            if len(selected_candidates) >= 5
            else "Saved artifacts did not produce a full credible queue; use the target ranking to design a bounded lower-label/signature search."
        ),
        "output_files": {
            "target_rankings_jsonl": str(output_dir / TARGETS_JSONL),
            "candidate_queue_jsonl": str(output_dir / CANDIDATES_JSONL),
            "candidate_coefficients_txt": str(output_dir / COEFFICIENTS_TXT),
            "candidate_hashes_txt": str(output_dir / HASHES_TXT),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "safety": {
            "local_file_only": True,
            "exact_group_claims_from_proxy": False,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "magma_executed": False,
            "pari_executed": False,
            "gpu_training": False,
            "cpu_search_loop": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], target_rows: list[dict[str, Any]], selected_candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Score-1 Target Analysis",
        "",
        SAFETY_NOTE,
        "",
        "## Target Snapshot",
        "",
        f"- Target rows: {summary.get('target_rows')}",
        f"- Target r counts: `{json.dumps(summary.get('target_r_counts'), sort_keys=True)}`",
        f"- Target label-band counts: `{json.dumps(summary.get('target_label_band_counts'), sort_keys=True)}`",
        f"- Baseline presence: `{json.dumps(summary.get('target_baseline_presence_counts'), sort_keys=True)}`",
        f"- Local pair statuses: `{json.dumps(summary.get('target_local_pair_status_counts'), sort_keys=True)}`",
        f"- Generator plausibility: `{json.dumps(summary.get('target_generator_plausibility_counts'), sort_keys=True)}`",
        "",
        "## Top Targets",
        "",
        "| rank | pair | band | baseline | local | saved r count | generator | score |",
        "| ---: | --- | --- | --- | --- | ---: | --- | ---: |",
    ]
    for row in target_rows[:20]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("target_rank")),
                    f"`{row.get('pair_key')}`",
                    str(row.get("label_band")),
                    "yes" if row.get("in_baseline") else "no",
                    str(row.get("local_pair_status")),
                    str(row.get("saved_candidate_r_count")),
                    str(row.get("generator_plausibility")),
                    f"{float(row.get('target_priority_score') or 0.0):.1f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Saved Candidate Search",
            "",
            f"- Selected proxy candidates: {summary.get('selected_candidate_records')}",
            f"- Candidate skipped counts: `{json.dumps(summary.get('candidate_skipped_counts'), sort_keys=True)}`",
            f"- Selected r counts: `{json.dumps(summary.get('selected_candidate_r_counts'), sort_keys=True)}`",
            f"- Queue status: `{summary.get('queue_status')}`",
            f"- Recommendation: {summary.get('recommendation')}",
            "",
            "| rank | hash | r | non-generic | score | strategy | flags |",
            "| ---: | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in selected_candidates:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("score1_candidate_rank")),
                    f"`{row.get('short_hash')}`",
                    str(row.get("real_root_count")),
                    f"{float(row.get('non_generic_score') or 0.0):.3f}",
                    f"{float(row.get('score') or 0.0):.3f}",
                    f"`{row.get('source_strategy')}`",
                    ",".join(_diagnostic_flags(row)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Target rankings JSONL: `{summary.get('output_files', {}).get('target_rankings_jsonl')}`",
            f"- Candidate queue JSONL: `{summary.get('output_files', {}).get('candidate_queue_jsonl')}`",
            f"- Candidate coefficients TXT: `{summary.get('output_files', {}).get('candidate_coefficients_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    *,
    target_rows: list[dict[str, Any]],
    selected_candidates: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    targets_path = output_dir / TARGETS_JSONL
    queue_path = output_dir / CANDIDATES_JSONL
    coeffs_path = output_dir / COEFFICIENTS_TXT
    hashes_path = output_dir / HASHES_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    with targets_path.open("w", encoding="utf-8") as handle:
        for row in target_rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    with queue_path.open("w", encoding="utf-8") as handle:
        for row in selected_candidates:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    with coeffs_path.open("w", encoding="utf-8") as handle:
        for row in selected_candidates:
            handle.write(",".join(str(value) for value in row.get("exported_coefficients") or []) + "\n")
    hashes_path.write_text(
        "".join(f"{row.get('score1_candidate_rank')}\t{row.get('canonical_hash')}\n" for row in selected_candidates),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, target_rows, selected_candidates), encoding="utf-8")
    return {
        "target_rankings_jsonl": targets_path,
        "candidate_queue_jsonl": queue_path,
        "candidate_coefficients_txt": coeffs_path,
        "candidate_hashes_txt": hashes_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze score-1 IGP24 target pairs and saved proxy candidates")
    parser.add_argument("--score1_snapshot_json", type=Path, required=True)
    parser.add_argument("--baseline_csv", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, required=True)
    parser.add_argument("--verified_label_feedback_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--sair_label_feedback_json", type=Path, action="append", default=[])
    parser.add_argument("--candidate_input", type=Path, action="append", default=[])
    parser.add_argument("--diagnostic_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--target_rs", default=None, help="Comma-separated signature values to search; defaults to 0,8,12,16,24")
    parser.add_argument("--candidate_limit", type=int, default=12)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        target_rs = _parse_int_csv(args.target_rs, default=DEFAULT_TARGET_RS)
        targets, snapshot_info = load_score1_snapshot(args.score1_snapshot_json.resolve())
        baseline_pairs, baseline_info = load_baseline_pairs(args.baseline_csv.resolve())
        pair_status, known_hashes, pair_status_info = load_pair_status(args.pair_status_json.resolve())
        verified_rows, verified_hashes, verified_info = load_verified_feedback(args.verified_label_feedback_jsonl)
        sair_feedback, sair_inputs = load_sair_label_feedback(args.sair_label_feedback_json)
        sair_rows = list(sair_feedback.values())
        feedback_hashes = set(verified_hashes) | set(sair_feedback)
        feedback_pair_counts = pair_counts_from_feedback([*verified_rows, *sair_rows])
        diagnostics, candidate_info = load_candidate_records(args.candidate_input, args.diagnostic_jsonl)
        saved_r_counts = _r_counter_from_candidates(diagnostics)
        target_rows = annotate_targets(
            targets,
            baseline_pairs=baseline_pairs,
            pair_status=pair_status,
            feedback_pair_counts=feedback_pair_counts,
            saved_r_counts=saved_r_counts,
        )
        selected_candidates, skipped = select_saved_candidates(
            diagnostics,
            target_rs=set(target_rs),
            known_hashes=known_hashes,
            feedback_hashes=feedback_hashes,
            limit=args.candidate_limit,
        )
    except (FileNotFoundError, json.JSONDecodeError, Score1TargetAnalysisError, ValueError) as exc:
        parser.error(str(exc))

    output_dir = args.output_dir.resolve()
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_score1_target_analysis.py", *argv]
    summary = build_summary(
        snapshot_info=snapshot_info,
        baseline_info=baseline_info,
        pair_status_info=pair_status_info,
        verified_feedback_info=verified_info,
        sair_feedback_inputs=sair_inputs,
        candidate_info=candidate_info,
        target_rows=target_rows,
        selected_candidates=selected_candidates,
        candidate_skipped_counts=skipped,
        output_dir=output_dir,
        target_rs=target_rs,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
    )
    paths = write_outputs(target_rows=target_rows, selected_candidates=selected_candidates, summary=summary, output_dir=output_dir)
    print(f"target_rows\t{summary['target_rows']}")
    print(f"target_r_counts\t{json.dumps(summary['target_r_counts'], sort_keys=True)}")
    print(f"target_baseline_presence_counts\t{json.dumps(summary['target_baseline_presence_counts'], sort_keys=True)}")
    print(f"target_generator_plausibility_counts\t{json.dumps(summary['target_generator_plausibility_counts'], sort_keys=True)}")
    print(f"selected_candidate_records\t{summary['selected_candidate_records']}")
    print(f"selected_candidate_r_counts\t{json.dumps(summary['selected_candidate_r_counts'], sort_keys=True)}")
    print(f"queue_status\t{summary['queue_status']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
