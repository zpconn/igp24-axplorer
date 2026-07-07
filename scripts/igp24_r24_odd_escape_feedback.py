#!/usr/bin/env python3
"""Ingest verified SAIR feedback for the r24 tower odd-escape probe.

This helper joins a saved SAIR submission response back to the local
``r24_tower_odd_escape`` queue, emits a compact accepted-feedback artifact, and
optionally appends scoreable duplicate rows as alternates in the pair-status
ledger. It is local/file-only after the SAIR response has been saved.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit, read_jsonl  # noqa: E402


DEFAULT_RESPONSE = (
    REPO_ROOT
    / "data/igp24/r24_tower_odd_escape_probe_20260707/r24_tower_odd_escape_sair_verified_response.json"
)
DEFAULT_QUEUE = (
    REPO_ROOT
    / "data/igp24/r24_tower_odd_escape_probe_20260707/r24_tower_odd_escape_candidate_queue.jsonl"
)
DEFAULT_COEFFS = (
    REPO_ROOT
    / "data/igp24/r24_tower_odd_escape_probe_20260707/r24_tower_odd_escape_candidate_coefficients.txt"
)
DEFAULT_SUMMARY = (
    REPO_ROOT
    / "data/igp24/r24_tower_odd_escape_probe_20260707/r24_tower_odd_escape_summary.json"
)
DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"
DEFAULT_OUTPUT = REPO_ROOT / "data/igp24/r24_tower_odd_escape_sair_accepted_feedback_20260707.json"


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def coefficient_line(exported_coefficients: Iterable[int]) -> str:
    values = [int(value) for value in exported_coefficients]
    if len(values) != 25 or values[-1] != 1:
        raise ValueError("expected 25 exported coefficients ending in leading coefficient 1")
    return ",".join(str(value) for value in values)


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def load_verified_response(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    data = _data(payload)
    if not isinstance(data.get("verifiedPolynomials"), list):
        raise ValueError(f"{path}: expected verifiedPolynomials list")
    return data


def _prior_exact_discs_from_pair(pair: dict[str, Any]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for source_name, item in [("pair_status_primary", pair)] + [
        ("pair_status_alternate", alt)
        for alt in pair.get("accepted_alternates") or []
        if isinstance(alt, dict)
    ]:
        disc = _int_or_none(item.get("exact_nfdisc_abs") or item.get("field_disc_abs"))
        if disc is None and isinstance(item.get("sair_scoring"), dict):
            disc = _int_or_none(item["sair_scoring"].get("field_disc_abs"))
        if disc is not None:
            values.append(
                {
                    "source": source_name,
                    "short_hash": item.get("short_hash"),
                    "canonical_hash": item.get("canonical_hash"),
                    "exact_nfdisc_abs": disc,
                }
            )
    return values


def _prior_exact_discs_from_feedback(path: Path, *, pair_key: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("accepted_rows") or payload.get("rows") or []
    values: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = row.get("label") or row.get("verified_group_label")
        r_value = row.get("r")
        if f"{label}|r={r_value}" != pair_key:
            continue
        disc_source = row.get("discSource") or row.get("disc_source")
        disc = _int_or_none(row.get("fieldDiscAbs") or row.get("field_disc_abs") or row.get("exact_nfdisc_abs"))
        if disc_source == "exact_nfdisc" and disc is not None:
            values.append(
                {
                    "source": str(path),
                    "short_hash": row.get("short_hash") or str(row.get("canonical_hash") or "")[:12],
                    "canonical_hash": row.get("canonical_hash"),
                    "exact_nfdisc_abs": disc,
                }
            )
    return values


def compare_discriminants(
    *,
    pair_status: dict[str, Any],
    pair_key: str,
    new_rows: list[dict[str, Any]],
    prior_feedback_paths: Iterable[Path],
) -> dict[str, Any]:
    current_hashes = {
        str(row.get("canonical_hash"))
        for row in new_rows
        if row.get("canonical_hash")
    }
    pair = next((item for item in pair_status.get("pairs") or [] if item.get("pair_key") == pair_key), {})
    prior_exact = [
        item
        for item in _prior_exact_discs_from_pair(pair)
        if item.get("canonical_hash") not in current_hashes
    ]
    for path in prior_feedback_paths:
        prior_exact.extend(
            item
            for item in _prior_exact_discs_from_feedback(path, pair_key=pair_key)
            if item.get("canonical_hash") not in current_hashes
        )

    new_exact = [
        {
            "row_number": row.get("row_number"),
            "short_hash": row.get("short_hash"),
            "canonical_hash": row.get("canonical_hash"),
            "exact_nfdisc_abs": int(row["field_disc_abs"]),
        }
        for row in new_rows
        if row.get("disc_source") == "exact_nfdisc" and row.get("field_disc_abs") is not None
    ]
    best_old = min(prior_exact, key=lambda item: item["exact_nfdisc_abs"], default=None)
    best_new = min(new_exact, key=lambda item: item["exact_nfdisc_abs"], default=None)
    if best_old is None and best_new is not None:
        status = "no_prior_exact_nfdisc_available"
    elif best_old is not None and best_new is not None and best_new["exact_nfdisc_abs"] < best_old["exact_nfdisc_abs"]:
        status = "new_exact_nfdisc_improves_prior_best"
    elif best_old is not None and best_new is not None:
        status = "new_exact_nfdisc_does_not_improve_prior_best"
    else:
        status = "no_comparable_exact_nfdisc"
    return {
        "pair_key": pair_key,
        "prior_exact_nfdisc_count": len(prior_exact),
        "new_exact_nfdisc_count": len(new_exact),
        "best_prior_exact_nfdisc": best_old,
        "best_new_exact_nfdisc": best_new,
        "comparison_status": status,
        "mixed_disc_rows_treated_conservatively": sum(1 for row in new_rows if row.get("disc_source") == "mixed_disc"),
        "improvement_claimed": status == "new_exact_nfdisc_improves_prior_best",
    }


def build_feedback_artifact(
    *,
    response_path: Path,
    queue_path: Path,
    coefficients_path: Path,
    summary_path: Path,
    pair_status_path: Path,
    prior_feedback_paths: Iterable[Path],
) -> dict[str, Any]:
    response = load_verified_response(response_path)
    queue_rows = read_jsonl(queue_path)
    coefficient_lines = [line.strip() for line in coefficients_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    pair_status = json.loads(pair_status_path.read_text(encoding="utf-8"))
    source_summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}

    accepted_rows: list[dict[str, Any]] = []
    failed_rows = response.get("failedPolynomials") or []
    queued_rows = (response.get("payload") or {}).get("queuedPolynomials") or []
    for verified in sorted(response.get("verifiedPolynomials") or [], key=lambda row: int(row["polynomialIndex"])):
        index = int(verified["polynomialIndex"])
        queue_row = queue_rows[index]
        metadata = queue_row.get("generation_metadata") or {}
        row_number = index + 1
        if row_number <= len(coefficient_lines):
            submission_line = coefficient_lines[index]
        else:
            submission_line = coefficient_line(queue_row["exported_coefficients"])
        label = str(verified["label"])
        r_value = int(verified["r"])
        field_disc = _int_or_none(verified.get("fieldDiscAbs"))
        accepted_rows.append(
            {
                "row_number": row_number,
                "polynomial_index": index,
                "canonical_hash": queue_row.get("canonical_hash"),
                "short_hash": str(queue_row.get("canonical_hash") or "")[:12],
                "submission_line": submission_line,
                "exported_coefficients": queue_row.get("exported_coefficients"),
                "label": label,
                "t": int(verified["t"]),
                "r": r_value,
                "pair_key": f"{label}|r={r_value}",
                "status": verified.get("status"),
                "reason": verified.get("reason"),
                "scoreable": bool(verified.get("scoreable")),
                "scoring_status": verified.get("scoringStatus"),
                "disc_source": verified.get("discSource"),
                "field_disc_abs": field_disc,
                "fieldDiscAbs": str(field_disc) if field_disc is not None else None,
                "in_baseline": bool(verified.get("inBaseline")),
                "baseline_unlocked": bool(verified.get("baselineUnlocked")),
                "coefficient_height": queue_row.get("coefficient_height"),
                "local_validation": {
                    "valid": bool(queue_row.get("valid", True)),
                    "real_root_count": queue_row.get("real_root_count"),
                    "irreducible": queue_row.get("irreducible"),
                    "squarefree": queue_row.get("squarefree"),
                },
                "construction_family": metadata.get("construction_family"),
                "family_key": metadata.get("r24_tower_odd_escape_family_key"),
                "support_gcd": metadata.get("r24_tower_odd_escape_support_gcd"),
                "even_support": metadata.get("r24_tower_odd_escape_even_support_after_perturbation"),
                "odd_support_exponents": metadata.get("r24_tower_odd_escape_odd_support_exponents"),
                "odd_perturbations": metadata.get("r24_tower_odd_escape_odd_perturbations"),
                "tower_odd_escape_metadata": {
                    "mode": metadata.get("r24_tower_odd_escape_mode"),
                    "inner_parameter_s": metadata.get("r24_tower_odd_escape_inner_parameter_s"),
                    "outer_four_real_preimage_levels": metadata.get(
                        "r24_tower_odd_escape_outer_four_real_preimage_levels"
                    ),
                    "anti_basin_features": metadata.get("anti_basin_features"),
                    "decomposition_degree_pattern": metadata.get("decomposition_degree_pattern"),
                    "exact_composition_after_perturbation": metadata.get(
                        "r24_tower_odd_escape_exact_composition_after_perturbation"
                    ),
                },
            }
        )

    label_counts = Counter(row["label"] for row in accepted_rows)
    pair_counts = Counter(row["pair_key"] for row in accepted_rows)
    disc_source_counts = Counter(str(row.get("disc_source")) for row in accepted_rows)
    discriminant_comparison = compare_discriminants(
        pair_status=pair_status,
        pair_key="24T25000|r=24",
        new_rows=accepted_rows,
        prior_feedback_paths=prior_feedback_paths,
    )
    return {
        "schema_version": 1,
        "record_type": "igp24_sair_accepted_label_feedback",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Verified SAIR feedback for the r24 tower odd-escape anti-basin probe.",
        "tool": "scripts/igp24_r24_odd_escape_feedback.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "submission_id": response.get("submissionId"),
        "submitted_at": response.get("createdAt"),
        "updated_at": response.get("updatedAt"),
        "competition_id": response.get("competitionId"),
        "source_response_json": repo_relative(response_path),
        "source_queue_jsonl": repo_relative(queue_path),
        "source_coefficients_txt": repo_relative(coefficients_path),
        "source_summary_json": repo_relative(summary_path),
        "source_summary": {
            "valid_r24_candidates": source_summary.get("valid_r24_candidates"),
            "selected_rows": source_summary.get("selected_rows"),
            "anti_basin_constraints_satisfied": source_summary.get("anti_basin_constraints_satisfied"),
        },
        "safety": {
            "api_key_recorded": False,
            "local_file_join_only": True,
            "automatic_submission": False,
            "magma": False,
            "pari": False,
            "gpu_training": False,
        },
        "accepted_rows": accepted_rows,
        "failed_rows": failed_rows,
        "queued_rows": queued_rows,
        "summary": {
            "accepted_rows": len(accepted_rows),
            "failed_rows": len(failed_rows),
            "queued_rows": len(queued_rows),
            "label_counts": dict(label_counts),
            "pair_counts": dict(pair_counts),
            "exact_nfdisc_rows": disc_source_counts.get("exact_nfdisc", 0),
            "mixed_disc_rows": disc_source_counts.get("mixed_disc", 0),
            "disc_source_counts": dict(disc_source_counts),
            "all_scoreable": all(row.get("scoreable") is True for row in accepted_rows),
            "scoreable_rows": sum(1 for row in accepted_rows if row.get("scoreable") is True),
            "in_baseline_rows": sum(1 for row in accepted_rows if row.get("in_baseline") is True),
            "accepted_pair_keys": sorted(pair_counts),
            "interpretation": (
                "Odd support escaped the exact even tower basin, but all verified rows collapsed "
                "to generic 24T25000|r=24."
            ),
        },
        "discriminant_comparison": discriminant_comparison,
        "next_lane_decision": {
            "submit_more_nearby_r24_6x4_towers": False,
            "reason": (
                "Exact even 6x4 towers landed in 24T23883/24T24651, while odd-escaped "
                "6x4 towers landed in generic 24T25000. Next work should use an alternate "
                "composition pattern such as 8x3 or 3x8, or a non-quadratic r20/r16 seed."
            ),
        },
    }


def update_pair_status_with_alternates(
    pair_status: dict[str, Any],
    feedback: dict[str, Any],
    *,
    feedback_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pair_key = "24T25000|r=24"
    pair = next((item for item in pair_status.get("pairs") or [] if item.get("pair_key") == pair_key), None)
    if pair is None:
        return pair_status, {
            "pair_status_updated": False,
            "reason": "pair_not_found",
            "pair_key": pair_key,
            "alternates_added": 0,
        }
    alternates = pair.setdefault("accepted_alternates", [])
    normalized_sources = 0
    for alternate in alternates:
        if isinstance(alternate, dict) and alternate.get("source"):
            old_source = str(alternate["source"])
            new_source = repo_relative(Path(old_source))
            if new_source != old_source:
                normalized_sources += 1
            alternate["source"] = new_source
    existing_hashes = {
        item.get("canonical_hash")
        for item in alternates
        if isinstance(item, dict) and item.get("canonical_hash")
    }
    if pair.get("canonical_hash"):
        existing_hashes.add(pair["canonical_hash"])
    added = 0
    already_present = 0
    for row in feedback.get("accepted_rows") or []:
        canonical_hash = row.get("canonical_hash")
        if not canonical_hash:
            continue
        if canonical_hash in existing_hashes:
            already_present += 1
            continue
        alternates.append(
            {
                "status": "accepted",
                "score_status": "scoreable",
                "canonical_hash": canonical_hash,
                "short_hash": row.get("short_hash"),
                "source": repo_relative(feedback_path),
                "source_row_number": row.get("row_number"),
                "source_mode": (row.get("tower_odd_escape_metadata") or {}).get("mode"),
                "source_family_key": row.get("family_key"),
                "disc_source": row.get("disc_source"),
                "field_disc_abs": row.get("field_disc_abs"),
                "scoreable": row.get("scoreable"),
                "scoring_status": row.get("scoring_status"),
                "note": (
                    "Scoreable duplicate r=24 pair from the r24 tower odd-escape probe; "
                    "all rows landed as generic 24T25000|r=24. Keep as alternates; "
                    "no discriminant improvement is claimed without a prior exact nfdisc comparison."
                ),
            }
        )
        existing_hashes.add(canonical_hash)
        added += 1
    pair["odd_escape_feedback_note"] = (
        "The r24 tower odd-escape probe added scoreable accepted alternates, but all landed "
        "as generic 24T25000|r=24. This is evidence against more nearby r24 6x4 tower variants."
    )
    return pair_status, {
        "pair_status_updated": added > 0 or normalized_sources > 0,
        "pair_key": pair_key,
        "alternates_added": added,
        "matching_alternates_already_present": already_present,
        "source_paths_normalized": normalized_sources,
        "total_alternates": len(alternates),
        "primary_pair_unchanged": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest r24 tower odd-escape SAIR feedback")
    parser.add_argument("--response_json", type=Path, default=DEFAULT_RESPONSE)
    parser.add_argument("--queue_jsonl", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--coefficients_txt", type=Path, default=DEFAULT_COEFFS)
    parser.add_argument("--summary_json", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--output_json", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--update_pair_status", action="store_true")
    parser.add_argument("--prior_feedback_json", type=Path, action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    default_prior = [
        path
        for path in sorted((REPO_ROOT / "data/igp24").glob("*accepted_feedback*.json"))
        if path.resolve() != args.output_json.resolve()
    ]
    prior_paths = args.prior_feedback_json or default_prior
    feedback = build_feedback_artifact(
        response_path=args.response_json,
        queue_path=args.queue_jsonl,
        coefficients_path=args.coefficients_txt,
        summary_path=args.summary_json,
        pair_status_path=args.pair_status_json,
        prior_feedback_paths=prior_paths,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    feedback["output_json"] = repo_relative(args.output_json)
    pair_update: dict[str, Any] = {"pair_status_updated": False, "reason": "update_pair_status_not_requested"}
    if args.update_pair_status:
        pair_status = json.loads(args.pair_status_json.read_text(encoding="utf-8"))
        pair_status, pair_update = update_pair_status_with_alternates(
            pair_status,
            feedback,
            feedback_path=args.output_json,
        )
        feedback["pair_status_update"] = pair_update
        args.pair_status_json.write_text(json.dumps(pair_status, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    else:
        feedback["pair_status_update"] = pair_update
    args.output_json.write_text(json.dumps(feedback, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"accepted_rows\t{feedback['summary']['accepted_rows']}")
    print(f"label_counts\t{json.dumps(feedback['summary']['label_counts'], sort_keys=True)}")
    print(f"disc_source_counts\t{json.dumps(feedback['summary']['disc_source_counts'], sort_keys=True)}")
    print(f"comparison_status\t{feedback['discriminant_comparison']['comparison_status']}")
    print(f"pair_status_update\t{json.dumps(feedback['pair_status_update'], sort_keys=True)}")
    print(f"output_json\t{args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
