"""Unit tests for regex-based parsers (fallback)."""

import pytest
from pathlib import Path
from palace.ingest.parsers.javascript_regex import JavaScriptRegexParser
from palace.ingest.parsers.typescript_regex import TypeScriptRegexParser
from palace.ingest.parsers.go_regex import GoRegexParser
from palace.ingest.parsers.base import Dependency, Symbol


class TestJavaScriptRegexParser:
    """Tests for JavaScriptRegexParser."""

    @pytest.fixture
    def parser(self):
        """Create JavaScript regex parser instance."""
        return JavaScriptRegexParser()

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".js" in parser.supported_extensions()
        assert ".jsx" in parser.supported_extensions()
        assert ".mjs" in parser.supported_extensions()
        assert ".cjs" in parser.supported_extensions()

    def test_extract_es6_imports(self, parser):
        """Test ES6 import extraction."""
        content = """
import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';
"""
        deps = parser.parse_dependencies(Path("test.js"), content)

        assert len(deps) == 3
        assert any(d.path == "react" for d in deps)
        assert any(d.path == "axios" for d in deps)

    def test_extract_commonjs_requires(self, parser):
        """Test CommonJS require extraction."""
        content = """
const express = require('express');
const logger = require('./logger');
const utils = require('../utils');
"""
        deps = parser.parse_dependencies(Path("test.js"), content)

        assert len(deps) >= 3
        assert any(d.path == "express" for d in deps)
        assert any(d.path == "./logger" for d in deps)
        assert any(d.path == "../utils" for d in deps)

    def test_extract_functions(self, parser):
        """Test function extraction."""
        content = """
function fetchData() {
    return data;
}

const processData = function(data) {
    return data;
}

const formatData = (data) => {
    return data;
};
"""
        symbols = parser.extract_symbols(content)

        # Should find function declarations and arrow functions
        assert any(s.name == "fetchData" and s.type == "function" for s in symbols)
        assert any(s.name == "formatData" and s.type == "function" for s in symbols)

    def test_extract_classes(self, parser):
        """Test class extraction."""
        content = """
class MyComponent extends React.Component {
    render() {
        return <div />;
    }
}

class BaseService {
    fetch() {
        return [];
    }
}
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "MyComponent" and s.type == "class" for s in symbols)
        assert any(s.name == "BaseService" and s.type == "class" for s in symbols)

    def test_extract_constants(self, parser):
        """Test constant extraction."""
        content = """
const API_URL = 'https://api.example.com';
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT = 5000;
"""
        symbols = parser.extract_symbols(content)

        # All uppercase constants
        assert any(s.name == "API_URL" and s.type == "constant" for s in symbols)
        assert any(s.name == "MAX_RETRIES" and s.type == "constant" for s in symbols)

    def test_fingerprint_deterministic(self, parser):
        """Test that fingerprinting is deterministic."""
        content = "const x = 42;"
        fp1 = parser.compute_fingerprint(content)
        fp2 = parser.compute_fingerprint(content)

        assert fp1 == fp2

    def test_fingerprint_different_content(self, parser):
        """Test that different content produces different fingerprints."""
        fp1 = parser.compute_fingerprint("const x = 42;")
        fp2 = parser.compute_fingerprint("const x = 43;")

        assert fp1 != fp2


class TestTypeScriptRegexParser:
    """Tests for TypeScriptRegexParser."""

    @pytest.fixture
    def parser(self):
        """Create TypeScript regex parser instance."""
        return TypeScriptRegexParser()

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".ts" in parser.supported_extensions()
        assert ".tsx" in parser.supported_extensions()

    def test_extract_imports(self, parser):
        """Test import extraction."""
        content = """
import React from 'react';
import { useState } from 'react';
import type { User } from './types';
"""
        deps = parser.parse_dependencies(Path("test.ts"), content)

        assert len(deps) >= 2
        assert any(d.path == "react" for d in deps)

    def test_extract_interfaces(self, parser):
        """Test interface extraction."""
        content = """
interface User {
    name: string;
    age: number;
}

interface Admin extends User {
    permissions: string[];
}

