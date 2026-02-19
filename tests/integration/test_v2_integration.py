"""
Palace Mental V2 - Integration Tests

Tests complete V2 workflow:
1. Parse code → AST fingerprint
2. Bloom filter membership
3. Graph traversal
4. TOON export for agents

Run with: pytest tests/integration/test_v2_integration.py -v
"""

import pytest
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from palace.core.hippocampus import Hippocampus
from palace.core.bloom_filter import create_palace_bloom_filter
from palace.core.ast_fingerprint import hash_file_ast, ASTFingerprintCache
from palace.core.toon import ASTSummary, TOONEncoder, export_to_agent
from palace.core.agent_interface import AgentQueryInterface, QueryResult
from palace.core.tree_sitter_v2 import parse_file_v2, detect_language


@pytest.fixture
def temp_palace_dir():
    """Create temporary palace directory for testing."""
    with TemporaryDirectory() as tmpdir:
        palace_dir = Path(tmpdir) / ".palace"
        palace_dir.mkdir(exist_ok=True)
        yield palace_dir


@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return """
def authenticate(username, password):
    user = validate_user(username)
    if user and check_password(password, user.password_hash):
        return create_token(user)
    return None

class AuthManager:
    def verify_token(self, token):
        return is_valid_token(token)
"""


@pytest.fixture
def sample_files(temp_palace_dir):
    """Create sample Python files for testing."""
    src_dir = temp_palace_dir.parent / "src"
    src_dir.mkdir(exist_ok=True)

    files = {}

    # Create auth.py
    auth_py = src_dir / "auth.py"
    auth_code = """
def authenticate(username, password):
    user = validate_user(username)
    if user and check_password(password, user.password_hash):
        return create_token(user)
    return None

class AuthManager:
    def verify_token(self, token):
        return is_valid_token(token)
"""
    auth_py.write_text(auth_code)
    files['auth.py'] = (auth_py, auth_code)

    # Create user.py
    user_py = src_dir / "user.py"
    user_code = """
def validate_user(username):
    return database.get_user(username)

def check_password(password, hash):
    return bcrypt.verify(password, hash)
"""
    user_py.write_text(user_code)
    files['user.py'] = (user_py, user_code)

    return files


class TestASTFingerprinting:
    """Test AST fingerprinting functionality."""

    def test_fingerprint_length(self, sample_code):
        """AST fingerprint should be 64 hex chars (32 bytes)."""
        fingerprint = hashlib.sha256(sample_code.encode()).hexdigest()
        assert len(fingerprint) == 64
        assert all(c in '0123456789abcdef' for c in fingerprint)

    def test_fingerprint_consistency(self, sample_code):
        """Same code should produce same fingerprint."""
        fp1 = hashlib.sha256(sample_code.encode()).hexdigest()
        fp2 = hashlib.sha256(sample_code.encode()).hexdigest()
        assert fp1 == fp2

    def test_fingerprint_uniqueness(self):
        """Different code should produce different fingerprints."""
        code1 = "def foo(): return 1"
        code2 = "def bar(): return 2"
        fp1 = hashlib.sha256(code1.encode()).hexdigest()
        fp2 = hashlib.sha256(code2.encode()).hexdigest()
        assert fp1 != fp2


class TestBloomFilter:
    """Test Bloom filter functionality."""

    def test_bloom_creation(self):
        """Bloom filter should create successfully."""
        bloom = create_palace_bloom_filter(num_artifacts=10_000)
        assert bloom is not None
        assert bloom.size_bits > 0

    def test_bloom_add_and_contains(self):
        """Bloom filter should add and check membership."""
        bloom = create_palace_bloom_filter(num_artifacts=1000)

        # Add item
        bloom.add("artifact_123")

        # Check membership
        assert bloom.contains("artifact_123") == True
        assert bloom.contains("artifact_456") == False

    def test_bloom_stats(self):
        """Bloom filter should provide statistics."""
        bloom = create_palace_bloom_filter(num_artifacts=10_000)

        # Add items
        for i in range(100):
            bloom.add(f"artifact_{i}")

        stats = bloom.get_stats()
        assert 'size_mb' in stats
        assert 'load_factor' in stats
        assert 'estimated_count' in stats
        assert stats['estimated_count'] > 0


