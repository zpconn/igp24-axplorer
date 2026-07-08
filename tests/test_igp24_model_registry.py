import json

import pytest

from scripts.igp24_model_registry import (
    create_version,
    record_run,
    summarize_registry,
    validate_registry,
    version_sort_key,
)


def test_version_sort_key_accepts_integer_and_decimal_versions():
    assert version_sort_key("AXG-1") == (1, 0)
    assert version_sort_key("AXG-5.5") == (5, 5)
    assert sorted(["AXG-2", "AXG-1.5", "AXG-1"], key=version_sort_key) == [
        "AXG-1",
        "AXG-1.5",
        "AXG-2",
    ]


@pytest.mark.parametrize("version", ["GPT-5", "AXG-0", "AXG-1.0", "AXG-01", "AXG-x"])
def test_version_sort_key_rejects_bad_versions(version):
    with pytest.raises(ValueError):
        version_sort_key(version)


def test_create_version_rejects_duplicate_and_validate_registry(tmp_path):
    registry = tmp_path / "registry"
    created = create_version(registry, "AXG-1", "none", "baseline")

    assert (registry / "README.md").exists()
    assert (registry / "models" / "AXG-1" / "model_manifest.json").exists()
    assert created["manifest"].endswith("model_manifest.json")

    with pytest.raises(FileExistsError):
        create_version(registry, "AXG-1", "none", "duplicate")

    validation = validate_registry(registry)
    assert validation["valid"] is True
    assert validation["models"] == ["AXG-1"]


def test_create_version_requires_existing_parent(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_version(tmp_path / "registry", "AXG-2", "AXG-1", "missing parent")


def test_create_axg13_links_to_axg12_parent(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1", "none", "baseline")
    create_version(registry, "AXG-1.1", "AXG-1", "seeded target r")
    create_version(registry, "AXG-1.2", "AXG-1.1", "control-token target r")

    created = create_version(registry, "AXG-1.3", "AXG-1.2", "diversity-aware target r")
    manifest = json.loads((registry / "models" / "AXG-1.3" / "model_manifest.json").read_text(encoding="utf-8"))

    assert created["manifest"].endswith("AXG-1.3/model_manifest.json")
    assert manifest["parent_version"] == "AXG-1.2"
    assert manifest["description"] == "diversity-aware target r"
    assert validate_registry(registry)["models"] == ["AXG-1", "AXG-1.1", "AXG-1.2", "AXG-1.3"]


def test_validate_registry_catches_secret_shape_and_binary(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1", "none", "baseline")
    (registry / "models" / "AXG-1" / "bad.ckpt").write_bytes(b"not a real checkpoint")
    fake_key = "sair_" + "123456789abc" + "_" + "abcdefghijklmnopqrstuvwx"
    (registry / "models" / "AXG-1" / "note.txt").write_text(fake_key, encoding="utf-8")

    validation = validate_registry(registry)

    assert validation["valid"] is False
    assert any(issue.startswith("checkpoint_binary_inside_registry") for issue in validation["issues"])
    assert any(issue.startswith("sair_key_shape_found") for issue in validation["issues"])


def test_record_run_links_run_manifest_to_model(tmp_path):
    registry = tmp_path / "registry"
    create_version(registry, "AXG-1", "none", "baseline")
    run_manifest_path = tmp_path / "run_manifest.json"
    run_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "record_type": "igp24_axg_proposal_run",
                "model_version": "AXG-1",
                "run_id": "run_20260707_000000",
                "safety": {"auto_submits": False, "calls_sair_post": False},
            }
        ),
        encoding="utf-8",
    )

    result = record_run(registry, "AXG-1", "run_20260707_000000", run_manifest_path)
    summary = summarize_registry(registry)

    assert result["run_manifest"].endswith("run_manifest.json")
    assert summary["models"][0]["run_count"] == 1
    assert validate_registry(registry)["valid"] is True
