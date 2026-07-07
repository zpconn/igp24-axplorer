#!/usr/bin/env python3
"""Manage AXG model-version manifests for the IGP24 active-learning loop."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "data/igp24/model_registry"
VERSION_RE = re.compile(r"^AXG-(?P<major>[1-9][0-9]*)(?:\.(?P<minor>[1-9][0-9]*))?$")
SAIR_KEY_RE = re.compile(r"sair_[0-9a-f]{12}_[A-Za-z0-9]{20,}")
BINARY_EXTENSIONS = {".bin", ".ckpt", ".gguf", ".onnx", ".pt", ".pth", ".safetensors"}
MAX_REGISTRY_FILE_BYTES = 2_000_000

REQUIRED_MODEL_FIELDS = [
    "schema_version",
    "record_type",
    "model_version",
    "parent_version",
    "created_at",
    "git_commit",
    "description",
    "purpose",
    "training_command",
    "training_data_inputs",
    "excluded_leakage_prevention_inputs",
    "objective_loss_configuration",
    "conditioning_fields",
    "architecture_config",
    "random_seed",
    "training_duration",
    "device_gpu_info",
    "checkpoint_paths",
    "sample_export_paths",
    "validation_metrics",
    "known_limitations",
    "sair_submission",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_commit(repo_root: Path = REPO_ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except Exception:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def version_sort_key(version: str) -> tuple[int, int]:
    match = VERSION_RE.match(version)
    if not match:
        raise ValueError(f"invalid AXG model version: {version}")
    major = int(match.group("major"))
    minor = int(match.group("minor") or 0)
    return major, minor


def validate_version(version: str) -> str:
    version_sort_key(version)
    return version


def model_dir(registry: Path, version: str) -> Path:
    return registry / "models" / version


def run_dir(registry: Path, version: str, run_id: str) -> Path:
    return registry / "runs" / version / run_id


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def registry_readme_text() -> str:
    return """# AXG Model Registry

AXG means Axplorer Generator. This registry tracks trained or planned IGP24
generator versions used for active learning.

Version rules:

- Integer versions such as `AXG-1` are full training generations.
- Decimal versions such as `AXG-1.5` are intermediate tuned/checkpoint
  generations with the same broad architecture and a meaningful data, sampler,
  or discriminator update.
- Model versions are never overwritten. New training attempt, new run id; new
  model generation, new AXG version.

Safety rules:

- Checkpoint files are referenced by path in manifests; large weight binaries
  are not stored here.
