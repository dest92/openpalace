"""Hippocampus - Main interface to graph and vector databases."""

import kuzu
import sqlite3
import sqlite_vec
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Literal
import numpy as np
from palace.core.compression import EmbeddingCompressor


class Hippocampus:
    """
    Main interface to KuzuDB and SQLite+vec.
    Manages graph schema, node/edge CRUD, and vector operations.
    """

    def __init__(self, palace_dir: Path):
        """
        Initialize both databases.

        Args:
            palace_dir: Directory containing .palace/ data
        """
        self.palace_dir = Path(palace_dir)
        self.palace_dir.mkdir(parents=True, exist_ok=True)

        # Initialize KuzuDB
        self.db_path = self.palace_dir / "brain.kuzu"
        self.kuzu_db = kuzu.Database(str(self.db_path))
        self.kuzu_conn = kuzu.Connection(self.kuzu_db)

        # Initialize SQLite+vec
        self.vec_db_path = self.palace_dir / "vectors.db"
        self.vec_conn = sqlite3.connect(str(self.vec_db_path))
        self.vec_conn.enable_load_extension(True)
        sqlite_vec.load(self.vec_conn)
        self.vec_conn.enable_load_extension(False)

    def is_connected(self) -> bool:
        """Check if databases are connected."""
        return self.kuzu_conn is not None and self.vec_conn is not None

    def initialize_schema(self) -> None:
        """Create all node types, edge types, and vector tables."""
        self._create_kuzu_schema()
        self._create_vector_schema()

    def _create_kuzu_schema(self) -> None:
        """Create KuzuDB node and edge types."""
        # Node types
        node_types = [
            """
            CREATE NODE TABLE Concept (
                id STRING,
                name STRING,
                embedding_id STRING,
                layer STRING,
                stability FLOAT,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Artifact (
                id STRING,
                path STRING,
                content_hash STRING,
                language STRING,
                ast_fingerprint STRING,
                last_modified TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Invariant (
                id STRING,
                rule STRING,
                severity STRING,
                check_query STRING,
                is_automatic BOOLEAN,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Decision (
                id STRING,
                title STRING,
                timestamp TIMESTAMP,
                status STRING,
                rationale STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
            """
            CREATE NODE TABLE Anchor (
                id STRING,
                spatial_coords STRING,
                description STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (id)
            )
            """,
        ]

        for node_type in node_types:
            try:
                self.kuzu_conn.execute(node_type)
            except Exception:
                # Node type might already exist
                pass

        # Edge types
        edge_types = [
            """
            CREATE REL TABLE EVOKES (
                FROM Artifact TO Concept,
                weight DOUBLE,
                last_activated TIMESTAMP
            )
            """,
            """
            CREATE REL TABLE CONSTRAINS (
                FROM Invariant TO Artifact,
                strictness DOUBLE
            )
            """,
            """
            CREATE REL TABLE DEPENDS_ON (
                FROM Artifact TO Artifact,
                weight DOUBLE,
                dependency_type STRING
            )
            """,
            """
            CREATE REL TABLE PRECEDES (
                FROM Decision TO Decision,
                reason STRING
            )
            """,
            """
            CREATE REL TABLE RELATED_TO (
                FROM Concept TO Concept,
                weight DOUBLE
            )
            """,
        ]

        for edge_type in edge_types:
            try:
                self.kuzu_conn.execute(edge_type)
            except Exception:
                # Edge type might already exist
                pass

    def _create_vector_schema(self) -> None:
        """Create SQLite+vec tables for embeddings."""
        cursor = self.vec_conn.cursor()

        # Create embeddings table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings
            USING vec0(
                node_id TEXT PRIMARY KEY,
                embedding FLOAT[384]
            )
        """)

        # Apply SQLite optimizations
        self._apply_sqlite_optimizations(cursor)
        self.vec_conn.commit()

    def _apply_sqlite_optimizations(self, cursor) -> None:
        """Apply SQLite performance pragmas for better performance."""
        pragmas = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -100000",  # 100MB cache
            "PRAGMA mmap_size = 2147483648",  # 2GB mmap
            "PRAGMA temp_store = MEMORY",
            "PRAGMA page_size = 4096",
        ]
        for pragma in pragmas:
            try:
                cursor.execute(pragma)
            except Exception:
                # Some pragmas may not be supported
                pass

    def get_node_types(self) -> List[str]:
        """Get all node types in the graph."""
        # KuzuDB uses a different syntax - we'll use a simple query
        # For now, return the known node types
        return ["Concept", "Artifact", "Invariant", "Decision", "Anchor"]

    def close(self) -> None:
        """Close database connections."""
        if self.kuzu_conn:
            self.kuzu_conn.close()
        if self.vec_conn:
            self.vec_conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def create_node(self, node_type: str, properties: Dict) -> str:
        """
        Create a node in the graph.

        Args:
            node_type: Type of node (Concept, Artifact, etc.)
            properties: Dictionary of node properties

        Returns:
            The ID of the created node
        """
        # Build parameterized query - KuzuDB needs explicit parameter references
        prop_list = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{node_type} {{{prop_list}}})"
        self.kuzu_conn.execute(query, properties)
        return properties["id"]

    def create_edge(self, src_id: str, dst_id: str, edge_type: str, properties: Dict) -> None:
        """
        Create an edge between two nodes.

        Args:
            src_id: Source node ID
            dst_id: Destination node ID
            edge_type: Type of edge (EVOKES, DEPENDS_ON, etc.)
            properties: Edge properties
        """
        # Build properties string
        if properties:
            prop_list = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            # Need to escape braces for f-string
            query = f"""
                MATCH (src), (dst)
                WHERE src.id = $src_id AND dst.id = $dst_id
                CREATE (src)-[r:{edge_type} {{prop_list}}]->(dst)
            """
            query = query.replace("{prop_list}", "{" + prop_list + "}")
            params = {"src_id": src_id, "dst_id": dst_id, **properties}
        else:
            query = f"""
                MATCH (src), (dst)
                WHERE src.id = $src_id AND dst.id = $dst_id
                CREATE (src)-[r:{edge_type}]->(dst)
            """
            params = {"src_id": src_id, "dst_id": dst_id}
        self.kuzu_conn.execute(query, params)

    def get_node(self, node_id: str) -> Optional[Dict]:
        """
        Get a node by ID.

        Args:
            node_id: Node ID to retrieve

        Returns:
            Node properties dict or None if not found
        """
        query = "MATCH (n) WHERE n.id = $node_id RETURN n"
        result = self.kuzu_conn.execute(query, {"node_id": node_id})

        if result.has_next():
            row = result.get_next()
            # In KuzuDB 0.5.0, when returning a node, it comes as a list
            # with nested structure. We need to handle this properly.
            if row and len(row) > 0:
                return row[0] if isinstance(row[0], dict) else {"data": row[0]}
        return None

    def execute_cypher(self, query: str, params: Dict) -> List[Dict]:
        """
        Execute a Cypher query.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result rows as dicts
        """
        result = self.kuzu_conn.execute(query, params)
        rows = []

        if result.has_next():
            # Get column names before consuming results
            column_names = result.get_column_names()

            while result.has_next():
                row = result.get_next()
                # Convert list to dict using column names
                if isinstance(row, list) and column_names:
                    row_dict = dict(zip(column_names, row))
                    rows.append(row_dict)
                else:
                    # Fallback: return as-is
                    rows.append(row)

        return rows

    def store_embedding(self, node_id: str, embedding: np.ndarray) -> None:
        """
        Store an embedding vector.

        Args:
            node_id: Node ID to associate with embedding
            embedding: Vector to store (numpy array)
        """
        cursor = self.vec_conn.cursor()
        # Ensure embedding is float32
        embedding = embedding.astype(np.float32)
        # sqlite-vec uses a different syntax - store as blob
        cursor.execute(
            "INSERT OR REPLACE INTO vec_embeddings(node_id, embedding) VALUES (?, ?)",
            [node_id, embedding.tobytes()],
        )
        self.vec_conn.commit()

    def similarity_search(
        self, query_embedding: np.ndarray, top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find similar embeddings using sqlite-vec native KNN search.
        Much faster than Python-based similarity computation.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of (node_id, distance) tuples
        """
        cursor = self.vec_conn.cursor()
        # Use sqlite-vec's native vector search with MATCH operator
        # This uses the underlying vec0 virtual table index for O(log n) search
        query_bytes = query_embedding.astype(np.float32).tobytes()

        try:
            cursor.execute(
                """
                SELECT node_id, distance
                FROM vec_embeddings
                WHERE embedding MATCH ?
                ORDER BY distance
                LIMIT ?
            """,
                [query_bytes, top_k],
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]
        except Exception:
            # Fallback to Python computation if MATCH not supported
            cursor.execute("SELECT node_id, embedding FROM vec_embeddings")
            results = []
            query_vec = query_embedding.astype(np.float32)

            for row in cursor.fetchall():
                node_id = row[0]
                emb_bytes = row[1]
                stored_emb = np.frombuffer(emb_bytes, dtype=np.float32)
                similarity = float(
                    np.dot(query_vec, stored_emb)
                    / (np.linalg.norm(query_vec) * np.linalg.norm(stored_emb))
                )
                results.append((node_id, 1.0 - similarity))

            results.sort(key=lambda x: x[1])
            return results[:top_k]

    def create_nodes_batch(self, node_type: str, nodes: List[Dict]) -> List[str]:
        """
        Create multiple nodes in batch for better performance.

        Args:
            node_type: Type of node (Concept, Artifact, etc.)
            nodes: List of node property dictionaries

        Returns:
            List of created node IDs
        """
        if not nodes:
            return []

        node_ids = []
        for node in nodes:
            try:
                self.create_node(node_type, node)
                node_ids.append(node.get("id"))
            except Exception:
                # Node might already exist, skip
                pass

        return node_ids

    def create_edges_batch(self, edges: List[Dict]) -> int:
        """
        Create multiple edges in batch.

        Args:
            edges: List of edge dictionaries with keys:
                   src_id, dst_id, edge_type, properties

        Returns:
            Number of edges created
        """
        if not edges:
            return 0

        count = 0
        for edge in edges:
            try:
                self.create_edge(
                    edge["src_id"], edge["dst_id"], edge["edge_type"], edge.get("properties", {})
                )
                count += 1
            except Exception:
                # Edge might already exist, skip
                pass

        return count

    def store_embeddings_batch(self, embeddings: List[Tuple[str, np.ndarray]]) -> None:
        """
        Store multiple embeddings in a single transaction for better performance.

        Args:
            embeddings: List of (node_id, embedding) tuples
        """
        if not embeddings:
            return

        cursor = self.vec_conn.cursor()
        data = [(node_id, emb.astype(np.float32).tobytes()) for node_id, emb in embeddings]

        cursor.executemany(
            "INSERT OR REPLACE INTO vec_embeddings(node_id, embedding) VALUES (?, ?)", data
        )
        self.vec_conn.commit()

    def store_embedding_compressed(
        self,
        node_id: str,
        embedding: np.ndarray,
        compression: Literal["float32", "int8", "binary"] = "int8",
    ) -> None:
        """
        Store embedding with compression for reduced storage size.

        Args:
            node_id: Node ID to associate with embedding
            embedding: Vector to store (numpy array)
            compression: Compression method - "float32" (none), "int8" (4x), or "binary" (32x)
        """
        if compression == "float32":
            # No compression, use regular storage
            self.store_embedding(node_id, embedding)
            return

        cursor = self.vec_conn.cursor()

        # Compress embedding
        compressed_bytes, metadata = EmbeddingCompressor.compress(embedding, compression)

        # Store in a separate table for compressed embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compressed_embeddings (
                node_id TEXT PRIMARY KEY,
                embedding BLOB,
                method TEXT,
                dims INTEGER,
                min_val REAL,
                max_val REAL
            )
        """)

        if compression == "int8":
            cursor.execute(
                """
                INSERT OR REPLACE INTO compressed_embeddings
                (node_id, embedding, method, dims, min_val, max_val)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                [
                    node_id,
                    compressed_bytes,
                    metadata["method"],
                    metadata["dims"],
                    metadata["min"],
                    metadata["max"],
                ],
            )
        else:  # binary
            cursor.execute(
                """
                INSERT OR REPLACE INTO compressed_embeddings
                (node_id, embedding, method, dims)
                VALUES (?, ?, ?, ?)
            """,
                [node_id, compressed_bytes, metadata["method"], metadata["dims"]],
            )

        self.vec_conn.commit()

    def load_embedding_compressed(self, node_id: str) -> Optional[np.ndarray]:
        """
        Load and decompress an embedding.

        Args:
            node_id: Node ID to retrieve

        Returns:
            Decompressed embedding or None if not found
        """
        cursor = self.vec_conn.cursor()

        # First check compressed table
        cursor.execute(
            """
            SELECT embedding, method, dims, min_val, max_val
            FROM compressed_embeddings
            WHERE node_id = ?
        """,
            [node_id],
        )

        row = cursor.fetchone()
        if row:
            compressed, method, dims, min_val, max_val = row
            metadata = {"method": method, "dims": dims, "min": min_val, "max": max_val}
            return EmbeddingCompressor.decompress(compressed, metadata)

        # Fall back to regular vec_embeddings table
        cursor.execute("SELECT embedding FROM vec_embeddings WHERE node_id = ?", [node_id])
        row = cursor.fetchone()
        if row:
            return np.frombuffer(row[0], dtype=np.float32)

        return None
