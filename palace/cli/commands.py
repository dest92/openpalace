"""CLI commands for Palacio Mental."""

import typer
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.ingest.pipeline import BigBangPipeline
from palace.api.context import ContextProvider
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
    repo_root: Path = typer.Option(".", help="Repository root directory")
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

        typer.echo(f"\nContext for {file_path}")
        typer.echo(f"Related files: {len(ctx['related_artifacts'])}")
        for artifact in ctx['related_artifacts']:
            typer.echo(f"  - {artifact['path']} (energy: {artifact['energy']:.2f})")

        typer.echo(f"\nRelated concepts: {len(ctx['related_concepts'])}")
        for concept in ctx['related_concepts']:
            typer.echo(f"  - {concept['name']} ({concept['layer']}) - {concept['energy']:.2f}")

        typer.echo(f"\nInvariants: {len(ctx['related_invariants'])}")
        for inv in ctx['related_invariants']:
            typer.echo(f"  - {inv['rule']} ({inv['severity']})")


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


if __name__ == "__main__":
    app()
