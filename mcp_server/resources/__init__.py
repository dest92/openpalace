"""
MCP Resources - Read-Only Data Access

Resources provide data that LLMs can read, similar to GET endpoints.
Resources are identified by URIs and return structured data.

Note: Individual resource functions (get_statistics, etc.) are registered
via register_*() functions and are not directly importable.
"""

from mcp_server.resources.stats import register_stat_resources
from mcp_server.resources.metadata import register_metadata_resources

__all__ = [
    "register_stat_resources",
    "register_metadata_resources",
]
