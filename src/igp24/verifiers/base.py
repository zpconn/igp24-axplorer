"""Common interfaces for optional IGP24 external verifiers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


class VerifierUnavailable(RuntimeError):
    """Raised when an optional verifier is not installed or configured."""


@dataclass(frozen=True)
class VerificationResult:
    status: str
    verified_group_label: str | None = None
    signature_r: int | None = None
    message: str = ""
    raw_output: str | None = None


class BaseVerifier:
    status_name = "unverified"

    def is_available(self) -> bool:
        return False

    def verify(self, coefficients: Sequence[int]) -> VerificationResult:
        _ = coefficients
        raise VerifierUnavailable(f"{self.__class__.__name__} is unavailable")

    def export_batch(self, records: Iterable[dict], path: str | Path) -> Path:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        return out_path