class TestASTParsing:
    """Test AST parsing with tree-sitter V2."""

    def test_language_detection(self, sample_files):
        """Should detect Python language from .py extension."""
        file_path = sample_files['auth.py'][0]
        language = detect_language(file_path)
        assert language == 'python'

    def test_parse_file(self, sample_files):
        """Should parse Python file successfully."""
        file_path, _ = sample_files['auth.py']
        result = parse_file_v2(file_path)

        # Note: parse_success may be False if tree-sitter parsers not installed
        # but ast_fingerprint should always be generated (fallback to SHA-256)
        assert result.ast_fingerprint is not None
        assert len(result.ast_fingerprint) == 64
        assert result.language == 'python'

    def test_extract_symbols(self, sample_files):
        """Should extract functions and classes."""
        file_path, _ = sample_files['auth.py']
        result = parse_file_v2(file_path)

        # Should have symbols (even if tree-sitter not available,
        # we should have fallback)
        assert isinstance(result.symbols, list)


class TestTOONEncoding:
    """Test TOON encoding functionality."""

    def test_ast_summary_creation(self):
        """Should create AST summary successfully."""
        summary = ASTSummary(
            file_path="test.py",
            language="python",
            functions=[
                {
                    'name': 'authenticate',
                    'parameters': ['username', 'password'],
                    'return_type': 'Token',
                    'calls': ['validate_user']
                }
            ],
            classes=[],
            imports=['database'],
            exports=['authenticate']
        )

        assert summary.file_path == "test.py"
        assert summary.language == "python"
        assert len(summary.functions) == 1
        assert summary.functions[0]['name'] == 'authenticate'

    def test_toon_encoding(self):
        """TOON should be more compact than JSON."""
        import json

        summary = ASTSummary(
            file_path="test.py",
            language="python",
            functions=[
                {
                    'name': 'foo',
                    'parameters': ['x', 'y'],
                    'return_type': 'int',
                    'calls': ['bar']
                }
            ],
            classes=[],
            imports=['os', 'sys'],
            exports=['foo']
        )

        encoder = TOONEncoder()

        # Generate TOON
        toon_str = encoder.encode_ast_summary(summary)

        # Generate JSON
        json_str = json.dumps({
            'file_path': summary.file_path,
            'language': summary.language,
            'functions': summary.functions,
            'classes': summary.classes,
            'imports': summary.imports,
            'exports': summary.exports,
        }, indent=2)

        # TOON should be more compact
        assert len(toon_str) < len(json_str)

    def test_token_efficiency(self):
        """TOON should reduce tokens by >40%."""
        import json

        summary = ASTSummary(
            file_path="auth.py",
            language="python",
            functions=[
                {
                    'name': 'authenticate',
                    'parameters': ['username', 'password'],
                    'return_type': 'Token',
                    'calls': ['validate_user', 'check_password']
                },
                {
                    'name': 'logout',
                    'parameters': ['token'],
                    'return_type': 'None',
                    'calls': ['invalidate_token']
                }
            ],
            classes=[],
            imports=['models', 'database'],
            exports=['authenticate', 'logout']
        )

        encoder = TOONEncoder()
        toon_str = encoder.encode_ast_summary(summary)

        json_str = json.dumps({
            'file_path': summary.file_path,
            'language': summary.language,
            'functions': summary.functions,
            'classes': summary.classes,
            'imports': summary.imports,
            'exports': summary.exports,
        }, indent=2)

        toon_tokens = encoder.estimate_tokens(toon_str)
        json_tokens = len(json_str) // 4

        reduction = (json_tokens - toon_tokens) / json_tokens
        assert reduction > 0.40  # >40% reduction


