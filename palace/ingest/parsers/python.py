"""Python language parser using tree-sitter."""

from pathlib import Path
from typing import List
import hashlib
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class PythonParser(BaseParser):
    """Parser for Python source code."""

    def __init__(self):
        """Initialize parser with tree-sitter."""
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter-python not installed")

        # New tree-sitter API requires library_path and name
        self.language = Language(tspython.language_path(), "python")
        self.parser = Parser(self.language)

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".py", ".pyx"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract import statements."""
        tree = self.parser.parse(bytes(content, "utf-8"))
        deps = []

        def find_imports(node):
            if node.type == "import_statement":
                # Handle: import os
                for child in node.children:
                    if child.type == "dotted_name" or child.type == "name":
                        deps.append(Dependency(
                            path=child.text.decode(),
                            type="IMPORT",
                            lineno=node.start_point[0] + 1
                        ))
                        break
            elif node.type == "import_from_statement":
                # Handle: from typing import List
                module_node = node.child_by_field_name("module_name")
                if module_node:
                    deps.append(Dependency(
                        path=module_node.text.decode(),
                        type="IMPORT",
                        lineno=node.start_point[0] + 1
                    ))

            for child in node.children:
                find_imports(child)

        find_imports(tree.root_node)
        return deps

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract functions, classes, constants."""
        tree = self.parser.parse(bytes(content, "utf-8"))
        symbols = []

        def find_symbols(node):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                symbols.append(Symbol(
                    name=name_node.text.decode() if name_node else "",
                    type="function",
                    lineno=node.start_point[0] + 1,
                    docstring=self._extract_docstring(node)
                ))
            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                symbols.append(Symbol(
                    name=name_node.text.decode() if name_node else "",
                    type="class",
                    lineno=node.start_point[0] + 1,
                    docstring=self._extract_docstring(node)
                ))

            for child in node.children:
                find_symbols(child)

        find_symbols(tree.root_node)
        return symbols

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of AST structure."""
        tree = self.parser.parse(bytes(content, "utf-8"))

        # Serialize structure
        structure = self._serialize_node(tree.root_node)
        return hashlib.sha256(structure.encode()).hexdigest()

    def _extract_docstring(self, node) -> str:
        """Extract docstring from function/class node."""
        # Find first string expression child
        for child in node.children:
            if child.type == "string":
                return child.text.decode().strip('"\'')
        return ""

    def _serialize_node(self, node, indent=0) -> str:
        """Serialize tree structure to string."""
        result = "  " * indent + node.type + "\n"
        for child in node.children:
            result += self._serialize_node(child, indent + 1)
        return result
