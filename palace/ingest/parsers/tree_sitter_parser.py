"""Base parser class for tree-sitter based language parsers."""

from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol


class TreeSitterParser(BaseParser):
    """
    Base class for tree-sitter based parsers.

    Provides common tree-sitter operations for language-specific parsers.
    Subclasses must implement language-specific extraction logic.
    """

    def __init__(self, language_name: str):
        """
        Initialize tree-sitter parser.

        Args:
            language_name: Name of the language (e.g., "javascript", "typescript")
        """
        self.language_name = language_name
        self._parser = None
        self._language = None
        self._initialize_tree_sitter()

    def _initialize_tree_sitter(self) -> None:
        """
        Initialize tree-sitter parser and language objects.

        Subclasses must override this to set self._language.
        """
        # Don't initialize yet - wait for subclass to set _language
        pass

    def _create_parser(self) -> None:
        """
        Create the tree-sitter parser with the language.

        Must be called after self._language is set.
        """
        if not self._language:
            return

        try:
            import tree_sitter
            # IMPORTANT: Pass language to constructor, not set_language()
            # The language object is a PyCapsule that must be passed to Parser()
            self._parser = tree_sitter.Parser(self._language)
        except ImportError:
            # tree-sitter not available
            self._parser = None
        except Exception:
            self._parser = None

    def _parse_tree(self, content: str) -> Optional[Any]:
        """
        Parse content into tree-sitter tree.

        Args:
            content: Source code content

        Returns:
            Tree-sitter tree object or None if parsing fails
        """
        if not self._parser:
            return None

        try:
            tree = self._parser.parse(bytes(content, "utf8"))
            return tree
        except Exception:
            return None

    def _find_nodes_by_type(self, tree: Any, node_type: str) -> List[Any]:
        """
        Find all nodes of a given type in the tree.

        Args:
            tree: Tree-sitter tree object
            node_type: Type of node to find (e.g., "function_declaration")

        Returns:
            List of tree-sitter nodes matching the type
        """
        if not tree or not tree.root_node:
            return []

        nodes = []
        self._traverse_tree(tree.root_node, node_type, nodes)
        return nodes

    def _traverse_tree(self, node: Any, target_type: str, results: List[Any]) -> None:
        """
        Recursively traverse tree to find nodes of target type.

        Args:
            node: Current tree-sitter node
            target_type: Type of node to find
            results: Accumulator list for matching nodes
        """
        if node.type == target_type:
            results.append(node)

        for child in node.children:
            self._traverse_tree(child, target_type, results)

    def _get_node_text(self, node: Any, content: str) -> str:
        """
        Extract text content from a tree-sitter node.

        Args:
            node: Tree-sitter node
            content: Full source code content

        Returns:
            Text content of the node
        """
        if not node or not hasattr(node, 'byte_range'):
            return ""

        try:
            start_byte, end_byte = node.byte_range
            return content[start_byte:end_byte]
        except Exception:
            return ""

    def _serialize_node(self, node: Any, content: str, indent: int = 0) -> str:
        """
        Serialize a tree-sitter node for fingerprinting.

        Args:
            node: Tree-sitter node to serialize
            content: Full source code content
            indent: Current indentation level

        Returns:
            String representation of node structure
        """
        if not node:
            return ""

        prefix = "  " * indent
        node_text = self._get_node_text(node, content)

        # Truncate very long nodes for fingerprinting
        if len(node_text) > 100:
            node_text = node_text[:100] + "..."

        result = f"{prefix}{node.type}: {repr(node_text)}\n"

        # Recursively serialize children
        for child in node.children:
            result += self._serialize_node(child, content, indent + 1)

        return result

    def _print_tree(self, node: Any, content: str, max_depth: int = 3, current_depth: int = 0) -> None:
        """
        Print tree structure for debugging.

        Args:
            node: Tree-sitter node to print
            content: Full source code content
            max_depth: Maximum depth to print
            current_depth: Current depth
        """
        if not node or current_depth >= max_depth:
            return

        prefix = "  " * current_depth
        node_text = self._get_node_text(node, content)
        if len(node_text) > 50:
            node_text = node_text[:50] + "..."

        print(f"{prefix}{node.type}: {repr(node_text)}")

        for child in node.children:
            self._print_tree(child, content, max_depth, current_depth + 1)

    def compute_fingerprint(self, content: str) -> str:
        """
        Compute hash of AST structure for change detection.

        Args:
            content: Source code content

        Returns:
            Fingerprint string (hash of serialized tree)
        """
        tree = self._parse_tree(content)

        if not tree:
            # Fallback to content hash if parsing fails
            return hashlib.sha256(content.encode()).hexdigest()

        # Serialize tree structure
        structure = self._serialize_node(tree.root_node, content)

        # Hash the structure
        return hashlib.sha256(structure.encode()).hexdigest()

    def _get_node_line_number(self, node: Any) -> int:
        """
        Get line number for a tree-sitter node.

        Args:
            node: Tree-sitter node

        Returns:
            Line number (1-indexed)
        """
        if not node or not hasattr(node, 'start_point'):
            return 1

        return node.start_point[0] + 1  # start_point is 0-indexed

    def _extract_node_children_by_type(
        self,
        node: Any,
        child_types: List[str]
    ) -> Dict[str, List[Any]]:
        """
        Extract immediate children of node by type.

        Args:
            node: Parent tree-sitter node
            child_types: List of child type names to extract

        Returns:
            Dict mapping type names to lists of child nodes
        """
        if not node or not node.children:
            return {t: [] for t in child_types}

        result = {t: [] for t in child_types}

        for child in node.children:
            if child.type in child_types:
                result[child.type].append(child)

        return result

    def is_available(self) -> bool:
        """
        Check if tree-sitter and language grammar are available.

        Returns:
            True if parser is functional
        """
        return self._parser is not None

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """
        Extract import/require statements.

        Base implementation returns empty list.
        Subclasses must override.

        Args:
            file_path: Path to the file
            content: Source code content

        Returns:
            List of Dependency objects
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement parse_dependencies()"
        )

    def extract_symbols(self, content: str) -> List[Symbol]:
        """
        Extract functions, classes, constants.

        Base implementation returns empty list.
        Subclasses must override.

        Args:
            content: Source code content

        Returns:
            List of Symbol objects
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement extract_symbols()"
        )
