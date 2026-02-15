"""Tests for ingestion pipeline."""

import pytest
from pathlib import Path
from palace.ingest.pipeline import BigBangPipeline
from palace.core.hippocampus import Hippocampus

try:
    from palace.ingest.extractors import ConceptExtractor
    CONCEPT_EXTRACTOR_AVAILABLE = True
except ImportError:
    CONCEPT_EXTRACTOR_AVAILABLE = False


@pytest.fixture
def pipeline(tmp_path):
    """Create a pipeline instance."""
    palace_dir = tmp_path / ".palace"
    palace_dir.mkdir()

    hippo = Hippocampus(palace_dir)
    hippo.initialize_schema()

    extractor = ConceptExtractor() if CONCEPT_EXTRACTOR_AVAILABLE else None

    return BigBangPipeline(hippo, concept_extractor=extractor), palace_dir


def test_pipeline_ingest_python_file(pipeline):
    """Test ingesting a Python file."""
    pipe, palace_dir = pipeline

    # Create test file
    test_file = palace_dir.parent / "test.py"
    test_file.write_text("""
def calculate(x, y):
    '''Calculate something.'''
    return x + y
""")

    # Ingest
    result = pipe.ingest_file(test_file)

    assert result["status"] == "success"
    assert result["symbols"] > 0


def test_pipeline_skips_unsupported_extensions(pipeline):
    """Test that unsupported files are skipped."""
    pipe, palace_dir = pipeline

    # Create unsupported file
    test_file = palace_dir.parent / "test.xyz"
    test_file.write_text("content")

    # Ingest
    result = pipe.ingest_file(test_file)

    assert result["status"] == "skipped"
