import json

from scripts.igp24_sair_sync import (
    build_local_hash_index,
    build_progress_summary,
    build_sync_from_client,
    build_sync_from_existing,
    build_submission_index,
    build_sync_summary,
    canonical_hash_from_polynomial_line,
    fetch_all_submission_summaries,
    fetch_full_label_progress,
    load_sync_progress_snapshot,
    load_sync_status,
    normalize_submission_rows,
    request_api,
    write_sync_artifacts,
)
from src.igp24.verifiers.sair_api import SAIRAPIError


LINE_A = "2,0,-3,0,1,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,2,0,-3,0,1"
LINE_B = "3,0,0,0,0,0,2,0,0,0,0,0,-4,0,0,0,0,0,-2,0,0,0,0,-1,1"


class FakeClient:
    def __init__(self):
        self.calls = []

    def _request(self, method, path, *, query=None, body=None, accept="application/json"):
        self.calls.append((method, path, query, accept))
        headers = {"X-RateLimit-Remaining": "999"}
        if path.endswith("/labels/progress"):
            cursor = (query or {}).get("cursor")
            if not cursor:
                return (
                    {
                        "ok": True,
                        "data": {
                            "generatedAt": "2026-07-07T00:00:00Z",
                            "labels": [
                                {
                                    "label": "24T1",
                                    "t": 1,
                                    "allowedR": [8, 24],
                                    "teamCount": 0,
                                    "minimumDiscAbs": None,
                                    "discoveredSignatures": [],
                                    "remainingSignatures": [8, 24],
                                    "signatures": [
                                        {"r": 8, "teamCount": 0, "minimumDiscAbs": None, "discovered": False},
                                        {"r": 24, "teamCount": 0, "minimumDiscAbs": None, "discovered": False},
                                    ],
                                }
                            ],
                            "nextCursor": "next",
                            "meta": {"published": True},
                        },
                    },
                    headers,
                )
            return (
                {
                    "ok": True,
                    "data": {
                        "generatedAt": "2026-07-07T00:00:01Z",
                        "labels": [
                            {
                                "label": "24T9993",
                                "t": 9993,
                                "allowedR": [8],
                                "teamCount": 10,
                                "minimumDiscAbs": "1000",
                                "discoveredSignatures": [8],
                                "remainingSignatures": [],
                                "signatures": [
                                    {"r": 8, "teamCount": 10, "minimumDiscAbs": "1000", "discovered": True}
                                ],
                            }
                        ],
                        "nextCursor": None,
                        "meta": {"published": True},
                    },
                },
                headers,
            )
        if path.endswith("/submissions/me"):
            cursor = (query or {}).get("cursor")
            items = [{"submissionId": "sub_a"}] if not cursor else [{"submissionId": "sub_b"}]
            return ({"ok": True, "data": {"items": items, "nextCursor": None if cursor else "next"}}, headers)
        raise AssertionError(path)


class FailingClient:
    def _request(self, method, path, *, query=None, body=None, accept="application/json"):
        raise SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE")


class LiveSyncFakeClient:
    def __init__(self, *, fail_at=None):
        self.fail_at = fail_at
        self.calls = []

    def _request(self, method, path, *, query=None, body=None, accept="application/json"):
        self.calls.append((method, path, query, accept))
        headers = {"X-RateLimit-Remaining": "999"}
        if path == "/api/public/v1/competitions/igp24":
            return ({"ok": True, "data": {"competitionId": "igp24", "submissionSpec": {"kind": "igp24-polynomial"}}}, headers)
        if path == "/api/public/v1/competitions/igp24/me":
            return ({"ok": True, "data": {"competitionId": "igp24", "team": {"role": "activeMember"}}}, headers)
        if path == "/api/public/v1/competitions/igp24/labels/progress":
            progress = _progress_snapshot()
            return (
                {
                    "ok": True,
                    "data": {
                        "generatedAt": "2026-07-07T00:00:00Z",
                        "labels": progress["labels"],
                        "nextCursor": None,
                        "meta": {"published": True},
                    },
                },
                headers,
            )
        if path == "/api/public/v1/competitions/igp24/submissions/me":
            if self.fail_at == "submissions/me":
                raise SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE")
            return ({"ok": True, "data": {"items": [{"submissionId": "sub_a"}], "nextCursor": None}}, headers)
        if path == "/api/public/v1/competitions/igp24/submissions/sub_a/download":
            if self.fail_at == "submissions/{id}/download":
                raise SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE")
            return (LINE_A, headers)
        if path == "/api/public/v1/competitions/igp24/submissions/sub_a":
            if self.fail_at == "submissions/{id}":
                raise SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE")
            return ({"ok": True, "data": _detail()}, headers)
        raise AssertionError(path)


