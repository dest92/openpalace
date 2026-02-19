"""Hebbian learning and synaptic plasticity."""

from typing import Set
from palace.core.hippocampus import Hippocampus


class PlasticityEngine:
    """
    Implements synaptic plasticity: learning and forgetting.
    "Neurons that fire together, wire together."
    """

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize plasticity engine.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus

    def reinforce_coactivation(self, node_set: Set[str], learning_rate: float = 0.1) -> None:
        """
        Strengthen connections between all pairs in node_set.

        Args:
            node_set: Set of node IDs that were co-activated
            learning_rate: How much to strengthen connections
        """
        node_list = sorted(list(node_set))  # Sort for deterministic order

        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                node_a, node_b = node_list[i], node_list[j]

                # Get current weight
                current_weight = self.get_edge_weight(node_a, node_b, "RELATED_TO")

                # Calculate new weight
                new_weight = min(1.0, current_weight + learning_rate)

                # Update or create edge
                self._set_edge_weight(node_a, node_b, "RELATED_TO", new_weight)

    def punish_mistake(self, node_a: str, node_b: str, penalty: float = 0.2) -> None:
        """
        Weaken connection between two nodes after bad outcome.

        Args:
            node_a: First node ID
            node_b: Second node ID
            penalty: How much to weaken the connection
        """
        current_weight = self.get_edge_weight(node_a, node_b, "RELATED_TO")

        if current_weight > 0:
            new_weight = max(0.0, current_weight - penalty)

            if new_weight < 0.1:
                # Remove weak edge
                self._remove_edge(node_a, node_b, "RELATED_TO")
            else:
                self._set_edge_weight(node_a, node_b, "RELATED_TO", new_weight)

    def get_edge_weight(self, src: str, dst: str, edge_type: str) -> float:
        """
        Get current edge weight or return 0.0 if no edge.

        Args:
            src: Source node ID
            dst: Destination node ID
            edge_type: Type of edge

        Returns:
            Edge weight or 0.0
        """
        # Can't use TYPE() in KuzuDB, so query specific edge type
        query = f"""
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            RETURN r.weight AS weight
        """
        result = self.hippocampus.execute_cypher(query, {"src": src, "dst": dst})

        if result:
            weight = result[0].get("weight")
            return float(weight) if weight is not None else 0.0
        return 0.0

    def _set_edge_weight(self, src: str, dst: str, edge_type: str, weight: float) -> None:
        """Create or update edge with weight."""
        # First check if edge exists
        query_check = f"""
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            RETURN r
        """
        existing = self.hippocampus.execute_cypher(query_check, {"src": src, "dst": dst})

        if existing:
            # Update existing edge
            query_update = f"""
                MATCH (a)-[r:{edge_type}]->(b)
                WHERE a.id = $src AND b.id = $dst
                SET r.weight = $weight
            """
            self.hippocampus.execute_cypher(
                query_update, {"src": src, "dst": dst, "weight": weight}
            )
        else:
            # Create new edge
            self.hippocampus.create_edge(src, dst, edge_type, {"weight": weight})

    def _remove_edge(self, src: str, dst: str, edge_type: str) -> None:
        """Remove edge between nodes."""
        query = f"""
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            DELETE r
        """
        self.hippocampus.execute_cypher(query, {"src": src, "dst": dst})
