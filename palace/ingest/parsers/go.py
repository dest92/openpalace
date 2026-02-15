"""Go language parser using tree-sitter."""

from pathlib import Path
from typing import List
from palace.ingest.parsers.tree_sitter_parser import TreeSitterParser
from palace.ingest.parsers.base import Dependency, Symbol


class GoParser(TreeSitterParser):
    """Parser for Go source code."""

    def __init__(self):
        """Initialize Go parser."""
        super().__init__("go")
        self._initialize_go_grammar()

    def _initialize_go_grammar(self) -> None:
        """Initialize tree-sitter Go grammar."""
        try:
            import tree_sitter_go
            self._language = tree_sitter_go.language()
            # Create parser with language
            self._create_parser()
        except ImportError:
            # tree-sitter-go not installed
            self._language = None
        except Exception:
            self._language = None

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".go"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract import declarations."""
        deps = []
        tree = self._parse_tree(content)

        if not tree:
            return deps

        # Find import declarations
        import_nodes = self._find_nodes_by_type(tree, "import_declaration")
        for node in import_nodes:
            self._extract_import_from_node(node, content, deps)

        return deps

    def _extract_import_from_node(
        self,
        node: any,
        content: str,
        deps: List[Dependency]
    ) -> None:
        """Extract dependency from import declaration."""
        try:
            for child in node.children:
                if child.type == "import_spec":
                    for subchild in child.children:
                        if subchild.type == "interpreted_string_literal":
                            import_path = self._get_node_text(subchild, content).strip('"')
                            lineno = self._get_node_line_number(node)
                            deps.append(Dependency(
                                path=import_path,
                                type="IMPORT",
                                lineno=lineno
                            ))
                            break
        except Exception:
            pass

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract packages, functions, methods, interfaces, structs, and constants."""
        symbols = []
        tree = self._parse_tree(content)

        if not tree:
            return symbols

        # Extract package declaration
        package_nodes = self._find_nodes_by_type(tree, "package_clause")
        for node in package_nodes:
            self._extract_package_from_node(node, content, symbols)

        # Extract function declarations
        func_nodes = self._find_nodes_by_type(tree, "function_declaration")
        for node in func_nodes:
            self._extract_function_from_node(node, content, symbols)

        # Extract method declarations
        method_nodes = self._find_nodes_by_type(tree, "method_declaration")
        for node in method_nodes:
            self._extract_method_from_node(node, content, symbols)

        # Extract interface declarations
        interface_nodes = self._find_nodes_by_type(tree, "interface_type")
        for node in interface_nodes:
            self._extract_interface_from_node(node, content, symbols)

        # Extract struct declarations
        struct_nodes = self._find_nodes_by_type(tree, "type_declaration")
        for node in struct_nodes:
            self._extract_struct_from_node(node, content, symbols)

        # Extract const declarations
        const_nodes = self._find_nodes_by_type(tree, "const_declaration")
        for node in const_nodes:
            self._extract_const_from_node(node, content, symbols)

        return symbols

    def _extract_package_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from package declaration."""
        try:
            for child in node.children:
                if child.type == "package_identifier":
                    name = self._get_node_text(child, content)
                    lineno = self._get_node_line_number(node)
                    symbols.append(Symbol(
                        name=name,
                        type="package",
                        lineno=lineno,
                        docstring=""
                    ))
                    break
        except Exception:
            pass

    def _extract_function_from_node(
        self,
        node: any,
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

    def _extract_method_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from method declaration."""
        try:
            name = None
            receiver = ""
            docstring = ""

            # Get receiver and method name
            for child in node.children:
                if child.type == "parameter_list":
                    # This is the receiver
                    receiver = self._get_node_text(child, content)
                elif child.type == "identifier":
                    name = self._get_node_text(child, content)

            if not name:
                return

            # Combine receiver and name for method symbol
            full_name = f"{receiver}.{name}" if receiver else name
            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=full_name,
                type="method",
                lineno=lineno,
                docstring=docstring
            ))
        except Exception:
            pass

    def _extract_interface_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from interface type."""
        try:
            # Interfaces in Go are type declarations
            # We need to find the parent type_declaration to get the name
            # This is a simplified extraction
            pass
        except Exception:
            pass

    def _extract_struct_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from type declaration (struct, interface, etc.)."""
        try:
            # Get the type spec
            for child in node.children:
                if child.type == "type_spec":
                    name = None
                    type_name = None

                    for subchild in child.children:
                        if subchild.type == "type_identifier":
                            name = self._get_node_text(subchild, content)
                        elif subchild.type == "struct_type":
                            type_name = "struct"
                        elif subchild.type == "interface_type":
                            type_name = "interface"

                    if name and type_name:
                        lineno = self._get_node_line_number(node)
                        symbols.append(Symbol(
                            name=name,
                            type=type_name,
                            lineno=lineno,
                            docstring=""
                        ))
                    break
        except Exception:
            pass

    def _extract_const_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from const declaration."""
        try:
            # Get const spec list
            for child in node.children:
                if child.type == "const_spec":
                    for subchild in child.children:
                        if subchild.type == "identifier":
                            name = self._get_node_text(subchild, content)
                            lineno = self._get_node_line_number(node)
                            symbols.append(Symbol(
                                name=name,
                                type="constant",
                                lineno=lineno,
                                docstring=""
                            ))
                            break
        except Exception:
            pass
