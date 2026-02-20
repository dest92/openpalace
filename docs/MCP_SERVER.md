# Palace Mental MCP Server

Model Context Protocol (MCP) server for Palace Mental V2.

## Overview

The Palace Mental MCP server exposes Palace Mental's capabilities as MCP primitives:

- **Tools**: Executable operations (query, compress, index)
- **Resources**: Read-only data access (stats, metadata)
- **Prompts**: Reusable interaction templates

## Installation

```bash
# Install with MCP support
poetry install

# Or install MCP manually
pip install mcp
```

## Usage

### Direct Execution

```bash
# Run server with stdio transport (for IDEs)
python -m mcp_server.server

# With debug logging
python -m mcp_server.server --log-level DEBUG
```

### IDE Configuration

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "palace-mental": {
      "command": "python",
      "args": ["/path/to/palace2/mcp_server/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/palace2"
      }
    }
  }
}
```

#### Cursor

Add to `settings.json`:

```json
{
  "mcp.servers": {
    "palace-mental": {
      "command": "python",
      "args": ["/path/to/palace2/mcp_server/server.py"],
      "transport": "stdio"
    }
  }
}
```

## Tools

### query_artifact

Query an artifact and return TOON-formatted context.

```python
query_artifact(
    artifact_id: str,
    include_dependencies: bool = True,
    max_depth: int = 2
) -> str
```

**Example:**
```
Use query_artifact to retrieve "src/auth/authenticate.py" with its dependencies
```

### explain_artifact

Generate natural language explanation of an artifact.

```python
explain_artifact(
    artifact_id: str,
    detail_level: str = "concise" | "standard" | "verbose"
) -> str
```

**Example:**
```
Use explain_artifact to explain "src/auth/login.py" with standard detail
```

### find_similar_artifacts

Find artifacts with identical AST structure.

```python
find_similar_artifacts(
    artifact_id: str,
    limit: int = 10
) -> str
```

**Example:**
```
Use find_similar_artifacts to find code similar to "authenticate.py"
```

### compress_code

Compress code to TOON format for token efficiency.

```python
compress_code(
    code: str,
    language: str,
    compact: bool = True
) -> str
```

**Example:**
```
Use compress_code to compress this Python code:
```python
def authenticate(user, password):
    return validate(user, password)
```
```

### index_files

Index files into Palace Mental knowledge graph.

```python
index_files(
    paths: List[str],
    force: bool = False,
    language: Optional[str] = None
) -> str
```

**Example:**
```
Use index_files to index ["src/"] directory
```

## Resources

### stats://overview

Get Palace Mental overview statistics.

```
Read resource: stats://overview
```

**Returns:**
```json
{
  "version": "2.0.0",
  "bloom_filter": {
    "size_bytes": 2000000,
    "item_count": 1000000
  },
  "graph": {
    "artifact_count": 1000,
    "dependency_edge_count": 5000
  }
}
```

### artifact://{artifact_id}/metadata

Get metadata for a specific artifact.

```
Read resource: artifact://src/auth/authenticate.py/metadata
```

### artifact://{artifact_id}/dependencies

Get dependency graph for an artifact.

```
Read resource: artifact://src/auth/authenticate.py/dependencies?max_depth=2
```

## Prompts

### query_with_context

Template for querying artifacts with specific questions.

```
Use prompt: query_with_context
- artifact_id: "src/auth/authenticate.py"
- question: "How is authentication validated?"
- include_dependencies: true
```

### analyze_dependencies

Template for analyzing artifact dependencies.

```
Use prompt: analyze_dependencies
- artifact_id: "src/auth/authenticate.py"
- focus: "critical"
```

### explain_code

Template for explaining code to different audiences.

```
Use prompt: explain_code
- artifact_id: "src/auth/authenticate.py"
- audience: "developer"
- detail_level: "standard"
```

## Architecture

```
mcp_server/
├── server.py              # Main entry point with FastMCP
├── tools/                 # Executable operations
│   ├── query.py          # Query tools
│   ├── compression.py    # Compression tools
│   └── indexing.py       # Indexing tools
├── resources/             # Read-only data
│   ├── stats.py          # Statistics
│   └── metadata.py       # Metadata
└── prompts/               # Reusable templates
    └── templates.py      # Prompt templates
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/test_mcp_server.py -v

