# MinHash & Locality-Sensitive Hashing - Research Summary

## Primary Paper Reference
**Title:** On the Resemblance and Containment of Documents
**Author:** Andrei Z. Broder
**Institution:** Digital Equipment Corporation (DEC)
**Publication:** Proceedings. Compression and Complexity of Sequences (SEQUENCES 1997)
**Pages:** 21-29
**PDF:** https://www.researchgate.net/publication/221313743_Identifying_and_Filtering_Near-Duplicate_Documents

## Related Key Papers

### Extensions and Improvements
- **Indyk, Motwani (1998):** LSH framework (STOC)
- **Andoni, Indyk (2006):** Near-optimality guarantees
- **Gollapudi, Panigrahy (2006):** Theoretical analysis
- **Thaper (2007):** MinHash for set containment

### Modern Applications
- **Milvus (2024):** LSH for massive LLM deduplication
- **Mash (2014):** Genome containment estimation
- **Web Archives:** Near-duplicate detection at scale

## Core Algorithm

### MinHash Concept
MinHash estimates Jaccard similarity between two sets using minimum hash values.

**Jaccard Similarity:**
```
J(A, B) = |A ∩ B| / |A ∪ B|

Range: [0, 1]
1 = identical sets
0 = disjoint sets
```

**MinHash Principle:**
```
For any permutation π:
min(π(A)) = min(π(B))  ⇔  h(A) = h(B)

Where h is min-wise hash function
Pr[h_min(A) = h_min(B)] = J(A, B)
```

### Algorithm Steps

#### 1. Hashing (Permutation)
For each set S, compute k hash values:
```
h₁(S), h₂(S), ..., hₖ(S)

Where hᵢ(S) = min{hash(x) : x ∈ S} using hashᵢ
```

#### 2. Signature Formation
```
Signature(S) = [h₁(S), h₂(S), ..., hₖ(S)]

Size: k × log₂(universe size) bits
Typical: k=200, 64-bit hashes = 1600 bytes
```

#### 3. Similarity Estimation
```
J_est(A, B) = (1/k) × Σ[hᵢ(A) == hᵢ(B)]

Count matching hash values, divide by k
```

## Banding Technique (CRITICAL)

### The Key Innovation
Instead of comparing all k hashes, divide into bands:

```
k hashes = 200
bands = 20
rows_per_band = 10

Signature: [h₁, h₂, ..., h₂₀₀]
Bands: [(h₁..h₁₀), (h₁₁..h₂₀), ..., (h₁₉₁..h₂₀₀)]

Two candidates match if ANY band matches exactly
```

### Why Banding Matters
**Naive:**
- Store 200 hashes × 8 bytes = 1600 bytes
- Compare all 200 hashes

**With Banding:**
- Store 20 bands × 4 bytes (hash of band) = 80 bytes
- **20x compression**
- Fast candidate filtering

### False Positive Analysis
For threshold t (similarity threshold):
```
Probability band-match = 1 - (1 - sʳ)ᵇ

Where:
s = Jaccard similarity
r = rows per band
b = number of bands

Choose r, b such that:
sʳ ≈ t for thresholding
```

## LSH Framework

### Locality-Sensitive Hashing
Hash functions that preserve locality:
```
Similar items → collide with high probability
Dissimilar items → rarely collide
```

### LSH Families
1. **MinHash LSH:** For Jaccard similarity (sets)
2. **SimHash LSH:** For cosine similarity (vectors)
3. **Cross-Polytope LSH:** For Euclidean distance

### MinHash LSH Properties
```
Collision probability: P[h(A) = h(B)] = J(A, B)

This is LSH because:
- High Jaccard → High collision probability ✓
- Low Jaccard → Low collision probability ✓
```

## Production Usage at Scale

### Milvus 2.6 (2024)
From Milvus blog on MinHash LSH:
> "MinHash LSH offers effective solution for massive LLM dataset deduplication with 2x faster processing and 3-5x cost savings"

**Scale:** Tens of billions of documents

**Configuration:**
- 200 MinHash signatures
- 20 bands of 10 hashes each
- 64-bit hash values
- Threshold: 0.7 similarity

