#!/usr/bin/env python3
"""
Palace Mental V1 → V2 Migration Script

Migrates existing V1 database to V2 architecture:

Steps:
1. Parse all code → AST fingerprints (32 bytes each)
2. Build Bloom filter (2MB for 10M items)
3. Keep existing KuzuDB graph
4. Remove SQLite+vec database

Usage:
    python scripts/migrate_v1_to_v2.py [--palace-dir PATH]
"""

import argparse
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Palace Mental V2 imports
from palace.core.hippocampus import Hippocampus
from palace.core.bloom_filter import create_palace_bloom_filter
from palace.core.tree_sitter_v2 import parse_file_v2, detect_language
from palace.core.ast_fingerprint import ASTFingerprintCache


@dataclass
class MigrationStats:
    """Statistics from migration."""
    total_files: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    bloom_items: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0
    duration_seconds: float = 0.0
    v1_db_size_mb: float = 0.0
    v2_db_size_mb: float = 0.0


class V1ToV2Migrator:
    """
    Migrates Palace Mental V1 to V2 architecture.

    What changes:
    - REMOVED: SQLite+vec (vectors.db)
    - REMOVED: Embeddings (1.5KB per artifact)
    - ADDED: AST fingerprints (32 bytes per artifact)
    - ADDED: Bloom filter (2MB for 10M items)
    - KEPT: KuzuDB graph
    """

    def __init__(self, palace_dir: Path, dry_run: bool = False):
        """
        Initialize migrator.

        Args:
            palace_dir: Path to .palace/ directory
            dry_run: If True, don't modify databases
        """
        self.palace_dir = Path(palace_dir)
        self.dry_run = dry_run

        # Paths
        self.kuzu_db_path = self.palace_dir / "brain.kuzu"
        self.v1_vec_db_path = self.palace_dir / "vectors.db"
        self.v2_bloom_path = self.palace_dir / "bloom_filter.pkl"

        # Initialize V2 components
        self.hippocampus = None
        self.bloom_filter = None
        self.fingerprint_cache = ASTFingerprintCache()

    def migrate(self) -> MigrationStats:
        """
        Execute full migration.

        Returns:
            MigrationStats with results
        """
        start_time = time.time()
        stats = MigrationStats()

        print("🚀 Starting Palace Mental V1 → V2 Migration")
        print("=" * 60)

        # Step 1: Validate V1 database
        print("\n📋 Step 1: Validating V1 database...")
        if not self._validate_v1_database(stats):
            print("❌ V1 database validation failed")
            return stats

        # Step 2: Backup V1 data
        print("\n💾 Step 2: Backing up V1 data...")
        backup_path = self._backup_v1_data()
        print(f"  ✅ Backup created: {backup_path}")

        # Step 3: Initialize V2 components
        print("\n🔧 Step 3: Initializing V2 components...")
        self._initialize_v2_components(stats)

        # Step 4: Get all artifacts from graph
        print("\n📊 Step 4: Discovering artifacts...")
        artifacts = self._discover_artifacts()
        stats.total_files = len(artifacts)
        print(f"  ✅ Found {stats.total_files:,} artifacts")

        # Step 5: Parse all files → AST fingerprints
        print("\n🌳 Step 5: Parsing code → AST fingerprints...")
        self._parse_artifacts(artifacts, stats)

        # Step 6: Build Bloom filter
        print("\n🌸 Step 6: Building Bloom filter...")
        self._build_bloom_filter(artifacts, stats)

        # Step 7: Update graph with fingerprints
        if not self.dry_run:
            print("\n📝 Step 7: Updating graph with AST fingerprints...")
            self._update_graph_fingerprints(artifacts, stats)

        # Step 8: Remove V1 databases
        if not self.dry_run:
            print("\n🗑️  Step 8: Removing V1 databases...")
            self._remove_v1_databases(stats)

        # Step 9: Calculate final statistics
        stats.duration_seconds = time.time() - start_time
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE")
        self._print_summary(stats)

        return stats

    def _validate_v1_database(self, stats: MigrationStats) -> bool:
        """Validate V1 database exists and is accessible."""
        if not self.kuzu_db_path.exists():
            print("  ❌ KuzuDB database not found")
            print(f"     Expected: {self.kuzu_db_path}")
            return False

        print(f"  ✅ KuzuDB found: {self.kuzu_db_path}")

        if self.v1_vec_db_path.exists():
            size_mb = self.v1_vec_db_path.stat().st_size / (1024 * 1024)
            stats.v1_db_size_mb += size_mb
            print(f"  ✅ V1 vectors.db found: {size_mb:.2f}MB")
        else:
            print("  ⚠️  V1 vectors.db not found (already migrated?)")

        return True

    def _backup_v1_data(self) -> Path:
        """Create backup of V1 data."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = self.palace_dir.parent / f".palace.v1.backup.{timestamp}"

        # Copy files
        import shutil
        shutil.copy2(self.kuzu_db_path, backup_dir / "brain.kuzu")

        if self.v1_vec_db_path.exists():
            shutil.copy2(self.v1_vec_db_path, backup_dir / "vectors.db")

        return backup_dir

    def _initialize_v2_components(self, stats: MigrationStats) -> None:
        """Initialize V2 Hippocampus and Bloom filter."""
        # Connect to KuzuDB
        self.hippocampus = Hippocampus(self.palace_dir)

        # Get current stats
        graph_stats = self.hippocampus.get_statistics()
        stats.graph_nodes = graph_stats.get('artifact_count', 0)
        stats.graph_edges = graph_stats.get('depends_on_count', 0)

        print(f"  ✅ KuzuDB connected")
        print(f"     Artifacts: {stats.graph_nodes:,}")
        print(f"     Edges: {stats.graph_edges:,}")

        # Create Bloom filter
        expected_items = max(stats.graph_nodes, 10_000_000)
        self.bloom_filter = create_palace_bloom_filter(
            num_artifacts=expected_items,
            false_positive_rate=0.001
        )

        print(f"  ✅ Bloom filter created")
        print(f"     Capacity: {expected_items:,} items")

    def _discover_artifacts(self) -> List[Dict]:
        """Get all artifacts from graph."""
        query = """
            MATCH (a:Artifact)
            RETURN a.id AS id, a.path AS path
            LIMIT 10000000
        """

        results = self.hippocampus.execute_cypher(query, {})
        artifacts = []

        for row in results:
            artifacts.append({
                'id': row['id'],
                'path': Path(row['path']) if row['path'] else None
            })

        return artifacts

    def _parse_artifacts(self, artifacts: List[Dict], stats: MigrationStats) -> None:
        """Parse all artifacts and compute AST fingerprints."""
        total = len(artifacts)
        batch_size = 100
        success = 0
        failed = 0

        for i in range(0, total, batch_size):
            batch = artifacts[i:i+batch_size]

            for artifact in batch:
                file_path = artifact['path']

                if not file_path or not file_path.exists():
                    failed += 1
                    continue

                try:
                    # Parse file with tree-sitter V2
                    result = parse_file_v2(file_path)

                    # Cache fingerprint
                    self.fingerprint_cache.set(
                        artifact['id'],
                        result.ast_fingerprint
                    )

                    if result.parse_success:
                        success += 1
                    else:
                        failed += 1

                except Exception as e:
                    failed += 1

            # Progress
            if (i + batch_size) % 1000 == 0 or i + batch_size >= total:
                progress = min(i + batch_size, total)
                print(f"  Progress: {progress:,}/{total:,} "
                      f"(✅ {success:,}, ❌ {failed:,})")

        stats.successful_parses = success
        stats.failed_parses = failed

    def _build_bloom_filter(self, artifacts: List[Dict], stats: MigrationStats) -> None:
        """Build Bloom filter with all artifact IDs."""
        for artifact in artifacts:
            self.bloom_filter.add(artifact['id'])

        stats.bloom_items = stats.total_files

        bloom_stats = self.bloom_filter.get_stats()
        print(f"  ✅ Bloom filter populated")
        print(f"     Items: {stats.bloom_items:,}")
        print(f"     Size: {bloom_stats['size_mb']:.2f}MB")
        print(f"     Load factor: {bloom_stats['load_factor']:.2%}")

        # Save to disk
        if not self.dry_run:
            self.bloom_filter.save(self.v2_bloom_path)
            print(f"  ✅ Saved: {self.v2_bloom_path}")

    def _update_graph_fingerprints(self, artifacts: List[Dict], stats: MigrationStats) -> None:
        """Update artifact nodes with AST fingerprints."""
        batch_size = 100
        updated = 0

        for i in range(0, len(artifacts), batch_size):
            batch = artifacts[i:i+batch_size]

            for artifact in batch:
                artifact_id = artifact['id']
                fingerprint = self.fingerprint_cache.get(artifact_id)

                if fingerprint:
                    # Update node
                    query = """
                        MATCH (a:Artifact)
                        WHERE a.id = $artifact_id
                        SET a.ast_fingerprint = $fingerprint
                    """

                    self.hippocampus.execute_cypher(query, {
                        'artifact_id': artifact_id,
                        'fingerprint': fingerprint
                    })
                    updated += 1

            # Progress
            if (i + batch_size) % 1000 == 0 or i + batch_size >= len(artifacts):
                print(f"  Progress: {min(i + batch_size, len(artifacts)):,}/{len(artifacts):,}")

        print(f"  ✅ Updated {updated:,} artifacts with AST fingerprints")

    def _remove_v1_databases(self, stats: MigrationStats) -> None:
        """Remove V1 vector database."""
        if self.v1_vec_db_path.exists():
            size_mb = self.v1_vec_db_path.stat().st_size / (1024 * 1024)

            # Remove
            self.v1_vec_db_path.unlink()
            stats.v2_db_size_mb -= size_mb

            print(f"  ✅ Removed vectors.db ({size_mb:.2f}MB)")
            print(f"     Storage saved: {size_mb:.2f}MB")

    def _print_summary(self, stats: MigrationStats) -> None:
        """Print migration summary."""
        print("\n📊 MIGRATION SUMMARY")
        print("-" * 60)

        print(f"\nFiles Processed:")
        print(f"  Total artifacts:     {stats.total_files:,}")
        print(f"  Successful parses:  {stats.successful_parses:,} ✅")
        print(f"  Failed parses:      {stats.failed_parses:,} ❌")

        print(f"\nV2 Components:")
        print(f"  Bloom filter items:  {stats.bloom_items:,}")
        print(f"  Graph nodes:         {stats.graph_nodes:,}")
        print(f"  Graph edges:         {stats.graph_edges:,}")

        print(f"\nStorage:")
        print(f"  V1 databases:        {stats.v1_db_size_mb:.2f}MB")
        print(f"  V2 databases:        {stats.v2_db_size_mb:.2f}MB")
        if stats.v1_db_size_mb > 0:
            reduction = (stats.v1_db_size_mb - stats.v2_db_size_mb) / stats.v1_db_size_mb
            print(f"  Reduction:          {reduction:.1%} ✅")

        print(f"\nPerformance:")
        print(f"  Duration:            {stats.duration_seconds:.1f}s")
        if stats.total_files > 0:
            throughput = stats.total_files / stats.duration_seconds
            print(f"  Throughput:          {throughput:.1f} files/s")

        print(f"\n✅ Migration complete! Palace Mental V2 is ready.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate Palace Mental V1 to V2"
    )
    parser.add_argument(
        '--palace-dir',
        type=Path,
        default=Path('.palace'),
        help='Path to .palace directory (default: .palace)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate migration without modifying databases'
    )

    args = parser.parse_args()

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No databases will be modified\n")

    # Create migrator
    migrator = V1ToV2Migrator(args.palace_dir, dry_run=args.dry_run)

    # Execute migration
    try:
        stats = migrator.migrate()
        return 0 if stats.successful_parses > 0 else 1
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
