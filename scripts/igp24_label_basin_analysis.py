#!/usr/bin/env python3
"""Analyze accepted IGP24 label basins from local SAIR feedback artifacts.

This helper normalizes the various accepted-feedback JSON shapes accumulated
while probing IGP24. It joins rows back to local candidate queues when possible
and emits compact basin features for label-steering decisions.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.igp24.verifiers.sair_api import SAIRAPIVerifier  # noqa: E402


DEFAULT_PAIR_STATUS = REPO_ROOT / "data/igp24/pair_status_20260706.json"
DEFAULT_TARGET_PLAN = REPO_ROOT / "data/igp24/sair_live_target_plan_20260707/sair_live_target_plan_summary.json"
OBSERVATIONS_JSONL = "label_basin_observations.jsonl"
SUMMARY_JSON = "label_basin_summary.json"
REPORT_MD = "label_basin_report.md"


def default_feedback_paths(root: Path = REPO_ROOT) -> list[Path]:
    return sorted(root.glob("data/igp24/**/*accepted_feedback*2026070*.json"))


def default_queue_paths(root: Path = REPO_ROOT) -> list[Path]:
    return sorted(root.glob("data/igp24/**/*candidate_queue.jsonl"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_pair_status(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("record_type") != "igp24_pair_status_ledger":
        raise ValueError(f"unexpected pair-status record_type in {path}")
    return payload


def index_queues(queue_paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for path in queue_paths:
        if not path.exists():
            continue
        for row in read_jsonl(path):
            canonical_hash = row.get("canonical_hash")
            if isinstance(canonical_hash, str) and canonical_hash and canonical_hash not in indexed:
                indexed[canonical_hash] = {**row, "_queue_path": str(path)}
    return indexed


def _accepted_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("accepted_rows")
    if isinstance(rows, list):
        return [row for row in rows if str(row.get("status") or "accepted") == "accepted"]
    rows = payload.get("rows")
    if isinstance(rows, list):
        return [row for row in rows if str(row.get("status") or "") == "accepted"]
    return []


def _label(row: dict[str, Any]) -> str:
    value = row.get("label") or row.get("verified_group_label")
    if not value:
        raise ValueError(f"accepted row missing label: {row}")
    return str(value)


def _r_value(row: dict[str, Any]) -> int:
    if row.get("r") is None:
        raise ValueError(f"accepted row missing r: {row}")
    return int(row["r"])


def _metadata_from(row: dict[str, Any], queue_row: dict[str, Any] | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if queue_row and isinstance(queue_row.get("generation_metadata"), dict):
        metadata.update(queue_row["generation_metadata"])
    if isinstance(row.get("tower_metadata"), dict):
        metadata.update(row["tower_metadata"])
    return metadata


def _exported_coefficients(row: dict[str, Any], queue_row: dict[str, Any] | None) -> list[int] | None:
    for source in (row, queue_row or {}):
        values = source.get("exported_coefficients")
        if isinstance(values, list) and len(values) == 25:
            return [int(value) for value in values]
        line = source.get("submission_line")
        if isinstance(line, str) and line.strip():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) == 25:
                return [int(part) for part in parts]
    return None


def support_summary(coefficients: list[int] | None) -> dict[str, Any]:
    if not coefficients:
        return {
            "support_exponents": [],
            "support_gcd": None,
            "even_support": None,
            "odd_support_exponents": [],
        }
    support = [index for index, value in enumerate(coefficients) if int(value) != 0]
    positive_support = [index for index in support if index > 0]
    support_gcd = 0
    for exponent in positive_support:
        support_gcd = math.gcd(support_gcd, exponent)
    return {
        "support_exponents": support,
        "support_gcd": support_gcd or None,
        "even_support": all(exponent % 2 == 0 for exponent in support),
        "odd_support_exponents": [exponent for exponent in support if exponent % 2 == 1],
    }


def _first_value(metadata: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = metadata.get(key)
        if value is not None:
            return value
    return None


def construction_family(metadata: dict[str, Any], row: dict[str, Any], feedback_path: Path) -> str:
    value = metadata.get("construction_family")
    if value:
        return str(value)
    source_mode = row.get("source_mode")
    record_hint = feedback_path.name.replace("_sair_accepted_feedback_20260706.json", "")
    return str(source_mode or record_hint)


def decomposition_pattern(metadata: dict[str, Any]) -> str | None:
    degree_pattern = metadata.get("decomposition_degree_pattern")
    if degree_pattern:
        return str(degree_pattern)
    decomposition_type = metadata.get("decomposition_type")
    divisor = _first_value(
        metadata,
        [
            "exact_composed_support_divisor",
            "r12_structured_exact_composed_support_divisor",
            "r24_high_real_exact_composed_seed_divisor",
            "near_composed_support_divisor",
        ],
    )
    if decomposition_type and divisor:
        return f"{decomposition_type}|support_divisor={divisor}"
    if divisor:
        return f"support_divisor={divisor}"
    return str(decomposition_type) if decomposition_type else None


def perturbation_mode(metadata: dict[str, Any], row: dict[str, Any]) -> str | None:
    return _first_value(
        metadata,
        [
            "r24_tower_mode",
            "r12_tower_mode",
            "alt_perturbation_mode",
            "r24_high_real_mode",
            "r20_high_real_mode",
            "r16_diversity_mode",
            "r12_structured_mode",
            "r24_high_real_perturbation_mode",
        ],
    ) or row.get("source_mode")


def perturbation_terms(metadata: dict[str, Any], row: dict[str, Any]) -> list[dict[str, int]]:
    candidates = [
        metadata.get("r24_tower_outer_perturbations"),
        metadata.get("r12_tower_outer_perturbations"),
        metadata.get("alt_outer_perturbations"),
        metadata.get("r24_high_real_odd_perturbations"),
        metadata.get("r20_high_real_perturbations"),
        metadata.get("r12_structured_base_perturbations"),
        metadata.get("r16_diversity_y_perturbation"),
        row.get("source_perturbations"),
        row.get("source_base_perturbations"),
    ]
    terms: list[dict[str, int]] = []
    for raw in candidates:
        if raw is None:
            continue
        items = raw if isinstance(raw, list) else [raw]
        for item in items:
            if not isinstance(item, dict):
                continue
            exponent = (
                item.get("outer_y_exponent")
                if item.get("outer_y_exponent") is not None
                else item.get("x_exponent")
                if item.get("x_exponent") is not None
                else item.get("y_exponent")
            )
            if exponent is None or item.get("delta") is None:
                continue
            terms.append({"exponent": int(exponent), "delta": int(item["delta"])})
        if terms:
            break
    return terms


def mod_pattern_signature(queue_row: dict[str, Any] | None) -> str | None:
    patterns = (queue_row or {}).get("mod_p_factorization_degree_patterns")
    if not isinstance(patterns, list) or not patterns:
        return None
    parts = []
    for pattern in patterns:
        if not isinstance(pattern, dict):
            continue
        degrees = "-".join(str(int(value)) for value in pattern.get("degrees") or [])
        parts.append(f"p{pattern.get('prime')}:{degrees}")
    return ";".join(sorted(parts)) or None


def normalize_observation(
    *,
    feedback_path: Path,
    feedback_payload: dict[str, Any],
    row: dict[str, Any],
    queue_by_hash: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    canonical_hash = str(row.get("canonical_hash") or "")
    queue_row = queue_by_hash.get(canonical_hash)
    metadata = _metadata_from(row, queue_row)
    exported = _exported_coefficients(row, queue_row)
    support = support_summary(exported)
    label = _label(row)
    r_value = _r_value(row)
    family_key = _first_value(
        metadata,
        [
            "alt_composition_family_key",
            "r24_tower_family_key",
            "r12_tower_family_key",
            "r24_high_real_family_key",
            "r20_high_real_family_key",
            "r16_diversity_family_key",
            "r12_structured_family_key",
        ],
    ) or row.get("source_family_key")
    outer_levels = _first_value(
        metadata,
        [
            "alt_outer_three_real_levels",
            "alt_outer_eight_real_levels",
            "r24_tower_outer_four_real_preimage_levels",
            "r12_tower_outer_four_real_preimage_levels",
            "r24_high_real_positive_quadratic_roots",
            "r20_high_real_positive_quadratic_roots",
            "r12_structured_positive_base_roots",
        ],
    )
    return {
        "feedback_path": str(feedback_path),
        "feedback_record_type": feedback_payload.get("record_type"),
        "source_queue_path": (queue_row or {}).get("_queue_path")
        or feedback_payload.get("source_queue_jsonl")
        or feedback_payload.get("source_queue")
        or feedback_payload.get("source_packet"),
        "row_number": row.get("row_number") or row.get("rank"),
        "canonical_hash": canonical_hash,
        "short_hash": str(row.get("short_hash") or canonical_hash[:12]),
        "label": label,
        "r": r_value,
        "pair_key": str(row.get("pair_key") or f"{label}|r={r_value}"),
        "status": str(row.get("status") or "accepted"),
        "score_status": row.get("score_status") or row.get("scoring_status"),
        "construction_family": construction_family(metadata, row, feedback_path),
        "decomposition_pattern": decomposition_pattern(metadata),
        "exact_support_divisor": _first_value(
            metadata,
            [
                "exact_composed_support_divisor",
                "r12_structured_exact_composed_support_divisor",
                "r24_high_real_exact_composed_seed_divisor",
            ],
        ),
        "near_support_divisor": _first_value(
            metadata,
            ["near_composed_support_divisor", "r24_high_real_near_composed_support_divisor"],
        ),
        "support_gcd": support["support_gcd"],
        "even_support": support["even_support"],
        "odd_support_exponents": support["odd_support_exponents"],
        "tower_inner_parameter_s": _first_value(
            metadata, ["r24_tower_inner_parameter_s", "r12_tower_inner_parameter_s"]
        ),
        "outer_or_base_levels": outer_levels,
        "perturbation_mode": perturbation_mode(metadata, row),
        "perturbation_terms": perturbation_terms(metadata, row),
        "coefficient_height": row.get("coefficient_height") or (queue_row or {}).get("coefficient_height"),
        "real_root_count": row.get("real_root_count") or (queue_row or {}).get("real_root_count") or r_value,
        "irreducible": row.get("irreducible") or (queue_row or {}).get("irreducible"),
        "squarefree": row.get("squarefree") or (queue_row or {}).get("squarefree"),
        "family_key": str(family_key or ""),
        "mod_p_pattern_signature": mod_pattern_signature(queue_row),
        "queue_joined": bool(queue_row),
    }


def load_observations(feedback_paths: Iterable[Path], queue_paths: Iterable[Path]) -> list[dict[str, Any]]:
    queue_by_hash = index_queues(queue_paths)
    observations: list[dict[str, Any]] = []
    for feedback_path in feedback_paths:
        payload = json.loads(feedback_path.read_text(encoding="utf-8"))
        for row in _accepted_rows(payload):
            observations.append(
                normalize_observation(
                    feedback_path=feedback_path,
                    feedback_payload=payload,
                    row=row,
                    queue_by_hash=queue_by_hash,
                )
            )
    observations.sort(key=lambda row: (row["r"], row["label"], str(row["row_number"]), row["canonical_hash"]))
    return observations


def fetch_progress_for_labels(labels: Iterable[str]) -> dict[str, Any]:
    unique = sorted({str(label) for label in labels if label})
    if not unique:
        return {}
    client = SAIRAPIVerifier(dry_run=False)
    payload = client.get_label_progress(labels=unique, include_empty=True, limit=max(100, len(unique)))
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    return {str(row.get("label")): row for row in data.get("labels") or [] if row.get("label")}


def load_progress_from_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels = payload.get("labels")
    if labels is None and isinstance(payload.get("data"), dict):
        labels = payload["data"].get("labels")
    if not isinstance(labels, list):
        return {}
    return {str(row.get("label")): row for row in labels if isinstance(row, dict) and row.get("label")}


def _height_range(rows: list[dict[str, Any]]) -> dict[str, int | None]:
    heights = [int(row["coefficient_height"]) for row in rows if row.get("coefficient_height") is not None]
    return {"min": min(heights) if heights else None, "max": max(heights) if heights else None}


def _counter_values(rows: list[dict[str, Any]], key: str, *, limit: int = 20) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows if row.get(key) not in (None, ""))
    return dict(counter.most_common(limit))


def _progress_summary(label: str, progress_by_label: dict[str, Any]) -> dict[str, Any]:
    row = progress_by_label.get(label) or {}
    remaining = [int(value) for value in row.get("remainingSignatures") or []]
    discovered = [int(value) for value in row.get("discoveredSignatures") or []]
    return {
        "team_count": row.get("teamCount"),
        "allowed_r": row.get("allowedR") or [],
        "discovered_r": discovered,
        "remaining_r": remaining,
        "fully_covered": bool(row) and not remaining,
        "minimum_disc_abs": row.get("minimumDiscAbs"),
    }


def build_summary(
    observations: list[dict[str, Any]],
    *,
    pair_status: dict[str, Any],
    target_plan: dict[str, Any] | None,
    progress_by_label: dict[str, Any],
    feedback_paths: list[Path],
    queue_paths: list[Path],
) -> dict[str, Any]:
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        by_label[row["label"]].append(row)
        by_pair[row["pair_key"]].append(row)
        by_family[str(row.get("construction_family"))].append(row)

    label_summary: dict[str, Any] = {}
    for label, rows in sorted(by_label.items()):
        label_summary[label] = {
            "accepted_rows": len(rows),
            "r_counts": dict(sorted(Counter(int(row["r"]) for row in rows).items())),
            "construction_family_counts": _counter_values(rows, "construction_family"),
            "perturbation_mode_counts": _counter_values(rows, "perturbation_mode"),
            "support_gcd_counts": _counter_values(rows, "support_gcd"),
            "decomposition_pattern_counts": _counter_values(rows, "decomposition_pattern"),
            "mod_p_pattern_counts": _counter_values(rows, "mod_p_pattern_signature"),
            "height_range": _height_range(rows),
            "global_progress": _progress_summary(label, progress_by_label),
        }

    pair_summary: dict[str, Any] = {}
    for pair_key, rows in sorted(by_pair.items()):
        label = str(rows[0]["label"])
        r_value = int(rows[0]["r"])
        progress = progress_by_label.get(label) or {}
        pair_summary[pair_key] = {
            "accepted_rows": len(rows),
            "label": label,
            "r": r_value,
            "construction_family_counts": _counter_values(rows, "construction_family"),
            "perturbation_mode_counts": _counter_values(rows, "perturbation_mode"),
            "family_key_counts": _counter_values(rows, "family_key", limit=10),
            "support_gcd_counts": _counter_values(rows, "support_gcd"),
            "height_range": _height_range(rows),
            "global_pair_discovered": r_value in [int(value) for value in progress.get("discoveredSignatures") or []],
            "global_label_fully_covered": bool(progress) and not (progress.get("remainingSignatures") or []),
        }

    family_summary: dict[str, Any] = {}
    for family, rows in sorted(by_family.items()):
        family_summary[family] = {
            "accepted_rows": len(rows),
            "label_counts": dict(Counter(row["label"] for row in rows).most_common()),
            "r_counts": dict(sorted(Counter(int(row["r"]) for row in rows).items())),
            "perturbation_mode_counts": _counter_values(rows, "perturbation_mode"),
            "support_gcd_counts": _counter_values(rows, "support_gcd"),
            "height_range": _height_range(rows),
        }

    anti_basin_constraints = derive_anti_basin_constraints(observations, label_summary, pair_summary)
    target_plan_summary = {
        "remaining_signature_count": (target_plan or {}).get("remaining_signature_count"),
        "top_remaining_rs": (target_plan or {}).get("top_remaining_rs"),
        "primary_target": (target_plan or {}).get("primary_target"),
        "recommended_lane": (target_plan or {}).get("recommended_lane"),
    }
    return {
        "schema_version": 1,
        "record_type": "igp24_label_basin_analysis",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/igp24_label_basin_analysis.py",
        "inputs": {
            "feedback_paths": [str(path) for path in feedback_paths],
            "queue_paths": [str(path) for path in queue_paths],
            "pair_status_pairs": len(pair_status.get("pairs") or []),
            "target_plan": target_plan_summary,
            "progress_labels_loaded": sorted(progress_by_label),
        },
        "observation_count": len(observations),
        "label_summary": label_summary,
        "pair_summary": pair_summary,
        "family_summary": family_summary,
        "anti_basin_constraints": anti_basin_constraints,
        "next_lane_decision": {
            "recommended": (
                "Do not submit more nearby r24 6x4 tower variants: exact even towers hit "
                "24T23883/24T24651, while odd-escaped 6x4 towers hit generic 24T25000. "
                "The alternate-composition 8x3 lane now also has a tracked collapse into "
                "globally covered 24T24932 across constant and nonconstant outer "
                "perturbations. Next generated queue must use a different composition "
                "pattern, a materially different inner family, or a stronger label-steering "
                "signal before any SAIR submission."
            ),
            "gpu_training_recommended_now": False,
            "submission_without_new_structure_recommended": False,
        },
    }


def derive_anti_basin_constraints(
    observations: list[dict[str, Any]],
    label_summary: dict[str, Any],
    pair_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    label_counts = Counter(row["label"] for row in observations)
    common_labels = sorted(label for label, count in label_counts.items() if count >= 5 or label in {"24T25000", "24T24979", "24T24651", "24T23883"})
    constraints.append(
        {
            "name": "avoid_common_labels_without_new_structure",
            "severity": "high",
            "labels": common_labels,
            "rule": "Do not spend more submissions on rows predicted to remain in these basins unless the structure differs in support divisor, composition pattern, perturbation mode, or mod-p signature.",
        }
    )
    exact_even_tower_rows = [
        row
        for row in observations
        if row.get("decomposition_pattern") == "6x4"
        and row.get("even_support") is True
        and row.get("perturbation_mode") == "outer_constant_shift"
    ]
    if exact_even_tower_rows:
        constraints.append(
            {
                "name": "stop_exact_even_6x4_constant_shift_towers",
                "severity": "high",
                "labels": sorted(set(row["label"] for row in exact_even_tower_rows)),
                "r_values": sorted(set(int(row["r"]) for row in exact_even_tower_rows)),
                "observed_rows": len(exact_even_tower_rows),
                "rule": "Require non-even support, non-constant outer perturbations, or a different decomposition degree pattern before submitting more tower rows.",
            }
        )
    generic_rows = [row for row in observations if row["label"] == "24T25000"]
    if generic_rows:
        constraints.append(
            {
                "name": "avoid_generic_24T25000_perturbation_lanes",
                "severity": "high",
                "r_values": sorted(set(int(row["r"]) for row in generic_rows)),
                "construction_family_counts": _counter_values(generic_rows, "construction_family"),
                "rule": "Do not widen product/composed seed plus low odd perturbation lanes that already collapsed to 24T25000.",
            }
        )
    odd_escaped_tower_rows = [
        row
        for row in observations
        if row.get("construction_family") == "odd_perturbed_r24_6x4_tower_escape"
        or row.get("decomposition_pattern") == "6x4_seed_plus_odd_x_perturbation"
    ]
    if odd_escaped_tower_rows:
        constraints.append(
            {
                "name": "stop_odd_escaped_r24_6x4_towers",
                "severity": "high",
                "labels": sorted(set(row["label"] for row in odd_escaped_tower_rows)),
                "r_values": sorted(set(int(row["r"]) for row in odd_escaped_tower_rows)),
                "observed_rows": len(odd_escaped_tower_rows),
                "rule": (
                    "Odd x-perturbed r24 6x4 tower rows broke exact even support but collapsed "
                    "to generic 24T25000; use a different composition pattern before submitting "
                    "more r24 tower-derived rows."
                ),
            }
        )
    alt_8x3_24932_rows = [
        row
        for row in observations
        if row.get("construction_family") == "alt_composition_8x3"
        and row.get("decomposition_pattern") == "8x3"
        and row.get("label") == "24T24932"
    ]
    if alt_8x3_24932_rows:
        constraints.append(
            {
                "name": "stop_plain_8x3_24T24932_lanes",
                "severity": "high",
                "labels": ["24T24932"],
                "r_values": sorted(set(int(row["r"]) for row in alt_8x3_24932_rows)),
                "observed_rows": len(alt_8x3_24932_rows),
                "perturbation_mode_counts": _counter_values(alt_8x3_24932_rows, "perturbation_mode"),
                "rule": (
                    "Plain 8x3 alternate compositions, including outer constant shifts and "
                    "the tested nonconstant outer coefficient shifts, collapsed to globally "
                    "covered 24T24932; require a different degree pattern, inner family, or "
                    "stronger mod-p/label-steering discriminator before submitting more 8x3 rows."
                ),
            }
        )
    divisor2_rows = [row for row in observations if row.get("support_gcd") == 2 or row.get("exact_support_divisor") == 2]
    if divisor2_rows:
        constraints.append(
            {
                "name": "require_divisor2_escape_feature",
                "severity": "medium",
                "observed_rows": len(divisor2_rows),
                "dominant_labels": dict(Counter(row["label"] for row in divisor2_rows).most_common(6)),
                "rule": "Exact divisor-2 support is now a known basin feature; require odd support or a different support divisor unless doing discriminant-only alternates.",
            }
        )
    constraints.append(
        {
            "name": "mod_p_pattern_novelty",
            "severity": "medium",
            "rule": "For future queues, compute mod-p signatures and prefer rows with signatures absent from accepted common-label observations.",
        }
    )
    return constraints


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# IGP24 Label Basin Analysis",
        "",
        f"- Observations: {summary['observation_count']}",
        f"- Feedback files: {len(summary['inputs']['feedback_paths'])}",
        f"- Queue files: {len(summary['inputs']['queue_paths'])}",
        f"- Progress labels loaded: {len(summary['inputs']['progress_labels_loaded'])}",
        "",
        "## Label Summary",
        "",
        "| label | rows | r counts | global fully covered | team count | dominant families |",
        "| --- | ---: | --- | --- | ---: | --- |",
    ]
    for label, row in sorted(summary["label_summary"].items(), key=lambda item: (-item[1]["accepted_rows"], item[0])):
        progress = row.get("global_progress") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    str(row["accepted_rows"]),
                    json.dumps(row["r_counts"], sort_keys=True),
                    str(progress.get("fully_covered")),
                    str(progress.get("team_count")),
                    json.dumps(row["construction_family_counts"], sort_keys=True),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Pair Basins", "", "| pair | rows | global discovered | fully covered label | families | modes |", "| --- | ---: | --- | --- | --- | --- |"])
    for pair_key, row in sorted(summary["pair_summary"].items(), key=lambda item: (-item[1]["accepted_rows"], item[0]))[:30]:
        lines.append(
            "| "
            + " | ".join(
                [
                    pair_key,
                    str(row["accepted_rows"]),
                    str(row["global_pair_discovered"]),
                    str(row["global_label_fully_covered"]),
                    json.dumps(row["construction_family_counts"], sort_keys=True),
                    json.dumps(row["perturbation_mode_counts"], sort_keys=True),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Anti-Basin Constraints", ""])
    for item in summary["anti_basin_constraints"]:
        lines.append(f"- **{item['name']}** ({item['severity']}): {item['rule']}")
    lines.extend(["", "## Next Lane Decision", "", summary["next_lane_decision"]["recommended"], ""])
    return "\n".join(lines)


def write_outputs(
    *,
    observations: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    observations_path = output_dir / OBSERVATIONS_JSONL
    summary_path = output_dir / SUMMARY_JSON
    report_path = output_dir / REPORT_MD
    with observations_path.open("w", encoding="utf-8") as handle:
        for row in observations:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary_with_outputs = {
        **summary,
        "output_files": {
            "observations_jsonl": str(observations_path),
            "summary_json": str(summary_path),
            "report_md": str(report_path),
        },
    }
    summary_path.write_text(json.dumps(summary_with_outputs, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    report_path.write_text(build_report(summary_with_outputs), encoding="utf-8")
    return {
        "observations_jsonl": observations_path,
        "summary_json": summary_path,
        "report_md": report_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze accepted IGP24 label basins")
    parser.add_argument("--pair_status_json", type=Path, default=DEFAULT_PAIR_STATUS)
    parser.add_argument("--target_plan_summary_json", type=Path, default=DEFAULT_TARGET_PLAN)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--feedback_json", type=Path, action="append")
    parser.add_argument("--queue_jsonl", type=Path, action="append")
    parser.add_argument("--progress_json")
    parser.add_argument("--fetch_label_progress", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    feedback_paths = args.feedback_json or default_feedback_paths()
    queue_paths = args.queue_jsonl or default_queue_paths()
    pair_status = load_pair_status(args.pair_status_json)
    target_plan = (
        json.loads(args.target_plan_summary_json.read_text(encoding="utf-8"))
        if args.target_plan_summary_json.exists()
        else {}
    )
    observations = load_observations(feedback_paths, queue_paths)
    progress_by_label = load_progress_from_json(Path(args.progress_json)) if args.progress_json else {}
    if args.fetch_label_progress:
        progress_by_label.update(fetch_progress_for_labels(row["label"] for row in observations))
    summary = build_summary(
        observations,
        pair_status=pair_status,
        target_plan=target_plan,
        progress_by_label=progress_by_label,
        feedback_paths=list(feedback_paths),
        queue_paths=list(queue_paths),
    )
    paths = write_outputs(observations=observations, summary=summary, output_dir=args.output_dir)
    print(f"observations\t{len(observations)}")
    print(f"labels\t{len(summary['label_summary'])}")
    print(f"pairs\t{len(summary['pair_summary'])}")
    print(f"constraints\t{len(summary['anti_basin_constraints'])}")
    for name, path in paths.items():
        print(f"{name}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
