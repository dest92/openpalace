"""Python language parser using AST/fallback."""

from pathlib import Path
from typing import List
import hashlib
import os
import ast
import re
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol


class PythonParser(BaseParser):
    """Parser for Python source code."""

    def __init__(self):
        """Initialize parser."""
        # Use Python's built-in AST module instead of tree-sitter
        # due to compatibility issues with tree-sitter 0.20+ in Python 3.12
        pass

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".py", ".pyx"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract import statements using AST."""
        deps = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append(Dependency(
                            path=alias.name,
                            type="IMPORT",
                            lineno=node.lineno
                        ))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        deps.append(Dependency(
                            path=f"{module}.{alias.name}" if module else alias.name,
                            type="IMPORT",
                            lineno=node.lineno
                        ))
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            import_pattern = r'^\s*(?:import|from)\s+([^\n]+)'
            for lineno, line in enumerate(content.split('\n'), 1):
                match = re.match(import_pattern, line)
                if match:
                    deps.append(Dependency(
                        path=match.group(1).split(' as ')[0].split(',')[0],
                        type="IMPORT",
                        lineno=lineno
                    ))

        return deps

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract functions, classes, constants using AST."""
        symbols = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node) or ""
                    symbols.append(Symbol(
                        name=node.name,
                        type="function",
                        lineno=node.lineno,
                        docstring=docstring
                    ))
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    symbols.append(Symbol(
                        name=node.name,
                        type="class",
                        lineno=node.lineno,
                        docstring=docstring
                    ))
        except SyntaxError:
            pass  # Return empty list if syntax error

        return symbols

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of AST structure."""
        try:
            tree = ast.parse(content)
            # Serialize AST structure
            structure = ast.dump(tree)
            return hashlib.sha256(structure.encode()).hexdigest()
        except SyntaxError:
            # Fallback to hash of content if AST parsing fails
            return hashlib.sha256(content.encode()).hexdigest()
