"""
Indexing Tools - File Indexing and Database Management

Tools for indexing files, managing the Palace Mental database,
and maintaining the knowledge graph.
"""

import logging
from typing import List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_indexing_tools(mcp: FastMCP) -> None:
    """
    Register indexing-related tools with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    def index_files(
        paths: List[str],
        force: bool = False,
        language: Optional[str] = None
    ) -> str:
        """
        Index files into Palace Mental knowledge graph.

        Parses source files, extracts AST fingerprints, builds
        dependency graph, and stores in KuzuDB.

        Args:
            paths: List of file or directory paths to index
            force: Re-index even if already indexed (default: False)
            language: Override language detection (optional)

        Returns:
            Indexing summary with statistics

        Examples:
            >>> index_files(["src/"])
            >>> index_files(["file.py", "file2.py"], force=True)
            >>> index_files(["src/"], language="python")

        Performance:
            - Small project (<100 files): ~10 seconds
            - Medium project (<1000 files): ~1-2 minutes
            - Large project (<10000 files): ~5-10 minutes

        Note:
            This is a long-running operation for large codebases.
            Progress is logged to stderr for monitoring.
        """
        if not paths:
            raise ValueError("paths list cannot be empty")

        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            raise RuntimeError("Hippocampus not initialized")

        logger.info(f"📇 Indexing {len(paths)} paths (force={force})")

        try:
            from palace.ingest.pipeline import IngestionPipeline

            stats = {
                "total_files": 0,
                "indexed": 0,
                "skipped": 0,
                "failed": 0,
                "errors": []
            }

            for path_str in paths:
                path_obj = Path(path_str)

                if not path_obj.exists():
                    stats["errors"].append(f"Path not found: {path_str}")
                    logger.warning(f"⚠️  Path not found: {path_str}")
                    continue

                # Collect files to index
                files_to_index = []
                if path_obj.is_file():
                    files_to_index = [path_obj]
                else:  # Directory
                    # Collect all supported source files
                    for ext in [".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"]:
                        files_to_index.extend(path_obj.rglob(f"*{ext}"))

                stats["total_files"] += len(files_to_index)

                # Index files
                pipeline = IngestionPipeline(hippocampus)

                for file_path in files_to_index:
                    try:
                        # Check if already indexed
                        artifact_id = f"artifact-{file_path}"
                        existing = hippocampus.get_node(artifact_id)

                        if existing and not force:
                            stats["skipped"] += 1
                            logger.debug(f"⊘ Skipped (already indexed): {file_path}")
                            continue

                        # Parse and index
                        result = pipeline.ingest_file(file_path, language=language)
                        if result.get("success"):
                            stats["indexed"] += 1
                            logger.info(f"✅ Indexed: {file_path}")
                        else:
                            stats["failed"] += 1
                            error_msg = result.get("error", "Unknown error")
                            stats["errors"].append(f"{file_path}: {error_msg}")
                            logger.error(f"❌ Failed to index {file_path}: {error_msg}")

                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append(f"{file_path}: {str(e)}")
                        logger.error(f"❌ Error indexing {file_path}: {e}", exc_info=True)

            # Format summary
            result = f"""# Indexing Complete

| Metric | Count |
|--------|-------|
| Total Files | {stats["total_files"]} |
| Indexed | {stats["indexed"]} |
| Skipped | {stats["skipped"]} |
| Failed | {stats["failed"]} |

---

## Errors ({len(stats["errors"])})

"""

            if stats["errors"]:
                for error in stats["errors"][:20]:  # Show first 20 errors
                    result += f"- {error}\n"

                if len(stats["errors"]) > 20:
                    result += f"- ... and {len(stats['errors']) - 20} more errors\n"
            else:
                result += "✅ No errors!\n"

            logger.info(
                f"✅ Indexing complete: {stats['indexed']} indexed, "
                f"{stats['skipped']} skipped, {stats['failed']} failed"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Indexing failed: {e}", exc_info=True)
            return f"# Error during indexing\n\n{str(e)}"

    @mcp.tool()
    def reindex_file(
        file_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Re-index a single file, replacing existing entry.

        Useful for updating the index after code changes.

        Args:
            file_path: Path to file to re-index
            language: Override language detection (optional)

        Returns:
            Re-indexing result

        Examples:
            >>> reindex_file("src/auth/authenticate.py")

        Note:
            This deletes the old artifact and creates a new one,
            preserving relationships to other artifacts.
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            raise RuntimeError("Hippocampus not initialized")

        logger.info(f"🔄 Re-indexing: {file_path}")

        try:
            from palace.ingest.pipeline import IngestionPipeline

            # Delete old artifact
            artifact_id = f"artifact-{file_path_obj}"
            hippocampus.delete_node(artifact_id)

            # Re-index
            pipeline = IngestionPipeline(hippocampus)
            result = pipeline.ingest_file(file_path_obj, language=language)

            if result.get("success"):
                logger.info(f"✅ Re-indexed: {file_path}")
                return f"""# Re-indexed Successfully

