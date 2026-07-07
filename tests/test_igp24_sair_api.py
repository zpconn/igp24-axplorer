import json
import urllib.parse

import pytest

from src.igp24.verifiers.sair_api import (
    SAIRAPIError,
    SAIRAPIVerifier,
    format_polynomial_line,
    load_polynomial_lines,
    parse_polynomial_line,
)


VALID_LINE = "2,0,-3,0,1,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,2,0,-3,0,1"


class FakeResponse:
    def __init__(self, payload, headers=None):
        self._payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        if isinstance(self._payload, str):
            return self._payload.encode("utf-8")
        return self._payload


def test_polynomial_line_validation_and_normalization(tmp_path):
    bracketed = "[" + VALID_LINE + "]"
    assert parse_polynomial_line(bracketed) == parse_polynomial_line(VALID_LINE)
    assert format_polynomial_line(bracketed) == VALID_LINE

    path = tmp_path / "rows.txt"
    path.write_text(f"# comment\n{bracketed} # trailing comment\n\n", encoding="utf-8")
    assert load_polynomial_lines(path) == [VALID_LINE]

    with pytest.raises(SAIRAPIError, match="constant coefficient"):
        parse_polynomial_line("0," + ",".join(["0"] * 23) + ",1")
    with pytest.raises(SAIRAPIError, match="leading coefficient"):
        parse_polynomial_line("2," + ",".join(["0"] * 23) + ",2")
    with pytest.raises(SAIRAPIError, match="expected 25 coefficients"):
        parse_polynomial_line("1,2,3")


def test_dry_run_submission_validates_without_api_key(monkeypatch):
    monkeypatch.delenv("SAIR_API_KEY", raising=False)
    client = SAIRAPIVerifier(dry_run=True)

    payload = client.submit_polynomials([VALID_LINE], description="pytest dry run")

    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["polynomial_count"] == 1
    assert payload["would_post"].endswith("/submissions")


def test_empty_submission_is_rejected_locally():
    client = SAIRAPIVerifier(dry_run=True)

    with pytest.raises(SAIRAPIError, match="at least one polynomial"):
        client.submit_polynomials([])


def test_live_submission_requires_api_key(monkeypatch):
    monkeypatch.delenv("SAIR_API_KEY", raising=False)
    client = SAIRAPIVerifier(dry_run=False)

    with pytest.raises(SAIRAPIError, match="missing SAIR_API_KEY"):
        client.submit_polynomials([VALID_LINE], dry_run=False)


def test_live_submission_posts_json_without_serializing_secret(monkeypatch):
    monkeypatch.setenv("SAIR_API_KEY", "test_secret_token")
    captured = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(
            '{"ok":true,"data":{"submissionId":"sub_test"}}',
            headers={"X-RateLimit-Remaining": "999"},
        )

    client = SAIRAPIVerifier(base_url="https://api.test", dry_run=False, opener=opener, timeout=7.5)
    payload = client.submit_polynomials([VALID_LINE], description="pytest live path", dry_run=False)

    assert captured["url"] == "https://api.test/api/public/v1/competitions/igp24/submissions"
    assert captured["timeout"] == 7.5
    assert captured["headers"]["Authorization"] == "Bearer test_secret_token"
    assert captured["headers"]["User-agent"] == "igp24-axplorer/0.1"
    assert captured["body"] == {
        "payload": {"polynomials": [VALID_LINE]},
        "meta": {"description": "pytest live path"},
    }
    assert payload["ok"] is True
    assert payload["_rate_limit_headers"] == {"X-RateLimit-Remaining": "999"}


def test_label_progress_uses_documented_filter_parameters(monkeypatch):
    monkeypatch.setenv("SAIR_API_KEY", "test_secret_token")
    captured = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse('{"ok":true,"data":{"labels":[],"nextCursor":null}}')

    client = SAIRAPIVerifier(base_url="https://api.test", dry_run=False, opener=opener)
    payload = client.get_label_progress(labels=["24T23883", "24T24651"], include_empty=False, limit=250)

    parsed = urllib.parse.urlparse(captured["url"])
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.path == "/api/public/v1/competitions/igp24/labels/progress"
    assert query["labels"] == ["24T23883,24T24651"]
    assert query["includeEmpty"] == ["false"]
    assert query["limit"] == ["250"]
    assert payload["ok"] is True
