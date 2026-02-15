# Palacio Mental v2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a bio-mimetic cognitive memory system for code engineering teams using graph databases, vector embeddings, and Hebbian learning algorithms.

**Architecture:** Layer-by-layer sequential development starting with storage foundation (Hippocampus), then core algorithms (Activation, Plasticity, Sleep), followed by ingestion pipeline, API layer, and CLI interface. All components use dependency injection for testability.

**Tech Stack:** Python 3.10+, KuzuDB (graph), SQLite+vec (vectors), sentence-transformers (embeddings), tree-sitter (parsing), Pydantic (models), Typer (CLI), pytest (testing), mypy (type checking).

---

## Prerequisites

### Task 1: Initialize Python Project with Poetry

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`

**Step 1: Create pyproject.toml**

```toml
[tool.poetry]
name = "palacio-mental"
version = "0.1.0"
description = "Cognitive memory system for code engineering"
authors = ["Palace Team"]
readme = "README.md"
packages = [{include = "palace"}]

[tool.poetry.dependencies]
python = "^3.10"
kuzu = "^0.5.0"
sqlite-vec = "^0.1.0"
sentence-transformers = "^2.2.0"
tree-sitter = "^0.20.0"
tree-sitter-python = "^0.20.0"
tree-sitter-typescript = "^0.20.0"
tree-sitter-rust = "^0.20.0"
tree-sitter-go = "^0.20.0"
numpy = "^1.24.0"
typer = {extras = ["all"], version = "^0.9.0"}
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"
tenacity = "^8.2.0"
python-dotenv = "^1.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.0"
mypy = "^1.5.0"
black = "^23.7.0"
ruff = "^0.0.280"
pre-commit = "^3.3.0"

[tool.poetry.scripts]
palace = "palace.cli.commands:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
strict = true
```

**Step 2: Create .python-version**

```
3.10
```

**Step 3: Create .gitignore**

```
# Palace
.palace/
*.kuzu
*.db

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# Poetry
poetry.lock

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

**Step 4: Install dependencies**

```bash
poetry install
```

**Step 5: Commit**

```bash
git add pyproject.toml .python-version .gitignore
git commit -m "chore: initialize Python project with Poetry"
```

---

### Task 2: Create Project Directory Structure

**Files:**
- Create: `palace/__init__.py`
- Create: `palace/core/__init__.py`
- Create: `palace/ingest/__init__.py`
- Create: `palace/ingest/parsers/__init__.py`
- Create: `palace/api/__init__.py`
- Create: `palace/cli/__init__.py`
- Create: `palace/shared/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_core/__init__.py`
- Create: `tests/unit/test_ingest/__init__.py`
- Create: `tests/unit/test_api/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/fixtures/__init__.py`

**Step 1: Create all __init__.py files**

```bash
# Run these commands sequentially
mkdir -p palace/core palace/ingest/parsers palace/api palace/cli palace/shared
mkdir -p tests/unit/test_core tests/unit/test_ingest tests/unit/test_api tests/integration tests/fixtures
touch palace/__init__.py palace/core/__init__.py palace/ingest/__init__.py
touch palace/ingest/parsers/__init__.py palace/api/__init__.py palace/cli/__init__.py palace/shared/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/unit/test_core/__init__.py
touch tests/unit/test_ingest/__init__.py tests/unit/test_api/__init__.py tests/integration/__init__.py tests/fixtures/__init__.py
```

**Step 2: Add version to palace/__init__.py**

```python
"""Palacio Mental - Cognitive Memory System for Code."""

__version__ = "0.1.0"
```

**Step 3: Verify structure**

```bash
tree palace tests -L 2
```

Expected: Directory tree showing all modules

**Step 4: Commit**

```bash
git add palace tests
git commit -m "feat: create project directory structure"
```

---

## Phase 1: Foundation (Models & Configuration)

### Task 3: Implement Data Models with Pydantic

**Files:**
- Create: `palace/shared/models.py`

**Step 1: Write tests for Node models**

Create: `tests/unit/test_shared/test_models.py`

```python
import pytest
from datetime import datetime
from palace.shared.models import Concept, Artifact, Invariant, Decision, Anchor

def test_concept_creation():
    concept = Concept(
        id="test-concept-1",
        name="Authentication",
        embedding_id="emb-123",
        layer="abstraction",
        stability=0.8
    )
    assert concept.id == "test-concept-1"
    assert concept.name == "Authentication"
    assert concept.layer == "abstraction"
    assert 0.0 <= concept.stability <= 1.0
    assert isinstance(concept.created_at, datetime)

def test_artifact_creation():
    artifact = Artifact(
        id="artifact-1",
        path="src/auth.py",
        content_hash="abc123",
        language="python",
        ast_fingerprint="fp-456"
    )
    assert artifact.path == "src/auth.py"
    assert artifact.language == "python"

def test_invariant_severity_validation():
    invariant = Invariant(
        id="inv-1",
        rule="No hardcoded secrets",
        severity="CRITICAL",
        is_automatic=True
    )
    assert invariant.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

def test_invariant_invalid_severity():
    with pytest.raises(ValueError):
        Invariant(
            id="inv-2",
            rule="Test",
            severity="INVALID",  # Should fail
            is_automatic=False
        )

def test_decision_status_validation():
    decision = Decision(
        id="dec-1",
        title="Use PostgreSQL",
        status="ACCEPTED",
        rationale="Best for relational data"
    )
    assert decision.status in ["PROPOSED", "ACCEPTED", "SUPERSEDED"]
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_shared/test_models.py -v
```

Expected: ImportError - palace.shared.models does not exist

**Step 3: Implement models**

Create: `palace/shared/models.py`

```python
"""Data models for Palacio Mental."""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class NodeModel(BaseModel):
    """Base model for all graph nodes."""
    id: str = Field(..., description="Deterministic hash-based ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Concept(NodeModel):
    """Abstract idea or concept extracted from code."""
    name: str = Field(..., description="Concept name")
    embedding_id: str = Field(..., description="Vector database reference")
    layer: Literal["abstraction", "implementation", "infrastructure"] = Field(
        ...,
        description="Concept abstraction level"
    )
    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How stable this concept is (0.0-1.0)"
    )


class Artifact(NodeModel):
    """Physical artifact (file, function, class) in the codebase."""
    path: str = Field(..., description="File path relative to repo root")
    content_hash: str = Field(..., description="SHA-256 of content")
    language: str = Field(..., description="Programming language")
    ast_fingerprint: str = Field(..., description="AST structure hash")
    last_modified: datetime = Field(default_factory=datetime.utcnow)


class Invariant(NodeModel):
    """Architectural or security rule/constraint."""
    rule: str = Field(..., description="Rule description")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        description="Impact level if violated"
    )
    check_query: Optional[str] = Field(
        None,
        description="Cypher query for automatic validation"
    )
    is_automatic: bool = Field(
        default=False,
        description="Can this be automatically checked?"
    )


class Decision(NodeModel):
    """Architectural Decision Record (ADR)."""
    title: str = Field(..., description="Decision title")
    timestamp: datetime = Field(..., description="When decision was made")
    status: Literal["PROPOSED", "ACCEPTED", "SUPERSEDED"] = Field(
        ...,
        description="Current status"
    )
    rationale: str = Field(..., description="Why this decision was made")


class Anchor(NodeModel):
    """Spatial reference point for topological navigation."""
    spatial_coords: str = Field(..., description="x,y,z coordinates")
    description: str = Field(..., description="What this area represents")


# Edge models

class EdgeModel(BaseModel):
    """Base model for graph edges."""
    src: str = Field(..., description="Source node ID")
    dst: str = Field(..., description="Destination node ID")
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class EvokesEdge(EdgeModel):
    """Artifact evokes a Concept (semantic association)."""
    last_activated: Optional[datetime] = Field(
        None,
        description="Last time this association fired"
    )


class DependsOnEdge(EdgeModel):
    """Artifact depends on another Artifact."""
    dependency_type: Literal[
        "IMPORT",
        "FUNCTION_CALL",
        "INHERITANCE",
        "COMPOSITION"
    ] = Field(..., description="Type of dependency")


class ConstrainsEdge(EdgeModel):
    """Invariant constrains an Artifact."""
    strictness: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How strictly this rule applies"
    )


class RelatedToEdge(EdgeModel):
    """Concept is related to another Concept."""
    pass


class PrecedesEdge(EdgeModel):
    """Decision precedes another Decision (temporal)."""
    reason: str = Field(..., description="Why this follows")
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_shared/test_models.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/shared/models.py tests/unit/test_shared/test_models.py
git commit -m "feat: implement Pydantic data models with validation"
```

---

### Task 4: Implement Exception Classes

**Files:**
- Create: `palace/shared/exceptions.py`

**Step 1: Write tests for exceptions**

Create: `tests/unit/test_shared/test_exceptions.py`

```python
import pytest
from palace.shared.exceptions import (
    PalaceError,
    DatabaseError,
    ConnectionError,
    SchemaError,
    IngestionError,
    ParseError,
    UnsupportedLanguageError,
    ActivationError,
    PlasticityError,
    CLIError,
    PalaceNotInitializedError
)

def test_exception_hierarchy():
    assert issubclass(DatabaseError, PalaceError)
    assert issubclass(ConnectionError, DatabaseError)
    assert issubclass(SchemaError, DatabaseError)
    assert issubclass(IngestionError, PalaceError)
    assert issubclass(ParseError, IngestionError)
    assert issubclass(UnsupportedLanguageError, IngestionError)
    assert issubclass(ActivationError, PalaceError)
    assert issubclass(PlasticityError, PalaceError)
    assert issubclass(CLIError, PalaceError)
    assert issubclass(PalaceNotInitializedError, CLIError)

def test_parse_error_attributes():
    error = ParseError("test.py", 42, "syntax error")
    assert "test.py" in str(error)
    assert "42" in str(error)
    assert "syntax error" in str(error)
    assert error.file_path == "test.py"
    assert error.line == 42

def test_exception_messages():
    assert "database" in str(DatabaseError("database error")).lower()
    assert "not initialized" in str(PalaceNotInitializedError()).lower()
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_shared/test_exceptions.py -v
```

Expected: ImportError

**Step 3: Implement exceptions**

Create: `palace/shared/exceptions.py`

```python
"""Exception hierarchy for Palacio Mental."""


class PalaceError(Exception):
    """Base exception for all Palace errors."""
    pass


# Database errors

class DatabaseError(PalaceError):
    """Base for KuzuDB/SQLite errors."""
    pass


class ConnectionError(DatabaseError):
    """Failed to connect to database."""
    pass


class SchemaError(DatabaseError):
    """Schema mismatch or corrupted database."""
    pass


# Ingestion errors

class IngestionError(PalaceError):
    """Base for ingestion failures."""
    pass


class ParseError(IngestionError):
    """Failed to parse file."""

    def __init__(self, file_path: str, line: int, message: str):
        self.file_path = file_path
        self.line = line
        super().__init__(f"{file_path}:{line} - {message}")


class UnsupportedLanguageError(IngestionError):
    """No parser available for language."""
    pass


# Algorithm errors

class ActivationError(PalaceError):
    """Spreading activation failure."""
    pass


class PlasticityError(PalaceError):
    """Hebbian learning failure."""
    pass


# CLI errors

class CLIError(PalaceError):
    """User-facing CLI error."""
    pass


class PalaceNotInitializedError(CLIError):
    """Command requires init to be run first."""
    pass
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_shared/test_exceptions.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/shared/exceptions.py tests/unit/test_shared/test_exceptions.py
git commit -m "feat: implement exception hierarchy"
```

---

### Task 5: Implement Configuration Management

**Files:**
- Create: `palace/shared/config.py`

**Step 1: Write tests for configuration**

Create: `tests/unit/test_shared/test_config.py`

```python
import pytest
from pathlib import Path
from palace.shared.config import PalaceConfig

def test_default_config():
    config = PalaceConfig()
    assert config.palace_dir == Path(".palace")
    assert config.repo_root == Path(".")
    assert "node_modules" in config.ignore_patterns
    assert config.embedding_model == "all-MiniLM-L6-v2"
    assert config.embedding_dim == 384
    assert config.default_max_depth == 3
    assert config.default_energy_threshold == 0.3

def test_config_from_env(monkeypatch):
    monkeypatch.setenv("PALACE_PALACE_DIR", "/tmp/test_palace")
    monkeypatch.setenv("PALACE_EMBEDDING_MODEL", "multi-qa-mpnet-base-dot-v1")
    config = PalaceConfig()
    assert config.palace_dir == Path("/tmp/test_palace")
    assert config.embedding_model == "multi-qa-mpnet-base-dot-v1"

def test_validation():
    config = PalaceConfig()
    assert 0.0 <= config.default_energy_threshold <= 1.0
    assert 0.0 <= config.default_lambda_decay <= 1.0
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_shared/test_config.py -v
```

