"""Credential-safe SAIR Public API helper for IGP24.

The live API path reads credentials only from an environment variable. This
module never serializes the key, and dry-run submission validation is available
without a key.
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.igp24.verifiers.base import BaseVerifier, VerificationResult


DEFAULT_BASE_URL = "https://api.sair.foundation"
DEFAULT_COMPETITION_ID = "igp24"
DEFAULT_API_KEY_ENV = "SAIR_API_KEY"
DEFAULT_TIMEOUT_SECONDS = 30.0
IGP24_DEGREE = 24
IGP24_POLYNOMIAL_WIDTH = IGP24_DEGREE + 1
IGP24_DEFAULT_MAX_BODY_BYTES = 1_000_000


class SAIRAPIError(RuntimeError):
    """Raised when local validation or the SAIR API request fails."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        retry_after: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retry_after = retry_after


def parse_polynomial_line(value: str | Sequence[int], *, line_number: int | None = None) -> list[int]:
    """Parse one IGP24 coefficient row into 25 integers.

    Strings may be plain comma-separated SAIR lines or bracketed JSON integer
    lists. Bracketed inputs are normalized before submission because the SAIR
    Public API accepts coefficient-only strings.
    """

    prefix = f"line {line_number}: " if line_number is not None else ""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise SAIRAPIError(f"{prefix}blank polynomial line")
        if text.startswith("[") and text.endswith("]"):
            try:
                raw = json.loads(text)
            except json.JSONDecodeError as exc:
                raise SAIRAPIError(f"{prefix}invalid bracketed coefficient list") from exc
            if not isinstance(raw, list):
                raise SAIRAPIError(f"{prefix}bracketed coefficient input must be a list")
            parts = raw
        else:
            parts = [part.strip() for part in text.split(",")]
    else:
        parts = list(value)

    if len(parts) != IGP24_POLYNOMIAL_WIDTH:
        raise SAIRAPIError(
            f"{prefix}expected {IGP24_POLYNOMIAL_WIDTH} coefficients, got {len(parts)}"
        )

    coefficients: list[int] = []
    for index, item in enumerate(parts):
        try:
            if isinstance(item, str) and item.strip() == "":
                raise ValueError("empty integer field")
            coefficients.append(int(item))
        except (TypeError, ValueError) as exc:
            raise SAIRAPIError(f"{prefix}coefficient {index} is not an integer") from exc

    if coefficients[0] == 0:
        raise SAIRAPIError(f"{prefix}constant coefficient a_0 must be nonzero")
    if coefficients[-1] != 1:
        raise SAIRAPIError(f"{prefix}leading coefficient a_24 must be 1")

    gcd_value = 0
    for coefficient in coefficients:
        gcd_value = math.gcd(gcd_value, abs(coefficient))
    if gcd_value != 1:
        raise SAIRAPIError(f"{prefix}coefficient gcd must be 1, got {gcd_value}")

    return coefficients


def format_polynomial_line(value: str | Sequence[int], *, line_number: int | None = None) -> str:
    """Return one normalized SAIR coefficient-only submission string."""

    return ",".join(str(coefficient) for coefficient in parse_polynomial_line(value, line_number=line_number))


def load_polynomial_lines(path: str | Path) -> list[str]:
    """Load and normalize coefficient lines from a text file.

    Full-line and trailing comments are stripped for local convenience, but the
    returned strings contain no comments because the Public API accepts JSON
    polynomial strings only.
    """

    polynomials: list[str] = []
    for line_number, raw_line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        polynomials.append(format_polynomial_line(line, line_number=line_number))
    if not polynomials:
        raise SAIRAPIError(f"no polynomial lines found in {path}")
    return polynomials


def submission_body_size(polynomials: Sequence[str]) -> int:
    """Measure the canonical raw submission body size in bytes."""

    return "\n".join(polynomials).encode("utf-8").__len__()


