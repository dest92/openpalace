"""JavaScript language parser using tree-sitter."""

from pathlib import Path
from typing import List
from palace.ingest.parsers.tree_sitter_parser import TreeSitterParser
from palace.ingest.parsers.base import Dependency, Symbol


class JavaScriptParser(TreeSitterParser):
    """Parser for JavaScript source code (including JSX)."""

    def __init__(self):
        """Initialize JavaScript parser."""
        super().__init__("javascript")
        self._initialize_javascript_grammar()

    def _initialize_javascript_grammar(self) -> None:
        """Initialize tree-sitter JavaScript grammar."""
        try:
            import tree_sitter_javascript
            self._language = tree_sitter_javascript.language()
            # Create parser with language
            self._create_parser()
        except ImportError:
            # tree-sitter-javascript not installed
            self._language = None
        except Exception:
            self._language = None

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".js", ".jsx", ".mjs", ".cjs"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract ES6 imports and CommonJS requires."""
        deps = []
        tree = self._parse_tree(content)

        if not tree:
            return deps

        # Find import statements (ES6)
        import_nodes = self._find_nodes_by_type(tree, "import_statement")
        for node in import_nodes:
            self._extract_import_from_node(node, content, deps)

        # Find require calls (CommonJS)
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
        """Extract dependency from ES6 import statement."""
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
        """Extract dependency from CommonJS require call."""
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
        """Extract functions, classes, constants, and variables."""
        symbols = []
        tree = self._parse_tree(content)

        if not tree:
            return symbols

        # Extract function declarations
        func_nodes = self._find_nodes_by_type(tree, "function_declaration")
        for node in func_nodes:
            self._extract_function_from_node(node, content, symbols)

        # Extract class declarations
        class_nodes = self._find_nodes_by_type(tree, "class_declaration")
        for node in class_nodes:
            self._extract_class_from_node(node, content, symbols)

        # Extract variable declarations (constants and exports)
        var_nodes = self._find_nodes_by_type(tree, "variable_declaration")
        for node in var_nodes:
            self._extract_variable_from_node(node, content, symbols)

        # Extract export statements
        export_nodes = self._find_nodes_by_type(tree, "export_statement")
        for node in export_nodes:
            self._extract_export_from_node(node, content, symbols)

        return symbols

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
                if child.type == "identifier":
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
            # Extract exported function/class names
            for child in node.children:
                if child.type == "function_declaration":
                    self._extract_function_from_node(child, content, symbols)
                elif child.type == "class_declaration":
                    self._extract_class_from_node(child, content, symbols)
                elif child.type == "lexical_declaration":
                    self._extract_variable_from_node(child, content, symbols)
        except Exception:
            pass
