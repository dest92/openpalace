"""
MCP Resources - Read-Only Data Access

Resources provide data that LLMs can read, similar to GET endpoints.
Resources are identified by URIs and return structured data.
"""

from mcp_server.resources.stats import (
    register_stat_resources,
    get_statistics,
    get_performance_metrics,
)
from mcp_server.resources.metadata import (
    register_metadata_resources,
    get_artifact_metadata,
    get_dependency_graph,
)

__all__ = [
    "register_stat_resources",
    "register_metadata_resources",
    "get_statistics",
    "get_performance_metrics",
    "get_artifact_metadata",
    "get_dependency_graph",
]