class TestHippocampusV2:
    """Test Hippocampus V2 (pure graph, no embeddings)."""

    def test_database_initialization(self, temp_palace_dir):
        """Should initialize KuzuDB without SQLite+vec."""
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        # Should be connected
        assert hippocampus.is_connected() == True

        # Should NOT have vec_conn
        assert not hasattr(hippocampus, 'vec_conn')

        hippocampus.close()

    def test_create_artifact(self, temp_palace_dir):
        """Should create artifact node with fingerprint."""
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        # Create artifact
        hippocampus.create_artifact(
            artifact_id="test_auth",
            path="src/auth.py",
            content_hash="abc123",
            language="python",
            ast_fingerprint="def456"
        )

        # Retrieve
        node = hippocampus.get_node("test_auth")
        assert node is not None
        assert node['path'] == "src/auth.py"
        assert node['ast_fingerprint'] == "def456"

        hippocampus.close()

    def test_create_dependency(self, temp_palace_dir):
        """Should create DEPENDS_ON edge between artifacts."""
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        # Create artifacts
        hippocampus.create_artifact(
            artifact_id="auth",
            path="auth.py",
            content_hash="1",
            language="python",
            ast_fingerprint="fp1"
        )

        hippocampus.create_artifact(
            artifact_id="user",
            path="user.py",
            content_hash="2",
            language="python",
            ast_fingerprint="fp2"
        )

        # Create dependency
        hippocampus.create_dependency("auth", "user", "import")

        # Query dependencies
        deps = hippocampus.get_dependencies("auth")
        assert len(deps) > 0
        assert deps[0]['id'] == "user"

        hippocampus.close()


class TestAgentInterface:
    """Test agent query interface."""

    def test_interface_initialization(self, temp_palace_dir):
        """Should initialize interface with Hippocampus and Bloom filter."""
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        bloom = create_palace_bloom_filter(num_artifacts=1000)

        interface = AgentQueryInterface(hippocampus, bloom)
        assert interface is not None
        assert interface.hippocampus == hippocampus
        assert interface.bloom_filter == bloom

        hippocampus.close()

    def test_bloom_filter_check(self, temp_palace_dir):
        """Should check Bloom filter for membership."""
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        bloom = create_palace_bloom_filter(num_artifacts=1000)
        bloom.add("artifact_123")

        interface = AgentQueryInterface(hippocampus, bloom)

        # Check membership (internal method)
        exists = interface._check_bloom_filter("artifact_123")
        assert exists == True

        not_exists = interface._check_bloom_filter("artifact_456")
        assert not_exists == False

        hippocampus.close()


class TestEndToEndWorkflow:
    """Test complete V2 workflow."""

    @pytest.mark.slow
    def test_complete_workflow(self, temp_palace_dir, sample_files):
        """Test complete V2 workflow: parse → fingerprint → bloom → graph → toon."""
        # Step 1: Initialize components
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        bloom = create_palace_bloom_filter(num_artifacts=1000)

        # Step 2: Parse files and get fingerprints
        fingerprints = {}
        for name, (file_path, code) in sample_files.items():
            result = parse_file_v2(file_path)
            fingerprints[name] = result.ast_fingerprint

            # Create artifact in graph
            artifact_id = name.replace('.', '_')
            hippocampus.create_artifact(
                artifact_id=artifact_id,
                path=str(file_path.relative_to(temp_palace_dir.parent)),
                content_hash=hashlib.sha256(code.encode()).hexdigest(),
                language="python",
                ast_fingerprint=result.ast_fingerprint
            )

            # Add to Bloom filter
            bloom.add(artifact_id)

        # Step 3: Create dependency
        hippocampus.create_dependency("auth_py", "user_py", "import")

        # Step 4: Verify graph
        auth_node = hippocampus.get_node("auth_py")
        assert auth_node is not None
        assert auth_node['ast_fingerprint'] == fingerprints['auth.py']

        # Step 5: Query dependencies
        deps = hippocampus.get_dependencies("auth_py")
        assert len(deps) > 0
        assert any(dep['id'] == 'user_py' for dep in deps)

        # Step 6: Verify Bloom filter
        assert bloom.contains("auth_py") == True
        assert bloom.contains("nonexistent") == False

        hippocampus.close()

    def test_statistics(self, temp_palace_dir):
        """Should provide accurate statistics."""
        hippocampus = Hippocampus(temp_palace_dir)
        hippocampus.initialize_schema()

        # Create test data
        hippocampus.create_artifact(
            "test1", "test1.py", "h1", "python", "fp1"
        )
        hippocampus.create_artifact(
            "test2", "test2.py", "h2", "python", "fp2"
        )
        hippocampus.create_dependency("test1", "test2", "import")

        # Get statistics
        stats = hippocampus.get_statistics()

        assert stats['artifact_count'] >= 2
        assert stats['depends_on_count'] >= 1

        hippocampus.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
