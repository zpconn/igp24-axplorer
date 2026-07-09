#!/usr/bin/env python3
"""Build a local review gate for group-compatible IGP24 packets.

This helper is deliberately conservative. It joins packet-optimizer rows with
their coefficient-only file, reruns exact local validation, performs a local
SAIR dry-run formatting/body-size check, and writes a review report. It never
performs a live SAIR submission and never reads an API key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.polynomial import score_candidate  # noqa: E402
from src.igp24.verifiers.sair_api import (  # noqa: E402
    SAIRAPIError,
    SAIRAPIVerifier,
    format_polynomial_line,
    load_polynomial_lines,
    parse_polynomial_line,
)


SUMMARY_JSON = "group_compatible_submission_gate_summary.json"
REPORT_MD = "group_compatible_submission_gate_report.md"
ROWS_JSONL = "group_compatible_submission_gate_rows.jsonl"
COEFFICIENTS_TXT = "group_compatible_submission_gate_coefficients.txt"
SAIR_DRY_RUN_JSON = "group_compatible_submission_gate_sair_local_dry_run.json"

Scorer = Callable[..., tuple[float, Any]]


class GateError(ValueError):
    """Raised when packet inputs are malformed before row-level checks."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_text(lines: Sequence[str]) -> str:
    digest = hashlib.sha256()
    digest.update(("\n".join(lines) + "\n").encode("utf-8"))
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def expected_r(row: dict[str, Any], fallback: int | None) -> int | None:
    features = row.get("features") if isinstance(row.get("features"), dict) else {}
    value = features.get("r") if isinstance(features, dict) else None
    if value is None:
        value = fallback
    if value is None:
        return None
    return int(value)


def _bool_attr(value: Any, name: str) -> bool | None:
    raw = getattr(value, name, None)
    if raw is None:
        return None
    return bool(raw)