class MultiSubmissionPartialClient(LiveSyncFakeClient):
    def __init__(self, *, fail_detail=None, fail_download=None):
        super().__init__()
        self.fail_detail = fail_detail
        self.fail_download = fail_download

    def _request(self, method, path, *, query=None, body=None, accept="application/json"):
        self.calls.append((method, path, query, accept))
        headers = {"X-RateLimit-Remaining": "999"}
        if path == "/api/public/v1/competitions/igp24":
            return ({"ok": True, "data": {"competitionId": "igp24", "submissionSpec": {"kind": "igp24-polynomial"}}}, headers)
        if path == "/api/public/v1/competitions/igp24/me":
            return ({"ok": True, "data": {"competitionId": "igp24", "team": {"role": "activeMember"}}}, headers)
        if path == "/api/public/v1/competitions/igp24/labels/progress":
            progress = _progress_snapshot()
            return (
                {
                    "ok": True,
                    "data": {
                        "generatedAt": "2026-07-07T00:00:00Z",
                        "labels": progress["labels"],
                        "nextCursor": None,
                        "meta": {"published": True},
                    },
                },
                headers,
            )
        if path == "/api/public/v1/competitions/igp24/submissions/me":
            return (
                {
                    "ok": True,
                    "data": {"items": [{"submissionId": "sub_a"}, {"submissionId": "sub_b"}], "nextCursor": None},
                },
                headers,
            )
        for submission_id, line in {"sub_a": LINE_A, "sub_b": LINE_B}.items():
            if path == f"/api/public/v1/competitions/igp24/submissions/{submission_id}":
                if self.fail_detail == submission_id:
                    raise SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE")
                return ({"ok": True, "data": _detail(submission_id=submission_id)}, headers)
            if path == f"/api/public/v1/competitions/igp24/submissions/{submission_id}/download":
                if self.fail_download == submission_id:
                    raise SAIRAPIError("temporarily unavailable", status=503, code="IGP24_SERVICE_UNAVAILABLE")
                return (line, headers)
        raise AssertionError(path)


def _detail(*, submission_id="sub_a"):
    return {
        "submissionId": submission_id,
        "competitionId": "igp24",
        "createdAt": "2026-07-07T00:00:02Z",
        "updatedAt": "2026-07-07T00:00:03Z",
        "kind": "igp24-polynomial",
        "meta": {"description": "pytest"},
        "verifiedPolynomials": [
            {
                "polynomialIndex": 0,
                "status": "accepted",
                "label": "24T9993",
                "t": 9993,
                "r": 8,
                "scoreable": True,
                "scoringStatus": "scoreable",
                "fieldDiscAbs": "900",
                "discSource": "exact_nfdisc",
                "inBaseline": False,
                "baselineUnlocked": False,
            }
        ],
        "failedPolynomials": [{"polynomialIndex": 1, "status": "failed", "reason": "bad"}],
        "payload": {"queuedPolynomials": [{"polynomialIndex": 2, "status": "queued"}]},
    }


