# Tree-Sitter Integration Issue

## Problem Description

The tree-sitter parsers (JavaScript, TypeScript, Go) are failing to parse even simple code snippets.

## Investigation

### Environment
- `tree-sitter`: 0.20.4
- `tree-sitter-typescript`: 0.23.2
- `tree-sitter-go`: 0.25.0
- Python: 3.12.3

### Error Pattern

```python
import tree_sitter
import tree_sitter_typescript

lang = tree_sitter_typescript.language_typescript()
parser = tree_sitter.Parser(lang)
tree = parser.parse(b"const x = 1;")
# ValueError: Parsing failed
```

**Even the Python parser fails:**
```python
from tree_sitter_python import language
parser = tree_sitter.Parser(language())
tree = parser.parse(b"def f(): pass")
# ValueError: Parsing failed
```

### Root Cause

The issue appears to be a **compatibility problem** between:
- tree-sitter Python bindings version 0.20.4
- tree-sitter language grammars (0.23.x - 0.25.x)
- Python 3.12.3

The language objects are successfully created and passed to `Parser()`, but `parse()` consistently fails with `ValueError: Parsing failed`.

## Potential Solutions

### 1. **Downgrade tree-sitter** ⚠️
```bash
poetry add tree-sitter@0.19.0
```
- Risk: May break other dependencies
- Status: Not tested

### 2. **Use Alternative Parsing Libraries** ✅
Instead of tree-sitter, use:
- **JavaScript**: `esprima` (Python port) or `ast` library
- **TypeScript**: `typescript` package via subprocess
- **Go**: `go/ast` via subprocess or custom regex-based parser

### 3. **Wait for tree-sitter Fix** ⏳
Monitor tree-sitter GitHub issues for:
- https://github.com/tree-sitter/py-tree-sitter/issues
- Search for "Parsing failed" errors with Python 3.12

### 4. **Mock Parsers for Testing** ✅
Create mock parsers that return simple test data:
- Useful for unit tests
- Allows development to continue
- Can be replaced when tree-sitter is fixed

## Current Status

### ✅ Working
- **Python Parser**: Uses stdlib `ast` module - perfect functionality
- **Registry**: Auto-detection and parser selection works
- **CLI**: Multi-language commands work
- **Tests**: Python parser tests pass completely

### ❌ Not Working
- **JavaScript Parser**: Returns 0 symbols/deps (tree-sitter issue)
- **TypeScript Parser**: Returns 0 symbols/deps (tree-sitter issue)
- **Go Parser**: Returns 0 symbols/deps (tree-sitter issue)

### ⚠️ Graceful Degradation
The parsers **don't crash** - they just return empty results. This means:
- System is stable and usable
- Python-only projects work perfectly
- Multi-language projects ingest Python files successfully
- JS/TS/Go files are ingested but without symbol/deprecation extraction

## Recommended Action Plan

### Short Term (This Week)
1. ✅ Document the issue (this file)
2. ⏳ Create mock parsers for testing
3. ⏳ Add integration tests that work with Python only
4. ⏳ Update documentation to note tree-sitter limitation

### Medium Term (This Month)
1. **Investigation**: Try downgrading tree-sitter to test compatibility
2. **Alternative**: Implement JavaScript parser with `esprima-python`
3. **Alternative**: Implement basic regex-based parsers for JS/TS/Go
4. **Community**: Post tree-sitter issue with reproduction steps

### Long Term (When Fixed)
1. ✅ Code is ready - just needs working tree-sitter
2. Swap back to tree-sitter when compatibility is resolved
3. Add comprehensive tree-sitter parser tests

## Workarounds

### For Testing
```python
# Mock parser for testing
class MockJavaScriptParser(BaseParser):
    def supported_extensions(self):
        return [".js", ".jsx"]

    def parse_dependencies(self, file_path, content):
        # Simple regex-based extraction
        import re
        deps = []
        for match in re.finditer(r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', content):
            deps.append(Dependency(path=match.group(1), type="IMPORT", lineno=1))
        return deps

    def extract_symbols(self, content):
        # Simple regex-based extraction
        import re
        symbols = []
        for match in re.finditer(r'function\s+(\w+)', content):
            symbols.append(Symbol(name=match.group(1), type="function", lineno=1))
        return symbols

    def compute_fingerprint(self, content):
        return hashlib.sha256(content.encode()).hexdigest()
```

### For Production
Continue using Python-only parsing until tree-sitter is fixed:
```bash
palace ingest --languages python
```

## Timeline

- **2026-02-15**: Issue discovered during implementation
- **2026-02-15**: Documented and workarounds identified
- **TBD**: tree-sitter compatibility fix or alternative implementation

## References

- tree-sitter Python: https://github.com/tree-sitter/py-tree-sitter
- tree-sitter-typescript: https://github.com/tree-sitter/tree-sitter-typescript
- Related Issues:
  - https://github.com/tree-sitter/py-tree-sitter/issues/285
  - https://github.com/tree-sitter/py-tree-sitter/issues/274
