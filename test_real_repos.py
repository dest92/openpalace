#!/usr/bin/env python3
"""
Test script to verify multi-language support with real code repositories.

This script:
1. Creates test repositories with real code patterns
2. Ingests them using the pipeline
3. Verifies parsing worked correctly
4. Reports results
"""

import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add palace to path
sys.path.insert(0, str(Path(__file__).parent))

from palace.core.hippocampus import Hippocampus
from palace.ingest.pipeline import BigBangPipeline


def create_python_repo(base_dir):
    """Create a Python repository with common patterns."""
    repo_dir = base_dir / "python-repo"
    repo_dir.mkdir()

    # Create package structure
    (repo_dir / "database.py").write_text("""
\"\"\"Database connection and models.\"\"\"

import psycopg2
from typing import List, Optional


class Database:
    \"\"\"Database connection manager.\"\"\"

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)

    def query(self, sql: str) -> List[dict]:
        \"\"\"Execute a query and return results.\"\"\"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def close(self):
        \"\"\"Close the database connection.\"\"\"
        self.conn.close()


class User:
    \"\"\"User model.\"\"\"

    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    def save(self, db: Database):
        \"\"\"Save user to database.\"\"\"
        db.query(f"INSERT INTO users VALUES ({self.id}, '{self.name}', '{self.email}')")
""")

    (repo_dir / "auth.py").write_text("""
\"\"\"Authentication module.\"\"\"

from database import Database
import hashlib


def authenticate_user(email: str, password: str, db: Database) -> bool:
    \"\"\"Authenticate a user.\"\"\"
    users = db.query(f"SELECT * FROM users WHERE email = '{email}'")

    if not users:
        return False

    hashed = hashlib.sha256(password.encode()).hexdigest()
    return users[0]['password_hash'] == hashed


class AuthenticationError(Exception):
    \"\"\"Raised when authentication fails.\"\"\"
    pass
""")

    return repo_dir


def create_javascript_repo(base_dir):
    """Create a JavaScript repository with common patterns."""
    repo_dir = base_dir / "javascript-repo"
    repo_dir.mkdir()

    # Create components directory
    (repo_dir / "components").mkdir()

    # Create directories
    (repo_dir / "components").mkdir(exist_ok=True)
    (repo_dir / "utils").mkdir(exist_ok=True)

    # Create React component
    (repo_dir / "components" / "UserProfile.js").write_text("""
/**
 * User profile component
 */

import React, { useState, useEffect } from 'react';
import { fetchUser } from '../api/users';
import { formatName } from '../utils/formatters';

export class UserProfile extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            user: null,
            loading: true,
            error: null
        };
    }

    async componentDidMount() {
        try {
            const user = await fetchUser(this.props.userId);
            this.setState({ user, loading: false });
        } catch (error) {
            this.setState({ error: error.message, loading: false });
        }
    }

    render() {
        const { user, loading, error } = this.state;

        if (loading) return <div>Loading...</div>;
        if (error) return <div>Error: {error}</div>;

        return (
            <div className="user-profile">
                <h1>{formatName(user.name)}</h1>
                <p>{user.email}</p>
            </div>
        );
    }
}

export default UserProfile;
""")

    # Create utility module
    (repo_dir / "utils" / "formatters.js").write_text("""
/**
 * String formatting utilities
 */

/**
 * Format a user's name with proper capitalization
 */
export function formatName(name) {
    return name
        .split(' ')
        .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
        .join(' ');
}

/**
 * Format a date as a relative time string
 */
export function formatRelativeTime(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
}
""")

    return repo_dir


