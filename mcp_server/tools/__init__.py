"""
MCP Tools - Executable Operations

Tools are functions that LLMs can invoke to perform actions.
Each tool is decorated with @mcp.tool() and includes type hints
and comprehensive docstrings for automatic schema generation.

Note: Individual tool functions (query_artifact, etc.) are registered
via register_*() functions and are not directly importable.
"""

from mcp_server.tools.query import register_query_tools
from mcp_server.tools.compression import register_compression_tools
from mcp_server.tools.indexing import register_indexing_tools

__all__ = [
    "register_query_tools",
    "register_compression_tools",
    "register_indexing_tools",
]