- SAIR API keys must never be written here.
- SAIR submission remains explicit and gated. GPU samples are proposals only.
"""


def init_registry(registry: Path) -> dict[str, Any]:
    (registry / "models").mkdir(parents=True, exist_ok=True)
    (registry / "runs").mkdir(parents=True, exist_ok=True)
    readme = registry / "README.md"
    if not readme.exists():
        readme.write_text(registry_readme_text(), encoding="utf-8")
    return {
        "registry": str(registry),
        "models_dir": str(registry / "models"),
        "runs_dir": str(registry / "runs"),
        "readme": str(readme),
    }


def default_model_manifest(version: str, parent: str, description: str) -> dict[str, Any]:
    validate_version(version)
    if parent != "none":
        validate_version(parent)
    return {
        "schema_version": 1,
        "record_type": "igp24_axg_model_manifest",
        "model_version": version,
        "parent_version": parent,
        "created_at": utc_now(),
        "git_commit": git_commit(),
        "description": description,
        "purpose": "Baseline GPU proposal generator for IGP24 active learning.",
        "training_command": {
            "status": "not_started",
            "command": None,
            "recommended_template": [
                "python3",
                "scripts/igp24_gpu_sampler_probe.py",
                "--probe_mode",
                "sample_export_split_dedup",
            ],
        },
        "training_data_inputs": [
            "data/igp24/pair_status_20260706.json",
            "data/igp24/sair_sync_basin_gate_20260707/",
            "data/igp24/*accepted_feedback*.json",
            "data/igp24/**/*candidate_queue.jsonl",
        ],
        "excluded_leakage_prevention_inputs": [
            "SAIR API keys",
            "unreleased future verifier outputs",
            "raw live submission responses not represented as training labels",
        ],
        "objective_loss_configuration": {
            "primary": "proposal generation for valid degree-24 integer polynomials",
            "secondary": "conditioned active-learning labels for exact-r yield and basin avoidance",
            "loss": "not_configured_yet",
        },
        "conditioning_fields": [
            "target_r",
            "construction_family",
            "support_pattern_class",
            "height_bucket",
            "known_basin_avoidance_flag",
        ],
        "architecture_config": {
            "base_entrypoint": "train.py",
            "status": "baseline_transformer_config_pending_full_training",
        },
        "random_seed": None,
        "training_duration": {
            "status": "not_started",
            "seconds": 0,
        },
        "device_gpu_info": {
            "status": "not_started",
            "expected": "CUDA GPU when --cpu false",
        },
        "checkpoint_paths": [],
        "sample_export_paths": [],
        "validation_metrics": {
            "status": "not_started",
            "success_metrics": [
                "valid exact-r yield after CPU filters",
                "diversity by family/mod-p/support",
                "basin-risk distribution",
                "reviewed candidates surviving strict gate",
                "information value per SAIR row if later submitted",
            ],
        },
        "known_limitations": [
            "AXG-1 is initially a registry and dry-run scaffold, not a completed long training run.",
            "GPU samples must pass CPU filters and basin gates before any submission review.",
        ],
        "sair_submission": {
            "raw_gpu_samples_submitted": False,
            "automatic_live_submission": False,
            "submitted_to_sair": False,
            "notes": "Submission is explicit and gated outside model training.",
        },
        "runs": [],
    }


def create_version(registry: Path, version: str, parent: str, description: str) -> dict[str, Any]:
    init_registry(registry)
    validate_version(version)
    destination = model_dir(registry, version)
    if destination.exists():
        raise FileExistsError(f"model version already exists: {destination}")
    if parent != "none" and not (model_dir(registry, parent) / "model_manifest.json").exists():
        raise FileNotFoundError(f"parent model version does not exist: {parent}")

    manifest = default_model_manifest(version, parent, description)
    destination.mkdir(parents=True)
    write_json(destination / "model_manifest.json", manifest)
    (destination / "training_summary.md").write_text(
        f"# {version} Training Summary\n\nStatus: not started.\n", encoding="utf-8"
    )
    write_json(
        destination / "sample_summary.json",
        {
            "schema_version": 1,
            "record_type": "igp24_axg_sample_summary",
            "model_version": version,
            "status": "not_started",
            "sample_exports": [],
        },
    )
    write_json(
        destination / "feedback_summary.json",
        {
            "schema_version": 1,
            "record_type": "igp24_axg_feedback_summary",
            "model_version": version,
            "status": "initialized",
            "sair_feedback_rows": 0,
            "notes": [],
        },
    )
    return {"created": str(destination), "manifest": str(destination / "model_manifest.json")}


def inspect_for_secret_and_binary_files(registry: Path, *, max_file_bytes: int) -> list[str]:
    issues: list[str] = []
    if not registry.exists():
        issues.append(f"registry_missing:{registry}")
        return issues
    for path in registry.rglob("*"):
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            issues.append(f"file_too_large:{path}:{size}")
        if path.suffix.lower() in BINARY_EXTENSIONS:
            issues.append(f"checkpoint_binary_inside_registry:{path}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append(f"non_text_file_inside_registry:{path}")
            continue
        if SAIR_KEY_RE.search(text):
            issues.append(f"sair_key_shape_found:{path}")
    return issues


def _checkpoint_paths_are_references(value: Any, prefix: str = "checkpoint_paths") -> list[str]:
    issues: list[str] = []
    if isinstance(value, str):
        return issues
    if isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(_checkpoint_paths_are_references(item, f"{prefix}[{index}]"))
        return issues
    if isinstance(value, dict):
        if any(key in value for key in ("bytes", "content", "data", "base64", "weights")):
            issues.append(f"embedded_checkpoint_payload:{prefix}")
        if "path" not in value and "uri" not in value and "description" not in value:
            issues.append(f"checkpoint_reference_missing_path_or_uri:{prefix}")
        for key, item in value.items():
            if key not in {"path", "uri", "description", "sha256", "size_bytes"}:
                if isinstance(item, (dict, list)):
                    issues.extend(_checkpoint_paths_are_references(item, f"{prefix}.{key}"))
        return issues
    if value is not None:
        issues.append(f"checkpoint_reference_invalid_type:{prefix}:{type(value).__name__}")
    return issues


def validate_model_manifest(
    manifest: dict[str, Any],
    *,
    registry: Path,
    known_versions: set[str],
) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_MODEL_FIELDS:
        if field not in manifest:
            issues.append(f"missing_required_field:{manifest.get('model_version', '<unknown>')}:{field}")
    version = str(manifest.get("model_version") or "")
    try:
        validate_version(version)
    except ValueError as exc:
        issues.append(str(exc))
    parent = str(manifest.get("parent_version") or "")
    if parent != "none" and parent not in known_versions:
        issues.append(f"parent_missing:{version}:{parent}")
    if manifest.get("record_type") != "igp24_axg_model_manifest":
        issues.append(f"bad_record_type:{version}:{manifest.get('record_type')}")
    submission = manifest.get("sair_submission") or {}
    if submission.get("raw_gpu_samples_submitted"):
        issues.append(f"raw_gpu_samples_marked_submitted:{version}")
    if submission.get("automatic_live_submission"):
        issues.append(f"automatic_live_submission_enabled:{version}")
    issues.extend(_checkpoint_paths_are_references(manifest.get("checkpoint_paths")))
    model_path = model_dir(registry, version) / "model_manifest.json"
    if model_path.exists() and read_json(model_path).get("model_version") != version:
        issues.append(f"manifest_path_version_mismatch:{model_path}")
    return issues


def validate_registry(registry: Path, *, max_file_bytes: int = MAX_REGISTRY_FILE_BYTES) -> dict[str, Any]:
    issues = inspect_for_secret_and_binary_files(registry, max_file_bytes=max_file_bytes)
    model_paths = sorted((registry / "models").glob("AXG-*/model_manifest.json")) if registry.exists() else []
    manifests = [read_json(path) for path in model_paths]
    versions = [str(manifest.get("model_version") or "") for manifest in manifests]
    duplicates = sorted({version for version in versions if versions.count(version) > 1})
    for version in duplicates:
        issues.append(f"duplicate_model_version:{version}")
    known_versions = set(versions)
    for manifest in manifests:
        issues.extend(validate_model_manifest(manifest, registry=registry, known_versions=known_versions))

    run_manifest_paths = sorted((registry / "runs").glob("AXG-*/*/run_manifest.json")) if registry.exists() else []
    for path in run_manifest_paths:
        payload = read_json(path)
        version = str(payload.get("model_version") or "")
        if version not in known_versions:
            issues.append(f"run_references_unknown_model:{path}:{version}")
        safety = payload.get("safety") or {}
        if safety.get("auto_submits") or safety.get("calls_sair_post"):
            issues.append(f"unsafe_run_manifest:{path}")

    return {
        "schema_version": 1,
        "record_type": "igp24_axg_registry_validation",
        "created_at": utc_now(),
        "registry": str(registry),
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "model_count": len(manifests),
        "run_count": len(run_manifest_paths),
        "models": sorted(versions, key=version_sort_key),
    }


def summarize_registry(registry: Path) -> dict[str, Any]:
    model_paths = sorted((registry / "models").glob("AXG-*/model_manifest.json"))
    models = []
    for path in model_paths:
        manifest = read_json(path)
        version = str(manifest.get("model_version"))
        runs = sorted((registry / "runs" / version).glob("*/run_manifest.json"))
        models.append(
            {
                "model_version": version,
                "parent_version": manifest.get("parent_version"),
                "description": manifest.get("description"),
                "training_status": (manifest.get("training_duration") or {}).get("status"),
                "run_count": len(runs),
                "submitted_to_sair": (manifest.get("sair_submission") or {}).get("submitted_to_sair"),
            }
        )
    models.sort(key=lambda row: version_sort_key(row["model_version"]))
    return {
        "schema_version": 1,
        "record_type": "igp24_axg_registry_summary",
        "created_at": utc_now(),
        "registry": str(registry),
        "model_count": len(models),
        "models": models,
    }


def record_run(registry: Path, version: str, run_id: str, manifest_path: Path) -> dict[str, Any]:
    validate_version(version)
    model_manifest_path = model_dir(registry, version) / "model_manifest.json"
    if not model_manifest_path.exists():
        raise FileNotFoundError(f"unknown model version: {version}")
    destination = run_dir(registry, version, run_id)
    if destination.exists():
        raise FileExistsError(f"run already exists: {destination}")
    run_manifest = read_json(manifest_path)
    if run_manifest.get("model_version") != version:
        raise ValueError(f"run manifest model_version does not match {version}")
    if SAIR_KEY_RE.search(json.dumps(run_manifest)):
        raise ValueError("run manifest contains SAIR key-shaped string")
    destination.mkdir(parents=True)
    write_json(destination / "run_manifest.json", run_manifest)

    model_manifest = read_json(model_manifest_path)
    runs = list(model_manifest.get("runs") or [])
    runs.append(
        {
            "run_id": run_id,
            "run_manifest": str(destination / "run_manifest.json"),
            "recorded_at": utc_now(),
        }
    )
    model_manifest["runs"] = runs
    write_json(model_manifest_path, model_manifest)
    return {"recorded_run": str(destination), "run_manifest": str(destination / "run_manifest.json")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-registry")

    create = subparsers.add_parser("create-version")
    create.add_argument("--version", required=True)
    create.add_argument("--parent", required=True)
    create.add_argument("--description", required=True)

    record = subparsers.add_parser("record-run")
    record.add_argument("--version", required=True)
    record.add_argument("--run-id", required=True)
    record.add_argument("--manifest", type=Path, required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--output_json", type=Path)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--output_json", type=Path)
    validate.add_argument("--max_file_bytes", type=int, default=MAX_REGISTRY_FILE_BYTES)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = args.registry
    if args.command == "init-registry":
        print(json.dumps(init_registry(registry), indent=2, sort_keys=True))
        return 0
    if args.command == "create-version":
        print(json.dumps(create_version(registry, args.version, args.parent, args.description), indent=2, sort_keys=True))
        return 0
    if args.command == "record-run":
        print(json.dumps(record_run(registry, args.version, args.run_id, args.manifest), indent=2, sort_keys=True))
        return 0
    if args.command == "summarize":
        payload = summarize_registry(registry)
        if args.output_json:
            write_json(args.output_json, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.command == "validate":
        payload = validate_registry(registry, max_file_bytes=args.max_file_bytes)
        if args.output_json:
            write_json(args.output_json, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["valid"] else 1
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
