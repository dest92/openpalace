"""Tests for spreading activation engine."""

import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.activation import ActivationEngine


@pytest.fixture
def populated_brain(tmp_path):
    """Create a brain with test data."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create test graph:
        # artifact1 -> concept1 (weight 0.9)
        # artifact1 -> concept2 (weight 0.5)
        # concept1 -> concept3 (weight 0.8)

        hippo.create_node("Artifact", {
            "id": "artifact1",
            "path": "test.py",
            "content_hash": "1",
            "language": "python",
            "ast_fingerprint": "1"
        })

        hippo.create_node("Concept", {
            "id": "concept1",
            "name": "Auth",
            "embedding_id": "1",
            "layer": "abstraction",
            "stability": 0.8
        })

        hippo.create_node("Concept", {
            "id": "concept2",
            "name": "Security",
            "embedding_id": "2",
            "layer": "abstraction",
            "stability": 0.7
        })

        hippo.create_node("Concept", {
            "id": "concept3",
            "name": "JWT",
            "embedding_id": "3",
            "layer": "implementation",
            "stability": 0.6
        })

        # Create edges
        hippo.create_edge("artifact1", "concept1", "EVOKES", {"weight": 0.9})
        hippo.create_edge("artifact1", "concept2", "EVOKES", {"weight": 0.5})
        hippo.create_edge("concept1", "concept3", "RELATED_TO", {"weight": 0.8})

    return palace_dir


def test_spreading_activation_basic(populated_brain):
    """Test basic spreading activation."""
    with Hippocampus(populated_brain) as hippo:
        engine = ActivationEngine(hippo)
        results = engine.spread("artifact1", max_depth=2, energy_threshold=0.2)

        # Should activate all nodes
        assert "artifact1" in results
        assert "concept1" in results
        assert "concept2" in results
        assert "concept3" in results

        # Energy should decrease with distance
        assert results["artifact1"] >= results["concept1"]
        assert results["concept1"] >= results["concept3"]


def test_spreading_activation_threshold(populated_brain):
    """Test that energy threshold filters nodes."""
    with Hippocampus(populated_brain) as hippo:
        engine = ActivationEngine(hippo)
        results = engine.spread("artifact1", max_depth=2, energy_threshold=0.6)

        # Only high-energy nodes
        for node_id, energy in results.items():
            assert energy >= 0.6


def test_spreading_activation_max_depth(populated_brain):
    """Test that max_depth limits propagation."""
    with Hippocampus(populated_brain) as hippo:
        engine = ActivationEngine(hippo)
        results = engine.spread("artifact1", max_depth=1, energy_threshold=0.1)

        # Should not reach concept3 (depth 2)
        assert "concept3" not in results or results["concept3"] < 0.1
