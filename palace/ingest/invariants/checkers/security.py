"""Security invariant checkers."""

import re
from typing import List
from pathlib import Path
from palace.ingest.parsers.base import Dependency, Symbol
from palace.ingest.invariants.base import BaseInvariantChecker, CheckerConfig


class HardcodedSecretsChecker(BaseInvariantChecker):
    """
    Detect hardcoded secrets (API keys, passwords, tokens).

    Patterns:
    - password = "..."
    - api_key = "..."
    - secret = "..."
    - token = "..."
    """

    # Common secret variable names
    SECRET_PATTERNS = [
        r'password\s*=\s*["\'][^"\']{8,}["\']',
        r'api_key\s*=\s*["\'][^"\']{20,}["\']',
        r'apikey\s*=\s*["\'][^"\']{20,}["\']',
        r'secret\s*=\s*["\'][^"\']{16,}["\']',
        r'token\s*=\s*["\'][^"\']{20,}["\']',
        r'auth_token\s*=\s*["\'][^"\']{20,}["\']',
        r'access_token\s*=\s*["\'][^"\']{20,}["\']',
        r'private_key\s*=\s*["\'][^"\']{20,}["\']',
        r'secret_key\s*=\s*["\'][^"\']{20,}["\']',
    ]

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="CRITICAL"))

        # Use custom patterns from config if provided
        if self.config.patterns:
            self.patterns = [re.compile(p) for p in self.config.patterns]
        else:
            self.patterns = [re.compile(p) for p in self.SECRET_PATTERNS]

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        for lineno, line in enumerate(content.split('\n'), 1):
            for pattern in self.patterns:
                if pattern.search(line):
                    # Skip if it's an example/test file
                    if 'example' in str(file_path).lower() or 'test' in str(file_path).lower():
                        continue

                    # Skip if line contains "placeholder", "example", "fake"
                    if any(word in line.lower() for word in ['placeholder', 'example', 'fake', 'xxx']):
                        continue

                    violations.append(self.create_violation(
                        file_path, lineno,
                        f"Potential hardcoded secret detected"
                    ))
                    break  # Only report one violation per line

        return violations


class EvalUsageChecker(BaseInvariantChecker):
    """
    Detect use of eval() or exec() which can lead to code injection.

    Dangerous functions:
    - eval()
    - exec()
    - __import__() (os.system)
    """

    DANGEROUS_FUNCTIONS = ['eval', 'exec', '__import__']

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="CRITICAL"))

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        # Only check Python files
        if not file_path.suffix in ['.py', '.pyx']:
            return violations

        for lineno, line in enumerate(content.split('\n'), 1):
            for func in self.DANGEROUS_FUNCTIONS:
                # Look for function calls
                if f'{func}(' in line:
                    # Skip if it's in a comment
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue

                    violations.append(self.create_violation(
                        file_path, lineno,
                        f"Use of dangerous function '{func}()' can lead to code injection"
                    ))
                    break

        return violations


class SQLInjectionChecker(BaseInvariantChecker):
    """
    Detect potential SQL injection vulnerabilities.

    Patterns:
    - String concatenation in SQL queries
    - f-strings with user input in queries
    """

    SQL_PATTERNS = [
        r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP).*?\+.*?(FROM|INTO|SET)',
        r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP).*?f["\'].*?\{.*?\}.*?(FROM|INTO|SET)',
        r'execute\s*\(\s*["\'].*?\+',
    ]

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="CRITICAL"))

        if self.config.patterns:
            self.patterns = [re.compile(p, re.IGNORECASE) for p in self.config.patterns]
        else:
            self.patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_PATTERNS]

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        for lineno, line in enumerate(content.split('\n'), 1):
            for pattern in self.patterns:
                if pattern.search(line):
                    violations.append(self.create_violation(
                        file_path, lineno,
                        f"Potential SQL injection: use parameterized queries instead"
                    ))
                    break

        return violations


class UnparameterizedSQLChecker(BaseInvariantChecker):
    """
    Detect SQL queries without parameterization.

    Checks for:
    - cursor.execute() with string formatting
    - Direct string concatenation in queries
    """

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="HIGH"))

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        violations = []

        # Look for execute() calls
        execute_pattern = re.compile(r'\.execute\s*\(\s*f?["\']')

        for lineno, line in enumerate(content.split('\n'), 1):
            if execute_pattern.search(line):
                # Check if parameters are used (look for %s, ?, or :params)
                if not any(param in line for param in ['%s', '?', ':', '$']):
                    violations.append(self.create_violation(
                        file_path, lineno,
                        f"SQL query without parameters: use parameterized queries to prevent injection"
                    ))

        return violations
