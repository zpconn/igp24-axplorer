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
    usable_primes=10,
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
            "index_scope": "target_subset",
            "indexed_group_count": label_count,
            "expected_global_group_count": 25000,
            "global_index_complete": False,
            "unindexed_label_mass_unknown": True,
            "indexed_target_survivor_count": label_count,
            "indexed_target_labels_not_ruled_out": [f"24T{i}" for i in range(1, label_count + 1)],
            "soundness": "necessary_target_exclusion_only",
            "evidence_strength": "modular_cycle_target_exclusion",
            "evidence": {"primes": list(range(101, 101 + int(usable_primes)))},
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
            known_submission_hashes=known_hashes,
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


def test_packet_optimizer_records_known_submission_metadata_for_proven_hashes(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    known_hashes = {
        "c814e1de3e8d" + "0" * 52: [
            {"submission_id": "sub_11fc", "status": "accepted", "label": "24T25000", "r": 24, "pair_key": "24T25000|r=24"}
        ],
        "2c8838b3f843" + "0" * 52: [
            {"submission_id": "sub_25c1", "status": "accepted", "label": "24T24932", "r": 24, "pair_key": "24T24932|r=24"}
        ],
    }
    candidates = _normalized_with_known(
        [
            _row("c814e1de3e8d", uncovered=["24T1|r=24"]),
            _row("2c8838b3f843", uncovered=["24T2|r=24"]),
            _row("freshhash001", uncovered=["24T1|r=24"]),
        ],
        score_plan,
        known_hashes,
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

    assert [row["short_hash"] for row in selected] == ["freshhash001"]
    rejected_by_hash = {row["short_hash"]: row for row in rejected}
    assert rejected_by_hash["c814e1de3e8d"]["known_submission_matches"][0]["pair_key"] == "24T25000|r=24"
    assert rejected_by_hash["2c8838b3f843"]["known_submission_matches"][0]["label"] == "24T24932"
    assert all(row["short_hash"] not in {"c814e1de3e8d", "2c8838b3f843"} for row in selected)


def test_candidate_with_many_uncovered_targets_has_one_point_best_case(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    targets = [f"24T{i}|r=24" for i in range(1, 18)]
    candidate = normalize_candidate(
        _row("aaa", uncovered=targets, label_count=17),
        score_plan=score_plan,
        require_eligible=True,
    )

    assert candidate["best_case_points"] == 1.0
    assert candidate["maximum_possible_points"] == 1.0
    assert len(candidate["possible_uncovered_pairs"]) == 17
    assert candidate["expected_points_status"] == "unavailable_uncalibrated"
    assert candidate["estimated_expected_points"] is None


def test_compatibility_candidate_with_tiny_frobenius_budget_is_not_packet_eligible(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    candidate = normalize_candidate(
        _row("aaa", uncovered=["24T1|r=24"], label_count=1, usable_primes=5),
        score_plan=score_plan,
        require_eligible=True,
    )

    assert candidate["frobenius_usable_prime_count"] == 5
    assert candidate["minimum_frobenius_primes_required"] == 10
    assert candidate["sufficient_frobenius_evidence"] is False
    assert candidate["adaptive_evidence_status"] == "insufficient_adaptive_frobenius_evidence"
    assert "insufficient_adaptive_frobenius_evidence" in candidate["reject_reasons"]
    assert candidate["eligible_for_optimization"] is False


def test_packet_best_case_ceiling_no_greater_than_row_count(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    candidates = _normalized(
        [
            _row("aaa", uncovered=[f"24T{i}|r=24" for i in range(1, 18)], label_count=17),
            _row("bbb", uncovered=[f"24T{i}|r=24" for i in range(18, 35)], label_count=17),
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

    assert len(selected) == 2
    assert summary["best_case_packet_points"] <= 2.0
    assert summary["expected_score_estimate"] is None
    assert summary["expected_points_status"] == "unavailable_uncalibrated"


def test_exact_verified_pair_can_use_official_economics(tmp_path):
    score_plan = load_score_plan(_score_plan(tmp_path))
    row = _row("ccc", uncovered=[], low_team=[], crowded=[], label_count=0)
    row.pop("group_compatibility")
    row["exact_label_verified"] = True
    row["features"]["label"] = "24T2"
    row["features"]["pair_key"] = "24T2|r=16"
    row["features"]["r"] = 16

    candidate = normalize_candidate(row, score_plan=score_plan, require_eligible=True)

    assert candidate["expected_points_status"] == "available_exact_verified_pair"
    assert candidate["estimated_expected_points"] == 0.125
    assert candidate["best_case_points"] == 0.125
    assert candidate["adaptive_evidence_status"] == "exact_verified_pair_no_adaptive_required"
    assert "insufficient_adaptive_frobenius_evidence" not in candidate["reject_reasons"]


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
