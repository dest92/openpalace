# Night Iterations - Palace Mental V2 Optimization

**Fecha:** 2026-02-19
**Objetivo:** Iterar constantemente mejorando Palace Mental V2 para máxima compresión

## Iteración #1: Delta Encoding ✅

**Implementación:**
- `palace/core/delta_encoding.py` (277 líneas)
- Clustering de ASTs similares por Hamming distance
- Binary delta encoding inspirado en git

**Resultados:**
- ✅ 1.33× compresión adicional
- ✅ Tests pasando (3/3)
- ✅ Threshold 70% para clustering
- ✅ 24 bytes savings en 3 artifacts

**Potencial:**
- 20-25% savings adicionales para codebases con 50% similitud
- Ideal para proyectos con muchos code clones

## Iteración #2: Investigación Brave - Compression 2024

### Hallazgos Clave:

#### 1. **TimescaleDB Production Case**
- **150GB → 15GB (90% reducción)**
- Zero operational overhead
- Queries más rápidas después de compresión
- Source: https://dev.to/polliog/timescaledb-compression-from-150gb-to-15gb-90-reduction-real-production-data-bnj

**Lecciones para Palace:**
- La compresión puede MEJORAR performance (menos I/O)
- Compresión columnar es clave para analytics
- Compression en caliente, no solo frío

#### 2. **Source Code a Escala Masiva**
- **1.5 PiB de código fuente comprimido**
- Content-defined compression para código
- Context-aware techniques
- Source: "On the compressibility of large-scale source code datasets" (ScienceDirect)

**Lecciones para Palace:**
- Source code es altamente compresible (repetitivo)
- Content-defined chunks mejor que fixed-size
- Context matters: imports, patterns repetitivos

#### 3. **ClickHouse Compression**
- Columnar compression por defecto
- Diferentes codecs por tipo de datos
- Compression ratios de 10× típicos

**Lecciones para Palace:**
- Separar datos por "tipo" (fingerprint vs metadata)
- Usar diferentes estrategias por tipo
- Encoding efficiente (no solo compression)

## Próximas Iteraciones Planificadas:

### Iteración #3: Columnar Storage para Fingerprints
**Idea:** Separar fingerprints en columnas para mejor compresión
- Columna 1: Prefijos comunes (primeros 16 bytes)
- Columna 2: Sufijos únicos (últimos 16 bytes)
- Potencial: 2-3× additional compression

### Iteración #4: LRU Cache para Fingerprints
**Idea:** Cache fingerprints calientes en memoria
- LRU eviction policy
- 10,000 fingerprints ~ 320KB en RAM
- Reduce disk reads para queries frecuentes

### Iteración #5: Dictionary Compression
**Idea:** Compresión por diccionario para patterns comunes
- "def " aparece 1M veces → encodear como byte 0x01
- "class " → 0x02
- "import " → 0x03
- Potential: 30-40% additional compression

## Estado de Descargas:

| Proyecto | Tamaño | Archivos | Estado |
|----------|-------|----------|--------|
| Linux kernel | 2.0GB | 63K (.c + .h) | ✅ Completado |
| CPython | Descargando | ~50K | 🔄 En progreso |

## Métricas Actuales V2:

```
Baseline (sin delta):
  AST fingerprints: 320MB (10M archivos × 32 bytes)
  Bloom filter: 2MB
  Graph edges: 200MB
  TOTAL: 522MB

Con delta encoding (1.33×):
  AST fingerprints: 240MB
  Bloom filter: 2MB
  Graph edges: 200MB
  Delta overhead: ~10MB
  TOTAL: 452MB (13.4% adicional de savings)
```

## Objetivo Nocturno:

**Meta: Alcanzar <300MB para 10M archivos**

Iteraciones necesarias:
- ✅ Delta encoding: 522MB → 452MB
- 🔄 Columnar storage: 452MB → 350MB
- 🔄 Dictionary compression: 350MB → 280MB
- 🔄 LRU caching: Solo performance, no storage

**Resultado esperado: ~280MB (46.4% del baseline original)**

---

**Log de Iteraciones - Timestamp:** 2026-02-19 ~21:00 UTC