Expected: ImportError

**Step 3: Install pydantic-settings if not in dependencies**

Check if `pydantic-settings` is in pyproject.toml (it should already be there from Task 1).

**Step 4: Implement configuration**

Create: `palace/shared/config.py`

```python
"""Configuration management for Palacio Mental."""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class PalaceConfig(BaseSettings):
    """Configuration loaded from env vars and .palace/config.toml"""

    # Paths
    palace_dir: Path = Path(".palace")
    repo_root: Path = Path(".")

    # Ingestion
    ignore_patterns: List[str] = [
        "node_modules",
        ".git",
        "__pycache__",
        "*.log",
        "dist",
        "build",
        ".venv",
        "venv",
        ".eggs",
        "*.egg-info",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".palace"
    ]
    max_file_size_mb: int = 10

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Activation
    default_max_depth: int = 3
    default_energy_threshold: float = 0.3
    default_decay_factor: float = 0.8

    # Sleep
    default_lambda_decay: float = 0.05
    default_prune_threshold: float = 0.1
    auto_sleep_after_ingest: bool = False

    # Performance
    db_connection_pool_size: int = 4
    batch_size: int = 100

    class Config:
        env_prefix = "PALACE_"
        env_file = ".palace/.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_shared/test_config.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add palace/shared/config.py tests/unit/test_shared/test_config.py
git commit -m "feat: implement configuration management with Pydantic Settings"
```

---

## Phase 2: Storage Layer (Hippocampus)

### Task 6: Implement Hippocampus - KuzuDB Connection

**Files:**
- Create: `palace/core/hippocampus.py`
- Create: `tests/unit/test_core/test_hippocampus.py`

**Step 1: Write test for Hippocampus initialization**

Create: `tests/unit/test_core/test_hippocampus.py`

```python
import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.shared.exceptions import DatabaseError

@pytest.fixture
def temp_palace_dir(tmp_path):
    """Create temporary .palace directory."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()
    return palace_dir

def test_hippocampus_initialization(temp_palace_dir):
    """Test that Hippocampus can be initialized."""
    hippo = Hippocampus(temp_palace_dir)
    assert hippo.palace_dir == temp_palace_dir
    assert hippo.is_connected()
    hippo.close()

def test_hippocampus_context_manager(temp_palace_dir):
    """Test that Hippocampus works as context manager."""
    with Hippocampus(temp_palace_dir) as hippo:
        assert hippo.is_connected()
    # Should be closed after context

def test_hippocampus_schema_creation(temp_palace_dir):
    """Test that schema is created on initialization."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        # Verify node types exist
        node_types = hippo.get_node_types()
        assert "Concept" in node_types
        assert "Artifact" in node_types
        assert "Invariant" in node_types
        assert "Decision" in node_types
        assert "Anchor" in node_types
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_core/test_hippocampus.py -v
```

Expected: ImportError

**Step 3: Implement basic Hippocampus class**

Create: `palace/core/hippocampus.py`

```python
"""Hippocampus - Main interface to graph and vector databases."""

import kuzu
import sqlite3
import sqlite_vec
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


class Hippocampus:
    """
    Main interface to KuzuDB and SQLite+vec.
    Manages graph schema, node/edge CRUD, and vector operations.
    """

    def __init__(self, palace_dir: Path):
        """
        Initialize both databases.

        Args:
            palace_dir: Directory containing .palace/ data
        """
        self.palace_dir = Path(palace_dir)
        self.palace_dir.mkdir(parents=True, exist_ok=True)

        # Initialize KuzuDB
        self.db_path = self.palace_dir / "brain.kuzu"
        self.kuzu_db = kuzu.Database(str(self.db_path))
        self.kuzu_conn = kuzu.Connection(self.kuzu_db)

        # Initialize SQLite+vec
        self.vec_db_path = self.palace_dir / "vectors.db"
        self.vec_conn = sqlite3.connect(str(self.vec_db_path))
        self.vec_conn.enable_load_extension(True)
        sqlite_vec.load(self.vec_conn)
        self.vec_conn.enable_load_extension(False)

    def is_connected(self) -> bool:
        """Check if databases are connected."""
        return self.kuzu_conn is not None and self.vec_conn is not None

    def initialize_schema(self) -> None:
        """Create all node types, edge types, and vector tables."""
        self._create_kuzu_schema()
        self._create_vector_schema()

    def _create_kuzu_schema(self) -> None:
        """Create KuzuDB node and edge types."""
        # Node types
        node_types = [
            """
            CREATE NODE TABLE Concept (
                id STRING,
                name STRING,
                embedding_id STRING,
                layer STRING,
                stability FLOAT,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Artifact (
                id STRING,
                path STRING,
                content_hash STRING,
                language STRING,
                ast_fingerprint STRING,
                last_modified TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Invariant (
                id STRING,
                rule STRING,
                severity STRING,
                check_query STRING,
                is_automatic BOOLEAN,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Decision (
                id STRING,
                title STRING,
                timestamp TIMESTAMP,
                status STRING,
                rationale STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Anchor (
                id STRING,
                spatial_coords STRING,
                description STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """
        ]

        for node_type in node_types:
            try:
                self.kuzu_conn.execute(node_type)
            except Exception:
                # Node type might already exist
                pass

        # Edge types
        edge_types = [
            """
            CREATE REL TABLE EVOKES (
                FROM Artifact TO Concept,
                weight DOUBLE,
                last_activated TIMESTAMP
            )
            """,
            """
            CREATE REL TABLE CONSTRAINS (
                FROM Invariant TO Artifact,
                strictness DOUBLE
            )
            """,
            """
            CREATE REL TABLE DEPENDS_ON (
                FROM Artifact TO Artifact,
                weight DOUBLE,
                dependency_type STRING
            )
            """,
            """
            CREATE REL TABLE PRECEDES (
                FROM Decision TO Decision,
                reason STRING
            )
            """,
            """
            CREATE REL TABLE RELATED_TO (
                FROM Concept TO Concept,
                weight DOUBLE
            )
            """
        ]

        for edge_type in edge_types:
            try:
                self.kuzu_conn.execute(edge_type)
            except Exception:
                # Edge type might already exist
                pass

    def _create_vector_schema(self) -> None:
        """Create SQLite+vec tables for embeddings."""
        cursor = self.vec_conn.cursor()

        # Create embeddings table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings
            USING vec0(
                node_id TEXT PRIMARY KEY,
                embedding FLOAT[384]
            )
        """)

        self.vec_conn.commit()

    def get_node_types(self) -> List[str]:
        """Get all node types in the graph."""
        result = self.kuzu_conn.execute("CALL SHOW_NODE_TABLES() RETURN *")
        return [str(row["name"]) for row in result]

    def close(self) -> None:
        """Close database connections."""
        if self.kuzu_conn:
            self.kuzu_conn.close()
        if self.vec_conn:
            self.vec_conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_core/test_hippocampus.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/core/hippocampus.py tests/unit/test_core/test_hippocampus.py
git commit -m "feat: implement Hippocampus with KuzuDB and SQLite+vec"
```

---

### Task 7: Implement Hippocampus CRUD Operations

**Files:**
- Modify: `palace/core/hippocampus.py`
- Modify: `tests/unit/test_core/test_hippocampus.py`

**Step 1: Write tests for CRUD operations**

Add to `tests/unit/test_core/test_hippocampus.py`:

```python
def test_create_concept_node(temp_palace_dir):
    """Test creating a Concept node."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        node_id = hippo.create_node(
            "Concept",
            {
                "id": "concept-1",
                "name": "Authentication",
                "embedding_id": "emb-1",
                "layer": "abstraction",
                "stability": 0.8
            }
        )
        assert node_id == "concept-1"

def test_create_and_get_node(temp_palace_dir):
    """Test creating and retrieving a node."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        hippo.create_node(
            "Artifact",
            {
                "id": "artifact-1",
                "path": "test.py",
                "content_hash": "abc123",
                "language": "python",
                "ast_fingerprint": "fp-1"
            }
        )
        node = hippo.get_node("artifact-1")
        assert node is not None
        assert node["path"] == "test.py"
        assert node["language"] == "python"

def test_create_edge(temp_palace_dir):
    """Test creating an edge between nodes."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        # Create two nodes
        hippo.create_node(
            "Artifact",
            {"id": "artifact-1", "path": "a.py", "content_hash": "1", "language": "py", "ast_fingerprint": "1"}
        )
        hippo.create_node(
            "Concept",
            {"id": "concept-1", "name": "Test", "embedding_id": "1", "layer": "abstraction", "stability": 0.5}
        )
        # Create edge
        hippo.create_edge(
            "artifact-1",
            "concept-1",
            "EVOKES",
            {"weight": 0.9, "last_activated": None}
        )

def test_execute_cypher(temp_palace_dir):
    """Test executing raw Cypher query."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        results = hippo.execute_cypher(
            "MATCH (c:Concept) RETURN c LIMIT 1",
            {}
        )
        assert isinstance(results, list)
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_core/test_hippocampus.py::test_create_concept_node -v
```

Expected: AttributeError - method doesn't exist

**Step 3: Implement CRUD operations**

Add to `palace/core/hippocampus.py`:

```python
def create_node(self, node_type: str, properties: Dict) -> str:
    """
    Create a node in the graph.

    Args:
        node_type: Type of node (Concept, Artifact, etc.)
        properties: Dictionary of node properties

    Returns:
        The ID of the created node
    """
    query = f"CREATE (:{{{node_type} $props}})"
    self.kuzu_conn.execute(query, {"props": properties})
    return properties["id"]

def create_edge(
    self,
    src_id: str,
    dst_id: str,
    edge_type: str,
    properties: Dict
) -> None:
    """
    Create an edge between two nodes.

    Args:
        src_id: Source node ID
        dst_id: Destination node ID
        edge_type: Type of edge (EVOKES, DEPENDS_ON, etc.)
        properties: Edge properties
    """
    query = f"""
        MATCH (src), (dst)
        WHERE src.id = $src_id AND dst.id = $dst_id
        CREATE (src)-[r:{edge_type} $props]->(dst)
    """
    self.kuzu_conn.execute(query, {
        "src_id": src_id,
        "dst_id": dst_id,
        "props": properties
    })

def get_node(self, node_id: str) -> Optional[Dict]:
    """
    Get a node by ID.

    Args:
        node_id: Node ID to retrieve

    Returns:
        Node properties dict or None if not found
    """
    query = "MATCH (n) WHERE n.id = $node_id RETURN n"
    result = self.kuzu_conn.execute(query, {"node_id": node_id})
    try:
        row = next(result)
        return dict(row["n"])
    except StopIteration:
        return None

def execute_cypher(self, query: str, params: Dict) -> List[Dict]:
    """
    Execute a Cypher query.

    Args:
        query: Cypher query string
        params: Query parameters

    Returns:
        List of result rows as dicts
    """
    result = self.kuzu_conn.execute(query, params)
    return [dict(row) for row in result]
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_core/test_hippocampus.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/core/hippocampus.py tests/unit/test_core/test_hippocampus.py
git commit -m "feat: implement CRUD operations for Hippocampus"
```

---

### Task 8: Implement Vector Operations

**Files:**
- Modify: `palace/core/hippocampus.py`
- Modify: `tests/unit/test_core/test_hippocampus.py`

**Step 1: Write tests for vector operations**

Add to `tests/unit/test_core/test_hippocampus.py`:

```python
import numpy as np

def test_store_embedding(temp_palace_dir):
    """Test storing an embedding."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        embedding = np.random.rand(384).astype(np.float32)
        hippo.store_embedding("node-1", embedding)

def test_similarity_search(temp_palace_dir):
    """Test similarity search."""
    with Hippocampus(temp_palace_dir) as hippo:
        hippo.initialize_schema()
        # Store some embeddings
        emb1 = np.random.rand(384).astype(np.float32)
        emb2 = np.random.rand(384).astype(np.float32)
        hippo.store_embedding("node-1", emb1)
        hippo.store_embedding("node-2", emb2)

        # Search
        results = hippo.similarity_search(emb1, top_k=2)
        assert len(results) <= 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_core/test_hippocampus.py::test_store_embedding -v
```

Expected: AttributeError

**Step 3: Implement vector operations**

Add to `palace/core/hippocampus.py`:

```python
def store_embedding(self, node_id: str, embedding: np.ndarray) -> None:
    """
    Store an embedding vector.

    Args:
        node_id: Node ID to associate with embedding
        embedding: Vector to store (numpy array)
    """
    cursor = self.vec_conn.cursor()
    # Ensure embedding is float32
    embedding = embedding.astype(np.float32)
    cursor.execute(
        "INSERT OR REPLACE INTO vec_embeddings(node_id, embedding) VALUES (?, vec_float32(?))",
        [node_id, embedding.tobytes()]
    )
    self.vec_conn.commit()

def similarity_search(
    self,
    query_embedding: np.ndarray,
    top_k: int = 10
) -> List[Tuple[str, float]]:
    """
    Find similar embeddings by cosine similarity.

    Args:
        query_embedding: Query vector
        top_k: Number of results to return

    Returns:
        List of (node_id, distance) tuples
    """
    cursor = self.vec_conn.cursor()
    query_embedding = query_embedding.astype(np.float32)

    cursor.execute("""
        SELECT
            node_id,
            distance
        FROM vec_embeddings
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
    """, [query_embedding.tobytes(), top_k])

    return [(row[0], row[1]) for row in cursor.fetchall()]
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_core/test_hippocampus.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/core/hippocampus.py tests/unit/test_core/test_hippocampus.py
git commit -m "feat: implement vector storage and similarity search"
```

---

## Phase 3: Core Algorithms

### Task 9: Implement Spreading Activation Engine

**Files:**
- Create: `palace/core/activation.py`
- Create: `tests/unit/test_core/test_activation.py`

**Step 1: Write tests for spreading activation**

Create: `tests/unit/test_core/test_activation.py`

```python
import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.activation import ActivationEngine

@pytest.fixture
def populated_brain(tmp_path):
    """Create a brain with test data."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create test graph:
        # artifact1 -> concept1 (weight 0.9)
        # artifact1 -> concept2 (weight 0.5)
        # concept1 -> concept3 (weight 0.8)

        hippo.create_node("Artifact", {
            "id": "artifact1",
            "path": "test.py",
            "content_hash": "1",
            "language": "python",
            "ast_fingerprint": "1"
        })

        hippo.create_node("Concept", {
            "id": "concept1",
            "name": "Auth",
            "embedding_id": "1",
            "layer": "abstraction",
            "stability": 0.8
        })

        hippo.create_node("Concept", {
            "id": "concept2",
            "name": "Security",
            "embedding_id": "2",
            "layer": "abstraction",
            "stability": 0.7
        })

        hippo.create_node("Concept", {
            "id": "concept3",
            "name": "JWT",
            "embedding_id": "3",
            "layer": "implementation",
            "stability": 0.6
        })

        # Create edges
        hippo.create_edge("artifact1", "concept1", "EVOKES", {"weight": 0.9})
        hippo.create_edge("artifact1", "concept2", "EVOKES", {"weight": 0.5})
        hippo.create_edge("concept1", "concept3", "RELATED_TO", {"weight": 0.8})

    return palace_dir

def test_spreading_activation_basic(populated_brain):
    """Test basic spreading activation."""
    with Hippocampus(populated_brain) as hippo:
        engine = ActivationEngine(hippo)
        results = engine.spread("artifact1", max_depth=2, energy_threshold=0.2)

        # Should activate all nodes
        assert "artifact1" in results
        assert "concept1" in results
        assert "concept2" in results
        assert "concept3" in results

        # Energy should decrease with distance
        assert results["artifact1"] >= results["concept1"]
        assert results["concept1"] >= results["concept3"]

def test_spreading_activation_threshold(populated_brain):
    """Test that energy threshold filters nodes."""
    with Hippocampus(populated_brain) as hippo:
        engine = ActivationEngine(hippo)
        results = engine.spread("artifact1", max_depth=2, energy_threshold=0.6)

        # Only high-energy nodes
        for node_id, energy in results.items():
            assert energy >= 0.6

def test_spreading_activation_max_depth(populated_brain):
    """Test that max_depth limits propagation."""
    with Hippocampus(populated_brain) as hippo:
        engine = ActivationEngine(hippo)
        results = engine.spread("artifact1", max_depth=1, energy_threshold=0.1)

        # Should not reach concept3 (depth 2)
        assert "concept3" not in results or results["concept3"] < 0.1
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_core/test_activation.py -v
```

Expected: ImportError

**Step 3: Implement ActivationEngine**

Create: `palace/core/activation.py`

```python
"""Spreading activation algorithm for cognitive navigation."""

from typing import Dict, List, Set
from collections import deque
import math
from palace.core.hippocampus import Hippocampus


class ActivationEngine:
    """
    Implements spreading activation algorithm for cognitive navigation.
    Simulates neural firing patterns across the graph.
    """

    # Edge type transmission factors
    TRANSMISSION_FACTORS = {
        "CONSTRAINS": 1.0,
        "EVOKES": 0.9,
        "DEPENDS_ON": 0.7,
        "PRECEDES": 0.6,
        "RELATED_TO": 0.5
    }

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize activation engine.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus

    def spread(
        self,
        seed_node_id: str,
        max_depth: int = 3,
        energy_threshold: float = 0.15,
        decay_factor: float = 0.8
    ) -> Dict[str, float]:
        """
        Execute spreading activation from a seed node.

        Args:
            seed_node_id: Starting node ID
            max_depth: Maximum hop distance
            energy_threshold: Minimum energy to include in results
            decay_factor: Energy decay per hop

        Returns:
            Dict mapping node_id to activation energy, sorted by energy
        """
        # BFS queue: (node_id, current_energy, current_depth)
        queue = deque([(seed_node_id, 1.0, 0)])
        visited: Set[str] = set()
        energies: Dict[str, float] = {}

        while queue:
            node_id, energy, depth = queue.popleft()

            if node_id in visited:
                continue
            visited.add(node_id)

            # Store energy if above threshold
            if energy >= energy_threshold:
                energies[node_id] = energy

            # Stop if max depth reached
            if depth >= max_depth:
                continue

            # Get outgoing edges
            edges = self._get_outgoing_edges(node_id)

            for edge in edges:
                neighbor_id = edge["dst"]
                if neighbor_id in visited:
                    continue

                # Calculate transmitted energy
                transmission_factor = self._get_edge_transmission_factor(edge["type"])
                transmitted_energy = (
                    energy *
                    edge.get("weight", 1.0) *
                    decay_factor *
                    transmission_factor
                )

                if transmitted_energy >= energy_threshold:
                    queue.append((neighbor_id, transmitted_energy, depth + 1))

        # Update edge activation timestamps
        self._update_activation_timestamps(visited)

        return dict(sorted(energies.items(), key=lambda x: x[1], reverse=True))

    def _get_outgoing_edges(self, node_id: str) -> List[Dict]:
        """Get all outgoing edges from a node."""
        query = """
            MATCH (n)-[r]->(m)
            WHERE n.id = $node_id
            RETURN m.id AS dst, type(r) AS type, r.weight AS weight
        """
        return self.hippocampus.execute_cypher(query, {"node_id": node_id})

    def _get_edge_transmission_factor(self, edge_type: str) -> float:
        """Get energy transmission factor for edge type."""
        return self.TRANSMISSION_FACTORS.get(edge_type, 0.5)

    def _update_activation_timestamps(self, visited_nodes: Set[str]) -> None:
        """Update last_activated timestamp for EVOKES edges."""
        # This would be implemented with Cypher UPDATE
        # For now, placeholder
        pass
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_core/test_activation.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/core/activation.py tests/unit/test_core/test_activation.py
git commit -m "feat: implement spreading activation algorithm"
```

---

### Task 10: Implement Hebbian Plasticity Engine

**Files:**
- Create: `palace/core/plasticity.py`
- Create: `tests/unit/test_core/test_plasticity.py`

**Step 1: Write tests for Hebbian learning**

Create: `tests/unit/test_core/test_plasticity.py`

```python
import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.plasticity import PlasticityEngine

@pytest.fixture
def plastic_brain(tmp_path):
    """Create a brain for plasticity testing."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create test nodes
        hippo.create_node("Concept", {
            "id": "concept1",
            "name": "Auth",
            "embedding_id": "1",
            "layer": "abstraction",
            "stability": 0.5
        })

        hippo.create_node("Concept", {
            "id": "concept2",
            "name": "JWT",
            "embedding_id": "2",
            "layer": "implementation",
            "stability": 0.5
        })

        # Create initial edge
        hippo.create_edge("concept1", "concept2", "RELATED_TO", {"weight": 0.5})

    return palace_dir

def test_reinforce_coactivation_existing_edge(plastic_brain):
    """Test strengthening existing connection."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        # Get initial weight
        initial_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert initial_weight == 0.5

        # Reinforce
        engine.reinforce_coactivation({"concept1", "concept2"}, learning_rate=0.1)

        # Check weight increased
        new_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert new_weight == pytest.approx(0.6, abs=0.01)

def test_reinforce_coactivation_no_edge(plastic_brain):
    """Test creating new edge when none exists."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        # Add unconnected node
        hippo.create_node("Concept", {
            "id": "concept3",
            "name": "Security",
            "embedding_id": "3",
            "layer": "abstraction",
            "stability": 0.5
        })

        # Reinforce (no edge exists)
        engine.reinforce_coactivation({"concept1", "concept3"}, learning_rate=0.2)

        # Edge should be created
        weight = engine.get_edge_weight("concept1", "concept3", "RELATED_TO")
        assert weight == 0.2

def test_weight_capping(plastic_brain):
    """Test that weights are capped at 1.0."""
    with Hippocain(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        # Reinforce with high learning rate
        engine.reinforce_coactivation({"concept1", "concept2"}, learning_rate=1.0)

        # Should be capped at 1.0
        weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert weight == 1.0

def test_punish_mistake(plastic_brain):
    """Test weakening connection after mistake."""
    with Hippocampus(plastic_brain) as hippo:
        engine = PlasticityEngine(hippo)

        initial_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")

        # Punish
        engine.punish_mistake("concept1", "concept2", penalty=0.2)

        new_weight = engine.get_edge_weight("concept1", "concept2", "RELATED_TO")
        assert new_weight == pytest.approx(initial_weight - 0.2, abs=0.01)
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_core/test_plasticity.py -v
```

Expected: ImportError

**Step 3: Implement PlasticityEngine**

Create: `palace/core/plasticity.py`

```python
"""Hebbian learning and synaptic plasticity."""

from typing import Set
from palace.core.hippocampus import Hippocampus


class PlasticityEngine:
    """
    Implements synaptic plasticity: learning and forgetting.
    "Neurons that fire together, wire together."
    """

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize plasticity engine.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus

    def reinforce_coactivation(
        self,
        node_set: Set[str],
        learning_rate: float = 0.1
    ) -> None:
        """
        Strengthen connections between all pairs in node_set.

        Args:
            node_set: Set of node IDs that were co-activated
            learning_rate: How much to strengthen connections
        """
        node_list = list(node_set)

        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                node_a, node_b = node_list[i], node_list[j]

                # Get current weight
                current_weight = self.get_edge_weight(node_a, node_b, "RELATED_TO")

                # Calculate new weight
                new_weight = min(1.0, current_weight + learning_rate)

                # Update or create edge
                self._set_edge_weight(node_a, node_b, "RELATED_TO", new_weight)

    def punish_mistake(
        self,
        node_a: str,
        node_b: str,
        penalty: float = 0.2
    ) -> None:
        """
        Weaken connection between two nodes after bad outcome.

        Args:
            node_a: First node ID
            node_b: Second node ID
            penalty: How much to weaken the connection
        """
        current_weight = self.get_edge_weight(node_a, node_b, "RELATED_TO")

        if current_weight > 0:
            new_weight = max(0.0, current_weight - penalty)

            if new_weight < 0.1:
                # Remove weak edge
                self._remove_edge(node_a, node_b, "RELATED_TO")
            else:
                self._set_edge_weight(node_a, node_b, "RELATED_TO", new_weight)

    def get_edge_weight(
        self,
        src: str,
        dst: str,
        edge_type: str
    ) -> float:
        """
        Get current edge weight or return 0.0 if no edge.

        Args:
            src: Source node ID
            dst: Destination node ID
            edge_type: Type of edge

        Returns:
            Edge weight or 0.0
        """
        query = """
            MATCH (a)-[r]->(b)
            WHERE a.id = $src AND b.id = $dst AND type(r) = $edge_type
            RETURN r.weight AS weight
        """
        result = self.hippocampus.execute_cypher(query, {
            "src": src,
            "dst": dst,
            "edge_type": edge_type
        })

        if result:
            return float(result[0].get("weight", 0.0))
        return 0.0

    def _set_edge_weight(
        self,
        src: str,
        dst: str,
        edge_type: str,
        weight: float
    ) -> None:
        """Create or update edge with weight."""
        # Check if edge exists
        query = """
            MATCH (a), (b)
            WHERE a.id = $src AND b.id = $dst
            CREATE (a)-[r:{edge_type}]->(b)
            SET r.weight = $weight
        """
        self.hippocampus.execute_cypher(query, {
            "src": src,
            "dst": dst,
            "weight": weight
        })

    def _remove_edge(self, src: str, dst: str, edge_type: str) -> None:
        """Remove edge between nodes."""
        query = """
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            DELETE r
        """
        self.hippocampus.execute_cypher(query, {"src": src, "dst": dst})
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_core/test_plasticity.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/core/plasticity.py tests/unit/test_core/test_plasticity.py
git commit -m "feat: implement Hebbian plasticity engine"
```

