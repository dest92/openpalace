# Palacio Mental Neuro-Simbólico v2.0 - Design Document

**Date:** 2025-02-15
**Status:** Design Approved
**Author:** Claude (Architect)
**Version:** 1.0

---

## Executive Summary

Palacio Mental is a bio-mimetic cognitive memory system for code engineering teams. It serves as a "hippocampus digital" - an extended memory that provides architectural context during development planning. The system uses graph databases for spatial memory, vector embeddings for associative memory, and Hebbian learning for synaptic plasticity.

**Key Goals:**
- Provide architectural context to prevent design errors
- Preserve institutional knowledge beyond individual memory
- Enable cognitive navigation through codebases using spreading activation
- Support continuous learning through debate feedback

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  init    │  │  ingest  │  │  sleep   │  │ context  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼────────────┼────────────┼────────────┼────────────┘
        │            │            │            │
┌───────┴────────────┴────────────┴────────────┴─────────────┐
│                      API Layer                              │
│               ContextProvider + Validators                  │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────────┐
│                    Core Algorithms                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Hippocampus  │  │  Activation  │  │  Plasticity  │     │
│  │  (Graph DB)  │  │  (Spreading) │  │  (Hebbian)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐                                           │
│  │     Sleep    │                                           │
│  │ (Consolidate)│                                           │
│  └──────────────┘                                           │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────────┐
│                    Storage Layer                            │
│  ┌──────────────────┐        ┌──────────────────┐         │
│  │   KuzuDB Graph   │        │  SQLite + VEC    │         │
│  │  .palace/brain   │        │  .palace/vectors │         │
│  └──────────────────┘        └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Storage Layer (Hippocampus)

**File:** `palace/core/hippocampus.py`

**Responsibilities:**
- Initialize and manage KuzuDB graph database
- Initialize and manage SQLite+vec vector database
- Create and maintain graph schema
- Provide CRUD operations for nodes and edges
- Execute Cypher queries
- Store and retrieve embeddings
- Handle database connections and lifecycle

**Key Methods:**
```python
class Hippocampus:
    def __init__(self, palace_dir: Path)
    def create_node(self, node_type: str, properties: Dict) -> str
    def create_edge(self, src_id: str, dst_id: str, edge_type: str, properties: Dict)
    def get_node(self, node_id: str) -> Optional[Dict]
    def execute_cypher(self, query: str, params: Dict) -> List[Dict]
    def store_embedding(self, node_id: str, embedding: np.ndarray)
    def similarity_search(self, query_embedding: np.ndarray, top_k: int) -> List[Tuple[str, float]]
    def close(self)
```

**Schema:**

**Nodes:**
- `Concept`: `{id, name, embedding_id, layer, stability, created_at}`
- `Artifact`: `{id, path, content_hash, language, ast_fingerprint, last_modified}`
- `Invariant`: `{id, rule, severity, check_query, is_automatic, created_at}`
- `Decision`: `{id, title, timestamp, status, rationale, created_at}`
- `Anchor`: `{id, spatial_coords, description, created_at}`

**Edges:**
- `EVOKES`: `{weight, last_activated}` (Artifact → Concept)
- `CONSTRAINS`: `{strictness}` (Invariant → Artifact)
- `DEPENDS_ON`: `{weight, dependency_type}` (Artifact → Artifact)
- `PRECEDES`: `{reason}` (Decision → Decision)
- `RELATED_TO`: `{weight}` (Concept → Concept)

---

### 2. Spreading Activation Engine

**File:** `palace/core/activation.py`

**Responsibilities:**
- Implement spreading activation algorithm
- Simulate neural firing across the graph
- Weight energy transmission by edge type
- Handle cycles with visited tracking
- Update edge activation timestamps

**Algorithm:**
```
1. Initialize queue with seed_node at energy = 1.0
2. While queue not empty:
   a. Pop node, add to results
   b. For each outgoing edge:
      - Calculate transmitted energy: E_next = E_current * edge_weight * decay_factor * transmission_factor
      - If E_next > threshold: add neighbor to queue
3. Return results sorted by energy
```

**Edge Transmission Factors:**
- `CONSTRAINS`: 1.0 (highest priority)
- `EVOKES`: 0.9
- `DEPENDS_ON`: 0.7
- `PRECEDES`: 0.6
- `RELATED_TO`: 0.5

---

