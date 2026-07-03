"""Dry-run SAIR API wrapper stub.

This module never auto-submits. API keys are read only from the environment and
are never included in messages or serialized records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence

from src.igp24.verifiers.base import BaseVerifier, VerificationResult


class SAIRAPIVerifier(BaseVerifier):
    status_name = "sair_verified"

    def __init__(self, api_key_env: str = "SAIR_API_KEY", dry_run: bool = True):
        self.api_key_env = api_key_env
        self.dry_run = dry_run

    def _api_key_present(self) -> bool:
        return bool(os.environ.get(self.api_key_env))

    def is_available(self) -> bool:
        return self._api_key_present()

    def verify(self, coefficients: Sequence[int]) -> VerificationResult:
        _ = coefficients
        return VerificationResult(status="unverified", message="SAIR API verification is not implemented in stage 0")

    def submit(self, records: Iterable[dict], submit: bool = False) -> VerificationResult:
        count = sum(1 for _ in records)
        if not submit or self.dry_run:
            return VerificationResult(status="unverified", message=f"dry-run only; would prepare {count} records")
        raise NotImplementedError("SAIR submission is intentionally disabled in stage 0")

    def export_batch_without_submission(self, records: Iterable[dict], path: str | Path) -> Path:
        return self.export_batch(records, path)
