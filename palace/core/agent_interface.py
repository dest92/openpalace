"""
Palace Mental V2 - Agent Query Interface

Optimized end-to-end flow for AI agent queries:
1. Bloom Filter Check → O(1) membership (<1ms)
2. KuzuDB Graph Traversal → Dependencies (<10ms)
3. Parse Code → Tree-sitter AST (<50ms)
4. TOON Export → Token-efficient format
5. Return to Agent → Structured context

Total: <100ms typical for 3-4 files
"""

from typing import List, Optional, Dict, Tuple
from pathlib import Path
import time
from dataclasses import dataclass

from palace.core.hippocampus import Hippocampus
from palace.core.bloom_filter import CompressedBloomFilter
from palace.core.ast_fingerprint import hash_file_ast, ASTFingerprintCache
from palace.core.toon import (
    ASTSummary,
    TOONEncoder,
    create_ast_summary,
    export_to_agent
)


@dataclass
class QueryResult:
    """Result of an agent query."""
    toon_format: str  # TOON-formatted context
    files_parsed: int  # Number of files parsed
    tokens_estimated: int  # Estimated token count
    duration_ms: float  # Total query time
    bloom_hit: bool  # Whether Bloom filter matched
    dependencies_found: int  # Number of dependencies discovered


class AgentQueryInterface:
    """
    High-performance interface for AI agent queries.

    Replaces embedding-based search with:
    - AST fingerprints for exact matching
    - Bloom filter for O(1) membership
    - Graph traversal for relationships
    - TOON format for token efficiency
    """

    def __init__(
        self,
        hippocampus: Hippocampus,
        bloom_filter: CompressedBloomFilter,
        fingerprint_cache: Optional[ASTFingerprintCache] = None
    ):
        """
        Initialize agent query interface.

        Args:
            hippocampus: KuzuDB graph connection
            bloom_filter: Bloom filter for membership testing
            fingerprint_cache: Optional AST fingerprint cache
        """
        self.hippocampus = hippocampus
        self.bloom_filter = bloom_filter
        self.fingerprint_cache = fingerprint_cache or ASTFingerprintCache()
        self.toon_encoder = TOONEncoder(compact=True)

    def query_artifact(
        self,
        artifact_id: str,
        include_dependencies: bool = True,
        max_depth: int = 2
    ) -> QueryResult:
        """
        Query an artifact and return TOON-formatted context.

        Main entry point for agent queries.

        Args:
            artifact_id: ID or path of artifact to query
            include_dependencies: Whether to include dependencies
            max_depth: Max depth of dependency traversal (default: 2)

        Returns:
            QueryResult with TOON-formatted context
        """
        start_time = time.time()

        # Step 1: Bloom filter check (<1ms)
        bloom_hit = self._check_bloom_filter(artifact_id)
        if not bloom_hit:
            # Artifact not in database
            return QueryResult(
                toon_format=f"# Artifact not found: {artifact_id}",
                files_parsed=0,
                tokens_estimated=0,
                duration_ms=(time.time() - start_time) * 1000,
                bloom_hit=False,
                dependencies_found=0
            )

        # Step 2: Get artifact from graph (<5ms)
        artifact_node = self.hippocampus.get_node(artifact_id)
        if not artifact_node:
            return QueryResult(
                toon_format=f"# Artifact node not found: {artifact_id}",
                files_parsed=0,
                tokens_estimated=0,
                duration_ms=(time.time() - start_time) * 1000,
                bloom_hit=True,
                dependencies_found=0
            )

        # Step 3: Get dependencies if requested (<10ms)
        dependencies = []
        if include_dependencies:
            dependencies = self._get_dependencies(artifact_id, max_depth)

        # Step 4: Parse artifacts and create AST summaries (<50ms per file)
        files_parsed = 0
        main_summary = None
        dependency_summaries = []

        # Parse main artifact
        main_summary = self._parse_artifact(artifact_node)
        files_parsed += 1

        # Parse dependencies
        for dep_id in dependencies:
            dep_node = self.hippocampus.get_node(dep_id)
            if dep_node:
                dep_summary = self._parse_artifact(dep_node)
                dependency_summaries.append(dep_summary)
                files_parsed += 1

        # Step 5: Export to TOON format (<5ms)
        if main_summary:
            toon_output = export_to_agent(
                artifact_id,
                main_summary,
                dependency_summaries
            )
        else:
            toon_output = f"# Error: Could not parse {artifact_id}"

        # Calculate statistics
        duration_ms = (time.time() - start_time) * 1000
        tokens_estimated = self.toon_encoder.estimate_tokens(toon_output)

        return QueryResult(
            toon_format=toon_output,
            files_parsed=files_parsed,
            tokens_estimated=tokens_estimated,
            duration_ms=duration_ms,
            bloom_hit=True,
            dependencies_found=len(dependencies)
        )

    def query_multiple_artifacts(
        self,
        artifact_ids: List[str],
        include_dependencies: bool = True
    ) -> Dict[str, QueryResult]:
        """
        Query multiple artifacts efficiently.

        Args:
            artifact_ids: List of artifact IDs to query
            include_dependencies: Whether to include dependencies

        Returns:
            Dictionary mapping artifact_id to QueryResult
        """
        results = {}

        for artifact_id in artifact_ids:
            results[artifact_id] = self.query_artifact(
                artifact_id,
                include_dependencies=include_dependencies
            )

        return results

    def _check_bloom_filter(self, artifact_id: str) -> bool:
        """
        Check if artifact exists in Bloom filter.

        Args:
            artifact_id: Artifact to check

        Returns:
            True if possibly in database
        """
        return self.bloom_filter.contains(artifact_id)

    def _get_dependencies(
        self,
        artifact_id: str,
        max_depth: int = 2
    ) -> List[str]:
        """
        Get dependencies via graph traversal.

        Args:
            artifact_id: Starting artifact
            max_depth: Max traversal depth

        Returns:
            List of dependency artifact IDs
        """
        # Cypher query for DEPENDS_ON edges
        query = """
            MATCH (a:Artifact)-[:DEPENDS_ON*1..{max_depth}]->(dep:Artifact)
            WHERE a.id = $artifact_id
            RETURN DISTINCT dep.id AS id
            LIMIT 50
        """.format(max_depth=max_depth)

        result = self.hippocampus.execute_cypher(
            query,
            {"artifact_id": artifact_id}
        )

        return [row["id"] for row in result if "id" in row]

    def _parse_artifact(self, artifact_node: Dict) -> Optional[ASTSummary]:
        """
        Parse artifact node into AST summary.

        This would typically:
        1. Get file path from node
        2. Read file from filesystem
        3. Parse with Tree-sitter
        4. Extract symbols and dependencies
        5. Create ASTSummary

        For now, returns a placeholder.

        Args:
            artifact_node: Artifact node from KuzuDB

        Returns:
            ASTSummary or None
        """
        # TODO: Implement full parsing pipeline
        # This requires:
        # 1. Reading file from disk
        # 2. Getting appropriate Tree-sitter parser
        # 3. Extracting symbols and dependencies
        # 4. Creating ASTSummary

        # Placeholder implementation
        return ASTSummary(
            file_path=artifact_node.get("path", "unknown"),
            language=artifact_node.get("language", "unknown"),
            functions=[],
            classes=[],
            imports=[],
            exports=[]
        )

    def explain_artifact(self, artifact_id: str) -> str:
        """
        Generate natural language explanation of artifact.

        Convenience method for agent queries like:
        "Explain auth.py and its dependencies"

        Args:
            artifact_id: Artifact to explain

        Returns:
            Natural language explanation
        """
        result = self.query_artifact(artifact_id, include_dependencies=True)

        # Add summary header
        explanation = f"""# Analysis of {artifact_id}

Files analyzed: {result.files_parsed}
Dependencies found: {result.dependencies_found}
Estimated tokens: {result.tokens_estimated:,}
Query time: {result.duration_ms:.1f}ms

---

{result.toon_format}
"""
        return explanation

    def find_similar_artifacts(
        self,
        artifact_id: str,
        limit: int = 10
    ) -> List[str]:
        """
        Find artifacts with similar AST structure.

        Uses fingerprint exact matching (no approximations needed).

        Args:
            artifact_id: Reference artifact
            limit: Max number of results

        Returns:
            List of similar artifact IDs
        """
        # Get fingerprint of reference artifact
        artifact_node = self.hippocampus.get_node(artifact_id)
        if not artifact_node:
            return []

        ref_fingerprint = artifact_node.get("ast_fingerprint")
        if not ref_fingerprint:
            return []

        # Query for matching fingerprints
        query = """
            MATCH (a:Artifact)
            WHERE a.ast_fingerprint = $fingerprint
               AND a.id != $artifact_id
            RETURN a.id AS id
            LIMIT $limit
        """

        result = self.hippocampus.execute_cypher(
            query,
            {
                "fingerprint": ref_fingerprint,
                "artifact_id": artifact_id,
                "limit": limit
            }
        )

        return [row["id"] for row in result if "id" in row]

    def get_statistics(self) -> Dict:
        """
        Get interface statistics.

        Returns:
            Dictionary with stats
        """
        bloom_stats = self.bloom_filter.get_stats()
        cache_stats = {
            'cache_size': self.fingerprint_cache.size(),
        }

        # Get graph stats
        node_count = self.hippocampus.execute_cypher(
            "MATCH (n:Artifact) RETURN count(n) AS count",
            {}
        )
        edge_count = self.hippocampus.execute_cypher(
            "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS count",
            {}
        )

        return {
            'bloom_filter': bloom_stats,
            'fingerprint_cache': cache_stats,
            'graph': {
                'artifact_count': int(node_count[0]["count"]) if node_count else 0,
                'dependency_edge_count': int(edge_count[0]["count"]) if edge_count else 0,
            }
        }


# Convenience function for quick queries

def query_for_agent(
    hippocampus: Hippocampus,
    bloom_filter: CompressedBloomFilter,
    artifact_id: str
) -> str:
    """
    Quick query for AI agent.

    Args:
        hippocampus: KuzuDB connection
        bloom_filter: Bloom filter
        artifact_id: Artifact to query

    Returns:
        TOON-formatted context
    """
    interface = AgentQueryInterface(hippocampus, bloom_filter)
    result = interface.query_artifact(artifact_id)
    return result.toon_format
