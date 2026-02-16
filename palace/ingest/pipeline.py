"""Big Bang ingestion pipeline."""

from pathlib import Path
from typing import List, Optional
from palace.core.hippocampus import Hippocampus
from palace.ingest.parsers.base import BaseParser
from palace.ingest.parsers.registry import ParserRegistry
from palace.ingest.extractors import ConceptExtractor
from palace.ingest.invariants import InvariantDetector
from palace.shared.models import Artifact, Concept
import hashlib


class BigBangPipeline:
    """Complete ingestion pipeline for code repositories."""

    def __init__(self, hippocampus: Hippocampus, concept_extractor: Optional[ConceptExtractor] = None):
        """
        Initialize pipeline.

        Args:
            hippocampus: Graph database interface
            concept_extractor: Optional concept extractor
        """
        self.hippocampus = hippocampus
        self.concept_extractor = concept_extractor
        self.invariant_detector = InvariantDetector()
        self.registry = ParserRegistry.instance()

    def ingest_file(self, file_path: Path) -> dict:
        """
        Ingest a single file.

        Args:
            file_path: Path to the file

        Returns:
            Dict with ingestion statistics
        """
        # Read file
        content = file_path.read_text()

        # Find appropriate parser
        parser = self._find_parser(file_path)
        if not parser:
            return {"status": "skipped", "reason": "No parser for extension"}

        # Parse file
        dependencies = parser.parse_dependencies(file_path, content)
        symbols = parser.extract_symbols(content)
        fingerprint = parser.compute_fingerprint(content)

        # Create artifact node
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        artifact_id = f"artifact-{content_hash[:16]}"

        self.hippocampus.create_node("Artifact", {
            "id": artifact_id,
            "path": str(file_path),
            "content_hash": content_hash,
            "language": self._get_language(file_path),
            "ast_fingerprint": fingerprint
        })

        # Extract and create concepts
        if self.concept_extractor:
            candidates = self.concept_extractor.extract_from_file(file_path, content, symbols)
            for candidate in candidates:
                concept_id = f"concept-{hashlib.md5(candidate.name.encode()).hexdigest()}"
                embedding_id = f"emb-{concept_id}"

                self.hippocampus.create_node("Concept", {
                    "id": concept_id,
                    "name": candidate.name,
                    "embedding_id": embedding_id,
                    "layer": "implementation",
                    "stability": candidate.confidence
                })

                # Store embedding
                if candidate.embedding:
                    import numpy as np
                    self.hippocampus.store_embedding(embedding_id, np.array(candidate.embedding))

                # Create EVOKES edge
                self.hippocampus.create_edge(artifact_id, concept_id, "EVOKES", {
                    "weight": candidate.confidence
                })

        # Detect invariants
        violations = self.invariant_detector.detect_from_file(str(file_path), dependencies, symbols)
        for violation in violations:
            invariant_id = f"invariant-{hashlib.md5(violation.rule.encode()).hexdigest()}"
            self.hippocampus.create_node("Invariant", {
                "id": invariant_id,
                "rule": violation.rule,
                "severity": violation.severity,
                "check_query": "",
                "is_automatic": True,
                "created_at": None
            })

            # Create CONSTRAINS edge
            self.hippocampus.create_edge(invariant_id, artifact_id, "CONSTRAINS", {
                "strictness": 0.8
            })

        return {
            "status": "success",
            "dependencies": len(dependencies),
            "symbols": len(symbols),
            "violations": len(violations)
        }

    def _find_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Find appropriate parser for file using registry."""
        return self.registry.get_parser(file_path)

    def _get_language(self, file_path: Path) -> str:
        """Get language name from file extension using registry."""
        return self.registry.detect_language(file_path)
