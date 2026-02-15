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

def test_create_concept_node(temp_palace_dir):
    """Test creating a Concept node."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        node_id = hippo.create_node(
            "Concept",
            {
                "id": "concept-1",
                "name": "Authentication",
                "embedding_id": "emb-1",
                "layer": "abstraction",
                "stability": 0.8
            }
        )
        assert node_id == "concept-1"

def test_create_and_get_node(temp_palace_dir):
    """Test creating and retrieving a node."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        hippo.create_node(
            "Artifact",
            {
                "id": "artifact-1",
                "path": "test.py",
                "content_hash": "abc123",
                "language": "python",
                "ast_fingerprint": "fp-1"
            }
        )
        node = hippo.get_node("artifact-1")
        assert node is not None
        assert node["path"] == "test.py"
        assert node["language"] == "python"

def test_create_edge(temp_palace_dir):
    """Test creating an edge between nodes."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        # Create two nodes
        hippo.create_node(
            "Artifact",
            {"id": "artifact-1", "path": "a.py", "content_hash": "1", "language": "py", "ast_fingerprint": "1"}
        )
        hippo.create_node(
            "Concept",
            {"id": "concept-1", "name": "Test", "embedding_id": "1", "layer": "abstraction", "stability": 0.5}
        )
        # Create edge
        hippo.create_edge(
            "artifact-1",
            "concept-1",
            "EVOKES",
            {"weight": 0.9, "last_activated": None}
        )

def test_execute_cypher(temp_palace_dir):
    """Test executing raw Cypher query."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        results = hippo.execute_cypher(
            "MATCH (c:Concept) RETURN c LIMIT 1",
            {}
        )
        assert isinstance(results, list)
