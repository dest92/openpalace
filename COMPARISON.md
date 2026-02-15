# Comparación: palace vs palace2

Análisis comparativo de funcionalidades entre los dos proyectos.

## 📊 Características Únicas de cada Proyecto

### palace (Proyecto Anterior)

| Característica | Descripción | Beneficio |
|---------------|-------------|-----------|
| **AGENTS.md** | Documentación específica para IA | Mejor integración con Claude/OpenCode |
| **CHEATSHEET.md** | Referencia visual rápida | Uso diario más eficiente |
| **formatters/** | Módulo de formateo de salida | Formatos personalizados por herramienta |
| **claude_formatter.py** | Formateador Markdown para Claude | Salida optimizada para Claude Code |
| **QUICKSTART.md** | Guía de 5 minutos | Onboarding rápido |
| **INSTALL.md** | Guía de instalación detallada | Troubleshooting de instalación |
| **setup_palace.py** | Script de instalación automatizado | Instalación con un comando |
| **demo.sh** | Script de demo automatizado | Testing rápido |
| **demo_repo/** | Repositorio de demostración | Testing con código real |
| **test_repo/** | Repositorio de pruebas | Validación de funcionalidades |
| **decisions/** | Directorio para ADRs | Documentación de decisiones arquitectónicas |
| **--compact** | Flag de salida compacta | Contexto en una línea |
| **-o/--output** | Guardar contexto a archivo | Integración con workflows |
| **risk_score** | Métrica de riesgo | Evaluación cuantificada |
| **ContextBundle** | Estructura de contexto enriquecida | Más información estructurada |
| **Emojis visuales** | 🟢🟡🔴 para severidad | Interpretación visual rápida |
| **Activation bars** | Barras de progreso visuales | Representación gráfica de energía |
| **Historical memory** | ADRs en contexto | Decisiones pasadas relevantes |
| **Layer concept** | Conceptos por capas (abstraction/implementation) | Organización semántica |

### palace2 (Proyecto Actual)

| Característica | Descripción | Beneficio |
|---------------|-------------|-----------|
| **Poetry** | Gestión de dependencias moderna | Mejor aislamiento y reproducibilidad |
| **Pydantic v2** | Modelos de datos validados | Type safety y runtime validation |
| **78% test coverage** | Mayor cobertura de tests | Mayor confianza en el código |
| **CLAUDE.md** | Guía para Claude Code | Mejor integración con AI assistants |
| **DEMO.md con datos reales** | Demo con ejecución real | Resultados verificables |
| **mypy strict** | Type checking estricto | Mayor seguridad de tipos |
| **pytest-cov** | Cobertura de tests integrada | Métricas de calidad |
| **pre-commit** | Hooks de pre-commit | Calidad de código automática |
| **black + ruff** | Formateo y linting moderno | Código consistente |
| **Type hints completos** | Hints en todo el código | Mejor IDE support y refactoring |

## 🎯 Funcionalidades Faltantes en palace2

### Prioridad ALTA

1. **ClaudeFormatter** - Formateador de salida con:
   - Emojis visuales (🔴🟠🟡🟢)
   - Barras de activación (██████████)
   - Secciones estructuradas (Invariants, Topology, Concepts, Risk)
   - Modo compacto
   - Output a archivo

2. **ContextBundle mejorado** con:
   - `risk_score` (0.0-1.0)
   - `total_activation`
   - `has_violations()` method
   - `topological_neighbors` con tipos de relación
   - `active_concepts` con evidence
   - `relevant_decisions` (ADRs)

3. **Documentación adicional**:
   - QUICKSTART.md (5 minutos)
   - CHEATSHEET.md (referencia visual)
   - AGENTS.md (para agentes de IA)
   - INSTALL.md (instalación detallada)

4. **CLI features**:
   - `--compact` flag
   - `-o/--output` flag
   - `palace stats` command
   - `palace query <cypher>` command

### Prioridad MEDIA

5. **ADRs (Architecture Decision Records)**:
   - Directorio `.palace/decisions/`
   - Parser de ADRs en markdown
   - Integración en contexto

6. **Scripts de utilidad**:
   - `setup_palace.py` (instalación automatizada)
   - `demo.sh` (demo automatizada)

7. **Mejoras en modelos**:
   - `layer` field en Concept (abstraction/implementation/infrastructure)
   - `distance` field en relaciones
   - `evidence` en Concept
   - `relation_type` en Artifact

### Prioridad BAJA

8. **Demo/repo**:
   - `demo_repo/` con código de ejemplo
   - `test_repo/` para testing

9. **Métricas adicionales**:
   - `hops` (distancia en grafo)
   - `relevance` (para ADRs)

## 🚀 Plan de Implementación

### Fase 1: Core Features (alta prioridad)
- [ ] Agregar `ClaudeFormatter` en `formatters/`
- [ ] Mejorar `ContextBundle` con campos faltantes
- [ ] Agregar flags `--compact` y `-o` al CLI
- [ ] Implementar `palace stats` y `palace query`

### Fase 2: Documentación
- [ ] Crear QUICKSTART.md
- [ ] Crear CHEATSHEET.md
- [ ] Crear AGENTS.md
- [ ] Crear INSTALL.md

### Fase 3: ADRs y utilidades
- [ ] Implementar parser de ADRs
- [ ] Crear directorio `.palace/decisions/`
- [ ] Script `setup_palace.py`

### Fase 4: Mejoras adicionales
- [ ] Agregar `layer` a Concept model
- [ ] Mejoras visuales (emojis, barras)
- [ ] Demo automatizada

## 📈 Comparativa de Salida

### palace (salida actual)
```markdown
## 🏛️ Architectural Context (Palace Mental)
**Seed**: `src/auth.py` | **Activation**: 12.46 | **Risk**: 0.15

### ⚠️ Active Invariants
• [🔴 CRITICAL] `no_eval` → DO NOT USE eval()
• [🟠 HIGH] `sql_injection_risk` → Use parameterization

### 🔗 Local Topology
📥 Depends on: tests/test_auth.py, config/settings.py
📤 Impacts: api/routes.py, middleware/auth.py
🔗 Related: utils/crypto.py

### 🧠 Active Concepts
Security Authentication  ██████████ 1.00  (core concept)
Security Tokens          █████████░ 0.92  (very related)
Pattern Middleware       ████████░░ 0.80  (used pattern)

### 📜 Historical Memory
• [2024-01-10] ADR-001: Use JWT
  ↳ Status: accepted | Reason: Stateless

### 🎯 Risk Assessment
🟡 Risk: Medium (0.15)
⚠️  2 active invariants
💡 Review security rules before modifying
```

### palace2 (salida actual)
```json
{
  "file_path": "src/auth.py",
  "related_artifacts": [...],
  "related_concepts": [...],
  "related_invariants": [...],
  "total_activated": 12
}
```

**Mejora necesaria**: palace2 necesita el formato visual y estructurado de palace.

## 💡 Conclusión

**palace2 tiene mejor base técnica** (Poetry, Pydantic, tests, type hints)

**palace tiene mejor UX y presentación** (emojis, barras, estructuración)

**Recomendación**: Combinar lo mejor de ambos:
- Mantener stack moderno de palace2
- Agregar formateadores visuales de palace
- Implementar flags CLI de palace
- Añadir documentación de palace
- Integrar ADRs