### 3. Hebbian Plasticity Engine

**File:** `palace/core/plasticity.py`

**Responsibilities:**
- Implement synaptic strengthening (coactivation)
- Implement synaptic weakening (mistake punishment)
- Create new edges when none exist
- Enforce weight bounds (0.0 - 1.0)

**Hebbian Learning:**
```python
def reinforce_coactivation(node_set: Set[str], learning_rate: float):
    for (node_a, node_b) in all_pairs(node_set):
        if edge_exists:
            weight += learning_rate
        else:
            create_edge(weight=learning_rate)
        weight = min(weight, 1.0)
```

---

### 4. Sleep Cycle Engine

**File:** `palace/core/sleep.py`

**Responsibilities:**
- Implement exponential decay: `w = w * exp(-λ * Δt)`
- Prune weak edges (weight < threshold)
- Detect communities using Louvain algorithm
- Create spatial Anchor nodes for communities
- Reindex stale embeddings
- Return sleep statistics

**Sleep Process:**
1. Decay all edges by time since last activation
2. Remove edges below prune threshold
3. Run community detection
4. Create Anchor nodes for significant clusters
5. Update embeddings for modified nodes
6. Return SleepReport with statistics

---

### 5. Ingestion System

#### 5.1 AST Parsers

**Files:** `palace/ingest/parsers/base.py`, `palace/ingest/parsers/python.py`, etc.

**Responsibilities:**
- Parse source code using tree-sitter
- Extract dependencies (imports, requires)
- Extract symbols (functions, classes, constants)
- Compute AST fingerprints for change detection
- Handle parse errors gracefully

**Supported Languages:**
- Python (tree-sitter-python)
- TypeScript/JavaScript (tree-sitter-typescript)
- Rust (tree-sitter-rust)
- Go (tree-sitter-go)
- Generic fallback (regex-based for markdown, config files)

#### 5.2 Concept Extractor

**File:** `palace/ingest/extractors.py`

**Responsibilities:**
- Extract semantic concepts from code
- Use sentence-transformers for embeddings
- Cluster similar concepts using cosine similarity
- Create Concept nodes in graph

**Extraction Methods:**
1. TF-IDF like keyword extraction
2. Embedding-based clustering
3. Symbol name analysis
4. Docstring parsing

#### 5.3 Invariant Detector

**File:** `palace/ingest/invariants.py`

**Responsibilities:**
- Detect security anti-patterns
- Detect architectural violations
- Create Invariant nodes linked to artifacts

**Detection Rules:**
- Security: Hardcoded secrets, eval usage, SQL injection risks
- Architecture: God objects, circular imports, missing error handling
- Performance: N+1 queries, missing indexes
- Code quality: Duplication, excessive complexity

#### 5.4 Big Bang Pipeline

**File:** `palace/ingest/pipeline.py`

**Responsibilities:**
- Orchestrate complete ingestion process
- Scan repository files
- Parse each artifact
- Extract concepts and invariants
- Build graph structure
- Compute and store embeddings
- Return ingestion statistics

**Process Flow:**
```
Repository Files
    ↓
Filter (ignore patterns)
    ↓
For each file:
    Parse AST → Extract dependencies & symbols
    ↓
    Extract concepts → Create Concept nodes
    ↓
    Detect invariants → Create Invariant nodes
    ↓
    Create Artifact node + edges
    ↓
    Compute embedding → Store in sqlite-vec
    ↓
Return IngestReport
```

---

### 6. API Layer

**File:** `palace/api/context_provider.py`

**Responsibilities:**
- Retrieve architectural context for queries
- Validate proposals against invariants
- Find related artifacts by edge type
- Assemble ContextBundle objects

**Key Methods:**
```python
class ContextProvider:
    def retrieve(target_file: str, query_embedding: Optional[np.ndarray]) -> ContextBundle
    def validate_proposal(proposal_text: str, affected_files: List[str]) -> List[Violation]
    def get_related_artifacts(artifact_path: str, relation_type: str) -> List[Tuple[str, float]]
```

**ContextBundle Structure:**
```python
@dataclass
class ContextBundle:
    invariants: List[Invariant]
    active_concepts: List[Concept]
    relevant_decisions: List[Decision]
    topological_neighbors: List[Artifact]
    risk_score: float
    activation_energy: float
    timestamp: datetime
```

---

### 7. CLI Interface

