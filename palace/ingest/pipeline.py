"""Big Bang ingestion pipeline."""

from pathlib import Path
from typing import List, Optional, Dict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import os
from palace.core.hippocampus import Hippocampus
from palace.ingest.parsers.base import BaseParser
from palace.ingest.parsers.registry import ParserRegistry
from palace.ingest.extractors import ConceptExtractor
from palace.ingest.invariants import InvariantDetector
from palace.shared.models import Artifact, Concept
import hashlib
import logging

logger = logging.getLogger(__name__)


class BigBangPipeline:
    """Complete ingestion pipeline for code repositories."""

    def __init__(
        self, hippocampus: Hippocampus, concept_extractor: Optional[ConceptExtractor] = None
    ):
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

        self.hippocampus.create_node(
            "Artifact",
            {
                "id": artifact_id,
                "path": str(file_path),
                "content_hash": content_hash,
                "language": self._get_language(file_path),
                "ast_fingerprint": fingerprint,
            },
        )

        # Extract and create concepts
        if self.concept_extractor:
            candidates = self.concept_extractor.extract_from_file(file_path, content, symbols)
            for candidate in candidates:
                concept_id = f"concept-{hashlib.md5(candidate.name.encode()).hexdigest()}"
                embedding_id = f"emb-{concept_id}"

                self.hippocampus.create_node(
                    "Concept",
                    {
                        "id": concept_id,
                        "name": candidate.name,
                        "embedding_id": embedding_id,
                        "layer": "implementation",
                        "stability": candidate.confidence,
                    },
                )

                # Store embedding
                if candidate.embedding:
                    import numpy as np

                    self.hippocampus.store_embedding(embedding_id, np.array(candidate.embedding))

                # Create EVOKES edge
                self.hippocampus.create_edge(
                    artifact_id, concept_id, "EVOKES", {"weight": candidate.confidence}
                )

        # Detect invariants
        violations = self.invariant_detector.detect_from_file(str(file_path), dependencies, symbols)
        for violation in violations:
            invariant_id = f"invariant-{hashlib.md5(violation.rule.encode()).hexdigest()}"
            self.hippocampus.create_node(
                "Invariant",
                {
                    "id": invariant_id,
                    "rule": violation.rule,
                    "severity": violation.severity,
                    "check_query": "",
                    "is_automatic": True,
                    "created_at": None,
                },
            )

            # Create CONSTRAINS edge
            self.hippocampus.create_edge(
                invariant_id, artifact_id, "CONSTRAINS", {"strictness": 0.8}
            )

        return {
            "status": "success",
            "dependencies": len(dependencies),
            "symbols": len(symbols),
            "violations": len(violations),
        }

    def _find_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Find appropriate parser for file using registry."""
        return self.registry.get_parser(file_path)

    def _get_language(self, file_path: Path) -> str:
        """Get language name from file extension using registry."""
        return self.registry.detect_language(file_path)

    def ingest_batch(
        self,
        file_paths: List[Path],
        batch_size: int = 50,
        max_workers: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Ingest multiple files using batch operations for better performance.

        Args:
            file_paths: List of file paths to ingest
            batch_size: Number of files to process before DB commit
            max_workers: Number of parallel workers (None = auto-detect)

        Returns:
            Dict with ingestion statistics
        """
        if not file_paths:
            return {
                "processed": 0,
                "artifacts": 0,
                "concepts": 0,
                "edges": 0,
                "errors": 0,
            }

        # Use ThreadPool for I/O-bound operations
        max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)

        stats = {
            "processed": 0,
            "artifacts": 0,
            "concepts": 0,
            "edges": 0,
            "errors": 0,
        }

        # Accumulators for batch operations
        artifacts_batch = []
        concepts_batch = []
        edges_batch = []
        embeddings_batch = []
        invariants_batch = []
        invariant_edges_batch = []

        logger.info(f"Processing {len(file_paths)} files with batch size {batch_size}")

        for i, file_path in enumerate(file_paths):
            try:
                # Read file
                content = file_path.read_text()

                # Find appropriate parser
                parser = self._find_parser(file_path)
                if not parser:
                    continue

                # Parse file
                dependencies = parser.parse_dependencies(file_path, content)
                symbols = parser.extract_symbols(content)
                fingerprint = parser.compute_fingerprint(content)

                # Create artifact data
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                artifact_id = f"artifact-{content_hash[:16]}"

                artifacts_batch.append(
                    {
                        "id": artifact_id,
                        "path": str(file_path),
                        "content_hash": content_hash,
                        "language": self._get_language(file_path),
                        "ast_fingerprint": fingerprint,
                    }
                )

                # Extract concepts
                if self.concept_extractor:
                    candidates = self.concept_extractor.extract_from_file(
                        file_path, content, symbols
                    )
                    for candidate in candidates:
                        concept_id = f"concept-{hashlib.md5(candidate.name.encode()).hexdigest()}"
                        embedding_id = f"emb-{concept_id}"

                        concepts_batch.append(
                            {
                                "id": concept_id,
                                "name": candidate.name,
                                "embedding_id": embedding_id,
                                "layer": "implementation",
                                "stability": candidate.confidence,
                            }
                        )

                        # Queue embedding
                        if candidate.embedding:
                            import numpy as np

                            embeddings_batch.append((embedding_id, np.array(candidate.embedding)))

                        # Queue edge
                        edges_batch.append(
                            {
                                "src_id": artifact_id,
                                "dst_id": concept_id,
                                "edge_type": "EVOKES",
                                "properties": {"weight": candidate.confidence},
                            }
                        )

                # Detect invariants
                violations = self.invariant_detector.detect_from_file(
                    str(file_path), dependencies, symbols
                )
                for violation in violations:
                    invariant_id = f"invariant-{hashlib.md5(violation.rule.encode()).hexdigest()}"
                    invariants_batch.append(
                        {
                            "id": invariant_id,
                            "rule": violation.rule,
                            "severity": violation.severity,
                            "check_query": "",
                            "is_automatic": True,
                            "created_at": None,
                        }
                    )

                    invariant_edges_batch.append(
                        {
                            "src_id": invariant_id,
                            "dst_id": artifact_id,
                            "edge_type": "CONSTRAINS",
                            "properties": {"strictness": 0.8},
                        }
                    )

                stats["processed"] += 1

                # Commit batch when threshold reached
                if len(artifacts_batch) >= batch_size:
                    self._commit_batch(
                        artifacts_batch,
                        concepts_batch,
                        edges_batch,
                        embeddings_batch,
                        invariants_batch,
                        invariant_edges_batch,
                        stats,
                    )
                    # Clear batches
                    artifacts_batch = []
                    concepts_batch = []
                    edges_batch = []
                    embeddings_batch = []
                    invariants_batch = []
                    invariant_edges_batch = []

                    if stats["processed"] % 100 == 0:
                        logger.info(f"Progress: {stats['processed']}/{len(file_paths)} files")

            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")
                stats["errors"] += 1

        # Commit remaining items
        if artifacts_batch:
            self._commit_batch(
                artifacts_batch,
                concepts_batch,
                edges_batch,
                embeddings_batch,
                invariants_batch,
                invariant_edges_batch,
                stats,
            )

        logger.info(f"Ingestion complete: {stats}")
        return stats

    def _commit_batch(
        self,
        artifacts: List[Dict],
        concepts: List[Dict],
        edges: List[Dict],
        embeddings: List,
        invariants: List[Dict],
        invariant_edges: List[Dict],
        stats: Dict,
    ) -> None:
        """Commit accumulated batch data to database."""
        try:
            # Batch create nodes
            if artifacts:
                self.hippocampus.create_nodes_batch("Artifact", artifacts)
                stats["artifacts"] += len(artifacts)

            if concepts:
                self.hippocampus.create_nodes_batch("Concept", concepts)
                stats["concepts"] += len(concepts)

            if invariants:
                self.hippocampus.create_nodes_batch("Invariant", invariants)

            # Batch create edges
            all_edges = edges + invariant_edges
            if all_edges:
                created = self.hippocampus.create_edges_batch(all_edges)
                stats["edges"] += created

            # Batch store embeddings
            if embeddings:
                self.hippocampus.store_embeddings_batch(embeddings)

        except Exception as e:
            logger.error(f"Failed to commit batch: {e}")
            raise