def _progress_snapshot():
    return {
        "record_type": "igp24_sair_label_progress_snapshot",
        "created_at": "2026-07-07T00:00:00Z",
        "page_count": 1,
        "label_count": 1,
        "pages": [{"generatedAt": "2026-07-07T00:00:00Z", "labels": 1, "meta": {"published": True}}],
        "labels": [
            {
                "label": "24T1",
                "t": 1,
                "allowedR": [24],
                "teamCount": 0,
                "minimumDiscAbs": None,
                "discoveredSignatures": [],
                "remainingSignatures": [24],
                "signatures": [{"r": 24, "teamCount": 0, "minimumDiscAbs": None, "discovered": False}],
            }
        ],
    }


def test_fetch_full_progress_and_submission_pages_are_paginated():
    client = FakeClient()
    rate_limits = []

    progress = fetch_full_label_progress(client, limit=1, rate_limits=rate_limits)
    submissions, pages = fetch_all_submission_summaries(client, limit=1, rate_limits=rate_limits)

    assert progress["label_count"] == 2
    assert progress["page_count"] == 2
    assert [row["submissionId"] for row in submissions] == ["sub_a", "sub_b"]
    assert len(pages) == 2
    assert len(rate_limits) == 4


def test_request_api_includes_endpoint_context_on_failure():
    try:
        request_api(
            FailingClient(),
            "GET",
            "/api/public/v1/competitions/igp24/submissions/sub_test",
            endpoint="submissions/{id}",
            rate_limits=[],
        )
    except SAIRAPIError as exc:
        assert exc.code == "IGP24_SERVICE_UNAVAILABLE"
        assert str(exc) == "submissions/{id}: temporarily unavailable"
    else:
        raise AssertionError("expected SAIRAPIError")


def test_submission_detail_download_join_matches_known_hash_and_retains_unmatched(tmp_path):
    known_hash, _line, _coeffs = canonical_hash_from_polynomial_line(LINE_A)
    local_jsonl = tmp_path / "candidate.jsonl"
    local_jsonl.write_text(json.dumps({"canonical_hash": known_hash, "exported_coefficients": [int(x) for x in LINE_A.split(",")]}) + "\n")
    local_index = build_local_hash_index(tmp_path)

    rows = normalize_submission_rows(_detail(), [LINE_A, LINE_B, LINE_A], local_hash_index=local_index)

    assert rows[0]["local_match_status"] == "matched"
    assert rows[0]["status_class"] == "scoreable"
    assert rows[0]["pair_key"] == "24T9993|r=8"
    assert rows[1]["local_match_status"] == "unmatched"
    assert rows[1]["status_class"] == "failed"
    assert rows[2]["status_class"] == "pending"


def test_write_sync_artifacts_keeps_unmatched_rows_and_no_secret(tmp_path):
    rows = normalize_submission_rows(_detail(), [LINE_A, LINE_B], local_hash_index={})
    index = build_submission_index(
        submission_summaries=[{"submissionId": "sub_a"}],
        submission_details=[_detail()],
        rows=rows,
        pages=[{"items": 1}],
        rate_limits=[{"endpoint": "pytest", "headers": {"X-RateLimit-Remaining": "999"}}],
    )

    paths = write_sync_artifacts(
        output_dir=tmp_path / "sync",
        competition={"submissionSpec": {"limits": {"maxPolynomials": 1000}}, "api_key": "should redact"},
        me={"team": {"role": "activeMember"}},
        progress_snapshot=_progress_snapshot(),
        submission_index=index,
        submission_rows=rows,
        command=["pytest"],
        live_fetch=True,
    )

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    unmatched = [json.loads(line) for line in paths["unmatched_rows_jsonl"].read_text(encoding="utf-8").splitlines()]
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in paths.values())

    assert summary["safety"]["api_key_recorded"] is False
    assert summary["competition"]["api_key"] == "[redacted]"
    assert len(unmatched) == 2
    assert "should redact" not in all_text
    assert build_progress_summary(_progress_snapshot())["remaining_signature_count"] == 1


