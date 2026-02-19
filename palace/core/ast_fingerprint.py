"""
AST Fingerprinting - Structural hashing for code similarity detection.

Based on research from Chilowicz et al. (ICPC 2009):
"Syntax tree fingerprinting: a foundation for source code similarity detection"

Key principles:
- Hash function sensitive to tree structure
- Combine child hashes with parent node
- Order-independent for structural equivalence
- 32 bytes per file (vs 1.5KB embedding)
"""

import hashlib
from typing import Any, Optional
from pathlib import Path


def hash_ast_structure(node: Any, content: str = "") -> str:
    """
    Recursively hash AST structure for fingerprinting.

    This function creates a structure-sensitive hash that:
    - Detects exact clone clusters
    - Is language-agnostic (tree-sitter supports 80+ languages)
    - Produces 32-byte hash (SHA-256)
    - Is order-independent for equivalent structures

    Args:
        node: Tree-sitter node (root or subtree)
        content: Optional source code content

    Returns:
        32-byte hex hash string (SHA-256)
    """
    if not node or not hasattr(node, 'type'):
        # Fallback for invalid nodes
        return hashlib.sha256(b"").hexdigest()

    # Start hash with node type
    hash_parts = [node.type]

    # Process named children only (skip anonymous nodes)
    named_children = [child for child in node.children if child.is_named]

    if named_children:
        # Recursively hash all children
        child_hashes = []
        for child in named_children:
            child_hash = hash_ast_structure(child, content)
            child_hashes.append(child_hash)

        # Sort for order-independence
        # This makes structurally equivalent trees produce same hash
        child_hashes.sort()

        # Combine with node type
        combined = f"{node.type}:{','.join(child_hashes)}"
    else:
        # Leaf node - just use type
        combined = node.type

    # Generate final hash
    return hashlib.sha256(combined.encode()).hexdigest()


def hash_file_ast(code: str, parser: Any) -> str:
    """
    Parse code and generate AST fingerprint.

    Args:
        code: Source code content
        parser: Tree-sitter parser object

    Returns:
        32-byte hex hash string
    """
    if not parser:
        # Fallback to content hash if parser unavailable
        return hashlib.sha256(code.encode()).hexdigest()

    try:
        # Parse code into AST
        tree = parser.parse(bytes(code, "utf8"))

        if not tree or not tree.root_node:
            return hashlib.sha256(code.encode()).hexdigest()

        # Hash structure
        return hash_ast_structure(tree.root_node, code)

    except Exception:
        # Fallback on any error
        return hashlib.sha256(code.encode()).hexdigest()


def compute_fingerprint_batch(
    files: dict,  # {file_path: (code, parser)}
) -> dict:
    """
    Compute fingerprints for multiple files efficiently.

    Args:
        files: Dictionary mapping file_path to (code, parser) tuples

    Returns:
        Dictionary mapping file_path to fingerprint
    """
    fingerprints = {}

    for file_path, (code, parser) in files.items():
        fingerprints[file_path] = hash_file_ast(code, parser)

    return fingerprints


def are_structurally_similar(fingerprint1: str, fingerprint2: str) -> bool:
    """
    Check if two fingerprints indicate structural similarity.

    Exact match = identical structure
    Different hash = definitely different structure

    Args:
        fingerprint1: First fingerprint
        fingerprint2: Second fingerprint

    Returns:
        True if structures are identical
    """
    return fingerprint1 == fingerprint2


class ASTFingerprintCache:
    """
    Cache for AST fingerprints to avoid re-parsing.

    Useful for incremental updates and optimization.
    """

    def __init__(self):
        """Initialize empty cache."""
        self._cache: dict = {}

    def get(self, file_path: str) -> Optional[str]:
        """
        Get cached fingerprint for file.

        Args:
            file_path: Path to file

        Returns:
            Fingerprint or None if not cached
        """
        return self._cache.get(file_path)

    def set(self, file_path: str, fingerprint: str) -> None:
        """
        Cache fingerprint for file.

        Args:
            file_path: Path to file
            fingerprint: Fingerprint to cache
        """
        self._cache[file_path] = fingerprint

    def invalidate(self, file_path: str) -> None:
        """
        Remove file from cache.

        Args:
            file_path: Path to invalidate
        """
        self._cache.pop(file_path, None)

    def clear(self) -> None:
        """Clear all cached fingerprints."""
        self._cache.clear()

    def size(self) -> int:
        """Get number of cached fingerprints."""
        return len(self._cache)

    def __repr__(self) -> str:
        return f"ASTFingerprintCache(size={self.size()})"


# Convenience function for Palace Mental
def fingerprint_artifact(
    code: str,
    parser: Any,
    cache: Optional[ASTFingerprintCache] = None,
    artifact_id: Optional[str] = None
) -> str:
    """
    Compute fingerprint for a Palace Mental artifact.

    Args:
        code: Source code content
        parser: Tree-sitter parser
        cache: Optional fingerprint cache
        artifact_id: Optional artifact ID for cache lookup

    Returns:
        32-byte fingerprint
    """
    # Check cache first
    if cache and artifact_id:
        cached = cache.get(artifact_id)
        if cached:
            return cached

    # Compute fingerprint
    fingerprint = hash_file_ast(code, parser)

    # Store in cache
    if cache and artifact_id:
        cache.set(artifact_id, fingerprint)

    return fingerprint
