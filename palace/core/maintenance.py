"""Aggressive maintenance operations for massive-scale databases.

For projects with millions of nodes/edges, regular maintenance is critical
to prevent database bloat. This module provides:
- Aggressive pruning of dead data
- Database compaction
- Index optimization
- Space reclamation
"""

import kuzu
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
import time


class DatabaseMaintainer:
    """
    Performs aggressive maintenance on KuzuDB and SQLite databases.

    Should be run periodically (weekly/monthly) to keep databases lean.
    """

    def __init__(self, palace_dir: Path):
        """
        Initialize maintainer.

        Args:
            palace_dir: Palace data directory
        """
        self.palace_dir = Path(palace_dir)
        self.kuzu_db_path = self.palace_dir / "brain.kuzu"
        self.sqlite_db_path = self.palace_dir / "vectors.db"

    def full_maintenance(self) -> Dict[str, any]:
        """
        Run full maintenance cycle.

        Returns:
            Dict with maintenance results
        """
        start_time = time.time()

        results = {
            'kuzu_compaction': self._compact_kuzu(),
            'sqlite_compaction': self._compact_sqlite(),
            'dead_nodes_removed': self._prune_dead_nodes(),
            'weak_edges_removed': self._prune_weak_edges(aggressive=True),
            'orphaned_embeddings_removed': self._prune_orphaned_embeddings(),
            'duration_seconds': time.time() - start_time,
        }

        # Calculate total space saved
        results['space_saved_mb'] = self._calculate_space_saved()

        return results

    def _compact_kuzu(self) -> Dict[str, int]:
        """
        Compact KuzuDB database.

        KuzuDB doesn't have VACUUM, but we can:
        1. Force checkpoint
        2. Trigger buffer pool flush
        3. Rebuild indexes if needed
        """
        if not self.kuzu_db_path.exists():
            return {'status': 'skipped', 'reason': 'database not found'}

        try:
            db = kuzu.Database(str(self.kuzu_db_path))
            conn = kuzu.Connection(db)

            # Checkpoint and flush
            conn.execute("CALL sanity_check();")

            # Get node/edge counts before
            node_result = conn.execute("MATCH (n) RETURN count(n) AS count")
            edge_result = conn.execute("MATCH ()-[r]->() RETURN count(r) AS count")

            node_count = node_result.get_next()[0] if node_result.has_next() else 0
            edge_count = edge_result.get_next()[0] if edge_result.has_next() else 0

            conn.close()
            db.close()

            return {
                'status': 'success',
                'nodes': node_count,
                'edges': edge_count,
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _compact_sqlite(self) -> Dict[str, int]:
        """
        Compact SQLite database with VACUUM.

        VACUUM rebuilds the database file, reclaiming free space.
        """
        if not self.sqlite_db_path.exists():
            return {'status': 'skipped', 'reason': 'database not found'}

        # Get size before
        size_before = self.sqlite_db_path.stat().st_size

        try:
            conn = sqlite3.connect(self.sqlite_db_path)

            # VACUUM to reclaim space
            conn.execute("VACUUM")

            # ANALYZE to update statistics
            conn.execute("ANALYZE")

            # Rebuild indexes
            conn.execute("REINDEX")

            conn.close()

            # Get size after
            size_after = self.sqlite_db_path.stat().st_size

            return {
                'status': 'success',
                'size_before_mb': size_before // (1024 * 1024),
                'size_after_mb': size_after // (1024 * 1024),
                'saved_mb': (size_before - size_after) // (1024 * 1024),
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _prune_dead_nodes(self, threshold_days: int = 365) -> int:
        """
        Remove nodes that haven't been accessed in threshold_days.

        Dead nodes are artifacts that:
        - No longer exist in filesystem
        - Haven't been accessed in > 1 year
        - Have no strong connections

        Args:
            threshold_days: Days of inactivity before pruning

        Returns:
            Number of nodes removed
        """
        # TODO: Implement dead node detection and removal
        # This requires:
        # 1. Track artifact last_modified
        # 2. Check if file still exists
        # 3. Check access patterns
        # 4. Remove if truly dead
        return 0

    def _prune_weak_edges(self, aggressive: bool = False) -> int:
        """
        Remove weak edges from the graph.

        Weak edges are edges with low weight that contribute little
        to graph connectivity.

        Args:
            aggressive: If True, use higher threshold (0.3 vs 0.1)

        Returns:
            Number of edges removed
        """
        threshold = 0.3 if aggressive else 0.1

        try:
            db = kuzu.Database(str(self.kuzu_db_path))
            conn = kuzu.Connection(db)

            # Count edges to remove
            count_result = conn.execute(f"""
                MATCH ()-[r:RELATED_TO]->()
                WHERE r.weight < {threshold}
                RETURN count(r) AS count
            """)

            count = count_result.get_next()[0] if count_result.has_next() else 0

            if count > 0:
                # Delete weak edges
                conn.execute(f"""
                    MATCH ()-[r:RELATED_TO]->()
                    WHERE r.weight < {threshold}
                    DELETE r
                """)

            conn.close()
            db.close()

            return count
        except Exception as e:
            print(f"Error pruning edges: {e}")
            return 0

    def _prune_orphaned_embeddings(self) -> int:
        """
        Remove embeddings that have no corresponding nodes.

        Embeddings can become orphaned when:
        - Artifacts are deleted
        - Concepts are pruned
        - Incomplete ingestion

        Returns:
            Number of embeddings removed
        """
        if not self.sqlite_db_path.exists():
            return 0

        try:
            vec_conn = sqlite3.connect(self.sqlite_db_path)
            kuzu_db = kuzu.Database(str(self.kuzu_db_path))
            kuzu_conn = kuzu.Connection(kuzu_db)

            # Get all embedding IDs from SQLite
            cursor = vec_conn.cursor()
            cursor.execute("SELECT node_id FROM vec_embeddings")
            vec_ids = set(row[0] for row in cursor.fetchall())

            # Get all node IDs from KuzuDB
            node_result = kuzu_conn.execute("MATCH (n) RETURN n.id AS id")
            kuzu_ids = set()
            while node_result.has_next():
                kuzu_ids.add(node_result.get_next()[0])

            # Find orphaned embeddings
            orphaned = vec_ids - kuzu_ids

            # Remove orphaned embeddings
            for node_id in orphaned:
                cursor.execute(
                    "DELETE FROM vec_embeddings WHERE node_id = ?",
                    (node_id,)
                )

            vec_conn.commit()
            vec_conn.close()
            kuzu_conn.close()
            kuzu_db.close()

            return len(orphaned)

        except Exception as e:
            print(f"Error pruning embeddings: {e}")
            return 0

    def _calculate_space_saved(self) -> int:
        """Calculate total space saved in MB."""
        # This would compare database sizes before/after
        # For now, return placeholder
        return 0

    def get_storage_breakdown(self) -> Dict[str, Dict[str, any]]:
        """
        Get detailed storage breakdown.

        Returns:
            Dict with storage info by component
        """
        kuzu_size = self.kuzu_db_path.stat().st_size // (1024 * 1024) if self.kuzu_db_path.exists() else 0
        sqlite_size = self.sqlite_db_path.stat().st_size // (1024 * 1024) if self.sqlite_db_path.exists() else 0

        return {
            'kuzu_db': {
                'path': str(self.kuzu_db_path),
                'size_mb': kuzu_size,
            },
            'sqlite_db': {
                'path': str(self.sqlite_db_path),
                'size_mb': sqlite_size,
            },
            'total_mb': kuzu_size + sqlite_size,
        }


class StorageOptimizer:
    """
    Advanced storage optimization strategies.

    Implements:
    - Graph compression (remove redundant paths)
    - Delta encoding for similar embeddings
    - Sparse representation for high-dimensional data
    """

    @staticmethod
    def compress_similar_embeddings(embeddings: List[bytes], similarity_threshold: float = 0.98) -> List[Tuple[bytes, bytes]]:
        """
        Compress embeddings using delta encoding.

        For very similar embeddings, store only the delta.

        Args:
            embeddings: List of embedding bytes
            similarity_threshold: Minimum similarity to use delta encoding

        Returns:
            List of (base_embedding, delta) tuples
        """
        # TODO: Implement delta encoding
        # This would:
        # 1. Cluster similar embeddings
        # 2. Store one base embedding per cluster
        # 3. Store deltas for others
        return []

    @staticmethod
    def sparse_representation(embedding: bytes, sparsity_threshold: float = 0.1) -> Tuple[bytes, List[int]]:
        """
        Convert embedding to sparse representation.

        For embeddings with many near-zero values, store only
        the indices and values of significant dimensions.

        Args:
            embedding: Full embedding bytes
            sparsity_threshold: Threshold below which value is considered zero

        Returns:
            Tuple of (sparse_values, significant_indices)
        """
        # TODO: Implement sparse encoding
        return (b'', [])
