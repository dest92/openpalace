"""Concept extraction and embedding generation."""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class ConceptCandidate:
    """A candidate concept extracted from code."""
    name: str
    confidence: float
    embedding: Optional[List[float]] = None


class ConceptExtractor:
    """Extracts concepts from code using NLP."""

    def __init__(self, model=None):
        """
        Initialize concept extractor.

        Args:
            model: SentenceTransformer model (optional)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not installed")

        self.model = model or SentenceTransformer('all-MiniLM-L6-v2')

    def extract_from_file(self, file_path: Path, content: str, symbols: List) -> List[ConceptCandidate]:
        """
        Extract concepts from a file.

        Args:
            file_path: Path to the file
            content: File content
            symbols: List of symbols from parser

        Returns:
            List of concept candidates
        """
        candidates = []

        # Extract from symbols
        for symbol in symbols:
            # Create description from symbol name and docstring
            description = f"{symbol.name}: {symbol.docstring}"
            embedding = self.model.encode(description).tolist()

            candidates.append(ConceptCandidate(
                name=symbol.name,
                confidence=0.8,
                embedding=embedding
            ))

        return candidates
