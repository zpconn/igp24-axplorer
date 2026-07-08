#!/usr/bin/env python3
"""Ingest SAIR feedback for anti-basin planner packets."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_anti_basin_planner import DEFAULT_AVOID_LABELS, candidate_features, read_jsonl  # noqa: E402
from scripts.igp24_r16_diversity_probe import coefficient_line  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402


DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "data/igp24/anti_basin_steering_20260707/anti_basin_sair_accepted_feedback_20260707.json"


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


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


def load_status_response(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    data = _data(payload)
    if not isinstance(data.get("verifiedPolynomials"), list):
        raise ValueError(f"{path}: expected verifiedPolynomials list")
    return data


def build_feedback(
    *,
    status_response_path: Path,
    selected_jsonl_path: Path,
    output_json_path: Path,
) -> dict[str, Any]:
    response = load_status_response(status_response_path)
    selected_rows = read_jsonl(selected_jsonl_path)
    selected_by_index = {index: row for index, row in enumerate(selected_rows)}
    accepted_rows: list[dict[str, Any]] = []
    for verified in sorted(response.get("verifiedPolynomials") or [], key=lambda row: int(row["polynomialIndex"])):
        index = int(verified["polynomialIndex"])
        selected = selected_by_index[index]
        metadata = selected.get("generation_metadata") or {}
        features = selected.get("anti_basin_features") or candidate_features(selected)
        exported = selected.get("exported_coefficients")
        label = str(verified["label"])
        r_value = int(verified["r"])
        field_disc = _int_or_none(verified.get("fieldDiscAbs"))
        accepted_rows.append(
            {
                "row_number": index + 1,
                "polynomial_index": index,
                "canonical_hash": selected.get("canonical_hash"),
                "short_hash": str(selected.get("canonical_hash") or "")[:12],
                "submission_line": coefficient_line(exported) if isinstance(exported, list) else None,
                "exported_coefficients": exported,
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
                "coefficient_height": selected.get("coefficient_height"),
                "real_root_count": selected.get("real_root_count"),
                "irreducible": selected.get("irreducible"),
                "squarefree": selected.get("squarefree"),
                "construction_family": metadata.get("construction_family") or features.get("construction_family"),
                "decomposition_pattern": metadata.get("decomposition_degree_pattern") or features.get("decomposition_pattern"),
                "template_family_id": metadata.get("template_family_id") or features.get("template_family_id"),
                "basin_fingerprint": metadata.get("basin_fingerprint") or features.get("basin_fingerprint"),
                "family_key": metadata.get("alt_composition_family_key") or features.get("family_key"),
                "perturbation_mode": metadata.get("alt_perturbation_mode") or features.get("perturbation_mode"),
                "support_gcd": metadata.get("alt_support_gcd") or features.get("support_gcd"),
                "even_support": metadata.get("alt_even_support") if metadata.get("alt_even_support") is not None else features.get("even_support"),
                "odd_support_exponents": metadata.get("alt_odd_support_exponents") or features.get("odd_support_exponents"),
                "mod_p_pattern_signature": features.get("mod_p_pattern_signature"),
                "anti_basin_score": selected.get("anti_basin_score"),
                "anti_basin_classification": selected.get("anti_basin_classification"),
                "anti_basin_risk_reasons": selected.get("anti_basin_risk_reasons") or [],
                "anti_basin_score_explanation": selected.get("anti_basin_score_explanation") or [],
                "alt_metadata": {
                    "perturbation_mode": metadata.get("alt_perturbation_mode"),
                    "inner_parameter_s": metadata.get("alt_inner_parameter_s"),
                    "outer_three_real_levels": metadata.get("alt_outer_three_real_levels"),
                    "outer_perturbations": metadata.get("alt_outer_perturbations"),
                    "anti_basin_features": metadata.get("anti_basin_features"),
                },
            }
        )

    failed_rows = response.get("failedPolynomials") or []
    queued_rows = (response.get("payload") or {}).get("queuedPolynomials") or []
    label_counts = Counter(row["label"] for row in accepted_rows)
    pair_counts = Counter(row["pair_key"] for row in accepted_rows)
    disc_source_counts = Counter(str(row.get("disc_source")) for row in accepted_rows)
    known_hits = sorted(label for label in label_counts if label in DEFAULT_AVOID_LABELS)
    escaped = sorted(label for label in label_counts if label not in DEFAULT_AVOID_LABELS)
    feedback = {
        "schema_version": 1,
        "record_type": "igp24_sair_accepted_label_feedback",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Verified SAIR feedback for the anti-basin nonconstant alternate-composition packet.",
        "tool": "scripts/igp24_anti_basin_feedback.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "submission_id": response.get("submissionId"),
        "submitted_at": response.get("createdAt"),
        "updated_at": response.get("updatedAt"),
        "competition_id": response.get("competitionId"),
        "source_response_json": repo_relative(status_response_path),
        "source_selected_jsonl": repo_relative(selected_jsonl_path),
        "safety": {
            "api_key_recorded": False,
            "local_file_join_only": True,
            "automatic_submission": False,
            "gpu_training": False,
            "magma": False,
            "pari": False,
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
            "disc_source_counts": dict(disc_source_counts),
            "exact_nfdisc_rows": disc_source_counts.get("exact_nfdisc", 0),
            "mixed_disc_rows": disc_source_counts.get("mixed_disc", 0),
            "pending_disc_rows": disc_source_counts.get("None", 0) + disc_source_counts.get("null", 0),
            "all_scoreable": all(row.get("scoreable") is True for row in accepted_rows) if accepted_rows else False,
            "scoreable_rows": sum(1 for row in accepted_rows if row.get("scoreable") is True),
            "known_basin_labels_hit": known_hits,
            "escaped_known_basin_labels": escaped,
            "escaped_known_basins": bool(escaped),
            "accepted_pair_keys": sorted(pair_counts),
            "interpretation": (
                "The anti-basin packet escaped the tracked known basin labels."
                if escaped
                else "The anti-basin packet did not escape the tracked known basin labels."
            ),
        },
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(feedback, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return feedback


def _existing_hashes(pair: dict[str, Any]) -> set[str]:
    hashes = {str(pair.get("canonical_hash"))} if pair.get("canonical_hash") else set()
    for alternate in pair.get("accepted_alternates") or []:
        if isinstance(alternate, dict) and alternate.get("canonical_hash"):
            hashes.add(str(alternate["canonical_hash"]))
    return hashes


def _existing_record_for_hash(pair: dict[str, Any], canonical_hash: Any) -> dict[str, Any] | None:
    if not canonical_hash:
        return None
    hash_text = str(canonical_hash)
    if str(pair.get("canonical_hash") or "") == hash_text:
        return pair
    for alternate in pair.get("accepted_alternates") or []:
        if isinstance(alternate, dict) and str(alternate.get("canonical_hash") or "") == hash_text:
            return alternate
    return None


def _merge_missing_metadata(target: dict[str, Any], row: dict[str, Any]) -> int:
    updates = 0
    for key in ("template_family_id", "basin_fingerprint", "source_family_key", "perturbation_mode"):
        value = row.get("family_key") if key == "source_family_key" else row.get(key)
        if value is not None and not target.get(key):
            target[key] = value
            updates += 1
    return updates


def update_pair_status(
    pair_status: dict[str, Any],
    feedback: dict[str, Any],
    *,
    feedback_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pairs = pair_status.setdefault("pairs", [])
    by_key = {pair.get("pair_key"): pair for pair in pairs if isinstance(pair, dict)}
    added_pairs = 0
    alternates_added = 0
    already_present = 0
    metadata_updates = 0
    source = repo_relative(feedback_path)
    for row in feedback.get("accepted_rows") or []:
        pair_key = row["pair_key"]
        pair = by_key.get(pair_key)
        if pair is None:
            pair = {
                "pair_key": pair_key,
                "label": row["label"],
                "r": row["r"],
                "status": "accepted",
                "canonical_hash": row.get("canonical_hash"),
                "short_hash": row.get("short_hash"),
                "score_status": row.get("scoring_status"),
                "accepted_reported_by_sair": True,
                "source": source,
                "source_row_number": row.get("row_number"),
                "construction_family": row.get("construction_family"),
                "decomposition_pattern": row.get("decomposition_pattern"),
                "template_family_id": row.get("template_family_id"),
                "basin_fingerprint": row.get("basin_fingerprint"),
                "family_key": row.get("family_key"),
                "anti_basin_score": row.get("anti_basin_score"),
                "anti_basin_classification": row.get("anti_basin_classification"),
                "sair_scoring": {
                    "scoreable": row.get("scoreable"),
                    "scoring_status": row.get("scoring_status"),
                    "disc_source": row.get("disc_source"),
                    "field_disc_abs": row.get("field_disc_abs"),
                    "in_baseline": row.get("in_baseline"),
                    "baseline_unlocked": row.get("baseline_unlocked"),
                },
                "note": "New pair from the anti-basin planner packet; scoring/discriminant fields are SAIR-reported when present.",
            }
            if row.get("disc_source") == "exact_nfdisc" and row.get("field_disc_abs") is not None:
                pair["exact_nfdisc_abs"] = row["field_disc_abs"]
            pairs.append(pair)
            by_key[pair_key] = pair
            added_pairs += 1
            continue

        existing_record = _existing_record_for_hash(pair, row.get("canonical_hash"))
        if existing_record is not None:
            metadata_updates += _merge_missing_metadata(existing_record, row)
            already_present += 1
            continue
        pair.setdefault("accepted_alternates", []).append(
            {
                "status": "accepted",
                "score_status": row.get("scoring_status"),
                "canonical_hash": row.get("canonical_hash"),
                "short_hash": row.get("short_hash"),
                "source": source,
                "source_row_number": row.get("row_number"),
                "source_family_key": row.get("family_key"),
                "template_family_id": row.get("template_family_id"),
                "basin_fingerprint": row.get("basin_fingerprint"),
                "perturbation_mode": row.get("perturbation_mode"),
                "anti_basin_score": row.get("anti_basin_score"),
                "anti_basin_classification": row.get("anti_basin_classification"),
                "disc_source": row.get("disc_source"),
                "field_disc_abs": row.get("field_disc_abs"),
                "scoreable": row.get("scoreable"),
                "scoring_status": row.get("scoring_status"),
                "note": "Accepted alternate from the anti-basin planner packet; primary representative unchanged.",
            }
        )
        alternates_added += 1

    pair_status.setdefault("notes", []).append(
        "The anti-basin planner packet was ingested conservatively: new pair keys were added, repeated pair keys were appended only as alternates, and no representative was replaced."
    )
    return pair_status, {
        "pair_status_updated": added_pairs > 0 or alternates_added > 0 or metadata_updates > 0,
        "new_pairs_added": added_pairs,
        "alternates_added": alternates_added,
        "already_present": already_present,
        "metadata_updates": metadata_updates,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest SAIR feedback for an anti-basin planner packet")
    parser.add_argument("--status_response_json", type=Path, required=True)
    parser.add_argument("--selected_jsonl", type=Path, required=True)
    parser.add_argument("--output_json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--update_pair_status", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    feedback = build_feedback(
        status_response_path=args.status_response_json,
        selected_jsonl_path=args.selected_jsonl,
        output_json_path=args.output_json,
    )
    pair_update = {"pair_status_updated": False, "reason": "update_pair_status_not_requested"}
    if args.update_pair_status:
        pair_status = json.loads(args.pair_status_json.read_text(encoding="utf-8"))
        pair_status, pair_update = update_pair_status(pair_status, feedback, feedback_path=args.output_json)
        args.pair_status_json.write_text(json.dumps(pair_status, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    feedback["pair_status_update"] = pair_update
    args.output_json.write_text(json.dumps(feedback, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"accepted_rows\t{feedback['summary']['accepted_rows']}")
    print(f"queued_rows\t{feedback['summary']['queued_rows']}")
    print(f"label_counts\t{json.dumps(feedback['summary']['label_counts'], sort_keys=True)}")
    print(f"escaped_known_basins\t{feedback['summary']['escaped_known_basins']}")
    print(f"pair_status_update\t{json.dumps(pair_update, sort_keys=True)}")
    print(f"output_json\t{repo_relative(args.output_json)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
