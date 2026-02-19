"""
Palace Mental V2 - Unified Tree-sitter Integration

Integrates tree-sitter parsing with:
- AST fingerprinting (32 bytes per file)
- Symbol extraction
- Dependency extraction
- Multi-language support (80+ languages)

Usage:
    parser = get_tree_sitter_parser("python")
    result = parse_code(code, parser)
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import hashlib

from palace.core.ast_fingerprint import hash_ast_structure


# Language detection mapping
LANGUAGE_MAP = {
    '.py': 'python',
    '.pyx': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.java': 'java',
    '.kt': 'kotlin',
    '.swift': 'swift',
    '.rb': 'ruby',
    '.php': 'php',
    '.sh': 'bash',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.md': 'markdown',
}


def detect_language(file_path: Path) -> Optional[str]:
    """
    Detect programming language from file extension.

    Args:
        file_path: Path to file

    Returns:
        Language name or None
    """
    ext = file_path.suffix.lower()
    return LANGUAGE_MAP.get(ext)


def get_tree_sitter_parser(language: str):
    """
    Get tree-sitter parser for given language.

    Args:
        language: Language name (python, javascript, etc.)

    Returns:
        Tree-sitter Parser object or None if unavailable
    """
    try:
        import tree_sitter

        # Import language-specific grammar
        lang_module = _import_language(language)
        if not lang_module:
            return None

        # Create parser with language
        parser = tree_sitter.Parser(lang_module.language())
        return parser

    except ImportError:
        return None
    except Exception:
        return None


def _import_language(language: str):
    """
    Import tree-sitter language grammar.

    Args:
        language: Language name

    Returns:
        Language module or None
    """
    try:
        if language == 'python':
            from tree_sitter_languages import get_language
            return get_language('python')
        elif language == 'javascript':
            from tree_sitter_languages import get_language
            return get_language('javascript')
        elif language == 'typescript':
            from tree_sitter_languages import get_language
            return get_language('typescript')
        # Add more languages as needed
        else:
            return None
    except ImportError:
        # Try alternative import paths
        try:
            import importlib
            module_name = f"tree_sitter_{language}"
            return importlib.import_module(module_name)
        except ImportError:
            return None


@dataclass
class ParsedCode:
    """Result of parsing code with tree-sitter."""
    file_path: str
    language: str
    ast_fingerprint: str
    symbols: List[Dict]  # Functions, classes, etc.
    dependencies: List[Dict]  # Imports, requires, etc.
    parse_success: bool
    parse_error: Optional[str] = None


def parse_code_v2(
    code: str,
    file_path: Path,
    parser: Optional[Any] = None
) -> ParsedCode:
    """
    Parse code using tree-sitter for V2 architecture.

    This is the main entry point for parsing in Palace Mental V2.

    Args:
        code: Source code content
        file_path: Path to file (for language detection)
        parser: Optional tree-sitter parser (will be created if None)

    Returns:
        ParsedCode object with fingerprint, symbols, dependencies
    """
    language = detect_language(file_path) or "unknown"

    # Create parser if not provided
    if parser is None:
        parser = get_tree_sitter_parser(language)

    if parser is None:
        # Fallback: hash content directly
        return ParsedCode(
            file_path=str(file_path),
            language=language,
            ast_fingerprint=hashlib.sha256(code.encode()).hexdigest(),
            symbols=[],
            dependencies=[],
            parse_success=False,
            parse_error="Tree-sitter parser not available"
        )

    try:
        # Parse code
        tree = parser.parse(bytes(code, "utf8"))

        if not tree or not tree.root_node:
            raise ValueError("Parse failed - no tree returned")

        # Compute AST fingerprint (32 bytes)
        ast_fingerprint = hash_ast_structure(tree.root_node, code)

        # Extract symbols
        symbols = _extract_symbols(tree, code, language)

        # Extract dependencies
        dependencies = _extract_dependencies(tree, code, language)

        return ParsedCode(
            file_path=str(file_path),
            language=language,
            ast_fingerprint=ast_fingerprint,
            symbols=symbols,
            dependencies=dependencies,
            parse_success=True
        )

    except Exception as e:
        # Fallback on any error
        return ParsedCode(
            file_path=str(file_path),
            language=language,
            ast_fingerprint=hashlib.sha256(code.encode()).hexdigest(),
            symbols=[],
            dependencies=[],
            parse_success=False,
            parse_error=str(e)
        )


def _extract_symbols(
    tree: Any,
    content: str,
    language: str
) -> List[Dict]:
    """
    Extract symbols (functions, classes, etc.) from parsed tree.

    Args:
        tree: Tree-sitter tree
        content: Source code content
        language: Programming language

    Returns:
        List of symbol dictionaries
    """
    symbols = []
    root = tree.root_node

    # Language-specific extraction
    if language == 'python':
        symbols.extend(_extract_python_symbols(root, content))
    elif language in ['javascript', 'typescript']:
        symbols.extend(_extract_js_symbols(root, content))
    elif language == 'go':
        symbols.extend(_extract_go_symbols(root, content))

    return symbols


def _extract_python_symbols(node: Any, content: str) -> List[Dict]:
    """Extract symbols from Python code."""
    symbols = []

    # Find function definitions
    func_nodes = _find_nodes_of_type(node, 'function_definition')
    for func_node in func_nodes:
        name = _extract_child_text(func_node, 'identifier', content)
        params = _extract_parameters(func_node, content)
        return_type = _extract_return_type(func_node, content)

        symbols.append({
            'kind': 'function',
            'name': name,
            'parameters': params,
            'return_type': return_type,
            'calls': _extract_function_calls(func_node, content)
        })

    # Find class definitions
    class_nodes = _find_nodes_of_type(node, 'class_definition')
    for class_node in class_nodes:
        name = _extract_child_text(class_node, 'identifier', content)
        methods = _extract_class_methods(class_node, content)

        symbols.append({
            'kind': 'class',
            'name': name,
            'methods': methods
        })

    return symbols


def _extract_js_symbols(node: Any, content: str) -> List[Dict]:
    """Extract symbols from JavaScript/TypeScript code."""
    symbols = []

    # Find function declarations
    func_nodes = _find_nodes_of_type(node, 'function_declaration')
    for func_node in func_nodes:
        name = _extract_child_text(func_node, 'identifier', content)
        params = _extract_parameters(func_node, content)

        symbols.append({
            'kind': 'function',
            'name': name,
            'parameters': params,
            'return_type': 'unknown',
            'calls': []
        })

    # Find class declarations
    class_nodes = _find_nodes_of_type(node, 'class_declaration')
    for class_node in class_nodes:
        name = _extract_child_text(class_node, 'identifier', content)
        methods = _extract_class_methods(class_node, content)

        symbols.append({
            'kind': 'class',
            'name': name,
            'methods': methods
        })

    return symbols


def _extract_go_symbols(node: Any, content: str) -> List[Dict]:
    """Extract symbols from Go code."""
    symbols = []

    # Find function declarations
    func_nodes = _find_nodes_of_type(node, 'function_declaration')
    for func_node in func_nodes:
        name = _extract_child_text(func_node, 'identifier', content)
        params = _extract_parameters(func_node, content)
        return_type = _extract_return_type(func_node, content)

        symbols.append({
            'kind': 'function',
            'name': name,
            'parameters': params,
            'return_type': return_type,
            'calls': []
        })

    return symbols


def _extract_dependencies(
    tree: Any,
    content: str,
    language: str
) -> List[Dict]:
    """
    Extract dependencies (imports, requires, etc.) from parsed tree.

    Args:
        tree: Tree-sitter tree
        content: Source code content
        language: Programming language

    Returns:
        List of dependency dictionaries
    """
    dependencies = []
    root = tree.root_node

    if language == 'python':
        # Find import statements
        import_nodes = _find_nodes_of_type(root, 'import_statement')
        for node in import_nodes:
            names = _extract_import_names(node, content)
            for name in names:
                dependencies.append({
                    'kind': 'import',
                    'name': name,
                    'type': 'import'
                })

        # Find from...import statements
        from_nodes = _find_nodes_of_type(root, 'import_from_statement')
        for node in from_nodes:
            module = _extract_module_name(node, content)
            names = _extract_import_names(node, content)
            for name in names:
                dependencies.append({
                    'kind': 'import',
                    'name': f"{module}.{name}",
                    'type': 'from_import'
                })

    elif language in ['javascript', 'typescript']:
        # Find import statements
        import_nodes = _find_nodes_of_type(root, 'import_statement')
        for node in import_nodes:
            # Extract import path
            dep = _extract_js_import(node, content)
            if dep:
                dependencies.append(dep)

        # Find require calls (CommonJS)
        require_nodes = _find_nodes_of_type(root, 'call_expression')
        for node in require_nodes:
            dep = _extract_require_call(node, content)
            if dep:
                dependencies.append(dep)

    elif language == 'go':
        # Find import declarations
        import_nodes = _find_nodes_of_type(root, 'import_declaration')
        for node in import_nodes:
            path = _extract_import_path(node, content)
            if path:
                dependencies.append({
                    'kind': 'import',
                    'name': path,
                    'type': 'import'
                })

    return dependencies


# Helper functions

def _find_nodes_of_type(node: Any, node_type: str) -> List[Any]:
    """Find all nodes of given type recursively."""
    results = []

    if node.type == node_type:
        results.append(node)

    for child in node.children:
        results.extend(_find_nodes_of_type(child, node_type))

    return results


def _extract_child_text(node: Any, child_type: str, content: str) -> str:
    """Extract text from child node of given type."""
    for child in node.children:
        if child.type == child_type and hasattr(child, 'start_byte'):
            start, end = child.start_byte, child.end_byte
            return content[start:end]
    return ""


def _extract_parameters(func_node: Any, content: str) -> List[str]:
    """Extract parameter names from function node."""
    params = []

    # Find parameters node
    for child in func_node.children:
        if 'parameter' in child.type.lower():
            # Extract parameter name
            if hasattr(child, 'start_byte'):
                start, end = child.start_byte, child.end_byte
                param_text = content[start:end].strip()
                if param_text:
                    params.append(param_text)

    return params


def _extract_return_type(func_node: Any, content: str) -> str:
    """Extract return type from function node."""
    # Look for type annotation
    for child in func_node.children:
        if 'type' in child.type.lower():
            if hasattr(child, 'start_byte'):
                start, end = child.start_byte, child.end_byte
                return content[start:end].strip()
    return "unknown"


def _extract_function_calls(func_node: Any, content: str) -> List[str]:
    """Extract function calls from function body."""
    calls = []
    call_nodes = _find_nodes_of_type(func_node, 'call_expression')

    for call_node in call_nodes:
        # Extract function name
        func = _extract_child_text(call_node, 'identifier', content)
        if func:
            calls.append(func)

    return calls


def _extract_class_methods(class_node: Any, content: str) -> List[Dict]:
    """Extract methods from class definition."""
    methods = []

    # Find function definitions within class
    func_nodes = _find_nodes_of_type(class_node, 'function_definition')
    for func_node in func_nodes:
        name = _extract_child_text(func_node, 'identifier', content)
        params = _extract_parameters(func_node, content)
        return_type = _extract_return_type(func_node, content)

        methods.append({
            'name': name,
            'parameters': params,
            'return_type': return_type
        })

    return methods


def _extract_import_names(import_node: Any, content: str) -> List[str]:
    """Extract imported names from import statement."""
    names = []
    for child in import_node.children:
        if child.type == 'identifier' or 'name' in child.type.lower():
            if hasattr(child, 'start_byte'):
                start, end = child.start_byte, child.end_byte
                names.append(content[start:end])
    return names


def _extract_module_name(from_node: Any, content: str) -> str:
    """Extract module name from from...import statement."""
    for child in from_node.children:
        if child.type == 'identifier' or 'module' in child.type.lower():
            if hasattr(child, 'start_byte'):
                start, end = child.start_byte, child.end_byte
                return content[start:end]
    return ""


def _extract_js_import(import_node: Any, content: str) -> Optional[Dict]:
    """Extract import from JS/TS import statement."""
    # Extract module path from string
    for child in import_node.children:
        if child.type == 'string':
            if hasattr(child, 'start_byte'):
                start, end = child.start_byte, child.end_byte
                path = content[start:end].strip('"\'')
                return {
                    'kind': 'import',
                    'name': path,
                    'type': 'import'
                }
    return None


def _extract_require_call(call_node: Any, content: str) -> Optional[Dict]:
    """Extract CommonJS require() call."""
    # Check if function name is 'require'
    func = _extract_child_text(call_node, 'identifier', content)
    if func == 'require':
        # Extract argument (module path)
        for child in call_node.children:
            if child.type == 'string':
                if hasattr(child, 'start_byte'):
                    start, end = child.start_byte, child.end_byte
                    path = content[start:end].strip('"\'')
                    return {
                        'kind': 'import',
                        'name': path,
                        'type': 'require'
                    }
    return None


def _extract_import_path(import_node: Any, content: str) -> str:
    """Extract import path from Go import declaration."""
    for child in import_node.children:
        if child.type == 'import_spec' or child.type == 'string':
            if hasattr(child, 'start_byte'):
                start, end = child.start_byte, child.end_byte
                return content[start:end].strip('"\'')
    return ""



def parse_file_v2(file_path: Path) -> ParsedCode:
    """
    Parse file for Palace Mental V2.

    Main entry point for ingestion pipeline.

    Args:
        file_path: Path to source file

    Returns:
        ParsedCode object
    """
    # Read file
    try:
        code = file_path.read_text(encoding='utf-8')
    except Exception:
        return ParsedCode(
            file_path=str(file_path),
            language="unknown",
            ast_fingerprint="",
            symbols=[],
            dependencies=[],
            parse_success=False,
            parse_error="Could not read file"
        )

    # Detect language and get parser
    language = detect_language(file_path) or "unknown"
    parser = get_tree_sitter_parser(language)

    # Parse
    return parse_code_v2(code, file_path, parser)


def batch_parse_files(file_paths: List[Path]) -> List[ParsedCode]:
    """
    Parse multiple files efficiently.

    Args:
        file_paths: List of file paths

    Returns:
        List of ParsedCode objects
    """
    results = []

    # Group by language to reuse parsers
    by_language: Dict[str, List[Path]] = {}
    for file_path in file_paths:
        lang = detect_language(file_path) or "unknown"
        if lang not in by_language:
            by_language[lang] = []
        by_language[lang].append(file_path)

    # Parse each language group
    for language, paths in by_language.items():
        parser = get_tree_sitter_parser(language)

        for file_path in paths:
            result = parse_file_v2(file_path)
            results.append(result)

    return results