def test_offline_sync_replays_saved_artifact_without_live_fetch(tmp_path):
    rows = normalize_submission_rows(_detail(), [LINE_A], local_hash_index={})
    index = build_submission_index(
        submission_summaries=[{"submissionId": "sub_a"}],
        submission_details=[_detail()],
        rows=rows,
        pages=[{"items": 1}],
        rate_limits=[],
    )
    paths = write_sync_artifacts(
        output_dir=tmp_path / "sync",
        competition={"submissionSpec": {"limits": {"maxPolynomials": 1000}}},
        me={"team": {"role": "activeMember"}},
        progress_snapshot=_progress_snapshot(),
        submission_index=index,
        submission_rows=rows,
        command=["pytest"],
        live_fetch=True,
    )

    replayed = build_sync_from_existing(sync_dir=paths["summary_json"].parent, output_dir=tmp_path / "replay", command=["pytest", "replay"])
    summary = json.loads(replayed["summary_json"].read_text(encoding="utf-8"))
    snapshot = load_sync_progress_snapshot(replayed["summary_json"].parent)

    assert summary["safety"]["live_fetch"] is False
    assert summary["progress"]["label_count"] == 1
    assert snapshot["labels"][0]["label"] == "24T1"


def test_live_sync_from_client_writes_complete_artifacts_when_all_endpoints_succeed(tmp_path):
    paths = build_sync_from_client(
        client=LiveSyncFakeClient(),
        output_dir=tmp_path / "sync",
        progress_limit=5000,
        submission_limit=100,
        local_data_root=tmp_path / "data",
        command=["pytest"],
        allow_partial=False,
        live_fetch=True,
    )
    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    status = load_sync_status(paths["summary_json"].parent)

    assert summary["sync_status"]["partial_sync"] is False
    assert status["submission_state_complete"] is True
    assert status["full_submission_state_complete"] is True
    assert status["submission_detail_complete"] is True
    assert status["download_complete"] is True
    assert summary["progress"]["label_count"] == 1
    assert summary["submissions"]["submission_count"] == 1
    assert summary["submissions"]["row_count"] == 3


def test_partial_sync_writes_progress_when_submission_listing_fails(tmp_path):
    paths = build_sync_from_client(
        client=LiveSyncFakeClient(fail_at="submissions/me"),
        output_dir=tmp_path / "sync",
        progress_limit=5000,
        submission_limit=100,
        local_data_root=tmp_path / "data",
        command=["pytest"],
        allow_partial=True,
        live_fetch=True,
    )
    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    index = json.loads(paths["submission_index_json"].read_text(encoding="utf-8"))
    rows = paths["submission_rows_jsonl"].read_text(encoding="utf-8").splitlines()

    assert summary["sync_status"]["partial_sync"] is True
    assert summary["sync_status"]["submission_state_complete"] is False
    assert summary["sync_status"]["full_submission_state_complete"] is False
    assert summary["sync_status"]["submission_index_complete"] is False
    assert summary["sync_status"]["failing_endpoint"] == "submissions/me"
    assert summary["decision"]["submission_recommended_now"] is False
    assert summary["progress"]["label_count"] == 1
    assert summary["api_endpoints_used"] == [
        "GET /api/public/v1/competitions/{competitionId}",
        "GET /api/public/v1/competitions/{competitionId}/me",
        "GET /api/public/v1/competitions/igp24/labels/progress",
        "GET /api/public/v1/competitions/{competitionId}/submissions/me",
    ]
    assert index["sync_status"]["submission_state_complete"] is False
    assert rows == []


