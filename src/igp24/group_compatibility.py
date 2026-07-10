"""Group-cycle compatibility helpers for IGP24 candidates.

For an unramified prime p, the factorization degrees of a polynomial modulo p
give a Frobenius cycle type. The exact Galois group must contain that cycle
type. This module implements the sound set-intersection layer over a prebuilt
SQLite index of degree-24 transitive-group cycle types.

Compatibility is necessary evidence only. It is never an exact-label claim.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

SCHEMA_VERSION = 1
RECORD_TYPE = "igp24_group_cycle_index"
DEGREE = 24
EXPECTED_GLOBAL_GROUP_COUNT = 25000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cycle_type_key(degrees: Iterable[int]) -> str:
    values = tuple(sorted(int(value) for value in degrees if int(value) > 0))
    if not values or sum(values) != DEGREE:
        raise ValueError(f"invalid degree-24 cycle type: {values}")
    return ".".join(str(value) for value in values)


def parse_cycle_type_key(value: str) -> tuple[int, ...]:
    if not value:
        raise ValueError("empty_cycle_type")
    return tuple(int(part) for part in value.split("."))


def is_square_integer(value: int | None) -> bool | None:
    if value is None:
        return None
    root = math.isqrt(abs(int(value)))
    return root * root == abs(int(value))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


@dataclass(frozen=True)
class GroupRecord:
    label: str
    t: int
    degree: int = DEGREE
    order: int | None = None
    primitive: bool | None = None
    solvable: bool | None = None
    parity: str | None = None
    block_sizes: tuple[int, ...] = ()
    cycle_types: tuple[str, ...] = ()
    status: str = "complete"
    provenance: dict[str, Any] | None = None

    def as_json(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "t": self.t,
            "degree": self.degree,
            "order": self.order,
            "primitive": self.primitive,
            "solvable": self.solvable,
            "parity": self.parity,
            "block_sizes": list(self.block_sizes),
            "cycle_types": list(self.cycle_types),
            "status": self.status,
            "provenance": self.provenance or {},
        }


class GroupCycleIndex:
    """SQLite-backed degree-24 group cycle-type index."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(
        self,
        *,
        provenance: dict[str, Any] | None = None,
        index_scope: str = "target_subset",
        expected_global_group_count: int = EXPECTED_GLOBAL_GROUP_COUNT,
        global_index_complete: bool = False,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS groups (
                    label TEXT PRIMARY KEY,
                    t INTEGER NOT NULL,
                    degree INTEGER NOT NULL,
                    group_order TEXT,
                    primitive INTEGER,
                    solvable INTEGER,
                    parity TEXT,
                    block_sizes_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provenance_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS group_cycle_types (
                    label TEXT NOT NULL,
                    cycle_type TEXT NOT NULL,
                    PRIMARY KEY (label, cycle_type),
                    FOREIGN KEY (label) REFERENCES groups(label) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_group_cycle_type ON group_cycle_types(cycle_type, label);
                """
            )
            metadata = {
                "schema_version": SCHEMA_VERSION,
                "record_type": RECORD_TYPE,
                "degree": DEGREE,
                "created_at": utc_now(),
                "index_scope": index_scope,
                "expected_global_group_count": int(expected_global_group_count),
                "global_index_complete": bool(global_index_complete),
                "provenance": provenance or {},
            }
            for key, value in metadata.items():
                conn.execute(
                    "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                    (key, json.dumps(value, sort_keys=True)),
                )

    def metadata(self) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute("SELECT key, value FROM metadata").fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}

    def scope_metadata(self) -> dict[str, Any]:
        metadata = self.metadata()
        indexed_group_count = self.group_count()
        expected = int(metadata.get("expected_global_group_count") or EXPECTED_GLOBAL_GROUP_COUNT)
        global_complete = bool(metadata.get("global_index_complete")) or indexed_group_count >= expected
        scope = str(metadata.get("index_scope") or ("complete_degree24_universe" if global_complete else "target_subset"))
        if global_complete:
            scope = "complete_degree24_universe"
        return {
            "index_scope": scope,
            "indexed_group_count": indexed_group_count,
            "expected_global_group_count": expected,
            "global_index_complete": global_complete,
            "unindexed_label_mass_unknown": not global_complete,
            "soundness": "necessary_target_exclusion_only",
        }

    def upsert_group(self, record: GroupRecord) -> None:
        self.upsert_groups([record])

    def upsert_groups(self, records: Iterable[GroupRecord]) -> None:
        prepared: list[tuple[GroupRecord, list[str]]] = []
        for record in records:
            if record.degree != DEGREE:
                raise ValueError(f"expected degree {DEGREE}, got {record.degree}")
            cycle_types = sorted({cycle_type_key(parse_cycle_type_key(value)) for value in record.cycle_types})
            prepared.append((record, cycle_types))
        if not prepared:
            return
        labels = [record.label for record, _cycle_types in prepared]
        with self.connect() as conn:
            conn.executemany("DELETE FROM group_cycle_types WHERE label = ?", [(label,) for label in labels])
            conn.executemany(
                """
                INSERT OR REPLACE INTO groups(
                    label, t, degree, group_order, primitive, solvable, parity,
                    block_sizes_json, status, provenance_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.label,
                        int(record.t),
                        int(record.degree),
                        str(record.order) if record.order is not None else None,
                        None if record.primitive is None else int(bool(record.primitive)),
                        None if record.solvable is None else int(bool(record.solvable)),
                        record.parity,
                        json.dumps(list(record.block_sizes), sort_keys=True),
                        record.status,
                        json.dumps(record.provenance or {}, sort_keys=True),
                    )
                    for record, _cycle_types in prepared
                ],
            )
            conn.executemany(
                "INSERT OR IGNORE INTO group_cycle_types(label, cycle_type) VALUES (?, ?)",
                [
                    (record.label, cycle_type)
                    for record, cycle_types in prepared
                    for cycle_type in cycle_types
                ],
            )

    def group_count(self) -> int:
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM groups WHERE status = 'complete'").fetchone()[0])

    def all_labels(self) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT label FROM groups WHERE status = 'complete'").fetchall()
        return {str(row["label"]) for row in rows}

    def labels_for_cycle_type(self, cycle_type: str) -> set[str]:
        key = cycle_type_key(parse_cycle_type_key(cycle_type))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT g.label
                FROM groups g
                JOIN group_cycle_types c ON c.label = g.label
                WHERE c.cycle_type = ? AND g.status = 'complete'
                """,
                (key,),
            ).fetchall()
        return {str(row["label"]) for row in rows}

    def records_for_labels(self, labels: Iterable[str]) -> dict[str, GroupRecord]:
        label_list = sorted({str(label) for label in labels})
        if not label_list:
            return {}
        placeholders = ",".join("?" for _ in label_list)
        with self.connect() as conn:
            group_rows = conn.execute(
                f"SELECT * FROM groups WHERE label IN ({placeholders})",
                label_list,
            ).fetchall()
            cycle_rows = conn.execute(
                f"SELECT label, cycle_type FROM group_cycle_types WHERE label IN ({placeholders})",
                label_list,
            ).fetchall()
        cycles: dict[str, list[str]] = {}
        for row in cycle_rows:
            cycles.setdefault(str(row["label"]), []).append(str(row["cycle_type"]))
        records: dict[str, GroupRecord] = {}
        for row in group_rows:
            label = str(row["label"])
            records[label] = GroupRecord(
                label=label,
                t=int(row["t"]),
                degree=int(row["degree"]),
                order=int(row["group_order"]) if row["group_order"] is not None else None,
                primitive=None if row["primitive"] is None else bool(row["primitive"]),
                solvable=None if row["solvable"] is None else bool(row["solvable"]),
                parity=row["parity"],
                block_sizes=tuple(json.loads(row["block_sizes_json"] or "[]")),
                status=str(row["status"]),
                provenance=json.loads(row["provenance_json"] or "{}"),
                cycle_types=tuple(sorted(cycles.get(label, []))),
            )
        return records


def observed_cycle_evidence(row: dict[str, Any]) -> list[dict[str, Any]]:
    patterns = row.get("mod_p_factorization_degree_patterns")
    if not isinstance(patterns, list):
        candidate = row.get("candidate") if isinstance(row.get("candidate"), dict) else {}
        patterns = candidate.get("mod_p_factorization_degree_patterns")
    evidence: list[dict[str, Any]] = []
    for pattern in patterns or []:
        if not isinstance(pattern, dict):
            continue
        degrees = pattern.get("degrees")
        prime = pattern.get("prime")
        if not isinstance(degrees, list):
            continue
        try:
            key = cycle_type_key(int(value) for value in degrees)
        except (TypeError, ValueError):
            continue
        evidence.append(
            {
                "prime": int(prime) if prime is not None else None,
                "degrees": list(parse_cycle_type_key(key)),
                "cycle_type": key,
            }
        )
    return evidence


def _row_r_value(row: dict[str, Any]) -> int | None:
    for source in (
        row,
        row.get("features") if isinstance(row.get("features"), dict) else {},
        row.get("candidate") if isinstance(row.get("candidate"), dict) else {},
    ):
        value = source.get("r", source.get("real_root_count"))
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _row_discriminant(row: dict[str, Any]) -> int | None:
    for key in ("discriminant", "field_disc_abs", "fieldDiscAbs"):
        value = row.get(key)
        try:
            if value is not None and value != "":
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _row_polynomial_discriminant(row: dict[str, Any]) -> tuple[int | None, str | None]:
    for key in ("polynomial_discriminant_abs", "polynomial_disc_abs", "polynomial_discriminant", "discriminant"):
        value = row.get(key)
        try:
            if value is not None and value != "":
                return int(value), key
        except (TypeError, ValueError):
            continue
    return None, None


def _progress_by_pair(progress_rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    progress: dict[str, dict[str, Any]] = {}
    for row in progress_rows:
        label = str(row.get("label") or "")
        if not label:
            continue
        allowed = set()
        for value in row.get("allowedR") or []:
            try:
                allowed.add(int(value))
            except (TypeError, ValueError):
                continue
        discovered = set()
        for value in row.get("discoveredSignatures") or []:
            try:
                discovered.add(int(value))
            except (TypeError, ValueError):
                continue
        remaining = set()
        for value in row.get("remainingSignatures") or []:
            try:
                remaining.add(int(value))
            except (TypeError, ValueError):
                continue
        for sig in row.get("signatures") or []:
            if not isinstance(sig, dict) or sig.get("r") is None:
                continue
            try:
                r_value = int(sig["r"])
            except (TypeError, ValueError):
                continue
            allowed.add(r_value)
            if bool(sig.get("discovered")):
                discovered.add(r_value)
            elif r_value not in discovered:
                remaining.add(r_value)
            progress[f"{label}|r={r_value}"] = {
                "label": label,
                "r": r_value,
                "allowed": True,
                "discovered": bool(sig.get("discovered")),
                "remaining": r_value in remaining and r_value not in discovered,
                "team_count": int(sig.get("teamCount") or 0),
                "minimum_disc_abs": sig.get("minimumDiscAbs") or row.get("minimumDiscAbs"),
                "in_baseline": bool(sig.get("inBaseline", False)),
            }
        for r_value in allowed:
            pair_key = f"{label}|r={r_value}"
            if pair_key not in progress:
                progress[pair_key] = {
                    "label": label,
                    "r": r_value,
                    "allowed": True,
                    "discovered": r_value in discovered,
                    "remaining": r_value in remaining and r_value not in discovered,
                    "team_count": int(row.get("teamCount") or 0) if r_value in discovered else 0,
                    "minimum_disc_abs": row.get("minimumDiscAbs"),
                    "in_baseline": False,
                }
    return progress


def _labels_with_progress(progress_rows: Iterable[dict[str, Any]]) -> dict[str, set[int]]:
    labels: dict[str, set[int]] = {}
    for row in progress_rows:
        label = str(row.get("label") or "")
        if not label:
            continue
        allowed: set[int] = set()
        for key in ("allowedR", "remainingSignatures", "discoveredSignatures"):
            for value in row.get(key) or []:
                try:
                    allowed.add(int(value))
                except (TypeError, ValueError):
                    continue
        for sig in row.get("signatures") or []:
            if isinstance(sig, dict) and sig.get("r") is not None:
                try:
                    allowed.add(int(sig["r"]))
                except (TypeError, ValueError):
                    continue
        labels[label] = allowed
    return labels


def _pair_progress_state(
    pair_key: str,
    *,
    progress: dict[str, dict[str, Any]],
    progress_labels: dict[str, set[int]],
) -> dict[str, Any]:
    if "|r=" not in pair_key:
        return {"pair_key": pair_key, "progress_state": "invalid_pair_key", "score_value_status": "no_score_value"}
    label, r_text = pair_key.split("|r=", 1)
    try:
        r_value = int(r_text)
    except ValueError:
        return {"pair_key": pair_key, "label": label, "progress_state": "invalid_pair_key", "score_value_status": "no_score_value"}
    if label not in progress_labels:
        return {
            "pair_key": pair_key,
            "label": label,
            "r": r_value,
            "progress_state": "progress_data_missing_unknown",
            "score_value_status": "unknown_no_score_value",
        }
    if r_value not in progress_labels[label]:
        return {
            "pair_key": pair_key,
            "label": label,
            "r": r_value,
            "progress_state": "signature_not_allowed",
            "score_value_status": "no_score_value",
        }
    item = progress.get(pair_key)
    if item is None:
        return {
            "pair_key": pair_key,
            "label": label,
            "r": r_value,
            "progress_state": "progress_data_missing_unknown",
            "score_value_status": "unknown_no_score_value",
        }
    team_count = int(item.get("team_count") or 0)
    if item.get("remaining") and not item.get("discovered"):
        state = "allowed_remaining"
        value_status = "valuable_uncovered"
    elif item.get("discovered"):
        state = "allowed_discovered"
        value_status = "valuable_low_team" if team_count <= 20 else "crowded_or_low_value"
    else:
        state = "progress_data_missing_unknown"
        value_status = "unknown_no_score_value"
    return {
        "pair_key": pair_key,
        "label": label,
        "r": r_value,
        "progress_state": state,
        "score_value_status": value_status,
        "team_count": team_count,
        "minimum_disc_abs": item.get("minimum_disc_abs"),
        "in_baseline": bool(item.get("in_baseline", False)),
    }


def candidate_compatibility(
    row: dict[str, Any],
    index: GroupCycleIndex,
    *,
    progress_rows: Iterable[dict[str, Any]] | None = None,
    low_team_threshold: int = 3,
    crowded_team_threshold: int = 20,
) -> dict[str, Any]:
    evidence = observed_cycle_evidence(row)
    all_labels = index.all_labels()
    scope = index.scope_metadata()
    deprecated_fields = {
        "compatible_label_fields_deprecated": True,
        "compatible_label_count_deprecated": True,
        "compatible_label_count_scope": "indexed_subset_only_not_global",
    }
    if not all_labels:
        return {
            "status": "index_empty",
            **scope,
            "indexed_target_survivor_count": 0,
            "indexed_target_labels_not_ruled_out": [],
            "compatible_label_count": 0,
            "compatible_labels": [],
            **deprecated_fields,
            "valuable_targets_not_ruled_out": [],
            "compatible_uncovered_pairs": [],
            "compatible_low_team_pairs": [],
            "compatible_crowded_pairs": [],
            "progress_states": {},
            "evidence": {"primes": [], "cycle_types": []},
            "evidence_strength": "insufficient_index",
        }
    if not evidence:
        return {
            "status": "insufficient_cycle_evidence",
            **scope,
            "indexed_target_survivor_count": len(all_labels),
            "indexed_target_labels_not_ruled_out": sorted(all_labels),
            "compatible_label_count": len(all_labels),
            "compatible_labels": sorted(all_labels),
            **deprecated_fields,
            "valuable_targets_not_ruled_out": [],
            "compatible_uncovered_pairs": [],
            "compatible_low_team_pairs": [],
            "compatible_crowded_pairs": [],
            "progress_states": {},
            "evidence": {"primes": [], "cycle_types": []},
            "evidence_strength": "insufficient_modular_cycle_evidence",
            "warning": "no modular cycle evidence; indexed targets have not been tested and this row is not packet-eligible",
        }

    compatible = set(all_labels)
    missing_cycle_types: list[str] = []
    for item in evidence:
        labels = index.labels_for_cycle_type(str(item["cycle_type"]))
        if not labels:
            missing_cycle_types.append(str(item["cycle_type"]))
        compatible &= labels

    polynomial_discriminant, polynomial_discriminant_source = _row_polynomial_discriminant(row)
    discriminant_square = is_square_integer(polynomial_discriminant)
    parity_filter_applied = False
    parity_filter_status = "polynomial_discriminant_missing"
    if discriminant_square is True and compatible:
        records = index.records_for_labels(compatible)
        even_labels = {label for label, record in records.items() if record.parity in {None, "even"}}
        if even_labels != compatible:
            compatible = even_labels
            parity_filter_applied = True
        parity_filter_status = "applied_polynomial_discriminant_square"
    elif discriminant_square is False:
        parity_filter_status = "not_square_polynomial_discriminant"

    r_value = _row_r_value(row)
    progress = _progress_by_pair(progress_rows or [])
    progress_labels = _labels_with_progress(progress_rows or [])
    compatible_pairs = [f"{label}|r={r_value}" for label in sorted(compatible) if r_value is not None]
    compatible_uncovered = []
    compatible_low_team = []
    compatible_crowded = []
    progress_states: dict[str, dict[str, Any]] = {}
    for pair in compatible_pairs:
        state = _pair_progress_state(pair, progress=progress, progress_labels=progress_labels)
        progress_states[pair] = state
        team_count = int(state.get("team_count") or 0)
        if state.get("progress_state") == "allowed_remaining":
            compatible_uncovered.append(pair)
        elif state.get("progress_state") == "allowed_discovered" and team_count <= low_team_threshold:
            compatible_low_team.append(pair)
        elif state.get("progress_state") == "allowed_discovered" and team_count >= crowded_team_threshold:
            compatible_crowded.append(pair)

    survivors = sorted(compatible)
    valuable_targets = sorted(set(compatible_uncovered + compatible_low_team))
    return {
        "status": "ok" if compatible else "empty_compatible_set",
        **scope,
        "indexed_target_survivor_count": len(compatible),
        "indexed_target_labels_not_ruled_out": survivors,
        "compatible_label_count": len(compatible),
        "compatible_labels": survivors,
        **deprecated_fields,
        "valuable_targets_not_ruled_out": valuable_targets,
        "compatible_uncovered_pairs": sorted(compatible_uncovered),
        "compatible_low_team_pairs": sorted(compatible_low_team),
        "compatible_crowded_pairs": sorted(compatible_crowded),
        "compatible_unknown_or_no_score_pairs": sorted(
            pair for pair in compatible_pairs if pair not in set(compatible_uncovered + compatible_low_team + compatible_crowded)
        ),
        "progress_states": progress_states,
        "crowded_only": bool(compatible) and not compatible_uncovered and not compatible_low_team,
        "ambiguity": {
            "indexed_target_survivor_count": len(compatible),
            "global_ambiguity_status": "unknown_partial_index" if not scope["global_index_complete"] else "complete_index_count",
            "narrowed_below_1000": len(compatible) < 1000,
            "narrowed_below_100": len(compatible) < 100,
            "narrowed_below_20": len(compatible) < 20,
            "narrowed_below_5": len(compatible) < 5,
        },
        "evidence": {
            "primes": [item["prime"] for item in evidence],
            "cycle_types": [item["cycle_type"] for item in evidence],
            "missing_cycle_types": missing_cycle_types,
            "discriminant_square": discriminant_square,
            "polynomial_discriminant_source": polynomial_discriminant_source,
            "parity_filter_applied": parity_filter_applied,
            "parity_filter_status": parity_filter_status,
        },
        "evidence_strength": "modular_cycle_target_exclusion",
        "warning": "indexed survivors are necessary target-exclusion evidence only; unindexed labels remain possible unless the index is complete",
    }


def validate_historical_containment(
    rows: Sequence[dict[str, Any]],
    index: GroupCycleIndex,
    *,
    progress_rows: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    checked: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    sizes: list[int] = []
    crowded_only_count = 0
    true_label_outside_index = 0
    for row in rows:
        label = str(row.get("label") or row.get("verified_group_label") or "")
        if not label:
            feedback = row.get("sair_feedback") if isinstance(row.get("sair_feedback"), dict) else {}
            label = str(feedback.get("label") or "")
        if not label:
            continue
        compatibility = candidate_compatibility(row, index, progress_rows=progress_rows)
        labels = set(compatibility.get("indexed_target_labels_not_ruled_out") or compatibility.get("compatible_labels") or [])
        indexed_labels = index.all_labels()
        label_indexed = label in indexed_labels
        contained = label in labels if label_indexed else None
        if not label_indexed:
            true_label_outside_index += 1
        size = int(compatibility.get("indexed_target_survivor_count") or compatibility.get("compatible_label_count") or 0)
        sizes.append(size)
        crowded_only_count += int(bool(compatibility.get("crowded_only")))
        item = {
            "label": label,
            "r": _row_r_value(row),
            "canonical_hash": row.get("canonical_hash"),
            "contained": contained,
            "true_label_indexed": label_indexed,
            "indexed_target_survivor_count": size,
            "compatible_label_count": size,
            "status": compatibility.get("status"),
            "unindexed_label_mass_unknown": compatibility.get("unindexed_label_mass_unknown"),
        }
        checked.append(item)
        if label_indexed and not contained:
            failures.append(item | {"indexed_target_labels_not_ruled_out": compatibility.get("indexed_target_labels_not_ruled_out", [])[:50]})

    sorted_sizes = sorted(sizes)
    median = sorted_sizes[len(sorted_sizes) // 2] if sorted_sizes else None
    indexed_checked_count = len(checked) - true_label_outside_index
    return {
        "checked_count": len(checked),
        "indexed_true_label_checked_count": indexed_checked_count,
        "true_label_outside_index_count": true_label_outside_index,
        "failure_count": len(failures),
        "true_label_containment": 1.0 - (len(failures) / indexed_checked_count) if indexed_checked_count else None,
        "failures": failures,
        "median_indexed_target_survivor_count": median,
        "median_compatible_label_count": median,
        "fraction_below_1000": sum(1 for value in sizes if value < 1000) / len(sizes) if sizes else None,
        "fraction_below_100": sum(1 for value in sizes if value < 100) / len(sizes) if sizes else None,
        "fraction_below_20": sum(1 for value in sizes if value < 20) / len(sizes) if sizes else None,
        "fraction_below_5": sum(1 for value in sizes if value < 5) / len(sizes) if sizes else None,
        "crowded_only_rejection_rate": crowded_only_count / len(checked) if checked else None,
        "checked_rows": checked,
    }


def summarize_compatibility(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    sizes = [
        int(
            row.get("group_compatibility", {}).get("indexed_target_survivor_count")
            or row.get("group_compatibility", {}).get("compatible_label_count")
            or 0
        )
        for row in rows
    ]
    statuses = Counter(str(row.get("group_compatibility", {}).get("status")) for row in rows)
    return {
        "row_count": len(rows),
        "status_counts": dict(sorted(statuses.items())),
        "median_indexed_target_survivor_count": sorted(sizes)[len(sizes) // 2] if sizes else None,
        "median_compatible_label_count": sorted(sizes)[len(sizes) // 2] if sizes else None,
        "fraction_below_1000": sum(1 for value in sizes if value < 1000) / len(sizes) if sizes else None,
        "fraction_below_100": sum(1 for value in sizes if value < 100) / len(sizes) if sizes else None,
        "fraction_below_20": sum(1 for value in sizes if value < 20) / len(sizes) if sizes else None,
        "fraction_below_5": sum(1 for value in sizes if value < 5) / len(sizes) if sizes else None,
        "crowded_only_count": sum(1 for row in rows if row.get("group_compatibility", {}).get("crowded_only")),
        "partial_index_rows": sum(
            1 for row in rows if row.get("group_compatibility", {}).get("unindexed_label_mass_unknown") is True
        ),
    }
