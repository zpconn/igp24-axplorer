import json

from scripts.igp24_adaptive_frobenius_benchmark import main as benchmark_main
from src.igp24.adaptive_frobenius import (
    adaptive_frobenius_evidence,
    collect_frobenius_observations,
    coefficients_from_record,
    factorization_degrees_mod_prime,
)
from src.igp24.group_compatibility import GroupCycleIndex, GroupRecord, cycle_type_key
from src.igp24.polynomial import DEGREE


VALID = tuple([-2] + [0] * (DEGREE - 1))


def _write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _record(hash_value="valid-hash"):
    return {
        "canonical_hash": hash_value,
        "label": "24T1",
        "t": 1,
        "r": 2,
        "pair_key": "24T1|r=2",
        "polynomial": ",".join(str(value) for value in list(VALID) + [1]),
    }


def _index_for_valid(path):
    first_degrees = factorization_degrees_mod_prime(VALID, 5)
    second_degrees = factorization_degrees_mod_prime(VALID, 7)
    index = GroupCycleIndex(path)
    index.initialize(provenance={"test": True})
    index.upsert_group(
        GroupRecord(
            label="24T1",
            t=1,
            parity="mixed",
            cycle_types=(cycle_type_key(first_degrees), cycle_type_key(second_degrees)),
        )
    )
    index.upsert_group(
        GroupRecord(
            label="24T2",
            t=2,
            parity="mixed",
            cycle_types=(cycle_type_key(first_degrees),),
        )
    )
    return index


def test_collect_frobenius_observations_skips_ramified_primes_and_tracks_survivors(tmp_path):
    index = _index_for_valid(tmp_path / "groups.sqlite")
    progress = [
        {"label": "24T1", "allowedR": [2], "remainingSignatures": [2], "discoveredSignatures": [], "signatures": [{"r": 2, "discovered": False, "teamCount": 0}]},
        {"label": "24T2", "allowedR": [2], "remainingSignatures": [2], "discoveredSignatures": [], "signatures": [{"r": 2, "discovered": False, "teamCount": 0}]},
    ]

    result = collect_frobenius_observations(_record(), index, progress_rows=progress, max_usable_primes=2)

    assert coefficients_from_record(_record()) == VALID
    assert 2 in result["skipped_ramified_primes"]
    assert 3 in result["skipped_ramified_primes"]
    assert result["usable_prime_count"] == 2
    assert result["observations"][0]["prime"] == 5
    assert result["observations"][0]["indexed_target_survivor_count"] == 2
    assert result["observations"][1]["prime"] == 7
    assert result["observations"][1]["indexed_target_survivor_count"] == 1
    assert result["final_compatibility"]["indexed_target_labels_not_ruled_out"] == ["24T1"]


def test_adaptive_frobenius_stops_when_survivor_set_stabilizes(tmp_path):
    index = _index_for_valid(tmp_path / "groups.sqlite")

    result = adaptive_frobenius_evidence(
        _record(),
        index,
        progress_rows=[],
        max_usable_primes=4,
        stable_after=1,
        stop_when_no_valuable_targets=False,
    )

    assert result["stop_reason"] in {"survivor_set_stable", "evidence_budget_exhausted"}
    assert result["usable_prime_count"] <= 4
    assert result["soundness"] == "adaptive_unramified_frobenius_cycle_target_exclusion_only"


def test_adaptive_frobenius_benchmark_cli_outputs_budget_summary(tmp_path):
    index = _index_for_valid(tmp_path / "groups.sqlite")
    scoreable = tmp_path / "scoreable.jsonl"
    progress = tmp_path / "progress.jsonl"
    output = tmp_path / "out"
    _write_jsonl(scoreable, [_record()])
    _write_jsonl(
        progress,
        [
            {"label": "24T1", "allowedR": [2], "remainingSignatures": [2], "discoveredSignatures": [], "signatures": [{"r": 2, "discovered": False, "teamCount": 0}]},
            {"label": "24T2", "allowedR": [2], "remainingSignatures": [2], "discoveredSignatures": [], "signatures": [{"r": 2, "discovered": False, "teamCount": 0}]},
        ],
    )

    assert (
        benchmark_main(
            [
                "--scoreable_rows_jsonl",
                str(scoreable),
                "--index",
                str(tmp_path / "groups.sqlite"),
                "--progress_jsonl",
                str(progress),
                "--budgets",
                "1,2",
                "--max_usable_primes",
                "2",
                "--output_dir",
                str(output),
            ]
        )
        == 0
    )

    summary = json.loads((output / "adaptive_frobenius_benchmark_summary.json").read_text(encoding="utf-8"))
    assert summary["input_row_count"] == 1
    assert summary["evaluated_row_count"] == 1
    assert summary["failed_row_count"] == 0
    assert summary["budget_summary"]["1"]["median_indexed_target_survivor_count"] == 2
    assert summary["budget_summary"]["2"]["median_indexed_target_survivor_count"] == 1
