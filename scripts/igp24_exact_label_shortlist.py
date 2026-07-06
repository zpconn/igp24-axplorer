#!/usr/bin/env python3
"""Build exact-label-aware IGP24 shortlist plans from saved feedback.

This helper is local/file-only. It reads saved verified-label feedback rows and
saved local structure-audit rows, assigns planning family labels by structural
key, and writes an auditable shortlist for the next manual verification round.
It does not call PARI, MAGMA, SAIR, training, GPU sampling, CPU proxy-search
loops, local search, network APIs, or submission paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl


SHORTLIST_JSONL = "exact_label_shortlist.jsonl"
COEFFICIENTS_TXT = "exact_label_shortlist_coefficients.txt"
SUMMARY_JSON = "exact_label_shortlist_summary.json"
REPORT_MD = "exact_label_shortlist_report.md"
SAFETY_NOTE = (
    "Exact-label-aware shortlist planning is local/file-only. Feedback family "
    "labels are planning labels inferred from saved verified rows; this helper "
    "does not claim new exact Galois labels and does not call PARI, MAGMA, "
    "SAIR, training, GPU sampling, CPU proxy-search loops, local search, "
    "network APIs, or submission paths."
)


class ExactLabelShortlistError(ValueError):
    """Raised when exact-label-aware shortlist inputs are inconsistent."""


def _coerce_int_list(value: Any) -> list[int] | None:
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        return None
    return list(value)


def _exported_coefficients(record: dict[str, Any] | None) -> list[int] | None:
    if not record:
        return None
    raw = _coerce_int_list(record.get("exported_coefficients"))
    if raw is not None and len(raw) == 25 and raw[-1] == 1:
        return raw
    raw = _coerce_int_list(record.get("coefficients"))
    if raw is not None:
        if len(raw) == 24:
            return raw + [1]
        if len(raw) == 25 and raw[-1] == 1:
            return raw
    raw = _coerce_int_list(record.get("decoded_coefficients"))
    if raw is not None and len(raw) == 24:
        return raw + [1]
    return None


def _index_candidates(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        canonical_hash = record.get("canonical_hash")
        if isinstance(canonical_hash, str) and canonical_hash and canonical_hash not in indexed:
            indexed[canonical_hash] = record
    return indexed


def family_key(record: dict[str, Any], *, mode: str = "coarse") -> str:
    parts = [
        f"square={bool(record.get('local_discriminant_is_square'))}",
        f"divisor={record.get('primary_exact_block_divisor')}",
        f"base_degree={record.get('primary_base_degree')}",
    ]
    if mode in {"sparse", "full"}:
        parts.append(f"sparse={record.get('sparse_bucket')}")
    if mode in {"strategy", "full"}:
        parts.append(f"strategy={record.get('source_strategy')}")
    if mode not in {"coarse", "sparse", "strategy", "full"}:
        raise ExactLabelShortlistError(f"unknown family key mode: {mode}")
    return "|".join(parts)


def _family_features(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "local_discriminant_is_square": bool(record.get("local_discriminant_is_square")),
        "primary_exact_block_divisor": record.get("primary_exact_block_divisor"),
        "primary_base_degree": record.get("primary_base_degree"),
        "sparse_bucket": record.get("sparse_bucket"),
        "source_strategy": record.get("source_strategy"),
    }


def build_family_rules(feedback_rows: list[dict[str, Any]], *, mode: str = "coarse") -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in feedback_rows:
        label = row.get("verified_group_label")
        if not isinstance(label, str) or not label:
            continue
        key = family_key(row, mode=mode)
        group = grouped.setdefault(
            key,
            {
                "family_key": key,
                "family_key_mode": mode,
                "features": _family_features(row),
                "label_counts": Counter(),
                "example_hashes_by_label": defaultdict(list),
            },
        )
        group["label_counts"][label] += 1
        if len(group["example_hashes_by_label"][label]) < 5:
            group["example_hashes_by_label"][label].append(row.get("canonical_hash"))

    rules: dict[str, dict[str, Any]] = {}
    for key, group in grouped.items():
        label_counts = Counter(group["label_counts"])
        total = sum(label_counts.values())
        dominant_label, dominant_count = label_counts.most_common(1)[0]
        rules[key] = {
            "family_key": key,
            "family_key_mode": mode,
            "features": group["features"],
            "label_counts": dict(sorted(label_counts.items())),
            "dominant_feedback_family_label": dominant_label,
            "dominant_count": dominant_count,
            "feedback_records": total,
            "confidence": dominant_count / total if total else 0.0,
            "ambiguous": len(label_counts) > 1,
            "example_hashes_by_label": {
                label: hashes for label, hashes in sorted(group["example_hashes_by_label"].items())
            },
        }
    return dict(sorted(rules.items()))


def _known_verified_by_hash(feedback_rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in feedback_rows:
        canonical_hash = row.get("canonical_hash")
        if isinstance(canonical_hash, str) and canonical_hash:
            indexed[canonical_hash] = row
    return indexed


def _flag_list(record: dict[str, Any]) -> list[str]:
    flags = record.get("non_generic_flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def annotate_records(
    audit_rows: list[dict[str, Any]],
    *,
    family_rules: dict[str, dict[str, Any]],
    feedback_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]] | None = None,
    mode: str = "coarse",
) -> list[dict[str, Any]]:
    candidates = _index_candidates(candidate_rows or [])
    known_verified = _known_verified_by_hash(feedback_rows)
    annotated: list[dict[str, Any]] = []
    for row in audit_rows:
        canonical_hash = row.get("canonical_hash")
        key = family_key(row, mode=mode)
        rule = family_rules.get(key)
        known = known_verified.get(canonical_hash) if isinstance(canonical_hash, str) else None
        candidate = candidates.get(canonical_hash) if isinstance(canonical_hash, str) else None
        exported = _exported_coefficients(candidate)
        if rule is None:
            status = "unmatched"
            family_label = None
            label_counts: dict[str, int] = {}
            confidence = 0.0
            ambiguous = False
        else:
            ambiguous = bool(rule["ambiguous"])
            status = "ambiguous" if ambiguous else "matched"
            family_label = rule["dominant_feedback_family_label"]
            label_counts = dict(rule["label_counts"])
            confidence = float(rule["confidence"])

        annotated.append(
            {
                "schema_version": 1,
                "record_type": "igp24_exact_label_shortlist_record",
                "canonical_hash": canonical_hash,
                "short_hash": str(canonical_hash or "")[:12],
                "queue_index": row.get("queue_index"),
                "feedback_family_key": key,
                "feedback_family_key_mode": mode,
                "feedback_family_match_status": status,
                "feedback_family_label": family_label,
                "feedback_family_label_counts": label_counts,
                "feedback_family_confidence": confidence,
                "feedback_family_ambiguous": ambiguous,
                "known_verified_group_label": known.get("verified_group_label") if known else None,
                "known_verified_source_path": known.get("raw_output_source_path") if known else None,
                "local_discriminant_is_square": bool(row.get("local_discriminant_is_square")),
                "primary_exact_block_divisor": row.get("primary_exact_block_divisor"),
                "primary_base_degree": row.get("primary_base_degree"),
                "sparse_bucket": row.get("sparse_bucket"),
                "source_strategy": row.get("source_strategy"),
                "non_generic_flags": _flag_list(row),
                "score": row.get("score"),
                "non_generic_score": row.get("non_generic_score"),
                "real_root_count": row.get("real_root_count"),
                "coefficient_height": row.get("coefficient_height"),
                "exported_coefficients": exported,
                "exact_group_claimed_by_helper": False,
                "planning_caveat": SAFETY_NOTE,
            }
        )
    annotated.sort(key=_priority_tuple, reverse=True)
    return annotated


def parse_label_quotas(value: str | None) -> dict[str, int]:
    quotas: dict[str, int] = {}
    if not value:
        return quotas
    for raw in str(value).split(","):
        raw = raw.strip()
        if not raw:
            continue
        if ":" not in raw:
            raise ExactLabelShortlistError(f"invalid label quota: {raw}")
        label, amount = raw.split(":", 1)
        label = label.strip()
        if not label:
            raise ExactLabelShortlistError(f"invalid label quota: {raw}")
        quotas[label] = max(0, int(amount.strip()))
    return quotas


def _priority_tuple(record: dict[str, Any]) -> tuple[int, float, float, int, str]:
    status_rank = {"matched": 2, "ambiguous": 1, "unmatched": 0}.get(str(record.get("feedback_family_match_status")), 0)
    return (
        status_rank,
        float(record.get("non_generic_score") or 0.0),
        float(record.get("score") or 0.0),
        -int(record.get("queue_index") or 0),
        str(record.get("canonical_hash") or ""),
    )


def _label_order(family_rules: dict[str, dict[str, Any]]) -> list[str]:
    totals: Counter[str] = Counter()
    for rule in family_rules.values():
        totals.update(rule.get("label_counts") or {})
    return [label for label, _count in sorted(totals.items(), key=lambda item: (-item[1], item[0]))]


def select_shortlist(
    annotated: list[dict[str, Any]],
    *,
    family_rules: dict[str, dict[str, Any]],
    limit: int = 25,
    min_per_label: int = 1,
    label_quotas: dict[str, int] | None = None,
    include_unmatched: bool = False,
    exclude_verified_hashes: bool = False,
) -> list[dict[str, Any]]:
    label_quotas = dict(label_quotas or {})
    limit = max(0, int(limit))
    selected: list[dict[str, Any]] = []
    selected_hashes: set[str] = set()

    def eligible(record: dict[str, Any]) -> bool:
        if not include_unmatched and record.get("feedback_family_match_status") == "unmatched":
            return False
        if exclude_verified_hashes and record.get("known_verified_group_label"):
            return False
        canonical_hash = record.get("canonical_hash")
        return isinstance(canonical_hash, str) and canonical_hash not in selected_hashes

    def take(record: dict[str, Any], reason: str) -> None:
        canonical_hash = str(record.get("canonical_hash"))
        out = dict(record)
        out["exact_label_shortlist_rank"] = len(selected) + 1
        out["exact_label_shortlist_reason"] = reason
        selected.append(out)
        selected_hashes.add(canonical_hash)

    quotas = {label: max(0, int(min_per_label)) for label in _label_order(family_rules)}
    quotas.update(label_quotas)
    ordered = sorted(annotated, key=_priority_tuple, reverse=True)
    for label, quota in quotas.items():
        if len(selected) >= limit:
            break
        candidates = [record for record in ordered if eligible(record) and record.get("feedback_family_label") == label]
        for record in candidates[: max(0, quota)]:
            if len(selected) >= limit:
                break
            take(record, f"quota:{label}")

    for record in ordered:
        if len(selected) >= limit:
            break
        if eligible(record):
            label = record.get("feedback_family_label") or "unmatched"
            take(record, f"fill:{label}")
    return selected


def _counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(field)) for record in records).items()))


def build_summary(
    *,
    structure_path: Path,
    feedback_path: Path,
    candidate_paths: list[Path],
    output_dir: Path,
    family_rules: dict[str, dict[str, Any]],
    annotated: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    command: list[str],
    source_commit: str | None,
    options: dict[str, Any],
) -> dict[str, Any]:
    coefficients_written = sum(1 for record in selected if record.get("exported_coefficients"))
    feedback_counts: Counter[str] = Counter()
    for rule in family_rules.values():
        feedback_counts.update(rule.get("label_counts") or {})
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_exact_label_shortlist.py",
        "source_commit": source_commit,
        "command": command,
        "structure_audit_jsonl": str(structure_path),
        "verified_label_feedback_jsonl": str(feedback_path),
        "candidate_jsonl": [str(path) for path in candidate_paths],
        "options": options,
        "family_rules": family_rules,
        "feedback_exact_label_counts": dict(sorted(feedback_counts.items())),
        "annotated_records": len(annotated),
        "matched_records": sum(1 for record in annotated if record.get("feedback_family_match_status") == "matched"),
        "ambiguous_records": sum(1 for record in annotated if record.get("feedback_family_match_status") == "ambiguous"),
        "unmatched_records": sum(1 for record in annotated if record.get("feedback_family_match_status") == "unmatched"),
        "selected_records": len(selected),
        "selected_family_label_counts": _counts(selected, "feedback_family_label"),
        "selected_match_status_counts": _counts(selected, "feedback_family_match_status"),
        "known_verified_selected_records": sum(1 for record in selected if record.get("known_verified_group_label")),
        "coefficients_written": coefficients_written,
        "output_files": {
            "shortlist_jsonl": str(output_dir / SHORTLIST_JSONL),
            "coefficients_txt": str(output_dir / COEFFICIENTS_TXT),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
        },
        "recommendations": [
            "Use the selected rows as an exact-label-aware manual verification queue, not as new exact labels.",
            "For fresh audited candidates, rerun with --exclude_verified_hashes to avoid reselecting already verified rows.",
            "Keep expanding the square divisor-2/base-degree-12 branch for 24T24970 and the nonsquare divisor-2/base-degree-12 tail for 24T24979.",
            "Preserve at least one divisor-3/base-degree-8 slot for the 24T24759 coverage track.",
        ],
        "safety": {
            "local_file_only": True,
            "exact_group_claims": False,
            "pari_executed": False,
            "magma_executed": False,
            "sair_submission": False,
            "network_calls": False,
            "runs_inside_train_loop": False,
            "runs_inside_gpu_sampling_loop": False,
            "runs_inside_cpu_proxy_scoring_loop": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Exact-Label-Aware Shortlist",
        "",
        SAFETY_NOTE,
        "",
        f"- Structure audit: `{summary.get('structure_audit_jsonl')}`",
        f"- Verified-label feedback: `{summary.get('verified_label_feedback_jsonl')}`",
        f"- Annotated records: {summary.get('annotated_records')}",
        f"- Selected records: {summary.get('selected_records')}",
        f"- Feedback exact label counts: `{json.dumps(summary.get('feedback_exact_label_counts'), sort_keys=True)}`",
        f"- Selected family label counts: `{json.dumps(summary.get('selected_family_label_counts'), sort_keys=True)}`",
        f"- Known verified selected records: {summary.get('known_verified_selected_records')}",
        f"- Coefficients written: {summary.get('coefficients_written')}",
        "",
        "## Family Rules",
        "",
        "| family key | dominant label | confidence | feedback rows | label counts |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for rule in summary.get("family_rules", {}).values():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{rule.get('family_key')}`",
                    str(rule.get("dominant_feedback_family_label")),
                    f"{float(rule.get('confidence') or 0.0):.3f}",
                    str(rule.get("feedback_records")),
                    f"`{json.dumps(rule.get('label_counts'), sort_keys=True)}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Selected Queue",
            "",
            "| rank | hash | family label | exact known | square | divisor | base degree | sparse | strategy | non-generic | reason |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |",
        ]
    )
    for record in selected:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(record.get("exact_label_shortlist_rank")),
                    f"`{record.get('short_hash')}`",
                    str(record.get("feedback_family_label") or ""),
                    str(record.get("known_verified_group_label") or ""),
                    str(record.get("local_discriminant_is_square")),
                    str(record.get("primary_exact_block_divisor") or ""),
                    str(record.get("primary_base_degree") or ""),
                    str(record.get("sparse_bucket") or ""),
                    f"`{record.get('source_strategy')}`",
                    f"{float(record.get('non_generic_score') or 0.0):.3f}",
                    str(record.get("exact_label_shortlist_reason")),
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
            f"- Shortlist JSONL: `{summary.get('output_files', {}).get('shortlist_jsonl')}`",
            f"- Coefficients TXT: `{summary.get('output_files', {}).get('coefficients_txt')}`",
            f"- Summary JSON: `{summary.get('output_files', {}).get('summary_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(*, selected: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    shortlist_path = output_dir / SHORTLIST_JSONL
    coefficients_path = output_dir / COEFFICIENTS_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD

    with shortlist_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with coefficients_path.open("w", encoding="utf-8") as handle:
        for record in selected:
            coeffs = record.get("exported_coefficients")
            if coeffs:
                handle.write(json.dumps(coeffs, separators=(",", ":")) + "\n")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, selected), encoding="utf-8")
    return {
        "shortlist_jsonl": shortlist_path,
        "coefficients_txt": coefficients_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an exact-label-aware IGP24 shortlist plan from saved feedback")
    parser.add_argument("--structure_audit_jsonl", type=Path, required=True)
    parser.add_argument("--verified_label_feedback_jsonl", type=Path, required=True)
    parser.add_argument("--candidate_jsonl", type=Path, action="append", default=[])
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--min_per_label", type=int, default=1)
    parser.add_argument("--label_quotas", default="")
    parser.add_argument("--family_key_mode", choices=["coarse", "sparse", "strategy", "full"], default="coarse")
    parser.add_argument("--include_unmatched", action="store_true")
    parser.add_argument("--exclude_verified_hashes", action="store_true")
    parser.add_argument("--repo_root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    structure_path = args.structure_audit_jsonl.resolve()
    feedback_path = args.verified_label_feedback_jsonl.resolve()
    candidate_paths = [path.resolve() for path in args.candidate_jsonl]
    output_dir = args.output_dir.resolve()
    try:
        label_quotas = parse_label_quotas(args.label_quotas)
        audit_rows = read_jsonl(structure_path)
        feedback_rows = read_jsonl(feedback_path)
        candidate_rows: list[dict[str, Any]] = []
        for path in candidate_paths:
            candidate_rows.extend(read_jsonl(path))
        family_rules = build_family_rules(feedback_rows, mode=args.family_key_mode)
        annotated = annotate_records(
            audit_rows,
            family_rules=family_rules,
            feedback_rows=feedback_rows,
            candidate_rows=candidate_rows,
            mode=args.family_key_mode,
        )
        selected = select_shortlist(
            annotated,
            family_rules=family_rules,
            limit=args.limit,
            min_per_label=args.min_per_label,
            label_quotas=label_quotas,
            include_unmatched=args.include_unmatched,
            exclude_verified_hashes=args.exclude_verified_hashes,
        )
    except (FileNotFoundError, ExactLabelShortlistError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_exact_label_shortlist.py", *argv]
    summary = build_summary(
        structure_path=structure_path,
        feedback_path=feedback_path,
        candidate_paths=candidate_paths,
        output_dir=output_dir,
        family_rules=family_rules,
        annotated=annotated,
        selected=selected,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        options={
            "limit": args.limit,
            "min_per_label": args.min_per_label,
            "label_quotas": label_quotas,
            "family_key_mode": args.family_key_mode,
            "include_unmatched": args.include_unmatched,
            "exclude_verified_hashes": args.exclude_verified_hashes,
        },
    )
    paths = write_outputs(selected=selected, summary=summary, output_dir=output_dir)
    print(f"annotated_records\t{summary['annotated_records']}")
    print(f"matched_records\t{summary['matched_records']}")
    print(f"selected_records\t{summary['selected_records']}")
    print(f"selected_family_label_counts\t{json.dumps(summary['selected_family_label_counts'], sort_keys=True)}")
    print(f"known_verified_selected_records\t{summary['known_verified_selected_records']}")
    print(f"coefficients_written\t{summary['coefficients_written']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
