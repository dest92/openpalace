"""Go language parser using tree-sitter."""

from pathlib import Path
from typing import List
import tree_sitter
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol


class GoParser(BaseParser):
    """Parser for Go source code."""

    def __init__(self):
        """Initialize Go parser."""
        super().__init__()
        self._parser = None
        self._language = None
        self._initialize_go_grammar()

    def _initialize_go_grammar(self) -> None:
        """Initialize tree-sitter Go grammar."""
        try:
            import tree_sitter_go
            
            # IMPORTANT: Wrap the PyCapsule in Language()
            lang_capsule = tree_sitter_go.language()
            self._language = tree_sitter.Language(lang_capsule)
            self._parser = tree_sitter.Parser(self._language)
        except ImportError:
            # tree-sitter-go not installed
            self._language = None
        except Exception:
            self._language = None

    def is_available(self) -> bool:
        """Check if parser is available."""
        return self._parser is not None

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".go"]

    def _parse_tree(self, content: str):
        """Parse content into tree-sitter tree."""
        if not self._parser:
            return None
        
        try:
            return self._parser.parse(bytes(content, "utf8"))
        except Exception:
            return None

    def _find_nodes_by_type(self, tree, node_type: str) -> List:
        """Find all nodes of given type."""
        if not tree:
            return []
        
        nodes = []
        
        def find_recursive(node):
            if node.type == node_type:
                nodes.append(node)
            for child in node.children:
                find_recursive(child)
        
        find_recursive(tree.root_node)
        return nodes

    def _get_node_text(self, node, content: str) -> str:
        """Get text content of a node."""
        return content[node.start_byte:node.end_byte]

    def _get_node_line_number(self, node) -> int:
        """Get line number of a node."""
        return node.start_point[0] + 1

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract import statements."""
        deps = []
        tree = self._parse_tree(content)

        if not tree:
            return deps

        # Find import specifications
        import_nodes = self._find_nodes_by_type(tree, "import_spec")
        for node in import_nodes:
            self._extract_import_from_node(node, content, deps)

        return deps

    def _extract_import_from_node(
        self,
        node,
        content: str,
        deps: List[Dependency]
    ) -> None:
        """Extract dependency from import statement."""
        try:
            # Find the import path string
            for child in node.children:
                if child.type == "import_path":
                    module_path = self._get_node_text(child, content).strip('"')
                    lineno = self._get_node_line_number(node)
                    deps.append(Dependency(
                        path=module_path,
                        type="IMPORT",
                        lineno=lineno
                    ))
                    break
        except Exception:
            pass

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract structs, functions, interfaces, and package."""
        symbols = []
        tree = self._parse_tree(content)

        if not tree:
            return symbols

        # Extract package declaration
        package_nodes = self._find_nodes_by_type(tree, "package_declaration")
        for node in package_nodes:
            self._extract_package_from_node(node, content, symbols)

        # Extract struct declarations
        struct_nodes = self._find_nodes_by_type(tree, "type_declaration")
        for node in struct_nodes:
            self._extract_type_from_node(node, content, symbols, "struct")

        # Extract interface declarations
        interface_nodes = self._find_nodes_by_type(tree, "type_declaration")
        for node in interface_nodes:
            # Check if it's an interface type
            if self._is_interface_type(node):
                self._extract_type_from_node(node, content, symbols, "interface")

        # Extract function declarations
        func_nodes = self._find_nodes_by_type(tree, "function_declaration")
        for node in func_nodes:
            self._extract_function_from_node(node, content, symbols)

        return symbols

    def _is_interface_type(self, node) -> bool:
        """Check if type declaration is for an interface."""
        for child in node.children:
            if child.type == "type_spec":
                for subchild in child.children:
                    if subchild.type == "interface_type":
                        return True
        return False

    def _extract_package_from_node(
        self,
        node,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from package declaration."""
        try:
            name = None
            for child in node.children:
                if child.type == "package_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return

            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=name,
                type="package",
                lineno=lineno,
                docstring=""
            ))
        except Exception:
            pass

    def _extract_type_from_node(
        self,
        node,
        content: str,
        symbols: List[Symbol],
        symbol_type: str
    ) -> None:
        """Extract symbol from type declaration."""
        try:
            name = None
            docstring = ""

            # Get type name
            for child in node.children:
                if child.type == "type_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return

            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=name,
                type=symbol_type,
                lineno=lineno,
                docstring=docstring
            ))
        except Exception:
            pass

    def _extract_function_from_node(
        self,
        node,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from function declaration."""
        try:
            name = None
            docstring = ""

            # Get function name
            for child in node.children:
                if child.type == "identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return

            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=name,
                type="function",
                lineno=lineno,
                docstring=docstring
            ))
        except Exception:
            pass

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of AST structure for change detection."""
        import hashlib
        
        tree = self._parse_tree(content)
        if not tree:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Use AST structure for fingerprint
        structure = []
        self._collect_structure(tree.root_node, structure)
        structure_str = ','.join(structure)
        return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

    def _collect_structure(self, node, structure: List[str]) -> None:
        """Recursively collect node types for fingerprinting."""
        structure.append(node.type)
        for child in node.children:
            self._collect_structure(child, structure)