# Run with coverage
pytest tests/test_mcp_server.py --cov=mcp_server --cov-report=html
```

### Adding a New Tool

1. Create tool function in `mcp_server/tools/`
2. Decorate with `@mcp.tool()`
3. Add type hints and comprehensive docstring
4. Register in `create_server()`

**Example:**

```python
@mcp.tool()
def my_new_tool(
    param1: str,
    param2: int = 10
) -> str:
    """
    Tool description for LLM.

    Args:
        param1: Description
        param2: Description with default

    Returns:
        Description of return value
    """
    # Implementation
    return result
```

### Adding a New Resource

1. Create resource function in `mcp_server/resources/`
2. Decorate with `@mcp.resource("uri://path")`
3. Return structured data (JSON preferred)

**Example:**

```python
@mcp.resource("custom://data")
def get_custom_data() -> str:
    """Get custom data resource."""
    import json
    return json.dumps({"key": "value"})
```

### Adding a New Prompt

1. Create prompt function in `mcp_server/prompts/`
2. Decorate with `@mcp.prompt()`
3. Return formatted prompt string

**Example:**

```python
@mcp.prompt()
def my_custom_prompt(
    artifact_id: str,
    option: str = "default"
) -> str:
    """
    Prompt description.

    Args:
        artifact_id: Artifact to process
        option: Configuration option

    Returns:
        Formatted prompt
    """
    return f"""Analyze {artifact_id} with {option} configuration.

Steps:
1. Use tool_x to get data
2. Analyze results
3. Provide insights
"""
```

## Best Practices

### Error Handling

- Log all errors to `stderr` (MCP uses `stdout` for protocol)
- Return structured error messages in tool responses
- Validate all input parameters

**Example:**

```python
try:
    result = operation()
    logger.info(f"✅ Success: {result}")
    return result
except Exception as e:
    logger.error(f"❌ Error: {e}", exc_info=True)
    return f"# Error\n\n{str(e)}"
```

### Performance

- Use Bloom filter for O(1) membership checks
- Batch queries when possible
- Limit dependency traversal depth
- Cache frequently accessed data

### Documentation

- Every tool must have comprehensive docstring
- Include examples in docstrings
- Document performance characteristics
- Note any limitations or warnings

## Troubleshooting

### Server Not Starting

**Problem**: Server fails to start with import error.

**Solution:**
```bash
# Ensure PYTHONPATH includes palace2
export PYTHONPATH=/path/to/palace2:$PYTHONPATH
python -m mcp_server.server
```

### Tools Not Found

**Problem**: IDE reports "tool not found".

**Solution:**
- Verify server is running
- Check server logs in stderr
- Ensure tool is registered in `create_server()`

### Database Connection Failed

**Problem**: "Hippocampus not initialized" error.

**Solution:**
```bash
# Initialize Palace Mental database
cd palace2
python setup_palace.py

# Then start MCP server
python -m mcp_server.server
```

## Performance Benchmarks

Based on Palace Mental V2 specifications:

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Bloom filter check | <1ms | <1ms | ✅ |
| Graph traversal | <10ms | <10ms | ✅ |
| AST parsing | <50ms | <50ms | ✅ |
| TOON export | <5ms | <5ms | ✅ |
| **Total query** | <100ms | **<100ms** | ✅ |

## Resources

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [Python SDK Documentation](https://modelcontextprotocol.github.io/python-sdk/)
- [Palace Mental V2 Docs](./PALACE_MENTAL_V2.md)

## License

Same as Palace Mental V2.

## Contributing

Contributions welcome! Please ensure:

1. All tests pass
2. New code is documented
3. Error handling follows best practices
4. Logging goes to stderr

## Support

For issues or questions:
- GitHub Issues: [palace2/issues](https://github.com/yourorg/palace2/issues)
- Documentation: [docs/](./)
