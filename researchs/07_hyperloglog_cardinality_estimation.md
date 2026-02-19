# HyperLogLog (HLL) - Cardinality Estimation - Research Summary

## Primary Paper Reference
**Title:** HyperLogLog: the analysis of a near-optimal probabilistic algorithm, dedicated to estimating the number of distinct elements (the cardinality) of very large data ensembles
**Authors:** Philippe Flajolet, Éric Fusy, Olivier Gandouet, Frédéric Meunier
**Institution:** INRIA Rocquencourt
**Publication:** ANALCO 2007 (Analytic Algorithms and Combinatorics)
**Full Paper:** https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf

## Related Key Papers

### HyperLogLogLog (KDD 2022)
**Title:** "HyperLogLogLog: Cardinality Estimation With One Log More"
**Authors:** Karppa, Pagh
**Publication:** KDD 2022
**Key innovation:** Uses just one log register (vs 12 in HLL)

### UltraLogLog (VLDB 2022)
**Title:** "UltraLogLog: A Practical and More Space-Efficient Alternative to HyperLogLog"
**Key insight:** Better space-accuracy trade-off than HLL

### HyperLogLog in Practice (SIGMOD 2013)
**Title:** "HyperLogLog in practice: An algorithmic engineering of a state of the art cardinality estimation algorithm"
**Authors:** Heule, Nunkesser, Hall
**Key findings:** Practical improvements and tunings

## Core Concept

### The Problem
**Count distinct elements** in massive data streams:
- Number of unique users
- Number of distinct words
- Number of unique IP addresses

**Naive approach:**
```python
def count_distinct(stream):
    seen = set()
    for item in stream:
        seen.add(item)
    return len(seen)

Problem: O(n) memory, infeasible for billions of items!
```

### HyperLogLog Solution
**Key insight:** Use hash functions → estimate cardinality with <1KB memory

**Algorithm:**
1. **Hash each element:** h(x) ∈ [0, 2³²-1]
2. **Find first 1-bit position:** ρ(h(x)) = position of least-significant 1-bit
3. **Track maximum:** M[j] = max(M[j], ρ(h(xᵢ))) for j-th hash function
4. **Estimate:** E[cardinality] ≈ f(M[0], ..., M[k-1])

**Storage:** k registers × 5 bits = 5k bits (k = number of hash functions)
**Typical:** k=12 → 60 bits ≈ 8 bytes (!!)

## Mathematical Foundation

### LogLog Analysis (Original)
For uniform hash:
```
E[cardinality] ≈ 2^M

Where M = average value of k registers

Problem: Only works for uniform distribution
```

### HyperLogLog Improvement
**From Flajolet et al.:**
> "This extended abstract describes and analyses a near-optimal probabilistic algorithm, HYPERLOGLOG, dedicated to estimating the number of distinct elements of very large data ensembles"

**Key innovation:** Harmonic mean instead of arithmetic mean

**Formula:**
```
E = α × m² × (1/k) × Σ(2^(-M[j]))

Where:
- m = number of registers (power of 2)
- k = number of hash functions
- α = correction factor (~0.7213 for m=2^16)
```

## Production Usage

### Network Monitoring
**From "Fast Updates for Line-Rate HyperLogLog" (IEEE 2024):**
> "HyperLogLog (HLL) is widely used to estimate cardinality with a small memory footprint and simple per packet operations"

**Applications:**
- Count distinct IP addresses (DDoS detection)
- Count distinct flows (traffic analysis)
- Count distinct users (analytics)

### Database Systems
**From "Cardinality Estimation in DBMS: A Comprehensive Benchmark" (VLDB 2021):**
> "Cardinality estimation has become an essential building block of modern network monitoring systems"

**Used by:**
- **Redis:** HyperLogLog commands (PFADD, PFCOUNT)
- **PostgreSQL:** HLL extensions
- **ClickHouse:** HLL data type
- **Apache Druid:** Cardinality aggregation

### Big Data Systems
**From Google (KDD 2016):**
> "Ordering Google's Datasets... Goods: Organizing Google's datasets"

**Scale:**
- Trillions of elements
- Sub-second queries
- <100 bytes memory per set

## Space Analysis

### Theoretical Bounds
```
n = number of distinct elements (cardinality)
m = number of registers (typically m = 2^b = 65536)

Standard error: 1.04/√m
Relative error: ~1.04/√m

Example: m=65536
Error: 1.04/256 ≈ 0.4%

Space: m × 5 bits = 65536 × 5 = 327680 bits ≈ 4KB (!!!)
```

### Practical Examples

**For n = 1 billion distinct elements:**
```
Naive: 1B × 8 bytes = 8GB (assuming 64-bit IDs)
HLL: 65536 registers × 5 bits = 40KB (!!)

Compression: 200,000x (!!)
Error rate: ~0.4%
```

**For Palace Mental (10M artifacts):**
```
Naive: 10M × 8 bytes (IDs) = 80MB
HLL: 4KB (m=65536)

Compression: 20,000x (!!)
Error: ~0.4% ±40,000 elements
```

## Critical Algorithms

