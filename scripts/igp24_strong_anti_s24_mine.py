#!/usr/bin/env python3
"""Mine saved IGP24 diagnostics for fresh strong anti-S24 candidates.

This helper is local/file-only. It reads existing proxy diagnostic JSONL
artifacts, excludes already exhausted hashes, joins saved exact-label feedback
and user-reported SAIR accepted-label feedback, and writes a smaller candidate
pool for structure audit and strict queue planning. It never calls SAIR,
Magma, PARI, online calculators, training, GPU sampling, CPU search loops, or
local search.
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

from scripts.igp24_next_verification_queue import (
    extract_label,
    extract_r,
    known_labels_by_hash,
    load_pair_status,
    load_sair_label_feedback,
    normalize_label,
    pair_key,
)
from scripts.igp24_shortlist import get_source_commit, read_jsonl


MINED_JSONL = "strong_anti_s24_mined.jsonl"
COEFFICIENTS_TXT = "strong_anti_s24_coefficients.txt"
HASHES_TXT = "strong_anti_s24_hashes.txt"
SUMMARY_JSON = "strong_anti_s24_mining_summary.json"
REPORT_MD = "strong_anti_s24_mining_report.md"
SAFETY_NOTE = (
    "Strong anti-S24 mining is local/file-only. It does not submit to SAIR, "
    "call SAIR APIs, call Magma/PARI, use online calculators, train models, "
    "sample on GPU, run CPU search loops, or run local search."
)
DEGREE = 24


class StrongAntiS24MineError(ValueError):
    """Raised when mining inputs are malformed."""


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


def _coerce_coefficients(record: dict[str, Any]) -> list[int] | None:
    for field in ("exported_coefficients", "coefficients", "decoded_coefficients"):
        raw = record.get(field)
        if not isinstance(raw, list) or any(not isinstance(item, int) for item in raw):
            continue
        if len(raw) == DEGREE + 1 and raw[-1] == 1 and raw[0] != 0:
            return list(raw)
        if len(raw) == DEGREE and raw[0] != 0:
            return list(raw) + [1]
    return None


def load_jsonl_many(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    resolved: list[str] = []
    for path in paths:
        absolute = path.resolve()
        resolved.append(str(absolute))
        rows.extend(read_jsonl(absolute))
    return rows, resolved


def load_excluded_hashes(paths: Iterable[Path]) -> tuple[set[str], list[str]]:
    hashes: set[str] = set()
    resolved: list[str] = []
    for path in paths:
        absolute = path.resolve()
        resolved.append(str(absolute))
        for row in read_jsonl(absolute):
            canonical_hash = row.get("canonical_hash") or row.get("candidate_hash")
            if isinstance(canonical_hash, str) and canonical_hash:
                hashes.add(canonical_hash)
    return hashes, resolved


def load_baseline_pairs(path: Path | None) -> tuple[set[str], dict[str, Any]]:
    if path is None:
        return set(), {"baseline_loaded": False, "path": None, "pairs": 0}
    pairs: set[str] = set()
    rows_loaded = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows_loaded += 1
            label = normalize_label(row.get("label"))
            r_value = _coerce_int(row.get("r"))
            key = pair_key(label, r_value)
            if key:
                pairs.add(key)
    return pairs, {"baseline_loaded": True, "path": str(path), "rows_loaded": rows_loaded, "pairs": len(pairs)}


def _evidence(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("non_generic_evidence")
    return value if isinstance(value, dict) else {}


def _block(record: dict[str, Any]) -> dict[str, Any]:
    value = _evidence(record).get("block_structure")
    return value if isinstance(value, dict) else {}


def _flags(record: dict[str, Any]) -> list[str]:
    value = record.get("non_generic_flags")
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _is_square_anti_s24(record: dict[str, Any]) -> bool:
    return bool(_evidence(record).get("square_discriminant")) or "square_discriminant_excludes_s24" in _flags(record)


def _sparse_bucket(record: dict[str, Any]) -> str:
    term_count = _coerce_int(_block(record).get("nonzero_term_count"))
    if term_count is None:
        return str(record.get("sparse_bucket") or "unknown")
    if term_count <= 6:
        return "very_sparse"
    if term_count <= 10:
        return "sparse"
    return "dense"


def diagnostic_family_key(record: dict[str, Any]) -> str:
    exact_divisors = _block(record).get("exact_block_divisors")
    divisors = [int(value) for value in exact_divisors if isinstance(value, int)] if isinstance(exact_divisors, list) else []
    primary_divisor = max(divisors) if divisors else None
    primary_base_degree = DEGREE // primary_divisor if primary_divisor else None
    return "|".join(
        [
            f"square={_is_square_anti_s24(record)}",
            f"divisor={primary_divisor}",
            f"base_degree={primary_base_degree}",
            f"sparse={_sparse_bucket(record)}",
            f"strategy={record.get('source_strategy')}",
        ]
    )


def _feedback_outcome(row: dict[str, Any], pair_status: dict[str, dict[str, Any]], *, target_r: int) -> str:
    label = extract_label(row)
    pair = pair_key(label, extract_r(row, default=target_r))
    ledger_status = str((pair_status.get(pair or "") or {}).get("status") or "")
    if label == "24T25000":
        return "generic_s24"
    if ledger_status == "accepted":
        return "accepted_pair_duplicate"
    if ledger_status == "pending":
        return "pending_pair_duplicate"
    return "accepted_new_pair"


def build_negative_family_rules(
    diagnostic_rows: list[dict[str, Any]],
    sair_feedback_rows: list[dict[str, Any]],
    *,
    pair_status: dict[str, dict[str, Any]],
    target_r: int,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    diagnostics_by_hash = {
        row.get("canonical_hash"): row
        for row in diagnostic_rows
        if isinstance(row.get("canonical_hash"), str) and row.get("canonical_hash")
    }
    by_hash: dict[str, dict[str, Any]] = {}
    families: dict[str, dict[str, Any]] = {}
    for row in sair_feedback_rows:
        canonical_hash = row.get("canonical_hash") or row.get("candidate_hash")
        if not isinstance(canonical_hash, str) or not canonical_hash:
            continue
        label = extract_label(row)
        r_value = extract_r(row, default=target_r)
        pair = pair_key(label, r_value)
        outcome = _feedback_outcome(row, pair_status, target_r=target_r)
        item = dict(row)
        item["sair_feedback_label"] = label
        item["sair_feedback_pair_key"] = pair
        item["sair_feedback_outcome"] = outcome
        by_hash[canonical_hash] = item
        diagnostic = diagnostics_by_hash.get(canonical_hash)
        if not diagnostic:
            continue
        family_key = diagnostic_family_key(diagnostic)
        group = families.setdefault(
            family_key,
            {
                "family_key": family_key,
                "label_counts": Counter(),
                "pair_counts": Counter(),
                "outcome_counts": Counter(),
                "example_hashes": [],
            },
        )
        if label:
            group["label_counts"][label] += 1
        if pair:
            group["pair_counts"][pair] += 1
        group["outcome_counts"][outcome] += 1
        if len(group["example_hashes"]) < 6:
            group["example_hashes"].append(canonical_hash)

    normalized: dict[str, dict[str, Any]] = {}
    for key, group in families.items():
        outcome_counts = Counter(group["outcome_counts"])
        if outcome_counts.get("generic_s24", 0):
            family_status = "generic_prone"
            avoid_reason = "sair_generic_prone_family"
        elif outcome_counts.get("accepted_pair_duplicate", 0):
            family_status = "accepted_duplicate_prone"
            avoid_reason = "sair_accepted_duplicate_family"
        elif outcome_counts.get("pending_pair_duplicate", 0):
            family_status = "pending_duplicate_prone"
            avoid_reason = "sair_pending_duplicate_family"
        else:
            family_status = "positive_or_unknown"
            avoid_reason = None
        normalized[key] = {
            "family_key": key,
            "family_status": family_status,
            "avoid_reason": avoid_reason,
            "label_counts": dict(sorted(Counter(group["label_counts"]).items())),
            "pair_counts": dict(sorted(Counter(group["pair_counts"]).items())),
            "outcome_counts": dict(sorted(outcome_counts.items())),
            "feedback_records": sum(outcome_counts.values()),
            "example_hashes": list(group["example_hashes"]),
        }
    return dict(sorted(normalized.items())), by_hash


def _pair_status(pair: str | None, pair_status: dict[str, dict[str, Any]]) -> str | None:
    if pair is None:
        return None
    item = pair_status.get(pair)
    return str(item.get("status")) if item else None


def _sort_key(record: dict[str, Any]) -> tuple[float, float, float, str]:
    return (
        1.0 if record.get("strong_anti_s24_evidence") else 0.0,
        float(record.get("non_generic_score") or 0.0),
        float(record.get("score") or 0.0),
        str(record.get("canonical_hash") or ""),
    )


def mine_records(
    diagnostic_rows: list[dict[str, Any]],
    *,
    excluded_hashes: set[str],
    known_by_hash: dict[str, dict[str, Any]],
    pair_status: dict[str, dict[str, Any]],
    baseline_pairs: set[str],
    negative_family_rules: dict[str, dict[str, Any]],
    sair_feedback_by_hash: dict[str, dict[str, Any]],
    target_r: int,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    annotated: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    seen: set[str] = set()
    for index, row in enumerate(diagnostic_rows, start=1):
        item = dict(row)
        canonical_hash = item.get("canonical_hash")
        if not isinstance(canonical_hash, str) or not canonical_hash:
            item["mine_filter_status"] = "skipped"
            item["mine_filter_reason"] = "missing_canonical_hash"
            skipped["missing_canonical_hash"] += 1
            annotated.append(item)
            continue
        family_key = diagnostic_family_key(item)
        known = known_by_hash.get(canonical_hash) or {}
        known_label = normalize_label(known.get("known_exact_label"))
        known_pair = known.get("known_exact_pair_key")
        feedback = sair_feedback_by_hash.get(canonical_hash)
        family_rule = negative_family_rules.get(family_key)
        item.update(
            {
                "mine_index": index,
                "fresh_mining_family_key": family_key,
                "strong_anti_s24_evidence": _is_square_anti_s24(item),
                "known_exact_label": known_label,
                "known_exact_pair_key": known_pair,
                "known_exact_pair_status": _pair_status(str(known_pair) if known_pair else None, pair_status),
                "known_exact_pair_in_baseline": known_pair in baseline_pairs if known_pair else False,
                "sair_feedback_hash_outcome": feedback.get("sair_feedback_outcome") if feedback else None,
                "sair_feedback_family_status": family_rule.get("family_status") if family_rule else None,
                "sair_feedback_family_avoid_reason": family_rule.get("avoid_reason") if family_rule else None,
                "sair_feedback_family_outcome_counts": family_rule.get("outcome_counts") if family_rule else {},
            }
        )
        reason = None
        if canonical_hash in seen:
            reason = "duplicate_canonical_hash"
        elif canonical_hash in excluded_hashes:
            reason = "exhausted_pool_hash"
        elif _coerce_coefficients(item) is None:
            reason = "missing_exported_coefficients"
        elif item.get("real_root_count") != target_r:
            reason = "target_r_mismatch"
        elif not item["strong_anti_s24_evidence"]:
            reason = "missing_strong_anti_s24_evidence"
        elif item.get("sair_feedback_hash_outcome") == "generic_s24":
            reason = "sair_feedback_generic_hash"
        elif item.get("sair_feedback_hash_outcome") == "accepted_pair_duplicate":
            reason = "sair_feedback_accepted_pair_duplicate_hash"
        elif item.get("sair_feedback_family_avoid_reason"):
            reason = str(item.get("sair_feedback_family_avoid_reason"))
        elif known_label == "24T25000":
            reason = "known_generic_s24"
        elif item.get("known_exact_pair_status") == "accepted":
            reason = "known_exact_accepted_pair"
        elif item.get("known_exact_pair_status") == "pending":
            reason = "known_exact_pending_pair"
        elif item.get("known_exact_pair_in_baseline"):
            reason = "known_exact_baseline_pair"

        seen.add(canonical_hash)
        if reason:
            item["mine_filter_status"] = "skipped"
            item["mine_filter_reason"] = reason
            skipped[reason] += 1
        else:
            item["mine_filter_status"] = "eligible"
            item["mine_filter_reason"] = "survived_strong_anti_s24_mining_filters"
            item["mining_survived_filters"] = [
                "fresh_hash_not_in_exhausted_pool",
                "has_exported_coefficients",
                "target_r_match",
                "strong_anti_s24_square_discriminant",
                "not_sair_negative_hash_or_family",
                "not_known_accepted_pending_baseline_or_generic",
            ]
            selected.append(item)
        annotated.append(item)

    selected = sorted(selected, key=_sort_key, reverse=True)[: max(0, int(limit))]
    for rank, item in enumerate(selected, start=1):
        item["strong_anti_s24_mining_rank"] = rank
    return annotated, selected, dict(sorted(skipped.items()))


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def build_summary(
    *,
    diagnostic_paths: list[str],
    excluded_hash_paths: list[str],
    feedback_paths: list[str],
    known_paths: list[str],
    sair_feedback_inputs: list[dict[str, Any]],
    pair_status_info: dict[str, Any],
    baseline_info: dict[str, Any],
    negative_family_rules: dict[str, dict[str, Any]],
    annotated: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    skipped_counts: dict[str, int],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    options: dict[str, Any],
) -> dict[str, Any]:
    eligible = [row for row in annotated if row.get("mine_filter_status") == "eligible"]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_strong_anti_s24_mine.py",
        "source_commit": source_commit,
        "command": command,
        "diagnostic_jsonl": diagnostic_paths,
        "excluded_hash_jsonl": excluded_hash_paths,
        "verified_label_feedback_jsonl": feedback_paths,
        "known_verified_jsonl": known_paths,
        "sair_label_feedback_inputs": sair_feedback_inputs,
        "pair_status": pair_status_info,
        "baseline": baseline_info,
        "options": options,
        "negative_family_rules_loaded": len(negative_family_rules),
        "negative_family_rules": negative_family_rules,
        "records_scanned": len(annotated),
        "eligible_records": len(eligible),
        "selected_records": len(selected),
        "strong_anti_s24_records": sum(1 for row in annotated if row.get("strong_anti_s24_evidence")),
        "skipped_counts": skipped_counts,
        "filter_reason_counts": _counts(annotated, "mine_filter_reason"),
        "selected_strategy_counts": _counts(selected, "source_strategy"),
        "selected_family_counts": _counts(selected, "fresh_mining_family_key"),
        "selected_hashes": [row.get("canonical_hash") for row in selected],
        "output_files": {
            "mined_jsonl": str(output_dir / MINED_JSONL),
            "coefficients_txt": str(output_dir / COEFFICIENTS_TXT),
            "hashes_txt": str(output_dir / HASHES_TXT),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "recommendation": (
            "Run structure audit and strict feedback-aware queue planning on the mined rows."
            if selected
            else "No saved strong anti-S24 rows survived; consider a tiny bounded CPU-only square-discriminant-oriented search."
        ),
        "safety": {
            "local_file_only": True,
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


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Strong Anti-S24 Saved Mining",
        "",
        SAFETY_NOTE,
        "",
        f"- Records scanned: {summary.get('records_scanned')}",
        f"- Strong anti-S24 rows: {summary.get('strong_anti_s24_records')}",
        f"- Eligible rows: {summary.get('eligible_records')}",
        f"- Selected rows: {summary.get('selected_records')}",
        f"- Filter reason counts: `{json.dumps(summary.get('filter_reason_counts'), sort_keys=True)}`",
        f"- Selected strategy counts: `{json.dumps(summary.get('selected_strategy_counts'), sort_keys=True)}`",
        f"- Recommendation: {summary.get('recommendation')}",
        "",
        "## Selected Rows",
        "",
        "| rank | hash | strategy | non-generic | score | family | flags |",
        "| ---: | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in selected:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("strong_anti_s24_mining_rank")),
                    f"`{str(row.get('canonical_hash') or '')[:12]}`",
                    str(row.get("source_strategy") or ""),
                    f"{float(row.get('non_generic_score') or 0.0):.3f}",
                    f"{float(row.get('score') or 0.0):.3f}",
                    f"`{row.get('fresh_mining_family_key')}`",
                    ",".join(_flags(row)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Mined JSONL: `{summary.get('output_files', {}).get('mined_jsonl')}`",
            f"- Coefficients TXT: `{summary.get('output_files', {}).get('coefficients_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(*, selected: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    mined_path = output_dir / MINED_JSONL
    coefficients_path = output_dir / COEFFICIENTS_TXT
    hashes_path = output_dir / HASHES_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    with mined_path.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    with coefficients_path.open("w", encoding="utf-8") as handle:
        for row in selected:
            handle.write(json.dumps(_coerce_coefficients(row), separators=(",", ":")) + "\n")
    hashes_path.write_text(
        "".join(f"{row.get('strong_anti_s24_mining_rank')}\t{row.get('canonical_hash')}\n" for row in selected),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, selected), encoding="utf-8")
    return {
        "mined_jsonl": mined_path,
        "coefficients_txt": coefficients_path,
        "hashes_txt": hashes_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mine saved diagnostics for fresh strong anti-S24 IGP24 rows")
    parser.add_argument("--diagnostic_jsonl", type=Path, action="append", required=True)
    parser.add_argument("--exclude_hash_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--verified_label_feedback_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--known_verified_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--sair_label_feedback_json", type=Path, action="append", default=[])
    parser.add_argument("--pair_status_json", type=Path, required=True)
    parser.add_argument("--baseline_csv", type=Path)
    parser.add_argument("--target_r", type=int, default=4)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        diagnostic_rows, diagnostic_paths = load_jsonl_many(args.diagnostic_jsonl)
        excluded_hashes, excluded_hash_paths = load_excluded_hashes(args.exclude_hash_jsonl)
        feedback_rows, feedback_paths = load_jsonl_many(args.verified_label_feedback_jsonl)
        known_rows, known_paths = load_jsonl_many(args.known_verified_jsonl)
        sair_feedback_rows, sair_feedback_inputs = load_sair_label_feedback(args.sair_label_feedback_json)
        pair_status, pair_status_info = load_pair_status(args.pair_status_json.resolve())
        baseline_pairs, baseline_info = load_baseline_pairs(args.baseline_csv.resolve() if args.baseline_csv else None)
        negative_family_rules, sair_feedback_by_hash = build_negative_family_rules(
            diagnostic_rows,
            sair_feedback_rows,
            pair_status=pair_status,
            target_r=args.target_r,
        )
        known = known_labels_by_hash([*feedback_rows, *known_rows, *sair_feedback_rows], target_r=args.target_r)
        output_dir = args.output_dir.resolve()
        annotated, selected, skipped = mine_records(
            diagnostic_rows,
            excluded_hashes=excluded_hashes,
            known_by_hash=known,
            pair_status=pair_status,
            baseline_pairs=baseline_pairs,
            negative_family_rules=negative_family_rules,
            sair_feedback_by_hash=sair_feedback_by_hash,
            target_r=args.target_r,
            limit=args.limit,
        )
    except (FileNotFoundError, StrongAntiS24MineError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_strong_anti_s24_mine.py", *argv]
    summary = build_summary(
        diagnostic_paths=diagnostic_paths,
        excluded_hash_paths=excluded_hash_paths,
        feedback_paths=feedback_paths,
        known_paths=known_paths,
        sair_feedback_inputs=sair_feedback_inputs,
        pair_status_info=pair_status_info,
        baseline_info=baseline_info,
        negative_family_rules=negative_family_rules,
        annotated=annotated,
        selected=selected,
        skipped_counts=skipped,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        options={"target_r": args.target_r, "limit": args.limit},
    )
    paths = write_outputs(selected=selected, summary=summary, output_dir=output_dir)
    print(f"records_scanned\t{summary['records_scanned']}")
    print(f"strong_anti_s24_records\t{summary['strong_anti_s24_records']}")
    print(f"eligible_records\t{summary['eligible_records']}")
    print(f"selected_records\t{summary['selected_records']}")
    print(f"filter_reason_counts\t{json.dumps(summary['filter_reason_counts'], sort_keys=True)}")
    print(f"selected_strategy_counts\t{json.dumps(summary['selected_strategy_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
