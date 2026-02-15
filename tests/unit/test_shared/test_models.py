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
    from datetime import datetime
    decision = Decision(
        id="dec-1",
        title="Use PostgreSQL",
        timestamp=datetime.utcnow(),
        status="ACCEPTED",
        rationale="Best for relational data"
    )
    assert decision.status in ["PROPOSED", "ACCEPTED", "SUPERSEDED"]