**Performance:**
- Insert: O(1) amortized
- Query: O(#candidates)
- Recall: >95% for near-duplicates

### Google (Historical)
From Broder's original work at AltaVista (1997):
> "Successfully implemented and used for last three years in AltaVista search engine"

**Scale:** Entire web corpus (1997-2000)

### Genomics (Mash)
**Mash Screen:**
- Fast containment estimation
- MinHash for genome sketches
- Billions of base pairs

## Critical Algorithms

### 1. MinHash Signature Generation
```python
def minhash_signature(set_elements, k=200):
    """Generate k MinHash values for a set"""
    signature = []
    for i in range(k):
        # Different seed for each hash function
        min_hash = float('inf')
        for element in set_elements:
            hash_val = hash(f"{element}:{i}")
            min_hash = min(min_hash, hash_val)
        signature.append(min_hash)
    return signature

# For document: set of shingles (n-grams)
shingles = set(doc_shingles(doc, n=5))
sig = minhash_signature(shingles, k=200)
```

### 2. Banding for LSH
```python
def hash_bands(signature, rows=10, bands=20):
    """Convert signature to band hashes"""
    band_hashes = []
    for b in range(bands):
        start = b * rows
        end = start + rows
        band = signature[start:end]
        # Hash the band to single value
        band_hash = hash(tuple(band))
        band_hashes.append(band_hash)
    return band_hashes

# Storage: 20 × 8 bytes = 160 bytes (vs 1600 bytes naive)
# Compression: 10x
```

### 3. Jaccard Estimation
```python
def jaccard_estimate(sig_a, sig_b):
    """Estimate Jaccard from MinHash signatures"""
    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / len(sig_a)

# Unbiased estimator
```

## For Palace Mental

### Application: Code Deduplication

**Problem:** Codebases have massive duplication:
- Boilerplate code
- Generated code
- Copied patterns

**Solution:** MinHash + LSH for deduplication

#### Pipeline
```python
1. Parse code → Extract tokens/shingles
2. Compute MinHash signature (200 hashes)
3. Band into 20 bands of 10 rows
4. Hash bands → LSH buckets
5. Store only unique cluster representatives

Expected dedup: 70-90% for typical codebases
```

#### Storage Calculation
```
Naive: 10M files × 1.5KB = 15GB

With dedup (80%):
- 2M unique signatures × 200 × 8 bytes = 3.2GB
- 8M pointers × 4 bytes = 32MB
- MinHash LSH index: ~500MB

Total: ~3.7GB (still high!)
```

#### With Ultra-Compression
```
Banding: 20 bands × 4 bytes per file = 80 bytes per file

10M × 80 bytes = 800MB (signatures)
Plus: 2M unique × 1.5KB = 3GB (actual embeddings)
Plus: Graph = 200MB

Total: ~4GB (not great)
```

### Better Alternative: MinHash + Bloom Filter

```
1. Deduplicate with MinHash (80% reduction)
2. Store unique items in Bloom filter (for O(1) lookup)
3. Graph for relationships only

Expected: ~500-600MB for 10M files
```

## Performance Characteristics

### Time Complexity
- **Signature computation:** O(n × k) where n = set size, k = signatures
- **Banding:** O(1) per band
- **Query:** O(bands) for candidate filtering + O(matches) for verification

### Space Complexity
- **Per element:** k × log₂(U) bits (U = universe size)
- **With banding:** bands × log₂(U) bits (10-20x less)

### Accuracy
- **Jaccard estimation:** Unbiased
- **False positive rate:** Tunable via threshold
- **Recall:** 95%+ for near-duplicates

## Comparison with Alternatives

| Technique | Storage | Speed | Accuracy | Use Case |
|-----------|---------|-------|----------|----------|
| **MinHash** | High | Fast | Exact Jaccard | Set similarity |
| **MinHash + LSH** | Medium | Very Fast | Approx (tunable) | Near-duplicate detection |
| **SimHash** | Medium | Fast | Cosine similarity | Document similarity |
| **Bloom Filter** | Very Low | O(1) | No false negatives | Membership testing |

## Best Practices

### 1. Shingle Selection
```python
# For code: use token sequences, not characters
# n=5 recommended (5-grams)

def shingle(code, n=5):
    tokens = code.split()
    return {' '.join(tokens[i:i+n])
            for i in range(len(tokens)-n+1)}
```

### 2. Number of Hashes
```python
# k=200 is standard
# More hashes = better precision, slower
# Fewer hashes = faster, more false positives

# Rule of thumb: k = 100-400
```

### 3. Banding Strategy
```python
# Threshold t = 0.7 (70% similarity)
# Want: (1/b)^(1/r) ≈ t

# Solve for r, b:
# b = 20, r = 10 → threshold ≈ 0.7
# b = 10, r = 20 → threshold ≈ 0.8

# Trade-off: More bands = stricter threshold
```

## References
1. Andrei Z. Broder, "On the Resemblance and Containment of Documents", 1997
2. Indyk, Motwani, "Approximate Nearest Neighbors: Towards Removing the Curse of Dimensionality", STOC 1998
3. Andoni, Indyk, "Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor in High Dimensions", 2006
4. Milvus Blog, "MinHash LSH: Secret Weapon for Fighting Duplicates", 2024
5. Broder et al., "Syntactic Clustering of the Web", 1997
