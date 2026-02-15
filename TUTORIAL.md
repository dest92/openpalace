# Tutorial

This tutorial will guide you through using Palacio Mental to build a cognitive memory system for your codebase.

## Prerequisites

Before starting, ensure you have:
- Python 3.10 or higher
- Poetry (for dependency management)
- A codebase you want to analyze

## Installation

### Step 1: Install Palace

```bash
# Clone the repository
git clone https://github.com/dest92/openpalace.git
cd openpalace

# Install dependencies with Poetry
poetry install

# Verify installation
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
```

## Step 2: Prepare Your Codebase

For this tutorial, we'll use a sample project. Create one:

```bash
mkdir ~/sample-project
cd ~/sample-project

# Create a simple Python project structure
mkdir -p src/auth src/database src/api

# Create sample files (we'll add content next)
touch src/auth/__init__.py src/auth/login.py
touch src/database/__init__.py src/database/connection.py
touch src/api/__init__.py src/api/endpoints.py
touch main.py
```

Add some sample code to `src/auth/login.py`:

```python
"""Authentication module for user login."""

import hashlib
from typing import Optional

from ..database.connection import Database


class UserAuthenticator:
    """Handles user authentication."""

    def __init__(self, db: Database):
        self.db = db

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user.

        Args:
            username: The username
            password: The password (will be hashed)

        Returns:
            True if authentication successful
        """
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Query database
        query = "SELECT id, password_hash FROM users WHERE username = ?"
        result = self.db.execute(query, (username,))

        if not result:
            return False

        stored_hash = result[0]['password_hash']
        return password_hash == stored_hash

    def create_user(self, username: str, password: str) -> bool:
        """Create a new user account."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        return self.db.execute(query, (username, password_hash))
```

Add code to `src/database/connection.py`:

```python
"""Database connection management."""

import sqlite3
from typing import List, Dict, Any, Optional


class Database:
    """SQLite database wrapper."""

    def __init__(self, path: str):
        self.path = path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Establish database connection."""
        self._connection = sqlite3.connect(self.path)

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()

    def execute(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query with ? placeholders
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row))
                for row in cursor.fetchall()]
```

Add code to `src/api/endpoints.py`:

```python
"""API endpoints for authentication."""

from typing import Dict, Any
from ..auth.login import UserAuthenticator
from ..database.connection import Database


class AuthEndpoints:
    """HTTP endpoints for authentication."""

    def __init__(self):
        self.db = Database("users.db")
        self.auth = UserAuthenticator(self.db)

    def login(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle login request.

        Args:
            request: HTTP request with username/password

        Returns:
            Response dict with status/token
        """
        username = request.get('username')
        password = request.get('password')

        if not username or not password:
            return {'error': 'Missing credentials'}

        if self.auth.authenticate(username, password):
            return {'status': 'success', 'token': 'sample-jwt-token'}

        return {'error': 'Invalid credentials'}
```

## Step 3: Initialize Palace

```bash
# In your project directory
cd ~/sample-project

# Initialize Palace
palace init
```

This creates a `.palace/` directory with empty databases:

```
.palace/
├── brain.kuzu    # Graph database
└── vectors.db    # Vector database
```

## Step 4: Ingest Your Code

```bash
# Ingest all Python files
palace ingest

# Or ingest specific patterns
palace ingest --file-pattern "src/**/*.py"
```

Expected output:
```
Found 6 files
✓ src/auth/__init__.py: 0 symbols
✓ src/auth/login.py: 3 symbols
✓ src/database/__init__.py: 0 symbols
✓ src/database/connection.py: 4 symbols
✓ src/api/__init__.py: 0 symbols
✓ src/api/endpoints.py: 2 symbols
Ingestion complete!
```

**What happened?**
1. Palace scanned your files
2. Parsed each file to extract:
   - Dependencies (imports, function calls)
   - Symbols (classes, functions, methods)
   - AST fingerprints (structural signatures)
3. Created Artifact nodes for each file
4. Detected Invariant violations (if any)
5. Built dependency graph with DEPENDS_ON edges

## Step 5: Query the Knowledge Graph

