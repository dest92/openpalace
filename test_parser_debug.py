"""Debug script to test tree-sitter parsers."""

from pathlib import Path
from palace.ingest.parsers.javascript import JavaScriptParser

# Create parser
parser = JavaScriptParser()

print(f"Parser available: {parser.is_available()}")
print(f"Supported extensions: {parser.supported_extensions()}")

# Test simple ES6 import
content = """
import React from 'react';
"""

print(f"\nParsing content: {repr(content)}")

deps = parser.parse_dependencies(Path("test.js"), content)
print(f"Dependencies extracted: {deps}")
print(f"Number of dependencies: {len(deps)}")

# Try parsing tree
tree = parser._parse_tree(content)
if tree:
    print(f"\nTree parsed successfully")
    print(f"Root node type: {tree.root_node.type}")
    print(f"Root node children: {len(tree.root_node.children)}")

    # Find import statements
    import_nodes = parser._find_nodes_by_type(tree, "import_statement")
    print(f"Import nodes found: {len(import_nodes)}")
    for node in import_nodes:
        print(f"  Node type: {node.type}")
else:
    print("\nFailed to parse tree")

# Test fingerprinting
fp = parser.compute_fingerprint(content)
print(f"\nFingerprint: {fp}")
