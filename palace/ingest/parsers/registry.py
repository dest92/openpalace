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
        Tree-sitter parsers must have their grammars installed to work.
        """
        from palace.ingest.parsers.python import PythonParser

        # Register Python parser (always available - uses stdlib ast)
        self.register(PythonParser(), language="python")

        # Register tree-sitter based parsers
        # These will only work if their grammars are installed
        try:
            from palace.ingest.parsers.javascript import JavaScriptParser
            js_parser = JavaScriptParser()
            if js_parser.is_available():
                self.register(js_parser, language="javascript")
        except Exception:
            pass  # JavaScript parser not available

        try:
            from palace.ingest.parsers.typescript import TypeScriptParser
            ts_parser = TypeScriptParser()
            if ts_parser.is_available():
                self.register(ts_parser, language="typescript")
        except Exception:
            pass  # TypeScript parser not available

        try:
            from palace.ingest.parsers.go import GoParser
            go_parser = GoParser()
            if go_parser.is_available():
                self.register(go_parser, language="go")
        except Exception:
            pass  # Go parser not available

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
