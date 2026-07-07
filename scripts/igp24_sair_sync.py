#!/usr/bin/env python3
"""Synchronize IGP24 planning state from the SAIR Public API.

The sync helper actively uses the documented IGP24 competition endpoints:
competition schema, participation state, label progress, submission listing,
submission detail, and submission download. It never serializes the API key and
does not submit anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_sair_progress_targets import coverage_by_r  # noqa: E402
from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.polynomial import stable_canonical_hash  # noqa: E402
from src.igp24.verifiers.sair_api import (  # noqa: E402
    DEFAULT_API_KEY_ENV,
    SAIRAPIError,
    SAIRAPIVerifier,
    format_polynomial_line,
    parse_polynomial_line,
)


SYNC_SUMMARY_JSON = "sair_sync_summary.json"
SYNC_REPORT_MD = "sair_sync_report.md"
PROGRESS_SUMMARY_JSON = "sair_progress_snapshot_summary.json"
LABEL_PROGRESS_JSONL = "sair_label_progress.jsonl"
SUBMISSION_INDEX_JSON = "sair_submission_index.json"
SUBMISSION_ROWS_JSONL = "sair_submission_rows.jsonl"
PENDING_ROWS_JSONL = "sair_pending_rows.jsonl"
SCOREABLE_ROWS_JSONL = "sair_scoreable_rows.jsonl"
FAILED_ROWS_JSONL = "sair_failed_rows.jsonl"
UNMATCHED_ROWS_JSONL = "sair_unmatched_rows.jsonl"

COMMITTED_DATA_ROOT = REPO_ROOT / "data/igp24"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def response_data(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    if isinstance(payload, dict):
        return payload
    return {}


def rate_limit_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in (headers or {}).items():
        lowered = key.lower()
        if lowered.startswith("x-ratelimit") or lowered == "retry-after":
            out[key] = str(value)
    return out


def safe_compact(value: Any, *, max_depth: int = 4) -> Any:
    """Keep API metadata useful while avoiding huge payload echoes."""

    if max_depth <= 0:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            return f"list[{len(value)}]"
        if isinstance(value, dict):
            return f"dict[{len(value)}]"
        return str(type(value).__name__)
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in {"apikey", "api_key", "authorization", "token", "secret"}:
                out[str(key)] = "[redacted]"
            else:
                out[str(key)] = safe_compact(item, max_depth=max_depth - 1)
        return out
    if isinstance(value, list):
        if len(value) > 25:
            return [safe_compact(item, max_depth=max_depth - 1) for item in value[:25]] + [f"... {len(value) - 25} more"]
        return [safe_compact(item, max_depth=max_depth - 1) for item in value]
    return value


def request_api(
    client: SAIRAPIVerifier,
    method: str,
    path: str,
    *,
    query: Mapping[str, str | int | bool] | None = None,
    accept: str = "application/json",
    endpoint: str,
    rate_limits: list[dict[str, Any]],
) -> Any:
    payload, headers = client._request(method, path, query=query, accept=accept)  # noqa: SLF001 - sync needs headers.
    captured = rate_limit_headers(headers)
    if captured:
        rate_limits.append({"endpoint": endpoint, "headers": captured})
    return payload


def fetch_full_label_progress(
    client: SAIRAPIVerifier,
    *,
    limit: int,
    rate_limits: list[dict[str, Any]],
) -> dict[str, Any]:
    labels: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        query: dict[str, str | int | bool] = {"limit": limit, "includeEmpty": True}
        if cursor:
            query["cursor"] = cursor
        payload = request_api(
            client,
            "GET",
            "/api/public/v1/competitions/igp24/labels/progress",
            query=query,
            endpoint="labels/progress",
            rate_limits=rate_limits,
        )
        data = response_data(payload)
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
        "created_at": utc_now(),
        "query": {"limit": limit, "includeEmpty": True},
        "page_count": len(pages),
        "label_count": len(labels),
        "pages": pages,
        "labels": labels,
    }


def fetch_all_submission_summaries(
    client: SAIRAPIVerifier,
    *,
    limit: int,
    rate_limits: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        query: dict[str, str | int] = {"limit": limit}
        if cursor:
            query["cursor"] = cursor
        payload = request_api(
            client,
            "GET",
            "/api/public/v1/competitions/igp24/submissions/me",
            query=query,
            endpoint="submissions/me",
            rate_limits=rate_limits,
        )
        data = response_data(payload)
        page_items = data.get("items") or data.get("submissions") or []
        pages.append({"items": len(page_items), "nextCursorPresent": bool(data.get("nextCursor"))})
        items.extend(page_items)
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return items, pages


def fetch_submission_detail(
    client: SAIRAPIVerifier,
    submission_id: str,
    *,
    rate_limits: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = request_api(
        client,
        "GET",
        f"/api/public/v1/competitions/igp24/submissions/{submission_id}",
        endpoint="submissions/{id}",
        rate_limits=rate_limits,
    )
    return response_data(payload)


def download_submission_lines(
    client: SAIRAPIVerifier,
    submission_id: str,
    *,
    rate_limits: list[dict[str, Any]],
) -> list[str]:
    payload = request_api(
        client,
        "GET",
        f"/api/public/v1/competitions/igp24/submissions/{submission_id}/download",
        endpoint="submissions/{id}/download",
        accept="text/plain",
        rate_limits=rate_limits,
    )
    if not isinstance(payload, str):
        return []
    return [line.strip() for line in payload.splitlines() if line.strip()]


def canonical_hash_from_polynomial_line(line: str) -> tuple[str | None, str | None, list[int] | None]:
    try:
        coefficients = parse_polynomial_line(line)
        normalized = format_polynomial_line(coefficients)
        canonical_hash = stable_canonical_hash(coefficients[:-1])
        return canonical_hash, normalized, coefficients
    except Exception as exc:
        return None, str(exc), None


def _iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _iter_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_dicts(item)


def _record_coefficient_line(record: dict[str, Any]) -> str | None:
    for key in ("coefficient_line", "submission_line", "polynomial"):
        if isinstance(record.get(key), str):
            try:
                return format_polynomial_line(str(record[key]))
            except SAIRAPIError:
                continue
    for key in ("exported_coefficients", "coefficients"):
        value = record.get(key)
        if isinstance(value, list):
            try:
                return format_polynomial_line(value)
            except SAIRAPIError:
                if key == "coefficients" and len(value) == 24:
                    try:
                        return format_polynomial_line([*value, 1])
                    except SAIRAPIError:
                        continue
    return None


def build_local_hash_index(data_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not data_root.exists():
        return index
    for path in sorted(data_root.rglob("*")):
        if path.suffix not in {".json", ".jsonl"} or not path.is_file():
            continue
        if "sair_sync_" in str(path):
            continue
        try:
            if path.suffix == ".jsonl":
                payloads = read_jsonl(path)
            else:
                payloads = [read_json(path)]
        except Exception:
            continue
        for payload in payloads:
            for record in _iter_dicts(payload):
                canonical_hash = record.get("canonical_hash") or record.get("candidate_hash")
                if not isinstance(canonical_hash, str) or not canonical_hash:
                    continue
                line = _record_coefficient_line(record)
                item = index.setdefault(
                    canonical_hash,
                    {
                        "canonical_hash": canonical_hash,
                        "short_hash": canonical_hash[:12],
                        "source_paths": [],
                        "coefficient_line": line,
                        "labels": [],
                        "pair_keys": [],
                    },
                )
                if str(path) not in item["source_paths"]:
                    item["source_paths"].append(str(path))
                if line and not item.get("coefficient_line"):
                    item["coefficient_line"] = line
                if record.get("label") and record.get("label") not in item["labels"]:
                    item["labels"].append(record.get("label"))
                if record.get("pair_key") and record.get("pair_key") not in item["pair_keys"]:
                    item["pair_keys"].append(record.get("pair_key"))
    return index


def label_progress_compact_rows(progress_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label_row in progress_snapshot.get("labels") or []:
        if not isinstance(label_row, dict) or not label_row.get("label"):
            continue
        rows.append(
            {
                "label": label_row.get("label"),
                "t": label_row.get("t"),
                "allowedR": label_row.get("allowedR") or [],
                "teamCount": label_row.get("teamCount") or 0,
                "minimumDiscAbs": label_row.get("minimumDiscAbs"),
                "discoveredSignatures": label_row.get("discoveredSignatures") or [],
                "remainingSignatures": label_row.get("remainingSignatures") or [],
                "signatures": label_row.get("signatures") or [],
            }
        )
    return rows


def build_progress_summary(progress_snapshot: dict[str, Any]) -> dict[str, Any]:
    labels = list(progress_snapshot.get("labels") or [])
    coverage_rows = coverage_by_r(labels)
    remaining_total = sum(int(row.get("remaining") or 0) for row in coverage_rows)
    discovered_total = sum(int(row.get("discovered") or 0) for row in coverage_rows)
    zero_team_remaining: list[dict[str, Any]] = []
    for label_row in labels:
        label = str(label_row.get("label") or "")
        team_count = int(label_row.get("teamCount") or 0)
        remaining = [int(value) for value in label_row.get("remainingSignatures") or []]
        if team_count != 0 or not remaining:
            continue
        zero_team_remaining.append(
            {
                "label": label,
                "t": int(label_row.get("t") or label.removeprefix("24T") or 0),
                "remaining_count": len(remaining),
                "remaining_r": remaining,
            }
        )
    zero_team_remaining.sort(key=lambda row: (row["remaining_count"], row["t"]), reverse=True)
    return {
        "record_type": "igp24_sair_progress_snapshot_summary",
        "created_at": utc_now(),
        "source_snapshot": {
            "record_type": progress_snapshot.get("record_type"),
            "created_at": progress_snapshot.get("created_at"),
            "page_count": progress_snapshot.get("page_count"),
            "label_count": progress_snapshot.get("label_count") or len(labels),
            "first_generated_at": (progress_snapshot.get("pages") or [{}])[0].get("generatedAt"),
            "last_generated_at": (progress_snapshot.get("pages") or [{}])[-1].get("generatedAt"),
            "published": ((progress_snapshot.get("pages") or [{}])[0].get("meta") or {}).get("published"),
        },
        "coverage_by_r": coverage_rows,
        "remaining_signature_count": remaining_total,
        "discovered_signature_count": discovered_total,
        "top_remaining_r_buckets": sorted(coverage_rows, key=lambda row: int(row.get("remaining") or 0), reverse=True)[:8],
        "top_zero_team_remaining_labels": zero_team_remaining[:25],
    }


def row_status_class(row: dict[str, Any]) -> str:
    if row.get("status") == "failed" or row.get("failed_reason"):
        return "failed"
    if row.get("queued"):
        return "pending"
    if row.get("scoring_status") == "pending":
        return "pending"
    if row.get("scoreable") is True or row.get("scoring_status") == "scoreable":
        return "scoreable"
    if row.get("status") == "accepted":
        return "accepted_not_scoreable_or_unknown"
    return "unknown"


def normalize_submission_rows(
    detail: dict[str, Any],
    downloaded_lines: list[str],
    *,
    local_hash_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    submission_id = str(detail.get("submissionId") or "")
    index_rows: dict[int, dict[str, Any]] = {}
    for row in detail.get("verifiedPolynomials") or []:
        if not isinstance(row, dict):
            continue
        index = int(row.get("polynomialIndex") or 0)
        pair_key = f"{row.get('label')}|r={int(row.get('r'))}" if row.get("label") and row.get("r") is not None else None
        index_rows[index] = {
            "status": row.get("status") or "accepted",
            "label": row.get("label"),
            "t": row.get("t"),
            "r": row.get("r"),
            "pair_key": pair_key,
            "scoreable": row.get("scoreable"),
            "scoring_status": row.get("scoringStatus"),
            "scoring_reason": row.get("scoringReason"),
            "no_score_reason": row.get("noScoreReason"),
            "in_baseline": row.get("inBaseline"),
            "baseline_unlocked": row.get("baselineUnlocked"),
            "baseline_disc_abs": row.get("baselineDiscAbs"),
            "field_disc_abs": row.get("fieldDiscAbs"),
            "disc_source": row.get("discSource"),
        }
    for row in detail.get("failedPolynomials") or []:
        if not isinstance(row, dict):
            continue
        index = int(row.get("polynomialIndex") or 0)
        index_rows[index] = {
            "status": row.get("status") or "failed",
            "failed_reason": row.get("reason") or row.get("message") or row.get("error"),
        }
    for row in (detail.get("payload") or {}).get("queuedPolynomials") or []:
        if not isinstance(row, dict):
            continue
        index = int(row.get("polynomialIndex") or 0)
        index_rows.setdefault(index, {"status": row.get("status") or "queued", "queued": True})

    max_index = max([len(downloaded_lines) - 1, *index_rows.keys()], default=-1)
    rows: list[dict[str, Any]] = []
    for index in range(max_index + 1):
        line = downloaded_lines[index] if index < len(downloaded_lines) else None
        canonical_hash = None
        normalized_line = None
        coefficient_validation_error = None
        if line:
            canonical_hash, normalized_or_error, _coefficients = canonical_hash_from_polynomial_line(line)
            if canonical_hash:
                normalized_line = normalized_or_error
            else:
                coefficient_validation_error = normalized_or_error
        local_match = local_hash_index.get(canonical_hash or "") if canonical_hash else None
        status_payload = dict(index_rows.get(index) or {"status": "missing_from_submission_detail"})
        local_match_status = "matched" if local_match else "unmatched" if line else "no_polynomial_line"
        row_payload = {
            "submission_id": submission_id,
            "competition_id": detail.get("competitionId"),
            "created_at": detail.get("createdAt"),
            "updated_at": detail.get("updatedAt"),
            "kind": detail.get("kind"),
            "description": (detail.get("meta") or {}).get("description") or detail.get("description"),
            "polynomial_index": index,
            "submitted_line_number": index + 1,
            "polynomial": normalized_line,
            "canonical_hash": canonical_hash,
            "short_hash": canonical_hash[:12] if canonical_hash else None,
            "coefficient_validation_error": coefficient_validation_error,
            "local_match_status": local_match_status,
            "local_match": {
                "source_paths": (local_match or {}).get("source_paths", [])[:6],
                "labels": (local_match or {}).get("labels", []),
                "pair_keys": (local_match or {}).get("pair_keys", []),
            }
            if local_match
            else None,
            **status_payload,
        }
        row_payload["status_class"] = row_status_class(row_payload)
        rows.append(row_payload)
    return rows


def build_submission_index(
    *,
    submission_summaries: list[dict[str, Any]],
    submission_details: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    rate_limits: list[dict[str, Any]],
) -> dict[str, Any]:
    by_submission: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_submission[str(row.get("submission_id"))][str(row.get("status_class"))] += 1
    detail_by_id = {str(row.get("submissionId")): row for row in submission_details}
    index_rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for summary in submission_summaries:
        submission_id = str(summary.get("submissionId") or summary.get("id") or "")
        if not submission_id:
            continue
        seen_ids.add(submission_id)
        detail = detail_by_id.get(submission_id) or summary
        index_rows.append(
            {
                "submission_id": submission_id,
                "created_at": detail.get("createdAt") or summary.get("createdAt"),
                "updated_at": detail.get("updatedAt") or summary.get("updatedAt"),
                "description": (detail.get("meta") or {}).get("description") or detail.get("description") or summary.get("description"),
                "kind": detail.get("kind") or summary.get("kind"),
                "row_counts": dict(by_submission.get(submission_id) or Counter()),
            }
        )
    for submission_id, detail in detail_by_id.items():
        if submission_id in seen_ids:
            continue
        index_rows.append(
            {
                "submission_id": submission_id,
                "created_at": detail.get("createdAt"),
                "updated_at": detail.get("updatedAt"),
                "description": (detail.get("meta") or {}).get("description") or detail.get("description"),
                "kind": detail.get("kind"),
                "row_counts": dict(by_submission.get(submission_id) or Counter()),
            }
        )
    return {
        "record_type": "igp24_sair_submission_index",
        "created_at": utc_now(),
        "page_count": len(pages),
        "pages": pages,
        "submission_count": len(index_rows),
        "submissions": sorted(index_rows, key=lambda row: str(row.get("created_at") or ""), reverse=True),
        "rate_limit_observations": rate_limits,
    }


def build_sync_summary(
    *,
    competition: dict[str, Any],
    me: dict[str, Any],
    progress_summary: dict[str, Any],
    submission_index: dict[str, Any],
    submission_rows: list[dict[str, Any]],
    output_files: dict[str, str],
    command: list[str],
    live_fetch: bool,
    source_commit: str,
) -> dict[str, Any]:
    status_counts = Counter(str(row.get("status_class")) for row in submission_rows)
    pair_counts = Counter(str(row.get("pair_key")) for row in submission_rows if row.get("pair_key"))
    pending = [row for row in submission_rows if row.get("status_class") == "pending"]
    scoreable = [row for row in submission_rows if row.get("status_class") == "scoreable"]
    unmatched = [row for row in submission_rows if row.get("local_match_status") == "unmatched"]
    return {
        "schema_version": 1,
        "record_type": "igp24_sair_sync",
        "created_at": utc_now(),
        "tool": "scripts/igp24_sair_sync.py",
        "source_commit": source_commit,
        "command": command,
        "safety": {
            "api_key_recorded": False,
            "sair_submission": False,
            "network_calls": bool(live_fetch),
            "live_fetch": bool(live_fetch),
        },
        "api_endpoints_used": [
            "GET /api/public/v1/competitions/{competitionId}",
            "GET /api/public/v1/competitions/{competitionId}/me",
            "GET /api/public/v1/competitions/igp24/labels/progress",
            "GET /api/public/v1/competitions/{competitionId}/submissions/me",
            "GET /api/public/v1/competitions/{competitionId}/submissions/{submissionId}",
            "GET /api/public/v1/competitions/{competitionId}/submissions/{submissionId}/download",
        ],
        "post_submission_supported_but_not_used": "POST /api/public/v1/competitions/{competitionId}/submissions remains dry-run/explicit only",
        "competition": safe_compact(competition, max_depth=5),
        "me": safe_compact(me, max_depth=5),
        "progress": {
            "label_count": progress_summary["source_snapshot"].get("label_count"),
            "remaining_signature_count": progress_summary.get("remaining_signature_count"),
            "top_remaining_r_buckets": progress_summary.get("top_remaining_r_buckets"),
            "top_zero_team_remaining_labels": progress_summary.get("top_zero_team_remaining_labels")[:10],
        },
        "submissions": {
            "submission_count": submission_index.get("submission_count"),
            "row_count": len(submission_rows),
            "status_class_counts": dict(status_counts),
            "pair_count": len(pair_counts),
            "top_pair_counts": pair_counts.most_common(12),
            "pending_rows": len(pending),
            "scoreable_rows": len(scoreable),
            "failed_rows": status_counts.get("failed", 0),
            "unmatched_rows": len(unmatched),
        },
        "decision": {
            "submission_recommended_now": False,
            "submission_reason": "sync only; no generated queue passed score-aware and anti-basin submission gates",
            "wait_for_scoring_rows": len(pending),
            "review_scoreable_rows": len(scoreable),
        },
        "output_files": output_files,
    }


def build_report(summary: dict[str, Any]) -> str:
    progress = summary["progress"]
    submissions = summary["submissions"]
    decision = summary["decision"]
    lines = [
        "# IGP24 SAIR Sync",
        "",
        "## API Coverage",
        "",
    ]
    for endpoint in summary["api_endpoints_used"]:
        lines.append(f"- `{endpoint}`")
    lines.extend(
        [
            f"- `{summary['post_submission_supported_but_not_used']}`",
            "",
            "## Progress",
            "",
            f"- Labels: {progress.get('label_count')}",
            f"- Remaining signatures: {progress.get('remaining_signature_count')}",
            "",
            "| rank | r | remaining | discovered | allowed |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for rank, row in enumerate(progress.get("top_remaining_r_buckets") or [], start=1):
        lines.append(f"| {rank} | {row.get('r')} | {row.get('remaining')} | {row.get('discovered')} | {row.get('allowed')} |")
    lines.extend(
        [
            "",
            "## Submissions",
            "",
            f"- Submissions: {submissions.get('submission_count')}",
            f"- Rows: {submissions.get('row_count')}",
            f"- Pending rows: {submissions.get('pending_rows')}",
            f"- Scoreable rows: {submissions.get('scoreable_rows')}",
            f"- Failed rows: {submissions.get('failed_rows')}",
            f"- Unmatched rows: {submissions.get('unmatched_rows')}",
            f"- Status counts: `{json.dumps(submissions.get('status_class_counts'), sort_keys=True)}`",
            "",
            "## Decision",
            "",
            f"- Submission recommended now: `{decision.get('submission_recommended_now')}`",
            f"- Reason: {decision.get('submission_reason')}",
            f"- Wait-for-scoring rows: {decision.get('wait_for_scoring_rows')}",
            f"- Scoreable rows to review: {decision.get('review_scoreable_rows')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_sync_artifacts(
    *,
    output_dir: Path,
    competition: dict[str, Any],
    me: dict[str, Any],
    progress_snapshot: dict[str, Any],
    submission_index: dict[str, Any],
    submission_rows: list[dict[str, Any]],
    command: list[str],
    live_fetch: bool,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary_json": output_dir / SYNC_SUMMARY_JSON,
        "report_md": output_dir / SYNC_REPORT_MD,
        "progress_summary_json": output_dir / PROGRESS_SUMMARY_JSON,
        "label_progress_jsonl": output_dir / LABEL_PROGRESS_JSONL,
        "submission_index_json": output_dir / SUBMISSION_INDEX_JSON,
        "submission_rows_jsonl": output_dir / SUBMISSION_ROWS_JSONL,
        "pending_rows_jsonl": output_dir / PENDING_ROWS_JSONL,
        "scoreable_rows_jsonl": output_dir / SCOREABLE_ROWS_JSONL,
        "failed_rows_jsonl": output_dir / FAILED_ROWS_JSONL,
        "unmatched_rows_jsonl": output_dir / UNMATCHED_ROWS_JSONL,
    }
    output_files = {name: str(path) for name, path in paths.items()}
    progress_summary = build_progress_summary(progress_snapshot)
    pending_rows = [row for row in submission_rows if row.get("status_class") == "pending"]
    scoreable_rows = [row for row in submission_rows if row.get("status_class") == "scoreable"]
    failed_rows = [row for row in submission_rows if row.get("status_class") == "failed"]
    unmatched_rows = [row for row in submission_rows if row.get("local_match_status") == "unmatched"]
    summary = build_sync_summary(
        competition=competition,
        me=me,
        progress_summary=progress_summary,
        submission_index=submission_index,
        submission_rows=submission_rows,
        output_files=output_files,
        command=command,
        live_fetch=live_fetch,
        source_commit=get_source_commit(REPO_ROOT),
    )
    write_json(paths["progress_summary_json"], progress_summary)
    write_jsonl(paths["label_progress_jsonl"], label_progress_compact_rows(progress_snapshot))
    write_json(paths["submission_index_json"], submission_index)
    write_jsonl(paths["submission_rows_jsonl"], submission_rows)
    write_jsonl(paths["pending_rows_jsonl"], pending_rows)
    write_jsonl(paths["scoreable_rows_jsonl"], scoreable_rows)
    write_jsonl(paths["failed_rows_jsonl"], failed_rows)
    write_jsonl(paths["unmatched_rows_jsonl"], unmatched_rows)
    write_json(paths["summary_json"], summary)
    paths["report_md"].write_text(build_report(summary), encoding="utf-8")
    return paths


def load_sync_progress_snapshot(sync_dir: Path) -> dict[str, Any]:
    labels = read_jsonl(sync_dir / LABEL_PROGRESS_JSONL)
    progress_summary = read_json(sync_dir / PROGRESS_SUMMARY_JSON)
    source = progress_summary.get("source_snapshot") or {}
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": source.get("created_at") or progress_summary.get("created_at"),
        "query": {"source": str(sync_dir)},
        "page_count": source.get("page_count") or 0,
        "label_count": source.get("label_count") or len(labels),
        "pages": [
            {
                "generatedAt": source.get("first_generated_at"),
                "labels": len(labels),
                "nextCursorPresent": False,
                "meta": {"published": source.get("published")},
            }
        ],
        "labels": labels,
    }


def load_sync_submission_rows(sync_dir: Path) -> list[dict[str, Any]]:
    return read_jsonl(sync_dir / SUBMISSION_ROWS_JSONL)


def build_sync_from_live(
    *,
    output_dir: Path,
    api_key_env: str,
    base_url: str,
    progress_limit: int,
    submission_limit: int,
    local_data_root: Path,
    command: list[str],
) -> dict[str, Path]:
    client = SAIRAPIVerifier(api_key_env=api_key_env, base_url=base_url, dry_run=False)
    rate_limits: list[dict[str, Any]] = []
    competition = response_data(
        request_api(
            client,
            "GET",
            "/api/public/v1/competitions/igp24",
            endpoint="competition",
            rate_limits=rate_limits,
        )
    )
    me = response_data(
        request_api(
            client,
            "GET",
            "/api/public/v1/competitions/igp24/me",
            endpoint="competition/me",
            rate_limits=rate_limits,
        )
    )
    progress_snapshot = fetch_full_label_progress(client, limit=progress_limit, rate_limits=rate_limits)
    submission_summaries, pages = fetch_all_submission_summaries(client, limit=submission_limit, rate_limits=rate_limits)
    local_index = build_local_hash_index(local_data_root)
    details: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for item in submission_summaries:
        submission_id = str(item.get("submissionId") or item.get("id") or "")
        if not submission_id:
            continue
        detail = fetch_submission_detail(client, submission_id, rate_limits=rate_limits)
        details.append(detail)
        downloaded = download_submission_lines(client, submission_id, rate_limits=rate_limits)
        all_rows.extend(normalize_submission_rows(detail, downloaded, local_hash_index=local_index))
    submission_index = build_submission_index(
        submission_summaries=submission_summaries,
        submission_details=details,
        rows=all_rows,
        pages=pages,
        rate_limits=rate_limits,
    )
    return write_sync_artifacts(
        output_dir=output_dir,
        competition=competition,
        me=me,
        progress_snapshot=progress_snapshot,
        submission_index=submission_index,
        submission_rows=all_rows,
        command=command,
        live_fetch=True,
    )


def build_sync_from_existing(*, sync_dir: Path, output_dir: Path, command: list[str]) -> dict[str, Path]:
    progress_snapshot = load_sync_progress_snapshot(sync_dir)
    submission_index = read_json(sync_dir / SUBMISSION_INDEX_JSON)
    submission_rows = load_sync_submission_rows(sync_dir)
    summary = read_json(sync_dir / SYNC_SUMMARY_JSON)
    return write_sync_artifacts(
        output_dir=output_dir,
        competition=summary.get("competition") or {},
        me=summary.get("me") or {},
        progress_snapshot=progress_snapshot,
        submission_index=submission_index,
        submission_rows=submission_rows,
        command=command,
        live_fetch=False,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch_live", action="store_true")
    source.add_argument("--offline_sync_dir", type=Path)
    parser.add_argument("--api_key_env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--base_url", default="https://api.sair.foundation")
    parser.add_argument("--progress_limit", type=int, default=5000)
    parser.add_argument("--submission_limit", type=int, default=100)
    parser.add_argument("--local_data_root", type=Path, default=COMMITTED_DATA_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_sair_sync.py", *argv]
    try:
        if args.fetch_live:
            paths = build_sync_from_live(
                output_dir=args.output_dir,
                api_key_env=args.api_key_env,
                base_url=args.base_url,
                progress_limit=int(args.progress_limit),
                submission_limit=int(args.submission_limit),
                local_data_root=args.local_data_root,
                command=command,
            )
        else:
            paths = build_sync_from_existing(sync_dir=args.offline_sync_dir, output_dir=args.output_dir, command=command)
    except SAIRAPIError as exc:
        retry = f" retry_after={exc.retry_after}" if exc.retry_after else ""
        code = f" code={exc.code}" if exc.code else ""
        print(f"SAIR sync error:{code}{retry} {exc}", file=sys.stderr)
        return 2

    summary = read_json(paths["summary_json"])
    print(f"endpoint_count\t{len(summary['api_endpoints_used'])}")
    print(f"label_count\t{summary['progress']['label_count']}")
    print(f"remaining_signature_count\t{summary['progress']['remaining_signature_count']}")
    print(f"submission_count\t{summary['submissions']['submission_count']}")
    print(f"submission_row_count\t{summary['submissions']['row_count']}")
    print(f"pending_rows\t{summary['submissions']['pending_rows']}")
    print(f"scoreable_rows\t{summary['submissions']['scoreable_rows']}")
    print(f"unmatched_rows\t{summary['submissions']['unmatched_rows']}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
