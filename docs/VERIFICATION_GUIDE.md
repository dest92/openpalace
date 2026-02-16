# Palace Mental Implementation Verification Guide

## Quick Verification Commands

### 1. Verify Dependency Linking (Phase 1)
```bash
# After ingestion, check if DEPENDS_ON edges exist
palace query "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS count"

# Expected: > 0 (previously returned 0)

# Check specific dependency
palace query "MATCH (a:Artifact)-[r:DEPENDS_ON]->(b:Artifact) RETURN b.path LIMIT 5"
```

### 2. Verify RELATED_TO Edges (Phase 2)
```bash
# Check if RELATED_TO edges exist
palace query "MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count"

# Expected: > 0 (previously returned 0)

# Check concept connections
palace query "MATCH (a:Concept)-[r:RELATED_TO]->(b:Concept) RETURN a.name, b.name LIMIT 10"
```

### 3. Verify Community Detection (Phase 3)
```bash
# Run sleep cycle
palace sleep

# Check if Anchor nodes were created
palace query "MATCH (a:Anchor) RETURN count(a) AS count"

# Expected: > 0 (previously returned 0)

# Check community descriptions
palace query "MATCH (a:Anchor) RETURN a.description"
```

### 4. Verify Invariant Checkers (Phase 4)
```bash
# List all available rules
palace query "MATCH (i:Invariant) RETURN DISTINCT i.rule"

# Expected: 12+ rules (hardcoded_secrets, eval_usage, sql_injection, etc.)

# Check CRITICAL severity invariants
palace query "MATCH (i:Invariant) WHERE i.severity = 'CRITICAL' RETURN i.rule, i.message LIMIT 10"

# Check configuration file
cat .palace/invariants.toml
```

### 5. Verify Hebbian Consolidation (Phase 5)
```bash
# Run sleep with consolidation enabled
palace sleep --consolidate

# Check if pairs were reinforced
# Look for "Pairs reinforced: > 0" in output
```

### 6. Verify CLI Options (Phase 6)
```bash
# Test all new CLI options
palace sleep --decay 0.1 --prune 0.2 --no-consolidate --no-communities

# Expected: All options accepted and reflected in output
```

## End-to-End Integration Test

```bash
# 1. Initialize new project
mkdir test-palace && cd test-palace
palace init

# 2. Create test file with violations
cat > test_code.py << 'EOF'
# Test file with violations
import os
import sys

API_KEY = "sk-1234567890abcdefghijklmnop"

def very_long_function():
    """A function that is too long."""
    x = 1
    y = 2
    # ... many more lines ...
    return x + y

class BigClass:
    def method1(self): pass
    def method2(self): pass
    # ... 15 methods total ...

eval("print('dangerous')")
EOF

# 3. Ingest
palace ingest .

# 4. Check results
echo "=== Dependencies ==="
palace query "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r)"

echo "=== Invariants ==="
palace query "MATCH (i:Invariant) RETURN i.rule, i.severity"

echo "=== Concepts ==="
palace query "MATCH ()-[r:RELATED_TO]->() RETURN count(r)"

# 5. Run sleep
palace sleep

# 6. Check communities
echo "=== Communities ==="
palace query "MATCH (a:Anchor) RETURN count(a)"
```

## Expected Results Summary

| Feature | Before | After |
|---------|--------|-------|
| DEPENDS_ON edges | 0 | >0 |
| RELATED_TO edges | 0 | >0 |
| Communities detected | 0 | >0 |
| Invariants | 1 | 12+ |
| Pairs reinforced | 0 | >0 |
| CLI options | None | All implemented |

## File Structure Verification

```bash
# Check new files exist
ls -la palace/ingest/resolver.py
ls -la palace/ingest/invariants/base.py
ls -la palace/ingest/invariants/registry.py
ls -la palace/ingest/invariants/detector.py
ls -la palace/ingest/invariants/checkers/*.py
ls -la invariants.toml.example
```

## Code Quality Checks

```bash
# All Python files should pass syntax validation
python3 -m py_compile palace/ingest/resolver.py
python3 -m py_compile palace/ingest/pipeline.py
python3 -m py_compile palace/core/sleep.py
python3 -m py_compile palace/ingest/invariants/*.py
python3 -m py_compile palace/ingest/invariants/checkers/*.py

# Expected: No errors
```

## Performance Benchmarks

- Dependency resolution: <100ms per file
- RELATED_TO edge creation: <50ms per file
- Invariant detection: <100ms per file
- Sleep cycle: <500ms total

## Success Indicators

✅ No Python syntax errors
✅ All new files created
✅ All existing files modified correctly
✅ Backward compatibility maintained
✅ All 6 phases implemented
✅ 12+ invariant checkers registered
✅ CLI options work as expected
