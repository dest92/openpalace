# Multi-Language Support

OpenPalace supports parsing and analyzing code across multiple programming languages, enabling you to work with polyglot codebases.

## Supported Languages

| Language | File Extensions | Parser | Status |
|----------|----------------|----------|--------|
| Python | `.py`, `.pyx` | stdlib `ast` | ✅ Stable |
| JavaScript | `.js`, `.jsx`, `.mjs`, `.cjs` | tree-sitter | ✅ Stable |
| TypeScript | `.ts`, `.tsx` | tree-sitter | ✅ Stable |
| Go | `.go` | tree-sitter | ✅ Stable |

## Installation

### Basic Installation

```bash
# Install OpenPalace
pip install palacio-mental

# Or using poetry
poetry add palacio-mental
```

### Language-Specific Dependencies

OpenPalace uses tree-sitter for JavaScript, TypeScript, and Go parsing. These are optional dependencies:

```bash
# Install all language parsers
poetry install --extras all-languages

# Or install specific languages
poetry install --extras javascript
poetry install --extras typescript
poetry install --extras go

# Install multiple languages
poetry install --extras javascript,typescript,go
```

**Note**: Python parsing uses the standard library `ast` module and requires no additional dependencies.

## Usage

### Basic Ingestion

Ingest all supported code files:

```bash
palace init
palace ingest
```

By default, OpenPalace searches for files matching: `**/*.{py,js,jsx,ts,tsx,go}`

### Language Filtering

Only ingest specific languages:

```bash
# Only ingest Python files
palace ingest --languages python

# Only ingest JavaScript/TypeScript
palace ingest --languages javascript,typescript

# Only ingest Go files
palace ingest --languages go
```

### Custom File Patterns

Specify custom file patterns:

```bash
# Ingest only TypeScript files
palace ingest "**/*.ts"

# Ingest files in a specific directory
palace ingest "src/**/*.ts"

# Mix multiple patterns
palace ingest "**/*.{py,ts}"
```

## Framework-Specific Features

### Next.js

OpenPalace includes special support for Next.js projects:

- **Router Detection**: Automatically detects Pages Router (`/pages/`) or App Router (`/app/`)
- **Route Extraction**: Extracts route metadata for both routers
- **API Routes**: Identifies and catalogs API routes from `/pages/api/` or `/app/api/`

Next.js projects are automatically detected by the presence of `next.config.js` or `next.config.ts`.

## Parser Architecture

OpenPalace uses a **hybrid parser strategy**:

- **Python**: Uses Python's stdlib `ast` module (zero dependencies, maximum compatibility)
- **JavaScript/TypeScript/Go**: Use tree-sitter (unified API, battle-tested)

This approach ensures:
- ✅ Zero breaking changes for existing Python codebases
- ✅ Fast, reliable parsing across languages
- ✅ Extensible architecture for adding new languages

## Adding New Languages

To add support for a new language:

1. **Create a parser class** inheriting from `TreeSitterParser`:

```python
from palace.ingest.parsers.tree_sitter_parser import TreeSitterParser
from palace.ingest.parsers.base import Dependency, Symbol

class MyLangParser(TreeSitterParser):
    def __init__(self):
        super().__init__("mylang")
        self._initialize_mylang_grammar()

    def supported_extensions(self):
        return [".ml", ".mylang"]

    def parse_dependencies(self, file_path, content):
        # Extract imports/requires
        deps = []
        # ... your extraction logic
        return deps

    def extract_symbols(self, content):
        # Extract functions, classes, etc.
        symbols = []
        # ... your extraction logic
        return symbols
```

2. **Register the parser** in `ParserRegistry._register_builtin_parsers()`:

```python
try:
    from palace.ingest.parsers.mylang import MyLangParser
    mylang_parser = MyLangParser()
    if mylang_parser.is_available():
        self.register(mylang_parser, language="mylang")
except Exception:
    pass  # Parser not available
```

