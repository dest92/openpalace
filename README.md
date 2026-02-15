# OpenPalace

OpenPalace turns large codebases into a persistent, queryable memory that understands relationships, intent, and context.

Ask any file: **"What will break if I change you?"** and get an answer in 100ms.

---

## The Real Problem

You're working on a codebase you didn't write. You need to:

- **Understand impact:** "If I refactor `database.py`, what breaks?"
- **Navigate unfamiliar code:** "Where is authentication actually handled?"
- **Onboard quickly:** "How does this system fit together?"
- **Avoid breaking things:** "What depends on this function?"

Current tools don't help much:
- `grep` shows text matches, not relationships
- IDEs show one file at a time, not the system
- Documentation is outdated or missing
- Asking seniors takes time everyone lacks

You spend hours reading code just to understand what you can safely touch.

---

## What OpenPalace Does

OpenPalace ingests your code and builds a knowledge graph that persists between sessions.

**What it gives you:**

1. **Impact analysis** — Query any file and see exactly what depends on it
2. **Contextual navigation** — Discover related files through dependency traversal
3. **Architectural awareness** — See connections, risks, and relationships before making changes
4. **AI integration** — Export structured context that LLMs can use to give better answers

**What it works with:**
- Python, JavaScript, TypeScript, Go (more languages coming)
- Framework-specific: Next.js route detection and metadata extraction
- Local-only, runs on your machine
- Works offline after initial setup

📖 **See [MULTI_LANG.md](docs/MULTI_LANG.md) for complete multi-language documentation**

---

## Try It in 3 Minutes

```bash
# Install
git clone https://github.com/dest92/openpalace.git
cd openpalace
poetry install

# Go to your project
cd /path/to/your-project

# Initialize and ingest
palace init

# Python-only project
palace ingest --languages python

# Multi-language project (Python, JavaScript, TypeScript, Go)
palace ingest

# Or specify custom patterns
palace ingest "**/*.{py,ts,tsx}"
```

Now ask questions your editor can't answer:

### Question 1: "What will break if I change this file?"

```bash
$ palace context src/database/connection.py
## Architectural Context (OpenPalace)
**Seed**: src/database/connection.py | **Total Activation**: 8.32 | **Risk**: 0.25

### Files That Depend on This:
• src/auth/login.py (IMPORT) — distance: 1
• src/api/routes.py (IMPORT) — distance: 1
• src/api/middleware.py (IMPORT) — distance: 2

### Active Concepts:
• Database Connection ████████ 1.00
• Data Access Layer ██████░ 0.78

### Risk Level: Medium (0.25)
⚠️ 2 files directly depend on this module
```

**Translation:** You have 3 files to test. You won't break anything else.

### Question 2: "How do I understand this file's role?"

```bash
$ palace context src/auth/login.py --compact
Context: src/auth/login.py (risk: 0.15) | Concepts: Authentication, Security | Depends on: src/database/connection.py | Impacts: src/api/routes.py
```

**Translation:** `login.py` is authentication logic, depends on the database, and is used by the API routes.

### Question 3: "What's the architecture here?"

```bash
$ palace query "MATCH (a)-[r:DEPENDS_ON]->(b) RETURN a.path as from, b.path as to LIMIT 10"

from                    │ to
─────────────────────────────────────────────────
src/api/routes.py    → src/auth/login.py
src/api/routes.py    → src/database/connection.py
src/auth/login.py    → src/database/connection.py
src/api/middleware.py → src/auth/jwt_handler.py
```

**Translation:** A complete dependency map in milliseconds. No manual tracing required.

---

## What Makes It Different

**1. Persistent memory of your code**
- Unlike `grep` or `find`, OpenPalace builds a graph that accumulates knowledge
- Relationships stay indexed between sessions
- You don't rebuild understanding every time you return to a project

**2. Understands relationships, not just text**
- Knows that `routes.py` *depends on* `auth.py` — not just that both contain "login"
- Traverses dependencies to show impact chains
- Surface hidden connections IDEs miss

**3. AI-ready context**
- Exports structured summaries LLMs can use effectively
- Works with Claude Code, Cursor, and other AI assistants
- Gives AI the architectural awareness it needs to provide useful answers

---

## Use Cases

