from scripts.igp24_materialize_adaptive_reviewed_candidates import review_candidate


def test_review_candidate_materializes_compatibility_and_packet_eligibility():
    candidate = {
        "canonical_hash": "abc",
        "route": {"label": "24T9993", "pair_key": "24T9993|r=8"},
        "real_root_count": 8,
        "adaptive_frobenius": {"usable_prime_count": 20},
    }
    adaptive_row = {
        "row_index": 1,
        "short_hash": "abc",
        "usable_prime_count": 40,
        "primes_examined": 45,
        "mod_p_factorization_degree_patterns": [
            {"prime": prime, "degrees": [24]} for prime in range(5, 45)
        ],
    }
    compatibility = {
        "indexed_target_survivor_count": 23,
        "indexed_target_labels_not_ruled_out": ["24T24134", "24T24908"],
        "valuable_targets_not_ruled_out": ["24T24134|r=8", "24T24908|r=8"],
        "compatible_uncovered_pairs": ["24T24134|r=8"],
        "compatible_low_team_pairs": ["24T24908|r=8"],
        "soundness": "necessary_target_exclusion_only",
    }

    reviewed = review_candidate(candidate, adaptive_row, compatibility, minimum_usable_primes=40)

    assert reviewed["group_compatibility"] == compatibility
    assert reviewed["adaptive_frobenius"]["usable_prime_count"] == 40
    assert reviewed["frobenius_usable_prime_count"] == 40
    assert reviewed["sufficient_adaptive_frobenius_evidence"] is True
    assert reviewed["target_label_not_ruled_out"] is False
    assert reviewed["target_pair_valuable_not_ruled_out"] is False
    assert reviewed["any_valuable_target_not_ruled_out"] is True
    assert reviewed["eligible_for_packet"] is True
    assert reviewed["live_submission_recommended_now"] is False
    assert reviewed["submission_recommendation"] == "offline_review_only_non_target_valuable_compatibility"
    assert reviewed["adaptive_review"]["soundness"] == "necessary_target_exclusion_only_not_exact_label_verification"
