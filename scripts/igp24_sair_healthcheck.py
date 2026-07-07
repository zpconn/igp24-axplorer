#!/usr/bin/env python3
"""Read-only SAIR IGP24 endpoint health check.

This helper probes only lightweight GET endpoints. It never submits
polynomials, never prints the API key, and writes compact artifacts suitable
for deciding whether a full sync should be retried.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.igp24_shortlist import get_source_commit  # noqa: E402
from src.igp24.verifiers.sair_api import (  # noqa: E402
    DEFAULT_API_KEY_ENV,
    DEFAULT_BASE_URL,
    SAIRAPIError,
    SAIRAPIVerifier,
)


HEALTH_JSON = "sair_healthcheck.json"
HEALTH_REPORT_MD = "sair_healthcheck_report.md"

HEALTH_ENDPOINTS = [
    {
        "name": "competition_schema",
        "method": "GET",
        "path": "/api/public/v1/competitions/igp24",
        "query": {},
    },
    {
        "name": "competition_me",
        "method": "GET",
        "path": "/api/public/v1/competitions/igp24/me",
        "query": {},
    },
    {
        "name": "labels_progress_limit_1",
        "method": "GET",
        "path": "/api/public/v1/competitions/igp24/labels/progress",
        "query": {"limit": 1, "includeEmpty": True},
    },
    {
        "name": "submissions_me_limit_1",
        "method": "GET",
        "path": "/api/public/v1/competitions/igp24/submissions/me",
        "query": {"limit": 1},
    },
]

SECRET_SHAPED_RE = re.compile(r"sair_[0-9a-f]{12}_[A-Za-z0-9]{20,}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    for part in command:
        redacted.append(SECRET_SHAPED_RE.sub("[redacted-sair-key]", str(part)))
    return redacted


def compact_payload_summary(payload: Any) -> dict[str, Any]:
    data = response_data(payload)
    summary: dict[str, Any] = {}
    if "competitionId" in data:
        summary["competitionId"] = data.get("competitionId")
    if "id" in data:
        summary["id"] = data.get("id")
    if "submissionSpec" in data:
        spec = data.get("submissionSpec") or {}
        summary["submissionSpec"] = {
            "kind": spec.get("kind"),
            "limits": spec.get("limits"),
            "permission": spec.get("permission"),
        }
    if "generatedAt" in data:
        summary["generatedAt"] = data.get("generatedAt")
    if "labels" in data:
        summary["labels"] = len(data.get("labels") or [])
    if "items" in data:
        summary["items"] = len(data.get("items") or [])
    if "submissions" in data:
        summary["submissions"] = len(data.get("submissions") or [])
    if "nextCursor" in data:
        summary["nextCursorPresent"] = bool(data.get("nextCursor"))
    if "meta" in data:
        meta = data.get("meta") or {}
        summary["meta"] = {
            "published": meta.get("published"),
            "publishedAt": meta.get("publishedAt"),
        }
    return summary


def classify_error(exc: SAIRAPIError) -> str:
    message = str(exc)
    code = str(exc.code or "")
    if code == "IGP24_SERVICE_UNAVAILABLE":
        return "service_unavailable"
    if exc.status in {401, 403}:
        return "auth_failure"
    if "missing " in message and "API_KEY" in message:
        return "auth_failure"
    if "auth" in code.lower() or "api_key" in code.lower() or "token" in code.lower():
        return "auth_failure"
    if message.startswith("SAIR API request failed:"):
        return "network_failure"
    if exc.status == 429:
        return "rate_limited"
    if exc.status is not None:
        return "http_error"
    return "unknown_error"


def check_endpoint(client: SAIRAPIVerifier, endpoint: dict[str, Any]) -> dict[str, Any]:
    try:
        payload, headers = client._request(  # noqa: SLF001 - health check needs response headers.
            endpoint["method"],
            endpoint["path"],
            query=endpoint.get("query") or None,
        )
        return {
            "name": endpoint["name"],
            "method": endpoint["method"],
            "path": endpoint["path"],
            "query": endpoint.get("query") or {},
            "status": "ok",
            "classification": "ok",
            "rate_limit_headers": rate_limit_headers(headers),
            "payload_summary": compact_payload_summary(payload),
        }
    except SAIRAPIError as exc:
        return {
            "name": endpoint["name"],
            "method": endpoint["method"],
            "path": endpoint["path"],
            "query": endpoint.get("query") or {},
            "status": "error",
            "classification": classify_error(exc),
            "http_status": exc.status,
            "error_code": exc.code,
            "retry_after": exc.retry_after,
            "message": str(exc),
            "rate_limit_headers": {},
        }


def build_healthcheck(
    *,
    client: SAIRAPIVerifier,
    command: list[str],
    endpoints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    checks = [check_endpoint(client, endpoint) for endpoint in (endpoints or HEALTH_ENDPOINTS)]
    counts: dict[str, int] = {}
    for row in checks:
        counts[str(row["classification"])] = counts.get(str(row["classification"]), 0) + 1
    all_ok = all(row["classification"] == "ok" for row in checks)
    service_unavailable = [row["name"] for row in checks if row["classification"] == "service_unavailable"]
    return {
        "schema_version": 1,
        "record_type": "igp24_sair_healthcheck",
        "created_at": utc_now(),
        "tool": "scripts/igp24_sair_healthcheck.py",
        "source_commit": get_source_commit(REPO_ROOT),
        "command": redact_command(command),
        "safety": {
            "read_only": True,
            "sair_submission": False,
            "api_key_recorded": False,
        },
        "summary": {
            "endpoint_count": len(checks),
            "all_ok": all_ok,
            "classification_counts": counts,
            "service_unavailable_endpoints": service_unavailable,
            "full_sync_recommended": all_ok,
            "submission_recommended_now": False,
        },
        "checks": checks,
    }


def build_report(health: dict[str, Any]) -> str:
    summary = health["summary"]
    lines = [
        "# IGP24 SAIR Health Check",
        "",
        f"- All endpoints OK: `{summary.get('all_ok')}`",
        f"- Full sync recommended: `{summary.get('full_sync_recommended')}`",
        f"- Submission recommended now: `{summary.get('submission_recommended_now')}`",
        f"- Classification counts: `{json.dumps(summary.get('classification_counts'), sort_keys=True)}`",
        "",
        "| endpoint | classification | error code | retry after |",
        "| --- | --- | --- | --- |",
    ]
    for row in health.get("checks") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("name")),
                    str(row.get("classification")),
                    str(row.get("error_code")),
                    str(row.get("retry_after")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_health_artifacts(health: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "health_json": output_dir / HEALTH_JSON,
        "report_md": output_dir / HEALTH_REPORT_MD,
    }
    paths["health_json"].write_text(json.dumps(health, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    paths["report_md"].write_text(build_report(health), encoding="utf-8")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api_key_env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--base_url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--output_dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = [sys.executable, *sys.argv] if argv is None else [sys.executable, "scripts/igp24_sair_healthcheck.py", *argv]
    client = SAIRAPIVerifier(
        api_key_env=args.api_key_env,
        base_url=args.base_url,
        timeout=args.timeout,
        dry_run=True,
    )
    health = build_healthcheck(client=client, command=command)
    if args.output_dir:
        paths = write_health_artifacts(health, args.output_dir)
        for name, path in paths.items():
            print(f"{name}\t{path}")
    print(f"all_ok\t{health['summary']['all_ok']}")
    print(f"classification_counts\t{json.dumps(health['summary']['classification_counts'], sort_keys=True)}")
    print(f"service_unavailable_endpoints\t{json.dumps(health['summary']['service_unavailable_endpoints'])}")
    print(f"full_sync_recommended\t{health['summary']['full_sync_recommended']}")
    print("submission_recommended_now\tFalse")
    return 0 if health["summary"]["all_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
