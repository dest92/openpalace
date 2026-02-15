"""Tests for parser interfaces."""

import pytest
from pathlib import Path
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol

try:
    from palace.ingest.parsers.python import PythonParser
    PYTHON_PARSER_AVAILABLE = True
except ImportError:
    PYTHON_PARSER_AVAILABLE = False


def test_base_parser_is_abstract():
    """Test that BaseParser cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseParser()


def test_dependency_model():
    """Test Dependency data model."""
    dep = Dependency(
        path="src/auth.py",
        type="IMPORT",
        lineno=10
    )
    assert dep.path == "src/auth.py"
    assert dep.type == "IMPORT"
    assert dep.lineno == 10


def test_symbol_model():
    """Test Symbol data model."""
    symbol = Symbol(
        name="authenticate",
        type="function",
        lineno=5,
        docstring="Authenticates user"
    )
    assert symbol.name == "authenticate"
    assert symbol.type == "function"


@pytest.mark.skipif(not PYTHON_PARSER_AVAILABLE, reason="Python parser not available")
def test_python_parser_extensions():
    """Test supported extensions."""
    parser = PythonParser()
    assert ".py" in parser.supported_extensions()
    assert ".pyx" in parser.supported_extensions()


@pytest.mark.skipif(not PYTHON_PARSER_AVAILABLE, reason="Python parser not available")
def test_python_parse_imports():
    """Test parsing Python imports."""
    parser = PythonParser()
    code = """
import os
from typing import List
import numpy as np
from .auth import authenticate
"""
    deps = parser.parse_dependencies(Path("test.py"), code)
    assert len(deps) >= 3
    assert any(d.path == "os" for d in deps)
    assert any(d.type == "IMPORT" for d in deps)


@pytest.mark.skipif(not PYTHON_PARSER_AVAILABLE, reason="Python parser not available")
def test_python_extract_symbols():
    """Test extracting functions and classes."""
    parser = PythonParser()
    code = """
def calculate(x, y):
    '''Calculate something.'''
    return x + y

class Calculator:
    '''A calculator class.'''
    def add(self, a, b):
        return a + b
"""
    symbols = parser.extract_symbols(code)
    assert len(symbols) >= 2
    assert any(s.name == "calculate" for s in symbols)
    assert any(s.name == "Calculator" for s in symbols)


@pytest.mark.skipif(not PYTHON_PARSER_AVAILABLE, reason="Python parser not available")
def test_python_fingerprint():
    """Test AST fingerprinting."""
    parser = PythonParser()
    code1 = "def foo(): pass"
    code2 = "def foo(): pass"
    code3 = "def foo(): return 42"  # Different structure

    fp1 = parser.compute_fingerprint(code1)
    fp2 = parser.compute_fingerprint(code2)
    fp3 = parser.compute_fingerprint(code3)

    assert fp1 == fp2  # Same AST
    assert fp1 != fp3  # Different AST

