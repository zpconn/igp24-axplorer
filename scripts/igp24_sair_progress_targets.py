#!/usr/bin/env python3
"""Build a target-aware IGP24 plan from live SAIR label progress.

The raw full progress snapshot is large, so this helper can read it from a
local JSON file under /tmp and commit only compact derived planning artifacts.
It can also fetch the snapshot directly through the credential-safe SAIR API
client when explicitly requested.
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

from src.igp24.verifiers.sair_api import SAIRAPIVerifier  # noqa: E402


DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"
PLAN_JSON = "sair_live_target_plan.json"
SUMMARY_JSON = "sair_live_target_plan_summary.json"
REPORT_MD = "sair_live_target_plan.md"
TOP_TARGETS_JSONL = "sair_live_top_remaining_targets.jsonl"
HIGH_VALUE_R_WEIGHTS = {24: 32.0, 16: 24.0, 20: 21.0, 12: 18.0, 8: 16.0}


def load_pair_status(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("record_type") != "igp24_pair_status_ledger":
        raise ValueError("unexpected pair-status record_type")
    return payload


def accepted_pair_keys(pair_status: dict[str, Any]) -> set[str]:
    return {
        str(pair.get("pair_key"))
        for pair in pair_status.get("pairs") or []
        if isinstance(pair, dict) and pair.get("status") == "accepted" and pair.get("pair_key")
    }


def accepted_labels(pair_status: dict[str, Any]) -> set[str]:
    return {
        str(pair.get("label"))
        for pair in pair_status.get("pairs") or []
        if isinstance(pair, dict) and pair.get("status") == "accepted" and pair.get("label")
    }


def load_progress_snapshot(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("data"), dict):
        data = payload["data"]
        labels = data.get("labels") or []
        pages = [
            {
                "generatedAt": data.get("generatedAt"),
                "labels": len(labels),
                "nextCursorPresent": bool(data.get("nextCursor")),
                "meta": data.get("meta"),
            }
        ]
        return {
            "record_type": "igp24_sair_label_progress_snapshot",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "query": {"source": str(path)},
            "page_count": 1,
            "label_count": len(labels),
            "pages": pages,
            "labels": labels,
        }
    if payload.get("record_type") != "igp24_sair_label_progress_snapshot":
        raise ValueError("unexpected progress snapshot record_type")
    if not isinstance(payload.get("labels"), list):
        raise ValueError("progress snapshot missing labels")
    return payload


def fetch_progress_snapshot(*, include_empty: bool = True, limit: int = 5000) -> dict[str, Any]:
    client = SAIRAPIVerifier(dry_run=False)
    labels: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload = client.get_label_progress(include_empty=include_empty, limit=limit, cursor=cursor)
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        page_labels = data.get("labels") or []
        pages.append(
            {
                "generatedAt": data.get("generatedAt"),
                "labels": len(page_labels),
                "nextCursorPresent": bool(data.get("nextCursor")),
                "meta": data.get("meta"),
            }
        )
        labels.extend(page_labels)
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "query": {"limit": limit, "includeEmpty": include_empty},
        "page_count": len(pages),
        "label_count": len(labels),
        "pages": pages,
        "labels": labels,
    }


def _signature_by_r(label_row: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_r: dict[int, dict[str, Any]] = {}
    for signature in label_row.get("signatures") or []:
        if isinstance(signature, dict) and signature.get("r") is not None:
            by_r[int(signature["r"])] = signature
    return by_r


def iter_signature_rows(
    labels: Iterable[dict[str, Any]],
    *,
    local_accepted_pairs: set[str],
    local_accepted_labels: set[str],
) -> Iterable[dict[str, Any]]:
    for label_row in labels:
        label = str(label_row.get("label"))
        label_team_count = int(label_row.get("teamCount") or 0)
        label_remaining = [int(value) for value in (label_row.get("remainingSignatures") or [])]
        signature_by_r = _signature_by_r(label_row)
        for r_value in label_remaining:
            signature = signature_by_r.get(r_value, {})
            pair_key = f"{label}|r={r_value}"
            signature_team_count = int(signature.get("teamCount") or 0)
            high_value_weight = HIGH_VALUE_R_WEIGHTS.get(r_value, 0.0)
            target_score = round(
                1000.0
                + high_value_weight
                + min(len(label_remaining), 12) * 2.0
                - signature_team_count * 9.0
                - label_team_count * 1.5
                - (60.0 if pair_key in local_accepted_pairs else 0.0)
                - (12.0 if label in local_accepted_labels else 0.0),
                2,
            )
            yield {
                "pair_key": pair_key,
                "label": label,
                "t": int(label_row.get("t") or label.removeprefix("24T")),
                "r": r_value,
                "target_score": target_score,
                "label_team_count": label_team_count,
                "signature_team_count": signature_team_count,
                "label_remaining_signature_count": len(label_remaining),
                "label_discovered_signature_count": len(label_row.get("discoveredSignatures") or []),
                "label_allowed_signature_count": len(label_row.get("allowedR") or []),
                "minimum_disc_abs": label_row.get("minimumDiscAbs"),
                "signature_minimum_disc_abs": signature.get("minimumDiscAbs"),
                "local_pair_already_accepted": pair_key in local_accepted_pairs,
                "local_label_already_seen": label in local_accepted_labels,
            }


def coverage_by_r(labels: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed: Counter[int] = Counter()
    discovered: Counter[int] = Counter()
    remaining: Counter[int] = Counter()
    signature_team_sum: Counter[int] = Counter()
    signature_team_max: Counter[int] = Counter()
    for label_row in labels:
        for r_value in label_row.get("allowedR") or []:
            allowed[int(r_value)] += 1
        for r_value in label_row.get("discoveredSignatures") or []:
            discovered[int(r_value)] += 1
        for r_value in label_row.get("remainingSignatures") or []:
            remaining[int(r_value)] += 1
        for signature in label_row.get("signatures") or []:
            r_value = int(signature.get("r"))
            team_count = int(signature.get("teamCount") or 0)
            signature_team_sum[r_value] += team_count
            signature_team_max[r_value] = max(signature_team_max[r_value], team_count)
    rows: list[dict[str, Any]] = []
    for r_value in sorted(allowed):
        total = allowed[r_value]
        rem = remaining[r_value]
        disc = discovered[r_value]
        rows.append(
            {
                "r": r_value,
                "allowed": total,
                "discovered": disc,
                "remaining": rem,
                "discovered_pct": round(100.0 * disc / total, 2) if total else 0.0,
                "remaining_pct": round(100.0 * rem / total, 2) if total else 0.0,
                "average_signature_team_count": round(signature_team_sum[r_value] / total, 2) if total else 0.0,
                "max_signature_team_count": signature_team_max[r_value],
            }
        )
    return rows


def target_groups_by_r(rows: Iterable[dict[str, Any]], *, limit_per_r: int = 12) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[int(row["r"])].append(row)
    out: dict[str, list[dict[str, Any]]] = {}
    for r_value, bucket_rows in sorted(buckets.items()):
        ranked = sorted(bucket_rows, key=lambda row: (row["target_score"], -int(row["t"])), reverse=True)
        out[str(r_value)] = ranked[:limit_per_r]
    return out


def build_plan(
    snapshot: dict[str, Any],
    pair_status: dict[str, Any],
    *,
    top_limit: int = 250,
    per_r_limit: int = 12,
) -> dict[str, Any]:
    labels = list(snapshot.get("labels") or [])
    local_pairs = accepted_pair_keys(pair_status)
    local_labels = accepted_labels(pair_status)
    signature_rows = list(
        iter_signature_rows(labels, local_accepted_pairs=local_pairs, local_accepted_labels=local_labels)
    )
    ranked_targets = sorted(signature_rows, key=lambda row: (row["target_score"], -int(row["t"])), reverse=True)
    by_r = coverage_by_r(labels)
    remaining_by_r = {row["r"]: row["remaining"] for row in by_r}
    top_remaining_rs = [row["r"] for row in sorted(by_r, key=lambda row: row["remaining"], reverse=True)[:5]]
    high_value_remaining = {str(r): remaining_by_r.get(r, 0) for r in HIGH_VALUE_R_WEIGHTS}
    primary = ranked_targets[0] if ranked_targets else None
    return {
        "schema_version": 1,
        "record_type": "igp24_sair_live_target_plan",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_sair_progress_targets.py",
        "input_snapshot": {
            "record_type": snapshot.get("record_type"),
            "created_at": snapshot.get("created_at"),
            "query": snapshot.get("query"),
            "page_count": snapshot.get("page_count"),
            "label_count": snapshot.get("label_count"),
            "first_generated_at": (snapshot.get("pages") or [{}])[0].get("generatedAt"),
            "last_generated_at": (snapshot.get("pages") or [{}])[-1].get("generatedAt"),
            "published": ((snapshot.get("pages") or [{}])[0].get("meta") or {}).get("published"),
        },
        "local_pair_status": {
            "accepted_pair_count": len(local_pairs),
            "accepted_label_count": len(local_labels),
        },
        "coverage_by_r": by_r,
        "remaining_signature_count": len(signature_rows),
        "top_remaining_rs": top_remaining_rs,
        "high_value_remaining": high_value_remaining,
        "top_remaining_targets": ranked_targets[:top_limit],
        "top_targets_by_r": target_groups_by_r(ranked_targets, limit_per_r=per_r_limit),
        "strategic_decision": {
            "primary_target": primary,
            "do_not_widen_recent_tower_blindly": True,
            "recommended_lane": "target-conditioned high-real-root search, starting with r=24/r=16/r=20 labels that have no credited teams",
            "generation_caveat": (
                "The API identifies exact remaining (24Tt, r) signatures, but the current local generators "
                "do not directly condition on 24T label. New queues should therefore be small, validated, "
                "and treated as exploratory exact-label probes rather than guaranteed target hits."
            ),
            "gpu_training_recommended_now": False,
            "auto_submission_recommended_now": False,
        },
    }


def build_markdown(plan: dict[str, Any]) -> str:
    snapshot = plan["input_snapshot"]
    decision = plan["strategic_decision"]
    lines = [
        "# SAIR Live Target Plan",
        "",
        "## Snapshot",
        "",
        f"- Pages: {snapshot.get('page_count')}",
        f"- Labels: {snapshot.get('label_count')}",
        f"- Published: {snapshot.get('published')}",
        f"- First generatedAt: `{snapshot.get('first_generated_at')}`",
        f"- Last generatedAt: `{snapshot.get('last_generated_at')}`",
        f"- Remaining signatures: {plan.get('remaining_signature_count')}",
        "",
        "## Coverage By r",
        "",
        "| r | allowed | discovered | remaining | discovered % | remaining % |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in plan["coverage_by_r"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["r"]),
                    str(row["allowed"]),
                    str(row["discovered"]),
                    str(row["remaining"]),
                    f"{row['discovered_pct']:.2f}",
                    f"{row['remaining_pct']:.2f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Top Remaining Targets",
            "",
            "| rank | pair | label teams | signature teams | remaining signatures on label | score |",
            "| ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for rank, row in enumerate(plan["top_remaining_targets"][:25], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    row["pair_key"],
                    str(row["label_team_count"]),
                    str(row["signature_team_count"]),
                    str(row["label_remaining_signature_count"]),
                    f"{float(row['target_score']):.2f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Recommended lane: {decision['recommended_lane']}",
            f"- GPU training now: {decision['gpu_training_recommended_now']}",
            f"- Automatic submission now: {decision['auto_submission_recommended_now']}",
            f"- Caveat: {decision['generation_caveat']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(plan: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / PLAN_JSON
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    targets_path = output_dir / TOP_TARGETS_JSONL
    output_files = {
        "plan_json": str(plan_path),
        "summary_json": str(summary_path),
        "report_md": str(report_path),
        "top_targets_jsonl": str(targets_path),
    }
    plan_with_files = {**plan, "output_files": output_files}
    plan_path.write_text(json.dumps(plan_with_files, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    summary = {
        "created_at": plan["created_at"],
        "snapshot": plan["input_snapshot"],
        "remaining_signature_count": plan["remaining_signature_count"],
        "top_remaining_rs": plan["top_remaining_rs"],
        "high_value_remaining": plan["high_value_remaining"],
        "primary_target": plan["strategic_decision"]["primary_target"],
        "recommended_lane": plan["strategic_decision"]["recommended_lane"],
        "gpu_training_recommended_now": plan["strategic_decision"]["gpu_training_recommended_now"],
        "auto_submission_recommended_now": plan["strategic_decision"]["auto_submission_recommended_now"],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    report_path.write_text(build_markdown(plan_with_files), encoding="utf-8")
    with targets_path.open("w", encoding="utf-8") as handle:
        for row in plan["top_remaining_targets"]:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {name: Path(path) for name, path in output_files.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a compact target plan from SAIR IGP24 label progress")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--progress_snapshot_json", type=Path)
    source.add_argument("--fetch_live", action="store_true")
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--top_limit", type=int, default=250)
    parser.add_argument("--per_r_limit", type=int, default=12)
    parser.add_argument("--fetch_limit", type=int, default=5000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    snapshot = (
        fetch_progress_snapshot(limit=args.fetch_limit)
        if args.fetch_live
        else load_progress_snapshot(args.progress_snapshot_json)
    )
    pair_status = load_pair_status(args.pair_status_json)
    plan = build_plan(snapshot, pair_status, top_limit=args.top_limit, per_r_limit=args.per_r_limit)
    paths = write_outputs(plan, args.output_dir)
    print(f"remaining_signature_count\t{plan['remaining_signature_count']}")
    print(f"top_remaining_rs\t{json.dumps(plan['top_remaining_rs'])}")
    print(f"primary_target\t{json.dumps(plan['strategic_decision']['primary_target'])}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
