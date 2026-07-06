#!/usr/bin/env python3
"""Build the next ledger-aware non-generic IGP24 verification queue.

This helper is local/file-only. It reuses saved structure-audit rows, saved
verified-label feedback, candidate metadata, and a local pair-status ledger to
select a manual Magma verification queue while avoiding accepted, pending,
baseline, generic S24, duplicate-hash, and over-repeated structural-family
rows when enough alternatives exist. It never calls SAIR, Magma, PARI,
network APIs, training, GPU sampling, CPU search loops, or local search.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_exact_label_shortlist import annotate_records, build_family_rules
from scripts.igp24_shortlist import get_source_commit, read_jsonl


QUEUE_JSONL = "next_verification_queue.jsonl"
COEFFICIENTS_TXT = "next_verification_coefficients.txt"
HASHES_TXT = "next_verification_hashes.txt"
MANIFEST_JSON = "next_verification_queue_manifest.json"
REPORT_MD = "next_verification_queue_report.md"
SAFETY_NOTE = (
    "Next verification queue planning is local/file-only. It does not submit "
    "to SAIR, call SAIR APIs, call Magma/PARI, use online calculators, train "
    "models, sample on GPU, run CPU search loops, or run local search."
)


class NextQueueError(ValueError):
    """Raised when next-queue inputs are inconsistent."""


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


def _coerce_coefficients(value: Any) -> list[int] | None:
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        return None
    if len(value) == 25 and value[-1] == 1 and value[0] != 0:
        return list(value)
    if len(value) == 24 and value[0] != 0:
        return list(value) + [1]
    return None


def exported_coefficients(record: dict[str, Any]) -> list[int] | None:
    for field in ("exported_coefficients", "coefficients", "decoded_coefficients"):
        coeffs = _coerce_coefficients(record.get(field))
        if coeffs is not None:
            return coeffs
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
    for field in (
        "verified_group_label",
        "computed_label",
        "expected_label",
        "feedback_family_label",
        "label",
        "transitive_group_id",
    ):
        label = normalize_label(record.get(field))
        if label:
            return label
    return None


def extract_r(record: dict[str, Any], *, default: int) -> int:
    for field in ("expected_r", "computed_r", "signature_r", "real_root_count", "r"):
        value = _coerce_int(record.get(field))
        if value is not None:
            return value
    pair_key = str(record.get("pair_key") or "")
    match = re.search(r"\|r=(\d+)", pair_key)
    if match:
        return int(match.group(1))
    return int(default)


def pair_key(label: str | None, r_value: int | None) -> str | None:
    if label is None or r_value is None:
        return None
    return f"{label}|r={int(r_value)}"


def load_pair_status(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_pair: dict[str, dict[str, Any]] = {}
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
        by_pair[key] = item
    return by_pair, {
        "path": str(path),
        "records": len(by_pair),
        "status_counts": dict(sorted(Counter(item["status"] for item in by_pair.values()).items())),
    }


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


def load_jsonl_many(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    resolved: list[str] = []
    for path in paths:
        absolute = path.resolve()
        resolved.append(str(absolute))
        for row in read_jsonl(absolute):
            item = dict(row)
            item.setdefault("source_jsonl_path", str(absolute))
            rows.append(item)
    return rows, resolved


def known_labels_by_hash(rows: Iterable[dict[str, Any]], *, target_r: int) -> dict[str, dict[str, Any]]:
    known: dict[str, dict[str, Any]] = {}
    for row in rows:
        canonical_hash = row.get("canonical_hash") or row.get("candidate_hash")
        if not isinstance(canonical_hash, str) or not canonical_hash:
            continue
        label = extract_label(row)
        if label is None:
            continue
        r_value = extract_r(row, default=target_r)
        known[canonical_hash] = {
            "known_exact_label": label,
            "known_exact_r": r_value,
            "known_exact_pair_key": pair_key(label, r_value),
            "known_exact_source_path": row.get("source_jsonl_path") or row.get("raw_output_source_path"),
        }
    return known


def _structural_family_key(record: dict[str, Any]) -> str:
    return "|".join(
        [
            f"square={bool(record.get('local_discriminant_is_square'))}",
            f"divisor={record.get('primary_exact_block_divisor')}",
            f"base_degree={record.get('primary_base_degree')}",
            f"sparse={record.get('sparse_bucket')}",
            f"strategy={record.get('source_strategy')}",
        ]
    )


def _label_family_pair(record: dict[str, Any], *, target_r: int) -> str | None:
    label = normalize_label(record.get("feedback_family_label"))
    return pair_key(label, target_r)


def _pair_status(pair: str | None, pair_status: dict[str, dict[str, Any]]) -> str | None:
    if pair is None:
        return None
    item = pair_status.get(pair)
    return str(item.get("status")) if item else None


def _generic_s24_hint(record: dict[str, Any]) -> bool:
    return (
        record.get("known_exact_label") == "24T25000"
        or record.get("feedback_family_label") == "24T25000"
        or record.get("verified_group_label") == "24T25000"
    )


def _priority_tuple(record: dict[str, Any]) -> tuple[int, int, int, float, float, int, str]:
    status_rank = {"unmatched": 3, "ambiguous": 2, "matched": 1}.get(str(record.get("feedback_family_match_status")), 0)
    has_exact_block = 1 if record.get("primary_exact_block_divisor") is not None else 0
    return (
        status_rank,
        1 if record.get("local_discriminant_is_square") else 0,
        has_exact_block,
        float(record.get("non_generic_score") or 0.0),
        float(record.get("score") or 0.0),
        -int(record.get("queue_index") or 0),
        str(record.get("canonical_hash") or ""),
    )


def annotate_filter_status(
    records: list[dict[str, Any]],
    *,
    pair_status: dict[str, dict[str, Any]],
    baseline_pairs: set[str],
    known_by_hash: dict[str, dict[str, Any]],
    target_r: int,
    allow_generic_s24: bool,
) -> list[dict[str, Any]]:
    seen_hashes: set[str] = set()
    out: list[dict[str, Any]] = []
    for record in sorted(records, key=_priority_tuple, reverse=True):
        item = dict(record)
        canonical_hash = item.get("canonical_hash")
        if not isinstance(canonical_hash, str) or not canonical_hash:
            item["queue_filter_status"] = "skipped"
            item["queue_filter_reason"] = "missing_canonical_hash"
            out.append(item)
            continue
        item.update(known_by_hash.get(canonical_hash) or {})
        item["feedback_pair_key_hint"] = _label_family_pair(item, target_r=target_r)
        item["feedback_pair_status_hint"] = _pair_status(item.get("feedback_pair_key_hint"), pair_status)
        item["known_exact_pair_status"] = _pair_status(item.get("known_exact_pair_key"), pair_status)
        item["known_exact_pair_in_baseline"] = item.get("known_exact_pair_key") in baseline_pairs if item.get("known_exact_pair_key") else False
        item["feedback_pair_in_baseline"] = item.get("feedback_pair_key_hint") in baseline_pairs if item.get("feedback_pair_key_hint") else False
        item["generic_s24_hint"] = _generic_s24_hint(item)
        item["structural_family_key"] = _structural_family_key(item)
        item["exported_coefficients"] = exported_coefficients(item) or item.get("exported_coefficients")

        reason = None
        if canonical_hash in seen_hashes:
            reason = "duplicate_canonical_hash"
        elif exported_coefficients(item) is None:
            reason = "missing_exported_coefficients"
        elif item.get("known_exact_pair_status") == "accepted":
            reason = "known_exact_accepted_pair"
        elif item.get("known_exact_pair_status") == "pending":
            reason = "known_exact_pending_pair"
        elif item.get("known_exact_pair_in_baseline"):
            reason = "known_exact_baseline_pair"
        elif item.get("generic_s24_hint") and not allow_generic_s24:
            reason = "generic_s24_hint"
        elif item.get("feedback_pair_status_hint") == "accepted":
            reason = "accepted_family_hint"
        elif item.get("feedback_pair_status_hint") == "pending":
            reason = "pending_family_hint"
        elif item.get("feedback_pair_in_baseline"):
            reason = "baseline_family_hint"

        seen_hashes.add(canonical_hash)
        if reason:
            item["queue_filter_status"] = "skipped"
            item["queue_filter_reason"] = reason
            item["survived_filters"] = []
        else:
            item["queue_filter_status"] = "eligible"
            item["queue_filter_reason"] = "survived_accepted_pending_baseline_generic_filters"
            item["survived_filters"] = [
                "unique_canonical_hash",
                "has_exported_coefficients",
                "not_known_accepted_pair",
                "not_known_pending_pair",
                "not_known_baseline_pair",
                "not_generic_s24",
                "not_accepted_or_pending_family_hint",
            ]
        out.append(item)
    return out


def select_queue(
    annotated: list[dict[str, Any]],
    *,
    limit: int,
    max_per_structural_family: int,
) -> list[dict[str, Any]]:
    eligible = [record for record in annotated if record.get("queue_filter_status") == "eligible"]
    ordered = sorted(eligible, key=_priority_tuple, reverse=True)
    selected: list[dict[str, Any]] = []
    selected_hashes: set[str] = set()
    family_counts: Counter[str] = Counter()
    deferred: list[dict[str, Any]] = []
    limit = max(0, int(limit))
    family_cap = max(1, int(max_per_structural_family))

    def take(record: dict[str, Any], phase: str, reason: str) -> None:
        item = dict(record)
        item["next_queue_rank"] = len(selected) + 1
        item["next_queue_selection_phase"] = phase
        item["next_queue_selection_reason"] = reason
        selected.append(item)
        selected_hashes.add(str(item.get("canonical_hash")))
        family_counts[str(item.get("structural_family_key"))] += 1

    for record in ordered:
        if len(selected) >= limit:
            break
        family = str(record.get("structural_family_key"))
        if family_counts[family] < family_cap:
            take(record, "primary_family_cap", "highest priority eligible row within structural-family cap")
        else:
            deferred.append(record)
    if len(selected) < limit:
        for record in deferred:
            if len(selected) >= limit:
                break
            canonical_hash = str(record.get("canonical_hash"))
            if canonical_hash in selected_hashes:
                continue
            take(record, "relaxed_family_cap", "filled remaining target after structural-family cap")
    return selected


def _counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(field)) for record in records).items()))


def build_summary(
    *,
    structure_path: Path,
    feedback_paths: list[str],
    known_paths: list[str],
    candidate_paths: list[str],
    pair_status_info: dict[str, Any],
    baseline_info: dict[str, Any],
    family_rules: dict[str, dict[str, Any]],
    annotated: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    options: dict[str, Any],
) -> dict[str, Any]:
    eligible = [record for record in annotated if record.get("queue_filter_status") == "eligible"]
    skipped = [record for record in annotated if record.get("queue_filter_status") == "skipped"]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_next_verification_queue.py",
        "source_commit": source_commit,
        "command": command,
        "structure_audit_jsonl": str(structure_path),
        "verified_label_feedback_jsonl": feedback_paths,
        "known_verified_jsonl": known_paths,
        "candidate_jsonl": candidate_paths,
        "pair_status": pair_status_info,
        "baseline": baseline_info,
        "options": options,
        "family_rules_loaded": len(family_rules),
        "annotated_records": len(annotated),
        "eligible_records": len(eligible),
        "skipped_records": len(skipped),
        "selected_records": len(selected),
        "filter_reason_counts": _counts(annotated, "queue_filter_reason"),
        "match_status_counts": _counts(annotated, "feedback_family_match_status"),
        "eligible_match_status_counts": _counts(eligible, "feedback_family_match_status"),
        "selected_match_status_counts": _counts(selected, "feedback_family_match_status"),
        "selected_feedback_family_label_counts": _counts(selected, "feedback_family_label"),
        "selected_structural_family_counts": _counts(selected, "structural_family_key"),
        "selected_strategy_counts": _counts(selected, "source_strategy"),
        "selected_hashes": [record.get("canonical_hash") for record in selected],
        "output_files": {
            "queue_jsonl": str(output_dir / QUEUE_JSONL),
            "coefficients_txt": str(output_dir / COEFFICIENTS_TXT),
            "hashes_txt": str(output_dir / HASHES_TXT),
            "manifest_json": str(output_dir / MANIFEST_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "recommendations": [
            "Feed next_verification_queue.jsonl to scripts/igp24_offline_verify.py with --online_magma_manual.",
            "Keep the pair-status ledger current before building each new queue.",
            "After manual verification, add accepted or rejected exact pairs to the ledger before another planning pass.",
        ],
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
        "# IGP24 Next Verification Queue",
        "",
        SAFETY_NOTE,
        "",
        f"- Structure audit: `{summary.get('structure_audit_jsonl')}`",
        f"- Pair-status ledger: `{summary.get('pair_status', {}).get('path')}`",
        f"- Baseline pairs loaded: {summary.get('baseline', {}).get('pairs')}",
        f"- Annotated records: {summary.get('annotated_records')}",
        f"- Eligible records: {summary.get('eligible_records')}",
        f"- Selected records: {summary.get('selected_records')}",
        f"- Filter reason counts: `{json.dumps(summary.get('filter_reason_counts'), sort_keys=True)}`",
        f"- Selected match status counts: `{json.dumps(summary.get('selected_match_status_counts'), sort_keys=True)}`",
        f"- Selected strategy counts: `{json.dumps(summary.get('selected_strategy_counts'), sort_keys=True)}`",
        "",
        "## Selected Queue",
        "",
        "| rank | hash | match | family hint | square | divisor | base degree | sparse | strategy | non-generic | phase | reason |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for record in selected:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(record.get("next_queue_rank")),
                    f"`{record.get('short_hash')}`",
                    str(record.get("feedback_family_match_status") or ""),
                    str(record.get("feedback_family_label") or ""),
                    str(record.get("local_discriminant_is_square")),
                    str(record.get("primary_exact_block_divisor") or ""),
                    str(record.get("primary_base_degree") or ""),
                    str(record.get("sparse_bucket") or ""),
                    f"`{record.get('source_strategy')}`",
                    f"{float(record.get('non_generic_score') or 0.0):.3f}",
                    str(record.get("next_queue_selection_phase")),
                    str(record.get("next_queue_selection_reason")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    for recommendation in summary.get("recommendations") or []:
        lines.append(f"- {recommendation}")
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Queue JSONL: `{summary.get('output_files', {}).get('queue_jsonl')}`",
            f"- Coefficients TXT: `{summary.get('output_files', {}).get('coefficients_txt')}`",
            f"- Manifest JSON: `{summary.get('output_files', {}).get('manifest_json')}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(*, selected: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    queue_path = output_dir / QUEUE_JSONL
    coefficients_path = output_dir / COEFFICIENTS_TXT
    hashes_path = output_dir / HASHES_TXT
    manifest_path = output_dir / MANIFEST_JSON
    report_path = output_dir / REPORT_MD
    with queue_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with coefficients_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(exported_coefficients(record), separators=(",", ":")) + "\n")
    hashes_path.write_text(
        "".join(f"{record.get('next_queue_rank')}\t{record.get('canonical_hash')}\n" for record in selected),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, selected), encoding="utf-8")
    return {
        "queue_jsonl": queue_path,
        "coefficients_txt": coefficients_path,
        "hashes_txt": hashes_path,
        "manifest_json": manifest_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a ledger-aware non-generic IGP24 manual verification queue")
    parser.add_argument("--structure_audit_jsonl", type=Path, required=True)
    parser.add_argument("--verified_label_feedback_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--known_verified_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--candidate_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--pair_status_json", type=Path, required=True)
    parser.add_argument("--baseline_csv", type=Path)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--target_r", type=int, default=4)
    parser.add_argument("--family_key_mode", choices=["coarse", "sparse", "strategy", "full"], default="full")
    parser.add_argument("--max_per_structural_family", type=int, default=2)
    parser.add_argument("--allow_generic_s24", action="store_true")
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        structure_path = args.structure_audit_jsonl.resolve()
        output_dir = args.output_dir.resolve()
        audit_rows = read_jsonl(structure_path)
        feedback_rows, feedback_paths = load_jsonl_many(args.verified_label_feedback_jsonl)
        known_extra_rows, known_paths = load_jsonl_many(args.known_verified_jsonl)
        candidate_rows, candidate_paths = load_jsonl_many(args.candidate_jsonl)
        family_rules = build_family_rules(feedback_rows, mode=args.family_key_mode)
        annotated = annotate_records(
            audit_rows,
            family_rules=family_rules,
            feedback_rows=feedback_rows,
            candidate_rows=candidate_rows,
            mode=args.family_key_mode,
        )
        known = known_labels_by_hash([*feedback_rows, *known_extra_rows], target_r=args.target_r)
        pair_status, pair_status_info = load_pair_status(args.pair_status_json.resolve())
        baseline_pairs, baseline_info = load_baseline_pairs(args.baseline_csv.resolve() if args.baseline_csv else None)
        filtered = annotate_filter_status(
            annotated,
            pair_status=pair_status,
            baseline_pairs=baseline_pairs,
            known_by_hash=known,
            target_r=args.target_r,
            allow_generic_s24=args.allow_generic_s24,
        )
        selected = select_queue(
            filtered,
            limit=args.limit,
            max_per_structural_family=args.max_per_structural_family,
        )
    except (FileNotFoundError, NextQueueError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_next_verification_queue.py", *argv]
    summary = build_summary(
        structure_path=structure_path,
        feedback_paths=feedback_paths,
        known_paths=known_paths,
        candidate_paths=candidate_paths,
        pair_status_info=pair_status_info,
        baseline_info=baseline_info,
        family_rules=family_rules,
        annotated=filtered,
        selected=selected,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        options={
            "limit": args.limit,
            "target_r": args.target_r,
            "family_key_mode": args.family_key_mode,
            "max_per_structural_family": args.max_per_structural_family,
            "allow_generic_s24": args.allow_generic_s24,
        },
    )
    paths = write_outputs(selected=selected, summary=summary, output_dir=output_dir)
    print(f"annotated_records\t{summary['annotated_records']}")
    print(f"eligible_records\t{summary['eligible_records']}")
    print(f"selected_records\t{summary['selected_records']}")
    print(f"filter_reason_counts\t{json.dumps(summary['filter_reason_counts'], sort_keys=True)}")
    print(f"selected_match_status_counts\t{json.dumps(summary['selected_match_status_counts'], sort_keys=True)}")
    print(f"selected_strategy_counts\t{json.dumps(summary['selected_strategy_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
