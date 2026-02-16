"""Invariant detection package."""

from dataclasses import dataclass
from typing import List


@dataclass
class InvariantViolation:
    """A detected invariant violation."""
    rule: str
    severity: str
    file_path: str
    lineno: int
    message: str


# Import detector for backward compatibility
from palace.ingest.invariants.detector import InvariantDetector
from palace.ingest.invariants.registry import InvariantRegistry

# Import and register all checkers
from palace.ingest.invariants.checkers.security import (
    HardcodedSecretsChecker,
    EvalUsageChecker,
    SQLInjectionChecker,
    UnparameterizedSQLChecker
)
from palace.ingest.invariants.checkers.code_quality import (
    LongFunctionChecker,
    MissingTypeHintsChecker,
    GodObjectChecker,
    MissingErrorHandlingChecker
)
from palace.ingest.invariants.checkers.architecture import (
    CircularImportChecker
)

# Register all checkers
InvariantRegistry.register(HardcodedSecretsChecker)
InvariantRegistry.register(EvalUsageChecker)
InvariantRegistry.register(SQLInjectionChecker)
InvariantRegistry.register(UnparameterizedSQLChecker)
InvariantRegistry.register(LongFunctionChecker)
InvariantRegistry.register(MissingTypeHintsChecker)
InvariantRegistry.register(GodObjectChecker)
InvariantRegistry.register(MissingErrorHandlingChecker)
InvariantRegistry.register(CircularImportChecker)

__all__ = [
    'InvariantViolation',
    'InvariantDetector',
    'InvariantRegistry',
]
