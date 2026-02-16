"""Base invariant checker interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from palace.ingest.parsers.base import Dependency, Symbol
from palace.ingest.invariants import InvariantViolation


@dataclass
class CheckerConfig:
    """Configuration for an invariant checker."""
    enabled: bool = True
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    threshold: Optional[float] = None
    patterns: Optional[List[str]] = None


class BaseInvariantChecker(ABC):
    """
    Abstract base class for invariant checkers.

    Each checker detects specific types of violations:
    - Security issues (secrets, SQL injection, eval usage)
    - Code quality (long functions, missing type hints)
    - Architecture (circular imports, god objects)
    """

    def __init__(self, config: Optional[CheckerConfig] = None):
        """
        Initialize checker.

        Args:
            config: Checker configuration
        """
        self.config = config or CheckerConfig()
        self.rule_name = self.__class__.__name__.replace("Checker", "").lower()

    @abstractmethod
    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List[InvariantViolation]:
        """
        Check file for invariant violations.

        Args:
            file_path: Path to the file
            content: File content
            dependencies: Extracted dependencies
            symbols: Extracted symbols

        Returns:
            List of violations detected
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this checker is enabled."""
        return self.config.enabled

    def get_severity(self) -> str:
        """Get the severity level for this checker."""
        return self.config.severity

    def create_violation(
        self,
        file_path: Path,
        lineno: int,
        message: str
    ) -> InvariantViolation:
        """
        Create an InvariantViolation with this checker's rule name and severity.

        Args:
            file_path: Path to the file
            lineno: Line number of violation
            message: Violation message

        Returns:
            InvariantViolation object
        """
        return InvariantViolation(
            rule=self.rule_name,
            severity=self.get_severity(),
            file_path=str(file_path),
            lineno=lineno,
            message=message
        )

    def supports_language(self, language: str) -> bool:
        """
        Check if this checker supports the given language.

        Default implementation supports all languages.
        Override for language-specific checkers.

        Args:
            language: Programming language

        Returns:
            True if checker supports this language
        """
        return True
