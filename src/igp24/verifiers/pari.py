"""PARI/GP verifier stub.

Stage 0 does not call PARI from the training loop. This wrapper exists so a
later stage can add exact verification without changing ledger records.
"""

from __future__ import annotations

import shutil
from typing import Sequence

from src.igp24.verifiers.base import BaseVerifier, VerificationResult


class PARIVerifier(BaseVerifier):
    status_name = "pari_verified"

    def __init__(self, executable: str = "gp"):
        self.executable = executable

    def is_available(self) -> bool:
        return shutil.which(self.executable) is not None

    def verify(self, coefficients: Sequence[int]) -> VerificationResult:
        _ = coefficients
        if not self.is_available():
            return VerificationResult(status="unverified", message=f"PARI/GP executable not found: {self.executable}")
        return VerificationResult(status="unverified", message="PARI verification is not implemented in stage 0")
