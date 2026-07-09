import json
from types import SimpleNamespace

from scripts.igp24_group_compatible_submission_gate import build_gate


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _progress_row(label, *, remaining=None, discovered=None, teams_by_r=None):
    remaining = remaining or []
    discovered = discovered or []
    teams_by_r = teams_by_r or {}
    allowed = sorted(set(remaining + discovered))
    return {
        "label": label,
        "t": int(label.removeprefix("24T")),
        "allowedR": allowed,
        "remainingSignatures": remaining,
        "discoveredSignatures": discovered,
        "teamCount": max(teams_by_r.values(), default=0),
        "minimumDiscAbs": None,
        "signatures": [
            {
                "r": r,
                "discovered": r in discovered,
                "teamCount": teams_by_r.get(r, 0),
                "minimumDiscAbs": None,
            }
            for r in allowed
        ],
    }


def _line(constant):
    coeffs = [constant] + [0] * 23 + [1]
    return ",".join(str(value) for value in coeffs)


def _selected_row(hash_value, *, rank=1, uncovered=None, low_team=None, crowded=None, label_count=3):
    return {
        "optimizer_rank": rank,
        "canonical_hash": hash_value,
        "short_hash": hash_value[:12],
        "eligible_for_optimization": True,
        "reject_reasons": [],
        "features": {
            "r": 24,
            "construction_family": "model_sample_export",
            "template_family_id": "model:fixed_sparse_template:r24:test",
            "perturbation_mode": "test",
            "basin_fingerprint": f"basin:{rank}",
        },
        "compatible_label_count": label_count,
        "possible_uncovered_pairs": uncovered or [],
        "possible_low_team_pairs": low_team or [],
        "possible_crowded_pairs": crowded or [],
        "maximum_possible_points": float(len(uncovered or []) + len(low_team or [])),
        "estimated_expected_points": 1.0,
        "marginal_estimated_points": 1.0,
        "compatibility_ambiguity_factor": 0.5,
    }


def _fake_scorer_by_constant(mapping):
    def score(coefficients24, *, target_r, coeff_bound, prime_limit, exact_score_timeout):
        hash_value = mapping[coefficients24[0]]
        return 123.0, SimpleNamespace(
            valid=True,
            rejection_reason=None,
            canonical_hash=hash_value,
            real_root_count=target_r,
            irreducible=True,
            squarefree=True,
            coefficient_height=max(abs(value) for value in coefficients24),
            log_abs_discriminant=12.5,
            sampled_primes=(3, 5),
            mod_p_factorization_degree_patterns=[
                SimpleNamespace(prime=3, degrees=(12, 12)),
                SimpleNamespace(prime=5, degrees=(8, 16)),
            ],
            warnings=(),
        )

    return score


def test_group_compatible_gate_writes_local_review_packet_without_live_submission(tmp_path, monkeypatch):
    monkeypatch.delenv("SAIR_API_KEY", raising=False)
    hash_a = "a" * 64
    hash_b = "b" * 64
    selected = [
        _selected_row(hash_a, rank=1, uncovered=["24T1|r=24"], crowded=["24T25000|r=24"]),
        _selected_row(hash_b, rank=2, uncovered=["24T2|r=24"]),
    ]
    selected_jsonl = tmp_path / "selected.jsonl"
    coefficients_txt = tmp_path / "coefficients.txt"
    _write_jsonl(selected_jsonl, selected)
    coefficients_txt.write_text(_line(2) + "\n" + _line(3) + "\n", encoding="utf-8")
    sync_summary = tmp_path / "sair_sync_summary.json"
    sync_summary.write_text(
        json.dumps({"created_at": "2026-07-09T00:00:00+00:00", "sync_status": {"partial_sync": False, "submissions_requested": 2}}),
        encoding="utf-8",
    )
    progress_jsonl = tmp_path / "sair_label_progress.jsonl"
    _write_jsonl(
        progress_jsonl,
        [
            _progress_row("24T1", remaining=[24]),
            _progress_row("24T2", remaining=[24]),
            _progress_row("24T25000", discovered=[24], teams_by_r={24: 35}),
        ],
    )

    paths = build_gate(
        selected_jsonl=selected_jsonl,
        coefficients_txt=coefficients_txt,
        output_dir=tmp_path / "gate",
        sair_sync_summary_json=sync_summary,
        sair_label_progress_jsonl=progress_jsonl,
        source_commit="abc123",
        scorer=_fake_scorer_by_constant({2: hash_a, 3: hash_b}),
    )

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in paths["rows_jsonl"].read_text(encoding="utf-8").splitlines()]
    dry_run = json.loads(paths["sair_local_dry_run_json"].read_text(encoding="utf-8"))

    assert summary["local_gate_passed"] is True
    assert summary["local_packet_ready_for_human_review"] is True
    assert summary["live_submission_recommended_now"] is False
    assert summary["exact_label_verified"] is False
    assert summary["safety"]["sair_submission"] is False
    assert summary["safety"]["api_key_required"] is False
    assert summary["selected_possible_uncovered_pair_count"] == 2
    assert summary["progress_cross_check"]["current_uncovered_pair_count"] == 2
    assert summary["progress_cross_check"]["stale_uncovered_pair_count"] == 0
    assert summary["sair_sync"]["partial_sync"] is False
    assert dry_run["dry_run"] is True
    assert dry_run["network_calls"] is False
    assert rows[0]["review_status"] == "local_gate_passed_compatibility_only"
    assert rows[0]["local_validation"]["hash_matches_optimizer_row"] is True
    assert paths["coefficients_txt"].read_text(encoding="utf-8").splitlines() == [_line(2), _line(3)]
    assert "Compatibility evidence is necessary evidence only" in paths["report_md"].read_text(encoding="utf-8")


