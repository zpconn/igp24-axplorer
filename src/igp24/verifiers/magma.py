"""MAGMA verifier stub for future exact Galois group checks."""

from __future__ import annotations

import shutil
from typing import Sequence

from src.igp24.verifiers.base import BaseVerifier, VerificationResult


class MagmaVerifier(BaseVerifier):
    status_name = "magma_verified"

    def __init__(self, executable: str = "magma"):
        self.executable = executable

    def is_available(self) -> bool:
        return shutil.which(self.executable) is not None

    def verify(self, coefficients: Sequence[int]) -> VerificationResult:
        _ = coefficients
        if not self.is_available():
            return VerificationResult(status="unverified", message=f"MAGMA executable not found: {self.executable}")
        return VerificationResult(status="unverified", message="MAGMA verification is not implemented in stage 0")
