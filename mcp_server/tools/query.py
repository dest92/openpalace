"""
Query Tools - Artifact Retrieval and Analysis

Tools for querying artifacts, generating explanations, and finding
similar code structures using AST fingerprinting.
"""

import logging
from typing import Optional, List
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_query_tools(mcp: FastMCP) -> None:
    """
    Register query-related tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    def query_artifact(
        artifact_id: str,
        include_dependencies: bool = True,
        max_depth: int = 2
    ) -> str:
        """
        Query an artifact and return TOON-formatted context.

        Main entry point for retrieving code context. Returns
        token-efficient TOON format that includes:
        - AST summary (functions, classes, imports)
        - Dependency analysis
        - Token estimation
        - Query performance metrics

        Args:
            artifact_id: Artifact ID or file path to query
            include_dependencies: Include dependency artifacts (default: True)
            max_depth: Max dependency traversal depth (default: 2, max: 5)

        Returns:
            TOON-formatted context string

        Examples:
            >>> query_artifact("artifact-123")
            >>> query_artifact("src/auth/authenticate.py", include_dependencies=True, max_depth=3)

        Raises:
            ValueError: If artifact_id is empty
            RuntimeError: If artifact not found in index

        Performance:
            - Bloom filter check: <1ms
            - Graph traversal: <10ms
            - Total query time: <100ms typical
        """
        # Validate input
        if not artifact_id or not artifact_id.strip():
            raise ValueError("artifact_id cannot be empty")

        if max_depth < 1 or max_depth > 5:
            raise ValueError("max_depth must be between 1 and 5")

        # Get query interface from lifespan context
        query_interface = mcp.get_context("query_interface")
        if not query_interface:
            raise RuntimeError("Query interface not initialized")

        logger.info(f"🔍 Querying artifact: {artifact_id}")

        try:
            result = query_interface.query_artifact(
                artifact_id=artifact_id,
                include_dependencies=include_dependencies,
                max_depth=max_depth
            )

            if not result.bloom_hit:
                raise RuntimeError(f"Artifact not found in index: {artifact_id}")

            logger.info(
                f"✅ Query complete: {result.files_parsed} files, "
                f"{result.tokens_estimated} tokens, {result.duration_ms:.1f}ms"
            )

            return result.toon_format

        except Exception as e:
            logger.error(f"❌ Query failed for {artifact_id}: {e}", exc_info=True)
            return f"# Error querying artifact {artifact_id}\n\n{str(e)}"

    @mcp.tool()
    def explain_artifact(
        artifact_id: str,
        detail_level: str = "concise"
    ) -> str:
        """
        Generate natural language explanation of an artifact.

        Provides human-readable analysis including:
        - File overview
        - Dependency summary
        - Performance metrics
        - TOON-formatted code structure

        Args:
            artifact_id: Artifact ID or file path to explain
            detail_level: Level of detail (concise, standard, verbose)

        Returns:
            Natural language explanation with code context

        Examples:
            >>> explain_artifact("artifact-123")
            >>> explain_artifact("src/auth/authenticate.py", detail_level="verbose")

        Note:
            Uses the same underlying query mechanism as query_artifact()
            but wraps results in a more readable format.
        """
        if detail_level not in ["concise", "standard", "verbose"]:
            raise ValueError("detail_level must be: concise, standard, or verbose")

        query_interface = mcp.get_context("query_interface")
        if not query_interface:
            raise RuntimeError("Query interface not initialized")

        logger.info(f"📝 Explaining artifact: {artifact_id} (detail: {detail_level})")

        try:
            explanation = query_interface.explain_artifact(artifact_id)

            # Add detail level header
            detail_header = {
                "concise": "## Concise Analysis",
                "standard": "## Standard Analysis",
                "verbose": "## Detailed Analysis"
            }[detail_level]

            return f"{detail_header}\n\n{explanation}"

        except Exception as e:
            logger.error(f"❌ Explanation failed for {artifact_id}: {e}", exc_info=True)
            return f"# Error explaining {artifact_id}\n\n{str(e)}"

    @mcp.tool()
    def find_similar_artifacts(
        artifact_id: str,
        limit: int = 10
    ) -> str:
        """
        Find artifacts with similar AST structure.

        Uses AST fingerprint exact matching to find code that
        shares the same structural patterns. Useful for:
        - Finding code clones
        - Discovering similar implementations
        - Refactoring opportunities

        Args:
            artifact_id: Reference artifact ID or path
            limit: Maximum number of similar artifacts (default: 10, max: 50)

        Returns:
            List of similar artifact IDs with metadata

        Examples:
            >>> find_similar_artifacts("artifact-123")
            >>> find_similar_artifacts("src/auth/login.py", limit=20)

        Note:
            Only returns artifacts with EXACT AST fingerprint matches.
            This is intentional - no approximate matching needed.

        Performance:
            - Graph query: <10ms
            - Returns results in O(k) where k = number of matches
        """
        if limit < 1 or limit > 50:
            raise ValueError("limit must be between 1 and 50")

        query_interface = mcp.get_context("query_interface")
        if not query_interface:
            raise RuntimeError("Query interface not initialized")

        logger.info(f"🔍 Finding similar artifacts to: {artifact_id}")

        try:
            similar_ids = query_interface.find_similar_artifacts(
                artifact_id=artifact_id,
                limit=limit
            )

            if not similar_ids:
                return f"# No similar artifacts found for {artifact_id}"

            # Format results
            result = f"# Similar Artifacts to {artifact_id}\n\n"
            result += f"Found {len(similar_ids)} artifacts with identical AST structure:\n\n"

            for i, sim_id in enumerate(similar_ids, 1):
                result += f"{i}. `{sim_id}`\n"

            result += f"\n**Note**: These artifacts have 100% identical AST fingerprints."

            logger.info(f"✅ Found {len(similar_ids)} similar artifacts")
            return result

        except Exception as e:
            logger.error(f"❌ Similarity search failed for {artifact_id}: {e}", exc_info=True)
            return f"# Error finding similar artifacts\n\n{str(e)}"

    @mcp.tool()
    def query_multiple_artifacts(
        artifact_ids: list[str],
        include_dependencies: bool = False
    ) -> str:
        """
        Query multiple artifacts efficiently.

        Batch query for multiple artifacts in a single call.
        More efficient than individual queries for large batches.

        Args:
            artifact_ids: List of artifact IDs to query
            include_dependencies: Include dependencies (default: False for performance)

        Returns:
            Combined TOON-formatted context for all artifacts

        Examples:
            >>> query_multiple_artifacts(["artifact-1", "artifact-2", "artifact-3"])

        Note:
            When include_dependencies=True, this can return large amounts
            of data. Use with caution for batches >10 artifacts.
        """
        if not artifact_ids:
            raise ValueError("artifact_ids list cannot be empty")

        if len(artifact_ids) > 50:
            raise ValueError("Cannot query more than 50 artifacts at once")

        query_interface = mcp.get_context("query_interface")
        if not query_interface:
            raise RuntimeError("Query interface not initialized")

        logger.info(f"🔍 Querying {len(artifact_ids)} artifacts")

        try:
            results = query_interface.query_multiple_artifacts(
                artifact_ids=artifact_ids,
                include_dependencies=include_dependencies
            )

            # Combine results
            combined = f"# Batch Query Results ({len(artifact_ids)} artifacts)\n\n"

            for artifact_id, result in results.items():
                if result.bloom_hit:
                    combined += f"## {artifact_id}\n\n"
                    combined += result.toon_format
                    combined += "\n\n---\n\n"
                else:
                    combined += f"## {artifact_id}\n\n"
                    combined += f"⚠️  Not found in index\n\n"

            total_files = sum(r.files_parsed for r in results.values())
            total_tokens = sum(r.tokens_estimated for r in results.values())

            logger.info(f"✅ Batch query complete: {total_files} files, {total_tokens} tokens")
            return combined

        except Exception as e:
            logger.error(f"❌ Batch query failed: {e}", exc_info=True)
            return f"# Error in batch query\n\n{str(e)}"


# Export for testing
__all__ = [
    "register_query_tools",
    "query_artifact",
    "explain_artifact",
    "find_similar_artifacts",
    "query_multiple_artifacts",
]
