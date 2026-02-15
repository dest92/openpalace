# 🧠 Palace API - Guía Completa de Integración con AI

## 📖 Índice

1. [Arquitectura de la API](#arquitectura-de-la-api)
2. [Componentes Principales](#componentes-principales)
3. [Flujo de Datos](#flujo-de-datos)
4. [Integración con Claude Code](#integración-con-claude-code)
5. [Integración con Otros Agentes](#integración-con-otros-agentes)
6. [Ejemplos Prácticos](#ejemplos-prácticos)
7. [Buenas Prácticas](#buenas-prácticas)

---

## 🏗️ Arquitectura de la API

### Diagrama de Flujo

```
┌─────────────────┐
│  Usuario/Agente │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  palace.cli.commands                                  │
│  ├── init              # Inicializar DB                │
│  ├── ingest            # Escanear código               │
│  ├── context <file>    # OBTENER CONTEXO ← TÚ          │
│  ├── stats             # Estadísticas                 │
│  └── sleep             # Consolidación                 │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  palace.api.ContextProvider                           │
│  └── get_context_for_file(file_path)                  │
│      Returns: Dict with context                         │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  palace.core.ActivationEngine                          │
│  └── spread(seed_node, max_depth, energy_threshold)   │
│      Returns: Dict[node_id → energy]                   │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  palace.core.Hippocampus                               │
│  ├── execute_cypher(query)  # Grafo                   │
│  ├── get_node(node_id)       # Obtener nodo            │
│  └── similarity_search(vec) # Vectores                │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  palace.formatters.ClaudeFormatter                     │
│  ├── format(bundle)        # Markdown rico            │
│  └── format_compact(bundle) # Una línea               │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Markdown Formateado                                   │
│  ## 🏛️ Architectural Context                          │
│  **Seed**: `src/auth.py` | **Risk**: 0.15               │
│  ### ⚠️ Active Invariants                             │
│  ### 🔗 Local Topology                                │
│  ### 🧠 Active Concepts                                │
│  ### 🎯 Risk Assessment                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes Principales

### 1. ContextProvider (`palace/api/context.py`)

**Propósito:** API principal para obtener contexto arquitectónico

**Método principal:**
```python
def get_context_for_file(
    self,
    file_path: str,
    max_depth: int = 3,
    energy_threshold: float = 0.3
) -> Dict:
    """
    Obtiene contexto arquitectónico para un archivo.

    Args:
        file_path: Ruta del archivo a analizar
        max_depth: Profundidad máxima de navegación (default: 3)
        energy_threshold: Umbral de energía mínimo (default: 0.3)

    Returns:
        Dict con:
        {
            "file_path": str,
            "related_artifacts": [{"path": str, "energy": float}],
            "related_concepts": [{"name": str, "layer": str, "energy": float}],
            "related_invariants": [{"rule": str, "severity": str}],
            "total_activated": int
        }
    """
```

**Proceso interno:**
1. Busca el nodo Artifact correspondiente al archivo
2. Ejecuta spreading activation desde ese nodo
3. Recupera nodos relacionados (artifacts, concepts, invariants)
4. Calcula energías y filtros
5. Retorna contexto estructurado

### 2. ActivationEngine (`palace/core/activation.py`)

**Propósito:** Algoritmo de spreading activation para navegación cognitiva

**Método principal:**
```python
def spread(
    self,
    seed_node_id: str,
    max_depth: int = 3,
    energy_threshold: float = 0.15,
    decay_factor: float = 0.8
) -> Dict[str, float]:
    """
    Ejecuta spreading activation desde un nodo semilla.

    Args:
        seed_node_id: ID del nodo inicial
        max_depth: Máxima distancia en hops
        energy_threshold: Energía mínima para incluir resultados
        decay_factor: Factor de decaimiento por hop (default: 0.8)

    Returns:
        Dict[node_id → activation_energy] ordenado por energía
    """
```

**Algoritmo:**
```
1. Iniciar con nodo semilla a energía 1.0
2. Para cada nivel de profundidad:
   a. Para cada nodo activo:
      - Obtener edges salientes
      - Calcular energía transmitida:
        E_nueva = E_actual × peso_edge × decay × tipo_factor
      - Si E_nueva ≥ threshold:
        → Activar nodo vecino
        → Agregar a cola BFS
3. Retornar nodos activados ordenados por energía
```

**Factores de transmisión por tipo de edge:**
- CONSTRAINS: 1.0 (transmisión completa)
- EVOKES: 0.9 (muy fuerte)
- DEPENDS_ON: 0.7 (fuerte)
- PRECEDES: 0.6 (moderada)
- RELATED_TO: 0.5 (débil)

### 3. Hippocampus (`palace/core/hippocampus.py`)

**Propósito:** Interfaz unificada a bases de datos de grafo y vectores

**Métodos clave:**
```python
class Hippocampus:
    def execute_cypher(self, query: str, params: Dict) -> List[Dict]:
        """Ejecuta query Cypher en KuzuDB"""

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Obtiene un nodo por su ID"""

    def create_node(self, node_type: str, properties: Dict) -> str:
        """Crea un nodo en el grafo"""

    def create_edge(self, src_id, dst_id, edge_type, properties):
        """Crea una edge entre nodos"""

    def store_embedding(self, node_id: str, embedding: np.ndarray):
        """Guarda embedding vectorial"""

    def similarity_search(self, query_embedding, top_k: int):
        """Búsqueda vectorial por similitud semántica"""
```

### 4. ClaudeFormatter (`palace/formatters/claude.py`)

**Propósito:** Formatea contexto en Markdown optimizado para Claude

**Métodos:**
```python
class ClaudeFormatter:
    def format(self, bundle: ContextBundle) -> str:
        """
        Genera Markdown completo y estructurado.

        Incluye:
        - Header con metadata
        - Sección de invariantes (por severidad)
        - Topología local (depends/impacts/related)
        - Conceptos activos (con barras visuales)
        - Memoria histórica (ADRs)
        - Evaluación de riesgo con recomendaciones
        """

    def format_compact(self, bundle: ContextBundle) -> str:
        """
        Versión compacta de una línea.
        Perfecto para prompts cortos.
        """
```

---

## 🌊 Flujo de Datos Completo

### Paso 1: Ingestión (previa al uso)

```python
# 1. Inicializar Palace
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.ingest.pipeline import BigBangPipeline

with Hippocampus(Path('.palace')) as hippo:
    hippo.initialize_schema()

    # 2. Ingestar código
    pipeline = BigBangPipeline(hippo)

    for file_path in Path('.').glob('**/*.py'):
        result = pipeline.ingest_file(file_path)
        # Crea Artifact nodes, DEPENDS_ON edges
        # Detecta invariants, extrae símbolos

# Ahora el grafo tiene:
# - 18 Artifact nodes (archivos)
# - 5 Concept nodes (conceptos)
# - 2 Invariant nodes (reglas)
# - 15 DEPENDS_ON edges (dependencias)
```

### Paso 2: Obtener Contexto (durante uso)

```python
# 1. Crear ContextProvider
from palace.api.context import ContextProvider
from palace.formatters.claude import ClaudeFormatter

with Hippocampus(Path('.palace')) as hippo:
    provider = ContextProvider(hippo)

    # 2. Obtener contexto crudo
    ctx = provider.get_context_for_file('src/auth/login.py')

    # 3. Convertir a ContextBundle enriquecido
    bundle = create_context_bundle(ctx, 'src/auth/login.py')

    # 4. Formatear para AI
    formatter = ClaudeFormatter()
    markdown = formatter.format(bundle)

    # 5. Usar con Claude
    print(markdown)  # → Copiar al clipboard
```

### Paso 3: Claude usa el contexto

```markdown
## 🏛️ Architectural Context (Palace Mental)
**Seed**: `src/auth/login.py` | **Total Activation**: 12.46 | **Risk**: 0.15

### ⚠️ Active Invariants
*No active invariants for this file.*

### 🔗 Local Topology (Cognitive Neighborhood)
**📥 Depends on:**
- `src/database/connection.py` (python) - dist: 1

**📤 Impacts:**
- `src/api/routes.py` (python) - dist: 1

### 🧠 Active Concepts
- **Authentication** `██████████` 1.00
- **Security** `█████████░` 0.92

### 🎯 Risk Assessment
**🟢 Risk Level: Low (0.15)**
*No significant risk factors detected.*
```

**Claude ahora SABE:**
- Qué archivos dependen de este
- Qué archivos usan este código
- Qué conceptos representa
- El nivel de riesgo de modificarlo
- Recomendaciones específicas

---

## 🤖 Integración con Claude Code

### Método 1: Manual (Recomendado para empezar)

**Workflow:**

```bash
# 1. Antes de pedir cambios a Claude
cd /tu/proyecto

# 2. Obtener contexto del archivo que vas a modificar
poetry run palace context src/auth/login.py -o /tmp/context.md

# 3. Copiar al clipboard
cat /tmp/context.md | xclip -selection clipboard

# 4. En Claude Code:
#    - Pegar el contexto
#    - Hacer tu pregunta con contexto arquitectónico completo
```

**Ejemplo de prompt para Claude:**

```
[Pegar contexto del palace]

Quiero agregar rate limiting al sistema de login.

Considerando:
- Risk Score: 0.15 (bajo)
- Dependencies: src/database/connection.py
- Impacts: src/api/routes.py
- Concepts: Authentication, Security

¿Dónde debería implementar el rate limiting
para no romper las dependencias existentes?
```

**Por qué funciona mejor:**
- ✅ Claude conoce el grafo de dependencias
- ✅ Sabe qué archivos se romperían
- ✅ Entiende los conceptos del dominio
- ✅ Ve invariants que no debe violar
- ✅ Recibe recomendaciones de riesgo

### Método 2: Script de ayuda

Crear `get-context.sh`:
```bash
#!/bin/bash
# Script para obtener contexto rápidamente

FILE=$1
OUTPUT=${2:-/tmp/palace_context.md}

cd $(git rev-parse --show-toplevel)
poetry run palace context "$FILE" -o "$OUTPUT"
cat "$OUTPUT" | xclip -selection clipboard
echo "✅ Context copied to clipboard"
echo "📄 Also saved to: $OUTPUT"
```

**Uso:**
```bash
# Hacer ejecutable
chmod +x get-context.sh

# Usar
./get-context.sh src/auth/login.py

# Resultado:
# ✅ Context copied to clipboard
# 📄 Also saved to: /tmp/palace_context.md
```

### Método 3: Integración VS Code

Crear `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Palace: Get Context (Full)",
      "type": "shell",
      "command": "poetry run palace context ${file}",
      "problemMatcher": []
    },
    {
      "label": "Palace: Get Context (Compact)",
      "type": "shell",
      "command": "poetry run palace context ${file} --compact",
      "problemMatcher": []
    },
    {
      "label": "Palace: Get Context to Clipboard",
      "type": "shell",
      "command": "poetry run palace context ${file} -o /tmp/ctx.md | cat /tmp/ctx.md | xclip -selection clipboard",
      "problemMatcher": []
    }
  ]
}
```

**Atajo de teclado:**
```json
// keybindings.json
{
  "key": "ctrl+shift+p",
  "command": "workbench.action.tasks.runTask",
  "args": "Palace: Get Context to Clipboard"
}
```

### Método 4: Extensión de VS Code (Avanzado)

Crear extensión que automáticamente muestra contexto:

`extension.ts`:
```typescript
import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    // Command to get context
    let disposable = vscode.commands.registerCommand(
        'palace.getContext',
        (fileUri) => {
            const filePath = fileUri.fsPath;

            exec(`poetry run palace context "${filePath}" --compact`,
              (error, stdout, stderr) => {
                if (error) {
                    vscode.window.showErrorMessage(`Error: ${stderr}`);
                } else {
                    // Show in output channel
                    const channel = vscode.window.createOutputChannel('Palace Context');
                    channel.show();
                    channel.appendLine(stdout);
                }
              });
        }
    );

    // Add status bar button
    let statusBarItem = vscode.window.createStatusBarItem(
        'palace.context',
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '🧠 Get Context';
    statusBarItem.command = 'palace.getContext';
    statusBarItem.show();

    context.subscriptions.push(disposable);
}
```

---

## 🤖 Integración con Otros Agentes de IA

### Cursor AI

**Opción 1: Usar el `.cursorrules`:**

Crear `.cursorrules`:
```
# Palace Context Rule
Before making any code changes, ALWAYS run:
poetry run palace context ${file} --compact

Consider the context in your response:
- Risk level
- Active invariants
- Dependencies
- Related concepts

Do not violate detected invariants.
```

**Opción 2: Script automático:**

Crear `.cursor/run-before-generation.sh`:
```bash
#!/bin/bash
# Script que corre antes de cada generación de Cursor

FILE="$1"
poetry run palace context "$FILE" --compact > /tmp/cursor_context.txt
echo "Context saved to /tmp/cursor_context.txt"
```

### Continue.dev / Continue

Configurar `~/.continue/config.toml`:
```toml
[context]
# Palace context provider
command = "poetry run palace context {file} --compact"
enabled = true

# Or with custom script
[context]
command = "./get-context.sh {file}"
enabled = true
```

### Aider (CLI AI)

Crear alias en shell:
```bash
# Add to ~/.bashrc or ~/.zshrc
alias aider-palace='aider --msg "$(poetry run palace context $1 --compact)"'
```

Uso:
```bash
aider-palace src/auth/login.py
# automatically gets context before aider starts
```

### GitHub Copilot Workspace

Crear `github/workspace.json`:
```json
{
  "extensions": {
    "github.copilot.chat": {
      "context": {
        "command": "poetry run palace context ${file} --compact"
      }
    }
  }
}
```

### Custom AI Agent (Python)

```python
"""
Ejemplo: Agente AI personalizado que usa Palace
"""
from typing import Dict, Any
from pathlib import Path
from palace.core.hippocampus import Hippocampus
from palace.api.context import ContextProvider
from palace.formatters.claude import ClaudeFormatter, ContextBundle


class AIAgent:
    """Agente de IA con contexto arquitectónico."""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.palace_dir = self.repo_root / ".palace"
        self.hippocampus = None
        self.provider = None
        self.formatter = None

    def __enter__(self):
        self.hippocampus = Hippocampus(self.palace_dir)
        self.hippocampus.__enter__()
        self.provider = ContextProvider(self.hippocampus)
        self.formatter = ClaudeFormatter()
        return self

    def __exit__(self, *args):
        if self.hippocampus:
            self.hippocampus.__exit__(*args)

    def modify_file(self, file_path: str, user_request: str) -> Dict[str, Any]:
        """
        Modifica un archivo considerando contexto arquitectónico.

        Args:
            file_path: Archivo a modificar
            user_request: Lo que el usuario quiere hacer

        Returns:
            Dict con el plan y contexto
        """
        # 1. Obtener contexto
        ctx = self.provider.get_context_for_file(file_path)
        bundle = self._create_bundle(ctx, file_path)

        # 2. Generar prompt enriquecido
        prompt = self._generate_prompt(bundle, user_request)

        # 3. Planificación
        plan = self._create_plan(bundle, user_request)

        return {
            "context": bundle,
            "prompt": prompt,
            "plan": plan
        }

    def _create_bundle(self, ctx: dict, file_path: str) -> ContextBundle:
        """Convierte contexto del provider a ContextBundle."""
        # ... implementación de conversión
        pass

    def _generate_prompt(self, bundle: ContextBundle, user_request: str) -> str:
        """Genera prompt para AI con contexto completo."""
        markdown_context = self.formatter.format(bundle)

        return f"""
{markdown_context}

## User Request
{user_request}

## Instructions
1. Consider all invariants listed above
2. Check all dependencies before modifying
3. Ensure changes don't break files that depend on this one
4. Follow the risk assessment recommendations
"""

    def _create_plan(self, bundle: ContextBundle, user_request: str) -> Dict:
        """Crea plan basado en riesgo y dependencias."""
        plan = {
            "steps": [],
            "risks": [],
            "recommendations": []
        }

        # Analizar riesgo
        if bundle.risk_score > 0.5:
            plan["risks"].append("High risk - extensive testing required")
            plan["steps"].append("Write comprehensive tests first")

        # Analizar dependencias
        impacts = [n for n in bundle.topological_neighbors
                   if n.relation_type == "depended_by"]
        if impacts:
            plan["recommendations"].append(
                f"Test {len(impacts)} dependent files after changes"
            )

        return plan


# Uso del agente
with AIAgent("/tu/proyecto") as agent:
    result = agent.modify_file(
        "src/auth/login.py",
        "Add rate limiting to prevent brute force attacks"
    )

    print(result["prompt"])
    # Enviar a tu LLM favorito
```

---

## 📚 Ejemplos Prácticos

### Ejemplo 1: Refactorización Segura

```python
from palace.api.context import ContextProvider
from palace.formatters.claude import ClaudeFormatter
from pathlib import Path

# 1. Setup
with Hippocampus(Path(".palace")) as hippo:
    provider = ContextProvider(hippo)

    # 2. Analizar antes de cambiar
    ctx = provider.get_context_for_file("src/database/connection.py")
    bundle = create_context_bundle(ctx, "src/database/connection.py")

    # 3. Verificar qué se rompería
    formatter = ClaudeFormatter()
    print("=== ANTES DE CAMBIAR ===")
    print(formatter.format(bundle))
    print("\n=== IMPACTO ===")
    print("Archivos que se romperían:")
    for art in bundle.topological_neighbors:
        if art.relation_type == "depended_by":
            print(f"  - {art.path}")

    # 4. Decisión informada
    if bundle.risk_score > 0.5:
        print("\n⚠️  ALTO RIESGO - Crear tests primero")
    else:
        print("\n✅ RIESGO BAJO - Proceder con refactor")
```

### Ejemplo 2: Code Review Automatizado

```python
def review_pr(changed_files: list[str]) -> dict:
    """
    Revisa Pull Request considerando contexto arquitectónico.
    """
    results = {}

    for file_path in changed_files:
        # Obtener contexto
        ctx = provider.get_context_for_file(file_path)
        bundle = create_context_bundle(ctx, file_path)

        # Revisión
        review = {
            "file": file_path,
            "risk_level": "HIGH" if bundle.risk_score > 0.6 else "MEDIUM" if bundle.risk_score > 0.3 else "LOW",
            "invariants": bundle.invariants,
            "impacts": [n.path for n in bundle.topological_neighbors if n.relation_type == "depended_by"],
            "recommendations": []
        }

        # Recomendaciones
        critical = [i for i in bundle.invariants if i.severity == "CRITICAL"]
        if critical:
            review["recommendations"].append("CRITICAL invariants must be addressed")

        if len(review["impacts"]) > 3:
            review["recommendations"].append("High connectivity - consider integration tests")

        results[file_path] = review

    return results


# Uso
changed_files = ["src/auth/login.py", "src/database/connection.py"]
review = review_pr(changed_files)

for file, review_item in review.items():
    print(f"\n📄 {file}")
    print(f"   Risk: {review_item['risk_level']}")
    print(f"   Impacts: {len(review_item['impacts'])} files")
    if review_item['recommendations']:
        for rec in review_item['recommendations']:
            print(f"   ⚠️  {rec}")
```

### Ejemplo 3: Chatbot con Contexto

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from palace.api.context import ContextProvider

class ContextAwareChatbot:
    """Chatbot que considera contexto arquitectónico."""

    def __init__(self, model_name: str, repo_root: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

        # Palace setup
        self.palace_dir = Path(repo_root) / ".palace"

    def chat(self, user_message: str, current_file: str) -> str:
        """Procesa mensaje del usuario con contexto."""

        # 1. Obtener contexto del archivo actual
        with Hippocampus(self.palace_dir) as hippo:
            provider = ContextProvider(hippo)
            ctx = provider.get_context_for_file(current_file)
            bundle = create_context_bundle(ctx, current_file)

            formatter = ClaudeFormatter()
            context_str = formatter.format_compact(bundle)

        # 2. Crear prompt con contexto
        augmented_prompt = f"""
You are a coding assistant with architectural awareness.

{context_str}

Current file: {current_file}

User request: {user_message}

Considering the architectural context above, provide a helpful response that:
- Respects all invariants
- Considers dependencies
- Follows established patterns
"""

        # 3. Generar respuesta
        inputs = self.tokenizer(augmented_prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_length=500)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return response
```

---

## ✅ Buenas Prácticas

### Para Usuarios de Palace

1. **SIEMPRE obtener contexto antes de modificar**
   ```bash
   # Habituación
   palace context file.py -o /tmp/ctx.md
   cat /tmp/ctx.md | xclip
   # Pegar en Claude
   ```

2. **Verificar riesgo antes de cambios grandes**
   ```python
   ctx = provider.get_context_for_file("critical_module.py")
   if ctx["risk_score"] > 0.6:
       print("⚠️  HIGH RISK - Create comprehensive tests first")
   ```

3. **Considerar todas las dependencias**
   ```python
   # Siempre revisar 'impacts'
   impacts = [a for a in bundle.topological_neighbors
              if a.relation_type == "depended_by"]
   if len(impacts) > 0:
       print(f"⚠️  {len(impacts)} files depend on this")
   ```

4. **Usar modo compacto para checks rápidos**
   ```bash
   palace context file.py --compact
   # Output: 🏛️ Context: `file.py` (risk: 0.15) | 🧠 Concepts: Auth, Security
   ```

### Para Desarrolladores de Integraciones

1. **Manejar errores gracefully**
   ```python
   try:
       ctx = provider.get_context_for_file(file_path)
   except FileNotFoundError:
       print(f"⚠️  File {file_path} not in knowledge graph")
       print("   Run 'palace ingest' first")
       return None
   ```

2. **Cache para performance**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def get_cached_context(file_path: str):
       """Cache context to avoid repeated queries."""
       with Hippocampus(palace_dir) as hippo:
           provider = ContextProvider(hippo)
           return provider.get_context_for_file(file_path)
   ```

3. **Validar antes de usar**
   ```python
   def validate_bundle(bundle: ContextBundle) -> bool:
       """Valida que el bundle tenga datos necesarios."""
       if not bundle.related_artifacts:
           print("⚠️  No artifacts found - file may not be ingested")
           return False
       return True
   ```

---

## 🎯 Conclusión

Palace se integra perfectamente con Claude Code y otros agentes de IA porque:

1. **API Simple**: Un solo método (`get_context_for_file`)
2. **Salida Estructurada**: JSON fácil de parsear
3. **Markdown Optimizado**: Listo para pegar en Claude
4. **Metadatos Ricos**: Riesgo, dependencias, invariantes
5. **Flexible**: Se puede adaptar a cualquier flujo de trabajo

**Proximo paso:** ¡Probarlo tú mismo!

```bash
cd /tu/proyecto
poetry install
poetry run palace init
poetry run palace ingest
poetry run palace context src/tu_archivo.py
```

¿Quieres que cree una extensión de VS Code específica para Palace? 🚀
