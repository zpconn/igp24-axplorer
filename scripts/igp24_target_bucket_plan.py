#!/usr/bin/env python3
"""Plan target IGP24 signature buckets from aggregate discovery data.

This helper is intentionally local-file-only. The discovery snapshot it reads
is aggregate screenshot-derived data, not a live uncovered-signature list, so
the output ranks r-buckets and recommends construction work rather than
claiming exact uncovered ``(24Tt, r)`` targets.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = REPO_ROOT / "data/igp24/sair_discovery_snapshot_20260706_1648.json"
DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"

PLAN_JSON = "target_bucket_plan.json"
PLAN_MD = "target_bucket_plan.md"
SUMMARY_JSON = "target_bucket_plan_summary.json"

API_CAVEAT = (
    "Exact uncovered (24Tt, r) target lists are not derivable from this "
    "screenshot snapshot. Pull fresh SAIR API data before search or submission "
    "planning that depends on exact target membership."
)


BUCKET_PROFILES: dict[int, dict[str, Any]] = {
    0: {
        "generator_status": "saved proxy rows exist, but this is not a largest remaining bucket",
        "action_adjustment": -8.0,
        "recommendation": "Treat r=0 as a lower-priority side lane unless fresh API targets show an easy gap.",
    },
    2: {
        "generator_status": "cleanup bucket, almost fully covered",
        "action_adjustment": -45.0,
        "recommendation": "Do not spend broad search here; only pursue exact API-listed cleanup targets.",
    },
    4: {
        "generator_status": "locally mature but crowded; many submissions collapsed to known/generic labels",
        "action_adjustment": -22.0,
        "recommendation": "Avoid broad r=4 mining unless exact score/discriminant improvement is the target.",
    },
    6: {
        "generator_status": "small cleanup bucket",
        "action_adjustment": -28.0,
        "recommendation": "Use only for exact API-guided cleanup.",
    },
    8: {
        "generator_status": "productive r8_quartic_lift path already produced four accepted labels from six rows",
        "action_adjustment": 22.0,
        "recommendation": "Continue bounded r8 solvable/composed-family variations as a near-term submission lane.",
    },
    10: {
        "generator_status": "small cleanup bucket",
        "action_adjustment": -30.0,
        "recommendation": "Use only for exact API-guided cleanup.",
    },
    12: {
        "generator_status": "large high-real-root bucket; no proven local explicit generator yet",
        "action_adjustment": 18.0,
        "recommendation": "Build an explicit solvable/composed r12 construction before broad sampling.",
    },
    14: {
        "generator_status": "small cleanup bucket",
        "action_adjustment": -30.0,
        "recommendation": "Use only for exact API-guided cleanup.",
    },
    16: {
        "generator_status": "large bucket, but current divisor-2 r16 families repeatedly collapsed",
        "action_adjustment": -25.0,
        "recommendation": "Keep r16 as globally important, but do not widen the current g(x^2)/odd-perturbation corridor.",
    },
    18: {
        "generator_status": "small cleanup bucket",
        "action_adjustment": -30.0,
        "recommendation": "Use only for exact API-guided cleanup.",
    },
    20: {
        "generator_status": "large undercovered high-real-root bucket; no proven local explicit generator yet",
        "action_adjustment": 24.0,
        "recommendation": "Prototype an explicit r20 solvable/high-real-root construction.",
    },
    22: {
        "generator_status": "fully covered in snapshot",
        "action_adjustment": -100.0,
        "recommendation": "Skip unless the live API later shows newly uncovered targets.",
    },
    24: {
        "generator_status": "largest remaining bucket; no proven local explicit generator yet",
        "action_adjustment": 28.0,
        "recommendation": "Prioritize a new explicit r24 solvable/high-real-root construction.",
    },
}


def load_discovery_snapshot(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("record_type") != "sair_igp24_discovery_page_snapshot":
        raise ValueError("unexpected discovery snapshot record_type")
    if not isinstance(payload.get("coverage_summary"), dict):
        raise ValueError("discovery snapshot missing coverage_summary")
    per_r = payload.get("per_r")
    if not isinstance(per_r, list) or not per_r:
        raise ValueError("discovery snapshot missing per_r rows")
    for row in per_r:
        for field in ("r", "solved", "total", "remaining"):
            if field not in row:
                raise ValueError(f"per_r row missing {field}")
        row["r"] = int(row["r"])
        row["solved"] = int(row["solved"])
        row["total"] = int(row["total"])
        row["remaining"] = int(row["remaining"])
        row["remaining_pct"] = float(row.get("remaining_pct", 100.0 * row["remaining"] / row["total"]))
        row["solved_pct"] = float(row.get("solved_pct", 100.0 * row["solved"] / row["total"]))
    return payload


def load_pair_status(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("record_type") != "igp24_pair_status_ledger":
        raise ValueError("unexpected pair-status record_type")
    return payload


def accepted_pair_summary(pair_status: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_r: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "accepted_pair_keys": [],
            "accepted_labels": [],
            "accepted_alternate_count": 0,
        }
    )
    for pair in pair_status.get("pairs") or []:
        if not isinstance(pair, dict) or str(pair.get("status") or "") != "accepted":
            continue
        r_value = int(pair.get("r"))
        item = by_r[r_value]
        item["accepted_pair_keys"].append(str(pair.get("pair_key")))
        item["accepted_labels"].append(str(pair.get("label")))
        item["accepted_alternate_count"] += len(pair.get("accepted_alternates") or [])
    for item in by_r.values():
        item["accepted_pair_keys"] = sorted(set(item["accepted_pair_keys"]))
        item["accepted_labels"] = sorted(set(item["accepted_labels"]))
        item["accepted_pair_count"] = len(item["accepted_pair_keys"])
    return dict(by_r)


def collapse_evidence_for_bucket(r_value: int, local: dict[str, Any]) -> list[str]:
    labels = set(local.get("accepted_labels") or [])
    if r_value == 16 and {"24T24979", "24T25000"}.issubset(labels):
        return [
            "exact divisor-2 g(x^2) rows landed as 24T24979|r=16",
            "odd and multi-odd near-composed divisor-2 rows landed as 24T25000|r=16",
        ]
    if r_value == 8 and {"24T657", "24T661", "24T1310", "24T9993"}.issubset(labels):
        return ["r8_quartic_lift produced multiple accepted labels from a six-row submission"]
    if r_value == 4 and "24T25000" in labels:
        return ["many r4 follow-up rows collapsed to generic 24T25000|r=4"]
    return []


def plan_bucket(
    row: dict[str, Any],
    *,
    max_remaining: int,
    local_by_r: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    r_value = int(row["r"])
    profile = BUCKET_PROFILES.get(
        r_value,
        {
            "generator_status": "no local profile",
            "action_adjustment": 0.0,
            "recommendation": "Use API target data before spending search budget.",
        },
    )
    remaining = int(row["remaining"])
    total = int(row["total"])
    remaining_pct = float(row["remaining_pct"])
    remaining_share_of_max = remaining / max_remaining if max_remaining else 0.0
    opportunity_score = round(65.0 * remaining_share_of_max + 0.35 * remaining_pct, 2)
    action_score = round(opportunity_score + float(profile["action_adjustment"]), 2)
    local = local_by_r.get(r_value, {})
    return {
        "r": r_value,
        "total": total,
        "solved": int(row["solved"]),
        "remaining": remaining,
        "solved_pct": float(row["solved_pct"]),
        "remaining_pct": remaining_pct,
        "remaining_share_of_all_uncovered_pct": None,
        "opportunity_score": opportunity_score,
        "action_score": action_score,
        "local_accepted_pair_count": int(local.get("accepted_pair_count") or 0),
        "local_accepted_pair_keys": list(local.get("accepted_pair_keys") or []),
        "local_accepted_labels": list(local.get("accepted_labels") or []),
        "local_accepted_alternate_count": int(local.get("accepted_alternate_count") or 0),
        "generator_status": str(profile["generator_status"]),
        "collapse_or_success_evidence": collapse_evidence_for_bucket(r_value, local),
        "recommendation": str(profile["recommendation"]),
        "api_required_for_exact_targets": True,
    }


def build_plan(snapshot: dict[str, Any], pair_status: dict[str, Any]) -> dict[str, Any]:
    local_by_r = accepted_pair_summary(pair_status)
    max_remaining = max(int(row["remaining"]) for row in snapshot["per_r"])
    total_uncovered = int(snapshot["coverage_summary"]["uncovered_signatures"])
    buckets = [plan_bucket(row, max_remaining=max_remaining, local_by_r=local_by_r) for row in snapshot["per_r"]]
    for bucket in buckets:
        bucket["remaining_share_of_all_uncovered_pct"] = round(
            100.0 * int(bucket["remaining"]) / total_uncovered, 2
        )
    by_action = sorted(buckets, key=lambda row: (row["action_score"], row["remaining"]), reverse=True)
    by_remaining = sorted(buckets, key=lambda row: row["remaining"], reverse=True)
    api_target_list_available = bool(snapshot.get("exact_uncovered_targets"))
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_target_bucket_plan.py",
        "inputs": {
            "discovery_snapshot_captured_at": snapshot.get("captured_at"),
            "discovery_snapshot_capture_method": snapshot.get("capture_method"),
            "pair_status_record_type": pair_status.get("record_type"),
        },
        "api_target_list_available": api_target_list_available,
        "api_caveat": API_CAVEAT,
        "coverage_summary": snapshot["coverage_summary"],
        "largest_remaining_buckets": by_remaining,
        "recommended_action_buckets": by_action,
        "bucket_rankings": buckets,
        "strategic_recommendations": [
            "Do not widen the current r16 divisor-2 perturbation family; it repeatedly collapsed to 24T24979/24T25000.",
            "Prioritize a new explicit r24 solvable/high-real-root construction because r=24 is the largest remaining bucket.",
            "Prototype r20 and r12 solvable/high-real-root constructions; both are large undercovered buckets without proven local generators.",
            "Continue bounded r8 composed-family work because r8_quartic_lift already produced multiple accepted labels.",
            "Do not start GPU/model training until there is a target-conditioned sampling objective derived from API target data or a successful construction family.",
        ],
        "no_gpu_training_recommended": True,
    }


def write_outputs(plan: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / PLAN_JSON
    md_path = output_dir / PLAN_MD
    summary_path = output_dir / SUMMARY_JSON
    output_files = {
        "target_bucket_plan_json": str(plan_path),
        "target_bucket_plan_md": str(md_path),
        "target_bucket_plan_summary_json": str(summary_path),
    }
    plan_with_files = {**plan, "output_files": output_files}
    plan_path.write_text(json.dumps(plan_with_files, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    summary = {
        "created_at": plan["created_at"],
        "api_target_list_available": plan["api_target_list_available"],
        "api_caveat": plan["api_caveat"],
        "top_action_rs": [row["r"] for row in plan["recommended_action_buckets"][:5]],
        "top_remaining_rs": [row["r"] for row in plan["largest_remaining_buckets"][:5]],
        "no_gpu_training_recommended": plan["no_gpu_training_recommended"],
        "primary_next_family_recommendation": plan["strategic_recommendations"][1],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown(plan_with_files), encoding="utf-8")
    return {name: Path(path) for name, path in output_files.items()}


def build_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Target Bucket Plan",
        "",
        plan["api_caveat"],
        "",
        "## Snapshot",
        "",
        f"- Captured at: `{plan['inputs'].get('discovery_snapshot_captured_at')}`",
        f"- Capture method: `{plan['inputs'].get('discovery_snapshot_capture_method')}`",
        f"- Total valid signatures: {plan['coverage_summary'].get('total_valid_signatures')}",
        f"- Uncovered signatures: {plan['coverage_summary'].get('uncovered_signatures')}",
        f"- Uncovered solvable: {plan['coverage_summary'].get('uncovered_solvable')} ({plan['coverage_summary'].get('uncovered_solvable_pct')}%)",
        f"- LMFDB baseline signatures: {plan['coverage_summary'].get('lmfdb_baseline')}",
        "",
        "## Largest Remaining Buckets",
        "",
        "| r | remaining | total | remaining % | local accepted pairs | note |",
        "| ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in plan["largest_remaining_buckets"][:8]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["r"]),
                    str(row["remaining"]),
                    str(row["total"]),
                    f"{float(row['remaining_pct']):.1f}",
                    str(row["local_accepted_pair_count"]),
                    row["generator_status"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recommended Action Buckets",
            "",
            "| rank | r | action score | remaining | local evidence | recommendation |",
            "| ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for rank, row in enumerate(plan["recommended_action_buckets"][:8], start=1):
        evidence = "; ".join(row["collapse_or_success_evidence"]) or row["generator_status"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    str(row["r"]),
                    f"{float(row['action_score']):.2f}",
                    str(row["remaining"]),
                    evidence,
                    row["recommendation"],
                ]
            )
            + " |"
        )
    lines.extend(["", "## Strategy", ""])
    for item in plan["strategic_recommendations"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Artifacts", ""])
    for label, path in plan.get("output_files", {}).items():
        lines.append(f"- {label}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local target-aware IGP24 r-bucket plan")
    parser.add_argument("--discovery_snapshot_json", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    snapshot = load_discovery_snapshot(args.discovery_snapshot_json)
    pair_status = load_pair_status(args.pair_status_json)
    plan = build_plan(snapshot, pair_status)
    paths = write_outputs(plan, args.output_dir)
    print(f"api_target_list_available\t{json.dumps(plan['api_target_list_available'])}")
    print(f"top_action_rs\t{json.dumps([row['r'] for row in plan['recommended_action_buckets'][:5]])}")
    print(f"top_remaining_rs\t{json.dumps([row['r'] for row in plan['largest_remaining_buckets'][:5]])}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