def _pattern_records(patterns: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for pattern in patterns or []:
        if isinstance(pattern, dict):
            prime = pattern.get("prime")
            degrees = pattern.get("degrees")
        else:
            prime = getattr(pattern, "prime", None)
            degrees = getattr(pattern, "degrees", None)
        if prime is not None and degrees is not None:
            records.append({"prime": int(prime), "degrees": [int(value) for value in degrees]})
    return records


def _default_scorer(
    coefficients24: Sequence[int],
    *,
    target_r: int | None,
    coeff_bound: int,
    prime_limit: int,
    exact_score_timeout: float,
) -> tuple[float, Any]:
    return score_candidate(
        coefficients24,
        coeff_bound=coeff_bound,
        target_r=target_r,
        prime_limit=prime_limit,
        exact_score_timeout=exact_score_timeout,
    )


def local_validation_record(
    *,
    coeffs25: Sequence[int],
    row: dict[str, Any],
    target_r: int | None,
    coeff_bound: int,
    prime_limit: int,
    exact_score_timeout: float,
    scorer: Scorer | None = None,
) -> dict[str, Any]:
    score, analysis = (scorer or _default_scorer)(
        list(coeffs25[:-1]),
        target_r=target_r,
        coeff_bound=coeff_bound,
        prime_limit=prime_limit,
        exact_score_timeout=exact_score_timeout,
    )
    observed_r = getattr(analysis, "real_root_count", None)
    canonical_hash = str(getattr(analysis, "canonical_hash", "") or "")
    expected_hash = str(row.get("canonical_hash") or "")
    local_valid = bool(getattr(analysis, "valid", False))
    root_match = bool(target_r is not None and observed_r == target_r)
    return {
        "score": float(score),
        "valid": local_valid,
        "rejection_reason": getattr(analysis, "rejection_reason", None),
        "canonical_hash": canonical_hash,
        "expected_hash": expected_hash,
        "hash_matches_optimizer_row": bool(expected_hash and canonical_hash == expected_hash),
        "real_root_count": observed_r,
        "expected_r": target_r,
        "real_root_count_matches": root_match,
        "irreducible": _bool_attr(analysis, "irreducible"),
        "squarefree": _bool_attr(analysis, "squarefree"),
        "coefficient_height": getattr(analysis, "coefficient_height", None),
        "log_abs_discriminant": getattr(analysis, "log_abs_discriminant", None),
        "sampled_primes": list(getattr(analysis, "sampled_primes", ()) or ()),
        "mod_p_factorization_degree_patterns": _pattern_records(
            getattr(analysis, "mod_p_factorization_degree_patterns", ())
        ),
        "warnings": list(getattr(analysis, "warnings", ()) or ()),
    }


def row_checks(row: dict[str, Any], local: dict[str, Any]) -> dict[str, bool]:
    possible_uncovered = list(row.get("possible_uncovered_pairs") or [])
    possible_low_team = list(row.get("possible_low_team_pairs") or [])
    possible_crowded = list(row.get("possible_crowded_pairs") or [])
    checks = {
        "optimizer_selected_row": int(row.get("optimizer_rank") or 0) > 0,
        "optimizer_eligible": bool(row.get("eligible_for_optimization")),
        "no_optimizer_reject_reasons": not bool(row.get("reject_reasons")),
        "local_valid": bool(local.get("valid")),
        "local_irreducible": local.get("irreducible") is True,
        "local_squarefree": local.get("squarefree") is True,
        "local_r_matches": bool(local.get("real_root_count_matches")),
        "hash_matches_optimizer_row": bool(local.get("hash_matches_optimizer_row")),
        "has_group_compatibility": int(row.get("compatible_label_count") or 0) > 0,
        "has_valuable_compatible_pair": bool(possible_uncovered or possible_low_team),
        "not_crowded_only": not bool(possible_crowded and not possible_uncovered and not possible_low_team),
    }
    return checks


def row_blockers(rank: int, checks: dict[str, bool]) -> list[str]:
    return [f"row_{rank}_{name}" for name, ok in checks.items() if not ok]


def build_gate(
    *,
    selected_jsonl: Path,
    coefficients_txt: Path,
    output_dir: Path,
    target_r: int | None = None,
    coeff_bound: int = 10**18,
    prime_limit: int = 11,
    exact_score_timeout: float = 10.0,
    sair_sync_summary_json: Path | None = None,
    command: list[str] | None = None,
    source_commit: str | None = None,
    scorer: Scorer | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_rows = read_jsonl(selected_jsonl)
    coefficient_lines = load_polynomial_lines(coefficients_txt)
    if len(selected_rows) != len(coefficient_lines):
        raise GateError(
            f"selected row count ({len(selected_rows)}) does not match coefficient line count ({len(coefficient_lines)})"
        )
    if not selected_rows:
        raise GateError("selected packet is empty")

    gate_rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    normalized_lines: list[str] = []
    seen_hashes: set[str] = set()
    duplicate_hashes: set[str] = set()

    for index, (row, line) in enumerate(zip(selected_rows, coefficient_lines, strict=True), start=1):
        coeffs25 = parse_polynomial_line(line, line_number=index)
        normalized = format_polynomial_line(coeffs25, line_number=index)
        normalized_lines.append(normalized)
        if row.get("canonical_hash") in seen_hashes:
            duplicate_hashes.add(str(row.get("canonical_hash")))
        seen_hashes.add(str(row.get("canonical_hash") or ""))
        local = local_validation_record(
            coeffs25=coeffs25,
            row=row,
            target_r=expected_r(row, target_r),
            coeff_bound=coeff_bound,
            prime_limit=prime_limit,
            exact_score_timeout=exact_score_timeout,
            scorer=scorer,
        )
        checks = row_checks(row, local)
        rank = int(row.get("optimizer_rank") or index)
        row_blocker_values = row_blockers(rank, checks)
        blockers.extend(row_blocker_values)
        gate_rows.append(
            {
                "schema_version": 1,
                "record_type": "igp24_group_compatible_submission_gate_row",
                "gate_rank": index,
                "optimizer_rank": row.get("optimizer_rank"),
                "canonical_hash": row.get("canonical_hash"),
                "short_hash": row.get("short_hash"),
                "coefficients": coeffs25,
                "features": row.get("features"),
                "compatible_label_count": row.get("compatible_label_count"),
                "possible_uncovered_pairs": list(row.get("possible_uncovered_pairs") or []),
                "possible_low_team_pairs": list(row.get("possible_low_team_pairs") or []),
                "possible_crowded_pairs": list(row.get("possible_crowded_pairs") or []),
                "maximum_possible_points": row.get("maximum_possible_points"),
                "estimated_expected_points": row.get("estimated_expected_points"),
                "marginal_estimated_points": row.get("marginal_estimated_points"),
                "compatibility_ambiguity_factor": row.get("compatibility_ambiguity_factor"),
                "local_validation": local,
                "checks": checks,
                "blockers": row_blocker_values,
                "review_status": "local_gate_passed_compatibility_only" if not row_blocker_values else "blocked",
            }
        )

    if duplicate_hashes:
        blockers.append("duplicate_hashes_in_packet")

    client = SAIRAPIVerifier(dry_run=True)
    dry_run_payload = client.submit_polynomials(
        normalized_lines,
        description="igp24-axplorer local group-compatible gate; no live submission",
        dry_run=True,
    )
    dry_run_payload = {
        **dry_run_payload,
        "local_only": True,
        "api_key_required": False,
        "network_calls": False,
        "live_submission": False,
    }

    sync_summary: dict[str, Any] | None = None
    if sair_sync_summary_json is not None:
        sync_summary = json.loads(sair_sync_summary_json.read_text(encoding="utf-8"))

    uncovered_pairs = sorted({pair for row in gate_rows for pair in row["possible_uncovered_pairs"]})
    low_team_pairs = sorted({pair for row in gate_rows for pair in row["possible_low_team_pairs"]})
    crowded_pairs = sorted({pair for row in gate_rows for pair in row["possible_crowded_pairs"]})
    local_gate_passed = not blockers and bool(dry_run_payload.get("ok")) and bool(dry_run_payload.get("dry_run"))
    remaining_gates = [
        "compatibility_only_exact_label_unknown",
        "fresh_sair_sync_required_immediately_before_live_submission",
        "explicit_user_approval_required_for_exact_live_packet",
    ]
    if sync_summary and sync_summary.get("sync_status", {}).get("partial_sync") is False:
        remaining_gates[1] = "fresh_sair_sync_present_but_should_refresh_immediately_before_live_submission"

    summary = {
        "schema_version": 1,
        "record_type": "igp24_group_compatible_submission_gate",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_group_compatible_submission_gate.py",
        "source_commit": source_commit,
        "command": command or [],
        "inputs": {
            "selected_jsonl": repo_relative(selected_jsonl),
            "coefficients_txt": repo_relative(coefficients_txt),
            "sair_sync_summary_json": repo_relative(sair_sync_summary_json) if sair_sync_summary_json else None,
            "target_r": target_r,
            "coeff_bound": coeff_bound,
            "prime_limit": prime_limit,
            "exact_score_timeout": exact_score_timeout,
        },
        "selected_rows": len(gate_rows),
        "selected_hashes": [row["canonical_hash"] for row in gate_rows],
        "duplicate_hashes": sorted(duplicate_hashes),
        "selected_possible_uncovered_pair_count": len(uncovered_pairs),
        "selected_possible_low_team_pair_count": len(low_team_pairs),
        "selected_possible_crowded_pair_count": len(crowded_pairs),
        "selected_possible_uncovered_pairs": uncovered_pairs,
        "selected_possible_low_team_pairs": low_team_pairs,
        "selected_possible_crowded_pairs": crowded_pairs,
        "compatible_label_count_distribution": dict(
            Counter(str(row.get("compatible_label_count")) for row in gate_rows)
        ),
        "check_failures": sorted(blockers),
        "local_sair_dry_run": dry_run_payload,
        "sair_sync": {
            "provided": sync_summary is not None,
            "created_at": sync_summary.get("created_at") if sync_summary else None,
            "partial_sync": sync_summary.get("sync_status", {}).get("partial_sync") if sync_summary else None,
            "submissions_requested": sync_summary.get("sync_status", {}).get("submissions_requested") if sync_summary else None,
        },
        "local_gate_passed": local_gate_passed,
        "local_packet_ready_for_human_review": local_gate_passed,
        "exact_label_verified": False,
        "dry_run_validation_passed": bool(dry_run_payload.get("ok") and dry_run_payload.get("dry_run")),
        "live_submission_recommended_now": False,
        "live_submission_reason": (
            "local gate passed, but compatibility is necessary evidence only; exact labels remain unknown and live SAIR submission requires explicit user approval"
            if local_gate_passed
            else "local gate failed; see check_failures"
        ),
        "remaining_submission_gates": remaining_gates,
        "output_files": {
            "summary_json": repo_relative(output_dir / SUMMARY_JSON),
            "report_md": repo_relative(output_dir / REPORT_MD),
            "rows_jsonl": repo_relative(output_dir / ROWS_JSONL),
            "coefficients_txt": repo_relative(output_dir / COEFFICIENTS_TXT),
            "sair_local_dry_run_json": repo_relative(output_dir / SAIR_DRY_RUN_JSON),
        },
        "safety": {
            "local_file_only": True,
            "sair_submission": False,
            "sair_api_calls": False,
            "network_calls": False,
            "api_key_recorded": False,
            "api_key_required": False,
            "manual_review_package_only": True,
            "compatibility_not_exact_label_claim": True,
        },
    }

    paths = {
        "summary_json": output_dir / SUMMARY_JSON,
        "report_md": output_dir / REPORT_MD,
        "rows_jsonl": output_dir / ROWS_JSONL,
        "coefficients_txt": output_dir / COEFFICIENTS_TXT,
        "sair_local_dry_run_json": output_dir / SAIR_DRY_RUN_JSON,
    }
    paths["summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    write_jsonl(paths["rows_jsonl"], gate_rows)
    paths["coefficients_txt"].write_text("\n".join(normalized_lines) + "\n", encoding="utf-8")
    paths["sair_local_dry_run_json"].write_text(
        json.dumps(dry_run_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["report_md"].write_text(report_markdown(summary, gate_rows, normalized_lines), encoding="utf-8")
    return paths


def report_markdown(summary: dict[str, Any], rows: list[dict[str, Any]], coefficient_lines: Sequence[str]) -> str:
    def mark(value: bool) -> str:
        return "x" if value else " "

    lines = [
        "# IGP24 Group-Compatible Submission Gate",
        "",
        "This is a local review gate only. It did not submit to SAIR, call the SAIR API, or read an API key.",
        "",
        "## Status",
        "",
        f"- [{mark(bool(summary.get('local_gate_passed')))}] Local exact validity and packet checks passed.",
        f"- [{mark(bool(summary.get('dry_run_validation_passed')))}] Local SAIR dry-run formatting/body-size validation passed.",
        f"- [{mark(bool(summary.get('sair_sync', {}).get('partial_sync') is False))}] Complete SAIR sync summary supplied.",
        f"- [ ] Exact Galois labels verified: `{summary.get('exact_label_verified')}`",
        f"- [ ] Live submission recommended now: `{summary.get('live_submission_recommended_now')}`",
        "",
        f"Reason: {summary.get('live_submission_reason')}",
        "",
        "## Packet Summary",
        "",
        f"- Rows: `{summary.get('selected_rows')}`",
        f"- Possible uncovered pairs: `{summary.get('selected_possible_uncovered_pair_count')}`",
        f"- Possible low-team pairs: `{summary.get('selected_possible_low_team_pair_count')}`",
        f"- Possible crowded pairs: `{summary.get('selected_possible_crowded_pair_count')}`",
        f"- Body bytes: `{summary.get('local_sair_dry_run', {}).get('body_bytes')}`",
        f"- Coefficient SHA256: `{sha256_text(coefficient_lines)}`",
        "",
        "## Selected Rows",
        "",
        "| rank | hash | r | compatible labels | uncovered | low-team | crowded | local status |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        local = row.get("local_validation", {})
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("gate_rank")),
                    f"`{row.get('short_hash')}`",
                    str(local.get("real_root_count")),
                    str(row.get("compatible_label_count")),
                    str(len(row.get("possible_uncovered_pairs") or [])),
                    str(len(row.get("possible_low_team_pairs") or [])),
                    str(len(row.get("possible_crowded_pairs") or [])),
                    str(row.get("review_status")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Remaining Gates",
            "",
        ]
    )
    for gate in summary.get("remaining_submission_gates") or []:
        lines.append(f"- `{gate}`")
    if summary.get("check_failures"):
        lines.extend(["", "## Check Failures", ""])
        for failure in summary["check_failures"]:
            lines.append(f"- `{failure}`")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Compatibility evidence is necessary evidence only; it is not an exact-label claim.",
            "- The coefficient file is normalized for manual review but is not submitted automatically.",
            "- Live submission still requires explicit user approval of the exact packet.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected_jsonl", type=Path, required=True)
    parser.add_argument("--coefficients_txt", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--target_r", type=int)
    parser.add_argument("--coeff_bound", type=int, default=10**18)
    parser.add_argument("--prime_limit", type=int, default=11)
    parser.add_argument("--exact_score_timeout", type=float, default=10.0)
    parser.add_argument("--sair_sync_summary_json", type=Path)
    parser.add_argument("--repo_root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = [sys.executable, *sys.argv] if argv is None else [
        sys.executable,
        "scripts/igp24_group_compatible_submission_gate.py",
        *argv,
    ]
    try:
        paths = build_gate(
            selected_jsonl=args.selected_jsonl.resolve(),
            coefficients_txt=args.coefficients_txt.resolve(),
            output_dir=args.output_dir.resolve(),
            target_r=args.target_r,
            coeff_bound=int(args.coeff_bound),
            prime_limit=int(args.prime_limit),
            exact_score_timeout=float(args.exact_score_timeout),
            sair_sync_summary_json=args.sair_sync_summary_json.resolve() if args.sair_sync_summary_json else None,
            command=command,
            source_commit=get_source_commit(args.repo_root.resolve()),
        )
    except (FileNotFoundError, json.JSONDecodeError, GateError, SAIRAPIError, ValueError) as exc:
        parser.error(str(exc))

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    print(f"selected_rows\t{summary['selected_rows']}")
    print(f"local_gate_passed\t{summary['local_gate_passed']}")
    print(f"dry_run_validation_passed\t{summary['dry_run_validation_passed']}")
    print(f"possible_uncovered_pairs\t{summary['selected_possible_uncovered_pair_count']}")
    print(f"possible_low_team_pairs\t{summary['selected_possible_low_team_pair_count']}")
    print(f"live_submission_recommended_now\t{summary['live_submission_recommended_now']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
