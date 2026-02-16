"""Import path resolver for creating DEPENDS_ON edges."""

from pathlib import Path
from typing import Optional, Set, Dict
from dataclasses import dataclass
from functools import lru_cache
import re


@dataclass
class ResolutionResult:
    """Result of resolving an import path."""
    artifact_id: Optional[str]
    file_path: Optional[str]
    is_external: bool


class ImportPathResolver:
    """
    Resolves import paths to artifact IDs for creating DEPENDS_ON edges.

    Handles language-specific path resolution and filters external packages.
    """

    # Python standard library modules
    PYTHON_STDLIB = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
        'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex',
        'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk',
        'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections', 'colorsys',
        'compileall', 'concurrent', 'configparser', 'contextlib', 'contextvars',
        'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses',
        'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils',
        'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler', 'fcntl',
        'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
        'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib',
        'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib',
        'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
        'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma',
        'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder',
        'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers',
        'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib', 'pdb', 'pickle',
        'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix',
        'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile',
        'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
        'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
        'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr',
        'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics',
        'string', 'stringprep', 'struct', 'subprocess', 'sunau', 'symbol', 'symtable',
        'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile',
        'termios', 'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
        'token', 'tokenize', 'tomllib', 'trace', 'traceback', 'tracemalloc', 'tty',
        'turtle', 'turtledemo', 'types', 'typing', 'typing_extensions', 'unicodedata',
        'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
        'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
        'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo',
    }

    # Common Node.js package prefixes (external)
    NODE_EXTERNAL_PREFIXES = {
        'react', 'react-dom', 'vue', 'angular', 'lodash', 'axios', 'express',
        'moment', 'date-fns', 'webpack', 'babel', 'eslint', 'prettier', 'jest',
        'vitest', 'typescript', '@types', '@mui', '@ant-design', '@chakra-ui',
    }

    # Go stdlib packages
    GO_STDLIB = {
        'fmt', 'os', 'io', 'bufio', 'bytes', 'strings', 'strconv', 'math',
        'time', 'http', 'net', 'context', 'sync', 'database/sql', 'encoding',
        'json', 'xml', 'log', 'path', 'filepath', 'sort', 'reflect',
    }

    def __init__(self, project_root: Path, hippocampus):
        """
        Initialize resolver.

        Args:
            project_root: Root directory of the project
            hippocampus: Hippocampus database instance for artifact lookups
        """
        self.project_root = Path(project_root)
        self.hippocampus = hippocampus
        self._artifact_cache: Dict[str, str] = {}  # file_path -> artifact_id

    def resolve(
        self,
        import_path: str,
        importing_file: Path,
        language: str
    ) -> ResolutionResult:
        """
        Resolve an import path to an artifact ID.

        Args:
            import_path: The import path from source code
            importing_file: Path of the file containing the import
            language: Programming language (python, javascript, go)

        Returns:
            ResolutionResult with artifact_id, file_path, and is_external flag
        """
        # Normalize import path
        normalized = self._normalize_import_path(import_path, language)

        # Check if external package
        if self._is_external_package(normalized, language):
            return ResolutionResult(None, None, is_external=True)

        # Convert to file system path
        fs_path = self._import_to_fs_path(normalized, importing_file, language)
        if not fs_path:
            return ResolutionResult(None, None, is_external=False)

        # Try to resolve relative to project root
        absolute_path = self._resolve_absolute_path(fs_path, importing_file)
        if not absolute_path or not absolute_path.exists():
            return ResolutionResult(None, str(absolute_path), is_external=False)

        # Look up artifact ID (with cache)
        artifact_id = self._lookup_artifact_id(absolute_path)

        return ResolutionResult(
            artifact_id=artifact_id,
            file_path=str(absolute_path),
            is_external=False
        )

    def _normalize_import_path(self, import_path: str, language: str) -> str:
        """Normalize import path for consistent handling."""
        # Remove quotes if present
        import_path = import_path.strip('"\'').strip()

        if language == 'python':
            # Remove relative dots for Python
            import_path = import_path.lstrip('.')
            # Split on first dot to get top-level module
            parts = import_path.split('.')
            return parts[0] if parts else import_path

        elif language in ('javascript', 'typescript'):
            # Keep relative indicators
            if import_path.startswith('./') or import_path.startswith('../'):
                # Normalize path separators
                return import_path.replace('\\', '/')
            # For bare imports, get the package name
            return import_path.split('/')[0]

        elif language == 'go':
            # Remove package suffix if present
            import_path = import_path.split('/')[-1]
            return import_path

        return import_path

    def _is_external_package(self, import_path: str, language: str) -> bool:
        """Check if import is an external package."""
        if language == 'python':
            # Check if it's a stdlib module
            top_level = import_path.split('.')[0]
            return top_level in self.PYTHON_STDLIB

        elif language in ('javascript', 'typescript'):
            # External if no relative indicators and not starting with @/
            if not (import_path.startswith('./') or
                    import_path.startswith('../') or
                    import_path.startswith('@/')):
                # Check common external packages
                top_level = import_path.split('/')[0]
                return top_level in self.NODE_EXTERNAL_PREFIXES

        elif language == 'go':
            # Check if it's stdlib
            return import_path in self.GO_STDLIB

        return False

    def _import_to_fs_path(
        self,
        import_path: str,
        importing_file: Path,
        language: str
    ) -> Optional[Path]:
        """Convert import path to file system path."""
        if language == 'python':
            # Python: os.path -> os/path.py or os/path/__init__.py
            return self._python_import_to_path(import_path, importing_file)

        elif language in ('javascript', 'typescript'):
            # JavaScript/TypeScript: ./utils -> ./utils.js or ./utils/index.js
            return self._js_import_to_path(import_path, importing_file)

        elif language == 'go':
            # Go: encoding/json -> encoding/json.go
            return self._go_import_to_path(import_path, importing_file)

        return None

    def _python_import_to_path(
        self,
        import_path: str,
        importing_file: Path
    ) -> Optional[Path]:
        """Convert Python import to file system path."""
        # Try as module.py
        module_path = Path(import_path.replace('.', '/'))
        possible_paths = [
            module_path / '__init__.py',
            module_path.with_suffix('.py'),
        ]

        # Try relative to importing file's package
        importing_dir = importing_file.parent
        for path in possible_paths:
            full_path = importing_dir / path
            if full_path.exists():
                return path

        # Try relative to project root
        for path in possible_paths:
            full_path = self.project_root / path
            if full_path.exists():
                return path

        return None

    def _js_import_to_path(
        self,
        import_path: str,
        importing_file: Path
    ) -> Optional[Path]:
        """Convert JavaScript/TypeScript import to file system path."""
        importing_dir = importing_file.parent

        # Relative import
        if import_path.startswith('./') or import_path.startswith('../'):
            # Resolve relative path
            resolved = importing_dir / import_path

            # Try with extensions
            extensions = ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs']
            for ext in extensions:
                if resolved.with_suffix(ext).exists():
                    return resolved.with_suffix(ext)

            # Try index.js
            if (resolved / 'index.js').exists():
                return resolved / 'index.js'
            if (resolved / 'index.ts').exists():
                return resolved / 'index.ts'

            return resolved

        # Absolute import (e.g., @/utils)
        if import_path.startswith('@/'):
            import_path = import_path[2:]  # Remove @/
            resolved = self.project_root / import_path

            extensions = ['.js', '.jsx', '.ts', '.tsx']
            for ext in extensions:
                if resolved.with_suffix(ext).exists():
                    return resolved.with_suffix(ext)

            return resolved

        return None

    def _go_import_to_path(
        self,
        import_path: str,
        importing_file: Path
    ) -> Optional[Path]:
        """Convert Go import to file system path."""
        # Go package -> go file
        go_path = Path(import_path.replace('.', '/')) / f'{import_path}.go'

        # Try relative to importing file
        importing_dir = importing_file.parent
        full_path = importing_dir / go_path
        if full_path.exists():
            return go_path

        # Try relative to project root
        full_path = self.project_root / go_path
        if full_path.exists():
            return go_path

        return None

    def _resolve_absolute_path(
        self,
        fs_path: Path,
        importing_file: Path
    ) -> Optional[Path]:
        """Resolve relative path to absolute path."""
        if fs_path.is_absolute():
            return fs_path

        # Resolve relative to importing file
        resolved = (importing_file.parent / fs_path).resolve()

        # Check if it's within project root
        try:
            resolved.relative_to(self.project_root)
            return resolved
        except ValueError:
            # Path is outside project root
            return None

    def _lookup_artifact_id(self, file_path: Path) -> Optional[str]:
        """
        Look up artifact ID for a file path.

        Uses cache for O(1) lookups after first query.
        """
        # Convert to relative path for consistency
        try:
            rel_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            # File is outside project root
            return None

        # Check in-memory cache first
        if rel_path in self._artifact_cache:
            return self._artifact_cache[rel_path]

        # Try exact match first
        results = self.hippocampus.execute_cypher(
            "MATCH (a:Artifact) WHERE a.path = $path RETURN a.id AS id LIMIT 1",
            {"path": str(file_path)}
        )

        if results and len(results) > 0:
            artifact_id = results[0]['id']
            self._artifact_cache[rel_path] = artifact_id
            return artifact_id

        # Try partial match (for relative paths)
        query = """
            MATCH (a:Artifact)
            WHERE a.path CONTAINS $path_suffix
            RETURN a.id AS id
            LIMIT 1
        """
        results = self.hippocampus.execute_cypher(
            query,
            {"path_suffix": rel_path}
        )

        if results and len(results) > 0:
            artifact_id = results[0]['id']
            self._artifact_cache[rel_path] = artifact_id
            return artifact_id

        return None

    @lru_cache(maxsize=4096)
    def _lookup_artifact_id_cached(self, file_path_str: str) -> Optional[str]:
        """
        Cached version of artifact lookup for high-frequency calls.

        Args:
            file_path_str: String representation of file path

        Returns:
            Artifact ID or None
        """
        # This is a wrapper that uses LRU cache
        # The actual cache is in _artifact_cache, but this adds
        # an additional layer of caching with automatic LRU eviction
        return self._artifact_cache.get(file_path_str)

    def preload_cache(self) -> None:
        """
        Preload artifact cache with all artifacts in database.

        Useful for batch processing to avoid repeated queries.
        """
        query = "MATCH (a:Artifact) RETURN a.id AS id, a.path AS path"
        results = self.hippocampus.execute_cypher(query, {})

        for row in results:
            path = row['path']
            artifact_id = row['id']

            # Store as relative path if possible
            try:
                rel_path = str(Path(path).relative_to(self.project_root))
                self._artifact_cache[rel_path] = artifact_id
            except ValueError:
                # Keep absolute path
                self._artifact_cache[path] = artifact_id
