"""Sleep cycle for consolidation and forgetting."""

from dataclasses import dataclass
from typing import List
import time
import math
from datetime import datetime, timedelta
from palace.core.hippocampus import Hippocampus


@dataclass
class SleepReport:
    """Report from a sleep cycle."""

    nodes_count: int
    edges_count: int
    edges_decayed: int
    edges_pruned: int
    communities_detected: int
    total_duration_ms: float


class SleepEngine:
    """
    Implements REM-like sleep cycle: consolidation, pruning, forgetting.
    Runs asynchronously or on-demand.
    """

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize sleep engine.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus

    def sleep_cycle(
        self,
        lambda_decay: float = 0.05,
        prune_threshold: float = 0.1,
        detect_communities: bool = True,
    ) -> SleepReport:
        """
        Execute full sleep cycle.

        Args:
            lambda_decay: Decay rate constant
            prune_threshold: Minimum weight to keep edge
            detect_communities: Whether to run community detection

        Returns:
            SleepReport with statistics
        """
        start_time = time.time()

        # Get initial counts
        nodes_count = self._count_nodes()
        edges_count = self._count_edges()

        # Decay edge weights
        edges_decayed = self._decay_edge_weights(lambda_decay)

        # Prune weak edges
        edges_pruned = self._prune_weak_edges(prune_threshold)

        # Detect communities
        communities_detected = 0
        if detect_communities:
            communities_detected = self._detect_communities()

        duration_ms = (time.time() - start_time) * 1000

        return SleepReport(
            nodes_count=nodes_count,
            edges_count=edges_count,
            edges_decayed=edges_decayed,
            edges_pruned=edges_pruned,
            communities_detected=communities_detected,
            total_duration_ms=duration_ms,
        )

    def _count_nodes(self) -> int:
        """Count total nodes in graph."""
        result = self.hippocampus.execute_cypher("MATCH (n) RETURN count(n) AS count", {})
        return int(result[0]["count"]) if result else 0

    def _count_edges(self) -> int:
        """Count total edges in graph."""
        result = self.hippocampus.execute_cypher("MATCH ()-[r]->() RETURN count(r) AS count", {})
        return int(result[0]["count"]) if result else 0

    def _decay_edge_weights(self, lambda_decay: float) -> int:
        """
        Apply exponential decay: w = w * exp(-λ * Δt)

        Optimized: Uses single Cypher query with batch update.

        Returns:
            Number of edges decayed
        """
        # Single batch query to decay all edges at once
        query = """
            MATCH (a)-[r:RELATED_TO]->(b)
            WHERE r.weight IS NOT NULL AND r.weight > 0
            SET r.weight = r.weight * (1.0 - $decay_rate)
            RETURN count(r) AS decayed
        """

        result = self.hippocampus.execute_cypher(query, {"decay_rate": lambda_decay})
        return int(result[0]["decayed"]) if result else 0

    def _prune_weak_edges(self, threshold: float) -> int:
        """
        Remove edges with weight < threshold.

        Optimized: Uses single Cypher query with batch delete.

        Returns:
            Number of edges pruned
        """
        # Single batch query to prune all weak edges at once
        query = """
            MATCH (a)-[r:RELATED_TO]->(b)
            WHERE r.weight IS NOT NULL AND r.weight < $threshold
            DELETE r
            RETURN count(r) AS pruned
        """

        result = self.hippocampus.execute_cypher(query, {"threshold": threshold})
        return int(result[0]["pruned"]) if result else 0

    def _detect_communities(self) -> int:
        """
        Run Louvain algorithm on concept graph.
        Create Anchor nodes for spatial reference.

        Returns:
            Number of communities detected
        """
        # Placeholder - would use networkx or similar for Louvain
        # For now, return 0 as placeholder
        return 0

    def _update_edge_weight(self, src: str, dst: str, edge_type: str, weight: float) -> None:
        """Update edge weight."""
        query = f"""
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            SET r.weight = $weight
        """
        self.hippocampus.execute_cypher(query, {"src": src, "dst": dst, "weight": weight})

    def _remove_edge(self, src: str, dst: str, edge_type: str) -> None:
        """Remove edge between nodes."""
        query = f"""
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            DELETE r
        """
        self.hippocampus.execute_cypher(query, {"src": src, "dst": dst})
