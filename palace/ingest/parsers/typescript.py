"""TypeScript language parser using tree-sitter."""

from pathlib import Path
from typing import List
from palace.ingest.parsers.tree_sitter_parser import TreeSitterParser
from palace.ingest.parsers.base import Dependency, Symbol


class TypeScriptParser(TreeSitterParser):
    """Parser for TypeScript source code (including TSX)."""

    def __init__(self):
        """Initialize TypeScript parser."""
        super().__init__("typescript")
        self._initialize_typescript_grammar()

    def _initialize_typescript_grammar(self) -> None:
        """Initialize tree-sitter TypeScript grammar."""
        try:
            import tree_sitter_typescript
            self._language = tree_sitter_typescript.language_typescript()
            if self._parser:
                self._parser.set_language(self._language)
        except ImportError:
            # tree-sitter-typescript not installed
            self._language = None
        except Exception:
            self._language = None

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".ts", ".tsx"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract ES6 imports and type-only imports."""
        deps = []
        tree = self._parse_tree(content)

        if not tree:
            return deps

        # Find import statements
        import_nodes = self._find_nodes_by_type(tree, "import_statement")
        for node in import_nodes:
            self._extract_import_from_node(node, content, deps)

        # Find require calls (for interop with CommonJS)
        require_nodes = self._find_nodes_by_type(tree, "call_expression")
        for node in require_nodes:
            self._extract_require_from_node(node, content, deps)

        return deps

    def _extract_import_from_node(
        self,
        node: any,
        content: str,
        deps: List[Dependency]
    ) -> None:
        """Extract dependency from import statement."""
        try:
            for child in node.children:
                if child.type == "string":
                    module_path = self._get_node_text(child, content).strip('"\'')
                    lineno = self._get_node_line_number(node)
                    deps.append(Dependency(
                        path=module_path,
                        type="IMPORT",
                        lineno=lineno
                    ))
                    break
        except Exception:
            pass

    def _extract_require_from_node(
        self,
        node: any,
        content: str,
        deps: List[Dependency]
    ) -> None:
        """Extract dependency from require call."""
        try:
            # Check if this is a require() call
            func_name = None
            for child in node.children:
                if child.type == "identifier":
                    text = self._get_node_text(child, content)
                    if text == "require":
                        func_name = text
                        break

            if not func_name:
                return

            # Extract module path from arguments
            for child in node.children:
                if child.type == "arguments":
                    for arg in child.children:
                        if arg.type == "string":
                            module_path = self._get_node_text(arg, content).strip('"\'')
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
        """Extract interfaces, types, classes, functions, and constants."""
        symbols = []
        tree = self._parse_tree(content)

        if not tree:
            return symbols

        # Extract interface declarations
        interface_nodes = self._find_nodes_by_type(tree, "interface_declaration")
        for node in interface_nodes:
            self._extract_interface_from_node(node, content, symbols)

        # Extract type aliases
        type_alias_nodes = self._find_nodes_by_type(tree, "type_alias_declaration")
        for node in type_alias_nodes:
            self._extract_type_alias_from_node(node, content, symbols)

        # Extract function declarations
        func_nodes = self._find_nodes_by_type(tree, "function_declaration")
        for node in func_nodes:
            self._extract_function_from_node(node, content, symbols)

        # Extract class declarations
        class_nodes = self._find_nodes_by_type(tree, "class_declaration")
        for node in class_nodes:
            self._extract_class_from_node(node, content, symbols)

        # Extract variable declarations
        var_nodes = self._find_nodes_by_type(tree, "variable_declaration")
        for node in var_nodes:
            self._extract_variable_from_node(node, content, symbols)

        # Extract export statements
        export_nodes = self._find_nodes_by_type(tree, "export_statement")
        for node in export_nodes:
            self._extract_export_from_node(node, content, symbols)

        return symbols

    def _extract_interface_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from interface declaration."""
        try:
            name = None
            docstring = ""

            # Get interface name
            for child in node.children:
                if child.type == "type_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return

            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=name,
                type="interface",
                lineno=lineno,
                docstring=docstring
            ))
        except Exception:
            pass

    def _extract_type_alias_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from type alias declaration."""
        try:
            name = None
            docstring = ""

            # Get type alias name
            for child in node.children:
                if child.type == "type_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return

            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=name,
                type="type_alias",
                lineno=lineno,
                docstring=docstring
            ))
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

    def _extract_class_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from class declaration."""
        try:
            name = None
            docstring = ""

            # Get class name
            for child in node.children:
                if child.type == "type_identifier":
                    name = self._get_node_text(child, content)
                    break

            if not name:
                return

            lineno = self._get_node_line_number(node)
            symbols.append(Symbol(
                name=name,
                type="class",
                lineno=lineno,
                docstring=docstring
            ))
        except Exception:
            pass

    def _extract_variable_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from variable declaration."""
        try:
            # Check if this is a const declaration
            is_const = False
            for child in node.children:
                if child.type == "const":
                    is_const = True
                    break

            if not is_const:
                return

            # Extract variable declarators
            for child in node.children:
                if child.type == "variable_declarator":
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

    def _extract_export_from_node(
        self,
        node: any,
        content: str,
        symbols: List[Symbol]
    ) -> None:
        """Extract symbol from export statement."""
        try:
            # Extract exported function/class/interface/types
            for child in node.children:
                if child.type == "function_declaration":
                    self._extract_function_from_node(child, content, symbols)
                elif child.type == "class_declaration":
                    self._extract_class_from_node(child, content, symbols)
                elif child.type == "interface_declaration":
                    self._extract_interface_from_node(child, content, symbols)
                elif child.type == "type_alias_declaration":
                    self._extract_type_alias_from_node(child, content, symbols)
                elif child.type == "lexical_declaration":
                    self._extract_variable_from_node(child, content, symbols)
        except Exception:
            pass
