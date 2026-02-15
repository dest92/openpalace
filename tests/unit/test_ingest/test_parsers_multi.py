"""Unit tests for multi-language parsers."""

import pytest
from pathlib import Path
from palace.ingest.parsers.javascript import JavaScriptParser
from palace.ingest.parsers.typescript import TypeScriptParser
from palace.ingest.parsers.go import GoParser
from palace.ingest.parsers.base import Dependency, Symbol


class TestJavaScriptParser:
    """Tests for JavaScriptParser."""

    @pytest.fixture
    def parser(self):
        """Create JavaScript parser instance."""
        return JavaScriptParser()

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".js" in parser.supported_extensions()
        assert ".jsx" in parser.supported_extensions()
        assert ".mjs" in parser.supported_extensions()
        assert ".cjs" in parser.supported_extensions()

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_extract_es6_imports(self, parser):
        """Test ES6 import extraction."""
        content = """
        import React from 'react';
        import { useState } from 'react';
        import axios from 'axios';
        """
        deps = parser.parse_dependencies(Path("test.js"), content)

        assert len(deps) == 3
        assert any(d.path == "react" for d in deps)
        assert any(d.path == "axios" for d in deps)

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_extract_commonjs_requires(self, parser):
        """Test CommonJS require extraction."""
        content = """
        const express = require('express');
        const logger = require('./logger');
        """
        deps = parser.parse_dependencies(Path("test.js"), content)

        assert len(deps) >= 1
        assert any(d.path == "express" for d in deps)

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_extract_functions(self, parser):
        """Test function extraction."""
        content = """
        function fetchData() {
            return data;
        }

        const processData = function(data) {
            return data;
        }
        """
        symbols = parser.extract_symbols(content)

        # Should find function declarations
        assert any(s.name == "fetchData" and s.type == "function" for s in symbols)

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_extract_classes(self, parser):
        """Test class extraction."""
        content = """
        class MyComponent extends React.Component {
            render() {
                return <div />;
            }
        }
        """
        symbols = parser.extract_symbols(content)

        assert any(s.name == "MyComponent" and s.type == "class" for s in symbols)

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_fingerprint_deterministic(self, parser):
        """Test that fingerprinting is deterministic."""
        content = "const x = 42;"
        fp1 = parser.compute_fingerprint(content)
        fp2 = parser.compute_fingerprint(content)

        assert fp1 == fp2

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_fingerprint_different_content(self, parser):
        """Test that different content produces different fingerprints."""
        fp1 = parser.compute_fingerprint("const x = 42;")
        fp2 = parser.compute_fingerprint("const x = 43;")

        assert fp1 != fp2


class TestTypeScriptParser:
    """Tests for TypeScriptParser."""

    @pytest.fixture
    def parser(self):
        """Create TypeScript parser instance."""
        return TypeScriptParser()

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".ts" in parser.supported_extensions()
        assert ".tsx" in parser.supported_extensions()

    @pytest.mark.skipif(
        not TypeScriptParser().is_available(),
        reason="tree-sitter-typescript not installed"
    )
    def test_extract_imports(self, parser):
        """Test import extraction."""
        content = """
        import React from 'react';
        import { useState } from 'react';
        import type { User } from './types';
        """
        deps = parser.parse_dependencies(Path("test.ts"), content)

        assert len(deps) >= 2
        assert any(d.path == "react" for d in deps)

    @pytest.mark.skipif(
        not TypeScriptParser().is_available(),
        reason="tree-sitter-typescript not installed"
    )
    def test_extract_interfaces(self, parser):
        """Test interface extraction."""
        content = """
        interface User {
            name: string;
            age: number;
        }

        interface Admin extends User {
            permissions: string[];
        }
        """
        symbols = parser.extract_symbols(content)

        assert any(s.name == "User" and s.type == "interface" for s in symbols)
        assert any(s.name == "Admin" and s.type == "interface" for s in symbols)

    @pytest.mark.skipif(
        not TypeScriptParser().is_available(),
        reason="tree-sitter-typescript not installed"
    )
    def test_extract_type_aliases(self, parser):
        """Test type alias extraction."""
        content = """
        type UserID = number;
        type UserMap = Map<number, string>;
        """
        symbols = parser.extract_symbols(content)

        assert any(s.name == "UserID" and s.type == "type_alias" for s in symbols)
        assert any(s.name == "UserMap" and s.type == "type_alias" for s in symbols)

    @pytest.mark.skipif(
        not TypeScriptParser().is_available(),
        reason="tree-sitter-typescript not installed"
    )
    def test_extract_classes(self, parser):
        """Test class extraction."""
        content = """
        class UserService {
            private users: User[] = [];

            getUser(id: number): User | undefined {
                return this.users.find(u => u.id === id);
            }
        }
        """
        symbols = parser.extract_symbols(content)

        assert any(s.name == "UserService" and s.type == "class" for s in symbols)

    @pytest.mark.skipif(
        not TypeScriptParser().is_available(),
        reason="tree-sitter-typescript not installed"
    )
    def test_fingerprint_deterministic(self, parser):
        """Test that fingerprinting is deterministic."""
        content = "const x: number = 42;"
        fp1 = parser.compute_fingerprint(content)
        fp2 = parser.compute_fingerprint(content)

        assert fp1 == fp2


