import json

from scripts.igp24_construction_outcome_ledger import build_ledger, main as ledger_main


def _triage_row(candidate_hash: str, *, observed_label: str = "24T7635") -> dict:
    return {
        "canonical_hash": candidate_hash,
        "short_hash": candidate_hash[:12],
        "verified_group_label": observed_label,
        "computed_r": 8,
        "pair_key": f"{observed_label}|r=8",
        "exact_nfdisc_abs": 123456,
        "score_aware_classification": "sair_discovered_pair_not_improved",
        "sair_progress_state": "allowed_discovered",
        "sair_score_value_status": "valuable_low_team",
        "sair_progress_team_count": 13,
        "sair_progress_discriminant_status": "sair_progress_not_improved",
        "submission_grade_candidate": False,
        "known_submission_hash_match": False,
        "route": {
            "family": "quartic_in_x6",
            "label": "24T24134",
            "pair_key": "24T24134|r=8",
            "r": 8,
            "soundness": "declared_structural_routing_only_not_exact_label_evidence",
            "target_group_block_sizes": [3, 6],
        },
    }


def test_construction_outcome_ledger_blocks_repeated_false_target_route(tmp_path):
    triage = tmp_path / "triage.jsonl"
    rows = [_triage_row("a" * 64), _triage_row("b" * 64, observed_label="24T10010"), _triage_row("c" * 64, observed_label="24T9962")]
    triage.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

    outcome_rows, route_outcomes, summary = build_ledger([triage], min_exact_rows_to_block=3)

    assert len(outcome_rows) == 3
    assert summary["false_target_row_count"] == 3
    assert summary["blocked_route_count"] == 1
    assert route_outcomes[0]["intended_pair_key"] == "24T24134|r=8"
    assert route_outcomes[0]["family"] == "quartic_in_x6"
    assert route_outcomes[0]["route_outcome"] == "all_false_target_discovered_not_improved"
    assert route_outcomes[0]["recommended_route_action"] == "block_repeat_exact_basin"
    assert route_outcomes[0]["blocking_reason"] == "exact_route_false_target_outcome"


def test_construction_outcome_ledger_cli_writes_outputs(tmp_path):
    triage = tmp_path / "triage.jsonl"
    triage.write_text(
        "".join(json.dumps(_triage_row(ch * 64), sort_keys=True) + "\n" for ch in ("a", "b", "c")),
        encoding="utf-8",
    )
    output = tmp_path / "ledger"

    assert ledger_main(["--triage_jsonl", str(triage), "--output_dir", str(output)]) == 0

    summary = json.loads((output / "construction_outcome_ledger_summary.json").read_text(encoding="utf-8"))
    assert summary["blocked_route_count"] == 1
    route_rows = [
        json.loads(line)
        for line in (output / "construction_route_outcomes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert route_rows[0]["block_repeat_exact_basin"] is True
    report = (output / "construction_outcome_ledger_report.md").read_text(encoding="utf-8")
    assert "block_repeat_exact_basin" in report
