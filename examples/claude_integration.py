#!/usr/bin/env python3
"""
Ejemplo práctico: Integración de Palace con Claude Code

Este script demuestra cómo usar Palace para obtener contexto
arquitectónico y prepararlo para Claude Code.
"""

from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.api.context import ContextProvider
from palace.formatters.claude import ClaudeFormatter, ContextBundle, Invariant, Artifact, Concept
import subprocess
import sys


def create_context_bundle(provider_context: dict, seed_file: str) -> ContextBundle:
    """Convierte el contexto del provider a un ContextBundle enriquecido."""
    # Convertir invariants
    invariants = []
    for inv in provider_context.get('related_invariants', []):
        invariants.append(Invariant(
            id=inv.get('rule', 'unknown')[:20],
            rule=inv['rule'],
            severity=inv['severity'],
            distance=1,
            affected_file=seed_file,
            check_result=None
        ))

    # Convertir artifacts
    artifacts = []
    for art in provider_context.get('related_artifacts', []):
        # Determinar tipo de relación
        art_str = str(art).lower()
        if 'depends' in art_str:
            relation_type = "depends_on"
        elif 'impact' in art_str:
            relation_type = "depended_by"
        else:
            relation_type = "related"

        artifacts.append(Artifact(
            path=art['path'],
            language="python",
            distance=1,
            relation_type=relation_type
        ))

    # Convertir concepts
    concepts = []
    for conc in provider_context.get('related_concepts', []):
        concepts.append(Concept(
            name=conc['name'],
            activation=conc.get('energy', 0.5),
            evidence=[]
        ))

    # Calcular risk score
    critical_count = len([i for i in invariants if i.severity == "CRITICAL"])
    high_count = len([i for i in invariants if i.severity == "HIGH"])
    risk_score = min(1.0, (critical_count * 0.3 + high_count * 0.15))

    return ContextBundle(
        seed_file=seed_file,
        total_activation=provider_context.get('total_activated', 0),
        risk_score=risk_score,
        invariants=invariants,
        topological_neighbors=artifacts,
        active_concepts=concepts,
        relevant_decisions=[]
    )


def get_context_for_claude(file_path: str, repo_root: str = ".") -> str:
    """
    Obtiene contexto formateado para Claude Code.

    Args:
        file_path: Ruta del archivo a analizar
        repo_root: Raíz del repositorio

    Returns:
        Markdown formateado listo para pegar en Claude
    """
    palace_dir = Path(repo_root) / ".palace"

    if not palace_dir.exists():
        return "❌ Error: Palace no está inicializado. Ejecuta 'palace init' primero."

    with Hippocampus(palace_dir) as hippo:
        # 1. Obtener contexto del provider
        provider = ContextProvider(hippo)
        ctx = provider.get_context_for_file(file_path)

        if "error" in ctx:
            return f"❌ Error: {ctx['error']}"

        # 2. Crear ContextBundle enriquecido
        bundle = create_context_bundle(ctx, file_path)

        # 3. Formatear para Claude
        formatter = ClaudeFormatter()
        markdown = formatter.format(bundle)

        return markdown


def get_context_compact(file_path: str, repo_root: str = ".") -> str:
    """
    Obtiene contexto compacto de una línea.

    Útil para checks rápidos.
    """
    palace_dir = Path(repo_root) / ".palace"

    if not palace_dir.exists():
        return "❌ Palace no inicializado"

    with Hippocampus(palace_dir) as hippo:
        provider = ContextProvider(hippo)
        ctx = provider.get_context_for_file(file_path)

        if "error" in ctx:
            return f"❌ {ctx['error']}"

        bundle = create_context_bundle(ctx, file_path)
        formatter = ClaudeFormatter()
        return formatter.format_compact(bundle)


def copy_to_clipboard(text: str) -> bool:
    """Copia texto al clipboard del sistema."""
    try:
        # Linux
        subprocess.run(['xclip', '-selection', 'clipboard'],
                      input=text.encode(), check=True)
        return True
    except FileNotFoundError:
        try:
            # macOS
            subprocess.run(['pbcopy'], input=text.encode(), check=True)
            return True
        except FileNotFoundError:
            return False


def main():
    """Función principal del ejemplo."""
    if len(sys.argv) < 2:
        print("Uso: python claude_integration.py <archivo> [--compact] [--copy]")
        print()
        print("Ejemplos:")
        print("  python claude_integration.py src/auth/login.py")
        print("  python claude_integration.py src/auth/login.py --compact")
        print("  python claude_integration.py src/auth/login.py --compact --copy")
        sys.exit(1)

    file_path = sys.argv[1]
    compact = '--compact' in sys.argv
    copy_to_cb = '--copy' in sys.argv

    # Obtener contexto
    if compact:
        context = get_context_compact(file_path)
        print("📋 Contexto Compacto:")
        print(context)
    else:
        context = get_context_for_claude(file_path)
        print(context)

    # Copiar al clipboard si se solicita
    if copy_to_cb:
        if copy_to_clipboard(context):
            print("\n✅ Contexto copiado al clipboard")
            print("   ¡Listo para pegar en Claude Code!")
        else:
            print("\n⚠️  No se pudo copiar al clipboard")
            print("   Instala xclip (Linux) o usa pbcopy (Mac)")


if __name__ == "__main__":
    main()
