"""Architecture invariant checkers."""

from typing import List, Dict, Set
from pathlib import Path
from collections import defaultdict
from palace.ingest.parsers.base import Dependency, Symbol
from palace.ingest.invariants.base import BaseInvariantChecker, CheckerConfig


class CircularImportChecker(BaseInvariantChecker):
    """
    Detect circular import dependencies between files.

    This requires cross-file analysis and needs to be run after
    all files have been ingested. Uses a global dependency graph.
    """

    def __init__(self, config: CheckerConfig = None):
        super().__init__(config or CheckerConfig(severity="HIGH"))

        # Build dependency graph: {file: set of files it imports}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._initialized = False

    def initialize_graph(self, all_files_data: List[tuple]) -> None:
        """
        Initialize the dependency graph from all files.

        Args:
            all_files_data: List of (file_path, dependencies) tuples
        """
        self.dependency_graph.clear()

        for file_path, dependencies in all_files_data:
            file_key = str(file_path)

            for dep in dependencies:
                # Add to graph
                self.dependency_graph[file_key].add(dep.path)

        self._initialized = True

    def check(
        self,
        file_path: Path,
        content: str,
        dependencies: List[Dependency],
        symbols: List[Symbol]
    ) -> List:
        """
        Check for circular imports.

        Note: This is a simplified check that only looks at direct
        circular dependencies (A imports B, B imports A). For full
        cycle detection, run detect_cycles() after processing all files.

        Returns:
            List of violations
        """
        violations = []
        current_file = str(file_path)

        # Check if any of our dependencies import us back
        for dep in dependencies:
            dep_file = dep.path

            # Check if this dependency imports the current file
            if dep_file in self.dependency_graph:
                if current_file in self.dependency_graph[dep_file]:
                    violations.append(self.create_violation(
                        file_path, dep.lineno,
                        f"Circular import detected: {current_file} <-> {dep_file}"
                    ))

        return violations

    def detect_cycles(self) -> List[tuple]:
        """
        Detect all circular import cycles in the dependency graph.

        Uses DFS to find cycles.

        Returns:
            List of cycles (each cycle is a list of file paths)
        """
        if not self._initialized:
            return []

        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(tuple(cycle))
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self.dependency_graph:
            if node not in visited:
                dfs(node)

        return cycles
