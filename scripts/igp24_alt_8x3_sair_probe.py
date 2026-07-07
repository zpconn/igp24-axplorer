#!/usr/bin/env python3
"""Prepare and ingest the reviewed 8x3 SAIR verification probe.

This helper is intentionally file/local except for the separate
``scripts/igp24_sair_api.py`` submission command. It builds a reviewed
coefficient-only packet from the alternate-composition queue, records a saved
submit response, and joins a saved SAIR status response back to local metadata.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_r16_diversity_probe import coefficient_line  # noqa: E402
from scripts.igp24_shortlist import get_source_commit, read_jsonl  # noqa: E402


DEFAULT_SOURCE_QUEUE = (
    REPO_ROOT / "data/igp24/alt_composition_probe_20260707/alt_composition_candidate_queue.jsonl"
)
DEFAULT_SOURCE_SUMMARY = REPO_ROOT / "data/igp24/alt_composition_probe_20260707/alt_composition_summary.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/igp24/alt_composition_8x3_sair_probe_20260707"
DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"

PACKET_JSONL = "alt_composition_8x3_sair_probe_subset.jsonl"
COEFFICIENTS_TXT = "alt_composition_8x3_sair_probe_coefficients.txt"
HASHES_TXT = "alt_composition_8x3_sair_probe_hashes.txt"
SUMMARY_JSON = "alt_composition_8x3_sair_probe_summary.json"
REPORT_MD = "alt_composition_8x3_sair_probe_report.md"
ACCEPTED_FEEDBACK_JSON = "alt_composition_8x3_sair_accepted_feedback_20260707.json"

KNOWN_BASIN_LABELS = {"24T25000", "24T23883", "24T24651", "24T24979", "24T24970"}


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


def support_gcd(exported_coefficients: Iterable[int]) -> int | None:
    gcd_value = 0
    for exponent, coefficient in enumerate(exported_coefficients):
        if exponent >= 24:
            continue
        if int(coefficient) != 0 and exponent > 0:
            gcd_value = math.gcd(gcd_value, exponent)
    return gcd_value or None


def validate_exported_coefficients(exported: Iterable[int]) -> list[int]:
    values = [int(value) for value in exported]
    if len(values) != 25:
        raise ValueError(f"expected 25 exported coefficients, got {len(values)}")
    if values[0] == 0:
        raise ValueError("constant coefficient must be nonzero")
    if values[-1] != 1:
        raise ValueError("leading coefficient must be 1")
    gcd_value = 0
    for value in values:
        gcd_value = math.gcd(gcd_value, abs(value))
    if gcd_value != 1:
        raise ValueError(f"coefficient gcd must be 1, got {gcd_value}")
    return values


def selected_source_rows(queue_path: Path, *, limit: int) -> list[dict[str, Any]]:
    rows = read_jsonl(queue_path)
    filtered = []
    for row in rows:
        metadata = row.get("generation_metadata") or {}
        if metadata.get("decomposition_degree_pattern") != "8x3":
            continue
        if int(row.get("real_root_count") or -1) != 24:
            continue
        filtered.append(row)
    filtered.sort(key=lambda row: int(row.get("alt_composition_queue_rank") or 10**9))
    if len(filtered) < int(limit):
        raise ValueError(f"only found {len(filtered)} reviewed 8x3 r=24 rows, need {limit}")
    return filtered[: int(limit)]


def packet_row(source: dict[str, Any], *, probe_row_number: int) -> dict[str, Any]:
    metadata = source.get("generation_metadata") or {}
    exported = validate_exported_coefficients(source["exported_coefficients"])
    support = support_gcd(exported)
    if support != 1:
        raise ValueError(f"source rank {source.get('alt_composition_queue_rank')} has support gcd {support}")
    if metadata.get("alt_even_support") is not False:
        raise ValueError(f"source rank {source.get('alt_composition_queue_rank')} still looks even-support")
    return {
        "probe_row_number": int(probe_row_number),
        "source_queue_rank": int(source.get("alt_composition_queue_rank")),
        "canonical_hash": source.get("canonical_hash"),
        "short_hash": str(source.get("canonical_hash") or "")[:12],
        "submission_line": coefficient_line(exported),
        "exported_coefficients": exported,
        "coefficient_height": source.get("coefficient_height"),
        "real_root_count": source.get("real_root_count"),
        "irreducible": source.get("irreducible"),
        "squarefree": source.get("squarefree"),
        "log_abs_discriminant": source.get("log_abs_discriminant"),
        "mod_p_factorization_degree_patterns": source.get("mod_p_factorization_degree_patterns"),
        "generation_metadata": metadata,
        "structural_gates_satisfied": [
            "decomposition_degree_pattern_8x3",
            "not_6x4",
            "not_g_x_squared_even_support",
            "not_odd_escaped_6x4",
            "support_gcd_one",
            "exact_local_r24",
            "irreducible_squarefree_local_check",
        ],
    }


def build_packet(
    *,
    source_queue_path: Path,
    source_summary_path: Path,
    output_dir: Path,
    limit: int,
) -> dict[str, Any]:
    source_summary = json.loads(source_summary_path.read_text(encoding="utf-8"))
    rows = [
        packet_row(row, probe_row_number=index)
        for index, row in enumerate(selected_source_rows(source_queue_path, limit=limit), start=1)
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_path = output_dir / PACKET_JSONL
    coeffs_path = output_dir / COEFFICIENTS_TXT
    hashes_path = output_dir / HASHES_TXT
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    with packet_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    coeffs_path.write_text("".join(f"{row['submission_line']}\n" for row in rows), encoding="utf-8")
    hashes_path.write_text(
        "".join(f"{row['probe_row_number']}\t{row['source_queue_rank']}\t{row['canonical_hash']}\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "schema_version": 1,
        "record_type": "igp24_alt_8x3_sair_probe_packet",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_alt_8x3_sair_probe.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "source_queue_jsonl": repo_relative(source_queue_path),
        "source_summary_json": repo_relative(source_summary_path),
        "source_summary": {
            "trials_attempted": source_summary.get("trials_attempted"),
            "valid_candidate_count": source_summary.get("valid_candidate_count"),
            "selected_rows": source_summary.get("selected_rows"),
            "queue_status": source_summary.get("queue_status"),
        },
        "safety": {
            "cpu_only": True,
            "gpu_training": False,
            "model_training": False,
            "sair_api": False,
            "automatic_submission": False,
            "magma": False,
            "pari": False,
            "network": False,
            "api_key_recorded": False,
        },
        "selection": {
            "strategy": "first_reviewed_8x3_rows",
            "requested_rows": int(limit),
            "selected_rows": len(rows),
            "source_queue_ranks": [row["source_queue_rank"] for row in rows],
            "short_hashes": [row["short_hash"] for row in rows],
        },
        "local_validation_summary": {
            "all_exact_local_r24": all(row.get("real_root_count") == 24 for row in rows),
            "all_irreducible": all(row.get("irreducible") is True for row in rows),
            "all_squarefree": all(row.get("squarefree") is True for row in rows),
            "all_support_gcd_one": all(support_gcd(row["exported_coefficients"]) == 1 for row in rows),
            "all_non_even_support": all((row.get("generation_metadata") or {}).get("alt_even_support") is False for row in rows),
            "coefficient_height_min": min(int(row["coefficient_height"]) for row in rows),
            "coefficient_height_max": max(int(row["coefficient_height"]) for row in rows),
        },
        "known_basins_avoided_by_structure": [
            "exact_even_6x4_tower_24T23883_24T24651",
            "odd_escaped_6x4_tower_24T25000",
            "product_quadratic_low_odd_perturbation_24T25000",
            "exact_g_x_squared_even_support",
        ],
        "submission": {
            "dry_run_response_json": None,
            "submit_response_json": None,
            "submission_id": None,
            "submitted_at": None,
            "status": "not_submitted_by_packet_builder",
        },
        "output_files": {
            "packet_jsonl": repo_relative(packet_path),
            "coefficients_txt": repo_relative(coeffs_path),
            "hashes_txt": repo_relative(hashes_path),
            "summary_json": repo_relative(summary_path),
            "report_md": repo_relative(report_path),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(build_packet_report(summary, rows), encoding="utf-8")
    return summary


def build_packet_report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# IGP24 8x3 SAIR Probe Packet",
        "",
        "Small reviewed verification packet for the alternate-composition `8x3|r=24` lane.",
        "",
        "- This is `8x3`, not `6x4`.",
        "- This is not exact even `g(x^2)` support.",
        "- This is not the odd-escaped `6x4` tower lane.",
        "- This is a small verification probe, not a widening run.",
        "- The packet builder did not call SAIR, Magma, PARI, the network, GPU, or training code.",
        "",
        f"- Selected rows: {summary['selection']['selected_rows']}",
        f"- Source ranks: `{summary['selection']['source_queue_ranks']}`",
        f"- Height range: {summary['local_validation_summary']['coefficient_height_min']} to {summary['local_validation_summary']['coefficient_height_max']}",
        "",
        "| row | source rank | hash | family | height |",
        "| ---: | ---: | --- | --- | ---: |",
    ]
    for row in rows:
        metadata = row.get("generation_metadata") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["probe_row_number"]),
                    str(row["source_queue_rank"]),
                    f"`{row['short_hash']}`",
                    f"`{metadata.get('alt_composition_family_key')}`",
                    str(row.get("coefficient_height")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def record_submit_response(*, output_dir: Path, submit_response_path: Path, dry_run_response_path: Path | None) -> dict[str, Any]:
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    packet_path = output_dir / PACKET_JSONL
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    payload = _data(json.loads(submit_response_path.read_text(encoding="utf-8")))
    submission_id = payload.get("submissionId") or payload.get("id")
    summary["submission"] = {
        "dry_run_response_json": repo_relative(dry_run_response_path) if dry_run_response_path else None,
        "submit_response_json": repo_relative(submit_response_path),
        "submission_id": submission_id,
        "submitted_at": payload.get("createdAt") or payload.get("submittedAt"),
        "status": "submitted",
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = read_jsonl(packet_path)
    report = build_packet_report(summary, rows)
    report += f"\n## SAIR Submission\n\n- Submission id: `{submission_id}`\n- Submit response: `{repo_relative(submit_response_path)}`\n"
    if dry_run_response_path:
        report += f"- Dry-run response: `{repo_relative(dry_run_response_path)}`\n"
    report_path.write_text(report, encoding="utf-8")
    return summary


def load_status_response(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    data = _data(payload)
    if not isinstance(data.get("verifiedPolynomials"), list):
        raise ValueError(f"{path}: expected verifiedPolynomials list")
    return data


def build_feedback(
    *,
    status_response_path: Path,
    packet_jsonl_path: Path,
    output_json_path: Path,
) -> dict[str, Any]:
    response = load_status_response(status_response_path)
    packet_rows = read_jsonl(packet_jsonl_path)
    packet_by_index = {index: row for index, row in enumerate(packet_rows)}
    accepted_rows: list[dict[str, Any]] = []
    for verified in sorted(response.get("verifiedPolynomials") or [], key=lambda row: int(row["polynomialIndex"])):
        index = int(verified["polynomialIndex"])
        packet = packet_by_index[index]
        metadata = packet.get("generation_metadata") or {}
        label = str(verified["label"])
        r_value = int(verified["r"])
        field_disc = _int_or_none(verified.get("fieldDiscAbs"))
        accepted_rows.append(
            {
                "row_number": int(index) + 1,
                "polynomial_index": index,
                "source_queue_rank": packet.get("source_queue_rank"),
                "canonical_hash": packet.get("canonical_hash"),
                "short_hash": packet.get("short_hash"),
                "submission_line": packet.get("submission_line"),
                "exported_coefficients": packet.get("exported_coefficients"),
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
                "coefficient_height": packet.get("coefficient_height"),
                "real_root_count": packet.get("real_root_count"),
                "irreducible": packet.get("irreducible"),
                "squarefree": packet.get("squarefree"),
                "construction_family": metadata.get("construction_family"),
                "decomposition_pattern": metadata.get("decomposition_degree_pattern"),
                "family_key": metadata.get("alt_composition_family_key"),
                "support_gcd": metadata.get("alt_support_gcd"),
                "even_support": metadata.get("alt_even_support"),
                "odd_support_exponents": metadata.get("alt_odd_support_exponents"),
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
    escaped_known_basins = sorted(label for label in label_counts if label not in KNOWN_BASIN_LABELS)
    feedback = {
        "schema_version": 1,
        "record_type": "igp24_sair_accepted_label_feedback",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "Verified SAIR feedback for the reviewed alternate-composition 8x3 probe.",
        "tool": "scripts/igp24_alt_8x3_sair_probe.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "submission_id": response.get("submissionId"),
        "submitted_at": response.get("createdAt"),
        "updated_at": response.get("updatedAt"),
        "competition_id": response.get("competitionId"),
        "source_response_json": repo_relative(status_response_path),
        "source_packet_jsonl": repo_relative(packet_jsonl_path),
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
            "known_basin_labels_hit": sorted(label for label in label_counts if label in KNOWN_BASIN_LABELS),
            "escaped_known_basin_labels": escaped_known_basins,
            "escaped_known_basins": bool(escaped_known_basins),
            "accepted_pair_keys": sorted(pair_counts),
            "interpretation": (
                "The reviewed 8x3 probe escaped the known crowded basins."
                if escaped_known_basins
                else "The reviewed 8x3 probe did not escape the tracked known basin labels."
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


def update_pair_status(pair_status: dict[str, Any], feedback: dict[str, Any], *, feedback_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    pairs = pair_status.setdefault("pairs", [])
    by_key = {pair.get("pair_key"): pair for pair in pairs if isinstance(pair, dict)}
    added_pairs = 0
    alternates_added = 0
    already_present = 0
    for row in feedback.get("accepted_rows") or []:
        pair_key = row["pair_key"]
        pair = by_key.get(pair_key)
        source = repo_relative(feedback_path)
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
                "family_key": row.get("family_key"),
                "sair_scoring": {
                    "scoreable": row.get("scoreable"),
                    "scoring_status": row.get("scoring_status"),
                    "disc_source": row.get("disc_source"),
                    "field_disc_abs": row.get("field_disc_abs"),
                    "in_baseline": row.get("in_baseline"),
                    "baseline_unlocked": row.get("baseline_unlocked"),
                },
                "note": "New pair from the reviewed alternate-composition 8x3 SAIR probe; scoring/discriminant fields are SAIR-reported when present.",
            }
            if row.get("disc_source") == "exact_nfdisc" and row.get("field_disc_abs") is not None:
                pair["exact_nfdisc_abs"] = row["field_disc_abs"]
            pairs.append(pair)
            by_key[pair_key] = pair
            added_pairs += 1
            continue
        hashes = _existing_hashes(pair)
        if row.get("canonical_hash") in hashes:
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
                "disc_source": row.get("disc_source"),
                "field_disc_abs": row.get("field_disc_abs"),
                "scoreable": row.get("scoreable"),
                "scoring_status": row.get("scoring_status"),
                "note": "Accepted duplicate/alternate from the reviewed alternate-composition 8x3 SAIR probe; primary representative unchanged.",
            }
        )
        alternates_added += 1
    pair_status.setdefault("notes", []).append(
        "The reviewed alternate-composition 8x3 SAIR probe was ingested conservatively: new pair keys were added, repeated pair keys were appended only as alternates, and no representative was replaced."
    )
    return pair_status, {
        "pair_status_updated": added_pairs > 0 or alternates_added > 0,
        "new_pairs_added": added_pairs,
        "alternates_added": alternates_added,
        "already_present": already_present,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and ingest the reviewed 8x3 SAIR probe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    packet = subparsers.add_parser("build-packet")
    packet.add_argument("--source_queue_jsonl", type=Path, default=DEFAULT_SOURCE_QUEUE)
    packet.add_argument("--source_summary_json", type=Path, default=DEFAULT_SOURCE_SUMMARY)
    packet.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    packet.add_argument("--limit", type=int, default=8)

    record = subparsers.add_parser("record-submit-response")
    record.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    record.add_argument("--submit_response_json", type=Path, required=True)
    record.add_argument("--dry_run_response_json", type=Path)

    ingest = subparsers.add_parser("ingest-response")
    ingest.add_argument("--status_response_json", type=Path, required=True)
    ingest.add_argument("--packet_jsonl", type=Path, default=DEFAULT_OUTPUT_DIR / PACKET_JSONL)
    ingest.add_argument("--output_json", type=Path, default=DEFAULT_OUTPUT_DIR / ACCEPTED_FEEDBACK_JSON)
    ingest.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    ingest.add_argument("--update_pair_status", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "build-packet":
        summary = build_packet(
            source_queue_path=args.source_queue_jsonl,
            source_summary_path=args.source_summary_json,
            output_dir=args.output_dir,
            limit=args.limit,
        )
        print(f"selected_rows\t{summary['selection']['selected_rows']}")
        print(f"coefficients_txt\t{summary['output_files']['coefficients_txt']}")
        print(f"summary_json\t{summary['output_files']['summary_json']}")
        return 0
    if args.command == "record-submit-response":
        summary = record_submit_response(
            output_dir=args.output_dir,
            submit_response_path=args.submit_response_json,
            dry_run_response_path=args.dry_run_response_json,
        )
        print(f"submission_id\t{summary['submission']['submission_id']}")
        print(f"summary_json\t{repo_relative(args.output_dir / SUMMARY_JSON)}")
        return 0
    if args.command == "ingest-response":
        feedback = build_feedback(
            status_response_path=args.status_response_json,
            packet_jsonl_path=args.packet_jsonl,
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
    raise AssertionError(f"unhandled command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
