"""Hippocampus V2 - Pure graph storage (NO embeddings)."""

import kuzu
from pathlib import Path
from typing import Dict, List, Optional
from palace.config.db_config import get_kuzu_config


class Hippocampus:
    """
    Palace Mental V2: Pure graph database interface.

    Changes from V1:
    - REMOVED: SQLite+vec (embeddings storage)
    - REMOVED: All vector operations
    - KEPT: KuzuDB for graph relationships only
    - OPTIMIZED: Minimal storage (~200MB for 10M artifacts)
    """

    def __init__(self, palace_dir: Path):
        """
        Initialize KuzuDB database (NO vector DB).

        Args:
            palace_dir: Directory containing .palace/ data
        """
        self.palace_dir = Path(palace_dir)
        self.palace_dir.mkdir(parents=True, exist_ok=True)

        # Initialize KuzuDB with optimal configuration
        self.db_path = self.palace_dir / "brain.kuzu"
        kuzu_config = get_kuzu_config()
        self.kuzu_db = kuzu.Database(str(self.db_path), **kuzu_config)
        self.kuzu_conn = kuzu.Connection(self.kuzu_db)

    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.kuzu_conn is not None

    def initialize_schema(self) -> None:
        """Create all node and edge types."""
        self._create_kuzu_schema()

    def _create_kuzu_schema(self) -> None:
        """
        Create KuzuDB node and edge types.

        Simplified V2 schema:
        - NO embedding_id in Concept
        - NO vector-related fields
        - Pure graph relationships only
        """
        # Node types
        node_types = [
            """
            CREATE NODE TABLE Concept (
                id STRING,
                name STRING,
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

    def get_node_types(self) -> List[str]:
        """Get all node types in the graph."""
        return ["Concept", "Artifact", "Invariant", "Decision", "Anchor"]

    def close(self) -> None:
        """Close database connection."""
        if self.kuzu_conn:
            self.kuzu_conn.close()

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
        # Build parameterized query
        prop_list = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{node_type} {{{prop_list}}})"
        self.kuzu_conn.execute(query, properties)
        return properties["id"]

    def create_edge(
        self,
        src_id: str,
        dst_id: str,
        edge_type: str,
        properties: Optional[Dict] = None
    ) -> None:
        """
        Create an edge between two nodes.

        Args:
            src_id: Source node ID
            dst_id: Destination node ID
            edge_type: Type of edge (EVOKES, DEPENDS_ON, etc.)
            properties: Optional edge properties
        """
        # Build properties string
        if properties:
            prop_list = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            query = f"""
                MATCH (src), (dst)
                WHERE src.id = $src_id AND dst.id = $dst_id
                CREATE (src)-[r:{edge_type} {{{prop_list}}}]->(dst)
            """
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
                    rows.append(row)

        return rows

    def create_artifact(
        self,
        artifact_id: str,
        path: str,
        content_hash: str,
        language: str,
        ast_fingerprint: str
    ) -> None:
        """
        Create an artifact node.

        Convenience method for artifact creation.

        Args:
            artifact_id: Unique artifact ID
            path: File path
            content_hash: Hash of file content
            language: Programming language
            ast_fingerprint: AST structural hash
        """
        properties = {
            "id": artifact_id,
            "path": path,
            "content_hash": content_hash,
            "language": language,
            "ast_fingerprint": ast_fingerprint,
            "last_modified": None  # TODO: Add timestamp
        }

        self.create_node("Artifact", properties)

    def create_dependency(
        self,
        src_id: str,
        dst_id: str,
        dependency_type: str = "import",
        weight: float = 1.0
    ) -> None:
        """
        Create DEPENDS_ON edge between artifacts.

        Args:
            src_id: Source artifact ID
            dst_id: Dependency artifact ID
            dependency_type: Type of dependency (import, require, etc.)
            weight: Edge weight (default: 1.0)
        """
        properties = {
            "dependency_type": dependency_type,
            "weight": weight
        }

        self.create_edge(src_id, dst_id, "DEPENDS_ON", properties)

    def get_dependencies(self, artifact_id: str) -> List[Dict]:
        """
        Get all dependencies for an artifact.

        Args:
            artifact_id: Artifact to query

        Returns:
            List of dependency artifacts with metadata
        """
        query = """
            MATCH (a:Artifact)-[r:DEPENDS_ON]->(dep:Artifact)
            WHERE a.id = $artifact_id
            RETURN dep.id AS id, dep.path AS path,
                   dep.language AS language, dep.ast_fingerprint AS fingerprint,
                   r.dependency_type AS dep_type, r.weight AS weight
        """

        return self.execute_cypher(query, {"artifact_id": artifact_id})

    def get_dependents(self, artifact_id: str) -> List[Dict]:
        """
        Get all artifacts that depend on this one.

        Args:
            artifact_id: Artifact to query

        Returns:
            List of dependent artifacts
        """
        query = """
            MATCH (a:Artifact)-[r:DEPENDS_ON]->(dep:Artifact)
            WHERE dep.id = $artifact_id
            RETURN a.id AS id, a.path AS path,
                   a.language AS language, a.ast_fingerprint AS fingerprint,
                   r.dependency_type AS dep_type, r.weight AS weight
        """

        return self.execute_cypher(query, {"artifact_id": artifact_id})

    def create_concept(
        self,
        concept_id: str,
        name: str,
        layer: str = "domain",
        stability: float = 0.5
    ) -> None:
        """
        Create a concept node.

        Args:
            concept_id: Unique concept ID
            name: Concept name
            layer: Concept layer (domain, task, etc.)
            stability: Stability score (0-1)
        """
        properties = {
            "id": concept_id,
            "name": name,
            "layer": layer,
            "stability": stability,
            "created_at": None  # TODO: Add timestamp
        }

        self.create_node("Concept", properties)

    def create_evocation(
        self,
        artifact_id: str,
        concept_id: str,
        weight: float = 1.0
    ) -> None:
        """
        Create EVOKES edge from artifact to concept.

        Args:
            artifact_id: Artifact ID
            concept_id: Concept ID
            weight: Association weight (0-1)
        """
        properties = {
            "weight": weight,
            "last_activated": None  # TODO: Add timestamp
        }

        self.create_edge(artifact_id, concept_id, "EVOKES", properties)

    def get_artifacts_by_fingerprint(
        self,
        fingerprint: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find artifacts with matching AST fingerprint.

        Used for clone detection and structural similarity.

        Args:
            fingerprint: AST fingerprint to match
            limit: Max number of results

        Returns:
            List of matching artifacts
        """
        query = """
            MATCH (a:Artifact)
            WHERE a.ast_fingerprint = $fingerprint
            RETURN a.id AS id, a.path AS path, a.language AS language
            LIMIT $limit
        """

        return self.execute_cypher(query, {
            "fingerprint": fingerprint,
            "limit": limit
        })

    def get_statistics(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Dictionary with counts and metadata
        """
        stats = {}

        # Count nodes by type
        for node_type in ["Artifact", "Concept", "Invariant", "Decision", "Anchor"]:
            query = f"MATCH (n:{node_type}) RETURN count(n) AS count"
            result = self.execute_cypher(query, {})
            stats[f"{node_type.lower()}_count"] = (
                int(result[0]["count"]) if result else 0
            )

        # Count edges by type
        for edge_type in ["EVOKES", "DEPENDS_ON", "CONSTRAINS", "PRECEDES", "RELATED_TO"]:
            query = f"MATCH ()-[r:{edge_type}]->() RETURN count(r) AS count"
            result = self.execute_cypher(query, {})
            stats[f"{edge_type.lower()}_count"] = (
                int(result[0]["count"]) if result else 0
            )

        return stats