**Developer Onboarding**
New developers spend 3 weeks understanding codebases. With OpenPalace, they query the graph and see relationships immediately. Onboarding drops to days, not weeks.

**Safe Refactoring**
Before changing code, run `palace context <file>` to see exactly what depends on it. Write tests for those files first. Refactor with confidence instead of fear.

**Legacy Code Exploration**
Inherited a project with no documentation? Ingest it and query the graph to understand the architecture without reading every file.

**AI-Assisted Development**
Using Claude Code or Cursor? Export context from OpenPalace so your AI assistant understands the system architecture, not just the file you're editing.

**Code Review**
Reviewing a PR? Query what files the changes impact and why. Reviews become architectural, not just syntactic.

---

## Architecture (For the Curious)

OpenPalace combines two storage systems:

**KuzuDB Graph Database**
- Stores artifacts (files), concepts (semantic meaning), and relationships
- 5 node types: Artifact, Concept, Invariant, Decision, Anchor
- 5 edge types: DEPENDS_ON, EVOKES, CONSTRAINS, PRECEDES, RELATED_TO

**SQLite+vec Vector Database**
- 384-dimensional embeddings for semantic search
- Finds conceptually similar code across the codebase

**Core Algorithms**
- **Spreading activation** — BFS traversal to discover related code
- **Hebbian learning** — Strengthens connections between co-activated concepts
- **Consolidation cycles** — Prunes weak connections, reinforces strong ones

The system uses tree-sitter (Python AST today) to parse code, extract symbols, and build the dependency graph automatically.

---

## Project Status

**Working Today (v2.0)**
- ✅ Python code ingestion with symbol extraction
- ✅ Dependency graph construction
- ✅ Context CLI with risk assessment
- ✅ Impact analysis queries
- ✅ Basic spreading activation
- ✅ Claude Code integration

**In Progress**
- 🚧 Multi-language support (TypeScript, Rust, Go parsers defined)
- 🚧 Advanced consolidation and forgetting cycles
- 🚧 Improved semantic concept extraction
- 🚧 Web UI for graph visualization

**Not Promised**
- ❌ Automatic refactoring (we show you what, not how)
- ❌ Code generation (we provide context, not features)
- ❌ Silver bullets for technical debt (we help you understand it, not eliminate it)

**Test Coverage:** 78% (625 statements)

---

## Installation

```bash
# Clone
git clone https://github.com/dest92/openpalace.git
cd openpalace

# Install with Poetry
poetry install

# Verify
palace --help
```

**Requirements:**
- Python 3.10+
- ~100MB disk space for databases
- 2GB RAM minimum (4GB+ recommended for large repos)

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `palace init` | Initialize OpenPalace in current directory |
| `palace ingest` | Scan and ingest all Python files |
| `palace ingest -p "src/**/*.py"` | Ingest specific file pattern |
| `palace context <file>` | Get architectural context for a file |
| `palace context <file> -c` | One-line compact context |
| `palace context <file> -o ctx.md` | Save context to file |
| `palace query "<cypher>"` | Execute raw Cypher query |
| `palace stats` | Show graph statistics |
| `palace sleep` | Run consolidation cycle |

---

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** — Get started in 5 minutes
- **[Tutorial](docs/TUTORIAL.md)** — Complete step-by-step walkthrough
- **[Demo with Real Code](docs/DEMO.md)** — See actual execution examples
- **[Claude Integration](docs/CLAUDE.md)** — Use with Claude Code
- **[API Guide](docs/API_INTEGRATION_GUIDE.md)** — Programmatic usage
- **[Glossary](docs/GLOSSARY.md)** — Concept definitions

---

## License

MIT

---

## Real Questions OpenPalace Can Answer

**"What files touch the authentication system?"**
→ Query: All files with path containing "auth" or dependencies on auth modules

**"Is this file safe to refactor?"**
→ Context: Check impact score, number of dependents, active invariants

**"Where should I add this new feature?"**
→ Query: Find files with related concepts, low coupling, and compatible dependencies

**"Why does this test fail after my change?"**
→ Impact analysis: See what you actually affected, not what you thought you touched

**"How do I give my AI assistant real context?"**
→ Export: `palace context src/file.py -o context.md` → paste into your AI tool