3. **Add the tree-sitter grammar** to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
tree-sitter-mylang = "^0.20.0"  # Optional
```

## Migration from Python-Only

If you've been using OpenPalace with Python-only repositories:

### ✅ No Changes Required!

Existing Python repositories continue to work exactly as before:

```bash
# Still works - ingests Python files
palace ingest

# Explicitly Python only
palace ingest --languages python
```

### Gradual Rollout

As you add multi-language support to your codebase:

```bash
# Ingest everything (Python + other languages)
palace ingest

# Or explicitly include new languages
palace ingest --languages python,javascript,typescript
```

## Performance

### Fingerprinting

All parsers compute AST fingerprints for change detection:

- **Incremental Parsing**: Only re-parse changed files
- **Fast Fingerprinting**: Tree structure hashing (not full AST serialization)
- **Language Agnostic**: Same fingerprinting strategy across all languages

### Scalability

OpenPalace has been tested with:

- Monorepos with 10,000+ files
- Mixed-language projects (Python + TypeScript + Go)
- Large files (>5000 lines of code)

## Troubleshooting

### Parser Not Available

If you see warnings about missing parsers:

```bash
⚠️  Found 5 .js files (skipped - no parser for javascript files)
```

**Solution**: Install the required tree-sitter grammar:

```bash
poetry add tree-sitter-javascript
# Or for all languages
poetry add tree-sitter-javascript tree-sitter-typescript tree-sitter-go
```

### Files Being Skipped

If files are being skipped unexpectedly:

1. **Check file extension**:
   ```bash
   palace stats  # See what languages were detected
   ```

2. **Check parser availability**:
   ```python
   from palace.ingest.parsers.registry import ParserRegistry
   registry = ParserRegistry.instance()
   print(f"Supported: {registry.get_supported_extensions()}")
   print(f"Languages: {registry.get_supported_languages()}")
   ```

3. **Use explicit pattern**:
   ```bash
   palace ingest "**/*.{py,js,ts}"  # Explicit pattern
   ```

## Examples

### Multi-Language Monorepo

```bash
# Initialize in monorepo root
cd /path/to/monorepo
palace init

# Ingest all code (Python backend, TS frontend, Go services)
palace ingest

# Query across all languages
palace query "MATCH (a:Artifact) WHERE a.language IN ['python', 'typescript', 'go'] RETURN a.path"
```

### Next.js Full-Stack App

```bash
# Initialize in Next.js project
cd /path/to/nextjs-app
palace init

# Ingest everything (React components, API routes, Python backend)
palace ingest

# Get context for a component
palace context src/components/Header.tsx

# Query for API routes
palace query "MATCH (a:Artifact) WHERE a.path CONTAINS 'api' RETURN a.path"
```

### Microservices Architecture

```bash
# Service 1: Python API
cd services/api && palace init && palace ingest --languages python

# Service 2: Go service
cd services/auth && palace init && palace ingest --languages go

# Service 3: TypeScript frontend
cd frontend && palace init && palace ingest --languages typescript
```

## API Reference

### ParserRegistry

```python
from palace.ingest.parsers.registry import ParserRegistry

# Get singleton instance
registry = ParserRegistry.instance()

# Get parser for a file
parser = registry.get_parser(Path("test.js"))

# Detect language
language = registry.detect_language(Path("test.py"))  # "python"

# Get all supported
extensions = registry.get_supported_extensions()
languages = registry.get_supported_languages()
```

### BigBangPipeline

```python
from palace.ingest.pipeline import BigBangPipeline
from palace.core.hippocampus import Hippocampus

with Hippocampus(".palace") as hippo:
    pipeline = BigBangPipeline(hippo)

    # Ingest any supported file
    result = pipeline.ingest_file(Path("src/main.ts"))

    if result["status"] == "success":
        print(f"Ingested: {result['symbols']} symbols")
```

## Contributing

Want to add support for a new language? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Implementing tree-sitter parsers
- Adding framework-specific enhancements
- Testing new language support
- Updating documentation
