"""CLI commands for Palacio Mental."""

import typer
from pathlib import Path
from typing import Optional
from palace.core.hippocampus import Hippocampus
from palace.ingest.pipeline import BigBangPipeline
from palace.api.context import ContextProvider
from palace.formatters.claude import ClaudeFormatter, ContextBundle, Invariant, Artifact, Concept, Decision
from palace.shared.exceptions import PalaceNotInitializedError

app = typer.Typer(help="Palacio Mental - Cognitive memory system for code")


@app.command()
def init(
    repo_root: Path = typer.Argument(".", help="Repository root directory")
):
    """Initialize Palace for a repository."""
    palace_dir = repo_root / ".palace"
    palace_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Initialized Palace at {palace_dir}")


@app.command()
def ingest(
    repo_root: Path = typer.Argument(".", help="Repository root directory"),
    file_pattern: str = typer.Option("**/*.py", help="File pattern to ingest")
):
    """Ingest code files into the knowledge graph."""
    palace_dir = repo_root / ".palace"

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    with Hippocampus(palace_dir) as hippo:
        hippo.initialize_schema()

        # Create pipeline (without concept extractor for speed)
        pipeline = BigBangPipeline(hippo, concept_extractor=None)

        # Find files
        files = list(repo_root.glob(file_pattern))

        typer.echo(f"Found {len(files)} files")

        # Ingest files
        for file_path in files:
            try:
                result = pipeline.ingest_file(file_path)
                if result["status"] == "success":
                    typer.echo(f"✓ {file_path}: {result['symbols']} symbols")
                elif result["status"] == "skipped":
                    typer.echo(f"- {file_path}: skipped")
            except Exception as e:
                typer.echo(f"✗ {file_path}: {e}")

    typer.echo("Ingestion complete!")


@app.command()
def context(
    file_path: Path = typer.Argument(..., help="File to get context for"),
    repo_root: Path = typer.Option(".", help="Repository root directory"),
    compact: bool = typer.Option(False, "-c", "--compact", help="Compact output (one line)"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Save context to file")
):
    """Get contextual information for a file."""
    palace_dir = repo_root / ".palace"

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    with Hippocampus(palace_dir) as hippo:
        provider = ContextProvider(hippo)
        ctx = provider.get_context_for_file(str(file_path))

        if "error" in ctx:
            typer.echo(f"Error: {ctx['error']}")
            return

        # Create enriched ContextBundle
        bundle = _create_context_bundle(ctx, str(file_path))

        # Format output
        formatter = ClaudeFormatter()

        if compact:
            formatted = formatter.format_compact(bundle)
        else:
            formatted = formatter.format(bundle)

        # Output
        if output:
            output.write_text(formatted)
            typer.echo(f"Context saved to {output}")
        else:
            typer.echo(formatted)


@app.command()
def sleep(
    repo_root: Path = typer.Option(".", help="Repository root directory")
):
    """Run sleep cycle for consolidation."""
    palace_dir = repo_root / ".palace"

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    with Hippocampus(palace_dir) as hippo:
        from palace.core.sleep import SleepEngine

        engine = SleepEngine(hippo)
        report = engine.sleep_cycle()

        typer.echo(f"Sleep cycle complete!")
        typer.echo(f"Nodes: {report.nodes_count}")
        typer.echo(f"Edges: {report.edges_count}")
        typer.echo(f"Edges decayed: {report.edges_decayed}")
        typer.echo(f"Edges pruned: {report.edges_pruned}")
        typer.echo(f"Duration: {report.total_duration_ms:.2f}ms")


@app.command()
def stats(
    repo_root: Path = typer.Option(".", help="Repository root directory")
):
    """Show brain statistics."""
    palace_dir = repo_root / ".palace"

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    with Hippocampus(palace_dir) as hippo:
        # Count nodes
        result = hippo.execute_cypher("MATCH (n) RETURN count(n) as count")
        total_nodes = result[0]['count'] if result else 0

        # Count edges
        result = hippo.execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
        total_edges = result[0]['count'] if result else 0

        # Count by node type
        node_types = ["Concept", "Artifact", "Invariant", "Decision", "Anchor"]
        typer.echo("📊 Palace Brain Statistics")
        typer.echo("=" * 40)
        typer.echo(f"Total Nodes: {total_nodes}")
        typer.echo(f"Total Edges: {total_edges}")
        typer.echo("")

        typer.echo("Nodes by Type:")
        for node_type in node_types:
            result = hippo.execute_cypher(f"MATCH (n:{node_type}) RETURN count(n) as count")
            count = result[0]['count'] if result else 0
            if count > 0:
                typer.echo(f"  {node_type}: {count}")

        typer.echo("")

        # Count by edge type
        edge_types = ["EVOKES", "DEPENDS_ON", "CONSTRAINS", "PRECEDES", "RELATED_TO"]
        typer.echo("Edges by Type:")
        for edge_type in edge_types:
            result = hippo.execute_cypher(f"MATCH ()-[r:{edge_type}]->() RETURN count(r) as count")
            count = result[0]['count'] if result else 0
            if count > 0:
                typer.echo(f"  {edge_type}: {count}")


@app.command()
def query(
    cypher: str = typer.Argument(..., help="Cypher query to execute"),
    repo_root: Path = typer.Option(".", help="Repository root directory")
):
    """Execute a raw Cypher query."""
    palace_dir = repo_root / ".palace"

    if not palace_dir.exists():
        raise PalaceNotInitializedError()

    with Hippocampus(palace_dir) as hippo:
        results = hippo.execute_cypher(cypher, {})

        if not results:
            typer.echo("No results")
            return

        # Print results as table
        if results:
            headers = results[0].keys()
            typer.echo(" | ".join(headers))
            typer.echo("-" * (len(" | ".join(headers))))

            for row in results:
                typer.echo(" | ".join(str(row.get(h, "")) for h in headers))


def _create_context_bundle(ctx: dict, seed_file: str) -> ContextBundle:
    """Create enriched ContextBundle from provider context."""
    # Convert invariants
    invariants = []
    for inv in ctx.get('related_invariants', []):
        invariants.append(Invariant(
            id=inv.get('rule', 'unknown')[:20],
            rule=inv['rule'],
            severity=inv['severity'],
            distance=1,
            affected_file=seed_file,
            check_result=None
        ))

    # Convert artifacts
    artifacts = []
    for art in ctx.get('related_artifacts', []):
        relation_type = "related"
        if 'depends' in str(art).lower():
            relation_type = "depends_on"
        artifacts.append(Artifact(
            path=art['path'],
            language="python",
            distance=1,
            relation_type=relation_type
        ))

    # Convert concepts
    concepts = []
    for conc in ctx.get('related_concepts', []):
        concepts.append(Concept(
            name=conc['name'],
            activation=conc.get('energy', 0.5),
            evidence=[]
        ))

    return ContextBundle(
        seed_file=seed_file,
        total_activation=ctx.get('total_activated', 0),
        risk_score=len([i for i in invariants if i.severity in ["CRITICAL", "HIGH"]]) * 0.2,
        invariants=invariants,
        topological_neighbors=artifacts,
        active_concepts=concepts,
        relevant_decisions=[]
    )


if __name__ == "__main__":
    app()
