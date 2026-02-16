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
            """
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
            """
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

    def create_edge(
        self,
        src_id: str,
        dst_id: str,
        edge_type: str,
        properties: Dict
    ) -> None:
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
            params = {
                "src_id": src_id,
                "dst_id": dst_id,
                **properties
            }
        else:
            query = f"""
                MATCH (src), (dst)
                WHERE src.id = $src_id AND dst.id = $dst_id
                CREATE (src)-[r:{edge_type}]->(dst)
            """
            params = {
                "src_id": src_id,
                "dst_id": dst_id
            }
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
            [node_id, embedding.tobytes()]
        )
        self.vec_conn.commit()

    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find similar embeddings by cosine similarity.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of (node_id, distance) tuples
        """
        # For now, just retrieve all embeddings and compute similarity in Python
        # TODO: Use proper sqlite-vec similarity search
        cursor = self.vec_conn.cursor()
        cursor.execute("SELECT node_id, embedding FROM vec_embeddings LIMIT ?", [top_k])

        results = []
        query_vec = query_embedding.astype(np.float32)

        for row in cursor.fetchall():
            node_id = row[0]
            emb_bytes = row[1]
            # Convert bytes back to numpy array
            stored_emb = np.frombuffer(emb_bytes, dtype=np.float32)
            # Compute cosine similarity (1 - cosine distance)
            similarity = float(np.dot(query_vec, stored_emb) / (np.linalg.norm(query_vec) * np.linalg.norm(stored_emb)))
            results.append((node_id, 1.0 - similarity))  # Return distance

        return results
