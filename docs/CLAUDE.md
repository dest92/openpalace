# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Palacio Mental is a bio-mimetic cognitive memory system for code engineering teams using graph databases, vector embeddings, and Hebbian learning algorithms. It combines spatial memory (KuzuDB graph database) with associative memory (SQLite+vec vector database) to create an AI-assisted code understanding and navigation system.

## Common Development Commands

```bash
# Install dependencies
poetry install

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_core/test_hippocampus.py

# Run tests with coverage
pytest --cov=palace --cov-report=html

# Type checking
mypy palace/

# Format code
black palace/

# Lint code
ruff check palace/

# Run the CLI (after poetry install)
palace init                    # Initialize Palace brain in .palace/
palace ingest                  # Ingest Python files into knowledge graph
palace context <file>          # Get architectural context for a file
palace sleep                   # Run consolidation and pruning cycle
```

## High-Level Architecture

The system is organized into four main layers:

### 1. Storage Layer (`palace/core/hippocampus.py`)
- **Hippocampus**: Main interface managing both KuzuDB (graph) and SQLite+vec (vectors)
- Uses KuzuDB for structured graph data with 5 node types (Concept, Artifact, Invariant, Decision, Anchor) and 5 edge types (EVOKES, DEPENDS_ON, CONSTRAINS, PRECEDES, RELATED_TO)
- Uses SQLite+vec for 384-dimensional vector embeddings (sentence-transformers)
- All node IDs are deterministic hash-based IDs
- Important: KuzuDB 0.5.0 has specific API requirements - no `TYPE()` function, parameterized queries use `$param` syntax

### 2. Core Algorithms (`palace/core/`)

**ActivationEngine** (`activation.py`): Spreading activation for cognitive navigation
- BFS traversal with configurable depth, energy threshold, and decay factor
- Edge-type-specific transmission factors (CONSTRAINS=1.0, EVOKES=0.9, DEPENDS_ON=0.7, etc.)
- Returns nodes ranked by activation energy

**PlasticityEngine** (`plasticity.py`): Hebbian learning ("neurons that fire together, wire together")
- `reinforce_coactivation()`: Strengthens connections between co-activated nodes
- `punish_mistake()`: Weakens connections after errors
- Weights capped at 1.0, edges removed when weight < 0.1

**SleepEngine** (`sleep.py`): Consolidation and forgetting
- Exponential decay of edge weights over time
- Prunes weak edges below threshold
- Returns SleepReport with statistics

### 3. Ingestion Pipeline (`palace/ingest/`)

**Parsers** (`parsers/`): Abstract base class with Python implementation
- Uses Python AST (not tree-sitter) for parsing Python code
- Extracts: imports/dependencies, functions, classes, methods
- Computes AST fingerprints for change detection

**BigBangPipeline** (`pipeline.py`): Orchestrates complete ingestion
- Finds appropriate parser for each file type
- Creates Artifact nodes with content hashes
- Optionally extracts concepts using NLP (ConceptExtractor)
- Detects architectural violations (InvariantDetector)
- Returns IngestReport with statistics

### 4. API & CLI (`palace/api/`, `palace/cli/`)

**ContextProvider** (`api/context.py`): LLM assistance interface
- Uses spreading activation to find related code
- Assembles ContextBundle with artifacts, concepts, and invariants
- Computes risk scores

**CLI** (`cli/commands.py`): Typer-based command interface
- `init`, `ingest`, `context`, `sleep` commands
- Raises `PalaceNotInitializedError` if `.palace/` doesn't exist

## Data Models (`palace/shared/models.py`)

All models use Pydantic v2 with strict validation:

- **Node types**: Concept (semantic), Artifact (code), Invariant (rules), Decision (ADRs), Anchor (spatial)
- **Edge types**: EvokesEdge, DependsOnEdge, ConstrainsEdge, RelatedToEdge, PrecedesEdge
- All edges have `weight` (0.0-1.0) for learning algorithms

## Configuration (`palace/shared/config.py`)

- Environment variables prefixed with `PALACE_`
- Config file at `.palace/config.toml` (optional)
- Default ignore patterns for ingestion (node_modules, .git, __pycache__, etc.)
- Embedding model: all-MiniLM-L6-v2 (384 dimensions)

## Important Implementation Notes

1. **KuzuDB API Compatibility**: Version 0.5.0 doesn't support `TYPE()` function - must query each edge type separately
2. **Vector storage**: Currently uses byte serialization (`tobytes()`) - similarity search is computed in Python (TODO: proper sqlite-vec implementation)
3. **Context management**: Always use `with Hippocampus(path) as hippo:` to ensure connections close properly
4. **Test coverage**: Currently 78% (625 statements) - integration tests for API/CLI needed
5. **Python parser**: Uses stdlib `ast` module, not tree-sitter (despite original design docs)

## Testing Structure

```
tests/
├── unit/test_core/       # ActivationEngine, PlasticityEngine, SleepEngine, Hippocampus
├── unit/test_ingest/     # Parsers, pipeline, extractors, invariants
├── unit/test_api/        # ContextProvider
├── unit/test_shared/     # Models, exceptions, config
└── integration/          # End-to-end workflows
```

## Working with the Codebase

When modifying core algorithms:
- Test thoroughly with `pytest tests/unit/test_core/`
- Respect edge transmission factors in ActivationEngine
- Remember weight capping (1.0) and pruning threshold (0.1) in PlasticityEngine

When extending ingestion:
- Inherit from `BaseParser` in `parsers/base.py`
- Register parser in `BigBangPipeline.__init__`
- Update `_get_language()` mapping in pipeline

When adding CLI commands:
- Use Typer for command definition
- Check for PalaceNotInitializedError
- Use Hippocampus context manager for database operations
