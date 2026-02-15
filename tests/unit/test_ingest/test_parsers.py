"""Tests for parser interfaces."""

import pytest
from pathlib import Path
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol


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
