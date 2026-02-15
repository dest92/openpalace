"""Tests for sleep cycle engine."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.sleep import SleepEngine, SleepReport


@pytest.fixture
def sleepy_brain(tmp_path):
    """Create a brain with edges for sleep testing."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create nodes
        for i in range(5):
            hippo.create_node("Concept", {
                "id": f"concept{i}",
                "name": f"Concept{i}",
                "embedding_id": f"{i}",
                "layer": "abstraction",
                "stability": 0.5
            })

        # Create edges with different weights and timestamps
        # Use RELATED_TO for Concept-to-Concept edges
        hippo.create_edge("concept0", "concept1", "RELATED_TO", {
            "weight": 0.9  # Strong, should survive
        })

        hippo.create_edge("concept1", "concept2", "RELATED_TO", {
            "weight": 0.15  # Weak, might be pruned
        })

        hippo.create_edge("concept2", "concept3", "RELATED_TO", {
            "weight": 0.05  # Very weak, should be pruned
        })

    return palace_dir


def test_sleep_cycle_decay(sleepy_brain):
    """Test that edge weights decay over time."""
    with Hippocampus(sleepy_brain) as hippo:
        engine = SleepEngine(hippo)
        report = engine.sleep_cycle(lambda_decay=0.1)

        assert report.edges_decayed > 0
        assert report.total_duration_ms > 0


def test_sleep_cycle_pruning(sleepy_brain):
    """Test that weak edges are pruned."""
    with Hippocampus(sleepy_brain) as hippo:
        engine = SleepEngine(hippo)
        report = engine.sleep_cycle(prune_threshold=0.1)

        assert report.edges_pruned >= 1  # At least the 0.05 edge


def test_sleep_report(sleepy_brain):
    """Test that sleep cycle returns detailed report."""
    with Hippocampus(sleepy_brain) as hippo:
        engine = SleepEngine(hippo)
        report = engine.sleep_cycle()

        assert isinstance(report.nodes_count, int)
        assert isinstance(report.edges_count, int)
        assert isinstance(report.edges_decayed, int)
        assert isinstance(report.edges_pruned, int)
        assert isinstance(report.communities_detected, int)
