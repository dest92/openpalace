import pytest
from palace.shared.exceptions import (
    PalaceError,
    DatabaseError,
    ConnectionError,
    SchemaError,
    IngestionError,
    ParseError,
    UnsupportedLanguageError,
    ActivationError,
    PlasticityError,
    CLIError,
    PalaceNotInitializedError
)

def test_exception_hierarchy():
    assert issubclass(DatabaseError, PalaceError)
    assert issubclass(ConnectionError, DatabaseError)
    assert issubclass(SchemaError, DatabaseError)
    assert issubclass(IngestionError, PalaceError)
    assert issubclass(ParseError, IngestionError)
    assert issubclass(UnsupportedLanguageError, IngestionError)
    assert issubclass(ActivationError, PalaceError)
    assert issubclass(PlasticityError, PalaceError)
    assert issubclass(CLIError, PalaceError)
    assert issubclass(PalaceNotInitializedError, CLIError)

def test_parse_error_attributes():
    error = ParseError("test.py", 42, "syntax error")
    assert "test.py" in str(error)
    assert "42" in str(error)
    assert "syntax error" in str(error)
    assert error.file_path == "test.py"
    assert error.line == 42

def test_exception_messages():
    assert "database" in str(DatabaseError("database error")).lower()
    assert "not initialized" in str(PalaceNotInitializedError()).lower()
