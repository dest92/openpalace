# Glossary

This glossary defines key terms and concepts used in Palacio Mental.

## Core Concepts

### Artifact
A physical artifact in the codebase - files, functions, classes, or modules. Artifacts are the concrete elements that make up your code.

**Example:** The file `src/auth/login.py` is an Artifact. The `User` class in `models.py` is also an Artifact.

### Concept
An abstract idea or theme extracted from code. Concepts represent the semantic meaning behind the code - the "why" rather than the "what."

**Example:** "Authentication", "Database Connection", "Error Handling" are concepts. Multiple artifacts can evoke the same concept.

### Invariant
An architectural rule or constraint that should never be violated. Invariants represent best practices, security rules, or design principles.

**Example:** "User passwords must be hashed", "Database queries must use parameterized statements", "API endpoints must validate input".

### Decision (ADR)
An Architectural Decision Record - a captured decision about the codebase architecture. Decisions have status (PROPOSED, ACCEPTED, SUPERSEDED) and rationale.

**Example:** "We chose PostgreSQL over MySQL because of better JSON support", "We're migrating from monolith to microservices".

### Anchor
A spatial reference point used for topological navigation. Anchors help organize the codebase mentally in 3D space.

**Example:** "The authentication area", "The database layer", "The API gateway zone".

## Graph Structure

### Node
An entity in the knowledge graph. Can be a Concept, Artifact, Invariant, Decision, or Anchor.

### Edge
A relationship between two nodes. Edges have weights (0.0-1.0) that indicate strength of association.

### Edge Types

#### EVOKES
An **Artifact → Concept** edge indicating that the artifact embodies or represents this concept.

**Example:** `login.py` EVOKES `Authentication` with weight 0.9

#### DEPENDS_ON
An **Artifact → Artifact** edge indicating dependency between code elements.

**Example:** `auth_service.py` DEPENDS_ON `user_model.py` (type: IMPORT)

#### RELATED_TO
A **Concept → Concept** edge indicating semantic association between concepts.

**Example:** `Authentication` RELATED_TO `Security` with weight 0.8

#### CONSTRAINS
An **Invariant → Artifact** edge indicating that a rule applies to an artifact.

**Example:** "Must validate input" CONSTRAINS `api_handler.py` with strictness 1.0

#### PRECEDES
A **Decision → Decision** edge indicating temporal sequence of decisions.

**Example:** "Choose PostgreSQL" PRECEDES "Design schema migration strategy"

## Algorithms

### Spreading Activation
A cognitive navigation algorithm that simulates how neurons fire and activate connected neurons. Starting from a seed node, activation spreads through the graph along edges, with energy decaying at each hop.

**Key Parameters:**
- `max_depth`: Maximum number of hops to traverse
- `energy_threshold`: Minimum energy required to include a node
- `decay_factor`: How much energy is lost per hop (default 0.8)

**Transmission Factors by Edge Type:**
- CONSTRAINS: 1.0 (full transmission)
- EVOKES: 0.9 (strong transmission)
- DEPENDS_ON: 0.7 (moderate transmission)
- PRECEDES: 0.6 (weaker transmission)
- RELATED_TO: 0.5 (weakest transmission)

### Hebbian Learning
The principle that "neurons that fire together, wire together." When two nodes are frequently co-activated, their connection strengthens.

**Key Operations:**
- `reinforce_coactivation()`: Strengthen connections between co-activated nodes
- `punish_mistake()`: Weaken connections after errors
- Weight capping: Connections max out at 1.0
- Pruning: Connections below 0.1 are removed

### Sleep Cycle
A consolidation process that runs periodically to optimize memory. It applies exponential decay to edge weights based on time and prunes weak connections.

**Key Parameters:**
- `lambda_decay`: Rate of exponential decay (default 0.05)
- `prune_threshold`: Remove edges below this weight (default 0.1)

## Database Architecture

### Hippocampus
The main interface to both graph and vector databases. Named after the brain region responsible for memory formation.

**Components:**
- **KuzuDB**: Graph database storing nodes and edges
- **SQLite+vec**: Vector database storing embeddings

### Vector Embedding
A numerical representation of text that captures semantic meaning. Similar concepts have similar vectors.

**Details:**
- Model: `all-MiniLM-L6-v2` (sentence-transformers)
- Dimensions: 384
- Used for: Semantic similarity search, concept extraction

### Content Hash
SHA-256 hash of file contents, used to detect changes and create unique artifact IDs.

**Example:** `a3f5e2b1c4d8e7f0...`

### AST Fingerprint
Hash of the Abstract Syntax Tree structure, used to detect structural changes independent of formatting.

**Use Case:** Refactoring code without changing logic produces the same fingerprint.

## Ingestion Pipeline

