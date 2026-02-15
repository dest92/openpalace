"""TypeScript language parser using regex (fallback when tree-sitter unavailable).

This is a basic parser that uses regex patterns to extract:
- ES6 imports
- Interfaces
- Type aliases
- Classes
- Functions
- Constants

Note: This is a simplified parser. For production use, tree-sitter is preferred.
"""

import re
from pathlib import Path
from typing import List
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol
import hashlib


class TypeScriptRegexParser(BaseParser):
    """TypeScript parser using regex patterns (fallback)."""

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".ts", ".tsx"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract imports using regex."""
        deps = []
        lines = content.split('\n')

        # ES6 imports (same as JavaScript)
        import_patterns = [
            r'^\s*import\s+\{[^}]+\}\s+from\s+["\']([^"\']+)["\']',
            r'^\s*import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+\w+|\w+))*\s+from\s+["\']([^"\']+)["\']',
            r'^\s*import\s+["\']([^"\']+)["\']',
            # Type-only imports
            r'^\s*import\s+type\s+\{[^}]+\}\s+from\s+["\']([^"\']+)["\']',
        ]

        for lineno, line in enumerate(lines, 1):
            for pattern in import_patterns:
                match = re.search(pattern, line)
                if match:
                    deps.append(Dependency(
                        path=match.group(1),
                        type="IMPORT",
                        lineno=lineno
                    ))
                    break

        return deps

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract symbols using regex."""
        symbols = []
        lines = content.split('\n')

        # Interface declarations: interface Name { ... }
        interface_pattern = r'^\s*(?:export\s+)?interface\s+(\w+)'

        # Type aliases: type Name = ...
        type_pattern = r'^\s*(?:export\s+)?type\s+(\w+)\s*='

        # Class declarations: class Name { ... }
        class_pattern = r'^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)'

        # Function declarations: function name() {}
        func_pattern = r'^\s*(?:export\s+)?(?:export\s+default\s+)?(?:async\s+)?function\s+(\w+)\s*\('

        # Const declarations: const NAME: type = ...
        const_pattern = r'^\s*(?:export\s+)?const\s+(\w+)\s*:'

        # Arrow functions: const name = ... =>
        # Simplified pattern - just look for const name = ... =>
        arrow_func_pattern = r'^\s*(?:export\s+)?const\s+(\w+)\s*=.*?=>'

        for lineno, line in enumerate(lines, 1):
            # Skip comments
            if re.match(r'^\s*//', line):
                continue

            # Try interface
            match = re.search(interface_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="interface",
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try type alias
            match = re.search(type_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="type_alias",
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try class
            match = re.search(class_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="class",
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try arrow function FIRST (before regular function)
            match = re.search(arrow_func_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="function",
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try function declaration
            match = re.search(func_pattern, line)
            if match:
                symbols.append(Symbol(
                    name=match.group(1),
                    type="function",
                    lineno=lineno,
                    docstring=""
                ))
                continue

            # Try const (constants only, uppercase)
            match = re.search(const_pattern, line)
            if match:
                name = match.group(1)
                # Only add if it's all uppercase (likely a constant)
                if name.isupper() or name.startswith('_'):
                    symbols.append(Symbol(
                        name=name,
                        type="constant",
                        lineno=lineno,
                        docstring=""
                    ))

        return symbols

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
