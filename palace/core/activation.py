"""Spreading activation algorithm for cognitive navigation."""

from typing import Dict, List, Set
from collections import deque
import math
from palace.core.hippocampus import Hippocampus


class ActivationEngine:
    """
    Implements spreading activation algorithm for cognitive navigation.
    Simulates neural firing patterns across the graph.
    """

    # Edge type transmission factors
    TRANSMISSION_FACTORS = {
        "CONSTRAINS": 1.0,
        "EVOKES": 0.9,
        "DEPENDS_ON": 0.7,
        "PRECEDES": 0.6,
        "RELATED_TO": 0.5
    }

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize activation engine.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus

    def spread(
        self,
        seed_node_id: str,
        max_depth: int = 3,
        energy_threshold: float = 0.15,
        decay_factor: float = 0.8
    ) -> Dict[str, float]:
        """
        Execute spreading activation from a seed node.

        Args:
            seed_node_id: Starting node ID
            max_depth: Maximum hop distance
            energy_threshold: Minimum energy to include in results
            decay_factor: Energy decay per hop

        Returns:
            Dict mapping node_id to activation energy, sorted by energy
        """
        # BFS queue: (node_id, current_energy, current_depth)
        queue = deque([(seed_node_id, 1.0, 0)])
        visited: Set[str] = set()
        energies: Dict[str, float] = {}

        while queue:
            node_id, energy, depth = queue.popleft()

            if node_id in visited:
                continue
            visited.add(node_id)

            # Store energy if above threshold
            if energy >= energy_threshold:
                energies[node_id] = energy

            # Stop if max depth reached
            if depth >= max_depth:
                continue

            # Get outgoing edges
            edges = self._get_outgoing_edges(node_id)

            for edge in edges:
                neighbor_id = edge["dst"]
                if neighbor_id in visited:
                    continue

                # Calculate transmitted energy
                transmission_factor = self._get_edge_transmission_factor(edge["type"])
                transmitted_energy = (
                    energy *
                    edge.get("weight", 1.0) *
                    decay_factor *
                    transmission_factor
                )

                if transmitted_energy >= energy_threshold:
                    queue.append((neighbor_id, transmitted_energy, depth + 1))

        # Update edge activation timestamps
        self._update_activation_timestamps(visited)

        return dict(sorted(energies.items(), key=lambda x: x[1], reverse=True))

    def _get_outgoing_edges(self, node_id: str) -> List[Dict]:
        """Get all outgoing edges from a node."""
        # KuzuDB doesn't support type() function, so we check each edge type
        edge_types = ["EVOKES", "RELATED_TO", "DEPENDS_ON", "CONSTRAINS", "PRECEDES"]
        all_edges = []

        for edge_type in edge_types:
            # Try to get weight if it exists, otherwise use default 1.0
            query = f"""
                MATCH (n)-[r:{edge_type}]->(m)
                WHERE n.id = $node_id
                RETURN m.id AS dst, '{edge_type}' AS type
            """
            edges = self.hippocampus.execute_cypher(query, {"node_id": node_id})
            # Add default weight if not present
            for edge in edges:
                if "weight" not in edge:
                    edge["weight"] = 1.0
                all_edges.append(edge)

        return all_edges

    def _get_edge_transmission_factor(self, edge_type: str) -> float:
        """Get energy transmission factor for edge type."""
        return self.TRANSMISSION_FACTORS.get(edge_type, 0.5)

    def _update_activation_timestamps(self, visited_nodes: Set[str]) -> None:
        """Update last_activated timestamp for EVOKES edges."""
        # This would be implemented with Cypher UPDATE
        # For now, placeholder
        pass
