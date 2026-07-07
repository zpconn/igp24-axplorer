import json

from scripts.igp24_sair_healthcheck import (
    HEALTH_ENDPOINTS,
    build_healthcheck,
    classify_error,
    write_health_artifacts,
)
from src.igp24.verifiers.sair_api import SAIRAPIError


class FakeHealthClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _request(self, method, path, *, query=None, body=None, accept="application/json"):
        self.calls.append((method, path, query, body, accept))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_error_classification_distinguishes_expected_modes():
    assert (
        classify_error(SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE"))
        == "service_unavailable"
    )
    assert classify_error(SAIRAPIError("SAIR API request failed: [Errno -3] Temporary failure")) == "network_failure"
    assert classify_error(SAIRAPIError("missing SAIR_API_KEY; set it", code=None)) == "auth_failure"
    assert classify_error(SAIRAPIError("forbidden", status=403, code="FORBIDDEN")) == "auth_failure"
    assert classify_error(SAIRAPIError("too many", status=429, code="RATE_LIMITED")) == "rate_limited"


def test_healthcheck_uses_only_read_endpoints_and_compacts_success_payloads():
    client = FakeHealthClient(
        [
            ({"ok": True, "data": {"competitionId": "igp24", "submissionSpec": {"kind": "igp24-polynomial"}}}, {}),
            ({"ok": True, "data": {"id": "team_test"}}, {}),
            (
                {
                    "ok": True,
                    "data": {
                        "generatedAt": "2026-07-07T00:00:00Z",
                        "labels": [{"label": "24T1"}],
                        "nextCursor": "next",
                        "meta": {"published": True},
                    },
                },
                {"X-RateLimit-Remaining": "999"},
            ),
            ({"ok": True, "data": {"items": [{"submissionId": "sub_test"}], "nextCursor": None}}, {}),
        ]
    )

    health = build_healthcheck(client=client, command=["pytest"])

    assert health["summary"]["all_ok"] is True
    assert health["summary"]["full_sync_recommended"] is True
    assert health["summary"]["classification_counts"] == {"ok": 4}
    assert all(call[0] == "GET" for call in client.calls)
    assert all(call[3] is None for call in client.calls)
    assert client.calls[2][2] == {"limit": 1, "includeEmpty": True}
    assert client.calls[3][2] == {"limit": 1}
    assert health["checks"][2]["payload_summary"]["labels"] == 1
    assert health["checks"][2]["payload_summary"]["nextCursorPresent"] is True


def test_healthcheck_records_service_unavailable_endpoints_and_artifact_has_no_secret(tmp_path):
    secret = "sair_0123456789ab_" + "abcdefghijklmnopqrstuvwxyz"
    client = FakeHealthClient(
        [
            ({"ok": True, "data": {"competitionId": "igp24"}}, {}),
            SAIRAPIError("service unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE"),
            SAIRAPIError("service unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE"),
            SAIRAPIError("service unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE"),
        ]
    )

    health = build_healthcheck(client=client, command=["pytest", "--token", secret], endpoints=HEALTH_ENDPOINTS)
    paths = write_health_artifacts(health, tmp_path)
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths.values())
    saved = json.loads(paths["health_json"].read_text(encoding="utf-8"))

    assert health["summary"]["all_ok"] is False
    assert health["summary"]["full_sync_recommended"] is False
    assert health["summary"]["classification_counts"] == {"ok": 1, "service_unavailable": 3}
    assert health["summary"]["service_unavailable_endpoints"] == [
        "competition_me",
        "labels_progress_limit_1",
        "submissions_me_limit_1",
    ]
    assert saved["safety"]["api_key_recorded"] is False
    assert secret not in text
