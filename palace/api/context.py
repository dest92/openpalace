"""Context provider for LLM code assistance."""

from typing import List, Dict, Optional
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.activation import ActivationEngine


class ContextProvider:
    """Provides contextual code information for LLM assistance."""

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize context provider.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus
        self.activation_engine = ActivationEngine(hippocampus)

    def get_context_for_file(
        self,
        file_path: str,
        max_depth: int = 3,
        energy_threshold: float = 0.3
    ) -> Dict:
        """
        Get contextual information for a file.

        Args:
            file_path: Path to the file
            max_depth: Maximum depth for spreading activation
            energy_threshold: Minimum energy threshold

        Returns:
            Dict with related files, concepts, and invariants
        """
        # Find artifact node
        result = self.hippocampus.execute_cypher(
            "MATCH (a:Artifact) WHERE a.path = $path RETURN a.id AS id",
            {"path": file_path}
        )

        if not result:
            return {"error": "File not found in knowledge graph"}

        artifact_id = result[0]["id"]

        # Spread activation to find related nodes
        activated = self.activation_engine.spread(
            artifact_id,
            max_depth=max_depth,
            energy_threshold=energy_threshold
        )

        # Get related artifacts
        related_artifacts = []
        related_concepts = []
        related_invariants = []

        for node_id, energy in activated.items():
            if node_id.startswith("artifact-"):
                node = self.hippocampus.get_node(node_id)
                if node:
                    related_artifacts.append({
                        "path": node.get("path"),
                        "energy": energy
                    })
            elif node_id.startswith("concept-"):
                node = self.hippocampus.get_node(node_id)
                if node:
                    related_concepts.append({
                        "name": node.get("name"),
                        "layer": node.get("layer"),
                        "energy": energy
                    })
            elif node_id.startswith("invariant-"):
                node = self.hippocampus.get_node(node_id)
                if node:
                    related_invariants.append({
                        "rule": node.get("rule"),
                        "severity": node.get("severity"),
                        "energy": energy
                    })

        return {
            "file_path": file_path,
            "related_artifacts": related_artifacts[:5],
            "related_concepts": related_concepts[:10],
            "related_invariants": related_invariants[:5],
            "total_activated": len(activated)
        }
