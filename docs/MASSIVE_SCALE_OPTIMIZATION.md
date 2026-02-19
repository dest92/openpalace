# Massive-Scale Optimization Strategies

## Problem Statement

Palace Mental was initially designed for small-to-medium projects. For **massive codebases** (millions of files, terabytes of code), the default configuration will lead to:

- **Database bloat**: KuzuDB and SQLite+vec can grow to hundreds of GB
- **Slow queries**: Traversing millions of nodes becomes prohibitive
- **Storage costs**: Embedding storage dominates (1.5KB per artifact × millions)
- **Memory pressure**: Loading entire graphs is impossible

## Strategy Overview

We implement a **multi-layered optimization strategy**:

```
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                     │
├─────────────────────────────────────────────────────────┤
│  Query Optimization  │  Caching  │  Result Limits      │
├─────────────────────────────────────────────────────────┤
│                  COMPRESSION LAYER                      │
│  PCA (3-6x) │ PQ (32x) │ Binary (32x) │ Int8 (4x)      │
├─────────────────────────────────────────────────────────┤
│                   TIERED STORAGE                        │
│  HOT (30d) │ WARM (1y) │ COLD (>1y)                    │
├─────────────────────────────────────────────────────────┤
│                 MAINTENANCE LAYER                       │
│  Pruning │ Compaction │ Archival │ Reindexing          │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Embedding Compression

### 1.1 Product Quantization (PQ) ⭐ **RECOMMENDED FOR MASSIVE SCALE**

**Compression:** 32x (384×4 bytes → 48 bytes)
**Recall:** ~95% for nearest neighbor search
**Use case:** 100K+ embeddings

```python
from palace.core.product_quantization import ProductQuantizer

# Initialize
pq = ProductQuantizer(n_subvectors=8, n_clusters=256)

# Fit on sample of embeddings
pq.fit(sample_embeddings, max_samples=100000)

# Encode
compressed = pq.encode(embedding)  # 48 bytes

# Decode (reconstruction is lossy)
reconstructed = pq.decode(compressed)

# Batch operations
batch_codes = pq.batch_encode(many_embeddings)
```

**When to use:**
- **USE:** Projects with >100K embeddings
- **USE:** When storage is critical
- **AVOID:** When exact similarity is required

---

### 1.2 PCA Dimensionality Reduction

**Compression:** 3-6x (384 dims → 64-128 dims)
**Quality:** Preserves ~95% variance
**Use case:** 10K-100K embeddings

```python
from palace.core.pca_compression import PCACompressor

# Initialize
pca = PCACompressor(n_components=128)

# Fit on representative sample
pca.fit(sample_embeddings)

# Transform
reduced = pca.transform(embedding)  # 128 dims × 4 bytes = 512 bytes

# Reconstruct (lossy)
reconstructed = pca.inverse_transform(reduced)
```

**When to use:**
- **USE:** Medium projects (10K-100K embeddings)
- **USE:** When faster computation is needed
- **AVOID:** Extreme compression needs (use PQ instead)

---

### 1.3 Scalar Quantization (Int8/Binary)

**Compression:** 4-32x
**Implementation:** `palace/core/compression.py`
**Use case:** All projects

```python
from palace.core.compression import EmbeddingCompressor

# Int8 quantization (4x compression)
compressed, metadata = EmbeddingCompressor.compress(embedding, "int8")
# 384 bytes

# Binary quantization (32x compression)
compressed, metadata = EmbeddingCompressor.compress(embedding, "binary")
# 48 bytes
```

**When to use:**
- **Int8:** Default choice, good quality/compression balance
- **Binary:** Maximum compression, acceptable for large-scale retrieval

---

### 1.4 Compression Strategy Guide

| Dataset Size | Compression | Storage per Embedding | Total (100K embeddings) |
|--------------|-------------|----------------------|-------------------------|
| < 10K | None (float32) | 1.5KB | 150MB |
| 10K - 100K | Int8 | 384B | 38MB |
| 100K - 1M | PCA-128 + Int8 | 128B | 12.8MB |
| 1M - 10M | Product Quantization | 48B | 4.8MB |
| > 10M | PQ + Tiered Storage | Variable | < 2MB |

---

## 2. Tiered Storage

### 2.1 Hot/Warm/Cold Architecture

```python
from palace.core.archival import TieredStorage

storage = TieredStorage(palace_dir)

# Record access when querying artifacts
storage.record_access(artifact_id)

# Migrate cold data
stats = storage.migrate_cold_data()
# Returns: {'candidates': 5000, 'migrated': 5000}

# Get storage breakdown
stats = storage.get_storage_stats()
# Returns: {'hot': {...}, 'warm': {...}, 'cold': {...}}
```

**Migration Criteria:**

- **HOT → WARM:** Not accessed in 30 days + access_count < 10
- **WARM → COLD:** Not accessed in 365 days + access_count < 2
- **COLD:** Compressed and archived to separate storage

---

### 2.2 Archival System

```python
from palace.core.archival import DataArchiver

archiver = DataArchiver(palace_dir)

# Archive deleted branches
archiver.archive_artifacts(
    artifact_ids=['art-1', 'art-2', ...],
    reason='deleted_branch'
)

# Archive deprecated modules
archiver.archive_artifacts(
    artifact_ids=deprecated_list,
    reason='deprecated'
)
```

**Archival Triggers:**
- Git branches deleted
- Files not modified in >2 years
- Test files (rarely accessed)
- Generated code

---

## 3. Aggressive Maintenance

### 3.1 Regular Maintenance Cycle

```python
from palace.core.maintenance import DatabaseMaintainer