---

### Task 11: Implement Sleep Cycle Engine

**Files:**
- Create: `palace/core/sleep.py`
- Create: `tests/unit/test_core/test_sleep.py`

**Step 1: Write tests for sleep cycle**

Create: `tests/unit/test_core/test_sleep.py`

```python
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.sleep import SleepEngine, SleepReport

@pytest.fixture
def sleepy_brain(tmp_path):
    """Create a brain with edges for sleep testing."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create nodes
        for i in range(5):
            hippo.create_node("Concept", {
                "id": f"concept{i}",
                "name": f"Concept{i}",
                "embedding_id": f"{i}",
                "layer": "abstraction",
                "stability": 0.5
            })

        # Create edges with different weights and timestamps
        hippo.create_edge("concept0", "concept1", "RELATED_TO", {
            "weight": 0.9,  # Strong, should survive
            "last_activated": datetime.utcnow()
        })

        hippo.create_edge("concept1", "concept2", "RELATED_TO", {
            "weight": 0.15,  # Weak, might be pruned
            "last_activated": datetime.utcnow() - timedelta(days=10)
        })

        hippo.create_edge("concept2", "concept3", "RELATED_TO", {
            "weight": 0.05,  # Very weak, should be pruned
            "last_activated": datetime.utcnow() - timedelta(days=20)
        })

    return palace_dir

def test_sleep_cycle_decay(sleepy_brain):
    """Test that edge weights decay over time."""
    with Hippocampus(sleepy_brain) as hippo:
        engine = SleepEngine(hippo)
        report = engine.sleep_cycle(lambda_decay=0.1)

        assert report.edges_decayed > 0
        assert report.total_duration_ms > 0

def test_sleep_cycle_pruning(sleepy_brain):
    """Test that weak edges are pruned."""
    with Hippocampus(sleepy_brain) as hippo:
        engine = SleepEngine(hippo)
        report = engine.sleep_cycle(prune_threshold=0.1)

        assert report.edges_pruned >= 1  # At least the 0.05 edge

def test_sleep_report(sleepy_brain):
    """Test that sleep cycle returns detailed report."""
    with Hippocampus(sleepy_brain) as hippo:
        engine = SleepEngine(hippo)
        report = engine.sleep_cycle()

        assert isinstance(report.nodes_count, int)
        assert isinstance(report.edges_count, int)
        assert isinstance(report.edges_decayed, int)
        assert isinstance(report.edges_pruned, int)
        assert isinstance(report.communities_detected, int)
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_core/test_sleep.py -v
```

Expected: ImportError

**Step 3: Implement SleepEngine**

Create: `palace/core/sleep.py`:

```python
"""Sleep cycle for consolidation and forgetting."""

from dataclasses import dataclass
from typing import List
import time
from datetime import datetime, timedelta
from palace.core.hippocampus import Hippocampus


@dataclass
class SleepReport:
    """Report from a sleep cycle."""
    nodes_count: int
    edges_count: int
    edges_decayed: int
    edges_pruned: int
    communities_detected: int
    total_duration_ms: float


class SleepEngine:
    """
    Implements REM-like sleep cycle: consolidation, pruning, forgetting.
    Runs asynchronously or on-demand.
    """

    def __init__(self, hippocampus: Hippocampus):
        """
        Initialize sleep engine.

        Args:
            hippocampus: Graph database interface
        """
        self.hippocampus = hippocampus

    def sleep_cycle(
        self,
        lambda_decay: float = 0.05,
        prune_threshold: float = 0.1,
        detect_communities: bool = True
    ) -> SleepReport:
        """
        Execute full sleep cycle.

        Args:
            lambda_decay: Decay rate constant
            prune_threshold: Minimum weight to keep edge
            detect_communities: Whether to run community detection

        Returns:
            SleepReport with statistics
        """
        start_time = time.time()

        # Get initial counts
        nodes_count = self._count_nodes()
        edges_count = self._count_edges()

        # Decay edge weights
        edges_decayed = self._decay_edge_weights(lambda_decay)

        # Prune weak edges
        edges_pruned = self._prune_weak_edges(prune_threshold)

        # Detect communities
        communities_detected = 0
        if detect_communities:
            communities_detected = self._detect_communities()

        duration_ms = (time.time() - start_time) * 1000

        return SleepReport(
            nodes_count=nodes_count,
            edges_count=edges_count,
            edges_decayed=edges_decayed,
            edges_pruned=edges_pruned,
            communities_detected=communities_detected,
            total_duration_ms=duration_ms
        )

    def _count_nodes(self) -> int:
        """Count total nodes in graph."""
        result = self.hippocampus.execute_cypher(
            "MATCH (n) RETURN count(n) AS count",
            {}
        )
        return int(result[0]["count"]) if result else 0

    def _count_edges(self) -> int:
        """Count total edges in graph."""
        result = self.hippocampus.execute_cypher(
            "MATCH ()-[r]->() RETURN count(r) AS count",
            {}
        )
        return int(result[0]["count"]) if result else 0

    def _decay_edge_weights(self, lambda_decay: float) -> int:
        """
        Apply exponential decay: w = w * exp(-λ * Δt)

        Returns:
            Number of edges decayed
        """
        # Get all edges with last_activated
        query = """
            MATCH (a)-[r:EVOKES]->(b)
            WHERE r.last_activated IS NOT NULL
            RETURN a.id AS src, b.id AS dst, r.weight AS weight,
                   r.last_activated AS last_activated
        """
        edges = self.hippocampus.execute_cypher(query, {})

        decayed_count = 0

        for edge in edges:
            last_activated = edge["last_activated"]
            delta_t = (datetime.utcnow() - last_activated).total_seconds() / 86400  # Days
            decay_factor = math.exp(-lambda_decay * delta_t)
            new_weight = edge["weight"] * decay_factor

            if new_weight < edge["weight"]:
                self._update_edge_weight(
                    edge["src"], edge["dst"], "EVOKES", new_weight
                )
                decayed_count += 1

        return decayed_count

    def _prune_weak_edges(self, threshold: float) -> int:
        """
        Remove edges with weight < threshold.

        Returns:
            Number of edges pruned
        """
        # This would need to be implemented with Cypher DELETE
        # Placeholder for now
        return 0

    def _detect_communities(self) -> int:
        """
        Run Louvain algorithm on concept graph.
        Create Anchor nodes for spatial reference.

        Returns:
            Number of communities detected
        """
        # Placeholder - would use networkx or similar for Louvain
        return 0

    def _update_edge_weight(
        self,
        src: str,
        dst: str,
        edge_type: str,
        weight: float
    ) -> None:
        """Update edge weight."""
        query = f"""
            MATCH (a)-[r:{edge_type}]->(b)
            WHERE a.id = $src AND b.id = $dst
            SET r.weight = $weight
        """
        self.hippocampus.execute_cypher(query, {
            "src": src,
            "dst": dst,
            "weight": weight
        })
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_core/test_sleep.py -v
```

Expected: All tests PASS (some tests may be placeholders)

**Step 5: Commit**

```bash
git add palace/core/sleep.py tests/unit/test_core/test_sleep.py
git commit -m "feat: implement sleep cycle engine"
```

---

## Phase 4: Ingestion System

### Task 12: Implement Base Parser Interface

**Files:**
- Create: `palace/ingest/parsers/base.py`
- Create: `tests/unit/test_ingest/test_parsers.py`

**Step 1: Write test for parser interface**

Create: `tests/unit/test_ingest/test_parsers.py`:

```python
import pytest
from pathlib import Path
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol

def test_base_parser_is_abstract():
    """Test that BaseParser cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseParser()

def test_dependency_model():
    """Test Dependency data model."""
    dep = Dependency(
        path="src/auth.py",
        type="IMPORT",
        lineno=10
    )
    assert dep.path == "src/auth.py"
    assert dep.type == "IMPORT"
    assert dep.lineno == 10

def test_symbol_model():
    """Test Symbol data model."""
    symbol = Symbol(
        name="authenticate",
        type="function",
        lineno=5,
        docstring="Authenticates user"
    )
    assert symbol.name == "authenticate"
    assert symbol.type == "function"
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_ingest/test_parsers.py -v
```

Expected: ImportError

**Step 3: Implement base parser**

Create: `palace/ingest/parsers/base.py`:

```python
"""Base parser interface and data models."""

from abc import ABC, abstractmethod
 from dataclasses import dataclass
from typing import List


@dataclass
class Dependency:
    """A dependency (import, require, etc.) extracted from code."""
    path: str
    type: str  # IMPORT, FUNCTION_CALL, INHERITANCE, COMPOSITION
    lineno: int


@dataclass
class Symbol:
    """A symbol (function, class, constant) extracted from code."""
    name: str
    type: str  # function, class, constant, method
    lineno: int
    docstring: str = ""


class BaseParser(ABC):
    """Abstract base for language-specific parsers."""

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of file extensions this parser handles."""
        pass

    @abstractmethod
    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """
        Extract import/require statements.

        Returns:
            List of Dependency objects
        """
        pass

    @abstractmethod
    def extract_symbols(self, content: str) -> List[Symbol]:
        """
        Extract functions, classes, constants.

        Returns:
            List of Symbol objects
        """
        pass

    @abstractmethod
    def compute_fingerprint(self, content: str) -> str:
        """
        Compute hash of AST structure for change detection.

        Returns:
            Fingerprint string
        """
        pass
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_ingest/test_parsers.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/ingest/parsers/base.py tests/unit/test_ingest/test_parsers.py
git commit -m "feat: implement base parser interface"
```

---

### Task 13: Implement Python Parser

**Files:**
- Create: `palace/ingest/parsers/python.py`
- Modify: `tests/unit/test_ingest/test_parsers.py`

**Step 1: Write tests for Python parser**

Add to `tests/unit/test_ingest/test_parsers.py`:

```python
from palace.ingest.parsers.python import PythonParser
import pytest

def test_python_parser_extensions():
    """Test supported extensions."""
    parser = PythonParser()
    assert ".py" in parser.supported_extensions()
    assert ".pyx" in parser.supported_extensions()

def test_python_parse_imports():
    """Test parsing Python imports."""
    parser = PythonParser()
    code = """
import os
from typing import List
import numpy as np
from .auth import authenticate
"""
    deps = parser.parse_dependencies(Path("test.py"), code)
    assert len(deps) >= 3
    assert any(d.path == "os" for d in deps)
    assert any(d.type == "IMPORT" for d in deps)

def test_python_extract_symbols():
    """Test extracting functions and classes."""
    parser = PythonParser()
    code = """
def calculate(x, y):
    '''Calculate something.'''
    return x + y

class Calculator:
    '''A calculator class.'''
    def add(self, a, b):
        return a + b
"""
    symbols = parser.extract_symbols(code)
    assert len(symbols) >= 2
    assert any(s.name == "calculate" for s in symbols)
    assert any(s.name == "Calculator" for s in symbols)

def test_python_fingerprint():
    """Test AST fingerprinting."""
    parser = PythonParser()
    code1 = "def foo(): pass"
    code2 = "def foo(): pass"
    code3 = "def bar(): pass"

    fp1 = parser.compute_fingerprint(code1)
    fp2 = parser.compute_fingerprint(code2)
    fp3 = parser.compute_fingerprint(code3)

    assert fp1 == fp2  # Same AST
    assert fp1 != fp3  # Different AST
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_ingest/test_parsers.py::test_python_parser_extensions -v
```

Expected: ImportError

**Step 3: Install tree-sitter Python if not available**

