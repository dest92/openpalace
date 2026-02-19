# Tree-sitter & AST Parsing - Research Summary

## Primary Reference
**Project:** Tree-sitter
**Authors:** Max Brunsfeld (original author), now maintained by GitHub
**Repository:** https://github.com/tree-sitter/tree-sitter
**Documentation:** https://tree-sitter.github.io/tree-sitter/

## Core Technology

### What is Tree-sitter?
A parser generator tool and incremental parsing library that:
- Builds **concrete syntax trees** (CST) for source code
- Supports **incremental parsing** (update AST as code edits)
- Provides parsers for **all major programming languages**
- Maintains **full fidelity** of source text

### Key Properties
**From paper "AST-T5" (2024):**
> "Using a lightweight, multi-language parser called Tree-sitter, our approach has broad applicability across all syntactically well-defined programming languages."

**From "Revisiting Code Similarity with AST" (2024):**
> "We use tree-sitter as our AST parser which is based on GLR, a powerful parsing algorithm."

### Performance Characteristics
- **Parsing speed:** O(n) for n tokens (linear)
- **Incremental update:** O(log n) for local edits
- **Memory:** ~100-200 bytes per node (CST)
- **Error recovery:** Robust (continues on syntax errors)

## AST Fingerprinting Applications

### 1. Syntax Tree Fingerprinting (ICPC 2009)
**Paper:** "Syntax tree fingerprinting: a foundation for source code similarity detection"
**Authors:** Michel Chilowicz, Éric Duris, Gilles Roussel, et al.

**Key Idea:**
> "Hash function sensitive to tree structure: must take into account internal nodes of AST to compute hash value of subtree"

**Algorithm:**
1. Parse code → AST using tree-sitter
2. Recursively hash subtrees
3. Combine child hashes with parent node
4. Result: Single hash value per AST

**Storage:**
- Per-file: 32-64 bytes (hash value)
- For 10M files: 320-640 MB

### 2. AST-Based Code Similarity (2024)
**Paper:** "Revisiting Code Similarity Evaluation with Abstract Syntax Tree Edit Distance"
**arXiv:** https://arxiv.org/html/2404.08817v1

**Key Findings:**
- Tree-sitter produces **concrete syntax tree** (CST)
- Need to **simplify** to AST (remove syntax noise)
- **Tree Edit Distance (TSED)** measures similarity

### 3. cAST: AST-based Call Graph Generator
**Paper:** "ACER: An AST-based Call Graph Generator Framework"
**arXiv:** https://arxiv.org/pdf/2308.15669

**Key Approach:**
> "Tree-sitter is both a parser generator tool and an incremental parsing library. It provides parsers for all popular languages and a common interface"

## Practical Implementation

### AST Hashing Strategy

**Naive approach:**
```python
# Serialize AST to string, then hash
ast_string = str(tree.to_dict())
hash_val = hash(ast_string)

# Problem: Serialization order unstable, size-dependent
```

**Structural hashing (RECOMMENDED):**
```python
def hash_ast_node(node):
    """Recursively hash AST node structure"""
    # Get node type
    node_type = node.type

    # Hash children recursively
    child_hashes = [hash_ast_node(child) for child in node.children]

    # Combine with node type
    combined = f"{node_type}:{':'.join(child_hashes)}"
    return hashlib.sha256(combined.encode()).hexdigest()

# Result: Structure-sensitive, order-independent hash
```

### Incremental Parsing Benefits

**From GitHub issue #3702:**
> "TS-Visualizer: TreeSitter-based in-browser AST parser and visualizer... The parsing is entirely performed in browser using TreeSitter's WASM support"

**Key advantage:**
- Real-time AST updates as user types
- No need to re-parse entire file
- Only affected subtrees updated

## Production Usage

### Known Systems Using Tree-sitter

1. **GitHub Copilot:** Code understanding
2. **VS Code:** Syntax highlighting, code navigation
3. **Neovim:** Treesitter-based highlighting
4. **LSP Servers:** Multiple language servers
5. **Code-graph-rag:** "The ultimate RAG for your monorepo... uses AST-based function targeting with Tree-sitter"

### Multi-Language Support

Tree-sitter supports **80+ programming languages** including:
- Python, JavaScript, TypeScript
- Go, Rust, C, C++
- Java, Kotlin, Swift
- Ruby, PHP, and many more

**All with unified API!**

## For Palace Mental

### Recommended Approach

**AST Fingerprint + Tree-sitter**

```python
import tree_sitter

def fingerprint_code(code: str, language: str) -> str:
    """
    Generate structural fingerprint of code using AST.

    Returns: 32-byte hash
    """
    # Get language parser
    parser = get_parser(language)
    tree = parser.parse(code)

    # Hash AST structure
    root_node = tree.root_node
    return hash_ast_structure(root_node)

def hash_ast_structure(node) -> str:
    """Recursively hash AST structure (order-independent)"""
    if not node.is_named:
        return ""

    # Collect child hashes
    children = []
    for child in node.children:
        h = hash_ast_structure(child)
        if h:
            children.append(h)

    # Sort for order-independence
    children.sort()

    # Combine node type with children
    combined = f"{node.type}:{','.join(children)}"
    return hashlib.sha256(combined.encode()).hexdigest()
```

### Storage Calculation

**For 10M code files:**
```
Naive storage (full AST):
- ~500 nodes per file × 100 bytes = 50KB per file
- 10M files × 50KB = 500GB (!!)

AST Fingerprint:
- 32 bytes per file (SHA-256 hash)
- 10M files × 32 bytes = 320MB

Compression: 1562x (!!)
```

### Integration with Bloom Filters

**Combined approach:**
```
1. Parse code → AST (tree-sitter)
2. Hash AST → 32-byte fingerprint
3. Store in Bloom filter (2MB for 10M items)
4. False positives → verify with actual AST comparison

Total storage: ~322MB for 10M files (!!)
```

## Critical Considerations

### When to Use Tree-sitter
✅ **Use for:**
- Structural code analysis
- Multi-language codebases
- Incremental parsing (editors)
- Precise syntax-aware operations

❌ **Avoid for:**
- Simple string search (grep is faster)
- Semantic-only analysis (embeddings better)
- Non-code text (use NLP)

### Performance Tips

1. **WASM compilation:** Compile to WebAssembly for browser
2. **Language detection:** Auto-detect from file extension
3. **Error recovery:** Use even with syntax errors
4. **Incremental:** Leverage for editor integrations

### Limitations

1. **CST vs AST:**
   - Tree-sitter produces CST (includes all syntax)
   - Need to simplify to AST (remove noise)
   - Some extra information kept for precision

2. **Memory overhead:**
   - Full CST is larger than AST
   - ~100-200 bytes per node
   - Not suitable for storing full trees

3. **Parsing errors:**
   - Robust error recovery
   - But may produce incorrect AST on severe errors
   - Always validate with syntax checker

## References
1. Tree-sitter GitHub: https://github.com/tree-sitter/tree-sitter
2. Chilowicz et al., "Syntax tree fingerprinting", ICPC 2009
3. arXiv:2404.08817, "Revisiting Code Similarity with AST", 2024
4. arXiv:2308.15669, "ACER: AST-based Call Graph Generator", 2023
5. arXiv:2506.15655, "cAST: Enhancing RAG with AST", 2025