maintainer = DatabaseMaintainer(palace_dir)

# Run full maintenance (weekly/monthly)
results = maintainer.full_maintenance()

# Results include:
# - kuzu_compaction
# - sqlite_compaction
# - dead_nodes_removed
# - weak_edges_removed
# - orphaned_embeddings_removed
# - space_saved_mb
```

**Recommended Schedule:**
- **Light maintenance:** Daily (prune weak edges)
- **Medium maintenance:** Weekly (VACUUM SQLite, compact Kuzu)
- **Full maintenance:** Monthly (migrate cold, aggressive prune)

---

### 3.2 Manual Pruning Operations

```python
# Prune weak edges (aggressive)
removed = maintainer._prune_weak_edges(aggressive=True)
# Removes edges with weight < 0.3

# Prune orphaned embeddings
removed = maintainer._prune_orphaned_embeddings()
# Removes embeddings with no corresponding nodes
```

**Pruning Thresholds:**
- **Conservative:** weight < 0.1 (default)
- **Moderate:** weight < 0.2
- **Aggressive:** weight < 0.3 (use sparingly)

---

## 4. Query Optimization

### 4.1 Result Limiting

Always limit query results for massive graphs:

```python
# GOOD: Limited results
results = hippocampus.execute_cypher(
    "MATCH (n) RETURN n LIMIT 1000",
    {}
)

# BAD: Unbounded results
results = hippocampus.execute_cypher(
    "MATCH (n) RETURN n",  # Can return millions of nodes!
    {}
)
```

---

### 4.2 Index Usage

Ensure frequently queried properties are indexed:

```python
# In Hippocampus initialization
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_artifact_path
    ON Artifact(path)
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_concept_name
    ON Concept(name)
""")
```

---

### 4.3 Query Batching

For large operations, batch queries:

```python
# GOOD: Batched operations
batch_size = 1000
for i in range(0, len(artifacts), batch_size):
    batch = artifacts[i:i+batch_size]
    process_batch(batch)

# BAD: One-by-one operations
for artifact in artifacts:
    process_one(artifact)  # Very slow!
```

---

## 5. Monitoring and Alerts

### 5.1 Storage Monitoring

```python
stats = maintainer.get_storage_breakdown()

# Alert if database > 10GB
if stats['total_mb'] > 10240:
    send_alert(f"Database size: {stats['total_mb']}MB")

# Alert if one tier dominates
hot_ratio = stats['kuzu_db']['size_mb'] / stats['total_mb']
if hot_ratio > 0.8:
    send_alert("Hot storage is 80% of total. Consider migration.")
```

---

### 5.2 Performance Metrics

Track these metrics:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Query latency | < 100ms | > 1s |
| Database size | < 10GB | > 50GB |
| Compression ratio | > 10x | < 4x |
| Cache hit rate | > 80% | < 50% |

---

## 6. Configuration Examples

### 6.1 Small Project (< 10K files)

```python
# No compression needed
# Default configuration is fine
```

---

### 6.2 Medium Project (10K - 100K files)

```python
# Use Int8 compression
from palace.core.compression import EmbeddingCompressor

compressed, metadata = EmbeddingCompressor.compress(embedding, "int8")

# Monthly maintenance
maintainer.full_maintenance()
```

---

### 6.3 Large Project (100K - 1M files)

```python
# Use PCA + Int8
from palace.core.pca_compression import PCACompressor

pca = PCACompressor(n_components=128)
pca.fit(sample_embeddings)
reduced = pca.transform(embedding)

# Tiered storage
storage = TieredStorage(palace_dir)
storage.record_access(artifact_id)  # Call on every query

# Weekly maintenance
maintainer.full_maintenance()
```

---

### 6.4 Massive Project (> 1M files)

```python
# Use Product Quantization
from palace.core.product_quantization import ProductQuantizer

pq = ProductQuantizer(n_subvectors=8, n_clusters=256)
pq.fit(sample_embeddings, max_samples=100000)
compressed = pq.encode(embedding)

# Aggressive tiered storage
storage.migrate_cold_data()

# Daily light maintenance
maintainer._prune_weak_edges(aggressive=True)

# Weekly full maintenance
maintainer.full_maintenance()

# Archive aggressively
archiver.archive_artifacts(old_artifacts, reason='deprecated')
```

---

## 7. Expected Storage Reductions

| Project Size | Uncompressed | With Optimizations | Reduction |
|--------------|--------------|-------------------|-----------|
| 10K files | ~15GB | ~4GB | 73% |
| 100K files | ~150GB | ~15GB | 90% |
| 1M files | ~1.5TB | ~75GB | 95% |
| 10M files | ~15TB | ~400GB | 97% |

---

## 8. Implementation Checklist

- [ ] Implement embedding compression (PQ/PCA/Int8)
- [ ] Set up tiered storage (hot/warm/cold)
- [ ] Configure maintenance schedule
- [ ] Add storage monitoring
- [ ] Test with production-scale data
- [ ] Document migration strategy
- [ ] Set up alerts for size/performance

---

## 9. References

- Product Quantization: [Jegou et al., 2011](https://lear.inrialpes.fr/pubs/2011/JDS11/jegou_searching_with_quantization.pdf)
- PCA for embeddings: [HuggingFace blog](https://huggingface.co/blog/matrixdimensionality-reduction)
- KuzuDB optimization: [KuzuDB docs](https://kuzudb.com/docs/)
- SQLite optimization: [SQLite optimization guide](https://www.sqlite.org/optoverview.html)
