"""Tests for Hebbian plasticity engine."""

import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.plasticity import PlasticityEngine


@pytest.fixture
def plastic_brain(tmp_path):
    """Create a brain for plasticity testing."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create test nodes
        hippo.create_node("Concept", {
            "id": "concept1",
            "name": "Auth",
            "embedding_id": "1",
            "layer": "abstraction",
            "stability": 0.5
        })

        hippo.create_node("Concept", {
            "id": "concept2",
            "name": "JWT",
            "embedding_id": "2",
            "layer": "implementation",
            "stability": 0.5
        })

        # Create initial edge
        hippo.create_edge("concept1", "concept2", "RELATED_TO", {"weight": 0.5})

    return palace_dir


def test_reinforce_coactivation_existing_edge(plastic_brain):
    """Test strengthening existing connection."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        # Get initial weight
        initial_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert initial_weight == 0.5

        # Reinforce
        engine.reinforce_coactivation({"concept1", "concept2"}, learning_rate=0.1)

        # Check weight increased
        new_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert new_weight == pytest.approx(0.6, abs=0.01)


def test_reinforce_coactivation_no_edge(plastic_brain):
    """Test creating new edge when none exists."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        # Add unconnected node
        hippo.create_node("Concept", {
            "id": "concept3",
            "name": "Security",
            "embedding_id": "3",
            "layer": "abstraction",
            "stability": 0.5
        })

        # Check that edge doesn't exist
        initial_weight = engine.get_edge_weight("concept1", "concept3", "RELATED_TO")
        assert initial_weight == 0.0, f"Edge should not exist initially, but weight is {initial_weight}"

        # Reinforce (no edge exists)
        engine.reinforce_coactivation({"concept1", "concept3"}, learning_rate=0.2)

        # Edge should be created
        weight = engine.get_edge_weight("concept1", "concept3", "RELATED_TO")
        assert weight == 0.2, f"Expected weight 0.2, got {weight}"


def test_weight_capping(plastic_brain):
    """Test that weights are capped at 1.0."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        # Reinforce with high learning rate
        engine.reinforce_coactivation({"concept1", "concept2"}, learning_rate=1.0)

        # Should be capped at 1.0
        weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert weight == 1.0


def test_punish_mistake(plastic_brain):
    """Test weakening connection after mistake."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        initial_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")

        # Punish
        engine.punish_mistake("concept1", "concept2", penalty=0.2)

        new_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert new_weight == pytest.approx(initial_weight - 0.2, abs=0.01)