**File:** `palace/cli/commands.py` (using Typer)

**Commands:**
- `palace init` - Initialize .palace/ directory with empty databases
- `palace ingest` - Execute Big Bang ingestion on repository
- `palace sleep` - Run sleep cycle for consolidation
- `palace context <file>` - Retrieve architectural context
- `palace query <cypher>` - Execute raw Cypher query
- `palace stats` - Show brain statistics

---

### 8. Data Models

**File:** `palace/shared/models.py`

All models use Pydantic for type safety and validation:

```python
class Concept(BaseModel):
    id: str
    name: str
    embedding_id: str
    layer: str  # abstraction, implementation, infrastructure
    stability: float

class Artifact(BaseModel):
    id: str
    path: str
    content_hash: str
    language: str
    ast_fingerprint: str

class Invariant(BaseModel):
    id: str
    rule: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    check_query: Optional[str]
    is_automatic: bool
```

---

## Error Handling Strategy

### Exception Hierarchy

```
PalaceError (base)
├── DatabaseError
│   ├── ConnectionError
│   └── SchemaError
├── IngestionError
│   ├── ParseError
│   └── UnsupportedLanguageError
├── ActivationError
├── PlasticityError
└── CLIError
    └── PalaceNotInitializedError
```

### Error Handling Patterns

- **Retriable operations**: Use `tenacity` for database operations
- **User-friendly messages**: Convert internal errors to clear CLI output
- **Graceful degradation**: Skip unsupported files during ingestion
- **Detailed logging**: Log technical errors for debugging

---

## Testing Strategy

### Test Structure

```
tests/
├── unit/              # >90% coverage target
│   ├── test_core/
│   ├── test_ingest/
│   ├── test_api/
│   └── test_shared/
├── integration/       # >70% coverage target
│   ├── test_full_ingestion.py
│   ├── test_spreading_activation_e2e.py
│   └── test_sleep_cycle_e2e.py
├── fixtures/
│   ├── repos/         # Sample repos for testing
│   └── brains/        # Pre-ingested databases
└── conftest.py        # Shared fixtures
```

### Key Test Cases

**Unit Tests:**
- Schema creation and CRUD operations
- Spreading activation with various parameters
- Hebbian learning and weight capping
- Parser dependency extraction for each language
- Context bundle assembly

**Integration Tests:**
- Full ingestion on sample repos
- End-to-end spreading activation
- Complete sleep cycle execution

**Coverage Target:** >80% overall

---

## Dependencies

### Core Dependencies

```
python = "^3.10"
kuzu = "^0.5.0"                    # Graph database
sqlite-vec = "^0.1.0"              # Vector extension
sentence-transformers = "^2.2.0"   # Embeddings
tree-sitter = "^0.20.0"            # AST parsing
tree-sitter-python = "^0.20.0"
tree-sitter-typescript = "^0.20.0"
tree-sitter-rust = "^0.20.0"
tree-sitter-go = "^0.20.0"
numpy = "^1.24.0"
typer = "^0.9.0"                   # CLI framework
pydantic = "^2.0.0"                # Data validation
pydantic-settings = "^2.0.0"       # Configuration
tenacity = "^8.2.0"                # Retry logic
python-dotenv = "^1.0.0"
```

### Development Dependencies

```
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.0"
mypy = "^1.5.0"                    # Type checking
black = "^23.7.0"                  # Code formatting
ruff = "^0.0.280"                  # Fast linter
pre-commit = "^3.3.0"
```

---

## Configuration

**File:** `palace/shared/config.py`

Configuration loaded from environment variables and `.palace/config.toml`:

```python
class PalaceConfig(BaseSettings):
    palace_dir: Path = Path(".palace")
    repo_root: Path = Path(".")
    ignore_patterns: List[str] = [...]
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    default_max_depth: int = 3
    default_energy_threshold: float = 0.3
    default_decay_factor: float = 0.8
    default_lambda_decay: float = 0.05
    default_prune_threshold: float = 0.1

    class Config:
        env_prefix = "PALACE_"
```

---

## Directory Structure

