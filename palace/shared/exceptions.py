"""Exception hierarchy for Palacio Mental."""


class PalaceError(Exception):
    """Base exception for all Palace errors."""
    pass


# Database errors

class DatabaseError(PalaceError):
    """Base for KuzuDB/SQLite errors."""
    pass


class ConnectionError(DatabaseError):
    """Failed to connect to database."""
    pass


class SchemaError(DatabaseError):
    """Schema mismatch or corrupted database."""
    pass


# Ingestion errors

class IngestionError(PalaceError):
    """Base for ingestion failures."""
    pass


class ParseError(IngestionError):
    """Failed to parse file."""

    def __init__(self, file_path: str, line: int, message: str):
        self.file_path = file_path
        self.line = line
        super().__init__(f"{file_path}:{line} - {message}")


class UnsupportedLanguageError(IngestionError):
    """No parser available for language."""
    pass


# Algorithm errors

class ActivationError(PalaceError):
    """Spreading activation failure."""
    pass


class PlasticityError(PalaceError):
    """Hebbian learning failure."""
    pass


# CLI errors

class CLIError(PalaceError):
    """User-facing CLI error."""
    pass


class PalaceNotInitializedError(CLIError):
    """Command requires init to be run first."""

    def __init__(self):
        super().__init__("Palace not initialized. Run 'palace init' first.")
