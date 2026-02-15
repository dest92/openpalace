"""Integration tests for multi-language repositories."""

import pytest
from pathlib import Path
import tempfile
import shutil
from palace.core.hippocampus import Hippocampus
from palace.ingest.pipeline import BigBangPipeline


class TestMultiLanguageRepo:
    """Tests for multi-language repository ingestion."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary multi-language repository."""
        repo_dir = tempfile.mkdtemp(prefix="palace_test_")
        yield Path(repo_dir)
        # Cleanup
        if Path(repo_dir).exists():
            shutil.rmtree(repo_dir)

    @pytest.fixture
    def hippocampus(self, temp_repo):
        """Create test hippocampus instance."""
        palace_dir = temp_repo / ".palace"
        palace_dir.mkdir(parents=True, exist_ok=True)

        hippo = Hippocampus(str(palace_dir))
        hippo.initialize_schema()
        yield hippo
        hippo.close()

    @pytest.fixture
    def pipeline(self, hippocampus):
        """Create test pipeline."""
        return BigBangPipeline(hippocampus, concept_extractor=None)

    def test_python_javascript_mixed_repo(self, temp_repo, pipeline):
        """Test repository with Python and JavaScript files."""
        # Create Python file
        py_file = temp_repo / "app.py"
        py_file.write_text("""
import requests
from database import Database

class UserService:
    def __init__(self):
        self.db = Database()

    def get_user(self, user_id):
        return self.db.query(user_id)

def create_user(name):
    return UserService().create(name)
""")

        # Create JavaScript file
        js_file = temp_repo / "client.js"
        js_file.write_text("""
import React from 'react';
import { render } from 'react-dom';

class App extends React.Component {
    render() {
        return <div>Hello World</div>;
    }
}

function initApp() {
    render(<App />, document.getElementById('root'));
}

initApp();
""")

        # Ingest Python file
        py_result = pipeline.ingest_file(py_file)
        assert py_result["status"] == "success"
        assert py_result["symbols"] > 0
        assert py_result["dependencies"] > 0

        # Ingest JavaScript file
        js_result = pipeline.ingest_file(js_file)
        assert js_result["status"] == "success"
        assert js_result["symbols"] > 0
        assert js_result["dependencies"] > 0

    def test_typescript_react_project(self, temp_repo, pipeline):
        """Test TypeScript React component."""
        # Create TypeScript file
        tsx_file = temp_repo / "Component.tsx"
        tsx_file.write_text("""
import React, { useState } from 'react';

interface User {
    name: string;
    age: number;
}

type UserList = User[];

export const UserCard: React.FC<{ user: User }> = ({ user }) => {
    const [count, setCount] = useState(0);

    return (
        <div>
            <h2>{user.name}</h2>
            <p>Age: {user.age}</p>
        </div>
    );
};

export default UserCard;
""")

        # Ingest TypeScript file
        result = pipeline.ingest_file(tsx_file)
        assert result["status"] == "success"
        assert result["symbols"] > 0  # Should find interface, type, component
        assert result["dependencies"] > 0  # Should find React imports

    def test_go_service(self, temp_repo, pipeline):
        """Test Go service file."""
        # Create Go file
        go_file = temp_repo / "service.go"
        go_file.write_text("""
package main

import (
    "fmt"
    "net/http"
    "github.com/gin-gonic/gin"
)

type User struct {
    Name string `json:"name"`
    Age  int    `json:"age"`
}

type Service struct {
    users []User
}

func (s *Service) GetUser(id int) (*User, error) {
    for _, user := range s.users {
        if user.ID == id {
            return &user, nil
        }
    }
    return nil, fmt.Errorf("user not found")
}

func main() {
    s := &Service{
        users: []User{
            {Name: "Alice", Age: 30},
        },
    }

    r := gin.Default()
    r.GET("/users/:id", s.GetUser)
    r.Run(":8080")
}
""")

        # Ingest Go file
        result = pipeline.ingest_file(go_file)
        assert result["status"] == "success"
        assert result["symbols"] > 0  # Should find package, structs, functions
        assert result["dependencies"] > 0  # Should find imports

    def test_nextjs_project_structure(self, temp_repo, pipeline):
        """Test Next.js project with multiple file types."""
        # Create Next.js config
        config_file = temp_repo / "next.config.js"
        config_file.write_text("""
module.exports = {
    reactStrictMode: true,
};
""")

        # Create app directory structure
        app_dir = temp_repo / "app"
        app_dir.mkdir()

        # Create page
        page_file = app_dir / "page.tsx"
        page_file.write_text("""
export default function Home() {
    return <main>Hello World</main>;
}
""")

        # Create API route
        api_dir = app_dir / "api"
        api_dir.mkdir()

        users_file = api_dir / "users" / "route.ts"
        users_file.parent.mkdir(parents=True, exist_ok=True)
        users_file.write_text("""
import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({ users: [] });
}
""")

        # Ingest all files
        config_result = pipeline.ingest_file(config_file)
        assert config_result["status"] == "skipped"  # .js config might be skipped or ingested

        page_result = pipeline.ingest_file(page_file)
        assert page_result["status"] == "success"

        api_result = pipeline.ingest_file(users_file)
        assert api_result["status"] == "success"

    def test_fingerprint_change_detection(self, temp_repo, pipeline):
        """Test that fingerprinting detects changes."""
        # Create file
        test_file = temp_repo / "test.py"
        content_v1 = "def hello():\n    return 'world'"
        test_file.write_text(content_v1)

        # Ingest first version
        result1 = pipeline.ingest_file(test_file)
        fp1 = result1.get("fingerprint", "")
        assert result1["status"] == "success"
        assert len(fp1) > 0

        # Modify file
        content_v2 = "def hello():\n    return 'universe'"
        test_file.write_text(content_v2)

        # Ingest second version
        result2 = pipeline.ingest_file(test_file)
        fp2 = result2.get("fingerprint", "")
        assert result2["status"] == "success"
        assert len(fp2) > 0

        # Fingerprints should be different
        assert fp1 != fp2

    def test_unsupported_file_skipped(self, temp_repo, pipeline):
        """Test that unsupported file types are skipped."""
        # Create unsupported file
        txt_file = temp_repo / "readme.txt"
        txt_file.write_text("This is not code")

        # Try to ingest
        result = pipeline.ingest_file(txt_file)
        assert result["status"] == "skipped"
        assert result["reason"] == "No parser for extension"

    def test_empty_file(self, temp_repo, pipeline):
        """Test handling of empty files."""
        # Create empty file
        empty_file = temp_repo / "empty.py"
        empty_file.write_text("")

        # Ingest empty file
        result = pipeline.ingest_file(empty_file)
        # Should handle gracefully - either success with 0 symbols or skipped
        assert result["status"] in ["success", "skipped"]

    def test_syntax_error_handling(self, temp_repo, pipeline):
        """Test handling of files with syntax errors."""
        # Create file with syntax error
        bad_file = temp_repo / "broken.py"
        bad_file.write_text("""
def broken(
    # Missing colon and body
    return 1
""")

        # Should still handle gracefully
        result = pipeline.ingest_file(bad_file)
        # Python parser uses try/except for syntax errors
        assert result["status"] == "success" or result["status"] == "skipped"


class TestParserRegistryIntegration:
    """Tests for ParserRegistry integration."""

    def test_registry_auto_registers_parsers(self):
        """Test that registry auto-registers available parsers."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()

        # Python parser should always be registered
        assert registry.has_parser(Path("test.py"))
        assert registry.detect_language(Path("test.py")) == "python"

    def test_multiple_parser_registration(self):
        """Test that multiple parsers are registered correctly."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()

        supported = registry.get_supported_extensions()

        # Should always have Python
        assert ".py" in supported

        # Check for other parsers if available
        js_parser = registry.is_parser_available(
            __import__("palace.ingest.parsers.javascript", fromlist=["JavaScriptParser"])
        )
        if js_parser:
            assert ".js" in supported

    def test_language_filtering(self):
        """Test language filtering in registry."""
        from palace.ingest.parsers.registry import ParserRegistry

        registry = ParserRegistry.instance()

        # Test detection for different languages
        assert registry.detect_language(Path("test.py")) == "python"
        assert registry.detect_language(Path("test.js")) == "javascript"
        assert registry.detect_language(Path("test.ts")) == "typescript"
        assert registry.detect_language(Path("test.go")) == "go"

        # Test unknown language
        assert registry.detect_language(Path("test.unknown")) == "unknown"
