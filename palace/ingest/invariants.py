"""Invariant detection for design patterns."""

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


class InvariantDetector:
    """Detects architectural invariants and violations."""

    def detect_from_file(self, file_path: str, dependencies: List, symbols: List) -> List[InvariantViolation]:
        """
        Detect invariants from a file.

        Args:
            file_path: Path to the file
            dependencies: List of dependencies
            symbols: List of symbols

        Returns:
            List of violations
        """
        violations = []

        # Example rule: Cyclical dependencies
        # (Simplified - would need full graph analysis in production)

        # Example rule: God objects (too many responsibilities)
        for symbol in symbols:
            if symbol.type == "class":
                # Count methods
                method_count = sum(1 for s in symbols if s.type == "method" and s.name.startswith(symbol.name))
                if method_count > 10:
                    violations.append(InvariantViolation(
                        rule="god_object",
                        severity="warning",
                        file_path=file_path,
                        lineno=symbol.lineno,
                        message=f"Class {symbol.name} has {method_count} methods, consider refactoring"
                    ))

        return violations