### Parser
A language-specific code analyzer that extracts dependencies, symbols, and structure from source files.

**Available Parsers:**
- PythonParser: Uses Python's built-in `ast` module

**Extensions:** `.py`, `.pyx`

### Symbol
A named entity in code - function, class, method, variable.

**Example:** `def authenticate_user():` → Symbol with name "authenticate_user", type "function"

### Dependency
A reference from one artifact to another - imports, function calls, inheritance.

**Types:**
- `IMPORT`: Direct import statement
- `FUNCTION_CALL`: Calling a function from another module
- `INHERITANCE`: Class inheritance
- `COMPOSITION`: Has-a relationship

### Concept Extraction
The process of identifying abstract concepts from concrete code using NLP and embeddings.

**Process:**
1. Extract keywords from file paths and symbols
2. Generate embeddings for code snippets
3. Cluster similar embeddings to identify concepts
4. Assign confidence scores

### Invariant Detection
Automatic detection of anti-patterns and violations in code.

**Categories:**
- **Security**: Hardcoded secrets, eval usage, SQL injection risks
- **Architecture**: God objects, missing error handling, circular dependencies

**Severity Levels:**
- CRITICAL: Must fix immediately
- HIGH: Should fix soon
- MEDIUM: Nice to fix
- LOW: Minor issues

## CLI Commands

### palace init
Initialize a new Palace brain in the `.palace/` directory.

**Creates:**
- `.palace/brain.kuzu` - Graph database
- `.palace/vectors.db` - Vector database
- `.palace/config.toml` - Configuration (optional)

### palace ingest
Scan and parse code files to build the knowledge graph.

**Options:**
- `--file-pattern`: Glob pattern for files to ingest (default: `**/*.py`)

**Output:** Creates Artifact nodes, extracts Concepts, detects Invariants

### palace context
Get contextual information for a file, showing related code and concepts.

**Example:** `palace context src/auth/login.py`

**Returns:**
- Related artifacts (files that are semantically related)
- Related concepts (abstractions embodied by this file)
- Related invariants (rules that apply to this file)

### palace sleep
Run the consolidation and pruning cycle to optimize memory.

**Effects:**
- Decay weak connections
- Remove edges below threshold
- Consolidate frequently-used patterns

## Metrics and Scoring

### Activation Energy
A value (0.0-1.0) indicating how strongly a node is activated during spreading activation.

**Calculation:** `energy = initial_energy × edge_weight × decay_factor × transmission_factor`

### Edge Weight
Strength of connection between two nodes (0.0-1.0). Modified by Hebbian learning.

**Evolution:**
- Initial: 1.0 (new connections)
- Increases: When co-activated (Hebbian learning)
- Decreases: During sleep cycles (decay)
- Removed: When weight < 0.1

### Confidence Score
How strongly a concept is associated with code (0.0-1.0).

**Factors:**
- Frequency of concept occurrence
- Clustering quality
- Semantic similarity

### Risk Score
Computed by ContextProvider, indicates potential issues in code.

**Based on:**
- Number of invariant violations
- Severity of violations
- Connection strength to problematic areas

## Technical Terms

### BFS (Breadth-First Search)
The traversal algorithm used by spreading activation. Visits nodes level by level.

### Cypher
Query language for KuzuDB graph database (similar to SQL but for graphs).

**Example:** `MATCH (a:Artifact)-[r:EVOKES]->(c:Concept) WHERE a.path = "test.py" RETURN c.name`

### Deterministic ID
A unique identifier generated from content using hash functions. Same content always produces same ID.

**Format:**
- Artifacts: `artifact-{content_hash[:16]}`
- Concepts: `concept-{md5_hash}`
- Invariants: `invariant-{md5_hash}`

### Node Type
The category of a node in the graph (Concept, Artifact, Invariant, Decision, Anchor).

### Context Bundle
A collection of contextual information returned by ContextProvider, including related artifacts, concepts, and invariants.

## Design Patterns

### Context Manager
Python pattern for resource management. Palace uses `with Hippocampus(path) as hippo:` to ensure database connections close properly.

### Pipeline Pattern
The ingestion system uses a pipeline pattern where data flows through multiple stages:
1. File discovery
2. Parsing
3. Concept extraction
4. Invariant detection
5. Graph construction

### Strategy Pattern
Parser interface uses strategy pattern - different parsers can be swapped without changing pipeline logic.

## Development Terms

### Test Fixture
Test data and setup used across multiple tests. Palace uses fixtures for creating test brains with sample data.

### Coverage
Percentage of code executed by tests. Palace has 78% test coverage.

### Type Hints
Python type annotations for better IDE support and type checking. Palace uses strict mypy checking.

### Pydantic Model
Data validation library. All Palace models use Pydantic v2 for runtime validation.
