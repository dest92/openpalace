import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.shared.exceptions import DatabaseError

@pytest.fixture
def temp_palace_dir(tmp_path):
    """Create temporary .palace directory."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()
    return palace_dir

def test_hippocampus_initialization(temp_palace_dir):
    """Test that Hippocampus can be initialized."""
    hippo = Hippocampus(temp_palace_dir)
    assert hippo.palace_dir == temp_palace_dir
    assert hippo.is_connected()
    hippo.close()

def test_hippocampus_context_manager(temp_palace_dir):
    """Test that Hippocampus works as context manager."""
    with Hippocampus(temp_palace_dir) as hippo:
        assert hippo.is_connected()
    # Should be closed after context

def test_hippocampus_schema_creation(temp_palace_dir):
    """Test that schema is created on initialization."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        # Verify node types exist
        node_types = hippo.get_node_types()
        assert "Concept" in node_types
        assert "Artifact" in node_types
        assert "Invariant" in node_types
        assert "Decision" in node_types
        assert "Anchor" in node_types