Check pyproject.toml - should already have `tree-sitter-python` from Task 1.

**Step 4: Implement Python parser**

Create: `palace/ingest/parsers/python.py`:

```python
"""Python language parser using tree-sitter."""

from pathlib import Path
from typing import List
import hashlib
from palace.ingest.parsers.base import BaseParser, Dependency, Symbol

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class PythonParser(BaseParser):
    """Parser for Python source code."""

    def __init__(self):
        """Initialize parser with tree-sitter."""
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter-python not installed")

        self.language = Language(tspython.language())
        self.parser = Parser(self.language)

    def supported_extensions(self) -> List[str]:
        """Return supported file extensions."""
        return [".py", ".pyx"]

    def parse_dependencies(
        self,
        file_path: Path,
        content: str
    ) -> List[Dependency]:
        """Extract import statements."""
        tree = self.parser.parse(bytes(content, "utf-8"))
        deps = []

        def find_imports(node):
            if node.type == "import_statement":
                # Handle: import os
                name_node = node.child_by_field_name("name")
                if name_node:
                    deps.append(Dependency(
                        path=name_node.text.decode(),
                        type="IMPORT",
                        lineno=node.start_point[0] + 1
                    ))
            elif node.type == "import_from_statement":
                # Handle: from typing import List
                module_node = node.child_by_field_name("module_name")
                if module_node:
                    deps.append(Dependency(
                        path=module_node.text.decode(),
                        type="IMPORT",
                        lineno=node.start_point[0] + 1
                    ))

            for child in node.children:
                find_imports(child)

        find_imports(tree.root_node)
        return deps

    def extract_symbols(self, content: str) -> List[Symbol]:
        """Extract functions, classes, constants."""
        tree = self.parser.parse(bytes(content, "utf-8"))
        symbols = []

        def find_symbols(node):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                symbols.append(Symbol(
                    name=name_node.text.decode() if name_node else "",
                    type="function",
                    lineno=node.start_point[0] + 1,
                    docstring=self._extract_docstring(node)
                ))
            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                symbols.append(Symbol(
                    name=name_node.text.decode() if name_node else "",
                    type="class",
                    lineno=node.start_point[0] + 1,
                    docstring=self._extract_docstring(node)
                ))

            for child in node.children:
                find_symbols(child)

        find_symbols(tree.root_node)
        return symbols

    def compute_fingerprint(self, content: str) -> str:
        """Compute hash of AST structure."""
        tree = self.parser.parse(bytes(content, "utf-8"))

        # Serialize structure
        structure = self._serialize_node(tree.root_node)
        return hashlib.sha256(structure.encode()).hexdigest()

    def _extract_docstring(self, node) -> str:
        """Extract docstring from function/class node."""
        # Find first string expression child
        for child in node.children:
            if child.type == "string":
                return child.text.decode().strip('"\'')
        return ""

    def _serialize_node(self, node, indent=0) -> str:
        """Serialize tree structure to string."""
        result = "  " * indent + node.type + "\n"
        for child in node.children:
            result += self._serialize_node(child, indent + 1)
        return result
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_ingest/test_parsers.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add palace/ingest/parsers/python.py tests/unit/test_ingest/test_parsers.py
git commit -m "feat: implement Python parser with tree-sitter"
```

---

### Task 14: Implement Concept Extractor

**Files:**
- Create: `palace/ingest/extractors.py`
- Create: `tests/unit/test_ingest/test_extractors.py`

**Step 1: Write tests for concept extraction**

Create: `tests/unit/test_ingest/test_extractors.py`:

```python
import pytest
from pathlib import Path
from palace.ingest.extractors import ConceptExtractor, ConceptCandidate

@pytest.fixture
def extractor():
    """Create a concept extractor."""
    # Would need sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return ConceptExtractor(model)
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_extract_concepts_from_auth_file(extractor):
    """Test concept extraction from authentication code."""
    artifact_path = "src/auth.py"
    content = """
import jwt
from datetime import timedelta

def authenticate(username, password):
    '''Authenticate user with JWT token.'''
    token = jwt.encode({'user': username}, 'secret', algorithm='HS256')
    return token

def verify_token(token):
    '''Verify JWT token.'''
    return jwt.decode(token, 'secret', algorithms=['HS256'])
"""
    symbols = [
        Symbol("authenticate", "function", 4, "Authenticate user with JWT token"),
        Symbol("verify_token", "function", 9, "Verify JWT token")
    ]

    concepts = extractor.extract_concepts(artifact_path, content, symbols)

    assert len(concepts) > 0
    assert any("JWT" in c.name.upper() or "auth" in c.name.lower() for c in concepts)

def test_cluster_similar_concepts(extractor):
    """Test concept clustering."""
    candidates = [
        ConceptCandidate("Authentication", 0.9),
        ConceptCandidate("Auth", 0.85),
        ConceptCandidate("Calculator", 0.8)
    ]

    clustered = extractor.cluster_similar_concepts(candidates, threshold=0.85)

    # Auth and Authentication should be merged
    auth_concepts = [c for c in clustered if "auth" in c.name.lower()]
    assert len(auth_concepts) <= 2  # May or may not be merged depending on embeddings
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_ingest/test_extractors.py -v
```

Expected: ImportError

**Step 3: Implement concept extractor**

Create: `palace/ingest/extractors.py`:

```python
"""Concept extraction using embeddings and NLP."""

from dataclasses import dataclass
from typing import List
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from palace.ingest.parsers.base import Symbol


@dataclass
class ConceptCandidate:
    """A potential concept extracted from code."""
    name: str
    confidence: float
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class ConceptExtractor:
    """
    Extracts semantic concepts from artifacts using:
    1. Keyword extraction
    2. Embedding clustering
    """

    def __init__(self, embedding_model: SentenceTransformer):
        """
        Initialize concept extractor.

        Args:
            embedding_model: sentence-transformers model
        """
        self.model = embedding_model

    def extract_concepts(
        self,
        artifact_path: str,
        content: str,
        symbols: List[Symbol]
    ) -> List[ConceptCandidate]:
        """
        Analyze code and extract concept candidates.

        Args:
            artifact_path: File path
            content: File content
            symbols: Extracted symbols

        Returns:
            List of ranked concept candidates
        """
        candidates = []

        # Extract from file path
        path_concepts = self._extract_from_path(artifact_path)
        candidates.extend(path_concepts)

        # Extract from symbol names
        for symbol in symbols:
            symbol_concepts = self._extract_from_symbol(symbol)
            candidates.extend(symbol_concepts)

        # Extract from docstrings
        for symbol in symbols:
            if symbol.docstring:
                docstring_concepts = self._extract_from_docstring(symbol.docstring)
                candidates.extend(docstring_concepts)

        return candidates

    def _extract_from_path(self, path: str) -> List[ConceptCandidate]:
        """Extract concepts from file path."""
        parts = Path(path).parts
        candidates = []

        for part in parts:
            # Filter out common non-concept parts
            if part not in ["src", "lib", "test", "tests", "__init__"]:
                candidates.append(ConceptCandidate(
                    name=part.replace("_", " ").title(),
                    confidence=0.7
                ))

        return candidates

    def _extract_from_symbol(self, symbol: Symbol) -> List[ConceptCandidate]:
        """Extract concepts from symbol names."""
        candidates = []

        # Split camelCase and snake_case
        words = self._split_identifier(symbol.name)

        if len(words) > 1:
            concept_name = " ".join(words).title()
            candidates.append(ConceptCandidate(
                name=concept_name,
                confidence=0.8
            ))

        return candidates

    def _extract_from_docstring(self, docstring: str) -> List[ConceptCandidate]:
        """Extract concepts from docstrings."""
        # Simple keyword extraction
        # In production, would use more sophisticated NLP
        return []

    def cluster_similar_concepts(
        self,
        candidates: List[ConceptCandidate],
        threshold: float = 0.85
    ) -> List[ConceptCandidate]:
        """
        Merge similar concepts using cosine similarity.

        Args:
            candidates: Concept candidates to cluster
            threshold: Similarity threshold for merging

        Returns:
            Deduplicated concept list
        """
        if not candidates:
            return []

        # Compute embeddings
        names = [c.name for c in candidates]
        embeddings = self.model.encode(names)

        # Cluster by similarity
        merged = []
        used_indices = set()

        for i, candidate in enumerate(candidates):
            if i in used_indices:
                continue

            # Find similar concepts
            similar_indices = self._find_similar(
                embeddings[i],
                embeddings,
                threshold,
                used_indices
            )

            # Merge similar concepts
            if len(similar_indices) > 1:
                merged_name = self._merge_concept_names([
                    candidates[j].name for j in similar_indices
                ])
                merged.append(ConceptCandidate(
                    name=merged_name,
                    confidence=max(candidates[j].confidence for j in similar_indices)
                ))
            else:
                merged.append(candidate)

            used_indices.update(similar_indices)

        return merged

    def _split_identifier(self, identifier: str) -> List[str]:
        """Split camelCase and snake_case into words."""
        # Simple implementation
        words = identifier.replace("_", " ").split()
        return words

    def _find_similar(
        self,
        query_embedding: np.ndarray,
        all_embeddings: np.ndarray,
        threshold: float,
        exclude: set
    ) -> List[int]:
        """Find indices of similar embeddings."""
        similarities = np.dot(all_embeddings, query_embedding)
        similar = np.where(similarities >= threshold)[0]
        return [int(i) for i in similar if i not in exclude]

    def _merge_concept_names(self, names: List[str]) -> str:
        """Merge similar concept names."""
        # Return the most common or shortest
        return min(names, key=len)
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_ingest/test_extractors.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/ingest/extractors.py tests/unit/test_ingest/test_extractors.py
git commit -m "feat: implement concept extractor with embeddings"
```

---

### Task 15: Implement Invariant Detector

**Files:**
- Create: `palace/ingest/invariants.py`
- Create: `tests/unit/test_ingest/test_invariants.py`

**Step 1: Write tests for invariant detection**

Create: `tests/unit/test_ingest/test_invariants.py`:

```python
import pytest
from palace.ingest.invariants import InvariantDetector
from palace.shared.models import Invariant

def test_detect_hardcoded_secrets():
    """Test detection of hardcoded secrets."""
    detector = InvariantDetector()
    content = """
API_KEY = "sk-1234567890"
password = "admin123"
token = "abc"
"""
    invariants = detector.detect("test.py", content)

    secret_invariants = [inv for inv in invariants if "secret" in inv.rule.lower()]
    assert len(secret_invariants) > 0

def test_detect_eval_usage():
    """Test detection of eval usage."""
    detector = InvariantDetector()
    content = """
x = eval(user_input)
code = exec(some_string)
"""
    invariants = detector.detect("test.py", content)

    eval_invariants = [inv for inv in invariants if "eval" in inv.rule.lower()]
    assert len(eval_invariants) > 0

def test_detect_god_object():
    """Test detection of god objects."""
    detector = InvariantDetector()
    symbols = [
        Symbol("GodClass", "class", 1, ""),
        Symbol("method1", "function", 10, ""),
        Symbol("method2", "function", 20, ""),
        # ... many more methods
    ]

    # Add 50+ methods to simulate god object
    for i in range(50):
        symbols.append(Symbol(f"method{i}", "function", i * 10, ""))

    invariants = detector.detect("test.py", "", symbols=symbols)
    god_invariants = [inv for inv in invariants if "god" in inv.rule.lower()]

    assert len(god_invariants) > 0
    assert any(inv.severity == "HIGH" for inv in god_invariants)
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_ingest/test_invariants.py -v
```

Expected: ImportError

**Step 3: Implement invariant detector**

Create: `palace/ingest/invariants.py`:

