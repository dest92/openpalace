"""Hippocampus - Main interface to graph and vector databases."""

import kuzu
import sqlite3
import sqlite_vec
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


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

        self.vec_conn.commit()

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
        try:
            row = next(result)
            # KuzuDB returns results - row[0] contains the node data
            node_data = row[0]
            # If it's a list, it contains column values
            if isinstance(node_data, list):
                # Get column names from the result
                columns = result.getColumns()
                return {col.getName(): node_data[i] for i, col in enumerate(columns)}
            return node_data
        except StopIteration:
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
        return [dict(row) for row in result]