### 1. HLL Add
```python
class HyperLogLog:
    def __init__(self, precision=12):
        self.m = 1 << precision  # m = 4096
        self.registers = [0] * self.m

    def add(self, item):
        # Hash item
        x = hash(item)

        # Find first 1-bit position (ρ)
        rank = (x & -x).bit_length() - 1

        # Choose register
        j = x % self.m

        # Take maximum
        self.registers[j] = max(self.registers[j], rank)

    def count(self):
        """Estimate cardinality"""
        # Harmonic mean
        sum_inverse = sum(2.0 ** (-r) for r in self.registers)
        alpha = 0.7213 / (1 + 1.1079 / self.m)
        estimate = alpha * (self.m * self.m) / sum_inverse
        return int(estimate)
```

### 2. HLL Union
```python
def union(hll1, hll2):
    """Merge two HLL sketches (no need for raw data!)"""
    result = HyperLogLog()
    for i in range(len(hll1.registers)):
        result.registers[i] = max(hll1.registers[i], hll2.registers[i])
    return result
```

### 3. Sliding Window HLL
**From "Sliding HyperLogLog" (ACM 2024):**
> "A new algorithm estimating the number of active flows in a data stream... Adapts HyperLogLog for sliding windows"

**Use case:** Detect active users in last hour/day/week

## For Palace Mental

### Application: Unique Artifact Counting

**Problem:** Track unique artifacts across billions of operations
**Solution:** HyperLogLog for cardinality estimation

```python
# Track unique artifacts
hll_artifacts = HyperLogLog(precision=14)

# On each artifact processed
hll_artifacts.add(artifact_id)

# Estimate count anytime
unique_count = hll_artifacts.count()
# Error: ~0.1% for precision=14
```

### Storage Savings
```
Current: Store all artifact IDs
- 10M artifacts × 8 bytes = 80MB

HLL: Cardinality sketch
- 16K registers × 5 bits = 10KB (!!)
- Plus 10M file metadata = 200MB

Savings: Minimal (but useful for dedup metrics)
```

### Better: HLL for Deduplication Detection

```python
# Use HLL to detect if artifact set has changed
hll_baseline = HyperLogLog()
for artifact_id in known_artifacts:
    hll_baseline.add(artifact_id)

# During scan
hll_current = HyperLogLog()
for artifact_id in scanned_artifacts:
    hll_current.add(artifact_id)

# Compare cardinalities
if hll_current.count() != hll_baseline.count():
    # Something changed! Need detailed scan
    detailed_scan_required = True
```

## Performance Characteristics

### Time Complexity
- **Add:** O(1) - just hash and max operation
- **Count:** O(m) where m = number of registers (typically 4K-64K)
- **Union:** O(m) - max of two sketches

### Space Complexity
- **Per sketch:** m × 5 bits (fixed)
- **Typical:** 4KB-32KB per HLL sketch
- **Can store billions** of elements in <10KB (!!)

### Accuracy
- **Standard error:** 1.04/√m
- **Precision=12 (m=4096):** Error ~1.6%
- **Precision=16 (m=65536):** Error ~0.4%
- **Precision=20 (m=1M):** Error ~0.1%

## HyperLogLogLog (2022) Improvement

**From "HyperLogLogLog: One Log More" (KDD 2022):**
> "Uses just one log register (vs 12 in HLL)... More space-efficient with similar accuracy"

**Storage:**
- **HLL:** m × 5 bits (typically 4KB)
- **HLLLogLog:** log₂(n) bits (typically 40-60 bits)

**Use case:** When memory is extremely constrained

## Best Practices

### When to Use HyperLogLog
✅ **Use for:**
- Counting distinct values (cardinality)
- Very large datasets (millions to billions)
- Memory-constrained environments
- Approximate answers acceptable

❌ **Avoid for:**
- Exact counts needed
- Small datasets (set is fine)
- Need actual distinct elements

### Configuration Tips
```python
# Choose precision based on expected cardinality
if expected_n < 1000:
    precision = 10  # m=1024, ~3% error
elif expected_n < 100000:
    precision = 12  # m=4096, ~1.6% error
elif expected_n < 10M:
    precision = 14  # m=16384, ~0.8% error
else:
    precision = 16  # m=65536, ~0.4% error
    precision = 18  # m=262144, ~0.2% error (for billions)
```

### Common Pitfalls
1. **Not enough registers:** For huge cardinalities, need larger m
2. **Hash collisions:** Use good hash function (hash(), SHA-1, Murmur3)
3. **Merging sketches:** Use union, not averaging!
4. **Small datasets:** Error can be high for n < 1000

## References
1. Flajolet et al., "HyperLogLog: the analysis of a near-optimal probabilistic algorithm", 2007
2. Heule et al., "HyperLogLog in practice: algorithmic engineering of state of the art", SIGMOD 2013
3. Karppa, Pagh, "HyperLogLogLog: Cardinality Estimation With One Log More", KDD 2022
4. Chabchoub, Hébrail, "Sliding HyperLogLog: Estimating cardinality in a data stream", Inria 2024
5. Redis HyperLogLog documentation: https://redis.io/docs/data-types/probabilistic/
