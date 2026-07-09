import json

from scripts.igp24_packet_optimizer import (
    greedy_select,
    load_score_plan,
    normalize_candidate,
    summarize,
    write_outputs,
)


def _score_plan(tmp_path):
    path = tmp_path / "score_plan.json"
    path.write_text(
        json.dumps(
            {
                "record_type": "igp24_score_aware_target_plan",
                "ranked_targets": [
                    {
                        "pair_key": "24T1|r=24",
                        "label": "24T1",
                        "r": 24,
                        "category": "uncovered_signature",
                        "progress_state": "remaining",
                        "maximum_possible_points": 1.0,
                        "estimated_expected_points": 1.0,
                        "score_ceiling_class": "uncovered_first_team_one_point",
                    },
                    {
                        "pair_key": "24T2|r=16",
                        "label": "24T2",
                        "r": 16,
                        "category": "lightly_solved_signature",
                        "progress_state": "discovered",
                        "maximum_possible_points": 0.125,
                        "estimated_expected_points": 0.125,
                        "score_ceiling_class": "very_low_team_high_ceiling",
                    },
                    {
                        "pair_key": "24T25000|r=16",
                        "label": "24T25000",
                        "r": 16,
                        "category": "covered_or_crowded",
                        "progress_state": "discovered",
                        "maximum_possible_points": 0.0,
                        "estimated_expected_points": 0.0,
                        "score_ceiling_class": "crowded_near_zero_ceiling",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _coefficients(seed):
    coeffs = [1 + int(seed)] + [0] * 23 + [1]
    coeffs[1] = 1
    return coeffs


def _row(
    short,
    *,
    r=24,
    uncovered=None,
    low_team=None,
    crowded=None,
    label_count=1,
    family="family_a",
    mode="mode_a",
    basin=None,
    mod_sig=None,
    eligible=True,
    fatal=False,
):
    return {
        "canonical_hash": f"{short}{'0' * (64 - len(short))}",
        "short_hash": short,
        "score": 100.0,
        "eligible_for_packet": eligible,
        "fatal_risk_reasons": ["known_bad"] if fatal else [],
        "features": {
            "canonical_hash": f"{short}{'0' * (64 - len(short))}",
            "short_hash": short,
            "r": r,
            "construction_family": family,
            "template_family_id": f"{family}:{mode}",
            "perturbation_mode": mode,
            "basin_fingerprint": basin or f"{family}:{mode}:{short}",
            "mod_p_pattern_signature": mod_sig or f"p3:{short}",
        },
        "group_compatibility": {
            "compatible_label_count": label_count,
            "compatible_uncovered_pairs": uncovered or [],
            "compatible_low_team_pairs": low_team or [],
            "compatible_crowded_pairs": crowded or [],
            "crowded_only": bool(crowded and not uncovered and not low_team),
        },
        "exported_coefficients": _coefficients(len(short)),
    }


def _normalized(rows, score_plan):
    return [normalize_candidate(row, score_plan=score_plan, require_eligible=True) for row in rows]


def _normalized_with_known(rows, score_plan, known_hashes):
    return [
        normalize_candidate(
            row,
            score_plan=score_plan,
            require_eligible=True,
            known_submission_hashes=set(known_hashes),
        )
        for row in rows
    ]


def test_packet_optimizer_selects_union_of_valuable_pairs_and_rejects_crowded_only(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    candidates = _normalized(
        [
            _row("aaa", uncovered=["24T1|r=24"], label_count=4, family="fam1", mode="m1"),
            _row("bbb", uncovered=["24T1|r=24"], label_count=1, family="fam2", mode="m2"),
            _row("ccc", r=16, low_team=["24T2|r=16"], family="fam3", mode="m3"),
            _row("ddd", r=16, crowded=["24T25000|r=16"], family="fam4", mode="m4"),
            {"canonical_hash": "eee", "eligible_for_packet": True, "features": {"r": 16}},
        ],
        score_plan,
    )

    selected, rejected = greedy_select(
        candidates,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    selected_pairs = {pair for row in selected for pair in row["pair_values"]}
    assert selected_pairs == {"24T1|r=24", "24T2|r=16"}
    assert len(selected) == 2
    assert sum(1 for row in selected if "24T1|r=24" in row["pair_values"]) == 1
    assert any("crowded_only" in row["reject_reasons"] for row in rejected)
    assert any("missing_pair_or_compatibility_evidence" in row["reject_reasons"] for row in rejected)


def test_packet_optimizer_rejects_known_submission_hashes_before_selection(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    known_hash = "aaa" + "0" * 61
    candidates = _normalized_with_known(
        [
            _row("aaa", uncovered=["24T1|r=24"], label_count=1, family="fam1", mode="m1"),
            _row("bbb", uncovered=["24T1|r=24"], label_count=1, family="fam2", mode="m2"),
        ],
        score_plan,
        {known_hash},
    )

    selected, rejected = greedy_select(
        candidates,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    assert [row["short_hash"] for row in selected] == ["bbb"]
    known_rejected = [row for row in rejected if row["short_hash"] == "aaa"][0]
    assert known_rejected["known_submission_hash"] is True
    assert "known_submission_hash" in known_rejected["reject_reasons"]


def test_packet_optimizer_enforces_diversity_caps(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    candidates = _normalized(
        [
            _row("aaa", uncovered=["24T1|r=24"], family="same_family", mode="same_mode"),
            _row("ccc", r=16, low_team=["24T2|r=16"], family="same_family", mode="same_mode"),
        ],
        score_plan,
    )

    selected, _ = greedy_select(
        candidates,
        packet_limit=10,
        caps={
            "construction_family": 1,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )

    assert len(selected) == 1
    assert selected[0]["features"]["construction_family"] == "same_family"


def test_packet_optimizer_writes_report_and_sair_ready_coefficients(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    candidates = _normalized(
        [
            _row("aaa", uncovered=["24T1|r=24"], family="fam1", mode="m1"),
            _row("ccc", r=16, low_team=["24T2|r=16"], family="fam2", mode="m2"),
        ],
        score_plan,
    )
    selected, rejected = greedy_select(
        candidates,
        packet_limit=10,
        caps={
            "construction_family": 10,
            "template_family_id": 10,
            "perturbation_mode": 10,
            "basin_fingerprint": 10,
            "mod_p_pattern_signature": 10,
            "compatible_label_cluster": 10,
            "r": 10,
        },
    )
    summary = summarize(
        candidate_paths=[tmp_path / "candidates.jsonl"],
        candidates=candidates,
        selected=selected,
        rejected=rejected,
        caps={"construction_family": 10},
        output_files={},
    )
    paths = write_outputs(tmp_path / "out", selected=selected, rejected=rejected, summary=summary)

    coefficient_lines = paths["coefficients_txt"].read_text(encoding="utf-8").splitlines()
    assert len(coefficient_lines) == 2
    assert all(not line.startswith("[") and line.endswith(",1") for line in coefficient_lines)
    saved_summary = json.loads(paths["summary_json"].read_text(encoding="utf-8"))
    assert saved_summary["selected_possible_uncovered_pair_count"] == 1
    assert saved_summary["selected_possible_low_team_pair_count"] == 1
    assert saved_summary["live_submission_recommended_now"] is False
    assert "IGP24 Packet Optimizer" in paths["report_md"].read_text(encoding="utf-8")
