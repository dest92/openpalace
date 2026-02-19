"""Configuration module for Palace Mental."""

from palace.config.db_config import (
    KUZU_OPTIMAL_CONFIG,
    SQLITE_OPTIMAL_PRAGMAS,
    PERFORMANCE_CONFIG,
    get_kuzu_config,
    get_sqlite_pragmas,
)

__all__ = [
    'KUZU_OPTIMAL_CONFIG',
    'SQLITE_OPTIMAL_PRAGMAS',
    'PERFORMANCE_CONFIG',
    'get_kuzu_config',
    'get_sqlite_pragmas',
]
