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
palace init
```

### Ingest Code

```bash
# Ingest all Python files
palace ingest

# Ingest specific pattern
palace ingest --file-pattern "src/**/*.py"
```

### Get Context

```bash
# Get contextual information for a file
palace context src/auth.py
```

### Run Sleep Cycle

```bash
# Run consolidation and pruning
palace sleep
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

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=palace --cov-report=html
```

### Type Checking

```bash
mypy palace/
```

### Code Quality

```bash
# Format code
black palace/

# Lint code
ruff check palace/
```

## License

MIT

## Status

**Phase 1**: Foundation (Models & Configuration) ✅
**Phase 2**: Storage Layer (Hippocampus) ✅
**Phase 3**: Core Algorithms ✅
**Phase 4**: Ingestion System ✅
**Phase 5**: API & CLI ✅
**Phase 6**: Documentation & Testing (In Progress)

Current test coverage: 39 passing tests
