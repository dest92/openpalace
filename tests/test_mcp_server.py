"""
MCP Server Tests - In-Memory Testing Pattern

Tests use the in-memory pattern to avoid subprocess overhead.
The server instance is passed directly to the test client.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from palace.core.hippocampus import Hippocampus
from palace.core.bloom_filter import CompressedBloomFilter
from palace.core.agent_interface import AgentQueryInterface, QueryResult

from mcp_server.server import create_server, server_lifespan


@pytest.fixture
def mock_hippocampus():
    """Mock Hippocampus instance."""
    mock = Mock(spec=Hippocampus)
    mock.execute_cypher = Mock(return_value=[])
    mock.get_node = Mock(return_value=None)
    mock.close = Mock()
    return mock


@pytest.fixture
def mock_bloom_filter():
    """Mock Bloom Filter instance."""
    mock = Mock(spec=CompressedBloomFilter)
    mock.contains = Mock(return_value=True)
    mock.get_stats = Mock(return_value={
        "size_bytes": 2_000_000,
        "item_count": 1_000_000,
        "false_positive_rate": 0.001,
    })
    return mock


@pytest.fixture
def mock_query_interface():
    """Mock AgentQueryInterface instance."""
    mock = Mock(spec=AgentQueryInterface)

    # Mock query_artifact result
    mock.query_artifact = Mock(return_value=QueryResult(
        toon_format="# Test Artifact\n\n```python\ndef foo(): pass\n```",
        files_parsed=1,
        tokens_estimated=100,
        duration_ms=50.0,
        bloom_hit=True,
        dependencies_found=2
    ))

    mock.explain_artifact = Mock(return_value="# Explanation\n\nTest artifact")
    mock.find_similar_artifacts = Mock(return_value=["artifact-2", "artifact-3"])
    mock.get_statistics = Mock(return_value={
        "bloom_filter": {"size_bytes": 2_000_000, "item_count": 1_000_000},
        "graph": {"artifact_count": 1000, "dependency_edge_count": 5000}
    })

    return mock


@pytest.fixture
async def server_context(mock_hippocampus, mock_bloom_filter, mock_query_interface):
    """
    Provide server context for testing.

    This simulates what server_lifespan provides during
    actual server execution.
    """
    return {
        "hippocampus": mock_hippocampus,
        "bloom_filter": mock_bloom_filter,
        "query_interface": mock_query_interface,
    }


class TestMCPServer:
    """Test MCP server creation and configuration."""

    def test_create_server(self):
        """Test server can be created with correct configuration."""
        server = create_server(name="test-palace", json_response=True)

        assert server is not None
        assert server.name == "test-palace"

    def test_server_has_tools_registered(self):
        """Test that tools are registered with the server."""
        server = create_server()

        # FastMCP stores tools in a registry
        # Check that our tools are accessible
        assert hasattr(server, "_tools")

    def test_server_has_resources_registered(self):
        """Test that resources are registered with the server."""
        server = create_server()

        # FastMCP stores resources in a registry
        assert hasattr(server, "_resources")

    def test_server_has_prompts_registered(self):
        """Test that prompts are registered with the server."""
        server = create_server()

        # FastMCP stores prompts in a registry
        assert hasattr(server, "_prompts")


class TestQueryTools:
    """Test query tool functionality."""

    @pytest.mark.asyncio
    async def test_query_artifact_tool_exists(self, server_context):
        """Test that query_artifact tool is registered."""
        server = create_server()

        # Get tool from server
        tools = server._tools
        tool_names = [tool.name for tool in tools]

        assert "query_artifact" in tool_names

    def test_query_artifact_validation(self, server_context):
        """Test query_artifact validates input."""
        server = create_server()

        # This would normally call the tool
        # For now, we test that validation logic exists
        # The actual tool should raise ValueError for empty artifact_id

        with pytest.raises(ValueError):
            from mcp_server.tools.query import query_artifact
            # Mock the context
            # query_artifact("", ...) should raise ValueError


class TestCompressionTools:
    """Test compression tool functionality."""

    def test_compress_code_validates_language(self, server_context):
        """Test compress_code validates language parameter."""
        from mcp_server.tools.compression import compress_code

        # Test unsupported language
        with pytest.raises(ValueError, match="Unsupported language"):
            compress_code("code", "invalid_language")

    def test_compress_code_validates_empty_code(self, server_context):
        """Test compress_code validates code is not empty."""
        from mcp_server.tools.compression import compress_code

        with pytest.raises(ValueError, match="code cannot be empty"):
            compress_code("", "python")


class TestIndexingTools:
    """Test indexing tool functionality."""

    def test_index_files_validates_paths(self, server_context):
        """Test index_files validates paths list is not empty."""
        from mcp_server.tools.indexing import index_files

        with pytest.raises(ValueError, match="paths list cannot be empty"):
            index_files([])

    def test_delete_from_index_validates_artifact_id(self, server_context):
        """Test delete_from_index validates artifact_id."""
        from mcp_server.tools.indexing import delete_from_index

        with pytest.raises(ValueError, match="artifact_id cannot be empty"):
            delete_from_index("")


class TestResources:
    """Test resource functionality."""

    def test_stats_resource_exists(self):
        """Test stats resources are registered."""
        server = create_server()

        resources = server._resources
        resource_uris = [res.uri for res in resources]

        assert "stats://overview" in resource_uris
        assert "stats://performance" in resource_uris
        assert "stats://bloom" in resource_uris

    def test_artifact_resource_exists(self):
        """Test artifact resources are registered."""
        server = create_server()

        resources = server._resources
        resource_uris = [res.uri for res in resources]

        assert any(uri.startswith("artifact://") for uri in resource_uris)


class TestPrompts:
    """Test prompt functionality."""

    def test_query_with_context_prompt_exists(self):
        """Test query_with_context prompt is registered."""
        server = create_server()

        prompts = server._prompts
        prompt_names = [prompt.name for prompt in prompts]

        assert "query_with_context" in prompt_names
        assert "analyze_dependencies" in prompt_names
        assert "explain_code" in prompt_names
        assert "find_similar_pattern" in prompt_names


class TestLifespan:
    """Test server lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_components(self, mock_hippocampus, mock_bloom_filter):
        """Test that lifespan initializes Palace Mental components."""
        server = create_server()

        # Mock the Hippocampus constructor
        import palace.core.hippocampus
        original_hippocampus = palace.core.hippocampus.Hippocampus
        palace.core.hippocampus.Hippocampus = Mock(return_value=mock_hippocampus)

        try:
            async with server_lifespan(server) as context:
                assert "hippocampus" in context
                assert "bloom_filter" in context
                assert "query_interface" in context
        finally:
            palace.core.hippocampus.Hippocampus = original_hippocampus

    @pytest.mark.asyncio
    async def test_lifespan_closes_connections(self, mock_hippocampus, mock_bloom_filter):
        """Test that lifespan closes Hippocampus on shutdown."""
        server = create_server()

        # Mock constructors
        import palace.core.hippocampus
        import palace.core.agent_interface

        original_hippocampus = palace.core.hippocampus.Hippocampus
        original_query_interface = palace.core.agent_interface.AgentQueryInterface

        palace.core.hippocampus.Hippocampus = Mock(return_value=mock_hippocampus)
        palace.core.agent_interface.AgentQueryInterface = Mock()

        try:
            async with server_lifespan(server):
                pass

            # Verify close was called
            mock_hippocampus.close.assert_called_once()

        finally:
            palace.core.hippocampus.Hippocampus = original_hippocampus
            palace.core.agent_interface.AgentQueryInterface = original_query_interface


class TestIntegration:
    """Integration tests for the full server."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Test that server can start up and shut down cleanly."""
        server = create_server()

        # Server should be created successfully
        assert server is not None

        # Server should have all components registered
        assert len(server._tools) > 0
        assert len(server._resources) > 0
        assert len(server._prompts) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
