"""JavaScript language parser using regex (fallback when tree-sitter unavailable).

This is a basic parser that uses regex patterns to extract:
- ES6 imports
- CommonJS requires
- Functions
- Classes
- Constants

Note: This is a simplified parser. For production use, tree-sitter is preferred.
"""

import re
from pathlib import Path
from typing import List
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol
import hashlib


class JavaScriptRegexParser(BaseParser):
    """JavaScript parser using regex patterns (fallback)."""

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".js", ".jsx", ".mjs", ".cjs"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract imports using regex."""
        deps = []
        lines = content.split('\n')

        # ES6 imports: import ... from '...'
        es6_import_pattern = r'^\s*import\s+(?:(?:\{[^}]*}|\*\s+as\s+\w+|\w+)(?:\s*,\s*(?:\{[^}]*}|\*\s+as\s+\w+|\w+))*\s+from\s+)?["\']([^"\']+)["\']'
        # Named imports: import { x, y } from '...'
        es6_import_pattern2 = r'^\s*import\s+\{[^}]+\}\s+from\s+["\']([^"\']+)["\']'

        # CommonJS requires
        cjs_require_pattern = r'require\(["\']([^"\']+)["\']\)'

        for lineno, line in enumerate(lines, 1):
            # Try ES6 imports
            match = re.search(es6_import_pattern, line)
            if match:
                deps.append(Dependency(
                    path=match.group(1),
                    type="IMPORT",
                    lineno=lineno
                ))
                continue

            # Try named imports
            match = re.search(es6_import_pattern2, line)
            if match:
                deps.append(Dependency(
                    path=match.group(1),
                    type="IMPORT",
                    lineno=lineno
                ))
                continue

            # Try CommonJS requires
            for match in re.finditer(cjs_require_pattern, line):
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

        # Function declarations: function name() {}
        func_pattern = r'^\s*function\s+(\w+)\s*\('

        # Class declarations: class Name { ... }
        class_pattern = r'^\s*class\s+(\w+)'

        # Arrow functions with const: const func = () => {}
        # Check this BEFORE regular const
        arrow_func_pattern = r'^\s*const\s+(\w+)\s*=\s*(?:(?:\([^)]*\))|(?:\w+(?:<[^>]+>)?))\s*=>'

        # Const declarations: const NAME = ... (but NOT arrow functions)
        const_pattern = r'^\s*const\s+(\w+)\s*='

        # Export const: export const NAME = ...
        export_const_pattern = r'^\s*export\s+const\s+(\w+)\s*='

        for lineno, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue

            # Try arrow function FIRST (before regular const)
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

            # Try const (only if not arrow function)
            match = re.search(const_pattern, line) or re.search(export_const_pattern, line)
            if match:
                # Determine if it's the const pattern or export_const_pattern
                const_match = re.search(const_pattern, line) or re.search(export_const_pattern, line)
                if const_match:
                    name = const_match.group(1)
                    # Check if it's uppercase (likely a constant)
                    if name.isupper() or name.startswith('_'):
                        symbols.append(Symbol(
                            name=name,
                            type="constant",
                            lineno=lineno,
                            docstring=""
                        ))
                    # Mixed case or lowercase with = might be a non-arrow-function variable
                    # Skip it for now as it's likely not a symbol we want to track
                continue

        return symbols

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
