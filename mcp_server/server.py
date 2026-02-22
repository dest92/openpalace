#!/usr/bin/env python3
"""
Palace Mental MCP Server - Main Entry Point

FastMCP server that exposes Palace Mental V2 capabilities to LLMs.
Uses stdio transport for local IDE integration (Claude Desktop, Cursor, etc.).

Architecture:
    - FastMCP for rapid server development
    - Lifespan management for Hippocampus connection
    - Structured error handling with stderr logging
    - Type-safe tool definitions with docstrings

Author: Palace Team
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Optional, Dict, Any

import typer
from mcp.server.fastmcp import FastMCP

from palace.core.hippocampus import Hippocampus
from palace.core.bloom_filter import CompressedBloomFilter
from palace.core.agent_interface import AgentQueryInterface
from palace.shared.exceptions import PalaceError

# Configure logging to stderr (critical for MCP compatibility)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # MCP uses stdout for protocol
)
logger = logging.getLogger(__name__)

# Global server state
_app_state: Dict[str, Any] = {}


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """
    Manage server startup and shutdown lifecycle.

    Initializes Palace Mental components on startup and ensures
    proper cleanup on shutdown.

    Yields:
        Dictionary with Hippocampus, BloomFilter, and AgentQueryInterface
    """
    # Startup: Initialize Palace Mental components
    logger.info("🚀 Initializing Palace Mental MCP Server...")

    try:
        # Initialize Hippocampus (KuzuDB connection)
        db_path = Path.cwd() / "palace_db"
        logger.info(f"📂 Connecting to database: {db_path}")

        hippocampus = Hippocampus(str(db_path))
        logger.info("✅ Hippocampus connected")

        # Initialize Bloom Filter
        # In production, load from persisted filter file
        bloom_filter = CompressedBloomFilter(
            expected_items=1_000_000,
            false_positive_rate=0.001
        )
        logger.info("✅ Bloom filter initialized")

        # Initialize Agent Query Interface
        query_interface = AgentQueryInterface(
            hippocampus=hippocampus,
            bloom_filter=bloom_filter
        )
        logger.info("✅ Agent query interface ready")

        # Provide state to tools
        state = {
            "hippocampus": hippocampus,
            "bloom_filter": bloom_filter,
            "query_interface": query_interface,
        }

        logger.info("✅ Palace Mental MCP Server ready")
        yield state

    except Exception as e:
        logger.error(f"❌ Failed to initialize server: {e}", exc_info=True)
        raise RuntimeError(f"Server initialization failed: {e}") from e

    finally:
        # Shutdown: Cleanup resources
        logger.info("🧹 Shutting down Palace Mental MCP Server...")

        try:
            # Close hippocampus connection if it was successfully initialized
            # Check if the variable exists in the exception handler scope
            hippocampus.close()
            logger.info("✅ Hippocampus connection closed")
        except NameError:
            # hippocampus was never initialized
            logger.debug("ℹ️  Hippocampus not initialized, skipping cleanup")
        except Exception as e:
            logger.error(f"⚠️  Error during shutdown: {e}", exc_info=True)


def create_server(
    name: str = "palace-mental",
    json_response: bool = True
) -> FastMCP:
    """
    Create and configure the FastMCP server.

    Args:
        name: Server name for identification
        json_response: Return structured JSON responses

    Returns:
        Configured FastMCP server instance
    """
    # Create FastMCP server with lifespan management
    mcp = FastMCP(
        name=name,
        json_response=json_response,
        lifespan=server_lifespan
    )

    # Register tools
    from mcp_server.tools.query import register_query_tools
    from mcp_server.tools.compression import register_compression_tools
    from mcp_server.tools.indexing import register_indexing_tools

    register_query_tools(mcp)
    register_compression_tools(mcp)
    register_indexing_tools(mcp)

    # Register resources
    from mcp_server.resources.stats import register_stat_resources
    from mcp_server.resources.metadata import register_metadata_resources

    register_stat_resources(mcp)
    register_metadata_resources(mcp)

    # Register prompts
    from mcp_server.prompts.templates import register_prompt_templates

    register_prompt_templates(mcp)

    return mcp


def main(
    log_level: str = typer.Option("INFO", help="Logging level"),
    transport: str = typer.Option("stdio", help="Transport type (stdio or streamable-http)")
) -> None:
    """
    Run the Palace Mental MCP server.

    Usage:
        python -m mcp_server.server
        python -m mcp_server.server --log-level DEBUG
    """
    # Set log level
    log_level_num = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level_num)

    # Create and run server
    mcp = create_server()

    logger.info(f"🎯 Starting MCP server with {transport} transport")

    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    typer.run(main)
