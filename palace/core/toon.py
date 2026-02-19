"""
TOON (Token-Oriented Object Notation) Encoder for LLM Agent Communication.

Based on TOON specification (2024):
- 40-60% token reduction vs JSON
- Tabular format for arrays
- Indentation-based for nested structures
- Schema-aware compression

Use for ON-DEMAND export to agents, NOT for storage.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class TOONNode:
    """
    Represents a node in TOON format.

    Uses indentation (YAML-like) and tabular structure (CSV-like).
    """
    name: str
    node_type: str
    children: List['TOONNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_toon(self, indent: int = 0) -> str:
        """
        Convert node to TOON format.

        Args:
            indent: Current indentation level

        Returns:
            TOON-formatted string
        """
        prefix = "  " * indent

        # Format: node_type: name
        lines = [f"{prefix}{self.node_type}: {self.name}"]

        # Add metadata as tabular if present
        if self.metadata:
            for key, value in self.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    lines.append(f"{prefix}  {key}: {value}")

        # Add children with increased indent
        for child in self.children:
            lines.append(child.to_toon(indent + 1))

        return "\n".join(lines)


@dataclass
class ASTSummary:
    """
    Simplified AST summary for TOON export.

    Contains only structural information relevant to agents.
    """
    file_path: str
    language: str
    functions: List[Dict] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)

    def to_toon(self) -> str:
        """
        Convert AST summary to TOON format.

        Returns:
            TOON-formatted string
        """
        lines = [f"{self.file_path}:"]
        lines.append(f"  language: {self.language}")

        # Imports (tabular format)
        if self.imports:
            lines.append("  imports:")
            for imp in self.imports:
                lines.append(f"    - {imp}")

        # Exports (tabular format)
        if self.exports:
            lines.append("  exports:")
            for exp in self.exports:
                lines.append(f"    - {exp}")

        # Functions (tabular with metadata)
        if self.functions:
            lines.append("  functions:")
            for func in self.functions:
                # Format: name(params) -> return_type
                params = ", ".join(func.get('parameters', []))
                ret = func.get('return_type', 'None')
                lines.append(f"    - {func['name']}({params}) -> {ret}")

                # Calls/dependencies
                if 'calls' in func and func['calls']:
                    lines.append(f"      calls: {', '.join(func['calls'])}")

        # Classes (tabular with methods)
        if self.classes:
            lines.append("  classes:")
            for cls in self.classes:
                lines.append(f"    - {cls['name']}:")
                if 'methods' in cls and cls['methods']:
                    for method in cls['methods']:
                        params = ", ".join(method.get('parameters', []))
                        ret = method.get('return_type', 'None')
                        lines.append(f"      - {method['name']}({params}) -> {ret}")

        return "\n".join(lines)


class TOONEncoder:
    """
    Encoder for converting AST structures to TOON format.

    Optimized for LLM token efficiency:
    - Removes verbose syntax (braces, quotes, commas)
    - Uses indentation for hierarchy
    - Uses tabular format for lists
    - Schema-aware (knows structure in advance)
    """

    def __init__(self, compact: bool = True):
        """
        Initialize TOON encoder.

        Args:
            compact: Use most compact format (default: True)
        """
        self.compact = compact

    def encode_ast_summary(self, summary: ASTSummary) -> str:
        """
        Encode AST summary to TOON format.

        Args:
            summary: AST summary object

        Returns:
            TOON-formatted string
        """
        return summary.to_toon()

    def encode_multiple_summaries(self, summaries: List[ASTSummary]) -> str:
        """
        Encode multiple AST summaries to TOON format.

        Args:
            summaries: List of AST summaries

        Returns:
            TOON-formatted string with all summaries
        """
        sections = []
        for summary in summaries:
            sections.append(self.encode_ast_summary(summary))

        return "\n\n---\n\n".join(sections)

    def encode_graph_context(
        self,
        main_artifact: ASTSummary,
        dependencies: List[ASTSummary],
        dependency_type: str = "DEPENDS_ON"
    ) -> str:
        """
        Encode artifact + dependencies in TOON format.

        This is the PRIMARY export format for agent queries.

        Args:
            main_artifact: Main artifact requested by agent
            dependencies: List of dependency artifacts
            dependency_type: Type of relationship (DEPENDS_ON, EVOKES, etc.)

        Returns:
            TOON-formatted string with full context
        """
        lines = []

        # Main artifact
        lines.append(f"# {main_artifact.file_path}")
        lines.append(self.encode_ast_summary(main_artifact))

        # Dependencies
        if dependencies:
            lines.append(f"\n# {dependency_type} ({len(dependencies)} files)")
            for dep in dependencies:
                lines.append(f"\n## {dep.file_path}")
                lines.append(self.encode_ast_summary(dep))

        return "\n".join(lines)

    def estimate_tokens(self, toon_string: str) -> int:
        """
        Estimate token count for TOON string.

        Rough estimation: ~4 characters per token.

        Args:
            toon_string: TOON-formatted string

        Returns:
            Estimated token count
        """
        return len(toon_string) // 4

    def compare_vs_json(self, summary: ASTSummary) -> dict:
        """
        Compare TOON vs JSON token usage for given summary.

        Args:
            summary: AST summary to compare

        Returns:
            Dictionary with comparison metrics
        """
        # Generate TOON
        toon_str = self.encode_ast_summary(summary)
        toon_tokens = self.estimate_tokens(toon_str)

        # Generate JSON
        json_str = json.dumps({
            'file_path': summary.file_path,
            'language': summary.language,
            'functions': summary.functions,
            'classes': summary.classes,
            'imports': summary.imports,
            'exports': summary.exports,
        }, indent=2)
        json_tokens = self.estimate_tokens(json_str)

        # Calculate savings
        token_reduction = (json_tokens - toon_tokens) / json_tokens
        space_reduction = (len(json_str) - len(toon_str)) / len(json_str)

        return {
            'toon_tokens': toon_tokens,
            'json_tokens': json_tokens,
            'token_reduction': f"{token_reduction:.1%}",
            'toon_size': len(toon_str),
            'json_size': len(json_str),
            'space_reduction': f"{space_reduction:.1%}",
        }


# Convenience functions for Palace Mental

def ast_to_toon(ast_summary: ASTSummary) -> str:
    """
    Quick conversion from AST summary to TOON format.

    Args:
        ast_summary: AST summary object

    Returns:
        TOON-formatted string
    """
    encoder = TOONEncoder()
    return encoder.encode_ast_summary(ast_summary)


def create_ast_summary(
    file_path: str,
    language: str,
    symbols: List[Any],
    dependencies: List[Any]
) -> ASTSummary:
    """
    Create AST summary from Palace Mental parser output.

    Args:
        file_path: Path to file
        language: Programming language
        symbols: List of Symbol objects from parser
        dependencies: List of Dependency objects from parser

    Returns:
        ASTSummary object
    """
    summary = ASTSummary(
        file_path=file_path,
        language=language
    )

    # Process symbols
    for symbol in symbols:
        if symbol.kind == 'function':
            summary.functions.append({
                'name': symbol.name,
                'parameters': [],  # TODO: Extract from symbol
                'return_type': 'None',  # TODO: Extract from symbol
                'calls': [],  # TODO: Extract from AST analysis
            })
        elif symbol.kind == 'class':
            summary.classes.append({
                'name': symbol.name,
                'methods': [],  # TODO: Extract methods
            })

    # Process dependencies
    for dep in dependencies:
        if dep.kind == 'import':
            summary.imports.append(dep.name)

    return summary


def export_to_agent(
    main_file: str,
    main_summary: ASTSummary,
    dependency_summaries: List[ASTSummary]
) -> str:
    """
    Export complete context to AI agent in TOON format.

    This is the main entry point for agent queries.

    Args:
        main_file: File path requested by agent
        main_summary: AST summary of main file
        dependency_summaries: AST summaries of dependencies

    Returns:
        TOON-formatted string ready for agent consumption
    """
    encoder = TOONEncoder()
    return encoder.encode_graph_context(
        main_summary,
        dependency_summaries,
        dependency_type="DEPENDS_ON"
    )
