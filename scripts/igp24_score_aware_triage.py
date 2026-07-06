#!/usr/bin/env python3
"""Score-aware triage for IGP24 exact-verification queues.

This helper is local/file-only. It joins a candidate queue with saved exact
evidence artifacts, the frozen baseline, and the local pair-status ledger. It
then classifies each row for score-aware submission readiness. It never calls
SAIR, Magma, PARI, online calculators, training, GPU sampling, CPU search
loops, or local search.
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

from scripts.igp24_shortlist import get_source_commit, read_jsonl


TRIAGE_JSONL = "score_aware_triage.jsonl"
SUMMARY_JSON = "score_aware_triage_summary.json"
REPORT_MD = "score_aware_triage_report.md"
SUBMISSION_CANDIDATES_JSONL = "submission_grade_rows.jsonl"
SUBMISSION_COEFFICIENTS_TXT = "submission_grade_coefficients.txt"
MANUAL_CHECKLIST_MD = "manual_magma_checklist.md"
SAFETY_NOTE = (
    "Score-aware triage is local/file-only. It does not submit to SAIR, call "
    "SAIR APIs, call Magma/PARI, use online calculators, train models, sample "
    "on GPU, run CPU search loops, or run local search."
)
SCORE_LESSON_NOTE = (
    "The first accepted five rows were valid but each scored <0.0001; "
    "acceptance alone is not enough. Prioritize genuinely new non-baseline "
    "non-generic pairs, or accepted-pair duplicates only when the exact "
    "discriminant improvement is material."
)


class ScoreAwareTriageError(ValueError):
    """Raised when score-aware triage inputs are malformed."""


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


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
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


def pair_key(label: str | None, r_value: int | None) -> str | None:
    if label is None or r_value is None:
        return None
    return f"{label}|r={int(r_value)}"


def exported_coefficients(record: dict[str, Any]) -> list[int] | None:
    for field in ("exported_coefficients", "coefficients", "decoded_coefficients"):
        value = record.get(field)
        if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
            continue
        if len(value) == 25 and value[-1] == 1:
            return list(value)
        if len(value) == 24:
            return list(value) + [1]
    return None


def coefficient_line(record: dict[str, Any]) -> str:
    coeffs = exported_coefficients(record)
    if coeffs is None:
        raise ScoreAwareTriageError(f"{record.get('canonical_hash')}: missing coefficients")
    return ",".join(str(value) for value in coeffs)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _hash_key(record: dict[str, Any]) -> str | None:
    value = record.get("candidate_hash") or record.get("canonical_hash")
    return value if isinstance(value, str) and value else None


def _read_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return read_jsonl(path)


def _index_by_hash(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = _hash_key(row)
        if key:
            indexed[key] = dict(row)
    return indexed


def load_baseline_pairs(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    baseline: dict[str, dict[str, Any]] = {}
    rows_loaded = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows_loaded += 1
            label = normalize_label(row.get("label"))
            r_value = _coerce_int(row.get("r"))
            key = pair_key(label, r_value)
            if key:
                baseline[key] = {
                    "pair_key": key,
                    "label": label,
                    "r": r_value,
                    "baseline_nfdisc_abs": _coerce_int(row.get("nfdisc_abs")),
                    "baseline_poly_disc_abs": _coerce_int(row.get("poly_disc_abs")),
                    "baseline_scoring_disc": row.get("scoring_disc"),
                }
    return baseline, {"path": str(path), "rows_loaded": rows_loaded, "pairs": len(baseline)}


def load_pair_status(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pairs: dict[str, dict[str, Any]] = {}
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
        item["exact_nfdisc_abs"] = _coerce_int(raw.get("exact_nfdisc_abs"))
        pairs[key] = item
    return pairs, {
        "path": str(path),
        "records": len(pairs),
        "status_counts": dict(sorted(Counter(item["status"] for item in pairs.values()).items())),
    }


def load_evidence(offline_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    online = _index_by_hash(
        _read_jsonl_if_exists(offline_dir / "online_magma_manual" / "online_magma_manual_results.jsonl")
    )
    local_magma = _index_by_hash(_read_jsonl_if_exists(offline_dir / "magma_verification_results.jsonl"))
    pari_nfdisc = _index_by_hash(_read_jsonl_if_exists(offline_dir / "pari_nfdisc_results.jsonl"))
    sympy_nfdisc = _index_by_hash(_read_jsonl_if_exists(offline_dir / "sympy_nfdisc_results.jsonl"))
    sympy_signature = _index_by_hash(_read_jsonl_if_exists(offline_dir / "sympy_signature_results.jsonl"))
    return {
        "online_magma": online,
        "local_magma": local_magma,
        "pari_nfdisc": pari_nfdisc,
        "sympy_nfdisc": sympy_nfdisc,
        "sympy_signature": sympy_signature,
    }


def _label_evidence(hash_value: str, evidence: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any] | None:
    for source_name in ("online_magma", "local_magma"):
        row = evidence[source_name].get(hash_value)
        if not row:
            continue
        label = normalize_label(row.get("verified_group_label"))
        if label:
            out = dict(row)
            out["exact_label_source"] = source_name
            out["verified_group_label"] = label
            return out
    return None


def _nfdisc_evidence(hash_value: str, evidence: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any] | None:
    for source_name in ("pari_nfdisc", "sympy_nfdisc"):
        row = evidence[source_name].get(hash_value)
        if not row:
            continue
        nfdisc = _coerce_int(row.get("exact_nfdisc_abs") or row.get("nfdisc_abs"))
        if nfdisc is not None:
            out = dict(row)
            out["exact_nfdisc_abs"] = nfdisc
            out["exact_nfdisc_source"] = row.get("exact_nfdisc_source") or row.get("nfdisc_source") or source_name
            out["exact_nfdisc_status"] = "ok"
            return out
    return None


def _signature_evidence(
    hash_value: str,
    label_row: dict[str, Any] | None,
    evidence: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any] | None:
    if label_row:
        r_value = _coerce_int(label_row.get("computed_r") or label_row.get("signature_r"))
        if r_value is not None:
            return {
                "computed_r": r_value,
                "signature_r": r_value,
                "exact_r_status": "ok",
                "exact_r_source": label_row.get("exact_r_source") or "magma_number_of_real_roots",
            }
    row = evidence["sympy_signature"].get(hash_value)
    if row:
        r_value = _coerce_int(row.get("computed_r") or row.get("signature_r") or row.get("sympy_real_root_count"))
        if r_value is not None:
            return {
                "computed_r": r_value,
                "signature_r": r_value,
                "exact_r_status": "ok",
                "exact_r_source": row.get("exact_r_source") or "sympy_poly_count_roots",
            }
    pari_row = evidence["pari_nfdisc"].get(hash_value)
    if pari_row:
        r_value = _coerce_int(pari_row.get("pari_real_root_count"))
        if r_value is not None:
            return {
                "computed_r": r_value,
                "signature_r": r_value,
                "exact_r_status": "ok",
                "exact_r_source": "pari_polsturm",
            }
    return None


def accepted_pair_status(
    *,
    pair: str | None,
    exact_nfdisc_abs: int | None,
    pair_status: dict[str, dict[str, Any]],
    material_ratio: float,
) -> dict[str, Any]:
    if pair is None or pair not in pair_status:
        return {
            "accepted_pair_status": "not_previously_accepted",
            "accepted_exact_nfdisc_abs": None,
            "accepted_nfdisc_ratio": None,
        }
    accepted = pair_status[pair]
    accepted_nfdisc = _coerce_int(accepted.get("exact_nfdisc_abs"))
    ratio = None
    status = "accepted_pair_needs_exact_nfdisc"
    if exact_nfdisc_abs is not None and accepted_nfdisc is not None and accepted_nfdisc:
        ratio = exact_nfdisc_abs / accepted_nfdisc
        if exact_nfdisc_abs < accepted_nfdisc and ratio <= material_ratio:
            status = "accepted_pair_material_discriminant_improvement"
        elif exact_nfdisc_abs < accepted_nfdisc:
            status = "accepted_pair_minor_discriminant_improvement"
        elif exact_nfdisc_abs == accepted_nfdisc:
            status = "accepted_pair_duplicate_equal_nfdisc"
        else:
            status = "accepted_pair_duplicate_not_improved"
    return {
        "accepted_pair_status": status,
        "accepted_exact_nfdisc_abs": accepted_nfdisc,
        "accepted_short_hash": accepted.get("short_hash"),
        "accepted_nfdisc_ratio": ratio,
        "accepted_leaderboard_scoring": accepted.get("leaderboard_scoring"),
    }


def classify_row(
    row: dict[str, Any],
    *,
    baseline_pairs: dict[str, dict[str, Any]],
    pair_status: dict[str, dict[str, Any]],
    material_ratio: float,
    allow_generic_submission: bool,
) -> dict[str, Any]:
    exact_label = normalize_label(row.get("verified_group_label"))
    exact_r = _coerce_int(row.get("computed_r") or row.get("signature_r"))
    exact_nfdisc = _coerce_int(row.get("exact_nfdisc_abs"))
    pair = pair_key(exact_label, exact_r)
    accepted_info = accepted_pair_status(
        pair=pair,
        exact_nfdisc_abs=exact_nfdisc,
        pair_status=pair_status,
        material_ratio=material_ratio,
    )
    baseline_info = baseline_pairs.get(pair or "")
    degree = _coerce_int(row.get("degree"))
    irreducible = _coerce_bool(row.get("is_irreducible"))
    generic_s24 = exact_label == "24T25000" or "symmetric group" in str(row.get("galois_group_text") or "").lower()

    exact_label_status = "ok" if exact_label else "missing"
    exact_r_status = "ok" if exact_r is not None else "missing"
    exact_nfdisc_status = "ok" if exact_nfdisc is not None else "missing"
    if exact_label is None:
        classification = "exact_result_missing"
        note = "Exact Magma label is missing; exact r/nfdisc fallback evidence alone is not submission-grade."
    elif degree not in (None, 24) or irreducible is False:
        classification = "invalid_unverified"
        note = "Exact result did not prove a degree-24 irreducible polynomial."
    elif exact_r is None or exact_nfdisc is None:
        classification = "exact_evidence_incomplete"
        note = "Exact label exists, but exact r or exact nfdisc is missing."
    elif pair in baseline_pairs:
        classification = "baseline_pair"
        note = "Exact pair is already present in the frozen official baseline."
    elif generic_s24:
        classification = "generic_24T25000"
        note = "Generic S24 rows may score if new, but are lower-priority than non-generic discoveries."
    elif accepted_info["accepted_pair_status"] == "accepted_pair_material_discriminant_improvement":
        classification = "accepted_pair_material_discriminant_improvement"
        note = "Accepted pair duplicate has a material exact-nfdisc improvement."
    elif accepted_info["accepted_pair_status"].startswith("accepted_pair_") and accepted_info[
        "accepted_pair_status"
    ] != "not_previously_accepted":
        classification = "accepted_pair_duplicate"
        note = "Pair is already accepted locally; prior accepted pairs scored <0.0001 unless discriminants improve materially."
    else:
        classification = "new_non_baseline_pair"
        note = "Exact non-generic pair is absent from the frozen baseline and local accepted ledger."

    submission_grade = classification == "new_non_baseline_pair" or classification == (
        "accepted_pair_material_discriminant_improvement"
    )
    if generic_s24 and not allow_generic_submission:
        submission_grade = False

    return {
        **row,
        **accepted_info,
        "verified_group_label": exact_label,
        "computed_r": exact_r,
        "pair_key": pair,
        "exact_nfdisc_abs": exact_nfdisc,
        "exact_label_status": exact_label_status,
        "exact_r_status": exact_r_status,
        "exact_nfdisc_status": exact_nfdisc_status,
        "baseline_pair_status": "baseline_pair" if baseline_info else "not_in_baseline_or_unknown_label",
        "baseline_nfdisc_abs": baseline_info.get("baseline_nfdisc_abs") if baseline_info else None,
        "baseline_scoring_disc": baseline_info.get("baseline_scoring_disc") if baseline_info else None,
        "generic_s24": generic_s24,
        "score_aware_classification": classification,
        "score_aware_note": note,
        "submission_grade_candidate": submission_grade,
    }


def build_triage_rows(
    queue_rows: list[dict[str, Any]],
    *,
    evidence: dict[str, dict[str, dict[str, Any]]],
    baseline_pairs: dict[str, dict[str, Any]],
    pair_status: dict[str, dict[str, Any]],
    material_ratio: float,
    allow_generic_submission: bool,
) -> list[dict[str, Any]]:
    triaged: list[dict[str, Any]] = []
    for index, queue_row in enumerate(queue_rows, start=1):
        canonical_hash = str(queue_row.get("canonical_hash") or queue_row.get("candidate_hash") or "")
        if not canonical_hash:
            raise ScoreAwareTriageError(f"queue row {index}: missing canonical_hash")
        label_row = _label_evidence(canonical_hash, evidence)
        nfdisc_row = _nfdisc_evidence(canonical_hash, evidence)
        signature_row = _signature_evidence(canonical_hash, label_row, evidence)
        merged = {
            **queue_row,
            "triage_rank": index,
            "canonical_hash": canonical_hash,
            "short_hash": str(queue_row.get("short_hash") or canonical_hash[:12]),
            "exact_label_source": label_row.get("exact_label_source") if label_row else None,
            "verified_group_label": label_row.get("verified_group_label") if label_row else None,
            "transitive_group_id": label_row.get("transitive_group_id") if label_row else None,
            "galois_group_text": label_row.get("galois_group_text") if label_row else None,
            "degree": label_row.get("degree") if label_row else nfdisc_row.get("degree") if nfdisc_row else None,
            "is_irreducible": label_row.get("is_irreducible") if label_row else None,
            "raw_output_source_path": label_row.get("raw_output_source_path") if label_row else None,
            "computed_r": signature_row.get("computed_r") if signature_row else None,
            "signature_r": signature_row.get("signature_r") if signature_row else None,
            "exact_r_source": signature_row.get("exact_r_source") if signature_row else None,
            "exact_nfdisc_abs": nfdisc_row.get("exact_nfdisc_abs") if nfdisc_row else None,
            "exact_nfdisc_source": nfdisc_row.get("exact_nfdisc_source") if nfdisc_row else None,
            "pari_degree": nfdisc_row.get("pari_degree") if nfdisc_row else None,
            "pari_is_irreducible": nfdisc_row.get("pari_is_irreducible") if nfdisc_row else None,
            "pari_real_root_count": nfdisc_row.get("pari_real_root_count") if nfdisc_row else None,
        }
        triaged.append(
            classify_row(
                merged,
                baseline_pairs=baseline_pairs,
                pair_status=pair_status,
                material_ratio=material_ratio,
                allow_generic_submission=allow_generic_submission,
            )
        )
    return triaged


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def build_summary(
    *,
    queue_path: Path,
    offline_dir: Path,
    baseline_info: dict[str, Any],
    pair_status_info: dict[str, Any],
    triage_rows: list[dict[str, Any]],
    submission_rows: list[dict[str, Any]],
    output_dir: Path,
    command: list[str],
    source_commit: str | None,
    material_ratio: float,
    allow_generic_submission: bool,
) -> dict[str, Any]:
    verified = [row for row in triage_rows if row.get("exact_label_status") == "ok"]
    missing = [row for row in triage_rows if row.get("score_aware_classification") == "exact_result_missing"]
    failed = [row for row in triage_rows if row.get("score_aware_classification") == "invalid_unverified"]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_score_aware_triage.py",
        "source_commit": source_commit,
        "command": command,
        "queue_jsonl": str(queue_path),
        "offline_verification_dir": str(offline_dir),
        "baseline": baseline_info,
        "pair_status": pair_status_info,
        "options": {
            "accepted_material_improvement_ratio": material_ratio,
            "allow_generic_submission": allow_generic_submission,
        },
        "reviewed_rows": len(triage_rows),
        "verified_rows": len(verified),
        "failed_rows": len(failed),
        "pending_exact_label_rows": len(missing),
        "submission_grade_rows": len(submission_rows),
        "labels_found_counts": _counts(verified, "verified_group_label"),
        "classification_counts": _counts(triage_rows, "score_aware_classification"),
        "exact_label_status_counts": _counts(triage_rows, "exact_label_status"),
        "exact_r_status_counts": _counts(triage_rows, "exact_r_status"),
        "exact_nfdisc_status_counts": _counts(triage_rows, "exact_nfdisc_status"),
        "strategy_counts": _counts(triage_rows, "source_strategy"),
        "submission_grade_hashes": [row.get("canonical_hash") for row in submission_rows],
        "submission_grade_pairs": [row.get("pair_key") for row in submission_rows],
        "score_lesson": {
            "prior_accepted_pair_score_text": "<0.0001",
            "acceptance_alone_is_not_enough": True,
            "note": SCORE_LESSON_NOTE,
        },
        "output_files": {
            "triage_jsonl": str(output_dir / TRIAGE_JSONL),
            "summary_json": str(output_dir / SUMMARY_JSON),
            "report_md": str(output_dir / REPORT_MD),
            "submission_candidates_jsonl": str(output_dir / SUBMISSION_CANDIDATES_JSONL),
            "submission_coefficients_txt": str(output_dir / SUBMISSION_COEFFICIENTS_TXT),
            "manual_checklist_md": str(output_dir / MANUAL_CHECKLIST_MD),
        },
        "safety": {
            "local_file_only": True,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "magma_executed": False,
            "pari_executed_by_triage": False,
            "online_calculator_called": False,
            "gpu_training": False,
            "cpu_search_loop": False,
            "local_search_executed": False,
            "note": SAFETY_NOTE,
        },
    }


def build_report(summary: dict[str, Any], triage_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 Score-Aware Triage",
        "",
        SAFETY_NOTE,
        "",
        SCORE_LESSON_NOTE,
        "",
        f"- Queue: `{summary.get('queue_jsonl')}`",
        f"- Exact artifact: `{summary.get('offline_verification_dir')}`",
        f"- Reviewed rows: {summary.get('reviewed_rows')}",
        f"- Verified labels: {summary.get('verified_rows')}",
        f"- Pending exact labels: {summary.get('pending_exact_label_rows')}",
        f"- Failed rows: {summary.get('failed_rows')}",
        f"- Submission-grade rows: {summary.get('submission_grade_rows')}",
        f"- Classification counts: `{json.dumps(summary.get('classification_counts'), sort_keys=True)}`",
        f"- Labels found: `{json.dumps(summary.get('labels_found_counts'), sort_keys=True)}`",
        f"- Exact r status counts: `{json.dumps(summary.get('exact_r_status_counts'), sort_keys=True)}`",
        f"- Exact nfdisc status counts: `{json.dumps(summary.get('exact_nfdisc_status_counts'), sort_keys=True)}`",
        "",
        "## Row Triage",
        "",
        "| rank | hash | label | r | nfdisc | class | submit | note |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in triage_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("triage_rank")),
                    f"`{row.get('short_hash')}`",
                    str(row.get("verified_group_label") or ""),
                    str(row.get("computed_r") or ""),
                    str(row.get("exact_nfdisc_abs") or ""),
                    str(row.get("score_aware_classification")),
                    "yes" if row.get("submission_grade_candidate") else "no",
                    str(row.get("score_aware_note")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
        ]
    )
    if summary.get("submission_grade_rows"):
        lines.append("Build a manual submission package from `submission_grade_coefficients.txt` after human review.")
    else:
        lines.append(
            "Do not submit this queue yet. Exact labels are still missing; run the manual Magma scripts, paste outputs into the template, and rerun this triage."
        )
    lines.extend(
        [
            "",
            "Artifacts:",
            f"- Triage JSONL: `{summary.get('output_files', {}).get('triage_jsonl')}`",
            f"- Submission-grade JSONL: `{summary.get('output_files', {}).get('submission_candidates_jsonl')}`",
            f"- Submission-grade coefficients: `{summary.get('output_files', {}).get('submission_coefficients_txt')}`",
            f"- Manual checklist: `{summary.get('output_files', {}).get('manual_checklist_md')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_manual_checklist(summary: dict[str, Any], triage_rows: list[dict[str, Any]]) -> str:
    offline_dir = Path(str(summary.get("offline_verification_dir")))
    template = offline_dir / "online_magma_manual" / "online_magma_pasted_outputs_template.jsonl"
    scripts_dir = offline_dir / "online_magma_manual" / "copy_paste_scripts"
    lines = [
        "# Manual Magma Checklist",
        "",
        "This queue is not submission-grade until exact Magma labels are parsed.",
        "",
        "1. Open the one-candidate scripts in:",
        f"   `{scripts_dir}`",
        "2. Paste each script manually into the free online Magma calculator.",
        "3. Paste each returned output into the matching `pasted_output` field in:",
        f"   `{template}`",
        "4. Re-run `scripts/igp24_offline_verify.py` with `--online_magma_pasted_output` pointing at that filled template.",
        "5. Re-run `scripts/igp24_score_aware_triage.py` on the refreshed exact artifact.",
        "",
        "Do not automate online calculator submission without explicit approval.",
        "",
        "## Queue",
        "",
        "| rank | hash | script | exact r | exact nfdisc | status |",
        "| ---: | --- | --- | ---: | ---: | --- |",
    ]
    for row in triage_rows:
        script_path = row.get("script_path") or row.get("online_magma_script_path")
        if not script_path:
            script_path = str(scripts_dir / f"{int(row.get('triage_rank') or 0):04d}_{row.get('canonical_hash')}.m")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("triage_rank")),
                    f"`{row.get('short_hash')}`",
                    f"`{script_path}`",
                    str(row.get("computed_r") or ""),
                    str(row.get("exact_nfdisc_abs") or ""),
                    str(row.get("score_aware_classification")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(
    *,
    output_dir: Path,
    summary: dict[str, Any],
    triage_rows: list[dict[str, Any]],
    submission_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    triage_path = output_dir / TRIAGE_JSONL
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    submission_jsonl_path = output_dir / SUBMISSION_CANDIDATES_JSONL
    submission_coefficients_path = output_dir / SUBMISSION_COEFFICIENTS_TXT
    checklist_path = output_dir / MANUAL_CHECKLIST_MD
    write_jsonl(triage_path, triage_rows)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary, triage_rows), encoding="utf-8")
    write_jsonl(submission_jsonl_path, submission_rows)
    submission_coefficients_path.write_text(
        "".join(coefficient_line(row) + "\n" for row in submission_rows),
        encoding="utf-8",
    )
    checklist_path.write_text(build_manual_checklist(summary, triage_rows), encoding="utf-8")
    return {
        "triage_jsonl": triage_path,
        "summary_json": summary_path,
        "report_md": report_path,
        "submission_candidates_jsonl": submission_jsonl_path,
        "submission_coefficients_txt": submission_coefficients_path,
        "manual_checklist_md": checklist_path,
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a score-aware IGP24 verification triage artifact")
    parser.add_argument("--queue_jsonl", type=Path, required=True)
    parser.add_argument("--offline_dir", type=Path, required=True)
    parser.add_argument("--baseline_csv", type=Path, required=True)
    parser.add_argument("--pair_status_json", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--accepted_material_improvement_ratio", type=float, default=0.5)
    parser.add_argument("--allow_generic_submission", action="store_true")
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    try:
        queue_path = args.queue_jsonl.resolve()
        offline_dir = args.offline_dir.resolve()
        output_dir = args.output_dir.resolve()
        queue_rows = read_jsonl(queue_path)
        baseline_pairs, baseline_info = load_baseline_pairs(args.baseline_csv.resolve())
        pair_status, pair_status_info = load_pair_status(args.pair_status_json.resolve())
        evidence = load_evidence(offline_dir)
        triage_rows = build_triage_rows(
            queue_rows,
            evidence=evidence,
            baseline_pairs=baseline_pairs,
            pair_status=pair_status,
            material_ratio=float(args.accepted_material_improvement_ratio),
            allow_generic_submission=bool(args.allow_generic_submission),
        )
        submission_rows = [row for row in triage_rows if row.get("submission_grade_candidate")]
    except (FileNotFoundError, ScoreAwareTriageError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_score_aware_triage.py", *argv]
    summary = build_summary(
        queue_path=queue_path,
        offline_dir=offline_dir,
        baseline_info=baseline_info,
        pair_status_info=pair_status_info,
        triage_rows=triage_rows,
        submission_rows=submission_rows,
        output_dir=output_dir,
        command=command,
        source_commit=get_source_commit(args.repo_root.resolve()),
        material_ratio=float(args.accepted_material_improvement_ratio),
        allow_generic_submission=bool(args.allow_generic_submission),
    )
    paths = write_outputs(
        output_dir=output_dir,
        summary=summary,
        triage_rows=triage_rows,
        submission_rows=submission_rows,
    )
    print(f"reviewed_rows\t{summary['reviewed_rows']}")
    print(f"verified_rows\t{summary['verified_rows']}")
    print(f"pending_exact_label_rows\t{summary['pending_exact_label_rows']}")
    print(f"failed_rows\t{summary['failed_rows']}")
    print(f"submission_grade_rows\t{summary['submission_grade_rows']}")
    print(f"classification_counts\t{json.dumps(summary['classification_counts'], sort_keys=True)}")
    print(f"labels_found_counts\t{json.dumps(summary['labels_found_counts'], sort_keys=True)}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