```
palace_engine/
├── palace/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── hippocampus.py
│   │   ├── activation.py
│   │   ├── plasticity.py
│   │   └── sleep.py
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── python.py
│   │   │   ├── typescript.py
│   │   │   ├── rust.py
│   │   │   └── go.py
│   │   ├── extractors.py
│   │   ├── invariants.py
│   │   └── pipeline.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── context_provider.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py
│   └── shared/
│       ├── __init__.py
│       ├── models.py
│       ├── exceptions.py
│       └── config.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── conftest.py
├── docs/
│   └── plans/
│       └── 2025-02-15-palacio-mental-v2-design.md
├── pyproject.toml
├── README.md
└── .palace/              # Generated, not in git
    ├── brain.kuzu
    ├── vectors.db
    └── decisions/
```

---

## Development Approach

**Strategy:** Layer-by-layer sequential development

1. **Foundation** (Hippocampus + Models)
   - Setup project structure
   - Implement data models (Pydantic)
   - Create Hippocampus class
   - Initialize KuzuDB schema
   - Initialize SQLite+vec schema

2. **Core Algorithms**
   - Implement SpreadingActivation
   - Implement PlasticityEngine
   - Implement SleepEngine
   - Test each algorithm independently

3. **Ingestion System**
   - Implement BaseParser interface
   - Create language-specific parsers
   - Implement ConceptExtractor
   - Implement InvariantDetector
   - Create BigBangPipeline

4. **API Layer**
   - Implement ContextProvider
   - Implement query validation
   - Create ContextBundle assembler

5. **CLI Interface**
   - Implement all commands using Typer
   - Add formatters for output
   - Create markdown output generator

6. **Testing & Documentation**
   - Write comprehensive tests
   - Create README with quickstart
   - Add inline algorithm comments
   - Create demo repository example

---

## Success Criteria

**Definition of Done:**
- ✅ All core components implemented and tested
- ✅ `palace init` creates functional brain with schema
- ✅ `palace ingest` processes repos creating >50 nodes in <30s
- ✅ `palace context` returns relevant invariants via spreading activation
- ✅ `palace sleep` decreases unused edge weights by >10%
- ✅ CLI commands provide user-friendly error messages
- ✅ Test coverage >80% overall
- ✅ Full README with quickstart guide
- ✅ Demo repo (FastAPI or similar) showing Palace capabilities
- ✅ All algorithms documented with inline comments

**Performance Targets:**
- Ingestion: <30s for small repo (100 files)
- Context retrieval: <2s for typical query
- Sleep cycle: <5s for medium graph

---

## Future Enhancements (Post-v1.0)

- MCP (Model Context Protocol) server implementation
- Web dashboard for visualization
- Additional language parsers (Java, C++, Ruby)
- Local LLM integration for advanced concept extraction
- Real-time graph updates via git hooks
- Export/import functionality for brain portability
- Distributed version for team synchronization

---

## Appendix: Algorithm Details

### Spreading Activation Algorithm

```python
def spreading_activation(
    seed_node_id: str,
    max_depth: int = 3,
    energy_threshold: float = 0.15,
    decay_factor: float = 0.8
) -> Dict[str, float]:
    """
    BFS with weighted energy propagation.

    Pseudocode:
    1. Initialize: queue = [(seed_node, 1.0)], visited = set()
    2. While queue not empty:
       - Pop (node_id, energy)
       - Add node_id to results with energy
       - For each outgoing edge:
         * Calculate transmitted_energy = energy * edge_weight * decay_factor * transmission_factor
         * If transmitted_energy > threshold AND neighbor not visited:
           - Add (neighbor, transmitted_energy) to queue
           - Mark neighbor as visited
    3. Return results sorted by energy (descending)
    """
```

### Hebbian Learning

```python
def reinforce_coactivation(node_set: Set[str], learning_rate: float = 0.1):
    """
    Strengthen connections between co-activated nodes.

    For each pair (a, b) in node_set:
        if edge exists:
            edge.weight = min(1.0, edge.weight + learning_rate)
        else:
            create RELATED_TO edge from a to b with weight = learning_rate
        update last_activated timestamp
    """
```

### Sleep Cycle Decay

```python
def decay_edge_weights(edge, lambda_decay: float, current_time: datetime):
    """
    Apply exponential decay based on time since last activation.

    delta_t = (current_time - edge.last_activated).total_seconds()
    decay_factor = exp(-lambda_decay * delta_t / 86400)  # Normalize to days
    edge.weight = edge.weight * decay_factor
    """
```

---

**Document Status:** ✅ Approved
**Next Step:** Invoke writing-plans skill to create implementation plan
