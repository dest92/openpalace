# Quick Start - Palace Mental

Quick guide to get started in 5 minutes.

---

## Requirements

- **Python**: 3.10 or higher
- **Poetry**: Latest version (for dependency management)
- **Disk**: ~100MB for the database + space for vectors
- **RAM**: 2GB minimum recommended (4GB+ for large repos)

---

## Installation (2 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/dest92/openpalace.git
cd openpalace

# 2. Install dependencies with Poetry
poetry install

# 3. Verify installation
poetry run palace --help
```

Expected output:
```
Palacio Mental - Cognitive memory system for code

Options:
  --help  Show this message and exit.

Commands:
  init      Initialize Palace for a repository
  ingest    Ingest code files into the knowledge graph
  context   Get contextual information for a file
  sleep     Run sleep cycle for consolidation
  stats     Show brain statistics
  query     Execute raw Cypher query
```

---

## Basic Usage (3 minutes)

### Step 1: Go to your project

```bash
cd /path/to/your/project
```

### Step 2: Initialize Palace

```bash
poetry run palace init
```

This creates a `.palace/` directory with:
- `brain.kuzu` - Graph database
- `vectors.db` - Vector database

### Step 3: Ingest your code

```bash
# Ingest all Python files
poetry run palace ingest

# Or ingest specific patterns
poetry run palace ingest --file-pattern "src/**/*.py"
```

Expected output:
```
Found 18 files
✓ src/auth/login.py: 5 symbols
✓ src/database/connection.py: 8 symbols
✓ src/api/routes.py: 9 symbols
...
Ingestion complete!
```

### Step 4: View statistics

```bash
poetry run palace stats
```

Expected output:
```
📊 Palace Brain Statistics
========================================
Total Nodes: 25
Total Edges: 42

Nodes by Type:
  Artifact: 18
  Concept: 5
  Invariant: 2

Edges by Type:
  DEPENDS_ON: 15
  EVOKES: 20
  CONSTRAINS: 5
```

---

## Get Context

### Full context (rich markdown)

```bash
poetry run palace context src/auth.py
```

Output:
```markdown
## 🏛️ Architectural Context (Palace Mental)
**Seed**: `src/auth.py` | **Total Activation**: 12.46 | **Risk**: 0.00

### ⚠️ Active Invariants
*No active invariants for this file.*

### 🔗 Local Topology (Cognitive Neighborhood)
**📥 Depends on:**
- `src/database/connection.py` (python) - dist: 1
- `src/utils/crypto.py` (python) - dist: 2

**📤 Impacts:**
- `src/api/routes.py` (python) - dist: 1
- `src/middleware/auth.py` (python) - dist: 2

### 🧠 Active Concepts
- **Authentication** `██████████` 1.00
- **Security** `█████████░` 0.92
- **Password Management** `███████░░` 0.78

### 🎯 Risk Assessment
**🟢 Risk Level: Low (0.00)**
*No significant risk factors detected.*
```

### Compact version (one line)

```bash
poetry run palace context src/auth.py --compact
```

Output:
```
🏛️ Context: `src/auth.py` (risk: 0.00) | 🧠 Concepts: Authentication, Security | 📥 Depends on: src/database/connection.py
```

### Save to file

```bash
poetry run palace context src/auth.py -o /tmp/context.md
```

---

## Workflow with Claude Code

```bash
# 1. Before asking Claude for changes, get context
poetry run palace context src/file_to_edit.py -o /tmp/ctx.md

# 2. Copy to clipboard (Linux)
cat /tmp/ctx.md | xclip -selection clipboard

# 3. In Claude Code:
#    - Paste the context
#    - Ask your question with full architectural awareness
```

---

## Essential Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `palace init` | Initialize Palace | `palace init` |
| `palace ingest` | Scan code and build graph | `palace ingest` |
| `palace ingest -p "src/**/*.py"` | Ingest specific pattern | `palace ingest -p "**/*.py"` |
| `palace context <file>` | Get architectural context | `palace context src/auth.py` |
| `palace context <file> -c` | One-line compact version | `palace context auth.py -c` |
| `palace context <file> -o <path>` | Save context to file | `palace context auth.py -o ctx.md` |
| `palace sleep` | Run consolidation cycle | `palace sleep` |
| `palace stats` | Show graph statistics | `palace stats` |
| `palace query "<cypher>"` | Direct Cypher query | `palace query "MATCH (n) RETURN count(n)"` |

---

## Generated Structure

```
your-project/
├── .palace/
│   ├── brain.kuzu          # Embedded graph (KuzuDB)
│   └── vectors.db          # SQLite+vec (embeddings)
├── src/
│   ├── auth.py
│   ├── database/
│   └── api/
└── pyproject.toml
```

---

## Troubleshooting

### `palace: command not found`

```bash
# Use poetry run
poetry run palace --help
```

### No concepts detected

```bash
# Install sentence-transformers
poetry add sentence-transformers
# First run downloads ~100MB of models
```

### Ingestion very slow

```bash
# For large repos, ensure .gitignore excludes heavy directories:
# node_modules/
# .git/
# __pycache__/
# *.pyc
# dist/
# build/
```

### Reset and start over

```bash
# Remove Palace database
rm -rf .palace/

# Re-initialize
poetry run palace init
poetry run palace ingest
```

---

## Real Example Output

```bash
$ poetry run palace context tests/test_auth.py
## 🏛️ Architectural Context (Palace Mental)
**Seed**: `tests/test_auth.py` | **Total Activation**: 8.32 | **Risk**: 0.20

### ⚠️ Active Invariants
**📋 Others (1):**
- [🟡] `test_coverage` → Missing tests for edge cases
  ↳ Distance: 1 hops | File: `tests/test_auth.py`

### 🔗 Local Topology (Cognitive Neighborhood)
**📥 Depends on:**
- `src/auth/login.py` (python) - dist: 1
- `src/database/connection.py` (python) - dist: 2

**📤 Impacts:**
*No dependent files*

### 🧠 Active Concepts
- **Testing** `██████████` 1.00
- **Authentication** `█████████░` 0.91
- **Security** `████████░░` 0.72

### 🎯 Risk Assessment
**🟢 Risk Level: Low (0.20)**
*No significant risk factors detected.*
```

---

## Next Steps

1. **Learn more**: Read the full [docs/TUTORIAL.md](TUTORIAL.md)
2. **Quick reference**: See [docs/CHEATSHEET.md](CHEATSHEET.md)
3. **Understand concepts**: Check [docs/GLOSSARY.md](GLOSSARY.md)
4. **Real demo**: Watch [docs/DEMO.md](DEMO.md) with actual execution

---

## Pro Tips

💡 **Run `palace context` before every coding session**
- See what files depend on your changes
- Understand architectural constraints
- Avoid breaking existing functionality

💡 **Run `palace sleep` weekly**
- Consolidates frequently-used patterns
- Prunes weak connections
- Keeps graph optimized

💡 **Use `--compact` for quick checks**
```bash
palace context src/auth.py --compact
# Quick overview without leaving terminal
```

💡 **Combine with git**
```bash
# See what changed since last commit
git diff --name-only HEAD | xargs -I {} palace context {}
```

---

**Ready!** Now you can use `palace context` before every coding session with Claude. 🏛️🧠

**Need help?** Open an issue at: https://github.com/dest92/openpalace/issues
