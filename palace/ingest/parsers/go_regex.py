"""Go language parser using regex (fallback when tree-sitter unavailable).

This is a basic parser that uses regex patterns to extract:
- Import declarations
- Package declarations
- Functions
- Methods
- Structs
- Interfaces
- Constants

Note: This is a simplified parser. For production use, tree-sitter is preferred.
"""

import re
from pathlib import Path
from typing import List
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol
import hashlib


class GoRegexParser(BaseParser):
    """Go parser using regex patterns (fallback)."""

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".go"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract imports using regex."""
        deps = []
        lines = content.split('\n')
        in_import_block = False

        for lineno, line in enumerate(lines, 1):
            # Start of import block
            if re.match(r'^\s*import\s*\(', line):
                in_import_block = True
                continue

            # End of import block
            if in_import_block and re.match(r'^\s*\)', line):
                in_import_block = False
                continue

            # Import statement
            import_pattern = r'^\s*import\s+["\']([^"\']+)["\']'
            match = re.search(import_pattern, line)
            if match:
                deps.append(Dependency(
                    path=match.group(1),
                    type="IMPORT",
                    lineno=lineno
                ))
                continue

            # Import block
            if in_import_block:
                match = re.search(r'^\s*["\']([^"\']+)["\']', line)
                if match:
                    deps.append(Dependency(
                        path=match.group(1),
                        type="IMPORT",
                        lineno=lineno
                    ))

        return deps

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract symbols using regex."""
        symbols = []
        lines = content.split('\n')

        # Package declaration: package name
        package_pattern = r'^\s*package\s+(\w+)'

        # Function declarations: func name(...) ...
        func_pattern = r'^\s*func\s+(?:(?:\([^)]*\)\s+)?)?(\w+)\s*\('

        # Type declarations: type Name struct/interface
        type_pattern = r'^\s*type\s+(\w+)\s+(struct|interface)'

        # Const declarations: const NAME ...
        const_pattern = r'^\s*const\s+\(([\s\S]*?\))|^\s*const\s+(\w+)\s*[=:]'

        for lineno, line in enumerate(lines, 1):
            # Skip comments
            if re.match(r'^\s*//', line):
                continue

            # Try package
            match = re.search(package_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="package",
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try function/method
            match = re.search(func_pattern, line)
            if match:
                func_name = match.group(1)
                # Check if it's a method (has receiver)
                receiver_match = re.search(r'^func\s*\(([^)]+)\)', line)
                if receiver_match:
                    # It's a method
                    symbols.append(Symbol(
                        name=f"{receiver_match.group(1)}.{func_name}",
                        type="method",
                        lineno=lineno,
                        docstring=""
                    ))
                else:
                    # It's a function
                    symbols.append(Symbol(
                        name=func_name,
                        type="function",
                        lineno=lineno,
                        docstring=""
                    ))
                continue

            # Try type (struct/interface)
            match = re.search(type_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type=match.group(2),  # "struct" or "interface"
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try const (simple case)
            match = re.match(r'^\s*const\s+(\w+)\s*[=:\n]', line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="constant",
                    lineno=lineno,
                    docstring=""
                ))

        return symbols

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
