"""
Prompt Templates - Reusable LLM Interaction Patterns

Pre-defined prompts that encapsulate common interaction patterns
for querying and analyzing code with Palace Mental.
"""

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_prompt_templates(mcp: FastMCP) -> None:
    """
    Register prompt templates with the MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.prompt()
    def query_with_context(
        artifact_id: str,
        question: str,
        include_dependencies: bool = True
    ) -> str:
        """
        Template for querying artifacts with specific questions.

        Use this prompt when you need to ask specific questions about
        code in the context of its dependencies.

        Args:
            artifact_id: Artifact to query
            question: Specific question to answer
            include_dependencies: Include dependency context (default: True)

        Returns:
            Formatted prompt for the LLM

        Examples:
            >>> query_with_context("src/auth/authenticate.py", "How is authentication validated?")
            >>> query_with_context("artifact-123", "What errors can occur?", include_dependencies=True)
        """
        return f"""You are analyzing code from Palace Mental, a cognitive memory system for code engineering.

## Task
Answer this question about the code below: {question}

## Context
Use the `query_artifact` tool to retrieve the artifact and its dependencies:
- Artifact ID: `{artifact_id}`
- Include dependencies: {include_dependencies}

## Analysis Guidelines
1. First, retrieve the code context using `query_artifact`
2. Analyze the code structure and relationships
3. Answer the specific question concisely
4. Reference specific functions, classes, or patterns
5. Highlight any potential issues or improvements

## Response Format
Provide a clear, structured answer that:
- Directly addresses the question
- References specific code elements
- Explains the reasoning
- Suggests improvements if relevant
"""

    @mcp.prompt()
    def analyze_dependencies(
        artifact_id: str,
        focus: str = "all"
    ) -> str:
        """
        Template for analyzing artifact dependencies.

        Use this prompt to understand how an artifact relates to
        other parts of the codebase.

        Args:
            artifact_id: Artifact to analyze
            focus: Focus area - "all", "incoming", "outgoing", or "critical"

        Returns:
            Formatted prompt for dependency analysis

        Examples:
            >>> analyze_dependencies("src/auth/authenticate.py")
            >>> analyze_dependencies("artifact-123", focus="critical")
        """
        focus_descriptions = {
            "all": "all dependencies (both incoming and outgoing)",
            "incoming": "what depends on this artifact (dependents)",
            "outgoing": "what this artifact depends on (dependencies)",
            "critical": "critical dependencies and failure impact",
        }

        focus_desc = focus_descriptions.get(focus, focus_descriptions["all"])

        return f"""You are analyzing code dependencies in Palace Mental.

## Task
Analyze the dependency relationships for artifact: `{artifact_id}`

## Focus
Analyze {focus_desc}

## Analysis Steps
1. Use `query_artifact` to get the artifact and its dependencies
2. Use `get_dependency_graph` to visualize relationships
3. Analyze:
   - Dependency direction and depth
   - Critical path identification
   - Potential circular dependencies
   - Coupling and cohesion metrics
   - Failure impact assessment

## Response Format
Provide a structured analysis including:
1. **Dependency Summary**: Count and type of dependencies
2. **Critical Path**: Most important dependency chain
3. **Risk Assessment**: What happens if dependencies fail
4. **Recommendations**: Refactoring suggestions if applicable

## Tools to Use
- `query_artifact("{artifact_id}")` - Get code context
- Use resource: `artifact://{artifact_id}/dependencies` - Get dependency graph
"""

    @mcp.prompt()
    def explain_code(
        artifact_id: str,
        audience: str = "developer",
        detail_level: str = "standard"
    ) -> str:
        """
        Template for explaining code to different audiences.

        Use this prompt to generate explanations tailored to
        different technical levels.

        Args:
            artifact_id: Artifact to explain
            audience: Target audience - "developer", "manager", "newbie"
            detail_level: Detail level - "concise", "standard", "verbose"

        Returns:
            Formatted prompt for code explanation

        Examples:
            >>> explain_code("src/auth/authenticate.py", audience="developer")
            >>> explain_code("artifact-123", audience="manager", detail_level="concise")
        """
        audience_guidance = {
            "developer": "Use technical terminology, reference design patterns, discuss implementation details",
            "manager": "Focus on business value, complexity, risk, and effort estimates",
            "newbie": "Use simple language, explain concepts, avoid jargon, provide examples",
        }

        detail_guidance = {
            "concise": "Provide a brief overview (2-3 sentences)",
            "standard": "Provide a comprehensive explanation (1-2 paragraphs)",
            "verbose": "Provide detailed explanation with examples and context (3+ paragraphs)",
        }

        return f"""You are explaining code from Palace Mental.

## Task
Explain this artifact in a way that a {audience} can understand.