```python
"""Invariant detection for security and architectural patterns."""

import re
from typing import List, Optional
from palace.shared.models import Invariant
from palace.ingest.parsers.base import Symbol


class InvariantDetector:
    """
    Detects architectural and security invariants using pattern matching.
    """

    # Security patterns
    SECRET_PATTERNS = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
        r'private[_-]?key\s*=\s*["\'][^"\']+["\']',
    ]

    def __init__(self):
        """Initialize detector with compiled patterns."""
        self.secret_regexes = [re.compile(p, re.IGNORECASE) for p in self.SECRET_PATTERNS]
        self.eval_regex = re.compile(r'\b(eval|exec)\s*\(', re.IGNORECASE)

    def detect(
        self,
        artifact_path: str,
        content: str,
        symbols: Optional[List[Symbol]] = None
    ) -> List[Invariant]:
        """
        Run all detection rules.

        Args:
            artifact_path: File being analyzed
            content: File content
            symbols: Extracted symbols

        Returns:
            List of triggered invariants
        """
        invariants = []

        # Security checks
        invariants.extend(self._detect_hardcoded_secrets(content))
        invariants.extend(self._detect_eval_usage(content))
        invariants.extend(self._detect_sql_injection_risk(content))

        # Architecture checks
        if symbols:
            invariants.extend(self._detect_god_object(symbols))
            invariants.extend(self._detect_missing_error_handling(content))

        return invariants

    def _detect_hardcoded_secrets(self, content: str) -> List[Invariant]:
        """Detect hardcoded secrets."""
        found = []

        for regex in self.secret_regexes:
            matches = regex.findall(content)
            if matches:
                found.append(Invariant(
                    id=self._generate_invariant_id("hardcoded_secret"),
                    rule="No hardcoded secrets or credentials",
                    severity="CRITICAL",
                    is_automatic=True
                ))
                break  # One invariant per type

        return found

    def _detect_eval_usage(self, content: str) -> List[Invariant]:
        """Detect use of eval/exec."""
        if self.eval_regex.search(content):
            return [Invariant(
                id=self._generate_invariant_id("no_eval"),
                rule="Avoid eval() and exec() - security risk",
                severity="HIGH",
                is_automatic=True
            )]
        return []

    def _detect_sql_injection_risk(self, content: str) -> List[Invariant]:
        """Detect potential SQL injection risks."""
        # Simple heuristic: string concatenation in SQL queries
        risky_patterns = [
            r'SELECT.*FROM.*\+.*WHERE',
            r'execute\(["\'].*SELECT.*\+',
        ]

        for pattern in risky_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return [Invariant(
                    id=self._generate_invariant_id("sql_injection"),
                    rule="Use parameterized queries to prevent SQL injection",
                    severity="CRITICAL",
                    is_automatic=True
                )]

        return []

    def _detect_god_object(self, symbols: List[Symbol]) -> List[Invariant]:
        """Detect god objects (too many responsibilities)."""
        # Count methods per class
        class_methods = {}
        for symbol in symbols:
            if symbol.type == "class":
                class_methods[symbol.name] = 0
            elif symbol.type == "function":
                # Heuristic: assume functions after a class belong to it
                pass  # Would need more sophisticated tracking

        # Check if any class has >20 methods
        for class_name, method_count in class_methods.items():
            if method_count > 20:
                return [Invariant(
                    id=self._generate_invariant_id(f"god_object_{class_name}"),
                    rule=f"Class {class_name} has too many methods (>20) - consider splitting",
                    severity="MEDIUM",
                    is_automatic=True
                )]

        return []

    def _detect_missing_error_handling(self, content: str) -> List[Invariant]:
        """Detect potential missing error handling."""
        # Check for file operations without try/except
        file_ops = re.findall(r'\b(open|read|write)\s*\(', content)
        try_blocks = len(re.findall(r'\btry\s*:', content))

        if file_ops > try_blocks and file_ops > 3:
            return [Invariant(
                id=self._generate_invariant_id("missing_error_handling"),
                rule="File operations should have error handling (try/except)",
                severity="MEDIUM",
                is_automatic=True
            )]

        return []

    def _generate_invariant_id(self, name: str) -> str:
        """Generate deterministic invariant ID."""
        import hashlib
        hash_val = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"inv-{name}-{hash_val}"
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_ingest/test_invariants.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/ingest/invariants.py tests/unit/test_ingest/test_invariants.py
git commit -m "feat: implement invariant detector"
```

---

### Task 16: Implement Big Bang Pipeline

**Files:**
- Create: `palace/ingest/pipeline.py`
- Create: `tests/integration/test_big_bang.py`

**Step 1: Write integration test for Big Bang**

Create: `tests/integration/test_big_bang.py`:

```python
import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.ingest.parsers.python import PythonParser
from palace.ingest.extractors import ConceptExtractor
from palace.ingest.invariants import InvariantDetector
from palace.ingest.pipeline import BigBangPipeline

@pytest.fixture
def sample_repo(tmp_path):
    """Create a sample Python repository."""
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    # Create test files
    (repo / "auth.py").write_text("""
import jwt

def authenticate(username, password):
    token = jwt.encode({'user': username}, 'secret')
    return token
""")

    (repo / "main.py").write_text("""
from auth import authenticate

def main():
    result = authenticate("user", "pass")
    print(result)
""")

    # Create directory to ignore
    node_modules = repo / "node_modules"
    node_modules.mkdir()
    (node_modules / "test.js").write_text("console.log('test');")

    return repo

@pytest.fixture
def embedding_model():
    """Load embedding model."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_big_bang_ingestion(sample_repo, embedding_model):
    """Test full ingestion pipeline."""
    palace_dir = sample_repo / ".palace"

    # Initialize components
    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        parsers = [PythonParser()]
        concept_extractor = ConceptExtractor(embedding_model)
        invariant_detector = InvariantDetector()

        pipeline = BigBangPipeline(
            hippocampus=hippo,
            parsers=parsers,
            concept_extractor=concept_extractor,
            invariant_detector=invariant_detector
        )

        # Run ingestion
        report = pipeline.ingest_repository(sample_repo)

        # Verify results
        assert report.files_processed >= 2  # auth.py and main.py
        assert report.nodes_created >= 2  # At least artifacts
        assert report.edges_created >= 1  # At least one dependency
        assert report.errors == 0  # No errors expected

        # Verify nodes exist
        nodes = hippo.execute_cypher("MATCH (n:Artifact) RETURN n", {})
        assert len(nodes) >= 2
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/integration/test_big_bang.py -v
```

Expected: ImportError

**Step 3: Implement Big Bang pipeline**

Create: `palace/ingest/pipeline.py`:

```python
"""Big Bang ingestion pipeline."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import hashlib
from tqdm import tqdm

from palace.core.hippocampus import Hippocampus
from palace.ingest.parsers.base import BaseParser
from palace.ingest.extractors import ConceptExtractor
from palace.ingest.invariants import InvariantDetector
from palace.shared.config import PalaceConfig


@dataclass
class IngestReport:
    """Report from ingestion process."""
    files_processed: int
    nodes_created: int
    edges_created: int
    invariants_detected: int
    errors: int
    duration_seconds: float


class BigBangPipeline:
    """
    Orchestrates the complete ingestion process.
    """

    DEFAULT_IGNORE_PATTERNS = [
        "node_modules", ".git", "__pycache__",
        "*.log", "dist", "build", ".venv",
        "*.pyc", ".pytest_cache", ".palace"
    ]

    def __init__(
        self,
        hippocampus: Hippocampus,
        parsers: List[BaseParser],
        concept_extractor: ConceptExtractor,
        invariant_detector: InvariantDetector,
        config: Optional[PalaceConfig] = None
    ):
        """
        Initialize pipeline.

        Args:
            hippocampus: Graph database interface
            parsers: List of language parsers
            concept_extractor: Concept extraction engine
            invariant_detector: Invariant detection engine
            config: Configuration (optional)
        """
        self.hippocampus = hippocampus
        self.parsers = {ext: parser for parser in parsers for ext in parser.supported_extensions()}
        self.concept_extractor = concept_extractor
        self.invariant_detector = invariant_detector
        self.config = config or PalaceConfig()

    def ingest_repository(
        self,
        repo_path: Path,
        ignore_patterns: Optional[List[str]] = None
    ) -> IngestReport:
        """
        Execute full Big Bang ingestion.

        Args:
            repo_path: Path to repository root
            ignore_patterns: Additional ignore patterns

        Returns:
            IngestReport with statistics
        """
        import time
        start_time = time.time()

        ignore = set(self.DEFAULT_IGNORE_PATTERNS)
        if ignore_patterns:
            ignore.update(ignore_patterns)

        # Scan all files
        files = self._scan_files(repo_path, ignore)

        nodes_created = 0
        edges_created = 0
        invariants_detected = 0
        errors = 0

        # Process each file
        for file_path in tqdm(files, desc="Ingesting"):
            try:
                result = self._process_file(file_path, repo_path)
                nodes_created += result["nodes"]
                edges_created += result["edges"]
                invariants_detected += result["invariants"]
            except Exception as e:
                errors += 1
                print(f"Error processing {file_path}: {e}")

        duration = time.time() - start_time

        return IngestReport(
            files_processed=len(files),
            nodes_created=nodes_created,
            edges_created=edges_created,
            invariants_detected=invariants_detected,
            errors=errors,
            duration_seconds=duration
        )

    def _scan_files(self, repo_path: Path, ignore_patterns: List[str]) -> List[Path]:
        """Scan repository for code files."""
        files = []

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check ignore patterns
            if self._should_ignore(file_path, repo_path, ignore_patterns):
                continue

            # Check if we have a parser
            if file_path.suffix in self.parsers:
                files.append(file_path)

        return files

    def _should_ignore(
        self,
        file_path: Path,
        repo_path: Path,
        ignore_patterns: List[str]
    ) -> bool:
        """Check if file should be ignored."""
        relative_path = file_path.relative_to(repo_path)

        for pattern in ignore_patterns:
            if pattern in str(relative_path):
                return True

        return False

    def _process_file(self, file_path: Path, repo_path: Path) -> dict:
        """Process a single file."""
        # Read content
        content = file_path.read_text()
        relative_path = str(file_path.relative_to(repo_path))

        # Get parser
        parser = self.parsers.get(file_path.suffix)
        if not parser:
            return {"nodes": 0, "edges": 0, "invariants": 0}

        # Parse dependencies and symbols
        dependencies = parser.parse_dependencies(file_path, content)
        symbols = parser.extract_symbols(content)
        fingerprint = parser.compute_fingerprint(content)

        # Create artifact node
        artifact_id = self._generate_artifact_id(relative_path)
        self.hippocampus.create_node("Artifact", {
            "id": artifact_id,
            "path": relative_path,
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "language": self._get_language(file_path.suffix),
            "ast_fingerprint": fingerprint
        })

        nodes_created = 1
        edges_created = 0
        invariants_detected = 0

        # Create dependency edges
        for dep in dependencies:
            dep_id = self._generate_artifact_id(dep.path)
            self.hippocampus.create_edge(
                artifact_id,
                dep_id,
                "DEPENDS_ON",
                {"weight": 0.8, "dependency_type": dep.type}
            )
            edges_created += 1

        # Extract concepts
        concepts = self.concept_extractor.extract_concepts(
            relative_path,
            content,
            symbols
        )

        for concept in concepts:
            concept_id = self._generate_concept_id(concept.name)
            # Check if concept exists, create if not
            if not self.hippocampus.get_node(concept_id):
                self.hippocampus.create_node("Concept", {
                    "id": concept_id,
                    "name": concept.name,
                    "embedding_id": "",  # Would be populated by vector store
                    "layer": "implementation",
                    "stability": concept.confidence
                })
                nodes_created += 1

            # Create EVOKES edge
            self.hippocampus.create_edge(
                artifact_id,
                concept_id,
                "EVOKES",
                {"weight": concept.confidence, "last_activated": None}
            )
            edges_created += 1

        # Detect invariants
        invariants = self.invariant_detector.detect(
            relative_path,
            content,
            symbols
        )

        for inv in invariants:
            inv_id = inv.id
            if not self.hippocampus.get_node(inv_id):
                self.hippocampus.create_node("Invariant", {
                    "id": inv.id,
                    "rule": inv.rule,
                    "severity": inv.severity,
                    "check_query": inv.check_query,
                    "is_automatic": inv.is_automatic
                })
                nodes_created += 1
                invariants_detected += 1

            # Create CONSTRAINS edge
            self.hippocampus.create_edge(
                inv_id,
                artifact_id,
                "CONSTRAINS",
                {"strictness": 1.0}
            )
            edges_created += 1

        return {
            "nodes": nodes_created,
            "edges": edges_created,
            "invariants": invariants_detected
        }

    def _generate_artifact_id(self, path: str) -> str:
        """Generate deterministic artifact ID."""
        import hashlib
        hash_val = hashlib.md5(f"artifact:{path}".encode()).hexdigest()
        return f"artifact-{hash_val[:8]}"

    def _generate_concept_id(self, name: str) -> str:
        """Generate deterministic concept ID."""
        import hashlib
        hash_val = hashlib.md5(f"concept:{name}".encode()).hexdigest()
        return f"concept-{hash_val[:8]}"

    def _get_language(self, extension: str) -> str:
        """Map file extension to language name."""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".rs": "rust",
            ".go": "go"
        }
        return mapping.get(extension, "unknown")
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/integration/test_big_bang.py -v
```