### Get Context for a File

```bash
palace context src/auth/login.py
```

Expected output:
```
Context for src/auth/login.py

Related files: 2
  - src/database/connection.py (energy: 0.72)
  - src/api/endpoints.py (energy: 0.58)

Related concepts: 3
  - Authentication (abstraction) - 0.85
  - Security (abstraction) - 0.63
  - Password Management (implementation) - 0.51

Invariants: 1
  - Use parameterized queries (MEDIUM)
```

**What does this tell us?**
- `login.py` is strongly connected to `connection.py` (imports Database class)
- It's semantically related to authentication and security concepts
- There's a reminder about using parameterized queries (good practice!)

### Explore Related Code

Let's check what depends on `login.py`:

```bash
# Query the graph directly
palace query "MATCH (a:Artifact)-[r:DEPENDS_ON]->(b:Artifact) WHERE b.path = 'src/auth/login.py' RETURN a.path"
```

## Step 6: Understanding Spreading Activation

The core power of Palace is cognitive navigation - finding related code through spreading activation.

### How It Works

1. **Start with a seed node** (e.g., `src/auth/login.py`)
2. **Activation spreads** along edges to connected nodes
3. **Energy decays** with each hop (default 0.8)
4. **Transmission varies** by edge type:
   - CONSTRAINS: 1.0 (rules transmit fully)
   - EVOKES: 0.9 (strong semantic link)
   - DEPENDS_ON: 0.7 (code dependency)
   - RELATED_TO: 0.5 (conceptual association)

### Example Walkthrough

Starting from `login.py`:

```
Hop 0: login.py (energy 1.0)
  ↓ DEPENDS_ON (0.7)
Hop 1: connection.py (energy 0.56)
  ↓ DEPENDS_ON (0.7)
Hop 2: sqlite3 module (not in graph)
```

Result: Palace discovers that `login.py` and `connection.py` are closely related.

## Step 7: Run Sleep Cycle

Over time, the knowledge graph accumulates weak connections. Run sleep cycles to consolidate memory:

```bash
palace sleep
```

Expected output:
```
Sleep cycle complete!
Nodes: 6
Edges: 8
Edges decayed: 2
Edges pruned: 0
Duration: 12.34ms
```

**What happened?**
1. Old connections had their weights decayed
2. Weak connections (weight < 0.1) were pruned
3. Frequently-used patterns were strengthened
4. Memory was optimized

## Step 8: Using Palace for Code Navigation

### Scenario: Understanding a Codebase

You're a new developer joining a team. Here's how Palace helps:

**Step 1:** Start with any file you're working on:

```bash
palace context src/api/endpoints.py
```

**Step 2:** Explore related files:

```bash
# Check what endpoints.py depends on
palace query "MATCH (a:Artifact)-[r:DEPENDS_ON]->(b:Artifact) WHERE a.path = 'src/api/endpoints.py' RETURN b.path"
```

**Step 3:** Find related concepts:

```bash
# What concepts does this file evoke?
palace query "MATCH (a:Artifact)-[r:EVOKES]->(c:Concept) WHERE a.path = 'src/api/endpoints.py' RETURN c.name, c.layer"
```

**Step 4:** Discover architectural decisions:

```bash
# Are there any decisions related to authentication?
palace query "MATCH (d:Decision) WHERE d.title CONTAINS 'auth' RETURN d.title, d.status"
```

### Scenario: Impact Analysis

You need to modify `connection.py`. What will break?

```bash
# Find all files that depend on connection.py
palace query "MATCH (a:Artifact)-[r:DEPENDS_ON]->(b:Artifact) WHERE b.path = 'src/database/connection.py' RETURN a.path"
```

This shows you all files that will be affected by your changes.

### Scenario: Finding Security Issues

```bash
# Find all invariants related to security
palace query "MATCH (i:Invariant) WHERE i.rule CONTAINS 'security' OR i.severity = 'CRITICAL' RETURN i.rule, i.severity"
```

## Step 9: Advanced Usage

### Custom Configuration

Create `.palace/config.toml`:

