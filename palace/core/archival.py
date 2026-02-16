"""Tiered storage system for massive codebases.

For projects with millions of files, not all code needs to be in "hot" storage.
This system implements a 3-tier storage strategy:

- HOT: Recent code, frequently accessed (in main DB)
- WARM: Older code, occasionally accessed (compressed in main DB)
- COLD: Legacy/dead code, rarely accessed (archived to separate storage)
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import shutil


class TieredStorage:
    """
    Manages tiered storage for graph and vector data.

    Automatically migrates data between tiers based on access patterns
    and age.
    """

    # Tier thresholds
    HOT_DAYS = 30  # Hot tier: last 30 days
    WARM_DAYS = 365  # Warm tier: last year
    COLD_DAYS = None  # Cold tier: everything older

    # Access thresholds
    HOT_ACCESS_THRESHOLD = 10  # Accesses per month to stay hot
    WARM_ACCESS_THRESHOLD = 2   # Accesses per month to stay warm

    def __init__(self, palace_dir: Path):
        """
        Initialize tiered storage system.

        Args:
            palace_dir: Palace data directory
        """
        self.palace_dir = Path(palace_dir)
        self.hot_db = self.palace_dir / "brain.kuzu"
        self.warm_db = self.palace_dir / "brain_warm.kuzu"
        self.cold_db = self.palace_dir / "brain_cold.kuzu"

        self.hot_vectors = self.palace_dir / "vectors.db"
        self.warm_vectors = self.palace_dir / "vectors_warm.db"
        self.cold_vectors = self.palace_dir / "vectors_cold.db"

        # Access tracking
        self.access_db = self.palace_dir / "access_tracking.db"
        self._init_access_tracking()

    def _init_access_tracking(self) -> None:
        """Initialize access tracking database."""
        conn = sqlite3.connect(self.access_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifact_access (
                artifact_id TEXT PRIMARY KEY,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                tier TEXT DEFAULT 'hot'
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed
            ON artifact_access(last_accessed)
        """)

        conn.commit()
        conn.close()

    def record_access(self, artifact_id: str) -> None:
        """
        Record access to an artifact.

        Should be called whenever an artifact is queried.

        Args:
            artifact_id: Artifact that was accessed
        """
        conn = sqlite3.connect(self.access_db)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO artifact_access (artifact_id, last_accessed, access_count, tier)
            VALUES (?, ?, 1, 'hot')
            ON CONFLICT(artifact_id) DO UPDATE SET
                last_accessed = ?,
                access_count = access_count + 1
        """, (artifact_id, now, now))

        conn.commit()
        conn.close()

    def migrate_cold_data(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Migrate cold data to cold storage.

        Cold data criteria:
        - Not accessed in > 1 year
        - Access count < 2 in last month

        Args:
            dry_run: If True, don't actually migrate, just report

        Returns:
            Statistics about migration
        """
        conn = sqlite3.connect(self.access_db)
        cursor = conn.cursor()

        # Find cold candidates
        one_year_ago = (datetime.now() - timedelta(days=365)).isoformat()

        cursor.execute("""
            SELECT artifact_id, access_count
            FROM artifact_access
            WHERE last_accessed < ?
            AND access_count < ?
            AND tier != 'cold'
        """, (one_year_ago, self.WARM_ACCESS_THRESHOLD))

        cold_artifacts = cursor.fetchall()
        conn.close()

        if dry_run:
            return {
                'candidates': len(cold_artifacts),
                'migrated': 0,
            }

        # TODO: Implement actual migration
        # This would:
        # 1. Copy artifacts from hot to cold DB
        # 2. Delete from hot DB
        # 3. Update access_tracking

        return {
            'candidates': len(cold_artifacts),
            'migrated': 0,  # Not implemented yet
        }

    def compact_tier(self, tier: str = 'hot') -> int:
        """
        Compact database files for a tier.

        For SQLite: Run VACUUM
        For KuzuDB: Trigger checkpoint and compaction

        Args:
            tier: 'hot', 'warm', or 'cold'

        Returns:
            Space saved in bytes
        """
        if tier == 'hot':
            vec_db = self.hot_vectors
        elif tier == 'warm':
            vec_db = self.warm_vectors
        else:
            vec_db = self.cold_vectors

        if not vec_db.exists():
            return 0

        # Get size before
        size_before = vec_db.stat().st_size

        # Run VACUUM
        conn = sqlite3.connect(vec_db)
        conn.execute("VACUUM")
        conn.close()

        # Get size after
        size_after = vec_db.stat().st_size

        return size_before - size_after

    def get_storage_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get storage statistics for all tiers.

        Returns:
            Dict with size info for each tier
        """
        stats = {}

        for tier_name, db_path, vec_path in [
            ('hot', self.hot_db, self.hot_vectors),
            ('warm', self.warm_db, self.warm_vectors),
            ('cold', self.cold_db, self.cold_vectors),
        ]:
            stats[tier_name] = {
                'graph_db_mb': db_path.stat().st_size // (1024 * 1024) if db_path.exists() else 0,
                'vector_db_mb': vec_path.stat().st_size // (1024 * 1024) if vec_path.exists() else 0,
            }

        return stats


class DataArchiver:
    """
    Archives old/dead code to compressed storage.

    For massive repositories, archives:
    - Deleted branches
    - Deprecated modules
    - Test files (rarely accessed)
    - Generated code
    """

    def __init__(self, palace_dir: Path):
        """
        Initialize archiver.

        Args:
            palace_dir: Palace data directory
        """
        self.palace_dir = Path(palace_dir)
        self.archive_dir = self.palace_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)

    def archive_artifacts(self, artifact_ids: List[str], reason: str) -> None:
        """
        Archive artifacts to compressed storage.

        Args:
            artifact_ids: List of artifact IDs to archive
            reason: Reason for archiving (e.g., "deleted_branch", "deprecated")
        """
        # Create archive directory for this batch
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.archive_dir / f"{reason}_{timestamp}"
        batch_dir.mkdir(exist_ok=True)

        # TODO: Implement actual archiving
        # This would:
        # 1. Export artifacts to JSON
        # 2. Compress with gzip
        # 3. Remove from main DB
        pass

    def estimate_archive_savings(self) -> Dict[str, int]:
        """
        Estimate potential space savings from archiving.

        Returns:
            Dict with estimates
        """
        # TODO: Scan for rarely accessed artifacts
        return {
            'archiveable_artifacts': 0,
            'potential_savings_mb': 0,
        }
