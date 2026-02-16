"""Code quality invariant checkers."""

import re
from typing import List
from pathlib import Path
from palace.ingest.parsers.base import Dependency, Symbol
from palace.ingest.invariants.base import BaseInvariantChecker, CheckerConfig


class LongFunctionChecker(BaseInvariantChecker):
    """
    Detect functions that are too long (hard to understand/maintain).

    Threshold: Functions longer than 50 lines (configurable).
    """

    def __init__(self, config: CheckerConfig = None):
        # Ensure threshold has a default value
        if config is None:
            config = CheckerConfig(severity="MEDIUM", threshold=50)
        elif config.threshold is None:
            config.threshold = 50
        super().__init__(config)

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        # Track function boundaries
        function_starts = {}

        for lineno, line in enumerate(content.split('\n'), 1):
            # Detect function definitions (Python, JavaScript, Go)
            func_patterns = [
                r'^\s*(def|func)\s+\w+',
                r'^\s*(function\s+\w+|\w+\s*\(.*\)\s*[{=>])',
                r'^\s*\w+\s*\([^)]*\)\s*[:{]\s*$',
            ]

            for pattern in func_patterns:
                if re.match(pattern, line):
                    # Extract function name
                    match = re.search(r'(def|func|function)\s+(\w+)', line)
                    if match:
                        func_name = match.group(2)
                    else:
                        func_name = f"function_at_{lineno}"

                    function_starts[func_name] = lineno
                    break

            # Check for function end and calculate length
            # Simplified: look for dedent or closing brace
            stripped = line.strip()
            if (stripped.endswith(':') or stripped.endswith('{') or
                stripped.startswith('def ') or stripped.startswith('func ')):

                # Check if any function has exceeded threshold
                for func_name, start_lineno in list(function_starts.items()):
                    func_length = lineno - start_lineno

                    if func_length > self.config.threshold:
                        violations.append(self.create_violation(
                            file_path, start_lineno,
                            f"Function '{func_name}' is {func_length} lines long "
                            f"(threshold: {self.config.threshold})"
                        ))
                        # Remove from dict to avoid duplicate reports
                        del function_starts[func_name]

        return violations


class MissingTypeHintsChecker(BaseInvariantChecker):
    """
    Detect missing type hints in Python and TypeScript.

    Functions should have type annotations for parameters and return values.
    """

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="LOW"))

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        # Only check Python and TypeScript files
        if file_path.suffix not in ['.py', '.pyx', '.ts', '.tsx']:
            return violations

        for symbol in symbols:
            if symbol.type == "function":
                # Check if function signature has type hints
                # This is simplified - real implementation would parse the signature
                if file_path.suffix in ['.py', '.pyx']:
                    # Python: def foo(x: int) -> int:
                    # For now, skip as we'd need to parse the function signature
                    pass
                elif file_path.suffix in ['.ts', '.tsx']:
                    # TypeScript: function foo(x: number): number
                    pass

        return violations


class GodObjectChecker(BaseInvariantChecker):
    """
    Detect god objects (classes with too many methods/responsibilities).

    Threshold: Classes with more than 10 methods (configurable).
    """

    def __init__(self, config: CheckerConfig = None):
        # Ensure threshold has a default value
        if config is None:
            config = CheckerConfig(severity="MEDIUM", threshold=10)
        elif config.threshold is None:
            config.threshold = 10
        super().__init__(config)

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        # Group methods by class
        class_methods = {}

        for symbol in symbols:
            if symbol.type == "class":
                class_methods[symbol.name] = []
            elif symbol.type == "method":
                # Method names are typically "ClassName.method_name"
                parts = symbol.name.split('.')
                if len(parts) > 1:
                    class_name = parts[0]
                    if class_name not in class_methods:
                        class_methods[class_name] = []
                    class_methods[class_name].append(symbol)

        # Check for god objects
        for class_name, methods in class_methods.items():
            method_count = len(methods)

            if method_count > self.config.threshold:
                # Find the class symbol to get line number
                class_symbol = next((s for s in symbols if s.name == class_name and s.type == "class"), None)

                lineno = class_symbol.lineno if class_symbol else 1

                violations.append(self.create_violation(
                    file_path, lineno,
                    f"Class '{class_name}' has {method_count} methods "
                    f"(threshold: {self.config.threshold}). Consider refactoring."
                ))

        return violations


class MissingErrorHandlingChecker(BaseInvariantChecker):
    """
    Detect missing error handling for risky operations.

    Risky operations:
    - File I/O operations
    - Network calls
    - Database operations
    - JSON parsing
    """

    RISKY_PATTERNS = [
        r'\.open\s*\(',
        r'\.read\s*\(',
        r'\.write\s*\(',
        r'\.get\s*\(',
        r'\.post\s*\(',
        r'\.execute\s*\(',
        r'json\.loads\s*\(',
        r'json\.load\s*\(',
    ]

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="MEDIUM"))

        if self.config.patterns:
            self.patterns = [re.compile(p) for p in self.config.patterns]
        else:
            self.patterns = [re.compile(p) for p in self.RISKY_PATTERNS]

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        lines = content.split('\n')
        in_try_block = False
        try_depth = 0

        for lineno, line in enumerate(lines, 1):
            # Track try/except blocks (Python, JavaScript, Go)
            stripped = line.strip()

            if stripped.startswith('try') or stripped.startswith('try{'):
                in_try_block = True
                try_depth += 1
            elif stripped.startswith('except') or stripped.startswith('catch') or stripped.startswith('}'):
                # End of try block
                if try_depth > 0:
                    try_depth -= 1
                    if try_depth == 0:
                        in_try_block = False

            # Check for risky operations
            for pattern in self.patterns:
                if pattern.search(line) and not in_try_block:
                    # Skip if it's in a comment
                    if stripped.startswith('#') or stripped.startswith('//'):
                        continue

                    violations.append(self.create_violation(
                        file_path, lineno,
                        f"Risky operation without error handling"
                    ))
                    break

        return violations
