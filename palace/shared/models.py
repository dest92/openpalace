"""Data models for Palacio Mental."""

from pydantic import BaseModel, Field, field_validator
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

    @field_validator('severity')
    @classmethod
    def severity_must_be_valid(cls, v: str) -> str:
        if v not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            raise ValueError(f"Invalid severity: {v}")
        return v


class Decision(NodeModel):
    """Architectural Decision Record (ADR)."""
    title: str = Field(..., description="Decision title")
    timestamp: datetime = Field(..., description="When decision was made")
    status: Literal["PROPOSED", "ACCEPTED", "SUPERSEDED"] = Field(
        ...,
        description="Current status"
    )
    rationale: str = Field(..., description="Why this decision was made")

    @field_validator('status')
    @classmethod
    def status_must_be_valid(cls, v: str) -> str:
        if v not in ["PROPOSED", "ACCEPTED", "SUPERSEDED"]:
            raise ValueError(f"Invalid status: {v}")
        return v


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
