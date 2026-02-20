"""
MCP Prompts - Reusable Interaction Templates

Prompts provide pre-written templates that guide LLM interactions.
They encapsulate common query patterns and best practices.
"""

from mcp_server.prompts.templates import (
    register_prompt_templates,
    query_with_context_template,
    analyze_dependencies_template,
    explain_code_template,
    find_similar_pattern_template,
)

__all__ = [
    "register_prompt_templates",
    "query_with_context_template",
    "analyze_dependencies_template",
    "explain_code_template",
    "find_similar_pattern_template",
]