def test_partial_sync_writes_progress_when_submission_detail_or_download_fails(tmp_path):
    for fail_at, failing_endpoint in [
        ("submissions/{id}", "submissions/{id}"),
        ("submissions/{id}/download", "submissions/{id}/download"),
    ]:
        paths = build_sync_from_client(
            client=LiveSyncFakeClient(fail_at=fail_at),
            output_dir=tmp_path / fail_at.replace("/", "_"),
            progress_limit=5000,
            submission_limit=100,
            local_data_root=tmp_path / "data",
            command=["pytest"],
            allow_partial=True,
            live_fetch=True,
        )
        summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
        index = json.loads(paths["submission_index_json"].read_text(encoding="utf-8"))
        all_text = "\n".join(path.read_text(encoding="utf-8") for path in paths.values())

        assert summary["sync_status"]["partial_sync"] is True
        assert summary["sync_status"]["failing_endpoint"] == failing_endpoint
        assert summary["submissions"]["submission_count"] == 1
        assert summary["decision"]["submission_recommended_now"] is False
        assert index["sync_status"]["partial_sync"] is True
        assert summary["sync_status"]["failed_submission_reads"]
        assert "sair_0123456789ab_" not in all_text


def test_partial_sync_retains_successful_submission_details_when_later_detail_fails(tmp_path):
    paths = build_sync_from_client(
        client=MultiSubmissionPartialClient(fail_detail="sub_b"),
        output_dir=tmp_path / "sync",
        progress_limit=5000,
        submission_limit=100,
        local_data_root=tmp_path / "data",
        command=["pytest"],
        allow_partial=True,
        live_fetch=True,
    )
    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in paths["submission_rows_jsonl"].read_text(encoding="utf-8").splitlines()]
    failed_reads = [json.loads(line) for line in paths["failed_submission_reads_jsonl"].read_text(encoding="utf-8").splitlines()]

    assert summary["sync_status"]["partial_sync"] is True
    assert summary["sync_status"]["submission_index_complete"] is True
    assert summary["sync_status"]["submission_detail_complete"] is False
    assert summary["sync_status"]["download_complete"] is False
    assert summary["sync_status"]["full_submission_state_complete"] is False
    assert summary["sync_status"]["degraded_mode_summary"].startswith("1/2 details recovered")
    assert summary["submissions"]["submission_count"] == 2
    assert summary["submissions"]["row_count"] == 3
    assert {row["submission_id"] for row in rows} == {"sub_a"}
    assert failed_reads == [
        {
            "submission_id": "sub_b",
            "endpoint": "submissions/{id}",
            "status": 503,
            "code": "IGP24_SERVICE_UNAVAILABLE",
            "message": "submissions/{id}: temporarily unavailable",
            "retry_after": None,
        }
    ]
    assert summary["decision"]["submission_recommended_now"] is False


def test_partial_sync_retains_detail_rows_when_download_fails(tmp_path):
    paths = build_sync_from_client(
        client=MultiSubmissionPartialClient(fail_download="sub_b"),
        output_dir=tmp_path / "sync",
        progress_limit=5000,
        submission_limit=100,
        local_data_root=tmp_path / "data",
        command=["pytest"],
        allow_partial=True,
        live_fetch=True,
    )
    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in paths["submission_rows_jsonl"].read_text(encoding="utf-8").splitlines()]
    failed_reads = [json.loads(line) for line in paths["failed_submission_reads_jsonl"].read_text(encoding="utf-8").splitlines()]

    assert summary["sync_status"]["submission_detail_complete"] is True
    assert summary["sync_status"]["download_complete"] is False
    assert summary["sync_status"]["submission_download_success_count"] == 1
    assert summary["sync_status"]["submission_download_failed_count"] == 1
    assert summary["sync_status"]["degraded_mode_summary"] == "2/2 details recovered; 1/2 downloads recovered"
    assert summary["submissions"]["row_count"] == 6
    assert [row["local_match_status"] for row in rows if row["submission_id"] == "sub_b"] == [
        "no_polynomial_line",
        "no_polynomial_line",
        "no_polynomial_line",
    ]
    assert failed_reads[0]["submission_id"] == "sub_b"
    assert failed_reads[0]["endpoint"] == "submissions/{id}/download"
