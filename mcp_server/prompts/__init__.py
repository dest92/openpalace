"""
MCP Prompts - Reusable Interaction Templates

Prompts provide pre-written templates that guide LLM interactions.
They encapsulate common query patterns and best practices.

Note: Individual prompt functions are registered via register_prompt_templates()
and are not directly importable.
"""

from mcp_server.prompts.templates import register_prompt_templates

__all__ = [
    "register_prompt_templates",
]