def test_group_compatible_gate_blocks_hash_mismatch_and_crowded_only_packet(tmp_path):
    expected_hash = "a" * 64
    selected_jsonl = tmp_path / "selected.jsonl"
    coefficients_txt = tmp_path / "coefficients.txt"
    _write_jsonl(
        selected_jsonl,
        [
            _selected_row(
                expected_hash,
                rank=1,
                uncovered=[],
                low_team=[],
                crowded=["24T25000|r=24"],
                label_count=1,
            )
        ],
    )
    coefficients_txt.write_text(_line(2) + "\n", encoding="utf-8")

    paths = build_gate(
        selected_jsonl=selected_jsonl,
        coefficients_txt=coefficients_txt,
        output_dir=tmp_path / "gate",
        source_commit="abc123",
        scorer=_fake_scorer_by_constant({2: "b" * 64}),
    )

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))

    assert summary["local_gate_passed"] is False
    assert summary["live_submission_reason"] == "local gate failed; see check_failures"
    assert "row_1_hash_matches_optimizer_row" in summary["check_failures"]
    assert "row_1_has_valuable_compatible_pair" in summary["check_failures"]
    assert "row_1_not_crowded_only" in summary["check_failures"]


def test_group_compatible_gate_blocks_stale_uncovered_pairs_when_progress_is_provided(tmp_path):
    hash_value = "a" * 64
    selected_jsonl = tmp_path / "selected.jsonl"
    coefficients_txt = tmp_path / "coefficients.txt"
    progress_jsonl = tmp_path / "sair_label_progress.jsonl"
    _write_jsonl(
        selected_jsonl,
        [_selected_row(hash_value, rank=1, uncovered=["24T1|r=24"], crowded=[])],
    )
    coefficients_txt.write_text(_line(2) + "\n", encoding="utf-8")
    _write_jsonl(progress_jsonl, [_progress_row("24T1", discovered=[24], teams_by_r={24: 44})])

    paths = build_gate(
        selected_jsonl=selected_jsonl,
        coefficients_txt=coefficients_txt,
        output_dir=tmp_path / "gate",
        sair_label_progress_jsonl=progress_jsonl,
        source_commit="abc123",
        scorer=_fake_scorer_by_constant({2: hash_value}),
    )

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))

    assert summary["local_gate_passed"] is False
    assert summary["progress_cross_check"]["current_uncovered_pair_count"] == 0
    assert summary["progress_cross_check"]["stale_uncovered_pairs"] == ["24T1|r=24"]
    assert "row_1_progress_current_valuable_pair" in summary["check_failures"]


def test_group_compatible_gate_blocks_known_submission_hashes(tmp_path):
    hash_value = "a" * 64
    selected_jsonl = tmp_path / "selected.jsonl"
    coefficients_txt = tmp_path / "coefficients.txt"
    submission_rows = tmp_path / "sair_submission_rows.jsonl"
    _write_jsonl(
        selected_jsonl,
        [_selected_row(hash_value, rank=1, uncovered=["24T1|r=24"], crowded=[])],
    )
    coefficients_txt.write_text(_line(2) + "\n", encoding="utf-8")
    _write_jsonl(
        submission_rows,
        [
            {
                "canonical_hash": hash_value,
                "submission_id": "sub_existing",
                "submitted_line_number": 4,
                "status": "accepted",
                "status_class": "scoreable",
                "label": "24T25000",
                "t": 25000,
                "r": 24,
                "pair_key": "24T25000|r=24",
                "scoreable": True,
                "scoring_status": "scoreable",
            }
        ],
    )

    paths = build_gate(
        selected_jsonl=selected_jsonl,
        coefficients_txt=coefficients_txt,
        output_dir=tmp_path / "gate",
        sair_submission_rows_jsonl=submission_rows,
        source_commit="abc123",
        scorer=_fake_scorer_by_constant({2: hash_value}),
    )

    summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    row = json.loads(paths["rows_jsonl"].read_text(encoding="utf-8").splitlines()[0])

    assert summary["local_gate_passed"] is False
    assert summary["submission_hash_cross_check"]["known_submission_hash_count"] == 1
    assert summary["submission_hash_cross_check"]["known_submission_pairs"] == ["24T25000|r=24"]
    assert row["submission_hash_cross_check"]["known_labels"] == ["24T25000"]
    assert "row_1_not_known_submission_hash" in summary["check_failures"]