class TestGoParser:
    """Tests for GoParser."""

    @pytest.fixture
    def parser(self):
        """Create Go parser instance."""
        return GoParser()

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".go" in parser.supported_extensions()

    @pytest.mark.skipif(
        not GoParser().is_available(),
        reason="tree-sitter-go not installed"
    )
    def test_extract_imports(self, parser):
        """Test import extraction."""
        content = """
        package main

        import (
            "fmt"
            "net/http"
            "github.com/gin-gonic/gin"
        )
        """
        deps = parser.parse_dependencies(Path("test.go"), content)

        assert len(deps) >= 3
        assert any(d.path == "fmt" for d in deps)
        assert any(d.path == "net/http" for d in deps)

    @pytest.mark.skipif(
        not GoParser().is_available(),
        reason="tree-sitter-go not installed"
    )
    def test_extract_package(self, parser):
        """Test package extraction."""
        content = """
        package main

        func main() {
            fmt.Println("Hello")
        }
        """
        symbols = parser.extract_symbols(content)

        assert any(s.type == "package" for s in symbols)

    @pytest.mark.skipif(
        not GoParser().is_available(),
        reason="tree-sitter-go not installed"
    )
    def test_extract_functions(self, parser):
        """Test function extraction."""
        content = """
        package main

        func add(a int, b int) int {
            return a + b
        }

        func greet(name string) {
            fmt.Printf("Hello, %s", name)
        }
        """
        symbols = parser.extract_symbols(content)

        assert any(s.name == "add" and s.type == "function" for s in symbols)
        assert any(s.name == "greet" and s.type == "function" for s in symbols)

    @pytest.mark.skipif(
        not GoParser().is_available(),
        reason="tree-sitter-go not installed"
    )
    def test_extract_structs(self, parser):
        """Test struct extraction."""
        content = """
        package main

        type User struct {
            Name string
            Age  int
        }

        type Service struct {
            users []User
        }
        """
        symbols = parser.extract_symbols(content)

        assert any(s.name == "User" and s.type == "struct" for s in symbols)
        assert any(s.name == "Service" and s.type == "struct" for s in symbols)

    @pytest.mark.skipif(
        not GoParser().is_available(),
        reason="tree-sitter-go not installed"
    )
    def test_fingerprint_deterministic(self, parser):
        """Test that fingerprinting is deterministic."""
        content = 'package main\n\nfunc main() {}'
        fp1 = parser.compute_fingerprint(content)
        fp2 = parser.compute_fingerprint(content)

        assert fp1 == fp2


class TestParserRegistry:
    """Tests for ParserRegistry."""

    def test_registry_singleton(self):
        """Test that registry returns singleton instance."""
        from palace.ingest.parsers.registry import ParserRegistry

        reg1 = ParserRegistry.instance()
        reg2 = ParserRegistry.instance()

        assert reg1 is reg2

    def test_registry_has_python_parser(self):
        """Test that Python parser is registered."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        parser = registry.get_parser(Path("test.py"))

        assert parser is not None
        assert parser.__class__.__name__ == "PythonParser"

    def test_detect_python_language(self):
        """Test Python language detection."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        lang = registry.detect_language(Path("test.py"))

        assert lang == "python"

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_registry_has_javascript_parser(self):
        """Test that JavaScript parser is registered when available."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        parser = registry.get_parser(Path("test.js"))

        assert parser is not None
        assert parser.__class__.__name__ == "JavaScriptParser"

    @pytest.mark.skipif(
        not JavaScriptParser().is_available(),
        reason="tree-sitter-javascript not installed"
    )
    def test_detect_javascript_language(self):
        """Test JavaScript language detection."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        lang = registry.detect_language(Path("test.js"))

        assert lang == "javascript"

    def test_get_supported_extensions(self):
        """Test getting all supported extensions."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        extensions = registry.get_supported_extensions()

        # Should always have .py (Python)
        assert ".py" in extensions

    def test_get_supported_languages(self):
        """Test getting all supported languages."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        languages = registry.get_supported_languages()

        # Should always have python
        assert "python" in languages

    def test_unknown_language_returns_unknown(self):
        """Test that unknown file types return 'unknown'."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        lang = registry.detect_language(Path("test.unknown"))

        assert lang == "unknown"

    def test_unsupported_file_returns_none(self):
        """Test that unsupported files return None parser."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()
        parser = registry.get_parser(Path("test.unknown"))

        assert parser is None
