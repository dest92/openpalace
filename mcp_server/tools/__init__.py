"""
MCP Tools - Executable Operations

Tools are functions that LLMs can invoke to perform actions.
Each tool is decorated with @mcp.tool() and includes type hints
and comprehensive docstrings for automatic schema generation.
"""

from mcp_server.tools.query import (
    register_query_tools,
    query_artifact,
    explain_artifact,
    find_similar,
)
from mcp_server.tools.compression import (
    register_compression_tools,
    compress_code,
    estimate_compression,
)
from mcp_server.tools.indexing import (
    register_indexing_tools,
    index_files,
    reindex_file,
    delete_from_index,
)

__all__ = [
    "register_query_tools",
    "register_compression_tools",
    "register_indexing_tools",
    "query_artifact",
    "explain_artifact",
    "find_similar",
    "compress_code",
    "estimate_compression",
    "index_files",
    "reindex_file",
    "delete_from_index",
]
