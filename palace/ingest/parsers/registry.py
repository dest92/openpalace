"""Parser registry for dynamic parser discovery and registration."""

from pathlib import Path
from typing import List, Optional, Dict, Type, Set
from palace.ingest.parsers.base import BaseParser


class ParserRegistry:
    """
    Singleton registry for language parsers.

    Provides dynamic parser discovery and registration.
    Auto-registers built-in parsers on import.
    """

    _instance: Optional['ParserRegistry'] = None

    def __init__(self):
        """Initialize registry (use instance() instead)."""
        if ParserRegistry._instance is not None:
            raise RuntimeError("Use ParserRegistry.instance() to get the singleton")

        self._parsers: List[BaseParser] = []
        self._extension_map: Dict[str, BaseParser] = {}
        self._language_map: Dict[str, str] = {}  # extension -> language name
        self._register_builtin_parsers()

    @classmethod
    def instance(cls) -> 'ParserRegistry':
        """
        Get the singleton ParserRegistry instance.

        Returns:
            ParserRegistry instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_builtin_parsers(self) -> None:
        """
        Register built-in parsers.

        Automatically registers all available language parsers.
        Tries tree-sitter parsers first, falls back to regex parsers.
        """
        from palace.ingest.parsers.python import PythonParser

        # Register Python parser (always available - uses stdlib ast)
        self.register(PythonParser(), language="python")

        # Register JavaScript parser (try tree-sitter, fallback to regex)
        js_parser_working = False
        try:
            from palace.ingest.parsers.javascript import JavaScriptParser
            js_parser = JavaScriptParser()
            # Test if parser actually works by parsing simple code
            # Use code that SHOULD extract symbols
            test_code = "function test() { return 1; }"
            test_result = js_parser.extract_symbols(test_code)
            # Only use tree-sitter if it actually extracts symbols
            if len(test_result) > 0:
                self.register(js_parser, language="javascript")
                js_parser_working = True
        except Exception:
            pass

        # Fallback to regex parser if tree-sitter not available/working
        if not js_parser_working:
            try:
                from palace.ingest.parsers.javascript_regex import JavaScriptRegexParser
                self.register(JavaScriptRegexParser(), language="javascript")
            except Exception:
                pass

        # Register TypeScript parser (try tree-sitter, fallback to regex)
        ts_parser_working = False
        try:
            from palace.ingest.parsers.typescript import TypeScriptParser
            ts_parser = TypeScriptParser()
            # Test if parser actually works
            test_code = "interface Test { x: number; }"
            test_result = ts_parser.extract_symbols(test_code)
            # Only use tree-sitter if it actually extracts symbols
            if len(test_result) > 0:
                self.register(ts_parser, language="typescript")
                ts_parser_working = True
        except Exception:
            pass

        # Fallback to regex parser if tree-sitter not available/working
        if not ts_parser_working:
            try:
                from palace.ingest.parsers.typescript_regex import TypeScriptRegexParser
                self.register(TypeScriptRegexParser(), language="typescript")
            except Exception:
                pass

        # Register Go parser (try tree-sitter, fallback to regex)
        go_parser_working = False
        try:
            from palace.ingest.parsers.go import GoParser
            go_parser = GoParser()
            # Test if parser actually works
            test_code = "package main\n\nfunc main() {}"
            test_result = go_parser.extract_symbols(test_code)
            # Only use tree-sitter if it actually extracts symbols
            if len(test_result) > 0:
                self.register(go_parser, language="go")
                go_parser_working = True
        except Exception:
            pass

        # Fallback to regex parser if tree-sitter not available/working
        if not go_parser_working:
            try:
                from palace.ingest.parsers.go_regex import GoRegexParser
                self.register(GoRegexParser(), language="go")
            except Exception:
                pass

    def register(self, parser: BaseParser, language: Optional[str] = None) -> None:
        """
        Register a parser.

        Args:
            parser: Parser instance to register
            language: Optional language name (defaults to parser class name)
        """
        if parser in self._parsers:
            return  # Already registered

        self._parsers.append(parser)

        # Map file extensions to this parser
        for ext in parser.supported_extensions():
            # Normalize extension (ensure leading dot)
            normalized_ext = ext if ext.startswith('.') else f'.{ext}'
            self._extension_map[normalized_ext] = parser

            # Map extension to language name
            if language:
                self._language_map[normalized_ext] = language
            else:
                # Derive language name from parser class name
                parser_name = parser.__class__.__name__
                if parser_name.endswith('Parser'):
                    lang = parser_name[:-6].lower()
                else:
                    lang = parser_name.lower()
                self._language_map[normalized_ext] = lang

    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """
        Get appropriate parser for a file.

        Args:
            file_path: Path to the file

        Returns:
            Parser instance or None if no parser available
        """
        ext = file_path.suffix

        # Normalize extension
        if not ext.startswith('.'):
            ext = f'.{ext}'

        return self._extension_map.get(ext)

    def detect_language(self, file_path: Path) -> str:
        """
        Detect language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name (e.g., "python", "javascript") or "unknown"
        """
        ext = file_path.suffix

        # Normalize extension
        if not ext.startswith('.'):
            ext = f'.{ext}'

        return self._language_map.get(ext, "unknown")

    def get_supported_extensions(self) -> Set[str]:
        """
        Get all supported file extensions.

        Returns:
            Set of file extensions (with leading dots)
        """
        return set(self._extension_map.keys())

    def get_supported_languages(self) -> Set[str]:
        """
        Get all supported languages.

        Returns:
            Set of language names
        """
        return set(self._language_map.values())

    def get_parsers(self) -> List[BaseParser]:
        """
        Get all registered parsers.

        Returns:
            List of parser instances
        """
        return self._parsers.copy()

    def has_parser(self, file_path: Path) -> bool:
        """
        Check if a parser exists for the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if a parser is available
        """
        return self.get_parser(file_path) is not None

    def is_parser_available(self, parser_class: Type[BaseParser]) -> bool:
        """
        Check if a specific parser class is registered and available.

        Args:
            parser_class: Parser class to check

        Returns:
            True if parser is registered and available
        """
        for parser in self._parsers:
            if isinstance(parser, parser_class):
                # Check if tree-sitter parser is available
                if hasattr(parser, 'is_available'):
                    return parser.is_available()
                return True
        return False


# Convenience function for getting the registry instance
def get_registry() -> ParserRegistry:
    """
    Get the singleton ParserRegistry instance.

    Returns:
        ParserRegistry instance
    """
    return ParserRegistry.instance()
