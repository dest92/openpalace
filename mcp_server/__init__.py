"""
Palace Mental MCP Server

Model Context Protocol (MCP) server for Palace Mental V2.
Exposes query, compression, indexing, and statistics capabilities to LLMs.

Architecture:
    - FastMCP server using stdio transport
    - Tools: Executable operations (query, compress, index)
    - Resources: Read-only data access (stats, metadata)
    - Prompts: Reusable interaction templates

Usage:
    # Direct execution
    python -m mcp_server.server

    # With Claude Desktop (config.json)
    {
      "mcpServers": {
        "palace-mental": {
          "command": "python",
          "args": ["/path/to/palace2/mcp_server/server.py"]
        }
      }
    }
"""

__version__ = "1.0.0"
__author__ = "Palace Team"

from mcp_server.server import create_server

__all__ = ["create_server"]