def create_typescript_repo(base_dir):
    """Create a TypeScript repository with common patterns."""
    repo_dir = base_dir / "typescript-repo"
    repo_dir.mkdir()

    # Create directories
    (repo_dir / "types").mkdir(exist_ok=True)
    (repo_dir / "services").mkdir(exist_ok=True)

    # Create type definitions
    (repo_dir / "types" / "index.ts").write_text("""
/**
 * Core type definitions
 */

export interface User {
    id: number;
    name: string;
    email: string;
    createdAt: Date;
}

export interface ApiResponse<T> {
    data: T;
    status: number;
    message?: string;
}

export type UserId = number;
export type UserName = string;

export interface CreateUserRequest {
    name: UserName;
    email: string;
    password: string;
}

export interface UpdateUserRequest extends Partial<CreateUserRequest> {
    id: UserId;
}
""")

    # Create API service
    (repo_dir / "services" / "userService.ts").write_text("""
/**
 * User service API
 */

import type { User, ApiResponse, CreateUserRequest, UpdateUserRequest } from '../types';
import { apiFetch } from './apiClient';

export class UserService {
    private readonly baseUrl = '/api/users';

    async getUsers(): Promise<User[]> {
        const response = await apiFetch<ApiResponse<User[]>>(this.baseUrl);
        return response.data;
    }

    async getUserById(id: number): Promise<User | null> {
        const response = await apiFetch<ApiResponse<User>>(`${this.baseUrl}/${id}`);
        return response.data || null;
    }

    async createUser(request: CreateUserRequest): Promise<User> {
        const response = await apiFetch<ApiResponse<User>>(this.baseUrl, {
            method: 'POST',
            body: JSON.stringify(request)
        });
        return response.data;
    }

    async updateUser(request: UpdateUserRequest): Promise<User> {
        const { id, ...data } = request;
        const response = await apiFetch<ApiResponse<User>>(`${this.baseUrl}/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return response.data;
    }

    async deleteUser(id: number): Promise<void> {
        await apiFetch(`${this.baseUrl}/${id}`, { method: 'DELETE' });
    }
}

export const userService = new UserService();
""")

    return repo_dir


def create_go_repo(base_dir):
    """Create a Go repository with common patterns."""
    repo_dir = base_dir / "go-repo"
    repo_dir.mkdir()

    # Create directory structure
    (repo_dir / "cmd" / "service").mkdir(parents=True)
    (repo_dir / "internal" / "models").mkdir(parents=True)

    # Create main service
    (repo_dir / "cmd" / "service" / "main.go").write_text("""
// Package main declares the main package
package main

import (
    "fmt"
    "log"
    "net/http"
    "github.com/gorilla/mux"
    "github.com/yourproject/internal/api"
    "github.com/yourproject/internal/models"
)

// Server holds the application dependencies
type Server struct {
    router *mux.Router
    users  *models.UserService
}

// Start initializes and starts the server
func Start(addr string) error {
    s := &Server{
        router: mux.NewRouter(),
        users:  models.NewUserService(),
    }

    s.setupRoutes()

    log.Printf("Starting server on %s", addr)
    return http.ListenAndServe(addr, s.router)
}

// setupRoutes configures all API routes
func (s *Server) setupRoutes() {
    api.HandleFunc(s.router, "/api/users", s.getUsers)
    api.HandleFunc(s.router, "/api/users/{id}", s.getUser)
}

// getUsers returns all users
func (s *Server) getUsers(w http.ResponseWriter, r *http.Request) {
    users, err := s.users.GetAll(r.Context())
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    api.RespondJSON(w, users, http.StatusOK)
}

// getUser returns a single user by ID
func (s *Server) getUser(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, err := strconv.Atoi(vars["id"])
    if err != nil {
        http.Error(w, "Invalid user ID", http.StatusBadRequest)
        return
    }

    user, err := s.users.GetByID(r.Context(), id)
    if err != nil {
        http.Error(w, "User not found", http.StatusNotFound)
        return
    }

    api.RespondJSON(w, user, http.StatusOK)
}

func main() {
    if err := Start(":8080"); err != nil {
        log.Fatalf("Server failed: %v", err)
    }
}
""")

    # Create models
    (repo_dir / "internal" / "models" / "user.go").write_text("""
// Package models defines data models
package models

import (
    "context"
    "database/sql"
)

// User represents a user in the system
type User struct {
    ID        int       `db:"id" json:"id"`
    Name      string    `db:"name" json:"name"`
    Email      string    `db:"email" json:"email"`
    CreatedAt  time.Time `db:"created_at" json:"created_at"`
}

// UserService provides user operations
type UserService struct {
    db *sql.DB
}

// NewUserService creates a new UserService
func NewUserService() *UserService {
    return &UserService{
        db: sql.OpenDB(),
    }
}

// GetAll retrieves all users
func (s *UserService) GetAll(ctx context.Context) ([]User, error) {
    var users []User
    err := s.db.SelectContext(ctx, &users, "SELECT * FROM users ORDER BY created_at DESC")
    return users, err
}

// GetByID retrieves a user by ID
func (s *UserService) GetByID(ctx context.Context, id int) (*User, error) {
    var user User
    err := s.db.GetContext(ctx, &user, "SELECT * FROM users WHERE id = ?", id)
    if err != nil {
        return nil, err
    }
    return &user, nil
}
""")

    return repo_dir


