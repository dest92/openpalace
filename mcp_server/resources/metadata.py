"""
Metadata Resources - Artifact and Graph Metadata

Resources for querying artifact metadata, dependency graphs,
and code structure information.
"""

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_metadata_resources(mcp: FastMCP) -> None:
    """
    Register metadata-related resources with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.resource("artifact://{artifact_id}/metadata")
    def get_artifact_metadata(artifact_id: str) -> str:
        """
        Get metadata for a specific artifact.

        Returns detailed metadata including:
        - File path and language
        - AST fingerprint
        - Creation timestamp
        - Dependency count

        Resource URI pattern: artifact://{artifact_id}/metadata

        Args:
            artifact_id: Artifact ID or file path

        Returns:
            JSON-formatted artifact metadata

        Examples:
            artifact://artifact-123/metadata
            artifact://src/auth/authenticate.py/metadata
        """
        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            return '{"error": "Hippocampus not initialized"}'

        logger.debug(f"📄 Getting metadata for: {artifact_id}")

        try:
            # Normalize artifact ID
            if not artifact_id.startswith("artifact-"):
                artifact_id = f"artifact-{artifact_id}"

            # Get artifact node
            node = hippocampus.get_node(artifact_id)
            if not node:
                return f'{{"error": "Artifact not found: {artifact_id}"}}'

            # Get dependency count
            deps_result = hippocampus.execute_cypher(
                """
                MATCH (a:Artifact)-[:DEPENDS_ON]->(dep:Artifact)
                WHERE a.id = $artifact_id
                RETURN count(dep) AS count
                """,
                {"artifact_id": artifact_id}
            )
            dep_count = deps_result[0]["count"] if deps_result else 0

            # Get dependent count (what depends on this)
            dependent_result = hippocampus.execute_cypher(
                """
                MATCH (dep:Artifact)-[:DEPENDS_ON]->(a:Artifact)
                WHERE a.id = $artifact_id
                RETURN count(dep) AS count
                """,
                {"artifact_id": artifact_id}
            )
            dependent_count = dependent_result[0]["count"] if dependent_result else 0

            metadata = {
                "id": node.get("id"),
                "path": node.get("path"),
                "language": node.get("language"),
                "ast_fingerprint": node.get("ast_fingerprint"),
                "created_at": node.get("created_at"),
                "dependencies": {
                    "count": dep_count,
                    "outgoing": dep_count,
                    "incoming": dependent_count,
                }
            }

            import json
            return json.dumps(metadata, indent=2)

        except Exception as e:
            logger.error(f"❌ Metadata query failed: {e}", exc_info=True)
            return f'{{"error": "{str(e)}"}}'

    @mcp.resource("artifact://{artifact_id}/dependencies")
    def get_dependency_graph(artifact_id: str, max_depth: int = 2) -> str:
        """
        Get dependency graph for an artifact.

        Returns the dependency graph showing:
        - Direct dependencies (depth 1)
        - Transitive dependencies (depth >1)
        - Dependency relationships

        Resource URI pattern: artifact://{artifact_id}/dependencies?max_depth=2

        Args:
            artifact_id: Artifact ID or file path
            max_depth: Maximum depth of graph traversal (default: 2, max: 5)

        Returns:
            JSON-formatted dependency graph

        Examples:
            artifact://artifact-123/dependencies
            artifact://src/auth/authenticate.py/dependencies?max_depth=3
        """
        if max_depth < 1 or max_depth > 5:
            return '{"error": "max_depth must be between 1 and 5"}'

        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            return '{"error": "Hippocampus not initialized"}'

        logger.debug(f"🔗 Getting dependency graph for: {artifact_id} (depth={max_depth})")

        try:
            # Normalize artifact ID
            if not artifact_id.startswith("artifact-"):
                artifact_id = f"artifact-{artifact_id}"

            # Get dependency graph
            query = f"""
                MATCH path = (a:Artifact)-[:DEPENDS_ON*1..{max_depth}]->(dep:Artifact)
                WHERE a.id = $artifact_id
                RETURN dep.id AS id, dep.path AS path, dep.language AS language,
                       length(path) AS depth
                ORDER BY depth, dep.path
                LIMIT 100
            """

            result = hippocampus.execute_cypher(query, {"artifact_id": artifact_id})

            if not result:
                return f'{{"artifact": "{artifact_id}", "dependencies": []}}'

            # Group by depth
            dependencies = {}
            for row in result:
                depth = row["depth"]
                if depth not in dependencies:
                    dependencies[depth] = []

                dependencies[depth].append({
                    "id": row["id"],
                    "path": row["path"],
                    "language": row["language"],
                })

            # Format as hierarchical structure
            graph = {
                "artifact": artifact_id,
                "max_depth": max_depth,
                "total_dependencies": len(result),
                "by_depth": {
                    str(depth): [
                        {"id": dep["id"], "path": dep["path"], "language": dep["language"]}
                        for dep in deps
                    ]
                    for depth, deps in dependencies.items()
                }
            }

            import json
            return json.dumps(graph, indent=2)

        except Exception as e:
            logger.error(f"❌ Dependency graph query failed: {e}", exc_info=True)
            return f'{{"error": "{str(e)}"}}'

    @mcp.resource("index://languages")
    def get_language_breakdown() -> str:
        """
        Get language breakdown of indexed artifacts.

        Returns statistics about which programming languages
        are represented in the index.

        Resource URI: index://languages

        Returns:
            JSON-formatted language breakdown
        """
        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            return '{"error": "Hippocampus not initialized"}'

        logger.debug("🌐 Getting language breakdown")

        try:
            result = hippocampus.execute_cypher(
                """
                MATCH (a:Artifact)
                RETURN a.language AS language, count(a) AS count
                ORDER BY count DESC
                """,
                {}
            )

            if not result:
                return '{"languages": [], "total": 0}'

            total = sum(row["count"] for row in result)

            breakdown = {
                "total": total,
                "languages": [
                    {
                        "language": row["language"],
                        "count": row["count"],
                        "percentage": round((row["count"] / total) * 100, 1)
                    }
                    for row in result
                ]
            }

            import json
            return json.dumps(breakdown, indent=2)

        except Exception as e:
            logger.error(f"❌ Language breakdown failed: {e}", exc_info=True)
            return f'{{"error": "{str(e)}"}}'


# Export for testing
__all__ = [
    "register_metadata_resources",
    "get_artifact_metadata",
    "get_dependency_graph",
    "get_language_breakdown",
]
