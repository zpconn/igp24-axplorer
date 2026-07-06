#!/usr/bin/env python3
"""Review verified IGP24 rows against baseline and accepted submission state.

This helper is local/file-only. It merges saved verification evidence with
candidate metadata, compares rows against the frozen baseline and an accepted
package manifest, classifies every row, and writes an optional manual
submission-review package for actionable rows. It does not call SAIR, Magma,
PARI, online calculators, training, GPU sampling, or search loops.
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
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit
from scripts.igp24_submission_plan import (
    CANDIDATE_NAMES,
    VERIFIED_RESULT_NAMES,
    _disc_rank_key,
    _path_records,
    build_joined_rows,
    exported_coefficients,
    load_baseline_csv,
    select_best_per_pair,
)


REVIEW_JSONL = "scoreability_review.jsonl"
SUMMARY_JSON = "scoreability_review_summary.json"
REPORT_MD = "scoreability_review_report.md"
ACTIONABLE_JSONL = "actionable_submission_rows.jsonl"
SUBMISSION_COEFFICIENTS_TXT = "submission_coefficients.txt"
SUBMISSION_ANNOTATED_TXT = "submission_coefficients_annotated.txt"
PACKAGE_MANIFEST_JSON = "package_manifest.json"
PACKAGE_CHECKLIST_MD = "submission_checklist.md"
SAFETY_NOTE = (
    "Scoreability review is local/file-only and manual-output-only. It does "
    "not submit to SAIR, call SAIR APIs, call Magma/PARI, use the online "
    "calculator, train models, sample on GPU, run CPU search loops, or run "
    "local search."
)

ACTIONABLE_CLASSIFICATIONS = {
    "scoreable_new_pair",
    "scoreable_new_pair_generic_s24",
    "accepted_pair_discriminant_improvement_candidate",
    "baseline_pair_improvement_candidate",
}

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
ONLINE_MAGMA_DIRS = ("copy_paste_scripts", "checked_xml")


class ScoreabilityReviewError(ValueError):
    """Raised when scoreability review inputs are incomplete or inconsistent."""


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip().replace("_", "")
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def load_accepted_pairs(manifest_path: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if manifest_path is None:
        return {}, {"accepted_manifest_loaded": False, "accepted_pairs": 0, "accepted_manifest_path": None}
    path = manifest_path.resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    rows = manifest.get("selected_record_summaries") or []
    accepted: dict[str, dict[str, Any]] = {}
    for row in rows:
        pair_key = str(row.get("pair_key") or "")
        nfdisc = _coerce_int(row.get("exact_nfdisc_abs"))
        if not pair_key:
            continue
        accepted[pair_key] = {
            "pair_key": pair_key,
            "accepted_hash": row.get("canonical_hash"),
            "accepted_short_hash": row.get("short_hash"),
            "accepted_exact_nfdisc_abs": nfdisc,
            "accepted_exact_nfdisc_source": row.get("exact_nfdisc_source"),
            "accepted_verified_group_label": row.get("verified_group_label"),
            "accepted_expected_r": row.get("expected_r"),
        }
    return accepted, {
        "accepted_manifest_loaded": True,
        "accepted_manifest_path": str(path),
        "accepted_pairs": len(accepted),
        "accepted_manifest_sha256": sha256_file(path),
    }


def _baseline_pair_count(path: Path) -> int:
    pairs: set[tuple[str, int]] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            label = str(row.get("label") or "")
            r_value = _coerce_int(row.get("r"))
            if label and r_value is not None:
                pairs.add((label, r_value))
    return len(pairs)


def _is_generic_s24(row: dict[str, Any]) -> bool:
    text = str(row.get("galois_group_text") or "").lower()
    return row.get("verified_group_label") == "24T25000" or "symmetric group" in text


def _accepted_status(row: dict[str, Any], accepted_pairs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    pair_key = str(row.get("pair_key") or "")
    accepted = accepted_pairs.get(pair_key)
    if accepted is None:
        return {
            "accepted_pair_status": "not_previously_accepted",
            "accepted_exact_nfdisc_abs": None,
            "accepted_short_hash": None,
            "accepted_nfdisc_delta": None,
            "accepted_nfdisc_ratio": None,
        }
    exact_nfdisc = _coerce_int(row.get("exact_nfdisc_abs"))
    accepted_nfdisc = _coerce_int(accepted.get("accepted_exact_nfdisc_abs"))
    delta = None
    ratio = None
    status = "accepted_pair_needs_exact_nfdisc"
    if exact_nfdisc is not None and accepted_nfdisc is not None:
        delta = exact_nfdisc - accepted_nfdisc
        ratio = exact_nfdisc / accepted_nfdisc if accepted_nfdisc else None
        if exact_nfdisc < accepted_nfdisc:
            status = "accepted_pair_discriminant_improvement_candidate"
        elif exact_nfdisc == accepted_nfdisc:
            status = "accepted_pair_duplicate_equal_nfdisc"
        else:
            status = "accepted_pair_duplicate_not_improved"
    return {
        **accepted,
        "accepted_pair_status": status,
        "accepted_nfdisc_delta": delta,
        "accepted_nfdisc_ratio": ratio,
    }


def _base_classification(row: dict[str, Any], accepted_info: dict[str, Any]) -> tuple[str, str]:
    if row.get("exact_r_status") != "ok":
        return "needs_more_verification", "Exact r is missing or proxy-only."
    if row.get("exact_nfdisc_status") != "ok":
        return "needs_more_verification", "Exact nfdisc is missing."

    accepted_status = str(accepted_info.get("accepted_pair_status") or "")
    if accepted_status == "accepted_pair_discriminant_improvement_candidate":
        return (
            "accepted_pair_discriminant_improvement_candidate",
            "This pair was already accepted for this team, but this row has a smaller exact nfdisc.",
        )
    if accepted_status == "accepted_pair_duplicate_equal_nfdisc":
        return "accepted_pair_duplicate_equal_nfdisc", "This accepted pair is not an improvement."
    if accepted_status == "accepted_pair_duplicate_not_improved":
        return "accepted_pair_duplicate_not_improved", "This accepted pair has a larger exact nfdisc."
    if accepted_status == "accepted_pair_needs_exact_nfdisc":
        return "needs_more_verification", "Accepted-pair comparison needs exact nfdisc."

    baseline_status = str(row.get("baseline_status") or "")
    if baseline_status == "baseline_improvement_candidate":
        return (
            "baseline_pair_improvement_candidate",
            "This baseline pair has an exact nfdisc below the frozen baseline threshold.",
        )
    if baseline_status == "baseline_not_improved":
        return "baseline_pair_not_scoreable", "This baseline pair does not beat the frozen baseline nfdisc."
    if baseline_status == "baseline_requires_exact_nfdisc":
        return "needs_more_verification", "This baseline pair needs exact nfdisc before it can score."
    if baseline_status == "invalid_pair_for_baseline_check":
        return "invalid_or_error", "The row is missing a valid label/signature pair."

    if row.get("scoreability_status") == "new_pair_candidate":
        if _is_generic_s24(row):
            return (
                "scoreable_new_pair_generic_s24",
                "This is generic S24, but the exact pair is absent from the frozen baseline.",
            )
        return "scoreable_new_pair", "This exact pair is absent from the frozen baseline."

    return "needs_more_verification", "The row is not yet in a scoreable state."


def classify_rows(
    joined_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    accepted_pairs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_by_pair = {str(row.get("pair_key")): row for row in selected_rows}
    classified: list[dict[str, Any]] = []
    for row in sorted(joined_rows, key=lambda item: (str(item.get("pair_key") or ""), _disc_rank_key(item))):
        out = dict(row)
        pair_key = str(out.get("pair_key") or "")
        selected = selected_by_pair.get(pair_key)
        selected_hash = selected.get("canonical_hash") if selected else None
        is_best_for_pending_pair = selected_hash == out.get("canonical_hash")
        accepted_info = _accepted_status(out, accepted_pairs)
        base_classification, note = _base_classification(out, accepted_info)
        if selected is not None and not is_best_for_pending_pair:
            classification = "duplicate_pending_pair_not_best"
            note = "Another pending row has a smaller preferred discriminant for this exact pair."
        else:
            classification = base_classification
        out.update(accepted_info)
        out.update(
            {
                "generic_s24": _is_generic_s24(out),
                "pending_pair_status": "best_for_pending_pair" if is_best_for_pending_pair else "duplicate_pending_pair_not_best",
                "pending_best_hash": selected_hash,
                "pending_best_short_hash": str(selected_hash or "")[:12] if selected_hash else None,
                "pending_best_exact_nfdisc_abs": selected.get("exact_nfdisc_abs") if selected else None,
                "scoreability_review_classification": classification,
                "scoreability_review_note": note,
                "actionable_for_manual_submission": classification in ACTIONABLE_CLASSIFICATIONS and is_best_for_pending_pair,
            }
        )
        classified.append(out)
    return classified


def _counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(field)) for record in records).items()))


def _coefficient_line(row: dict[str, Any], *, annotated: bool) -> str:
    coeffs = exported_coefficients(row)
    if coeffs is None:
        raise ScoreabilityReviewError(f"{row.get('short_hash')}: missing exported coefficients")
    line = ",".join(str(value) for value in coeffs)
    if not annotated:
        return line
    return (
        f"{line} # expected_pair={row.get('pair_key')} "
        f"class={row.get('scoreability_review_classification')} "
        f"nfdisc={row.get('exact_nfdisc_abs')} hash={row.get('short_hash')}"
    )


def _copy_file(src: Path, dst: Path) -> dict[str, Any] | None:
    if not src.exists() or not src.is_file():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "relative_path": str(dst),
        "source_path": str(src),
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
    }


def _copy_tree(src: Path, dst: Path) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    if not src.exists() or not src.is_dir():
        return copied
    for path in sorted(item for item in src.rglob("*") if item.is_file()):
        copied_file = _copy_file(path, dst / path.relative_to(src))
        if copied_file:
            copied.append(copied_file)
    return copied


def copy_supporting_artifacts(
    *,
    output_dir: Path,
    evidence_dir: Path | None,
    baseline_csv: Path | None,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    if baseline_csv is not None:
        copied_file = _copy_file(baseline_csv, output_dir / "baseline" / baseline_csv.name)
        if copied_file:
            copied.append(copied_file)
    if evidence_dir is not None and evidence_dir.exists():
        evidence_out = output_dir / "evidence"
        for name in EVIDENCE_FILES:
            copied_file = _copy_file(evidence_dir / name, evidence_out / name)
            if copied_file:
                copied.append(copied_file)
        online_out = evidence_out / "online_magma_manual"
        for name in ONLINE_MAGMA_FILES:
            copied_file = _copy_file(evidence_dir / "online_magma_manual" / name, online_out / name)
            if copied_file:
                copied.append(copied_file)
        for name in ONLINE_MAGMA_DIRS:
            copied.extend(_copy_tree(evidence_dir / "online_magma_manual" / name, online_out / name))
        copied.extend(_copy_tree(evidence_dir / "magma_candidate_scripts", evidence_out / "magma_candidate_scripts"))

    raw_out = output_dir / "raw_magma_xml"
    for row in rows:
        raw_path = row.get("raw_output_source_path")
        if raw_path:
            src = Path(str(raw_path))
            copied_file = _copy_file(src, raw_out / src.name)
            if copied_file:
                copied.append(copied_file)
    return copied


def build_summary(
    *,
    reviewed_rows: list[dict[str, Any]],
    actionable_rows: list[dict[str, Any]],
    verified_paths: list[Path],
    candidate_paths: list[Path],
    baseline_info: dict[str, Any],
    accepted_info: dict[str, Any],
    diagnostics: dict[str, Any],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    copied_files: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_scoreability_review.py",
        "source_commit": source_commit,
        "command": command,
        "verified_result_paths": [str(path) for path in verified_paths],
        "candidate_paths": [str(path) for path in candidate_paths],
        "baseline": baseline_info,
        "accepted_submission": accepted_info,
        "input_diagnostics": diagnostics,
        "reviewed_rows": len(reviewed_rows),
        "actionable_rows": len(actionable_rows),
        "classification_counts": _counts(reviewed_rows, "scoreability_review_classification"),
        "baseline_status_counts": _counts(reviewed_rows, "baseline_status"),
        "accepted_pair_status_counts": _counts(reviewed_rows, "accepted_pair_status"),
        "pending_pair_status_counts": _counts(reviewed_rows, "pending_pair_status"),
        "actionable_pairs": [row.get("pair_key") for row in actionable_rows],
        "actionable_hashes": [row.get("canonical_hash") for row in actionable_rows],
        "output_files": {
            "review_jsonl": str(output_dir / REVIEW_JSONL),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
            "actionable_jsonl": str(output_dir / ACTIONABLE_JSONL),
            "submission_coefficients_txt": str(output_dir / SUBMISSION_COEFFICIENTS_TXT),
            "submission_annotated_txt": str(output_dir / SUBMISSION_ANNOTATED_TXT),
            "package_manifest_json": str(output_dir / PACKAGE_MANIFEST_JSON),
            "submission_checklist_md": str(output_dir / PACKAGE_CHECKLIST_MD),
        },
        "copied_files": copied_files,
        "recommendation": (
            "Submit the actionable coefficient file manually if the team wants this incremental score attempt."
            if actionable_rows
            else "Do not submit these rows; no actionable score candidate survived review."
        ),
        "safety": {
            "local_file_only": True,
            "manual_output_only": True,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls_by_helper": False,
            "magma_executed": False,
            "pari_executed": False,
            "online_calculator_called": False,
            "gpu_training": False,
            "cpu_search_loop": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], reviewed_rows: list[dict[str, Any]], actionable_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Scoreability Review",
        "",
        SAFETY_NOTE,
        "",
        f"- Reviewed rows: {summary.get('reviewed_rows')}",
        f"- Actionable rows: {summary.get('actionable_rows')}",
        f"- Classification counts: `{json.dumps(summary.get('classification_counts'), sort_keys=True)}`",
        f"- Baseline status counts: `{json.dumps(summary.get('baseline_status_counts'), sort_keys=True)}`",
        f"- Accepted-pair status counts: `{json.dumps(summary.get('accepted_pair_status_counts'), sort_keys=True)}`",
        f"- Recommendation: {summary.get('recommendation')}",
        "",
        "## Row Classification",
        "",
        "| pair | hash | nfdisc | baseline | accepted status | pending status | class | note |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in reviewed_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('pair_key')}`",
                    f"`{row.get('short_hash')}`",
                    str(row.get("exact_nfdisc_abs")),
                    str(row.get("baseline_status")),
                    str(row.get("accepted_pair_status")),
                    str(row.get("pending_pair_status")),
                    str(row.get("scoreability_review_classification")),
                    str(row.get("scoreability_review_note")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Actionable Rows", ""])
    if actionable_rows:
        lines.extend(
            [
                "| pair | hash | class | nfdisc |",
                "| --- | --- | --- | ---: |",
            ]
        )
        for row in actionable_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row.get('pair_key')}`",
                        f"`{row.get('short_hash')}`",
                        str(row.get("scoreability_review_classification")),
                        str(row.get("exact_nfdisc_abs")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No rows are actionable for manual submission.")
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Clean coefficients: `{summary.get('output_files', {}).get('submission_coefficients_txt')}`",
            f"- Annotated coefficients: `{summary.get('output_files', {}).get('submission_annotated_txt')}`",
            f"- Manifest: `{summary.get('output_files', {}).get('package_manifest_json')}`",
            f"- Checklist: `{summary.get('output_files', {}).get('submission_checklist_md')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_checklist(summary: dict[str, Any], actionable_rows: list[dict[str, Any]]) -> str:
    def mark(value: bool) -> str:
        return "x" if value else " "

    pair_counts = Counter(str(row.get("pair_key") or "") for row in actionable_rows)
    one_row_per_pair = bool(actionable_rows) and all(count == 1 for count in pair_counts.values())
    all_exact = all(row.get("exact_r_status") == "ok" and row.get("exact_nfdisc_status") == "ok" for row in actionable_rows)
    lines = [
        "# IGP24 Manual Scoreability Package Checklist",
        "",
        "This package is for manual review only. No SAIR submission or API call was performed.",
        "",
        f"- [{mark(bool(actionable_rows))}] At least one actionable row.",
        f"- [{mark(one_row_per_pair)}] One row per `(24Tt, r)` pair.",
        f"- [{mark(all_exact)}] Every actionable row has exact `r` and exact `nfdisc` evidence.",
        f"- [{mark(not summary.get('safety', {}).get('sair_submission'))}] No SAIR/API submission has been performed.",
        "",
        "## Selected Rows",
        "",
        "| pair | hash | class | nfdisc |",
        "| --- | --- | --- | ---: |",
    ]
    for row in actionable_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('pair_key')}`",
                    f"`{row.get('short_hash')}`",
                    str(row.get("scoreability_review_classification")),
                    str(row.get("exact_nfdisc_abs")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            f"- Clean coefficient file: `{summary.get('output_files', {}).get('submission_coefficients_txt')}`",
            f"- Annotated coefficient file: `{summary.get('output_files', {}).get('submission_annotated_txt')}`",
            f"- Review report: `{summary.get('output_files', {}).get('report_md')}`",
            f"- Manifest: `{summary.get('output_files', {}).get('package_manifest_json')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    *,
    reviewed_rows: list[dict[str, Any]],
    actionable_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    review_path = output_dir / REVIEW_JSONL
    actionable_path = output_dir / ACTIONABLE_JSONL
    coefficients_path = output_dir / SUBMISSION_COEFFICIENTS_TXT
    annotated_path = output_dir / SUBMISSION_ANNOTATED_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    manifest_path = output_dir / PACKAGE_MANIFEST_JSON
    checklist_path = output_dir / PACKAGE_CHECKLIST_MD

    write_jsonl(review_path, reviewed_rows)
    write_jsonl(actionable_path, actionable_rows)
    coefficients_path.write_text("\n".join(_coefficient_line(row, annotated=False) for row in actionable_rows) + ("\n" if actionable_rows else ""), encoding="utf-8")
    annotated_path.write_text("\n".join(_coefficient_line(row, annotated=True) for row in actionable_rows) + ("\n" if actionable_rows else ""), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, reviewed_rows, actionable_rows), encoding="utf-8")
    manifest_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist_path.write_text(build_checklist(summary, actionable_rows), encoding="utf-8")
    return {
        "review_jsonl": review_path,
        "actionable_jsonl": actionable_path,
        "submission_coefficients_txt": coefficients_path,
        "submission_annotated_txt": annotated_path,
        "summary_json": summary_path,
        "report_md": report_path,
        "package_manifest_json": manifest_path,
        "submission_checklist_md": checklist_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review verified IGP24 rows against baseline and accepted pairs")
    parser.add_argument("--verified_results", nargs="+", type=Path, required=True, help="Verified result JSONL files or directories")
    parser.add_argument("--candidate_jsonl", action="append", type=Path, default=[], help="Candidate JSONL file or directory; repeatable")
    parser.add_argument("--baseline_csv", type=Path, required=True)
    parser.add_argument("--accepted_package_manifest", type=Path, required=True)
    parser.add_argument("--evidence_dir", type=Path, help="Optional evidence directory to copy into the review package")
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        verified_rows, verified_paths = _path_records(args.verified_results, VERIFIED_RESULT_NAMES)
        candidate_rows, candidate_paths = _path_records(args.candidate_jsonl, CANDIDATE_NAMES) if args.candidate_jsonl else ([], [])
        baseline, baseline_info = load_baseline_csv(args.baseline_csv)
        baseline_info["baseline_pair_count_recounted"] = _baseline_pair_count(args.baseline_csv.resolve())
        accepted_pairs, accepted_info = load_accepted_pairs(args.accepted_package_manifest)
        joined, diagnostics = build_joined_rows(
            verified_rows=verified_rows,
            candidate_rows=candidate_rows,
            baseline=baseline,
            baseline_loaded=bool(baseline_info.get("baseline_loaded")),
        )
        selected, suppressed = select_best_per_pair(joined)
        diagnostics["suppressed_duplicate_pair_candidates"] = len(suppressed)
        reviewed_rows = classify_rows(joined, selected, accepted_pairs)
        actionable_rows = [row for row in reviewed_rows if row.get("actionable_for_manual_submission")]
        actionable_rows.sort(key=lambda row: (str(row.get("scoreability_review_classification")), str(row.get("pair_key"))))
        output_dir = args.output_dir.resolve()
        copied_files = copy_supporting_artifacts(
            output_dir=output_dir,
            evidence_dir=args.evidence_dir.resolve() if args.evidence_dir else None,
            baseline_csv=args.baseline_csv.resolve(),
            rows=actionable_rows,
        )
        command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_scoreability_review.py", *argv]
        summary = build_summary(
            reviewed_rows=reviewed_rows,
            actionable_rows=actionable_rows,
            verified_paths=verified_paths,
            candidate_paths=candidate_paths,
            baseline_info=baseline_info,
            accepted_info=accepted_info,
            diagnostics=diagnostics,
            output_dir=output_dir,
            command=command,
            source_commit=get_source_commit(args.repo_root.resolve()),
            copied_files=copied_files,
        )
        paths = write_outputs(
            reviewed_rows=reviewed_rows,
            actionable_rows=actionable_rows,
            summary=summary,
            output_dir=output_dir,
        )
    except (FileNotFoundError, json.JSONDecodeError, ScoreabilityReviewError, ValueError) as exc:
        parser.error(str(exc))

    print(f"reviewed_rows\t{summary['reviewed_rows']}")
    print(f"actionable_rows\t{summary['actionable_rows']}")
    print(f"classification_counts\t{json.dumps(summary['classification_counts'], sort_keys=True)}")
    print(f"accepted_pair_status_counts\t{json.dumps(summary['accepted_pair_status_counts'], sort_keys=True)}")
    print(f"actionable_pairs\t{json.dumps(summary['actionable_pairs'])}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
