import json

from scripts.igp24_build_structural_pretraining_corpus import (
    EVAL_FAMILIES,
    TARGET_RS,
    TRAIN_FAMILIES,
    allocate_quota,
    build_quota_plan,
    centers_for_index,
    main,
    unrank_combination,
)
from src.igp24.constructions.eisenstein_composition import build_eisenstein_power_composition


def test_combination_unranking_is_unique_and_lexicographic():
    rows = [unrank_combination(5, 3, rank) for rank in range(10)]

    assert rows[0] == (0, 1, 2)
    assert rows[-1] == (2, 3, 4)
    assert rows == sorted(rows)
    assert len(set(rows)) == 10


def test_quota_plan_is_balanced_and_uses_disjoint_families():
    plan = build_quota_plan(1_000, 100)

    assert sum(item["quota"] for item in plan if item["split"] == "train") == 1_000
    assert sum(item["quota"] for item in plan if item["split"] == "eval") == 100
    for target_r in TARGET_RS:
        assert sum(item["quota"] for item in plan if item["split"] == "train" and item["target_r"] == target_r) == 200
        assert sum(item["quota"] for item in plan if item["split"] == "eval" and item["target_r"] == target_r) == 20
    assert {family.family_id for family in TRAIN_FAMILIES}.isdisjoint(
        {family.family_id for family in EVAL_FAMILIES}
    )


def test_centers_generate_requested_exact_r_for_every_supported_family():
    for family in TRAIN_FAMILIES + EVAL_FAMILIES:
        for target_r in TARGET_RS:
            if not family.supports_r(target_r):
                continue
            centers = centers_for_index(family, target_r, 0)
            certificate = build_eisenstein_power_composition(
                centers,
                prime=family.prime,
                inner_power=family.inner_power,
            )
            assert certificate.real_root_count == target_r


def test_smoke_corpus_is_resumable_unique_and_exact(tmp_path):
    output_dir = tmp_path / "corpus"

    assert main(["--output_dir", str(output_dir), "--train_rows", "100", "--eval_rows", "50"]) == 0
    manifest = json.loads((output_dir / "corpus_manifest.json").read_text(encoding="utf-8"))
    rows = []
    for item in manifest["files"]:
        rows.extend(
            json.loads(line)
            for line in (output_dir / item["path"]).read_text(encoding="utf-8").splitlines()
            if line
        )

    assert manifest["train_row_count"] == 100
    assert manifest["eval_row_count"] == 50
    assert len(rows) == 150
    assert len({row["canonical_hash"] for row in rows}) == 150
    assert all(row["features"]["packet_eligible"] is False for row in rows)
    assert all(row["features"]["irreducibility_proof"] == "eisenstein" for row in rows)

    assert main(["--output_dir", str(output_dir), "--train_rows", "100", "--eval_rows", "50"]) == 0
    resumed = json.loads((output_dir / "corpus_manifest.json").read_text(encoding="utf-8"))
    assert all(shard["resumed"] is True for shard in resumed["shards"])
