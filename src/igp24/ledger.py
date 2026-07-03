"""Persistent JSONL candidate ledger for IGP24 stage 0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


ALLOWED_VERIFICATION_STATUSES = {
    "unverified",
    "proxy_scored",
    "pari_verified",
    "magma_verified",
    "sair_verified",
    "rejected",
}


class CandidateLedger:
    """Append-only JSONL ledger with canonical-hash deduplication."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._records_by_hash: dict[str, dict] = {}
        self.reload()

    def reload(self) -> None:
        self._records_by_hash = {}
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                canonical_hash = record.get("canonical_hash")
                if canonical_hash:
                    self._records_by_hash.setdefault(canonical_hash, record)

    @property
    def hashes(self) -> set[str]:
        return set(self._records_by_hash)

    def records(self) -> list[dict]:
        return list(self._records_by_hash.values())

    def __len__(self) -> int:
        return len(self._records_by_hash)

    def append(self, record: dict) -> bool:
        canonical_hash = record.get("canonical_hash")
        if not canonical_hash:
            raise ValueError("ledger records require canonical_hash")
        status = record.get("verification_status", "unverified")
        if status not in ALLOWED_VERIFICATION_STATUSES:
            raise ValueError(f"invalid verification_status:{status}")
        if canonical_hash in self._records_by_hash:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        self._records_by_hash[canonical_hash] = record
        return True

    def append_many(self, records: Iterable[dict]) -> int:
        added = 0
        for record in records:
            if self.append(record):
                added += 1
        return added