## Artifact
`{artifact_id}`

## Audience Guidelines
{audience_guidance.get(audience, audience_guidance["developer"])}

## Detail Level
{detail_guidance.get(detail_level, detail_guidance["standard"])}

## Steps
1. Use `explain_artifact` to get the artifact explanation
2. Use `query_artifact` to get detailed code context
3. Tailor the explanation to the specified audience
4. Adjust detail level accordingly

## Response Format
Structure your explanation as:
1. **Overview**: High-level purpose (1-2 sentences)
2. **How It Works**: Key components and logic
3. **Why It Matters**: Business/technical value
4. **Key Insights**: Important patterns or decisions

## Tools to Use
- `explain_artifact("{artifact_id}")` - Get base explanation
- `query_artifact("{artifact_id}")` - Get detailed context
"""

    @mcp.prompt()
    def find_similar_pattern(
        artifact_id: str,
        use_case: str = "refactoring"
    ) -> str:
        """
        Template for finding and analyzing similar code patterns.

        Use this prompt to discover code duplication, refactoring
        opportunities, or similar implementations.

        Args:
            artifact_id: Reference artifact
            use_case: "refactoring", "learning", "debugging"

        Returns:
            Formatted prompt for pattern analysis

        Examples:
            >>> find_similar_pattern("src/auth/login.py")
            >>> find_similar_pattern("artifact-123", use_case="learning")
        """
        use_case_guidance = {
            "refactoring": "Focus on consolidation opportunities and code reuse",
            "learning": "Focus on understanding patterns and implementation approaches",
            "debugging": "Focus on finding similar bugs or comparing working vs non-working code",
        }

        return f"""You are analyzing code patterns using Palace Mental's structural similarity detection.

## Task
Find and analyze artifacts with similar structure to: `{artifact_id}`

## Use Case
{use_case_guidance.get(use_case, use_case_guidance["refactoring"])}

## Analysis Steps
1. Use `find_similar_artifacts` to get structurally similar code
2. Use `query_artifact` to examine each similar artifact
3. Compare implementations, identify patterns
4. Provide actionable insights based on use case

## Response Format

### For Refactoring:
1. **Similar Artifacts**: List with similarity confidence
2. **Common Patterns**: What's repeated across artifacts
3. **Consolidation Opportunity**: How to extract shared logic
4. **Impact**: Effort and benefit analysis

### For Learning:
1. **Similar Implementations**: How others solved similar problems
2. **Pattern Variations**: Key differences and trade-offs
3. **Best Practices**: What approaches work best
4. **Recommendations**: What to apply or avoid

### For Debugging:
1. **Working vs Non-working**: Compare implementations
2. **Key Differences**: What diverges between artifacts
3. **Bug Pattern**: Common issues in similar code
4. **Fix Strategy**: How to apply working patterns

## Tools to Use
- `find_similar_artifacts("{artifact_id}")` - Get similar artifacts
- `query_artifact(artifact_id)` - Examine each artifact
"""

    @mcp.prompt()
    def index_project(
        project_path: str,
        scope: str = "full"
    ) -> str:
        """
        Template for indexing a new project.

        Use this prompt to guide the indexing process and verify
        results.

        Args:
            project_path: Path to project directory
            scope: "full", "incremental", or "specific"

        Returns:
            Formatted prompt for project indexing

        Examples:
            >>> index_project("/path/to/project")
            >>> index_project("src/", scope="specific")
        """
        return f"""You are indexing a new project into Palace Mental.

## Task
Index project at: `{project_path}`

## Scope
{scope}

## Indexing Steps
1. **Preparation**: Verify path exists and is accessible
2. **Indexing**: Use `index_files` to index the project
3. **Verification**: Use `get_index_status` to verify results
4. **Testing**: Use `query_artifact` to test a few files

## Best Practices
1. Start with a small subset to verify setup
2. Monitor stderr for progress and errors
3. Check language breakdown is correct
4. Test queries on indexed artifacts
5. Verify dependency graphs are accurate

## Troubleshooting
- **Slow indexing**: Normal for large projects, monitor progress
- **Language detection errors**: Specify language explicitly
- **Memory issues**: Index in batches using specific paths
- **Dependency issues**: Check file parsing logs

## Tools to Use
1. `index_files(["{project_path}"])` - Index the project
2. `get_index_status("{project_path}")` - Check results
3. `query_artifact("test_file.py")` - Test query

## Success Criteria
- ✅ All files indexed successfully
- ✅ Language breakdown looks correct
- ✅ Sample queries return TOON format
- ✅ Dependency graphs build correctly
"""


# Export for testing
__all__ = [
    "register_prompt_templates",
    "query_with_context",
    "analyze_dependencies",
    "explain_code",
    "find_similar_pattern",
    "index_project",
]