export interface Config {
    debug: boolean;
}
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "User" and s.type == "interface" for s in symbols)
        assert any(s.name == "Admin" and s.type == "interface" for s in symbols)
        assert any(s.name == "Config" and s.type == "interface" for s in symbols)

    def test_extract_type_aliases(self, parser):
        """Test type alias extraction."""
        content = """
type UserID = number;
type UserMap = Map<number, string>;
type ApiResponse<T> = {
    data: T;
    status: number;
};
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "UserID" and s.type == "type_alias" for s in symbols)
        assert any(s.name == "UserMap" and s.type == "type_alias" for s in symbols)

    def test_extract_classes(self, parser):
        """Test class extraction."""
        content = """
class UserService {
    private users: User[] = [];

    getUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
}

export class ApiController {
    handleRequest(): void {
        console.log('Request');
    }
}
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "UserService" and s.type == "class" for s in symbols)
        assert any(s.name == "ApiController" and s.type == "class" for s in symbols)

    def test_extract_functions(self, parser):
        """Test function extraction."""
        content = """
function getAllUsers(): User[] {
    return [];
}

export async function getUserById(id: number): Promise<User> {
    return fetchUser(id);
}

const getUsers = (): User[] => {
    return [];
};
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "getAllUsers" and s.type == "function" for s in symbols)
        assert any(s.name == "getUserById" and s.type == "function" for s in symbols)
        assert any(s.name == "getUsers" and s.type == "function" for s in symbols)

    def test_fingerprint_deterministic(self, parser):
        """Test that fingerprinting is deterministic."""
        content = "const x: number = 42;"
        fp1 = parser.compute_fingerprint(content)
        fp2 = parser.compute_fingerprint(content)

        assert fp1 == fp2


class TestGoRegexParser:
    """Tests for GoRegexParser."""

    @pytest.fixture
    def parser(self):
        """Create Go regex parser instance."""
        return GoRegexParser()

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".go" in parser.supported_extensions()

    def test_extract_imports(self, parser):
        """Test import extraction."""
        content = """
package main

import (
    "fmt"
    "net/http"

    "github.com/gin-gonic/gin"
)
"""
        deps = parser.parse_dependencies(Path("test.go"), content)

        assert len(deps) >= 3
        assert any(d.path == "fmt" for d in deps)
        assert any(d.path == "net/http" for d in deps)
        assert any(d.path == "github.com/gin-gonic/gin" for d in deps)

    def test_extract_import_block(self, parser):
        """Test import block extraction."""
        content = """
import (
    "database/sql"
    "fmt"
    "log"
)
"""
        deps = parser.parse_dependencies(Path("test.go"), content)

        assert len(deps) == 3
        assert any(d.path == "database/sql" for d in deps)
        assert any(d.path == "fmt" for d in deps)
        assert any(d.path == "log" for d in deps)

    def test_extract_package(self, parser):
        """Test package extraction."""
        content = """
package main

func main() {}
"""
        symbols = parser.extract_symbols(content)

        assert any(s.type == "package" for s in symbols)

    def test_extract_functions(self, parser):
        """Test function extraction."""
        content = """
package main

func add(a int, b int) int {
    return a + b
}

func (s *Service) GetUser(id int) *User {
    return s.db.Query(id)
}
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "add" and s.type == "function" for s in symbols)
        assert any("Service.GetUser" in s.name and s.type == "method" for s in symbols)

    def test_extract_structs(self, parser):
        """Test struct extraction."""
        content = """
package main

type User struct {
    Name string
    Age  int
}

type Service struct {
    db *Database
    users []User
}
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "User" and s.type == "struct" for s in symbols)
        assert any(s.name == "Service" and s.type == "struct" for s in symbols)

    def test_extract_constants(self, parser):
        """Test constant extraction."""
        content = """
package main

const MAX_USERS = 100
const API_VERSION = "v1"
"""
        symbols = parser.extract_symbols(content)

        assert any(s.name == "MAX_USERS" and s.type == "constant" for s in symbols)
        assert any(s.name == "API_VERSION" and s.type == "constant" for s in symbols)

    def test_fingerprint_deterministic(self, parser):
        """Test that fingerprinting is deterministic."""
        content = 'package main\n\nfunc main() {}'
        fp1 = parser.compute_fingerprint(content)
        fp2 = parser.compute_fingerprint(content)

        assert fp1 == fp2