def test_repository(repo_dir, repo_name):
    """Test ingesting a repository."""
    print(f"\n{'='*60}")
    print(f"Testing: {repo_name}")
    print(f"{'='*60}")

    # Initialize Palace
    palace_dir = repo_dir / ".palace"
    palace_dir.mkdir(parents=True, exist_ok=True)

    with Hippocampus(str(palace_dir)) as hippo:
        hippo.initialize_schema()

        pipeline = BigBangPipeline(hippo, concept_extractor=None)

        # Find all code files
        files = []
        for ext in ['.py', '.js', '.ts', '.tsx', '.go']:
            files.extend(list(repo_dir.rglob(f"*{ext}")))

        print(f"Found {len(files)} code files")

        # Ingest files
        results = {"success": 0, "skipped": 0, "errors": 0}
        total_symbols = 0
        total_deps = 0

        for file_path in files:
            if file_path.is_file():
                try:
                    result = pipeline.ingest_file(file_path)
                    if result["status"] == "success":
                        results["success"] += 1
                        total_symbols += result.get("symbols", 0)
                        total_deps += result.get("dependencies", 0)
                        print(f"  ✓ {file_path.relative_to(repo_dir)}: {result.get('symbols', 0)} symbols, {result.get('dependencies', 0)} deps")
                    elif result["status"] == "skipped":
                        results["skipped"] += 1
                        print(f"  - {file_path.relative_to(repo_dir)}: skipped")
                    else:
                        results["errors"] += 1
                        print(f"  ✗ {file_path.relative_to(repo_dir)}: {result.get('reason', 'unknown')}")
                except Exception as e:
                    results["errors"] += 1
                    print(f"  ✗ {file_path.relative_to(repo_dir)}: {e}")

        # Summary
        print(f"\n{'-'*60}")
        print(f"Results for {repo_name}:")
        print(f"  ✓ Ingested: {results['success']} files")
        print(f"  - Skipped: {results['skipped']} files")
        print(f"  ✗ Errors: {results['errors']} files")
        print(f"  Σ Total symbols: {total_symbols}")
        print(f"  Σ Total dependencies: {total_deps}")
        print(f"{'-'*60}")

        return results['success'] > 0 and results['errors'] == 0


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Multi-Language Support Test Suite")
    print("="*60)

    # Create temporary directory for test repos
    test_dir = Path(tempfile.mkdtemp(prefix="palace_multilang_test_"))

    try:
        # Create test repositories
        python_repo = create_python_repo(test_dir)
        js_repo = create_javascript_repo(test_dir)
        ts_repo = create_typescript_repo(test_dir)
        go_repo = create_go_repo(test_dir)

        # Test each repository
        results = {}
        results["python"] = test_repository(python_repo, "Python Repository")
        results["javascript"] = test_repository(js_repo, "JavaScript Repository")
        results["typescript"] = test_repository(ts_repo, "TypeScript Repository")
        results["go"] = test_repository(go_repo, "Go Repository")

        # Final summary
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)

        all_passed = True
        for lang, passed in results.items():
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"  {lang.capitalize():12} : {status}")
            if not passed:
                all_passed = False

        print("="*60)

        if all_passed:
            print("\n✓ All tests passed!")
            return 0
        else:
            print("\n✗ Some tests failed")
            return 1

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\nCleaned up test directory: {test_dir}")


if __name__ == "__main__":
    sys.exit(main())
