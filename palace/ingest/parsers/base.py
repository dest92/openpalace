"""Base parser interface and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class Dependency:
    """A dependency (import, require, etc.) extracted from code."""
    path: str
    type: str  # IMPORT, FUNCTION_CALL, INHERITANCE, COMPOSITION
    lineno: int


@dataclass
class Symbol:
    """A symbol (function, class, constant) extracted from code."""
    name: str
    type: str  # function, class, constant, method
    lineno: int
    docstring: str = ""


class BaseParser(ABC):
    """Abstract base for language-specific parsers."""

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of file extensions this parser handles."""
        pass

    @abstractmethod
    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """
        Extract import/require statements.

        Returns:
            List of Dependency objects
        """
        pass

    @abstractmethod
    def extract_symbols(self, content: str) -> List[Symbol]:
        """
        Extract functions, classes, constants.

        Returns:
            List of Symbol objects
        """
        pass

    @abstractmethod
    def compute_fingerprint(self, content: str) -> str:
        """
        Compute hash of AST structure for change detection.

        Returns:
            Fingerprint string
        """
        pass
