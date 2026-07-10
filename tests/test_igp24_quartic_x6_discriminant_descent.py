import json

from scripts import igp24_quartic_x6_discriminant_descent as descent
from src.igp24.adaptive_frobenius import factorization_degrees_mod_prime
from src.igp24.constructions.quartic_x6_descent import (
    QuarticX6Parameters,
    coefficient_support,
    iter_alternating_sign_grid,
    lift_quartic_x6,
    outer_galois_profile,
    positive_real_root_count,
    quartic_discriminant,
    quartic_x6_polynomial_discriminant_abs,
)
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord, cycle_type_key


KNOWN_9993 = QuarticX6Parameters(a=-9, b=17, c=-8, d=1)
KNOWN_1310 = QuarticX6Parameters(a=-8, b=14, c=-7, d=1)
KNOWN_661 = QuarticX6Parameters(a=-8, b=16, c=-8, d=1)


def test_quartic_x6_exact_invariants_match_known_9993_row():
    assert quartic_discriminant(KNOWN_9993) == 7537
    assert quartic_x6_polynomial_discriminant_abs(KNOWN_9993) == 868602551660119550264838028544723034046464
    assert positive_real_root_count(KNOWN_9993) == 4
    assert outer_galois_profile(KNOWN_9993)["outer_galois_group_name"] == "S4"
    assert outer_galois_profile(KNOWN_9993)["outer_action_matches_24T9993"] is True
    assert coefficient_support(lift_quartic_x6(KNOWN_9993)) == (0, 6, 12, 18)


def test_outer_s4_gate_rejects_known_c4_and_d4_collapse_rows():
    profile_1310 = outer_galois_profile(KNOWN_1310)
    profile_661 = outer_galois_profile(KNOWN_661)

    assert profile_1310["outer_galois_group_order"] == 4
    assert profile_1310["outer_action_matches_24T9993"] is False
    assert profile_661["outer_galois_group_order"] == 8
    assert profile_661["outer_action_matches_24T9993"] is False


def test_grid_deduplicates_reciprocal_outer_polynomials():
    rows = list(
        iter_alternating_sign_grid(
            a_abs_min=8,
            a_abs_max=9,
            b_min=16,
            b_max=17,
            c_abs_min=8,
            c_abs_max=9,
            maximum_quartic_discriminant=20_000,
            deduplicate_reciprocals=True,
        )
    )
    keys = [row.reciprocal_key for row in rows]
    assert len(keys) == len(set(keys))
    assert KNOWN_9993.reciprocal_key in keys


def test_known_submission_state_indexes_hash_and_reciprocal_equivalence(tmp_path):
    submissions = tmp_path / "submissions.jsonl"
    submissions.write_text(
        json.dumps(
            {
                "canonical_hash": "known-hash",
                "submission_id": "sub-test",
                "status": "accepted",
                "label": "24T9993",
                "r": 8,
                "pair_key": "24T9993|r=8",
                "polynomial": "1,0,0,0,0,0,-8,0,0,0,0,0,17,0,0,0,0,0,-9,0,0,0,0,0,1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    state = descent.load_known_submission_state([submissions])

    assert state["by_hash"]["known-hash"]["pair_key"] == "24T9993|r=8"
    assert KNOWN_9993.reciprocal_key in state["by_reciprocal_outer"]


def test_exact_nfdisc_matches_axg121_exact_feedback():
    exported = [*lift_quartic_x6(KNOWN_9993), 1]
    result = descent.compute_exact_nfdisc(
        exported,
        polynomial_discriminant_abs=quartic_x6_polynomial_discriminant_abs(KNOWN_9993),
        timeout_seconds=5.0,
    )

    assert result["status"] == "ok"
    assert result["exact_nfdisc_abs"] == 10723488292100241361294296648700284370944
    assert result["index_factor"] == 9


def _complete_test_index(path, *, cycles):
    index = GroupCycleIndex(path)
    index.initialize(
        provenance={"test": True},
        index_scope="complete_degree24_universe",
        expected_global_group_count=1,
        global_index_complete=True,
    )
    index.upsert_group(
        GroupRecord(
            label="24T9993",
            t=9993,
            degree=24,
            order=10368,
            primitive=False,
            solvable=True,
            parity="even",
            block_sizes=(2, 3, 6),
            cycle_types=tuple(cycles),
            status="complete",
            provenance={"test": True},
        )
    )
    return index


def test_target_specific_screen_uses_unramified_cycles(tmp_path):
    coefficients = lift_quartic_x6(KNOWN_9993)
    cycles = [
        cycle_type_key(factorization_degrees_mod_prime(coefficients, prime))
        for prime in (5, 7)
    ]
    index = _complete_test_index(tmp_path / "index.sqlite", cycles=cycles)
    record = {
        "coefficients": coefficients,
        "polynomial_discriminant_abs": quartic_x6_polynomial_discriminant_abs(KNOWN_9993),
    }

    result = descent.target_specific_frobenius_screen(
        record,
        target_label="24T9993",
        group_index=index,
        usable_prime_budget=2,
        minimum_usable_primes=2,
    )

    assert result["skipped_ramified_primes"] == [2, 3]
    assert result["usable_prime_count"] == 2
    assert result["target_label_not_ruled_out"] is True
    assert result["sufficient_evidence"] is True


def test_cli_materializes_review_queue_without_exact_label_claim(tmp_path):
    coefficients = lift_quartic_x6(KNOWN_9993)
    cycles = [
        cycle_type_key(factorization_degrees_mod_prime(coefficients, prime))
        for prime in (5, 7)
    ]
    index_path = tmp_path / "index.sqlite"
    _complete_test_index(index_path, cycles=cycles)
    progress = tmp_path / "progress.jsonl"
    progress.write_text(
        json.dumps(
            {
                "label": "24T9993",
                "allowedR": [8],
                "signatures": [
                    {
                        "r": 8,
                        "discovered": True,
                        "teamCount": 12,
                        "minimumDiscAbs": "999999999999999999999999999999999999999999999",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    submissions = tmp_path / "submissions.jsonl"
    submissions.write_text("", encoding="utf-8")
    output = tmp_path / "out"

    assert (
        descent.main(
            [
                "--output_dir",
                str(output),
                "--group_index",
                str(index_path),
                "--progress_jsonl",
                str(progress),
                "--known_submission_jsonl",
                str(submissions),
                "--a_abs_min",
                "9",
                "--a_abs_max",
                "9",
                "--b_min",
                "17",
                "--b_max",
                "17",
                "--c_abs_min",
                "8",
                "--c_abs_max",
                "8",
                "--maximum_nfdisc_evaluations",
                "1",
                "--usable_prime_budget",
                "2",
                "--minimum_usable_primes",
                "2",
            ]
        )
        == 0
    )

    summary = json.loads((output / descent.SUMMARY_JSON).read_text(encoding="utf-8"))
    queue = [
        json.loads(line)
        for line in (output / descent.EXACT_LABEL_QUEUE_JSONL).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert summary["exact_label_queue_count"] == 1
    assert summary["live_submission_recommended_now"] is False
    assert queue[0]["exact_degree24_label_status"] == "pending"
    assert queue[0]["verified_group_label"] is None
    assert queue[0]["submission_recommendation"] == "false_pending_exact_degree24_label"