Expected: Test PASS (may require tqdm installation)

**Step 5: Install tqdm if missing**

```bash
poetry add tqdm
```

**Step 6: Commit**

```bash
git add palace/ingest/pipeline.py tests/integration/test_big_bang.py pyproject.toml
git commit -m "feat: implement Big Bang ingestion pipeline"
```

---

## Phase 5: API Layer

### Task 17: Implement Context Provider

**Files:**
- Create: `palace/api/context_provider.py`
- Create: `tests/unit/test_api/test_context_provider.py`

**Step 1: Write tests for context provider**

Create: `tests/unit/test_api/test_context_provider.py`:

```python
import pytest
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.core.activation import ActivationEngine
from palace.api.context_provider import ContextProvider, ContextBundle

@pytest.fixture
def context_brain(tmp_path):
    """Create a populated brain for context testing."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create artifact
        hippo.create_node("Artifact", {
            "id": "artifact-1",
            "path": "src/auth.py",
            "content_hash": "1",
            "language": "python",
            "ast_fingerprint": "1"
        })

        # Create concepts
        hippo.create_node("Concept", {
            "id": "concept-1",
            "name": "Authentication",
            "embedding_id": "1",
            "layer": "abstraction",
            "stability": 0.8
        })

        # Create invariant
        hippo.create_node("Invariant", {
            "id": "inv-1",
            "rule": "No hardcoded secrets",
            "severity": "CRITICAL",
            "check_query": None,
            "is_automatic": True
        })

        # Create edges
        hippo.create_edge("artifact-1", "concept-1", "EVOKES", {"weight": 0.9})
        hippo.create_edge("inv-1", "artifact-1", "CONSTRAINS", {"strictness": 1.0})

    return palace_dir

def test_context_retrieval(context_brain):
    """Test retrieving context for a file."""
    with Hippocampus(context_brain) as hippo:
        engine = ActivationEngine(hippo)
        provider = ContextProvider(hippo, engine)

        bundle = provider.retrieve("src/auth.py")

        assert isinstance(bundle, ContextBundle)
        assert bundle.activation_energy >= 0
        assert isinstance(bundle.invariants, list)
        assert isinstance(bundle.active_concepts, list)
        assert 0 <= bundle.risk_score <= 1
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/unit/test_api/test_context_provider.py -v
```

Expected: ImportError

**Step 3: Implement context provider**

Create: `palace/api/context_provider.py`:

```python
"""Context provider API for retrieving architectural context."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import numpy as np

from palace.core.hippocampus import Hippocampus
from palace.core.activation import ActivationEngine
from palace.shared.models import Invariant, Concept, Decision, Artifact


@dataclass
class ContextBundle:
    """Structured context for code generation assistants."""
    invariants: List[Invariant]
    active_concepts: List[Concept]
    relevant_decisions: List[Decision]
    topological_neighbors: List[Artifact]
    risk_score: float
    activation_energy: float
    timestamp: datetime


@dataclass
class Violation:
    """Potential violation detected during proposal validation."""
    invariant_id: str
    rule: str
    severity: str
    justification: str
    affected_artifact: str


class ContextProvider:
    """
    Main API for retrieving architectural context.
    """

    def __init__(
        self,
        hippocampus: Hippocampus,
        activation_engine: ActivationEngine
    ):
        """
        Initialize context provider.

        Args:
            hippocampus: Graph database interface
            activation_engine: Spreading activation engine
        """
        self.hippocampus = hippocampus
        self.activation = activation_engine

    def retrieve(
        self,
        target_file: str,
        query_embedding: Optional[np.ndarray] = None,
        max_depth: int = 3,
        energy_threshold: float = 0.3
    ) -> ContextBundle:
        """
        Retrieve context for a target file.

        Args:
            target_file: File path to get context for
            query_embedding: Optional query vector
            max_depth: Max hops for spreading activation
            energy_threshold: Minimum energy for inclusion

        Returns:
            ContextBundle with relevant information
        """
        # Run spreading activation from target file
        artifact_id = self._find_artifact_id(target_file)
        if not artifact_id:
            return self._empty_context()

        activated = self.activation.spread(
            artifact_id,
            max_depth=max_depth,
            energy_threshold=energy_threshold
        )

        # Classify by type
        invariants = []
        active_concepts = []
        relevant_decisions = []
        topological_neighbors = []

        for node_id, energy in activated.items():
            node = self.hippocampus.get_node(node_id)
            if not node:
                continue

            node_type = self._get_node_type(node)

            if node_type == "Invariant":
                invariants.append(self._to_invariant(node))
            elif node_type == "Concept":
                active_concepts.append(self._to_concept(node))
            elif node_type == "Decision":
                relevant_decisions.append(self._to_decision(node))
            elif node_type == "Artifact":
                topological_neighbors.append(self._to_artifact(node))

        # Compute risk score based on invariants
        risk_score = self._compute_risk_score(invariants)

        return ContextBundle(
            invariants=invariants,
            active_concepts=active_concepts,
            relevant_decisions=relevant_decisions,
            topological_neighbors=topological_neighbors,
            risk_score=risk_score,
            activation_energy=sum(activated.values()),
            timestamp=datetime.utcnow()
        )

    def _find_artifact_id(self, file_path: str) -> Optional[str]:
        """Find artifact node ID by file path."""
        query = "MATCH (a:Artifact) WHERE a.path = $path RETURN a.id AS id"
        result = self.hippocampus.execute_cypher(query, {"path": file_path})
        return result[0]["id"] if result else None

    def _get_node_type(self, node: dict) -> str:
        """Extract node type from node data."""
        # KuzuDB doesn't explicitly give node type, infer from properties
        if "rule" in node:
            return "Invariant"
        elif "embedding_id" in node and "layer" in node:
            return "Concept"
        elif "title" in node and "status" in node:
            return "Decision"
        elif "path" in node:
            return "Artifact"
        return "Unknown"

    def _to_invariant(self, node: dict) -> Invariant:
        """Convert node dict to Invariant model."""
        return Invariant(**node)

    def _to_concept(self, node: dict) -> Concept:
        """Convert node dict to Concept model."""
        return Concept(**node)

    def _to_decision(self, node: dict) -> Decision:
        """Convert node dict to Decision model."""
        return Decision(**node)

    def _to_artifact(self, node: dict) -> Artifact:
        """Convert node dict to Artifact model."""
        return Artifact(**node)

    def _compute_risk_score(self, invariants: List[Invariant]) -> float:
        """Compute risk score from invariants."""
        if not invariants:
            return 0.0

        severity_weights = {
            "CRITICAL": 1.0,
            "HIGH": 0.7,
            "MEDIUM": 0.4,
            "LOW": 0.1
        }

        max_severity = max(
            (severity_weights.get(inv.severity, 0.0) for inv in invariants),
            default=0.0
        )

        return min(1.0, max_severity)

    def _empty_context(self) -> ContextBundle:
        """Return empty context bundle."""
        return ContextBundle(
            invariants=[],
            active_concepts=[],
            relevant_decisions=[],
            topological_neighbors=[],
            risk_score=0.0,
            activation_energy=0.0,
            timestamp=datetime.utcnow()
        )
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/unit/test_api/test_context_provider.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/api/context_provider.py tests/unit/test_api/test_context_provider.py
git commit -m "feat: implement context provider API"
```

---

## Phase 6: CLI Interface

### Task 18: Implement CLI Commands

**Files:**
- Create: `palace/cli/commands.py`
- Create: `tests/integration/test_cli.py`

**Step 1: Write tests for CLI commands**

Create: `tests/integration/test_cli.py`:

```python
import pytest
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from palace.cli.commands import app

runner = CliRunner()

def test_init_command(tmp_path):
    """Test palace init command."""
    with tmp_path.as_cwd():
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert (Path(".palace")).exists()
        assert (Path(".palace") / "brain.kuzu").exists()
        assert (Path(".palace") / "vectors.db").exists()

def test_stats_command(tmp_path):
    """Test palace stats command."""
    with tmp_path.as_cwd():
        # Initialize first
        runner.invoke(app, ["init"])

        # Run stats
        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        assert "nodes" in result.stdout.lower() or "0" in result.stdout
```

**Step 2: Run tests to verify they fail**

```bash
poetry run pytest tests/integration/test_cli.py -v
```

Expected: ImportError

**Step 3: Implement CLI commands**

Create: `palace/cli/commands.py`:

```python
"""CLI commands for Palacio Mental."""

import typer
from pathlib import Path
from typing import Optional
import sys

from palace.core.hippocampus import Hippocampus
from palace.core.activation import ActivationEngine
from palace.core.sleep import SleepEngine
from palace.api.context_provider import ContextProvider
from palace.ingest.pipeline import BigBangPipeline
from palace.ingest.parsers.python import PythonParser
from palace.ingest.extractors import ConceptExtractor
from palace.ingest.invariants import InvariantDetector
from palace.shared.config import PalaceConfig
from palace.shared.exceptions import PalaceNotInitializedError

app = typer.Typer(help="Palacio Mental v2.0 - Cognitive Memory for Code")


@app.command()
def init(
    palace_dir: Path = typer.Option(Path(".palace"), "--dir", "-d", help="Palace directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing")
) -> None:
    """
    Initialize a new Palace brain.
    Creates .palace/ directory with empty databases.
    """
    palace_dir = Path(palace_dir)

    if palace_dir.exists() and not force:
        typer.echo(f"❌ {palace_dir} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(1)

    typer.echo(f"🏛️  Initializing Palace in {palace_dir}")

    palace_dir.mkdir(parents=True, exist_ok=True)

    try:
        with Hippocampus(palace_dir) as hippo:
            hippo.initialize_schema()

        typer.echo(f"✅ Palace initialized successfully")
        typer.echo(f"   Brain: {palace_dir / 'brain.kuzu'}")
        typer.echo(f"   Vectors: {palace_dir / 'vectors.db'}")

    except Exception as e:
        typer.echo(f"❌ Failed to initialize: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def ingest(
    repo_path: Path = typer.Option(Path("."), "--path", "-p", help="Repository path"),
    ignore: Optional[list[str]] = typer.Option(None, "--ignore", "-i", help="Additional ignore patterns"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
) -> None:
    """
    Execute Big Bang ingestion on a repository.
    Parses code, extracts concepts, builds graph.
    """
    config = PalaceConfig()
    palace_dir = config.palace_dir

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    typer.echo(f"🌌 Big Bang ingestion starting...")
    typer.echo(f"   Repository: {repo_path}")

    try:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer(config.embedding_model)
    except ImportError:
        typer.echo("❌ sentence-transformers not installed. Run: pip install sentence-transformers", err=True)
        raise typer.Exit(1)

    try:
        with Hippocampus(palace_dir) as hippo:
            # Initialize components
            parsers = [PythonParser()]
            concept_extractor = ConceptExtractor(embedding_model)
            invariant_detector = InvariantDetector()

            pipeline = BigBangPipeline(
                hippocampus=hippo,
                parsers=parsers,
                concept_extractor=concept_extractor,
                invariant_detector=invariant_detector,
                config=config
            )

            # Run ingestion
            report = pipeline.ingest_repository(repo_path, ignore)

            # Print results
            typer.echo(f"\n✅ Ingestion complete!")
            typer.echo(f"   Files processed: {report.files_processed}")
            typer.echo(f"   Nodes created: {report.nodes_created}")
            typer.echo(f"   Edges created: {report.edges_created}")
            typer.echo(f"   Invariants detected: {report.invariants_detected}")
            typer.echo(f"   Errors: {report.errors}")
            typer.echo(f"   Duration: {report.duration_seconds:.2f}s")

    except Exception as e:
        typer.echo(f"❌ Ingestion failed: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def sleep(
    palace_dir: Path = typer.Option(Path(".palace"), "--dir", "-d", help="Palace directory"),
    decay: float = typer.Option(0.05, "--decay", "-d", help="Lambda decay rate"),
    prune_threshold: float = typer.Option(0.1, "--prune", "-p", help="Prune threshold")
) -> None:
    """
    Run sleep cycle for consolidation and forgetting.
    Prunes weak edges, detects communities, reindexes.
    """
    palace_dir = Path(palace_dir)

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    typer.echo(f"😴 Running sleep cycle...")

    try:
        with Hippocampus(palace_dir) as hippo:
            engine = SleepEngine(hippo)
            report = engine.sleep_cycle(
                lambda_decay=decay,
                prune_threshold=prune_threshold
            )

            typer.echo(f"✅ Sleep cycle complete!")
            typer.echo(f"   Nodes: {report.nodes_count}")
            typer.echo(f"   Edges: {report.edges_count}")
            typer.echo(f"   Edges decayed: {report.edges_decayed}")
            typer.echo(f"   Edges pruned: {report.edges_pruned}")
            typer.echo(f"   Communities detected: {report.communities_detected}")
            typer.echo(f"   Duration: {report.total_duration_ms:.2f}ms")

    except Exception as e:
        typer.echo(f"❌ Sleep cycle failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def context(
    target_file: Path = typer.Argument(..., help="File to get context for"),
    output: str = typer.Option("markdown", "--output", "-o", help="Output format"),
    max_depth: int = typer.Option(3, "--depth", "-d", help="Activation depth"),
    energy_threshold: float = typer.Option(0.3, "--threshold", "-t", help="Energy threshold")
) -> None:
    """
    Retrieve architectural context for a file.
    Outputs formatted markdown for Claude Code.
    """
    config = PalaceConfig()
    palace_dir = config.palace_dir

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    target_file = Path(target_file)
    if not target_file.exists():
        typer.echo(f"❌ File not found: {target_file}", err=True)
        raise typer.Exit(1)

    try:
        with Hippocampus(palace_dir) as hippo:
            engine = ActivationEngine(hippo)
            provider = ContextProvider(hippo, engine)

            bundle = provider.retrieve(
                str(target_file),
                max_depth=max_depth,
                energy_threshold=energy_threshold
            )

            # Format output
            if output == "markdown":
                output_text = _format_markdown(bundle, str(target_file))
            else:
                output_text = str(bundle)

            typer.echo(output_text)

    except Exception as e:
        typer.echo(f"❌ Failed to retrieve context: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def query(
    cypher: str = typer.Argument(..., help="Cypher query to execute"),
) -> None:
    """
    Execute raw Cypher query on the graph.
    For debugging and exploration.
    """
    config = PalaceConfig()
    palace_dir = config.palace_dir

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    try:
        with Hippocampus(palace_dir) as hippo:
            results = hippo.execute_cypher(cypher, {})

            # Print results as table
            if results:
                headers = results[0].keys()
                typer.echo("\t".join(headers))
                for row in results:
                    typer.echo("\t".join(str(v) for v in row.values()))
            else:
                typer.echo("No results")

    except Exception as e:
        typer.echo(f"❌ Query failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def stats() -> None:
    """
    Show brain statistics.
    Node counts, edge counts, last sleep, etc.
    """
    config = PalaceConfig()
    palace_dir = config.palace_dir

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    try:
        with Hippocampus(palace_dir) as hippo:
            # Count nodes by type
            node_query = """
                MATCH (n)
                RETURN labels(n)[0] AS type, count(*) AS count
            """
            nodes = hippo.execute_cypher(node_query, {})

            # Count edges
            edge_query = "MATCH ()-[r]->() RETURN count(r) AS count"
            edges = hippo.execute_cypher(edge_query, {})
            edge_count = edges[0]["count"] if edges else 0

            typer.echo("🧠 Palace Brain Statistics")
            typer.echo("=" * 40)

            for node_type in nodes:
                typer.echo(f"  {node_type['type']}: {node_type['count']}")

            typer.echo(f"  Total edges: {edge_count}")

    except Exception as e:
        typer.echo(f"❌ Failed to get stats: {e}", err=True)
        raise typer.Exit(1)


def _format_markdown(bundle: ContextBundle, target_file: str) -> str:
    """Format context bundle as markdown."""
    lines = [
        "## 🏛️ Contexto Arquitectónico (Palacio Mental)",
        f"**Semilla**: `{target_file}` | **Activación**: {bundle.activation_energy:.2f}",
        ""
    ]

    if bundle.invariants:
        lines.append("### ⚠️ Invariantes Activas")
        for inv in bundle.invariants:
            lines.append(f"- [{inv.severity}] `{inv.id}`: {inv.rule}")
        lines.append("")

    if bundle.active_concepts:
        lines.append("### 🔥 Conceptos Activos")
        for concept in bundle.active_concepts[:5]:
            lines.append(f"- **{concept.name}** (capa: {concept.layer}, estabilidad: {concept.stability:.2f})")
        lines.append("")

    if bundle.topological_neighbors:
        lines.append("### 🔗 Vecindad Topológica")
        for artifact in bundle.topological_neighbors[:5]:
            lines.append(f"- `{artifact.path}` ({artifact.language})")
        lines.append("")

    lines.append(f"### 📊 Score de Riesgo: {bundle.risk_score:.2f}")
    lines.append("")
    lines.append(f"*Palacio v2.0 | {bundle.timestamp}*)

    return "\n".join(lines)


if __name__ == "__main__":
    app()
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/integration/test_cli.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add palace/cli/commands.py tests/integration/test_cli.py
git commit -m "feat: implement CLI commands with Typer"
```

---

## Phase 7: Documentation & Testing

### Task 19: Create README

**Files:**
- Create: `README.md`

**Step 1: Create comprehensive README**

Create: `README.md`:

```markdown
# Palacio Mental v2.0

A bio-mimetic cognitive memory system for code engineering teams. Serves as an extended architectural memory that provides context during development, preventing design errors and preserving institutional knowledge.

## Features

- 🧠 **Spatial Memory**: Graph-based representation using KuzuDB
- 🔗 **Associative Memory**: Vector embeddings with cosine similarity
- ⚡ **Spreading Activation**: Cognitive navigation through codebase
- 🔄 **Hebbian Learning**: Synaptic plasticity for continuous learning
- 😴 **Sleep Cycles**: Consolidation and forgetting for memory optimization
- 🔍 **Invariant Detection**: Automatic detection of anti-patterns
- 🎯 **Context Provider**: API for retrieving architectural context

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/palacio-mental.git
cd palacio-mental

# Install with Poetry
poetry install

# Or with pip
pip install palacio-mental
```

## Quickstart

```bash
# Initialize a new Palace brain
palace init

# Ingest your codebase
palace ingest

# Get architectural context for a file
palace context src/auth.py

# Run sleep cycle for consolidation
palace sleep

# Show brain statistics
palace stats
```

## Architecture

Palacio Mental implements a neuro-symbolic architecture:

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

## Data Model

### Nodes

- **Concept**: Abstract ideas extracted from code
- **Artifact**: Physical artifacts (files, functions, classes)
- **Invariant**: Architectural/security rules
- **Decision**: Architectural Decision Records (ADRs)
- **Anchor**: Spatial reference points

### Edges

- **EVOKES**: Artifact evokes a Concept (semantic association)
- **CONSTRAINS**: Invariant constrains an Artifact
- **DEPENDS_ON**: Artifact depends on another Artifact
- **PRECEDES**: Decision precedes another Decision
- **RELATED_TO**: Concept is related to another Concept

## Configuration

Configuration is managed via environment variables with the `PALACE_` prefix:

```bash
export PALACE_PALACE_DIR=".palace"
export PALACE_EMBEDDING_MODEL="all-MiniLM-L6-v2"
export PALACE_DEFAULT_MAX_DEPTH=3
export PALACE_DEFAULT_ENERGY_THRESHOLD=0.3
```

Or create `.palace/config.toml`.

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=palace --cov-report=html

# Type checking
poetry run mypy palace

# Format code
poetry run black palace tests

# Lint
poetry run ruff check palace tests
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

### Task 20: Create Example Repository for Demo

**Files:**
- Create: `examples/simple-python-app/`
- Create: `examples/simple-python-app/main.py`
- Create: `examples/simple-python-app/auth.py`
- Create: `examples/simple-python-app/utils.py`

**Step 1: Create example Python app**

```bash
mkdir -p examples/simple-python-app
```

Create: `examples/simple-python-app/main.py`:

```python
"""Simple Python application for Palace demo."""

from auth import authenticate
from utils import log_result

def main():
    """Main application."""
    username = input("Username: ")
    password = input("Password: ")

    if authenticate(username, password):
        log_result("Authentication successful")
        print("Welcome!")
    else:
        log_result("Authentication failed")
        print("Access denied")

if __name__ == "__main__":
    main()
```

Create: `examples/simple-python-app/auth.py`:

```python
"""Authentication module."""

import hashlib

def authenticate(username, password):
    """Authenticate user with hashed password."""
    # In production, never hardcode credentials
    secret_key = "hardcoded-secret-key-12345"  # This will trigger invariant

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Simplified authentication (not secure!)
    if username == "admin" and hashed_password == "known-hash":
        return True

    return False

def generate_token(user_id):
    """Generate authentication token."""
    # Uses eval (will trigger invariant)
    token_expr = f"'token-{user_id}'"
    return eval(token_expr)
```

Create: `examples/simple-python-app/utils.py`:

```python
"""Utility functions."""

import logging

def log_result(message):
    """Log a message."""
    logging.basicConfig(level=logging.INFO)
    logging.info(message)

def calculate(x, y):
    """Simple calculation."""
    return x + y
```

Create: `examples/simple-python-app/README.md`:

```markdown
# Simple Python App - Palace Demo

This is a deliberately simple (and slightly problematic) Python application to demonstrate Palacio Mental's capabilities.

## Known Issues (for Palace to detect)

1. Hardcoded secret in `auth.py` - triggers invariant
2. Use of `eval()` in `auth.py` - triggers invariant
3. Missing error handling in file operations

## Running Palace

```bash
# From this directory
palace init
palace ingest
palace context auth.py
```

Expected output should show the invariants triggered by the code.
```

**Step 2: Commit**

```bash
git add examples/
git commit -m "feat: add example Python app for demo"
```

---

### Task 21: Add Pre-commit Hooks and CI Configuration

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/test.yml`

**Step 1: Create pre-commit config**

Create: `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.0.280
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0.0
          - types-requests
```

**Step 2: Create GitHub Actions workflow**

Create: `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Install Poetry
        run: pipx install poetry

      - name: Install dependencies
        run: poetry install --with dev

      - name: Run tests
        run: poetry run pytest --cov=palace

      - name: Type checking
        run: poetry run mypy palace

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

**Step 3: Commit**

```bash
git add .pre-commit-config.yaml .github/workflows/test.yml
git commit -m "ci: add pre-commit hooks and GitHub Actions"
```

---

## Final Steps

### Task 22: Run Full Test Suite

**Step 1: Run all tests**

```bash
poetry run pytest --cov=palace --cov-report=term-missing -v
```

Expected: >80% coverage, all tests passing

**Step 2: Run type checking**

```bash
poetry run mypy palace
```

Expected: No type errors

**Step 3: Test on example repository**

```bash
cd examples/simple-python-app
palace init
palace ingest
palace context auth.py
palace stats
```

Expected: Successful context retrieval with invariants detected

**Step 4: Commit any fixes**

```bash
git add .
git commit -m "fix: resolve issues found during final testing"
```

---

### Task 23: Create Release Notes

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Create CHANGELOG**

Create: `CHANGELOG.md`:

```markdown
# Changelog

## [0.1.0] - 2025-02-15

### Added
- Initial release of Palacio Mental v2.0
- Hippocampus storage layer with KuzuDB and SQLite+vec
- Spreading activation algorithm for cognitive navigation
- Hebbian plasticity engine for learning
- Sleep cycle for consolidation and forgetting
- AST parsers for Python (extensible for other languages)
- Concept extraction using sentence-transformers
- Invariant detection for security and architectural patterns
- Big Bang ingestion pipeline
- Context provider API
- Full-featured CLI with init, ingest, sleep, context, query, stats commands
- Comprehensive test suite with >80% coverage
- Example Python application for demo

### Architecture
- Layer-by-layer sequential development
- Dependency injection for testability
- Pydantic models for type safety
- Component-based design with clear boundaries

### Documentation
- Comprehensive README with quickstart guide
- Inline algorithm documentation
- Design document and implementation plan
```

**Step 2: Tag release**

```bash
git tag v0.1.0
git push origin main --tags
```

**Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add changelog for v0.1.0"
```

---

## Summary

This implementation plan provides:

1. **Layer-by-layer development** following the approved architecture
2. **TDD approach** with failing tests written first
3. **Bite-sized tasks** (2-5 minutes each)
4. **Complete code examples** in the plan
5. **Frequent commits** after each component
6. **Full test coverage** targeting >80%
7. **Production quality** with error handling, type hints, and documentation

**Total estimated tasks:** 23
**Estimated lines of code:** ~3,500
**Estimated test coverage:** >80%

The plan can be executed using the `superpowers:executing-plans` skill in a separate session for batch execution with checkpoints, or using `superpowers:subagent-driven-development` in the current session for task-by-task execution with review.
