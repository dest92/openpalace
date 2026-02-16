"""Invariant detector that orchestrates all checkers."""

from typing import List
from pathlib import Path
from palace.ingest.parsers.base import Dependency, Symbol
from palace.ingest.invariants.base import BaseInvariantChecker
from palace.ingest.invariants.registry import InvariantRegistry
from palace.ingest.invariants import InvariantViolation


class InvariantDetector:
    """
    Orchestrates multiple invariant checkers.

    Runs all registered checkers against files and collects violations.
    """

    def __init__(self, config_path: Path = None):
        """
        Initialize detector.

        Args:
            config_path: Optional path to invariants.toml configuration file
        """
        self.registry = InvariantRegistry()

        # Load configuration if provided
        if config_path:
            self.registry.load_config(config_path)

        # Get all enabled checkers
        self.checkers = self.registry.get_all_checkers()

    def detect_from_file(
        self,
        file_path: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List[InvariantViolation]:
        """
        Detect invariants from a file using all enabled checkers.

        Args:
            file_path: Path to the file
            dependencies: List of dependencies
            symbols: List of symbols

        Returns:
            List of violations from all checkers
        """
        violations = []
        path = Path(file_path)

        try:
            content = path.read_text()
        except Exception:
            # Can't read file, skip checks
            return violations

        # Run each checker
        for checker in self.checkers:
            # Skip checkers that don't support this file's language
            # (if checker implements language filtering)
            violations.extend(
                checker.check(path, content, dependencies, symbols)
            )

        return violations

    def get_violations_by_severity(self, violations: List[InvariantViolation]) -> dict:
        """
        Group violations by severity level.

        Args:
            violations: List of violations

        Returns:
            Dict mapping severity to list of violations
        """
        by_severity = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }

        for violation in violations:
            severity = violation.severity.upper()
            if severity in by_severity:
                by_severity[severity].append(violation)

        return by_severity

    def register_checker(self, checker_class: type) -> None:
        """
        Register a custom checker.

        Args:
            checker_class: Checker class to register
        """
        InvariantRegistry.register(checker_class)
