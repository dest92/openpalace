# Product Quantization - Research Summary

## Paper Reference
**Title:** Product Quantization for Nearest Neighbor Search
**Authors:** Hervé Jégou, Matthijs Douze, Cordelia Schmid
**Publication:** IEEE Transactions on Pattern Analysis and Machine Intelligence (PAMI), 2011
**DOI:** 10.1109/TPAMI.2011.77
**arXiv:** https://arxiv.org/pdf/1102.3828

## Core Algorithm

### Concept
Product Quantization (PQ) decomposes a high-dimensional space into a Cartesian product of low-dimensional subspaces and quantizes each subspace separately.

**Compression Ratio:**
- Original: 384 dims × 4 bytes = 1,536 bytes per vector
- PQ-8: 8 subvectors × 1 byte = 8 bytes per vector (192x compression)
- PQ-16: 16 subvectors × 1 byte = 16 bytes per vector (96x compression)

### Algorithm Steps

1. **Decomposition:** Split D-dimensional vector into M sub-vectors
   - Dimension per subvector: D* = D/M
   - Example: 384 dims → 8 subvectors of 48 dims

2. **Quantization:** For each sub-space, run K-means clustering
   - K centroids per sub-space (typically K=256)
   - Store only codebook (centroids)

3. **Encoding:** Replace sub-vector with nearest centroid index
   - Encode as 1 byte (when K=256)
   - Storage: M bytes per vector

4. **Distance Computation:** Asymmetric Distance Computation (ADC)
   - Pre-compute query-to-centroid distances
   - Sum distances across sub-spaces
   - No need to decode vectors

### Key Formula

```
Storage per vector = M × log₂(K) bits
For K=256, M=8: 8 × 8 = 64 bits = 8 bytes

Compression ratio = (D × 32) / (M × 8)
For D=384, M=8: 12,288 / 64 = 192x
```

## Production Usage

### Used By
- **Facebook/Meta:** FAISS IVF-PQ index
- **Milvus:** Vector database with PQ support
- **Qdrant:** HNSW + PQ hybrid
- **Billions-scale:** Proven effective at billion+ scale

### Performance Characteristics
- **Recall:** 95%+ for nearest neighbor search
- **Speed:** O(1) lookup with inverted file index
- **Memory:** 64-192x compression vs float32
- **Training:** Requires offline K-means on sample data

## Critical Insights

1. **ADC is key:** Don't use symmetric distances (decode both). Use asymmetric (decode only database).
2. **Inverted File Index:** Combine with IVF for billion-scale
3. **Codebook training:** Use representative sample (100K-1M vectors)
4. **Subvector count:** More subvectors = better quality but slower

## Implementation Considerations

### For Palace Mental
- **Fit on:** 100K sample embeddings from codebase
- **M=8 subvectors:** 32x compression (384 → 8 bytes)
- **K=256 clusters:** 1 byte per subvector
- **Storage:** 10M embeddings × 8 bytes = 80MB + codebooks
- **Speed:** <5ms per query with IVF-PQ

### Advantages
- ✅ Industry standard (proven at scale)
- ✅ High compression with minimal accuracy loss
- ✅ Fast lookup with inverted index
- ✅ Supports updates (add new centroids)

### Limitations
- ❌ Requires training phase
- ❌ Approximate (not exact)
- ❌ Codebook storage overhead
- ❌ Retraining needed for distribution shift

## References
1. Jegou et al., "Product Quantization for Nearest Neighbor Search", PAMI 2011
2. Jegou et al., "Searching in One Billion Vectors", 2011
3. FAISS IVF-PQ implementation: https://github.com/facebookresearch/faiss
