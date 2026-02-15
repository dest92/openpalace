# Palacio Mental v2.0

A bio-mimetic cognitive memory system for code engineering teams using graph databases, vector embeddings, and Hebbian learning algorithms.

## Features

- **Graph-Based Memory**: Uses KuzuDB for storing code relationships as a knowledge graph
- **Vector Embeddings**: SQLite+vec for semantic similarity search
- **Spreading Activation**: Cognitive navigation algorithm for discovering related code
- **Hebbian Learning**: Automatic strengthening of connections between co-activated concepts
- **Sleep Cycle**: Consolidation and forgetting mechanism for memory optimization
- **Code Ingestion**: Parse Python code with tree-sitter to extract symbols and dependencies
- **Context Provider**: LLM assistance through contextual code information

## Installation

```bash
# Install dependencies
pip install kuzu sqlite-vec sentence-transformers tree-sitter tree-sitter-python

# Or with Poetry
poetry install
```

## Usage

### Initialize Repository

```bash
poetry run palace init
```

### Ingest Code

```bash
# Ingest all Python files
poetry run palace ingest

# Ingest specific pattern
poetry run palace ingest --file-pattern "src/**/*.py"
```

### Get Context

```bash
# Get full architectural context (rich Markdown)
poetry run palace context src/auth.py

# Get compact one-line context
poetry run palace context src/auth.py --compact

# Save context to file
poetry run palace context src/auth.py -o /tmp/context.md
```

### Run Sleep Cycle

```bash
# Run consolidation and pruning
poetry run palace sleep
```

### Statistics and Queries

```bash
# Show brain statistics
poetry run palace stats

# Execute raw Cypher query
poetry run palace query "MATCH (n) RETURN count(n)"
```

## Architecture

### Storage Layer (Hippocampus)
- **KuzuDB**: Graph database for nodes (Concept, Artifact, Invariant, Decision, Anchor) and edges
- **SQLite+vec**: Vector database for semantic similarity search

### Core Algorithms
- **ActivationEngine**: BFS-based spreading activation with configurable depth and energy thresholds
- **PlasticityEngine**: Hebbian learning ("neurons that fire together, wire together")
- **SleepEngine**: Consolidation, pruning, and forgetting mechanisms

### Ingestion Pipeline
- **PythonParser**: Tree-sitter based parsing for Python code
- **ConceptExtractor**: Extracts concepts using sentence-transformers
- **InvariantDetector**: Detects architectural violations
- **BigBangPipeline**: Orchestrates the complete ingestion process

### API & CLI
- **ContextProvider**: Provides contextual information for LLM assistance
- **CLI Commands**: init, ingest, context, sleep

## Quick Start (5 minutes)

```bash
# Clone and install
git clone https://github.com/dest92/openpalace.git
cd openpalace
poetry install

# Or use automated setup
python setup_palace.py

# In your project
cd /path/to/your/project
poetry run palace init
poetry run palace ingest
poetry run palace context src/file.py
```

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed guide.

## Documentation

Complete documentation available in the [docs/](docs/) directory:

| Document | Description |
|----------|-------------|
| **[docs/QUICKSTART.md](docs/QUICKSTART.md)** | 5-minute quick start guide |
| **[docs/CHEATSHEET.md](docs/CHEATSHEET.md)** | Quick visual reference |
| **[docs/TUTORIAL.md](docs/TUTORIAL.md)** | Complete step-by-step tutorial |
| **[docs/GLOSSARY.md](docs/GLOSSARY.md)** | Glossary of all concepts |
| **[docs/DEMO.md](docs/DEMO.md)** | Real execution examples |
| **[docs/AGENTS.md](docs/AGENTS.md)** | Integration with AI assistants |
| **[docs/CLAUDE.md](docs/CLAUDE.md)** | Guide for Claude Code |
| **[docs/API_INTEGRATION_GUIDE.md](docs/API_INTEGRATION_GUIDE.md)** | API documentation |

See [docs/README.md](docs/README.md) for complete documentation index.

## Development

## Example Output

```bash
$ poetry run palace context src/auth.py
## 🏛️ Architectural Context (Palace Mental)
**Seed**: `src/auth.py` | **Total Activation**: 12.46 | **Risk**: 0.15

### ⚠️ Active Invariants
• [🔴 CRITICAL] `no_eval` → DO NOT USE eval()
• [🟠 HIGH] `sql_injection_risk` → Use parameterization

### 🔗 Local Topology (Cognitive Neighborhood)
**📥 Depends on:**
- `src/database/connection.py` (python) - dist: 1
- `src/utils/crypto.py` (python) - dist: 2

**📤 Impacts:**
- `src/api/routes.py` (python) - dist: 1

### 🧠 Active Concepts
- **Authentication** `██████████` 1.00
- **Security** `█████████░` 0.92
- **Password Management** `███████░░` 0.78

### 🎯 Risk Assessment
**🟡 Risk Level: Medium (0.15)**
**Risk factors:**
- ⚠️ 2 CRITICAL invariants active

**💡 Recommendations:**
- Carefully review CRITICAL invariants before modifying
- This file has 3 connections - changes may have domino effects
```

## License

MIT

## New Features ✨

### Enhanced CLI
- **Rich Markdown Output**: Beautiful formatted context with emojis and visual indicators
- **Compact Mode**: One-line context for quick checks (`--compact`)
- **Output to File**: Save context for later use (`-o file.md`)
- **Statistics Command**: View graph statistics (`palace stats`)
- **Query Command**: Execute raw Cypher queries (`palace query`)

### Improved Output
- 🟢🟡🔴 Risk levels with visual indicators
- 📊 Progress bars for activation energy
- ⚠️ Categorized invariants by severity
- 🔗 Topology visualization (depends/impacts/related)
- 📜 Historical ADR integration
- 🎯 Risk assessment with recommendations

### Better AI Integration
- **ClaudeFormatter**: Optimized Markdown for Claude Code
- **ContextBundle**: Enriched context structure
- **AGENTS.md**: Guide for AI assistant integration
- **Compact prompts**: Perfect for AI workflows

## Development