class SAIRAPIVerifier(BaseVerifier):
    """Small stdlib SAIR API client with dry-run submission support."""

    status_name = "sair_verified"

    def __init__(
        self,
        api_key_env: str = DEFAULT_API_KEY_ENV,
        dry_run: bool = True,
        *,
        base_url: str = DEFAULT_BASE_URL,
        competition_id: str = DEFAULT_COMPETITION_ID,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        opener: Any | None = None,
    ) -> None:
        self.api_key_env = api_key_env
        self.dry_run = dry_run
        self.base_url = base_url.rstrip("/")
        self.competition_id = competition_id
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen

    def _api_key_present(self) -> bool:
        return bool(os.environ.get(self.api_key_env))

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise SAIRAPIError(f"missing {self.api_key_env}; set it in the environment for live SAIR API calls")
        return key

    def is_available(self) -> bool:
        return self._api_key_present()

    def verify(self, coefficients: Sequence[int]) -> VerificationResult:
        _ = parse_polynomial_line(list(coefficients) + [1] if len(coefficients) == IGP24_DEGREE else coefficients)
        return VerificationResult(status="unverified", message="SAIR verifies only through submission batches")

    def _competition_path(self, suffix: str = "") -> str:
        return f"/api/public/v1/competitions/{self.competition_id}{suffix}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str | int | bool | Sequence[str]] | None = None,
        body: Mapping[str, Any] | None = None,
        accept: str = "application/json",
    ) -> tuple[Any, Mapping[str, str]]:
        query_items: list[tuple[str, str]] = []
        for key, value in (query or {}).items():
            if isinstance(value, bool):
                query_items.append((key, str(value).lower()))
            elif isinstance(value, (list, tuple)):
                query_items.extend((key, str(item)) for item in value)
            else:
                query_items.append((key, str(value)))
        query_string = urllib.parse.urlencode(query_items)
        url = f"{self.base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        data = None
        headers = {
            "Accept": accept,
            "Authorization": f"Bearer {self._api_key()}",
        }
        if body is not None:
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read()
                response_headers = dict(response.headers.items())
                if accept == "text/plain":
                    return raw.decode("utf-8"), response_headers
                if not raw:
                    return {}, response_headers
                return json.loads(raw.decode("utf-8")), response_headers
        except urllib.error.HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            code = None
            message = f"SAIR API returned HTTP {exc.code}"
            raw = exc.read()
            if raw:
                try:
                    payload = json.loads(raw.decode("utf-8"))
                    error = payload.get("error") if isinstance(payload, dict) else None
                    if isinstance(error, dict):
                        code = str(error.get("code") or "") or None
                        message = str(error.get("message") or message)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
            raise SAIRAPIError(message, status=exc.code, code=code, retry_after=retry_after) from exc
        except urllib.error.URLError as exc:
            raise SAIRAPIError(f"SAIR API request failed: {exc.reason}") from exc

    def get_competition(self) -> Any:
        payload, _headers = self._request("GET", self._competition_path())
        return payload

    def get_me(self) -> Any:
        payload, _headers = self._request("GET", self._competition_path("/me"))
        return payload

    def get_label_progress(
        self,
        *,
        labels: Sequence[str] | None = None,
        include_empty: bool = True,
        limit: int = 5000,
        cursor: str | None = None,
    ) -> Any:
        query: dict[str, str | int | bool] = {"limit": limit, "includeEmpty": include_empty}
        if labels:
            query["labels"] = ",".join(labels)
        if cursor:
            query["cursor"] = cursor
        payload, _headers = self._request(
            "GET",
            "/api/public/v1/competitions/igp24/labels/progress",
            query=query,
        )
        return payload

    def iter_label_progress(
        self,
        *,
        labels: Sequence[str] | None = None,
        include_empty: bool = True,
        limit: int = 5000,
    ) -> Iterable[dict[str, Any]]:
        cursor: str | None = None
        while True:
            payload = self.get_label_progress(labels=labels, include_empty=include_empty, limit=limit, cursor=cursor)
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            for row in data.get("labels", []):
                yield row
            cursor = data.get("nextCursor")
            if not cursor:
                break

    def list_my_submissions(self, *, limit: int = 100, cursor: str | None = None) -> Any:
        query: dict[str, str | int] = {"limit": limit}
        if cursor:
            query["cursor"] = cursor
        payload, _headers = self._request("GET", self._competition_path("/submissions/me"), query=query)
        return payload

    def get_submission(self, submission_id: str) -> Any:
        payload, _headers = self._request("GET", self._competition_path(f"/submissions/{submission_id}"))
        return payload

    def download_submission(self, submission_id: str) -> str:
        payload, _headers = self._request(
            "GET",
            self._competition_path(f"/submissions/{submission_id}/download"),
            accept="text/plain",
        )
        return str(payload)

    def submit_polynomials(
        self,
        polynomials: Sequence[str | Sequence[int]],
        *,
        description: str | None = None,
        dry_run: bool | None = None,
        max_body_bytes: int = IGP24_DEFAULT_MAX_BODY_BYTES,
    ) -> Any:
        normalized = [format_polynomial_line(line, line_number=index) for index, line in enumerate(polynomials, start=1)]
        if not normalized:
            raise SAIRAPIError("at least one polynomial is required")
        body_size = submission_body_size(normalized)
        if body_size > max_body_bytes:
            raise SAIRAPIError(f"submission body is {body_size} bytes, above limit {max_body_bytes}")

        should_dry_run = self.dry_run if dry_run is None else dry_run
        request_body: dict[str, Any] = {"payload": {"polynomials": normalized}}
        if description:
            if len(description) > 500:
                raise SAIRAPIError("meta.description must be 500 characters or fewer")
            request_body["meta"] = {"description": description}

        if should_dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "polynomial_count": len(normalized),
                "body_bytes": body_size,
                "would_post": self._competition_path("/submissions"),
            }

        payload, headers = self._request("POST", self._competition_path("/submissions"), body=request_body)
        if isinstance(payload, dict):
            payload = dict(payload)
            payload["_rate_limit_headers"] = {
                key: value
                for key, value in headers.items()
                if key.lower().startswith("x-ratelimit") or key.lower() == "retry-after"
            }
        return payload

    def submit(self, records: Iterable[dict], submit: bool = False) -> VerificationResult:
        polynomials: list[str] = []
        for index, record in enumerate(records, start=1):
            exported = record.get("exported_coefficients") or record.get("coefficients")
            if exported is None:
                return VerificationResult(status="unverified", message=f"record {index} has no coefficient export")
            polynomials.append(format_polynomial_line(exported, line_number=index))
        result = self.submit_polynomials(polynomials, dry_run=(self.dry_run or not submit))
        mode = "dry-run only" if result.get("dry_run") else "submitted"
        return VerificationResult(status="unverified", message=f"{mode}; processed {len(polynomials)} records")

    def export_batch_without_submission(self, records: Iterable[dict], path: str | Path) -> Path:
        return self.export_batch(records, path)