```toml
[palace]
# Ingestion settings
ignore_patterns = [
    "node_modules",
    ".git",
    "__pycache__",
    "tests",
    "*.pyc"
]
max_file_size_mb = 10

# Embedding settings
embedding_model = "all-MiniLM-L6-v2"
embedding_dim = 384

# Activation settings
default_max_depth = 3
default_energy_threshold = 0.3
default_decay_factor = 0.8

# Sleep settings
default_lambda_decay = 0.05
default_prune_threshold = 0.1
auto_sleep_after_ingest = false
```

### Environment Variables

```bash
# Set embedding model
export PALACE_EMBEDDING_MODEL="all-mpnet-base-v2"

# Set activation parameters
export PALACE_DEFAULT_MAX_DEPTH=4
export PALACE_DEFAULT_ENERGY_THRESHOLD=0.2

# Run ingest with custom settings
palace ingest
```

### Integration with CI/CD

Add to your `.github/workflows/test.yml`:

```yaml
- name: Check for architectural violations
  run: |
    palace ingest
    palace query "MATCH (i:Invariant) WHERE i.severity = 'CRITICAL' RETURN count(i) > 0"
```

## Step 10: Best Practices

### 1. Regular Ingestion

After making changes, re-run ingestion:

```bash
# After each coding session
git add .
git commit -m "Add new feature"
palace ingest
```

### 2. Periodic Sleep Cycles

Run sleep cycles to keep memory optimized:

```bash
# Weekly or after major changes
palace sleep
```

### 3. Use Context Before Coding

Before modifying a file, check what's related:

```bash
palace context src/auth/login.py
```

This helps you understand impact and dependencies.

### 4. Combine with Version Control

```bash
# See what changed since last ingestion
git diff --name-only HEAD | palace ingest --file-pattern -
```

### 5. Document Architectural Decisions

Add ADRs to the knowledge graph:

```python
from palace.core.hippocampus import Hippocampus

with Hippocampus(Path(".palace")) as hippo:
    hippo.create_node("Decision", {
        "id": "decision-use-postgres",
        "title": "Use PostgreSQL for primary database",
        "timestamp": datetime.now(),
        "status": "ACCEPTED",
        "rationale": "Better JSON support, superior indexing, active community"
    })
```

## Troubleshooting

### Issue: "File not found in knowledge graph"

**Cause:** File hasn't been ingested yet.

**Solution:** Run `palace ingest` again.

### Issue: High memory usage during ingestion

**Cause:** Large codebase with many files.

**Solution:**
- Use `--file-pattern` to limit scope
- Increase `batch_size` in config
- Run ingestion in chunks

### Issue: No related concepts found

**Cause:** Concept extraction is disabled (default for speed).

**Solution:** Enable concept extractor:

```python
from palace.ingest.pipeline import BigBangPipeline
from palace.ingest.extractors import ConceptExtractor

pipeline = BigBangPipeline(
    hippo,
    concept_extractor=ConceptExtractor()  # Enable NLP
)
```

### Issue: Too many weak connections

**Cause:** Graph needs consolidation.

**Solution:** Run `palace sleep` with lower prune threshold.

## Next Steps

Now that you understand the basics:

1. **Explore the API**: Use `Hippocampus` directly in Python scripts
2. **Extend parsers**: Add support for other languages (TypeScript, Go, Rust)
3. **Custom algorithms**: Implement your own spreading activation strategies
4. **Integrate with editors**: Build VS Code or Neovim plugins
5. **Contribute**: Open issues and PRs on GitHub

## Resources

- [GitHub Repository](https://github.com/dest92/openpalace)
- [Glossary](GLOSSARY.md) - Understand terminology
- [Demo](DEMO.md) - See real-world usage examples
- [CLAUDE.md](CLAUDE.md) - For AI code assistance

## Summary

Palace helps you:
- **Navigate code** cognitively (find related code by meaning, not just structure)
- **Understand impact** (see what depends on what)
- **Detect violations** (find architectural problems)
- **Optimize memory** (consolidate and prune connections)
- **Learn patterns** (discover how concepts relate)

Happy coding with cognitive memory! 🧠