**File**: {file_path}
**Artifact ID**: {artifact_id}
**Language**: {result.get('language', 'auto-detected')}

---

✅ File has been re-indexed with updated AST fingerprint.
"""
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Re-indexing failed: {error_msg}")
                return f"# Re-indexing Failed\n\n{error_msg}"

        except Exception as e:
            logger.error(f"❌ Re-indexing error: {e}", exc_info=True)
            return f"# Error re-indexing file\n\n{str(e)}"

    @mcp.tool()
    def delete_from_index(
        artifact_id: str
    ) -> str:
        """
        Delete an artifact from the index.

        Removes the artifact node and its edges from the knowledge graph.
        Dependent artifacts will lose the dependency relationship.

        Args:
            artifact_id: Artifact ID or file path to delete

        Returns:
            Deletion result

        Examples:
            >>> delete_from_index("artifact-123")
            >>> delete_from_index("src/deleted/file.py")

        Warning:
            This operation cannot be undone. The artifact will need
            to be re-indexed to restore it.
        """
        if not artifact_id or not artifact_id.strip():
            raise ValueError("artifact_id cannot be empty")

        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            raise RuntimeError("Hippocampus not initialized")

        logger.info(f"🗑️  Deleting artifact: {artifact_id}")

        try:
            # Normalize artifact ID
            if not artifact_id.startswith("artifact-"):
                artifact_id = f"artifact-{artifact_id}"

            # Check if exists
            existing = hippocampus.get_node(artifact_id)
            if not existing:
                return f"# Artifact Not Found\n\nArtifact `{artifact_id}` does not exist in index."

            # Delete
            hippocampus.delete_node(artifact_id)

            logger.info(f"✅ Deleted: {artifact_id}")
            return f"""# Deleted Successfully

**Artifact ID**: {artifact_id}
**Path**: {existing.get('path', 'unknown')}

---

⚠️  Artifact has been removed from the index. Dependencies on this
artifact have been removed from the graph.

To restore, re-run: `index_files(["{existing.get('path', '')}"])`
"""

        except Exception as e:
            logger.error(f"❌ Deletion failed: {e}", exc_info=True)
            return f"# Error deleting artifact\n\n{str(e)}"

    @mcp.tool()
    def get_index_status(
        path: Optional[str] = None
    ) -> str:
        """
        Get indexing status for a path or entire database.

        Shows statistics about indexed files, coverage, and database size.

        Args:
            path: Optional path to filter (default: entire database)

        Returns:
            Index status summary

        Examples:
            >>> get_index_status()
            >>> get_index_status("src/auth/")
        """
        hippocampus = mcp.get_context("hippocampus")
        if not hippocampus:
            raise RuntimeError("Hippocampus not initialized")

        logger.info(f"📊 Getting index status (path={path})")

        try:
            # Query statistics
            if path:
                # Filter by path
                result = hippocampus.execute_cypher(
                    """
                    MATCH (a:Artifact)
                    WHERE a.path STARTS WITH $path
                    RETURN count(a) AS count
                    """,
                    {"path": path}
                )
                count = result[0]["count"] if result else 0

                result = f"""# Index Status - {path}

**Indexed Files**: {count:,}

---

"""
            else:
                # Entire database
                artifacts = hippocampus.execute_cypher(
                    "MATCH (a:Artifact) RETURN count(a) AS count",
                    {}
                )
                edges = hippocampus.execute_cypher(
                    "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS count",
                    {}
                )

                artifact_count = artifacts[0]["count"] if artifacts else 0
                edge_count = edges[0]["count"] if edges else 0

                # Get language breakdown
                languages = hippocampus.execute_cypher(
                    """
                    MATCH (a:Artifact)
                    RETURN a.language AS lang, count(a) AS count
                    ORDER BY count DESC
                    """,
                    {}
                )

                lang_breakdown = "\n".join([
                    f"- {row['lang']}: {row['count']:,} files"
                    for row in languages
                ])

                result = f"""# Palace Mental Index Status

## Overview

| Metric | Count |
|--------|-------|
| Total Artifacts | {artifact_count:,} |
| Dependency Edges | {edge_count:,} |
| Avg Dependencies | {edge_count / artifact_count if artifact_count > 0 else 0:.1f} |

## Language Breakdown

{lang_breakdown}

---

💾 Database location: `{Path.cwd()}/palace_db`
"""

            return result

        except Exception as e:
            logger.error(f"❌ Status query failed: {e}", exc_info=True)
            return f"# Error getting status\n\n{str(e)}"


# Export for testing
__all__ = [
    "register_indexing_tools",
    "index_files",
    "reindex_file",
    "delete_from_index",
    "get_index_status",
]
